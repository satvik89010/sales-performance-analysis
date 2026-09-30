"""
generate_data.py
----------------
Generates the raw dataset used in this project: 4 years (2022-2025) of order-line
data for a fictional Indian office-products and electronics retailer ("ShopEase India").

The data is synthetic but modelled on realistic retail behaviour:
  * year-on-year growth and a festive-season (Diwali) peak in Oct-Nov
  * a March spike from corporate financial-year-end buying
  * heavier discounting in some regions, which erodes profit
  * category-specific margins (Furniture tables often sell at a loss)

To make the cleaning step realistic, the raw file intentionally contains
data-quality problems: duplicate rows, inconsistent text casing / extra spaces,
missing values, invalid quantities and dates stored as DD-MM-YYYY text.

Run:  python scripts/generate_data.py
Output: data/raw/sales_raw.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = ROOT / "data" / "raw" / "sales_raw.csv"

# --------------------------------------------------------------------------
# 1. Reference data
# --------------------------------------------------------------------------
# (city, state, region, weight)
CITIES = [
    ("New Delhi", "Delhi", "North", 10), ("Gurugram", "Haryana", "North", 7),
    ("Chandigarh", "Chandigarh", "North", 3), ("Jaipur", "Rajasthan", "North", 4),
    ("Lucknow", "Uttar Pradesh", "North", 4),
    ("Bengaluru", "Karnataka", "South", 10), ("Chennai", "Tamil Nadu", "South", 7),
    ("Hyderabad", "Telangana", "South", 7), ("Kochi", "Kerala", "South", 3),
    ("Mumbai", "Maharashtra", "West", 11), ("Pune", "Maharashtra", "West", 6),
    ("Ahmedabad", "Gujarat", "West", 5), ("Indore", "Madhya Pradesh", "West", 3),
    ("Kolkata", "West Bengal", "East", 7), ("Bhubaneswar", "Odisha", "East", 3),
    ("Patna", "Bihar", "East", 3), ("Guwahati", "Assam", "East", 2),
]

# (category, sub_category, [product names], price range INR, base gross margin)
CATALOG = [
    ("Technology", "Phones", ["Samsung Galaxy M34", "Redmi Note 13", "OnePlus Nord CE3",
                              "Realme Narzo 60", "Motorola G54"], (11000, 24000), 0.16),
    ("Technology", "Laptops", ["HP 15s Ryzen 5", "Lenovo IdeaPad Slim 3", "Dell Inspiron 3520",
                               "ASUS Vivobook 15", "Acer Aspire Lite"], (38000, 68000), 0.12),
    ("Technology", "Accessories", ["Logitech Wireless Mouse", "boAt Rockerz Headphones",
                                   "SanDisk 128GB Pen Drive", "Zebronics Keyboard",
                                   "Portronics Power Bank"], (450, 2600), 0.34),
    ("Technology", "Printers", ["HP DeskJet Ink Advantage", "Canon PIXMA G3000",
                                "Epson EcoTank L3250", "Brother Laser HL-L2321"], (6500, 16000), 0.18),
    ("Furniture", "Chairs", ["Green Soul Ergonomic Chair", "Featherlite Office Chair",
                             "Godrej Interio Mesh Chair", "Nilkamal Visitor Chair"], (3200, 14000), 0.24),
    ("Furniture", "Tables", ["Godrej Study Table", "Nilkamal Conference Table",
                             "Wakefit Computer Desk", "Durian Meeting Table"], (5500, 26000), 0.10),
    ("Furniture", "Bookcases", ["Nilkamal 4-Shelf Bookcase", "Wakefit Wooden Bookshelf",
                                "Godrej Steel Cabinet"], (3500, 12500), 0.14),
    ("Furniture", "Furnishings", ["Philips LED Desk Lamp", "Ajanta Wall Clock",
                                  "Solimo Photo Frame Set", "Cello Desk Organizer"], (350, 2400), 0.36),
    ("Office Supplies", "Paper", ["JK Copier A4 Paper (500)", "Classmate Notebook Pack",
                                  "Navneet Ruled Register", "Sticky Notes Pack"], (120, 520), 0.40),
    ("Office Supplies", "Binders", ["Solo Ring Binder", "Kangaro Box File",
                                    "Deli Lever Arch File"], (90, 450), 0.38),
    ("Office Supplies", "Storage", ["Cello Plastic Storage Box", "Nilkamal Drawer Unit",
                                    "Kangaro Document Rack"], (400, 3800), 0.26),
    ("Office Supplies", "Art & Stationery", ["Faber-Castell Marker Set", "Camlin Colour Pencils",
                                             "Reynolds Pen Pack", "Kangaro Stapler"], (60, 650), 0.42),
]

CATEGORY_DEMAND = {"Technology": 0.30, "Furniture": 0.22, "Office Supplies": 0.48}

SEGMENTS = ["Consumer", "Corporate", "Home Office"]
SEGMENT_P = [0.52, 0.30, 0.18]

SHIP_MODES = {  # mode: (probability, min_days, max_days)
    "Standard Class": (0.60, 4, 7),
    "Second Class": (0.20, 2, 4),
    "First Class": (0.15, 1, 3),
    "Same Day": (0.05, 0, 0),
}

MONTH_SEASONALITY = {1: 0.80, 2: 0.75, 3: 1.10, 4: 0.85, 5: 0.85, 6: 0.90,
                     7: 0.90, 8: 1.00, 9: 1.15, 10: 1.35, 11: 1.45, 12: 1.20}
YEAR_GROWTH = {2022: 1.00, 2023: 1.12, 2024: 1.25, 2025: 1.38}

# Regions differ in how aggressively the sales team discounts.
REGION_DISCOUNTS = {
    "North": ([0.0, 0.05, 0.10, 0.15, 0.20], [0.45, 0.20, 0.20, 0.10, 0.05]),
    "South": ([0.0, 0.05, 0.10, 0.15, 0.20], [0.50, 0.20, 0.18, 0.08, 0.04]),
    "West":  ([0.0, 0.05, 0.10, 0.15, 0.20, 0.30], [0.40, 0.20, 0.20, 0.10, 0.06, 0.04]),
    "East":  ([0.0, 0.10, 0.20, 0.30, 0.40], [0.25, 0.20, 0.25, 0.18, 0.12]),
}

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Arjun", "Sai", "Reyansh", "Krishna", "Ishaan",
               "Rohan", "Kabir", "Ananya", "Diya", "Priya", "Saanvi", "Aadhya", "Kavya",
               "Isha", "Meera", "Neha", "Pooja", "Rahul", "Amit", "Vikram", "Karan", "Siddharth",
               "Nikhil", "Manish", "Deepak", "Sneha", "Ritika", "Tanvi", "Shreya", "Arnav",
               "Harsh", "Yash", "Aditi", "Riya", "Simran", "Gaurav", "Varun"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Singh", "Kumar", "Mehta", "Patel", "Reddy",
              "Nair", "Iyer", "Das", "Chatterjee", "Banerjee", "Joshi", "Kapoor", "Malhotra",
              "Agarwal", "Bansal", "Chopra", "Rao", "Pillai", "Mishra", "Yadav", "Saxena",
              "Bose", "Khanna", "Arora", "Sethi", "Menon", "Desai"]

# --------------------------------------------------------------------------
# 2. Customers and products
# --------------------------------------------------------------------------
N_CUSTOMERS = 850
city_weights = np.array([c[3] for c in CITIES], dtype=float)
city_weights /= city_weights.sum()

customers = []
for i in range(1, N_CUSTOMERS + 1):
    city, state, region, _ = CITIES[rng.choice(len(CITIES), p=city_weights)]
    customers.append({
        "customer_id": f"CUST-{i:04d}",
        "customer_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
        "segment": rng.choice(SEGMENTS, p=SEGMENT_P),
        "city": city, "state": state, "region": region,
        # some customers buy far more often than others (Pareto-like)
        "activity": rng.pareto(2.2) + 0.3,
    })
cust_df = pd.DataFrame(customers)
cust_p = (cust_df["activity"] / cust_df["activity"].sum()).to_numpy()

products = []
pid = 1
for category, sub_cat, names, (lo, hi), margin in CATALOG:
    for name in names:
        products.append({
            "product_id": f"{category[:3].upper()}-{sub_cat[:2].upper()}-{pid:04d}",
            "category": category, "sub_category": sub_cat, "product_name": name,
            "unit_price": float(round(rng.uniform(lo, hi), -1)),
            "base_margin": margin,
        })
        pid += 1
prod_df = pd.DataFrame(products)

# product sampling probability: category demand split evenly inside category
cat_counts = prod_df["category"].value_counts()
prod_p = np.array(prod_df["category"].map(lambda c: CATEGORY_DEMAND[c] / cat_counts[c]), dtype=float)
prod_p = prod_p / prod_p.sum()

# --------------------------------------------------------------------------
# 3. Order dates (seasonality x growth)
# --------------------------------------------------------------------------
all_days = pd.date_range("2022-01-01", "2025-12-31", freq="D")
day_w = np.array([MONTH_SEASONALITY[d.month] * YEAR_GROWTH[d.year]
                  * (0.85 if d.dayofweek == 6 else 1.0) for d in all_days])
day_w /= day_w.sum()

N_ORDERS = 5200
order_dates = np.sort(rng.choice(all_days, size=N_ORDERS, p=day_w))

# --------------------------------------------------------------------------
# 4. Build order lines
# --------------------------------------------------------------------------
mode_names = list(SHIP_MODES)
mode_p = [SHIP_MODES[m][0] for m in mode_names]

rows = []
for n, odate in enumerate(order_dates, start=1):
    odate = pd.Timestamp(odate)
    cust = cust_df.iloc[rng.choice(len(cust_df), p=cust_p)]
    mode = rng.choice(mode_names, p=mode_p)
    _, dmin, dmax = SHIP_MODES[mode]
    ship_date = odate + pd.Timedelta(days=int(rng.integers(dmin, dmax + 1)))
    order_id = f"IN-{odate.year}-{n:06d}"

    n_lines = rng.choice([1, 2, 3, 4], p=[0.45, 0.30, 0.17, 0.08])
    line_products = rng.choice(len(prod_df), size=n_lines, replace=False, p=prod_p)
    disc_levels, disc_p = REGION_DISCOUNTS[cust["region"]]

    for pi in line_products:
        prod = prod_df.iloc[pi]
        # cheap items are bought in larger quantities
        max_q = 3 if prod["unit_price"] > 10000 else (6 if prod["unit_price"] > 2000 else 12)
        qty = int(rng.integers(1, max_q + 1))
        if cust["segment"] == "Corporate":
            qty = int(np.ceil(qty * 1.4))

        discount = float(rng.choice(disc_levels, p=disc_p))
        if prod["sub_category"] == "Tables":          # tables are pushed with deep discounts
            discount = min(0.45, discount + 0.10)

        price = prod["unit_price"] * rng.uniform(0.97, 1.03)   # small price variation
        gross = qty * price
        sales = gross * (1 - discount)
        cost = gross * (1 - prod["base_margin"]) * rng.uniform(0.97, 1.03)
        profit = sales - cost

        rows.append({
            "Order ID": order_id,
            "Order Date": odate.strftime("%d-%m-%Y"),
            "Ship Date": ship_date.strftime("%d-%m-%Y"),
            "Ship Mode": mode,
            "Customer ID": cust["customer_id"],
            "Customer Name": cust["customer_name"],
            "Segment": cust["segment"],
            "City": cust["city"],
            "State": cust["state"],
            "Region": cust["region"],
            "Product ID": prod["product_id"],
            "Category": prod["category"],
            "Sub-Category": prod["sub_category"],
            "Product Name": prod["product_name"],
            "Quantity": qty,
            "Unit Price": round(price, 2),
            "Discount": discount,
            "Sales": round(sales, 2),
            "Profit": round(profit, 2),
        })

df = pd.DataFrame(rows)
df.insert(0, "Row ID", range(1, len(df) + 1))

# --------------------------------------------------------------------------
# 5. Inject realistic data-quality issues
# --------------------------------------------------------------------------
n = len(df)

# a) inconsistent casing / stray spaces in text columns
idx = rng.choice(n, size=int(n * 0.03), replace=False)
df.loc[idx, "Region"] = df.loc[idx, "Region"].map(
    lambda s: rng.choice([s.upper(), s.lower(), f" {s} ", f"{s} "]))
idx = rng.choice(n, size=int(n * 0.02), replace=False)
df.loc[idx, "Category"] = df.loc[idx, "Category"].map(lambda s: rng.choice([s.upper(), f"{s}  "]))
idx = rng.choice(n, size=int(n * 0.015), replace=False)
df.loc[idx, "Ship Mode"] = df.loc[idx, "Ship Mode"].str.lower()

# b) missing values
df.loc[rng.choice(n, size=45, replace=False), "Customer Name"] = np.nan
df.loc[rng.choice(n, size=60, replace=False), "Ship Date"] = np.nan

# c) invalid rows (zero / negative quantity - data-entry errors)
bad = rng.choice(n, size=12, replace=False)
df.loc[bad, "Quantity"] = rng.choice([0, -1, -2], size=12)

# d) exact duplicate rows (double-loaded records)
dups = df.sample(n=55, random_state=SEED)
df = pd.concat([df, dups]).sort_values("Row ID", kind="stable").reset_index(drop=True)

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_FILE, index=False)
print(f"Raw data written -> {OUT_FILE.relative_to(ROOT)}  ({len(df):,} rows, {df.shape[1]} columns)")
