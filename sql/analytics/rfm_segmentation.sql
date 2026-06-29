-- rfm_segmentation.sql
-- RFM (Recency, Frequency, Monetary) customer segmentation using BigQuery.
-- Scores each customer 1-4 on each dimension, then classifies them.

WITH rfm_raw AS (
    SELECT
        customer_id,
        DATE_DIFF(CURRENT_DATE(), MAX(order_date), DAY)     AS recency_days,
        COUNT(DISTINCT order_date)                           AS frequency,
        ROUND(SUM(net_revenue), 2)                          AS monetary
    FROM `PROJECT_ID.ecommerce_raw.orders`
    WHERE status IN ("completed", "shipped")
    GROUP BY customer_id
),
rfm_scored AS (
    SELECT
        customer_id,
        recency_days, frequency, monetary,
        -- Lower recency = better (recently active)
        NTILE(4) OVER (ORDER BY recency_days DESC)  AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC)      AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)       AS m_score
    FROM rfm_raw
)
SELECT
    r.customer_id,
    c.first_name,
    c.last_name,
    c.country,
    r.recency_days,
    r.frequency,
    r.monetary,
    r.r_score,
    r.f_score,
    r.m_score,
    r.r_score + r.f_score + r.m_score                       AS rfm_total,
    CASE
        WHEN r_score = 4 AND f_score = 4 AND m_score = 4   THEN "Champions"
        WHEN r_score >= 3 AND f_score >= 3                  THEN "Loyal Customers"
        WHEN r_score = 4 AND f_score <= 2                   THEN "Recent Customers"
        WHEN r_score >= 3 AND m_score >= 3                  THEN "Potential Loyalists"
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN "At Risk"
        WHEN r_score = 1 AND f_score >= 2                   THEN "Hibernating"
        WHEN r_score = 1 AND f_score = 1                    THEN "Lost"
        ELSE "Needs Attention"
    END                                                      AS rfm_segment
FROM rfm_scored r
JOIN `PROJECT_ID.ecommerce_raw.customers` c USING (customer_id)
ORDER BY rfm_total DESC;