/* =====================================================================
   03_data_cleaning.sql
   Transforms the raw staging table into the clean `sales` table.
     1. Remove exact duplicates             (SELECT DISTINCT)
     2. Trim spaces / standardise casing    (TRIM + CASE mapping)
     3. Convert DD-MM-YYYY text to ISO dates (SUBSTR)
     4. Drop invalid quantities             (WHERE quantity > 0)
     5. Fill missing customer names         (window MAX over customer_id)
     6. Fill missing ship dates             (order date + MEDIAN days per ship mode)
     7. Add derived columns
   ===================================================================== */

DELETE FROM sales;

INSERT INTO sales
WITH deduped AS (                                    -- step 1
    SELECT DISTINCT * FROM sales_raw
),
standardised AS (                                    -- steps 2, 3, 4
    SELECT
        row_id,
        TRIM(order_id)                                              AS order_id,
        SUBSTR(order_date, 7, 4) || '-' || SUBSTR(order_date, 4, 2) || '-' || SUBSTR(order_date, 1, 2) AS order_date,
        CASE WHEN ship_date IS NULL OR TRIM(ship_date) = '' THEN NULL
             ELSE SUBSTR(ship_date, 7, 4) || '-' || SUBSTR(ship_date, 4, 2) || '-' || SUBSTR(ship_date, 1, 2)
        END                                                          AS ship_date,
        CASE LOWER(TRIM(ship_mode))
             WHEN 'standard class' THEN 'Standard Class'
             WHEN 'second class'   THEN 'Second Class'
             WHEN 'first class'    THEN 'First Class'
             WHEN 'same day'       THEN 'Same Day'
        END                                                          AS ship_mode,
        TRIM(customer_id)                                            AS customer_id,
        NULLIF(TRIM(customer_name), '')                              AS customer_name,
        TRIM(segment)                                                AS segment,
        TRIM(city)                                                   AS city,
        TRIM(state)                                                  AS state,
        UPPER(SUBSTR(TRIM(region), 1, 1)) || LOWER(SUBSTR(TRIM(region), 2)) AS region,
        TRIM(product_id)                                             AS product_id,
        CASE UPPER(TRIM(category))
             WHEN 'TECHNOLOGY'      THEN 'Technology'
             WHEN 'FURNITURE'       THEN 'Furniture'
             WHEN 'OFFICE SUPPLIES' THEN 'Office Supplies'
        END                                                          AS category,
        TRIM(sub_category)                                           AS sub_category,
        TRIM(product_name)                                           AS product_name,
        quantity, unit_price, discount, sales, profit
    FROM deduped
    WHERE quantity > 0
),
ship_days_ranked AS (                                -- median helper for step 6
    SELECT
        ship_mode,
        julianday(ship_date) - julianday(order_date)                         AS days,
        ROW_NUMBER() OVER (PARTITION BY ship_mode
                           ORDER BY julianday(ship_date) - julianday(order_date)) AS rn,
        COUNT(*)     OVER (PARTITION BY ship_mode)                           AS cnt
    FROM standardised
    WHERE ship_date IS NOT NULL
),
median_ship_days AS (
    SELECT ship_mode, AVG(days) AS median_days
    FROM ship_days_ranked
    WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
    GROUP BY ship_mode
),
filled AS (                                          -- steps 5, 6
    SELECT
        s.row_id, s.order_id, s.order_date,
        COALESCE(s.ship_date,
                 DATE(s.order_date, '+' || m.median_days || ' days'))       AS ship_date,
        s.ship_mode, s.customer_id,
        COALESCE(s.customer_name,
                 MAX(s.customer_name) OVER (PARTITION BY s.customer_id),
                 'Unknown Customer')                                         AS customer_name,
        s.segment, s.city, s.state, s.region, s.product_id, s.category,
        s.sub_category, s.product_name, s.quantity, s.unit_price, s.discount,
        s.sales, s.profit
    FROM standardised s
    JOIN median_ship_days m ON m.ship_mode = s.ship_mode
)
SELECT                                               -- step 7
    row_id, order_id, order_date, ship_date, ship_mode, customer_id, customer_name,
    segment, city, state, region, product_id, category, sub_category, product_name,
    quantity, unit_price, discount, sales, profit,
    CAST(STRFTIME('%Y', order_date) AS INTEGER)                              AS order_year,
    CAST(STRFTIME('%m', order_date) AS INTEGER)                              AS order_month,
    'Q' || ((CAST(STRFTIME('%m', order_date) AS INTEGER) + 2) / 3)           AS quarter,
    STRFTIME('%Y-%m', order_date)                                            AS year_month,
    CAST(julianday(ship_date) - julianday(order_date) AS INTEGER)            AS shipping_days,
    ROUND(profit / sales, 4)                                                 AS profit_margin,
    CASE WHEN discount = 0     THEN 'No Discount'
         WHEN discount <= 0.10 THEN '1-10%'
         WHEN discount <= 0.20 THEN '11-20%'
         ELSE 'Above 20%'
    END                                                                      AS discount_band,
    CASE WHEN profit < 0 THEN 1 ELSE 0 END                                   AS is_loss
FROM filled
ORDER BY row_id;

-- @query: clean01_rows_after_cleaning | Row count and remaining nulls after cleaning
SELECT
    COUNT(*)                                                     AS clean_rows,
    SUM(CASE WHEN ship_date     IS NULL THEN 1 ELSE 0 END)       AS null_ship_date,
    SUM(CASE WHEN customer_name IS NULL THEN 1 ELSE 0 END)       AS null_customer_name,
    COUNT(DISTINCT region)                                       AS distinct_regions,
    COUNT(DISTINCT category)                                     AS distinct_categories,
    COUNT(DISTINCT ship_mode)                                    AS distinct_ship_modes
FROM sales;
