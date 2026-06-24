"""
Fully automatic: read your Excel, fill all missing/zero discharge, write one Excel.
No other software to open. No manual steps.

Run:   python fill_auto.py

- Reads: input/ulhas_gauges.xlsx  (or pass path as argument)
- Fills: every empty and zero value automatically (time-series interpolation)
- Writes: output/ulhas_discharge_filled.xlsx  (one sheet per station: date, discharge (m3/sec))
"""
import sys
from pathlib import Path

import pandas as pd
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_EXCEL = INPUT_DIR / "ulhas_gauges.xlsx"
OUTPUT_EXCEL = OUTPUT_DIR / "ulhas_discharge_filled.xlsx"
DISC_COLS = ["discharge (m3/sec)", "discharge (m3 sec)"]


def main():
    if len(sys.argv) > 1:
        excel_path = Path(sys.argv[1])
    else:
        excel_path = DEFAULT_EXCEL

    if not excel_path.exists():
        print(f"File not found: {excel_path}")
        print("Usage: python fill_auto.py [path_to_excel.xlsx]")
        sys.exit(1)

    print(f"Reading: {excel_path.name}")
    xl = pd.ExcelFile(excel_path)
    sheets = [s for s in xl.sheet_names if s.strip()]

    all_dates = set()
    series_by_station = {}

    for sheet in sheets:
        df = pd.read_excel(excel_path, sheet_name=sheet)
        # find date column
        date_col = "date" if "date" in df.columns else df.columns[0]
        disc_col = None
        for c in DISC_COLS:
            if c in df.columns:
                disc_col = c
                break
        if disc_col is None:
            for c in df.columns:
                if "discharge" in c.lower():
                    disc_col = c
                    break
        if disc_col is None:
            print(f"  Skip sheet '{sheet}': no discharge column")
            continue

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
        df = df.dropna(subset=[date_col]).sort_values(date_col)
        # treat 0 and empty as missing
        discharge = df[disc_col].replace(0, np.nan)
        discharge = discharge.where(pd.notna(discharge))
        series_by_station[sheet] = df[[date_col]].copy()
        series_by_station[sheet]["discharge (m3/sec)"] = discharge.values
        all_dates.update(series_by_station[sheet][date_col].dt.normalize().values)

    if not series_by_station:
        print("No station data found. Check sheet names and columns (date, discharge (m3/sec)).")
        sys.exit(1)

    all_dates = sorted(pd.Series(list(all_dates)).drop_duplicates().tolist())
    print(f"Stations: {list(series_by_station.keys())}")
    print(f"Date range: {all_dates[0]} to {all_dates[-1]} ({len(all_dates)} days)")
    print("Filling all missing and zero values automatically...")

    with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
        for station, df in series_by_station.items():
            df = df.rename(columns={df.columns[0]: "date"})
            df = df.set_index("date").sort_index()
            # fill every missing/zero: interpolate in time, then forward/backward fill any remaining
            ser = df["discharge (m3/sec)"]
            filled = ser.interpolate(method="linear", limit_direction="both")
            filled = filled.ffill().bfill()  # leading/trailing gaps use nearest value
            out = pd.DataFrame({"date": filled.index, "discharge (m3/sec)": filled.values})
            out.to_excel(writer, sheet_name=station[:31], index=False)
            n_filled = out["discharge (m3/sec)"].notna().sum()
            print(f"  {station}: {n_filled} rows written")

    print(f"\nDone. Output: {OUTPUT_EXCEL}")
    print("Each sheet has columns: date, discharge (m3/sec)")


if __name__ == "__main__":
    main()
