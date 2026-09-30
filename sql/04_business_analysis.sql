/* =====================================================================
   04_business_analysis.sql
   Core business questions answered on the clean `sales` table.
   Currency: Indian Rupees (INR). 1 Crore = 10,000,000 | 1 Lakh = 100,000
   ===================================================================== */

-- @query: q01_overall_kpis | Headline KPIs for the full period (2022-2025)
SELECT
    ROUND(SUM(sales) / 1e7, 2)                         AS total_sales_cr,
    ROUND(SUM(profit) / 1e7, 2)                        AS total_profit_cr,
    ROUND(100.0 * SUM(profit) / SUM(sales), 2)         AS profit_margin_pct,
    COUNT(DISTINCT order_id)                           AS total_orders,
    COUNT(DISTINCT customer_id)                        AS total_customers,
    SUM(quantity)                                      AS units_sold,
    ROUND(SUM(sales) / COUNT(DISTINCT order_id), 0)    AS avg_order_value
FROM sales;

-- @query: q02_yearly_performance | Sales, profit and YoY growth by year
WITH yearly AS (
    SELECT order_year,
           SUM(sales)               AS sales,
           SUM(profit)              AS profit,
           COUNT(DISTINCT order_id) AS orders
    FROM sales
    GROUP BY order_year
)
SELECT
    order_year,
    ROUND(sales / 1e5, 2)                                                        AS sales_lakh,
    ROUND(profit / 1e5, 2)                                                       AS profit_lakh,
    ROUND(100.0 * profit / sales, 2)                                             AS margin_pct,
    orders,
    ROUND(100.0 * (sales - LAG(sales) OVER (ORDER BY order_year))
          / LAG(sales) OVER (ORDER BY order_year), 2)                            AS sales_yoy_pct,
    ROUND(100.0 * (profit - LAG(profit) OVER (ORDER BY order_year))
          / LAG(profit) OVER (ORDER BY order_year), 2)                           AS profit_yoy_pct
FROM yearly
ORDER BY order_year;

-- @query: q03_monthly_trend | Monthly sales and profit (for trend line)
SELECT
    year_month,
    ROUND(SUM(sales) / 1e5, 2)   AS sales_lakh,
    ROUND(SUM(profit) / 1e5, 2)  AS profit_lakh,
    COUNT(DISTINCT order_id)     AS orders
FROM sales
GROUP BY year_month
ORDER BY year_month;

-- @query: q04_seasonality | Average monthly sales by calendar month (festive-season effect)
WITH monthly AS (
    SELECT order_year, order_month, SUM(sales) AS sales
    FROM sales
    GROUP BY order_year, order_month
)
SELECT
    order_month,
    ROUND(AVG(sales) / 1e5, 2)                                                   AS avg_sales_lakh,
    ROUND(100.0 * AVG(sales) / (SELECT AVG(sales) FROM monthly) - 100, 1)        AS pct_vs_avg_month
FROM monthly
GROUP BY order_month
ORDER BY order_month;

-- @query: q05_category_performance | Sales, profit and margin by category
SELECT
    category,
    ROUND(SUM(sales) / 1e5, 2)                                   AS sales_lakh,
    ROUND(SUM(profit) / 1e5, 2)                                  AS profit_lakh,
    ROUND(100.0 * SUM(profit) / SUM(sales), 2)                   AS margin_pct,
    ROUND(100.0 * SUM(sales) / (SELECT SUM(sales) FROM sales), 2) AS sales_share_pct
FROM sales
GROUP BY category
ORDER BY sales_lakh DESC;

-- @query: q06_subcategory_profitability | Sub-categories ranked by profit (loss-makers at the bottom)
SELECT
    category,
    sub_category,
    ROUND(SUM(sales) / 1e5, 2)                   AS sales_lakh,
    ROUND(SUM(profit) / 1e5, 2)                  AS profit_lakh,
    ROUND(100.0 * SUM(profit) / SUM(sales), 2)   AS margin_pct,
    ROUND(100.0 * AVG(discount), 1)              AS avg_discount_pct
FROM sales
GROUP BY category, sub_category
ORDER BY profit_lakh DESC;

