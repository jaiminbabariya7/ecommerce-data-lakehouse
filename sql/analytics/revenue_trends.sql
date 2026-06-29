-- revenue_trends.sql
-- Monthly and weekly revenue trends with YoY and WoW comparisons.

-- Monthly revenue + MoM growth
WITH monthly AS (
    SELECT
        DATE_TRUNC(order_date, MONTH)                       AS month,
        SUM(net_revenue)                                    AS revenue,
        COUNT(DISTINCT order_id)                            AS orders,
        COUNT(DISTINCT customer_id)                         AS customers,
        ROUND(AVG(net_revenue), 2)                          AS avg_order_value
    FROM `PROJECT_ID.ecommerce_raw.orders`
    WHERE status IN ("completed", "shipped")
    GROUP BY month
)
SELECT
    month,
    ROUND(revenue, 2)                                       AS revenue,
    orders,
    customers,
    avg_order_value,
    LAG(revenue) OVER (ORDER BY month)                      AS prev_month_revenue,
    ROUND(100 * SAFE_DIVIDE(revenue - LAG(revenue) OVER (ORDER BY month),
                            LAG(revenue) OVER (ORDER BY month)), 1) AS mom_growth_pct,
    LAG(revenue, 12) OVER (ORDER BY month)                  AS prev_year_revenue,
    ROUND(100 * SAFE_DIVIDE(revenue - LAG(revenue, 12) OVER (ORDER BY month),
                            LAG(revenue, 12) OVER (ORDER BY month)), 1) AS yoy_growth_pct
FROM monthly
ORDER BY month;


-- Revenue by channel + running share
SELECT
    channel,
    ROUND(SUM(net_revenue), 2)                              AS total_revenue,
    COUNT(DISTINCT order_id)                                AS total_orders,
    ROUND(100 * SUM(net_revenue) / SUM(SUM(net_revenue)) OVER (), 2) AS revenue_share_pct
FROM `PROJECT_ID.ecommerce_raw.orders`
WHERE status IN ("completed","shipped")
GROUP BY channel
ORDER BY total_revenue DESC;