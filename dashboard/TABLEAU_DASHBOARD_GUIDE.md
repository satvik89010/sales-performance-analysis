# Tableau Dashboard — Step-by-Step Build Guide

This guide rebuilds the **Sales Performance Dashboard** in **Tableau Public (free)** using
`data/processed/sales_clean.csv`. It takes about 45–60 minutes. Once published, add the
Tableau Public link to the top of the README and to your LinkedIn post.

> Tableau workbooks (`.twbx`) can only be created inside Tableau, so this repository provides the
> clean data, the calculated fields and the exact layout. The numbers you see should match
> `outputs/SQL_RESULTS.md` (for example: Total Sales ₹22.16 Cr, Profit ₹2.01 Cr, Margin 9.09%).

---

## 1. Connect to the data
1. Download **Tableau Public** → https://public.tableau.com/app/discover (free sign-up).
2. **Connect → Text file →** `data/processed/sales_clean.csv`.
3. On the Data Source page, check the data types:
   - `Order Date`, `Ship Date` → **Date**
   - `Order Year` → change to **String** (so it doesn't get summed) or drag it as a Dimension
   - `Discount`, `Profit Margin` → Number (decimal)
4. Rename the data source to **Sales**.

## 2. Calculated fields
Create these via **Analysis → Create Calculated Field**:

| Name | Formula |
|------|---------|
| `Profit Margin %` | `SUM([Profit]) / SUM([Sales])` |
| `Orders` | `COUNTD([Order ID])` |
| `Customers` | `COUNTD([Customer ID])` |
| `Avg Order Value` | `SUM([Sales]) / COUNTD([Order ID])` |
| `Sales (Lakh)` | `SUM([Sales]) / 100000` |
| `Profit (Lakh)` | `SUM([Profit]) / 100000` |
| `Profit / Loss` | `IF SUM([Profit]) >= 0 THEN "Profit" ELSE "Loss" END` |
| `Sales YoY %` | `(SUM([Sales]) - LOOKUP(SUM([Sales]), -1)) / ABS(LOOKUP(SUM([Sales]), -1))` |
| `Loss Lines %` | `SUM(IF [Profit] < 0 THEN 1 ELSE 0 END) / COUNT([Row ID])` |

**Parameter (metric switcher)**
1. Create Parameter → Name `Select Metric`, Data type *String*, List: `Sales`, `Profit`.
2. Calculated field `Selected Metric`:
   ```
   CASE [Select Metric]
       WHEN "Sales"  THEN SUM([Sales])
       WHEN "Profit" THEN SUM([Profit])
   END
   ```
3. Right-click the parameter → **Show Parameter**.

## 3. Build the sheets

| # | Sheet name | Columns | Rows | Marks / Colour | Notes |
|---|-----------|---------|------|----------------|-------|
| 1 | **KPI – Sales** | – | – | Text: `SUM(Sales)` | Format as ₹ Crore: `Sales / 10000000`, 2 decimals, prefix "₹", suffix " Cr" |
| 2 | **KPI – Profit** | – | – | Text: `SUM(Profit)` | Same formatting |
| 3 | **KPI – Margin** | – | – | Text: `Profit Margin %` | Format → Percentage, 1 decimal |
| 4 | **KPI – Orders** | – | – | Text: `Orders` | |
| 5 | **Monthly Trend** | `MONTH(Order Date)` (continuous, green pill) | `Selected Metric` | Line | Add a trend line: Analytics pane → Trend Line |
| 6 | **Category & Sub-Category** | `Sales (Lakh)` | `Category`, `Sub-Category` | Bar; Colour: `Profit Margin %` (red-blue diverging, centre 0) | Sort descending by Sales |
| 7 | **Region Map** | `Longitude` (generated) | `Latitude` (generated) | Map: drag `State`; Colour: `Profit Margin %` | Set *Map → Edit Locations → Country = India* |
| 8 | **Region Performance** | `Region` | `Sales (Lakh)` + `Profit Margin %` (dual axis) | Bar + Line | Right-click 2nd axis → Dual Axis |
| 9 | **Discount Impact** | `Discount Band` | `Profit Margin %` | Bar; Colour: `Profit / Loss` (Loss = red) | Sort manually: No Discount, 1-10%, 11-20%, Above 20% |
| 10 | **Top 10 Customers** | `Sales (Lakh)` | `Customer Name` | Bar | Filter: Customer Name → Top 10 by SUM(Sales) |
| 11 | **Segment Share** | – | – | Pie: Angle `SUM(Sales)`, Colour `Segment` | Label: percent of total (Quick Table Calc) |

## 4. Assemble the dashboard
1. **New Dashboard** → Size: *Automatic* (or Fixed 1400 × 900).
2. Layout (top to bottom):
   - **Title bar** (Text object, navy `#1F4E79` background, white text): *ShopEase India — Sales Performance Dashboard 2022–2025*
   - **KPI row**: sheets 1–4 in a Horizontal container.
   - **Row 2**: Monthly Trend (left, 60%) + Segment Share (right, 40%).
   - **Row 3**: Category & Sub-Category (left) + Region Map (right).
   - **Row 4**: Discount Impact (left) + Top 10 Customers (right).
3. **Filters** — add `Order Year`, `Region`, `Segment` and `Category` as filters →
   click each filter's ▼ → *Apply to Worksheets → All Using This Data Source* →
   show them as **Single Value (dropdown)**.
4. **Interactivity** — on the Region Map click the funnel icon (*Use as Filter*), so clicking a
   state filters the whole dashboard.
5. Colours: primary `#1F4E79`, secondary `#5B9BD5`, loss `#C0392B`.
6. Add tooltips with Sales, Profit and Margin to every chart.

## 5. Publish
1. **File → Save to Tableau Public As…** → name it `Sales Performance Dashboard – Satvik Mansotra`.
2. Open the published page → **Share** → copy the link.
3. Take a screenshot → save it as `images/tableau_dashboard.png` in this repo.
4. Add both to the README (a placeholder line is already there).

## 6. Checks — your dashboard should show
| Filter | Total Sales | Total Profit | Margin |
|--------|-------------|--------------|--------|
| All years, all regions | ₹22.16 Cr | ₹2.01 Cr | 9.1% |
| 2025 | ₹6.21 Cr | ₹0.57 Cr | 9.2% |
| Region = East | ₹3.40 Cr | −₹0.06 Cr | −1.8% |
| 2024 + East | ₹0.95 Cr | −₹0.03 Cr | −3.5% |