-- @query: q07_region_performance | Performance by region
SELECT
    region,
    ROUND(SUM(sales) / 1e5, 2)                   AS sales_lakh,
    ROUND(SUM(profit) / 1e5, 2)                  AS profit_lakh,
    ROUND(100.0 * SUM(profit) / SUM(sales), 2)   AS margin_pct,
    ROUND(100.0 * AVG(discount), 1)              AS avg_discount_pct,
    COUNT(DISTINCT customer_id)                  AS customers
FROM sales
GROUP BY region
ORDER BY sales_lakh DESC;

-- @query: q08_top_states | Top 10 states by sales
SELECT
    state,
    region,
    ROUND(SUM(sales) / 1e5, 2)                   AS sales_lakh,
    ROUND(SUM(profit) / 1e5, 2)                  AS profit_lakh,
    ROUND(100.0 * SUM(profit) / SUM(sales), 2)   AS margin_pct
FROM sales
GROUP BY state, region
ORDER BY sales_lakh DESC
LIMIT 10;

-- @query: q09_segment_performance | Performance by customer segment
SELECT
    segment,
    COUNT(DISTINCT customer_id)                              AS customers,
    COUNT(DISTINCT order_id)                                 AS orders,
    ROUND(SUM(sales) / 1e5, 2)                               AS sales_lakh,
    ROUND(100.0 * SUM(profit) / SUM(sales), 2)               AS margin_pct,
    ROUND(SUM(sales) / COUNT(DISTINCT order_id), 0)          AS avg_order_value
FROM sales
GROUP BY segment
ORDER BY sales_lakh DESC;

-- @query: q10_discount_impact | How discount level affects profit margin
SELECT
    discount_band,
    COUNT(*)                                     AS order_lines,
    ROUND(SUM(sales) / 1e5, 2)                   AS sales_lakh,
    ROUND(SUM(profit) / 1e5, 2)                  AS profit_lakh,
    ROUND(100.0 * SUM(profit) / SUM(sales), 2)   AS margin_pct,
    ROUND(100.0 * AVG(is_loss), 1)               AS pct_lines_at_loss
FROM sales
GROUP BY discount_band
ORDER BY MIN(discount);

-- @query: q11_ship_mode | Shipping mode usage and speed
SELECT
    ship_mode,
    COUNT(DISTINCT order_id)                                               AS orders,
    ROUND(100.0 * COUNT(DISTINCT order_id)
          / (SELECT COUNT(DISTINCT order_id) FROM sales), 1)               AS order_share_pct,
    ROUND(AVG(shipping_days), 2)                                           AS avg_shipping_days,
    ROUND(SUM(sales) / 1e5, 2)                                             AS sales_lakh
FROM sales
GROUP BY ship_mode
ORDER BY orders DESC;

-- @query: q12_top_customers | Top 10 customers by lifetime sales
SELECT
    customer_id,
    customer_name,
    segment,
    region,
    COUNT(DISTINCT order_id)                     AS orders,
    ROUND(SUM(sales), 0)                         AS lifetime_sales,
    ROUND(SUM(profit), 0)                        AS lifetime_profit
FROM sales
GROUP BY customer_id, customer_name, segment, region
ORDER BY lifetime_sales DESC
LIMIT 10;

-- @query: q13_top_products_by_profit | Top 10 most profitable products
SELECT
    product_name,
    sub_category,
    SUM(quantity)                                AS units_sold,
    ROUND(SUM(sales) / 1e5, 2)                   AS sales_lakh,
    ROUND(SUM(profit) / 1e5, 2)                  AS profit_lakh
FROM sales
GROUP BY product_name, sub_category
ORDER BY profit_lakh DESC
LIMIT 10;

-- @query: q14_loss_making_products | Products that lose money overall
SELECT
    product_name,
    sub_category,
    ROUND(100.0 * AVG(discount), 1)              AS avg_discount_pct,
    ROUND(SUM(sales) / 1e5, 2)                   AS sales_lakh,
    ROUND(SUM(profit) / 1e5, 2)                  AS profit_lakh
FROM sales
GROUP BY product_name, sub_category
HAVING SUM(profit) < 0
ORDER BY profit_lakh;
