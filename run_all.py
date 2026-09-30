"""
run_all.py - runs the full pipeline end to end.

    python run_all.py

1. scripts/generate_data.py         -> data/raw/sales_raw.csv
2. scripts/clean_data.py            -> data/processed/sales_clean.csv
3. scripts/run_sql.py               -> outputs/sql_results/*.csv, outputs/SQL_RESULTS.md
4. scripts/build_excel_dashboard.py -> dashboard/Sales_Dashboard.xlsx

Then open notebooks/sales_performance_analysis.ipynb for the full analysis.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = ["generate_data.py", "clean_data.py", "run_sql.py", "build_excel_dashboard.py"]

for step in STEPS:
    print(f"\n{'=' * 70}\n>>> {step}\n{'=' * 70}")
    subprocess.run([sys.executable, str(ROOT / "scripts" / step)], check=True)

print("\nPipeline finished successfully.")
