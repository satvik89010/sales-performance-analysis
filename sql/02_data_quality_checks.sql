/* =====================================================================
   02_data_quality_checks.sql
   Profiles the RAW staging table before cleaning so every cleaning
   step in 03_data_cleaning.sql is justified by evidence.
   ===================================================================== */

-- @query: dq01_row_count | Total raw rows loaded
SELECT COUNT(*) AS total_rows
FROM sales_raw;

-- @query: dq02_exact_duplicates | Rows that are exact copies of another row
SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM sales_raw)) AS duplicate_rows
FROM sales_raw;

-- @query: dq03_null_counts | Missing values per column (only columns with issues shown)
SELECT
    SUM(CASE WHEN customer_name IS NULL OR TRIM(customer_name) = '' THEN 1 ELSE 0 END) AS null_customer_name,
    SUM(CASE WHEN ship_date     IS NULL OR TRIM(ship_date)     = '' THEN 1 ELSE 0 END) AS null_ship_date,
    SUM(CASE WHEN order_date    IS NULL THEN 1 ELSE 0 END)                             AS null_order_date,
    SUM(CASE WHEN sales         IS NULL THEN 1 ELSE 0 END)                             AS null_sales
FROM sales_raw;

-- @query: dq04_region_spellings | Inconsistent spellings of Region
SELECT '[' || region || ']' AS region_value, COUNT(*) AS row_count
FROM sales_raw
GROUP BY region
ORDER BY row_count DESC;

-- @query: dq05_category_spellings | Inconsistent spellings of Category
SELECT '[' || category || ']' AS category_value, COUNT(*) AS row_count
FROM sales_raw
GROUP BY category
ORDER BY row_count DESC;

-- @query: dq06_invalid_quantity | Rows with zero or negative quantity
SELECT quantity, COUNT(*) AS row_count
FROM sales_raw
WHERE quantity <= 0
GROUP BY quantity;

-- @query: dq07_date_format_sample | Dates are stored as DD-MM-YYYY text
SELECT order_date, ship_date
FROM sales_raw
LIMIT 5;
