# E-commerce Analytics with BigQuery — Advanced SQL & Business Intelligence

![BigQuery](https://img.shields.io/badge/BigQuery-Data%20Warehouse-blue?logo=googlebigquery)
![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![GCP](https://img.shields.io/badge/Google%20Cloud-Platform-4285F4?logo=googlecloud)
![SQL](https://img.shields.io/badge/SQL-Advanced-lightgrey)
![MIT License](https://img.shields.io/badge/License-MIT-green)

> Advanced SQL analytics on a multi-table e-commerce dataset in BigQuery — window functions, customer segmentation, RFM analysis, cohort analysis, and revenue trend modeling. Synthetic data generated with Python for reproducibility.

---

## Overview

This project demonstrates the SQL analytics skills expected of a data analyst or analytics engineer: going beyond basic aggregations to window functions, cohort analysis, and customer segmentation patterns used in production e-commerce analytics.

All queries are production-grade BigQuery SQL, optimized with partitioning and clustering.

---

## Dataset Schema

```sql
-- orders: one row per order
CREATE TABLE ecommerce.orders (
  order_id     STRING NOT NULL,
  customer_id  STRING NOT NULL,
  product_id   STRING NOT NULL,
  order_date   DATE NOT NULL,
  order_amount FLOAT64,
  quantity     INT64,
  status       STRING,   -- 'completed', 'returned', 'cancelled'
  channel      STRING    -- 'web', 'mobile', 'store'
)
PARTITION BY order_date
CLUSTER BY customer_id, product_id;

-- customers
CREATE TABLE ecommerce.customers (
  customer_id   STRING NOT NULL,
  signup_date   DATE,
  country       STRING,
  age_group     STRING,  -- '18-24', '25-34', '35-44', '45+'
  loyalty_tier  STRING   -- 'bronze', 'silver', 'gold', 'platinum'
);

-- products
CREATE TABLE ecommerce.products (
  product_id   STRING NOT NULL,
  product_name STRING,
  category     STRING,
  unit_price   FLOAT64,
  brand        STRING
);
```

---

## Analytics Queries

### Revenue & Product Performance

```sql
-- Product revenue with ranking and running total
SELECT
  p.product_name,
  p.category,
  COUNT(o.order_id)               AS total_orders,
  SUM(o.order_amount)             AS total_revenue,
  ROUND(AVG(o.order_amount), 2)   AS avg_order_value,
  RANK() OVER (
    PARTITION BY p.category
    ORDER BY SUM(o.order_amount) DESC
  )                               AS rank_in_category,
  SUM(SUM(o.order_amount)) OVER (
    ORDER BY SUM(o.order_amount) DESC
    ROWS UNBOUNDED PRECEDING
  )                               AS running_total_revenue
FROM ecommerce.orders o
JOIN ecommerce.products p USING (product_id)
WHERE o.status = 'completed'
  AND o.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY p.product_name, p.category
ORDER BY total_revenue DESC;
```

**Sample Result:**
```
product_name       | category    | total_orders | total_revenue | avg_order_value | rank_in_category
Wireless Headphones| Electronics |        3,241 |  $648,200     |          $200   | 1
Running Shoes      | Apparel     |        2,891 |  $520,380     |          $180   | 1
Smart Watch        | Electronics |        2,104 |  $420,800     |          $200   | 2
```

---

### Customer Segmentation (RFM Analysis)

```sql
-- RFM: Recency, Frequency, Monetary segmentation
WITH rfm_base AS (
  SELECT
    customer_id,
    DATE_DIFF(CURRENT_DATE(), MAX(order_date), DAY)  AS recency_days,
    COUNT(DISTINCT order_id)                          AS frequency,
    SUM(order_amount)                                 AS monetary
  FROM ecommerce.orders
  WHERE status = 'completed'
  GROUP BY customer_id
),
rfm_scores AS (
  SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    NTILE(5) OVER (ORDER BY recency_days ASC)   AS r_score,  -- lower recency = better
    NTILE(5) OVER (ORDER BY frequency DESC)     AS f_score,
    NTILE(5) OVER (ORDER BY monetary DESC)      AS m_score
  FROM rfm_base
)
SELECT
  customer_id,
  r_score, f_score, m_score,
  (r_score + f_score + m_score) AS total_rfm_score,
  CASE
    WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
    WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
    WHEN r_score >= 4 AND f_score <= 2 THEN 'Recent Customers'
    WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
    WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost Customers'
    ELSE 'Potential Loyalists'
  END AS segment
FROM rfm_scores
ORDER BY total_rfm_score DESC;
```

**Sample Segment Distribution:**
```
segment              | customers | avg_revenue | pct_of_total_revenue
Champions            |     1,240 |    $842     |          34.2%
Loyal Customers      |     3,180 |    $421     |          43.8%
At Risk              |     2,100 |    $189     |          12.9%
Lost Customers       |     4,820 |     $67     |           9.1%
```

---

### Cohort Retention Analysis

```sql
-- Monthly cohort retention: what % of customers from each signup month
-- are still purchasing N months later?
WITH cohorts AS (
  SELECT
    c.customer_id,
    DATE_TRUNC(c.signup_date, MONTH)  AS cohort_month,
    DATE_TRUNC(o.order_date, MONTH)   AS order_month
  FROM ecommerce.customers c
  JOIN ecommerce.orders o USING (customer_id)
  WHERE o.status = 'completed'
),
cohort_sizes AS (
  SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
  FROM cohorts
  GROUP BY cohort_month
),
retention AS (
  SELECT
    c.cohort_month,
    DATE_DIFF(c.order_month, c.cohort_month, MONTH) AS months_since_signup,
    COUNT(DISTINCT c.customer_id) AS active_customers
  FROM cohorts c
  GROUP BY cohort_month, months_since_signup
)
SELECT
  r.cohort_month,
  r.months_since_signup,
  r.active_customers,
  cs.cohort_size,
  ROUND(r.active_customers / cs.cohort_size * 100, 1) AS retention_pct
FROM retention r
JOIN cohort_sizes cs USING (cohort_month)
ORDER BY cohort_month, months_since_signup;
```

**Sample Cohort Output:**
```
cohort_month | month_0 | month_1 | month_2 | month_3 | month_6
2024-01      |   100%  |  42.1%  |  31.4%  |  26.8%  |  21.3%
2024-02      |   100%  |  44.3%  |  33.1%  |  28.2%  |  22.7%
2024-03      |   100%  |  41.8%  |  30.9%  |  25.4%  |    —
```

---

### Customer Acquisition & Revenue Trends

```sql
-- Monthly new customers + MoM growth + cumulative
SELECT
  DATE_TRUNC(signup_date, MONTH)                            AS month,
  COUNT(*)                                                  AS new_customers,
  LAG(COUNT(*)) OVER (ORDER BY DATE_TRUNC(signup_date, MONTH)) AS prev_month,
  ROUND(
    (COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY DATE_TRUNC(signup_date, MONTH)))
    / NULLIF(LAG(COUNT(*)) OVER (ORDER BY DATE_TRUNC(signup_date, MONTH)), 0) * 100, 1
  )                                                         AS mom_growth_pct,
  SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC(signup_date, MONTH)) AS cumulative_customers
FROM ecommerce.customers
GROUP BY month
ORDER BY month;
```

---

### Channel Attribution

```sql
-- Revenue and conversion by acquisition channel
SELECT
  o.channel,
  COUNT(DISTINCT o.customer_id)       AS unique_buyers,
  COUNT(o.order_id)                   AS total_orders,
  SUM(o.order_amount)                 AS total_revenue,
  ROUND(AVG(o.order_amount), 2)       AS avg_order_value,
  ROUND(SUM(o.order_amount) /
    SUM(SUM(o.order_amount)) OVER () * 100, 1) AS revenue_share_pct
FROM ecommerce.orders o
WHERE status = 'completed'
GROUP BY o.channel
ORDER BY total_revenue DESC;
```

---

## Python Data Generator

```python
# scripts/generate_data.py
from faker import Faker
import pandas as pd, random, uuid
from datetime import date, timedelta

fake = Faker()
Faker.seed(42)
random.seed(42)

CATEGORIES = ["Electronics", "Apparel", "Home", "Sports", "Beauty"]
CHANNELS = ["web", "mobile", "store"]

def generate_customers(n=10000) -> pd.DataFrame:
    return pd.DataFrame([{
        "customer_id": str(uuid.uuid4())[:8],
        "signup_date": fake.date_between(start_date="-2y", end_date="today"),
        "country": fake.country_code(),
        "age_group": random.choice(["18-24", "25-34", "35-44", "45+"]),
        "loyalty_tier": random.choice(["bronze", "silver", "gold", "platinum"]),
    } for _ in range(n)])

def generate_orders(customers: pd.DataFrame, n=50000) -> pd.DataFrame:
    return pd.DataFrame([{
        "order_id": str(uuid.uuid4())[:12],
        "customer_id": random.choice(customers["customer_id"].tolist()),
        "product_id": str(random.randint(1, 500)),
        "order_date": fake.date_between(start_date="-1y", end_date="today"),
        "order_amount": round(random.lognormvariate(4.5, 0.8), 2),
        "quantity": random.randint(1, 5),
        "status": random.choices(["completed", "returned", "cancelled"], weights=[85, 10, 5])[0],
        "channel": random.choice(CHANNELS),
    } for _ in range(n)])

if __name__ == "__main__":
    customers = generate_customers(10000)
    orders = generate_orders(customers, 50000)
    customers.to_csv("data/customers.csv", index=False)
    orders.to_csv("data/orders.csv", index=False)
    print(f"Generated {len(customers)} customers, {len(orders)} orders")
```

---

## Project Structure

```
Ecommerce_Data_Analysis_BigQuery/
├── data/                   # Generated CSVs
├── sql/
│   ├── schema.sql          # Table DDL
│   ├── product_revenue.sql
│   ├── rfm_segmentation.sql
│   ├── cohort_retention.sql
│   ├── acquisition_trends.sql
│   └── channel_attribution.sql
├── scripts/
│   └── generate_data.py    # Synthetic data generator
├── notebooks/
│   └── analysis.ipynb      # Exploration + visualizations
├── requirements.txt
└── README.md
```

---

## Setup

```bash
git clone https://github.com/jaiminbabariya7/Ecommerce_Data_Analysis_BigQuery
pip install google-cloud-bigquery faker pandas

# Generate data
python scripts/generate_data.py

# Upload to GCS and load into BigQuery
gsutil cp data/*.csv gs://your-bucket/ecommerce/
bq load --source_format=CSV ecommerce.customers gs://your-bucket/ecommerce/customers.csv
bq load --source_format=CSV ecommerce.orders gs://your-bucket/ecommerce/orders.csv

# Run queries
bq query --use_legacy_sql=false < sql/rfm_segmentation.sql
```

---

## Skills Demonstrated
`BigQuery` · `Advanced SQL` · `Window Functions` · `RFM Analysis` · `Cohort Analysis` · `Customer Segmentation` · `Revenue Analytics` · `GCP` · `Python` · `Data Modeling`
