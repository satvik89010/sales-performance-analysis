/* =====================================================================
   01_create_tables.sql
   Creates the clean, typed `sales` table that the cleaning script loads.
   (The raw staging table `sales_raw` is loaded as-is from
    data/raw/sales_raw.csv by scripts/run_sql.py.)
   Dialect: SQLite 3.25+  (see README for MySQL / PostgreSQL notes)
   ===================================================================== */

DROP TABLE IF EXISTS sales;

CREATE TABLE sales (
    row_id          INTEGER PRIMARY KEY,
    order_id        TEXT    NOT NULL,
    order_date      DATE    NOT NULL,
    ship_date       DATE    NOT NULL,
    ship_mode       TEXT    NOT NULL,
    customer_id     TEXT    NOT NULL,
    customer_name   TEXT    NOT NULL,
    segment         TEXT    NOT NULL,
    city            TEXT    NOT NULL,
    state           TEXT    NOT NULL,
    region          TEXT    NOT NULL,
    product_id      TEXT    NOT NULL,
    category        TEXT    NOT NULL,
    sub_category    TEXT    NOT NULL,
    product_name    TEXT    NOT NULL,
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      REAL    NOT NULL,
    discount        REAL    NOT NULL CHECK (discount BETWEEN 0 AND 1),
    sales           REAL    NOT NULL,
    profit          REAL    NOT NULL,
    -- derived columns
    order_year      INTEGER NOT NULL,
    order_month     INTEGER NOT NULL,
    quarter         TEXT    NOT NULL,
    year_month      TEXT    NOT NULL,
    shipping_days   INTEGER NOT NULL,
    profit_margin   REAL    NOT NULL,
    discount_band   TEXT    NOT NULL,
    is_loss         INTEGER NOT NULL
);

CREATE INDEX idx_sales_order_date ON sales (order_date);
CREATE INDEX idx_sales_region     ON sales (region);
CREATE INDEX idx_sales_category   ON sales (category, sub_category);
CREATE INDEX idx_sales_customer   ON sales (customer_id);
