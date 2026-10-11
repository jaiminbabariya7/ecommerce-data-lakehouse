"""
Airflow DAG: E-Commerce ELT Pipeline

Orchestrates the ELT flow:
  1. Load:      CSVs in gs://<bucket>/landing/<table>/<table>.csv -> BigQuery raw layer
  2. Validate:  data-quality checks on the raw tables (row counts, referential
                integrity, order totals = sum of line items)
  3. Transform: run each analytics query in sql/analytics/ and materialise it
                as a table in the analytics dataset (RFM, revenue trends,
                revenue by channel, product performance, cohort retention)

Schedule: Daily at 05:00 UTC.
"""
from __future__ import annotations
import os
from datetime import timedelta
from airflow import DAG
from pathlib import Path
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCheckOperator, BigQueryInsertJobOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.utils.dates import days_ago

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
GCS_BUCKET = os.environ["GCS_ECOMMERCE_BUCKET"]
BQ_DATASET = "ecommerce_raw"            # the analytics SQL reads PROJECT_ID.ecommerce_raw.*
ANALYTICS  = os.getenv("BQ_ANALYTICS_DATASET", "ecommerce_analytics")
SQL_DIR    = Path(os.getenv("SQL_DIR", "/opt/airflow/sql/analytics"))

DEFAULT_ARGS = {
    "owner": "jaimin.babariya",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
}

TABLES = {
    "customers":   ["customer_id:STRING","first_name:STRING","last_name:STRING","email:STRING","country:STRING","city:STRING","registration_date:DATE","is_active:BOOLEAN"],
    "products":    ["product_id:STRING","product_name:STRING","category:STRING","unit_price:NUMERIC","unit_cost:NUMERIC"],
    "orders":      ["order_id:STRING","customer_id:STRING","order_date:DATE","status:STRING","channel:STRING","net_revenue:NUMERIC"],
    "order_items": ["item_id:STRING","order_id:STRING","product_id:STRING","quantity:INTEGER","unit_price:NUMERIC","discount_pct:NUMERIC","line_revenue:NUMERIC"],
}


with DAG(
    dag_id="ecommerce_elt_pipeline",
    description="E-commerce ELT: GCS -> BigQuery raw -> quality checks -> analytics tables",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 5 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["ecommerce","bigquery","elt"],
) as dag:

    start = EmptyOperator(task_id="start")
    end   = EmptyOperator(task_id="end")

    # Load tasks (GCS → BigQuery, one per table)
    load_tasks = {}
    for table, schema in TABLES.items():
        load_tasks[table] = GCSToBigQueryOperator(
            task_id=f"load_{table}",
            bucket=GCS_BUCKET,
            source_objects=[f"landing/{table}/{table}.csv"],
            destination_project_dataset_table=f"{PROJECT_ID}.{BQ_DATASET}.{table}",
            schema_fields=[{"name":f.split(":")[0],"type":f.split(":")[1],"mode":"NULLABLE"} for f in schema],
            write_disposition="WRITE_TRUNCATE",
            skip_leading_rows=1,
            allow_jagged_rows=True,
            ignore_unknown_values=True,
        )

    raw = f"`{PROJECT_ID}.{BQ_DATASET}"
    checks = {
        "check_orders_loaded":        f"SELECT COUNT(*) > 0 FROM {raw}.orders`",
        "check_orders_have_customer": f"""SELECT COUNT(*) = 0 FROM {raw}.orders` o
                                          LEFT JOIN {raw}.customers` c USING (customer_id)
                                          WHERE c.customer_id IS NULL""",
        "check_items_have_order":     f"""SELECT COUNT(*) = 0 FROM {raw}.order_items` i
                                          LEFT JOIN {raw}.orders` o USING (order_id)
                                          WHERE o.order_id IS NULL""",
        "check_order_totals":         f"""SELECT COUNT(*) = 0 FROM (
                                            SELECT o.order_id, o.net_revenue, SUM(i.line_revenue) AS lines
                                            FROM {raw}.orders` o JOIN {raw}.order_items` i USING (order_id)
                                            GROUP BY o.order_id, o.net_revenue
                                            HAVING ABS(o.net_revenue - lines) > 0.05)""",
    }
    check_tasks = [
        BigQueryCheckOperator(task_id=name, sql=sql, use_legacy_sql=False)
        for name, sql in checks.items()
    ]

    def analytics_job(sql_file: Path) -> BigQueryInsertJobOperator:
        query = sql_file.read_text().replace("PROJECT_ID", PROJECT_ID).strip().rstrip(";")
        return BigQueryInsertJobOperator(
            task_id=f"build_{sql_file.stem}",
            configuration={"query": {
                "query": f"CREATE OR REPLACE TABLE `{PROJECT_ID}.{ANALYTICS}.{sql_file.stem}` AS\n{query}",
                "useLegacySql": False,
            }},
        )

    analytics_tasks = [analytics_job(f) for f in sorted(SQL_DIR.glob("*.sql"))]

    start >> list(load_tasks.values())
    for load in load_tasks.values():
        load >> check_tasks
    for check in check_tasks:
        check >> analytics_tasks
    for job in analytics_tasks:
        job >> end
