-- 01_create_raw_tables.sql
-- Creates the raw e-commerce tables in BigQuery.
-- Run once before the first Airflow ELT execution.

CREATE SCHEMA IF NOT EXISTS `PROJECT_ID.ecommerce_raw`;

CREATE OR REPLACE TABLE `PROJECT_ID.ecommerce_raw.customers` (
    customer_id       STRING      NOT NULL,
    first_name        STRING,
    last_name         STRING,
    email             STRING,
    country           STRING,
    city              STRING,
    registration_date DATE,
    is_active         BOOL
)  OPTIONS (description = "Raw customer records");

CREATE OR REPLACE TABLE `PROJECT_ID.ecommerce_raw.products` (
    product_id   STRING  NOT NULL,
    product_name STRING,
    category     STRING,
    unit_price   NUMERIC,
    unit_cost    NUMERIC
) OPTIONS (description = "Raw product catalogue");

CREATE OR REPLACE TABLE `PROJECT_ID.ecommerce_raw.orders` (
    order_id    STRING  NOT NULL,
    customer_id STRING,
    order_date  DATE,
    status      STRING,
    channel     STRING,
    net_revenue NUMERIC
) PARTITION BY order_date
  OPTIONS (description = "Raw orders, partitioned by order_date");

CREATE OR REPLACE TABLE `PROJECT_ID.ecommerce_raw.order_items` (
    item_id      STRING  NOT NULL,
    order_id     STRING,
    product_id   STRING,
    quantity     INT64,
    unit_price   NUMERIC,
    discount_pct NUMERIC,
    line_revenue NUMERIC
) OPTIONS (description = "Raw order line items");