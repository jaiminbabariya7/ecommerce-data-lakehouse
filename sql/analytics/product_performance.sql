-- product_performance.sql
-- Product sales performance: revenue, units, margin, and ranking.

WITH sales AS (
    SELECT
        oi.product_id,
        SUM(oi.quantity)                                     AS units_sold,
        ROUND(SUM(oi.line_revenue), 2)                       AS total_revenue,
        ROUND(SUM(oi.quantity * (oi.unit_price - p.unit_cost)), 2) AS gross_profit,
        COUNT(DISTINCT o.order_id)                           AS total_orders,
        COUNT(DISTINCT o.customer_id)                        AS unique_buyers
    FROM `PROJECT_ID.ecommerce_raw.order_items` oi
    JOIN `PROJECT_ID.ecommerce_raw.orders`   o USING (order_id)
    JOIN `PROJECT_ID.ecommerce_raw.products` p USING (product_id)
    WHERE o.status IN ("completed","shipped")
    GROUP BY oi.product_id
)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.unit_price,
    p.unit_cost,
    ROUND((p.unit_price - p.unit_cost) / p.unit_price * 100, 1) AS margin_pct,
    s.units_sold,
    s.total_revenue,
    s.gross_profit,
    s.total_orders,
    s.unique_buyers,
    RANK() OVER (ORDER BY s.total_revenue DESC)              AS revenue_rank,
    RANK() OVER (PARTITION BY p.category ORDER BY s.total_revenue DESC) AS category_rank
FROM sales s
JOIN `PROJECT_ID.ecommerce_raw.products` p USING (product_id)
ORDER BY s.total_revenue DESC
LIMIT 100;