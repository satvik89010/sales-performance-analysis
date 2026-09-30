"""
build_excel_dashboard.py
------------------------
Builds dashboard/Sales_Dashboard.xlsx from the clean data:

  * Data       - clean order lines, formatted as an Excel Table with filters
  * Analysis   - summary tables driven by SUMIFS / COUNTIFS / AVERAGEIFS formulas
  * Dashboard  - KPI cards + 6 charts, with Year and Region drop-down filters

Every number on the Dashboard and Analysis sheets is a live formula, so changing
the Year / Region drop-down recalculates the whole dashboard.

Run:  python scripts/build_excel_dashboard.py
"""

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "processed" / "sales_clean.csv"
OUT = ROOT / "dashboard" / "Sales_Dashboard.xlsx"

NAVY, BLUE, LIGHT, WHITE, GREY = "1F4E79", "5B9BD5", "DDEBF7", "FFFFFF", "595959"
FONT = "Arial"
thin = Side(style="thin", color="BFBFBF")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

DATA_COLS = ["Order ID", "Order Date", "Order Year", "Order Month", "Month Name", "Quarter",
             "Customer Name", "Segment", "City", "State", "Region", "Category", "Sub-Category",
             "Product Name", "Quantity", "Discount", "Sales", "Profit", "Discount Band"]


def value_labels(num_fmt):
    """Data labels that show only the value (no series / category name)."""
    return DataLabelList(showVal=True, showSerName=False, showCatName=False,
                         showLegendKey=False, showPercent=False, numFmt=num_fmt)


def style_header(cell):
    cell.font = Font(name=FONT, bold=True, color=WHITE)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = BOX


