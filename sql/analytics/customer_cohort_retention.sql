-- customer_cohort_retention.sql
-- Monthly cohort retention: tracks returning purchase rate for each signup cohort.

WITH cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC(registration_date, MONTH)  AS cohort_month
    FROM `PROJECT_ID.ecommerce_raw.customers`
    WHERE is_active = TRUE
),
purchases AS (
    SELECT
        customer_id,
        DATE_TRUNC(order_date, MONTH)          AS purchase_month
    FROM `PROJECT_ID.ecommerce_raw.orders`
    WHERE status IN ("completed","shipped")
    GROUP BY customer_id, purchase_month
),
cohort_data AS (
    SELECT
        c.cohort_month,
        DATE_DIFF(p.purchase_month, c.cohort_month, MONTH) AS months_since_signup,
        COUNT(DISTINCT c.customer_id)                       AS customers
    FROM cohorts c
    LEFT JOIN purchases p USING (customer_id)
    GROUP BY c.cohort_month, months_since_signup
),
cohort_sizes AS (
    SELECT cohort_month, customers AS cohort_size
    FROM cohort_data
    WHERE months_since_signup = 0
)
SELECT
    cd.cohort_month,
    cs.cohort_size,
    cd.months_since_signup,
    cd.customers                                              AS retained,
    ROUND(100 * SAFE_DIVIDE(cd.customers, cs.cohort_size), 1) AS retention_pct
FROM cohort_data cd
JOIN cohort_sizes cs USING (cohort_month)
WHERE cd.months_since_signup BETWEEN 0 AND 12
ORDER BY cd.cohort_month, cd.months_since_signup;