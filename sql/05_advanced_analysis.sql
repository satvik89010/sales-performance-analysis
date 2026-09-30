/* =====================================================================
   05_advanced_analysis.sql
   Window functions, CTEs, pivoting and Pareto analysis.
   ===================================================================== */

-- @query: a01_running_total_2025 | Month-by-month running total of sales in 2025
SELECT
    year_month,
    ROUND(SUM(sales) / 1e5, 2)                                               AS month_sales_lakh,
    ROUND(SUM(SUM(sales)) OVER (ORDER BY year_month) / 1e5, 2)               AS running_total_lakh
FROM sales
WHERE order_year = 2025
GROUP BY year_month
ORDER BY year_month;

-- @query: a02_mom_growth | Month-over-month sales growth (last 12 months)
WITH monthly AS (
    SELECT year_month, SUM(sales) AS sales
    FROM sales
    GROUP BY year_month
),
growth AS (
    SELECT
        year_month,
        ROUND(sales / 1e5, 2)                                                         AS sales_lakh,
        ROUND(100.0 * (sales - LAG(sales) OVER (ORDER BY year_month))
              / LAG(sales) OVER (ORDER BY year_month), 2)                            AS mom_growth_pct,
        ROUND(100.0 * (sales - LAG(sales, 12) OVER (ORDER BY year_month))
              / LAG(sales, 12) OVER (ORDER BY year_month), 2)                        AS yoy_same_month_pct
    FROM monthly
)
SELECT * FROM growth
WHERE year_month >= '2025-01'
ORDER BY year_month;

-- @query: a03_top3_products_per_category | Best 3 products in each category by sales (DENSE_RANK)
WITH product_sales AS (
    SELECT category, product_name, SUM(sales) AS sales
    FROM sales
    GROUP BY category, product_name
),
ranked AS (
    SELECT category, product_name, sales,
           DENSE_RANK() OVER (PARTITION BY category ORDER BY sales DESC) AS rnk
    FROM product_sales
)
SELECT category, rnk AS rank_in_category, product_name, ROUND(sales / 1e5, 2) AS sales_lakh
FROM ranked
WHERE rnk <= 3
ORDER BY category, rnk;

-- @query: a04_region_category_matrix | Profit matrix: region x category (pivot with CASE)
SELECT
    region,
    ROUND(SUM(CASE WHEN category = 'Technology'      THEN profit ELSE 0 END) / 1e5, 2) AS technology_profit_lakh,
    ROUND(SUM(CASE WHEN category = 'Furniture'       THEN profit ELSE 0 END) / 1e5, 2) AS furniture_profit_lakh,
    ROUND(SUM(CASE WHEN category = 'Office Supplies' THEN profit ELSE 0 END) / 1e5, 2) AS office_supplies_profit_lakh,
    ROUND(SUM(profit) / 1e5, 2)                                                        AS total_profit_lakh
FROM sales
GROUP BY region
ORDER BY total_profit_lakh DESC;

-- @query: a05_pareto_customers | Share of revenue from each 20% slice of customers (NTILE)
WITH customer_sales AS (
    SELECT customer_id, SUM(sales) AS sales
    FROM sales
    GROUP BY customer_id
),
bucketed AS (
    SELECT customer_id, sales,
           NTILE(5) OVER (ORDER BY sales DESC) AS quintile
    FROM customer_sales
)
SELECT
    'Top ' || (quintile * 20 - 19) || '-' || (quintile * 20) || '% customers' AS customer_group,
    COUNT(*)                                                                  AS customers,
    ROUND(SUM(sales) / 1e5, 2)                                                AS sales_lakh,
    ROUND(100.0 * SUM(sales) / (SELECT SUM(sales) FROM customer_sales), 1)    AS revenue_share_pct
FROM bucketed
GROUP BY quintile
ORDER BY quintile;

-- @query: a06_customer_order_frequency | How many customers are one-time vs repeat buyers
WITH orders_per_customer AS (
    SELECT customer_id, COUNT(DISTINCT order_id) AS orders
    FROM sales
    GROUP BY customer_id
)
SELECT
    CASE WHEN orders = 1  THEN '1 order'
         WHEN orders <= 3 THEN '2-3 orders'
         WHEN orders <= 6 THEN '4-6 orders'
         ELSE '7+ orders'
    END                                                              AS frequency_band,
    COUNT(*)                                                         AS customers,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders_per_customer), 1) AS pct_customers
FROM orders_per_customer
GROUP BY frequency_band
ORDER BY MIN(orders);

-- @query: a07_east_discount_deep_dive | Why is East unprofitable? Discount vs profit in East
SELECT
    discount_band,
    COUNT(*)                                     AS order_lines,
    ROUND(SUM(sales) / 1e5, 2)                   AS sales_lakh,
    ROUND(SUM(profit) / 1e5, 2)                  AS profit_lakh,
    ROUND(100.0 * SUM(profit) / SUM(sales), 2)   AS margin_pct
FROM sales
WHERE region = 'East'
GROUP BY discount_band
ORDER BY MIN(discount);

-- @query: a08_what_if_discount_cap | What-if: profit if discounts above 20% were capped at 20%
WITH capped AS (
    SELECT
        region,
        profit,
        CASE WHEN discount > 0.20
             THEN profit + sales / (1 - discount) * (discount - 0.20)   -- add back the extra discount
             ELSE profit
        END AS profit_if_capped
    FROM sales
)
SELECT
    region,
    ROUND(SUM(profit) / 1e5, 2)                              AS actual_profit_lakh,
    ROUND(SUM(profit_if_capped) / 1e5, 2)                    AS profit_if_capped_lakh,
    ROUND((SUM(profit_if_capped) - SUM(profit)) / 1e5, 2)    AS uplift_lakh
FROM capped
GROUP BY region
ORDER BY uplift_lakh DESC;