def main() -> None:
    df = pd.read_csv(CLEAN, parse_dates=["Order Date"])[DATA_COLS]
    n = len(df)
    last = n + 1  # last data row in Excel

    wb = Workbook()
    dash = wb.active
    dash.title = "Dashboard"
    ana = wb.create_sheet("Analysis")
    data = wb.create_sheet("Data")

    # ------------------------------------------------------------------ Data
    for j, col in enumerate(DATA_COLS, start=1):
        style_header(data.cell(row=1, column=j, value=col))
    for i, row in enumerate(df.itertuples(index=False), start=2):
        for j, val in enumerate(row, start=1):
            if isinstance(val, pd.Timestamp):
                val = val.to_pydatetime()
            data.cell(row=i, column=j, value=val)
    col_idx = {c: get_column_letter(i) for i, c in enumerate(DATA_COLS, start=1)}
    for i in range(2, last + 1):
        data[f"{col_idx['Order Date']}{i}"].number_format = "dd-mmm-yyyy"
        data[f"{col_idx['Discount']}{i}"].number_format = "0%"
        data[f"{col_idx['Sales']}{i}"].number_format = "#,##0.00"
        data[f"{col_idx['Profit']}{i}"].number_format = "#,##0.00"
    widths = {"Order ID": 16, "Order Date": 13, "Customer Name": 20, "Product Name": 28,
              "Sub-Category": 16, "Category": 15, "Discount Band": 13, "State": 15}
    for c, letter in col_idx.items():
        data.column_dimensions[letter].width = widths.get(c, 12)
    table = Table(displayName="SalesData", ref=f"A1:{get_column_letter(len(DATA_COLS))}{last}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    data.add_table(table)
    data.freeze_panes = "A2"

    def rng(col):
        c = col_idx[col]
        return f"Data!${c}$2:${c}${last}"

    SALES, PROFIT, YEAR, REGION = rng("Sales"), rng("Profit"), rng("Order Year"), rng("Region")
    QTY, DISC = rng("Quantity"), rng("Discount")
    FILTERS = f"{YEAR},Analysis!$C$3,{REGION},Analysis!$C$4"   # appended to every SUMIFS

    # -------------------------------------------------------------- Analysis
    ana["A1"] = "Analysis tables (feed the Dashboard charts) - all values are live formulas"
    ana["A1"].font = Font(name=FONT, bold=True, size=13, color=NAVY)
    ana["A3"], ana["A4"] = "Year criteria", "Region criteria"
    ana["C3"] = '=IF(Dashboard!$D$4="All",">0",Dashboard!$D$4)'
    ana["C4"] = '=IF(Dashboard!$H$4="All","*",Dashboard!$H$4)'
    ana["E3"] = "Helper cells translate the Dashboard drop-downs into SUMIFS criteria (\"All\" = match everything)."
    ana["E3"].font = Font(name=FONT, italic=True, color=GREY)

    def table_block(top, left, title, headers, labels, formulas, fmts):
        """Write a small titled table. formulas: list of functions label_cell -> formula."""
        c0 = left
        ana.cell(row=top, column=c0, value=title).font = Font(name=FONT, bold=True, color=NAVY, size=11)
        for j, h in enumerate(headers):
            style_header(ana.cell(row=top + 1, column=c0 + j, value=h))
        for i, lab in enumerate(labels):
            r = top + 2 + i
            lc = ana.cell(row=r, column=c0, value=lab)
            lc.border = BOX
            lc.font = Font(name=FONT)
            ref = f"${get_column_letter(c0)}{r}"
            for j, (f, fmt) in enumerate(zip(formulas, fmts), start=1):
                cell = ana.cell(row=r, column=c0 + j, value=f(ref, r))
                cell.number_format = fmt
                cell.border = BOX
                cell.font = Font(name=FONT)
        return top + 2, top + 1 + len(labels)   # first & last data rows

    L = "#,##0.00"   # lakh format
    P = "0.0%"

    # Monthly trend
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    MONTH = rng("Month Name")
    m_first, m_last = table_block(
        6, 1, "Monthly sales & profit", ["Month", "Sales (Rs Lakh)", "Profit (Rs Lakh)"], months,
        [lambda ref, r: f"=SUMIFS({SALES},{MONTH},{ref},{FILTERS})/100000",
         lambda ref, r: f"=SUMIFS({PROFIT},{MONTH},{ref},{FILTERS})/100000"], [L, L])

    # Category
    CAT = rng("Category")
    cats = ["Technology", "Furniture", "Office Supplies"]
    c_first, c_last = table_block(
        6, 5, "Category performance", ["Category", "Sales (Rs Lakh)", "Profit (Rs Lakh)", "Margin %"], cats,
        [lambda ref, r: f"=SUMIFS({SALES},{CAT},{ref},{FILTERS})/100000",
         lambda ref, r: f"=SUMIFS({PROFIT},{CAT},{ref},{FILTERS})/100000",
         lambda ref, r: f"=IFERROR(G{r}/F{r},0)"], [L, L, P])

    # Region (region filter intentionally NOT applied so all regions can be compared)
    regions = ["North", "South", "West", "East"]
    YEAR_ONLY = f"{YEAR},Analysis!$C$3"
    r_first, r_last = table_block(
        12, 5, "Region performance (year filter only)",
        ["Region", "Sales (Rs Lakh)", "Profit (Rs Lakh)", "Margin %", "Avg Discount"], regions,
        [lambda ref, r: f"=SUMIFS({SALES},{REGION},{ref},{YEAR_ONLY})/100000",
         lambda ref, r: f"=SUMIFS({PROFIT},{REGION},{ref},{YEAR_ONLY})/100000",
         lambda ref, r: f"=IFERROR(G{r}/F{r},0)",
         lambda ref, r: f"=IFERROR(AVERAGEIFS({DISC},{REGION},{ref},{YEAR_ONLY}),0)"], [L, L, P, P])

    # Sub-category
    SUB = rng("Sub-Category")
    subs = sorted(pd.read_csv(CLEAN)["Sub-Category"].unique())
    s_first, s_last = table_block(
        20, 1, "Sub-category profit", ["Sub-Category", "Sales (Rs Lakh)", "Profit (Rs Lakh)", "Margin %"], subs,
        [lambda ref, r: f"=SUMIFS({SALES},{SUB},{ref},{FILTERS})/100000",
         lambda ref, r: f"=SUMIFS({PROFIT},{SUB},{ref},{FILTERS})/100000",
         lambda ref, r: f"=IFERROR(C{r}/B{r},0)"], [L, L, P])

    # Discount band
    BAND = rng("Discount Band")
    bands = ["No Discount", "1-10%", "11-20%", "Above 20%"]
    d_first, d_last = table_block(
        20, 6, "Discount impact", ["Discount Band", "Sales (Rs Lakh)", "Profit (Rs Lakh)", "Margin %"], bands,
        [lambda ref, r: f"=SUMIFS({SALES},{BAND},{ref},{FILTERS})/100000",
         lambda ref, r: f"=SUMIFS({PROFIT},{BAND},{ref},{FILTERS})/100000",
         lambda ref, r: f"=IFERROR(H{r}/G{r},0)"], [L, L, P])

    # Segment
    SEG = rng("Segment")
    segs = ["Consumer", "Corporate", "Home Office"]
    g_first, g_last = table_block(
        28, 6, "Segment share", ["Segment", "Sales (Rs Lakh)"], segs,
        [lambda ref, r: f"=SUMIFS({SALES},{SEG},{ref},{FILTERS})/100000"], [L])

    # Year x Category pivot (no filters - full history)
    ana.cell(row=35, column=6, value="Year x Category sales (Rs Lakh) - pivot view").font = \
        Font(name=FONT, bold=True, color=NAVY, size=11)
    style_header(ana.cell(row=36, column=6, value="Year"))
    for j, c in enumerate(cats + ["Total"], start=7):
        style_header(ana.cell(row=36, column=j, value=c))
    for i, yr in enumerate([2022, 2023, 2024, 2025], start=37):
        ana.cell(row=i, column=6, value=yr).border = BOX
        for j, c in enumerate(cats, start=7):
            cell = ana.cell(row=i, column=j,
                            value=f"=SUMIFS({SALES},{YEAR},$F{i},{CAT},{get_column_letter(j)}$36)/100000")
            cell.number_format, cell.border = L, BOX
        tot = ana.cell(row=i, column=10, value=f"=SUM(G{i}:I{i})")
        tot.number_format, tot.border, tot.font = L, BOX, Font(name=FONT, bold=True)

    for col, w in zip("ABCDEFGHIJ", [16, 15, 15, 12, 18, 15, 15, 15, 13, 13]):
        ana.column_dimensions[col].width = w

    # ------------------------------------------------------------- Dashboard
    dash.sheet_view.showGridLines = False
    for col in range(1, 20):
        dash.column_dimensions[get_column_letter(col)].width = 9.5
    dash.column_dimensions["A"].width = 2

    dash.merge_cells("B1:Q2")
    dash["B1"] = "ShopEase India  |  Sales Performance Dashboard (2022 - 2025)"
    dash["B1"].font = Font(name=FONT, bold=True, size=20, color=WHITE)
    dash["B1"].fill = PatternFill("solid", fgColor=NAVY)
    dash["B1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)

    dash["B4"], dash["F4"] = "Year:", "Region:"
    for ref in ("B4", "F4"):
        dash[ref].font = Font(name=FONT, bold=True, color=NAVY)
        dash[ref].alignment = Alignment(horizontal="right")
    for ref, default in (("D4", "All"), ("H4", "All")):
        dash[ref] = default
        dash[ref].fill = PatternFill("solid", fgColor="FFF2CC")
        dash[ref].font = Font(name=FONT, bold=True)
        dash[ref].border = BOX
        dash[ref].alignment = Alignment(horizontal="center")
    dash.merge_cells("J4:Q4")
    dash["J4"] = "<- Pick a Year and Region from the yellow drop-downs; every KPI and chart updates."
    dash["J4"].font = Font(name=FONT, italic=True, color=GREY, size=9)

    dv_year = DataValidation(type="list", formula1='"All,2022,2023,2024,2025"', allow_blank=False)
    dv_region = DataValidation(type="list", formula1='"All,North,South,West,East"', allow_blank=False)
    dash.add_data_validation(dv_year)
    dash.add_data_validation(dv_region)
    dv_year.add("D4")
    dv_region.add("H4")

    kpis = [
        ("TOTAL SALES", f"=SUMIFS({SALES},{FILTERS})/10000000", '"Rs "0.00" Cr"'),
        ("TOTAL PROFIT", f"=SUMIFS({PROFIT},{FILTERS})/10000000", '"Rs "0.00" Cr"'),
        ("PROFIT MARGIN", f"=IFERROR(SUMIFS({PROFIT},{FILTERS})/SUMIFS({SALES},{FILTERS}),0)", "0.0%"),
        ("UNITS SOLD", f"=SUMIFS({QTY},{FILTERS})", "#,##0"),
        ("AVG DISCOUNT", f"=IFERROR(AVERAGEIFS({DISC},{FILTERS}),0)", "0.0%"),
    ]
    for k, (label, formula, fmt) in enumerate(kpis):
        c1 = 2 + k * 3
        c2 = c1 + 2
        L1, L2 = get_column_letter(c1), get_column_letter(c2)
        dash.merge_cells(f"{L1}6:{L2}6")
        dash.merge_cells(f"{L1}7:{L2}8")
        head = dash[f"{L1}6"]
        head.value = label
        head.font = Font(name=FONT, bold=True, size=9, color=WHITE)
        head.fill = PatternFill("solid", fgColor=BLUE)
        head.alignment = Alignment(horizontal="center", vertical="center")
        val = dash[f"{L1}7"]
        val.value = formula
        val.number_format = fmt
        val.font = Font(name=FONT, bold=True, size=18, color=NAVY)
        val.fill = PatternFill("solid", fgColor=LIGHT)
        val.alignment = Alignment(horizontal="center", vertical="center")
        for r in (6, 7, 8):
            for c in range(c1, c2 + 1):
                dash.cell(row=r, column=c).border = BOX
                if r > 6:
                    dash.cell(row=r, column=c).fill = PatternFill("solid", fgColor=LIGHT)

    def place(chart, anchor, w=15.5, h=7.2):
        chart.width, chart.height = w, h
        if chart.legend is not None:
            chart.legend.position = "b"
        dash.add_chart(chart, anchor)

    # 1. Monthly trend (line)
    ch = LineChart()
    ch.title = "Monthly Sales & Profit (Rs Lakh)"
    ch.add_data(Reference(ana, min_col=2, max_col=3, min_row=m_first - 1, max_row=m_last), titles_from_data=True)
    ch.set_categories(Reference(ana, min_col=1, min_row=m_first, max_row=m_last))
    for series in ch.series:
        series.smooth = False
    ch.y_axis.numFmt = "#,##0"
    ch.y_axis.majorGridlines = None
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    place(ch, "B10")

    # 2. Category (clustered bar)
    ch = BarChart()
    ch.type = "col"
    ch.title = "Sales vs Profit by Category (Rs Lakh)"
    ch.add_data(Reference(ana, min_col=6, max_col=7, min_row=c_first - 1, max_row=c_last), titles_from_data=True)
    ch.set_categories(Reference(ana, min_col=5, min_row=c_first, max_row=c_last))
    ch.y_axis.numFmt = "#,##0"
    ch.y_axis.majorGridlines = None
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    place(ch, "K10")

    # 3. Region margin
    ch = BarChart()
    ch.type = "col"
    ch.title = "Profit Margin by Region"
    ch.add_data(Reference(ana, min_col=8, min_row=r_first - 1, max_row=r_last), titles_from_data=True)
    ch.set_categories(Reference(ana, min_col=5, min_row=r_first, max_row=r_last))
    ch.y_axis.numFmt = "0%"
    ch.y_axis.majorGridlines = None
    ch.legend = None
    ch.dataLabels = value_labels("0.0%")
    ch.x_axis.tickLblPos = "low"
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    place(ch, "B25")

    # 4. Sub-category profit (horizontal bar)
    ch = BarChart()
    ch.type = "bar"
    ch.title = "Profit by Sub-Category (Rs Lakh)"
    ch.add_data(Reference(ana, min_col=3, min_row=s_first - 1, max_row=s_last), titles_from_data=True)
    ch.set_categories(Reference(ana, min_col=1, min_row=s_first, max_row=s_last))
    ch.y_axis.numFmt = "#,##0"
    ch.y_axis.majorGridlines = None
    ch.x_axis.tickLblPos = "low"
    ch.legend = None
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    place(ch, "K25")

    # 5. Discount band margin
    ch = BarChart()
    ch.type = "col"
    ch.title = "Profit Margin by Discount Band"
    ch.add_data(Reference(ana, min_col=9, min_row=d_first - 1, max_row=d_last), titles_from_data=True)
    ch.set_categories(Reference(ana, min_col=6, min_row=d_first, max_row=d_last))
    ch.y_axis.numFmt = "0%"
    ch.y_axis.majorGridlines = None
    ch.legend = None
    ch.dataLabels = value_labels("0.0%")
    ch.x_axis.tickLblPos = "low"
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    place(ch, "B40")

    # 6. Segment share (pie)
    ch = PieChart()
    ch.title = "Sales Share by Segment"
    ch.add_data(Reference(ana, min_col=7, min_row=g_first - 1, max_row=g_last), titles_from_data=True)
    ch.set_categories(Reference(ana, min_col=6, min_row=g_first, max_row=g_last))
    ch.dataLabels = DataLabelList(showPercent=True, showVal=False, showCatName=False,
                                  showSerName=False, showLegendKey=False)
    place(ch, "K40")

    # Insights box
    dash.merge_cells("B56:Q56")
    dash["B56"] = "KEY INSIGHTS"
    dash["B56"].font = Font(name=FONT, bold=True, color=WHITE)
    dash["B56"].fill = PatternFill("solid", fgColor=NAVY)
    insights = [
        "1. Sales grew every year (Rs 4.86 Cr in 2022 to Rs 6.21 Cr in 2025) but profit fell 1.2% in 2023.",
        "2. Oct-Nov (festive season) and March (financial-year end) are the peak months; February is the weakest.",
        "3. Tables are the only loss-making sub-category (-9.2% margin) because of ~17.5% average discounts.",
        "4. East region runs at a -1.9% margin with 17.9% average discount vs 5-7% elsewhere.",
        "5. Discounts above 10% make margins negative; capping discounts at 20% adds ~Rs 23 Lakh profit.",
    ]
    for i, text in enumerate(insights, start=57):
        dash.merge_cells(f"B{i}:Q{i}")
        dash[f"B{i}"] = text
        dash[f"B{i}"].font = Font(name=FONT, size=10)
        dash[f"B{i}"].fill = PatternFill("solid", fgColor=LIGHT)

    for ws in (dash, ana):
        for row in ws.iter_rows():
            for cell in row:
                if cell.font and cell.font.name != FONT:
                    f = cell.font
                    cell.font = Font(name=FONT, bold=f.bold, italic=f.italic, size=f.size, color=f.color)

    wb.calculation.fullCalcOnLoad = True   # Excel computes every formula when the file opens
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"Excel dashboard written -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
