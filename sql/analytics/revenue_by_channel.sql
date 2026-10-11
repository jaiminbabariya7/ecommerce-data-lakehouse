-- revenue_by_channel.sql
-- Revenue and order share by sales channel.

SELECT
    channel,
    ROUND(SUM(net_revenue), 2)                              AS total_revenue,
    COUNT(DISTINCT order_id)                                AS total_orders,
    ROUND(100 * SUM(net_revenue) / SUM(SUM(net_revenue)) OVER (), 2) AS revenue_share_pct
FROM `PROJECT_ID.ecommerce_raw.orders`
WHERE status IN ("completed","shipped")
GROUP BY channel
ORDER BY total_revenue DESC;