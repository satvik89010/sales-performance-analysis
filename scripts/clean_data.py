"""
clean_data.py
-------------
Cleans the raw sales file and produces an analysis-ready dataset.

Steps
  1. Remove exact duplicate rows
  2. Standardise text columns (trim spaces, fix casing)
  3. Parse DD-MM-YYYY dates into real dates
  4. Remove invalid rows (quantity <= 0)
  5. Handle missing values
       - Customer Name  -> looked up from other orders of the same Customer ID
       - Ship Date      -> Order Date + median shipping days for that Ship Mode
  6. Add derived columns (year, month, quarter, shipping days, profit margin, ...)
  7. Validate the result and save

Run:  python scripts/clean_data.py
Output: data/processed/sales_clean.csv
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "sales_raw.csv"
OUT = ROOT / "data" / "processed" / "sales_clean.csv"


def log(step: str, before: int, after: int) -> None:
    print(f"  {step:<45} {before:>6,} -> {after:>6,} rows")


def main() -> pd.DataFrame:
    df = pd.read_csv(RAW)
    print(f"Loaded raw data: {len(df):,} rows, {df.shape[1]} columns\n")

    # 1. Exact duplicates ---------------------------------------------------
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    log("1. Removed exact duplicate rows", before, len(df))

    # 2. Standardise text ---------------------------------------------------
    text_cols = ["Ship Mode", "Customer Name", "Segment", "City", "State",
                 "Region", "Category", "Sub-Category", "Product Name"]
    for col in text_cols:
        df[col] = df[col].str.strip().str.replace(r"\s+", " ", regex=True)
    df["Region"] = df["Region"].str.title()
    df["Ship Mode"] = df["Ship Mode"].str.title()
    df["Category"] = df["Category"].str.title()
    log("2. Standardised text columns", len(df), len(df))

    # 3. Dates ---------------------------------------------------------------
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d-%m-%Y")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%d-%m-%Y")
    log("3. Converted DD-MM-YYYY text to dates", len(df), len(df))
    # 4. Invalid quantities ----------------------------------------------------
    before = len(df)
    df = df[df["Quantity"] > 0].reset_index(drop=True)
    log("4. Removed rows with quantity <= 0", before, len(df))

    # 5. Missing values --------------------------------------------------------
    missing_names = int(df["Customer Name"].isna().sum())
    name_lookup = (df.dropna(subset=["Customer Name"])
                     .groupby("Customer ID")["Customer Name"].first())
    df["Customer Name"] = df["Customer Name"].fillna(df["Customer ID"].map(name_lookup))
    df["Customer Name"] = df["Customer Name"].fillna("Unknown Customer")

    missing_ship = int(df["Ship Date"].isna().sum())
    ship_days = (df["Ship Date"] - df["Order Date"]).dt.days
    median_days = ship_days.groupby(df["Ship Mode"]).median()
    fill = df["Order Date"] + pd.to_timedelta(df["Ship Mode"].map(median_days), unit="D")
    df["Ship Date"] = df["Ship Date"].fillna(fill)
    print(f"  5. Filled missing values: {missing_names} customer names, {missing_ship} ship dates")

    # 6. Derived columns ---------------------------------------------------------
    df["Order Year"] = df["Order Date"].dt.year
    df["Order Month"] = df["Order Date"].dt.month
    df["Month Name"] = df["Order Date"].dt.strftime("%b")
    df["Quarter"] = "Q" + df["Order Date"].dt.quarter.astype(str)
    df["Year-Month"] = df["Order Date"].dt.strftime("%Y-%m")
    df["Shipping Days"] = (df["Ship Date"] - df["Order Date"]).dt.days
    df["Profit Margin"] = (df["Profit"] / df["Sales"]).round(4)
    df["Discount Band"] = pd.cut(df["Discount"], bins=[-0.01, 0, 0.10, 0.20, 1.0],
                                 labels=["No Discount", "1-10%", "11-20%", "Above 20%"]).astype(str)
    df["Is Loss"] = (df["Profit"] < 0).astype(int)

    # 7. Validation -------------------------------------------------------------
    assert df.isna().sum().sum() == 0, "Nulls remain after cleaning"
    assert not df.duplicated().any(), "Duplicates remain after cleaning"
    assert (df["Quantity"] > 0).all()
    assert (df["Shipping Days"] >= 0).all()
    assert set(df["Region"]) == {"North", "South", "East", "West"}
    assert set(df["Category"]) == {"Technology", "Furniture", "Office Supplies"}

    df["Order Date"] = df["Order Date"].dt.strftime("%Y-%m-%d")
    df["Ship Date"] = df["Ship Date"].dt.strftime("%Y-%m-%d")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nAll validation checks passed.")
    print(f"Clean data written -> {OUT.relative_to(ROOT)}  ({len(df):,} rows, {df.shape[1]} columns)")
    return df


if __name__ == "__main__":
    main()
