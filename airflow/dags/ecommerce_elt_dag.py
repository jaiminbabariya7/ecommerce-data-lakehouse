"""
Airflow DAG: E-Commerce ELT Pipeline

Orchestrates the full ELT flow:
  1. Extract: Upload CSV files from GCS landing zone
  2. Load:    Load raw CSVs into BigQuery raw layer
  3. Transform: Run dbt models (staging -> mart)
  4. Validate: Run dbt tests + data quality checks

Schedule: Daily at 05:00 UTC.
"""
from __future__ import annotations
import os
from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.utils.dates import days_ago

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
GCS_BUCKET = os.environ["GCS_ECOMMERCE_BUCKET"]
BQ_DATASET = os.getenv("BQ_RAW_DATASET", "ecommerce_raw")
DBT_DIR    = "/opt/airflow/dbt"

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
    description="E-commerce ELT: GCS -> BigQuery raw -> dbt transforms -> analytics",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 5 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["ecommerce","bigquery","dbt","elt"],
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

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"dbt run --project-dir {DBT_DIR} --profiles-dir {DBT_DIR}",
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"dbt test --project-dir {DBT_DIR} --profiles-dir {DBT_DIR}",
    )

    start >> list(load_tasks.values()) >> dbt_run >> dbt_test >> end