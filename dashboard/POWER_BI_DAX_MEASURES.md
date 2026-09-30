# Power BI Version — Data Model & DAX Measures

An optional Power BI version of the Sales dashboard (uses the same clean data).
Import `data/processed/sales_clean.csv` → **Get Data → Text/CSV**. The table will be named
`sales_clean`.

## 1. Date table (Modeling → New Table)
```DAX
Calendar =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2022, 1, 1 ), DATE ( 2025, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Month No", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM" ),
    "Quarter", "Q" & QUARTER ( [Date] ),
    "Year-Month", FORMAT ( [Date], "YYYY-MM" )
)
```
- Mark it as a date table: *Table tools → Mark as date table → Date*.
- Sort `Month` by `Month No` (*Column tools → Sort by column*).
- Relationship: `Calendar[Date]` 1 → * `sales_clean[Order Date]`.

## 2. Measures (create a blank table called `_Measures` to hold them)
```DAX
Total Sales      = SUM ( sales_clean[Sales] )
Total Profit     = SUM ( sales_clean[Profit] )
Profit Margin %  = DIVIDE ( [Total Profit], [Total Sales] )
Total Orders     = DISTINCTCOUNT ( sales_clean[Order ID] )
Total Customers  = DISTINCTCOUNT ( sales_clean[Customer ID] )
Units Sold       = SUM ( sales_clean[Quantity] )
Avg Order Value  = DIVIDE ( [Total Sales], [Total Orders] )
Avg Discount %   = AVERAGE ( sales_clean[Discount] )

Sales LY         = CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( 'Calendar'[Date] ) )
Sales YoY %      = DIVIDE ( [Total Sales] - [Sales LY], [Sales LY] )
Profit LY        = CALCULATE ( [Total Profit], SAMEPERIODLASTYEAR ( 'Calendar'[Date] ) )
Profit YoY %     = DIVIDE ( [Total Profit] - [Profit LY], [Profit LY] )
Sales YTD        = TOTALYTD ( [Total Sales], 'Calendar'[Date] )

Loss Lines %     =
DIVIDE (
    CALCULATE ( COUNTROWS ( sales_clean ), sales_clean[Profit] < 0 ),
    COUNTROWS ( sales_clean )
)

Profit if Discount Capped at 20% =
SUMX (
    sales_clean,
    IF (
        sales_clean[Discount] > 0.2,
        sales_clean[Profit]
            + DIVIDE ( sales_clean[Sales], 1 - sales_clean[Discount] ) * ( sales_clean[Discount] - 0.2 ),
        sales_clean[Profit]
    )
)

Discount Cap Uplift = [Profit if Discount Capped at 20%] - [Total Profit]

Margin Colour =
IF ( [Profit Margin %] < 0, "#C0392B", "#1F4E79" )
```
Use `Margin Colour` for conditional formatting: *Format visual → Columns → fx → Field value*.

## 3. Report layout
| Visual | Fields |
|--------|--------|
| 5 KPI **Cards** | Total Sales, Total Profit, Profit Margin %, Total Orders, Sales YoY % |
| **Line chart** | X: `Calendar[Year-Month]` · Y: Total Sales, Total Profit |
| **Clustered bar** | Y: `Sub-Category` · X: Total Profit (colour by `Margin Colour`) |
| **Filled map** | Location: `State` · Colour saturation: Profit Margin % |
| **Column chart** | X: `Discount Band` · Y: Profit Margin % |
| **Donut** | Legend: `Segment` · Values: Total Sales |
| **Table** | Top 10 customers (Filter pane → Top N = 10 by Total Sales) |
| **Slicers** | `Calendar[Year]`, `Region`, `Category`, `Segment` |

Expected totals (no filters): Total Sales ₹22.16 Cr · Total Profit ₹2.01 Cr · Margin 9.09% ·
Orders 5,198 · Discount Cap Uplift ≈ ₹23.2 Lakh.
