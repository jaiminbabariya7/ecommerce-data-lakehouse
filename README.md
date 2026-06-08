# E-Commerce Analytics Pipeline — BigQuery

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![BigQuery](https://img.shields.io/badge/BigQuery-Analytics-4285F4?logo=googlebigquery)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

> End-to-end e-commerce analytics: synthetic dataset generation in Python → BigQuery ingestion → deep-dive SQL analysis for revenue, customer behaviour, and product performance KPIs.

## Architecture
```
Python Data Generator
  └── generates realistic orders, customers, products (~100K rows)
        ↓
Google Cloud Storage (raw CSV/Parquet)
        ↓
BigQuery Ingestion (external table → native)
        ↓
SQL Analytics Layer
  ├── Revenue & GMV analysis
  ├── Customer cohort analysis
  ├── Product performance ranking
  ├── Cart abandonment patterns
  └── Time-series trend analysis
        ↓
Business KPI Dashboard
```

## Key Analyses

| Analysis | SQL Technique | Business Question |
|---|---|---|
| Revenue by category | GROUP BY + SUM | Which categories drive most GMV? |
| Top customers by LTV | Window function RANK() | Who are the high-value customers? |
| Monthly GMV trend | DATE_TRUNC + time series | Is revenue growing MoM? |
| Repeat purchase rate | Self-join on customer_id | What is customer retention? |
| Product affinity | Co-occurrence matrix | What products are bought together? |

## Setup
```bash
git clone https://github.com/jaiminbabariya7/Ecommerce_Data_Analysis_BigQuery
cd Ecommerce_Data_Analysis_BigQuery
pip install -r requirements.txt
python generate_data.py          # generate synthetic dataset
# Load to BigQuery
bq load --autodetect your_project:ecommerce.orders data/orders.csv
```

## Skills Demonstrated
`Python` · `BigQuery` · `SQL` · `Data Generation` · `E-Commerce Analytics` · `KPI Design` · `GCP`
