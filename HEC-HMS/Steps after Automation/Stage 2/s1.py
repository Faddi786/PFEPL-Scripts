"""
hourly_to_daily_combined_v2.py
-------------------------------
Usage:
    python hourly_to_daily_combined_v2.py /path/to/input_folder

Description:
    Reads all Excel workbooks in a folder, converts hourly data to daily averages
    (× 0.0864, rounded to 1 decimal), skips 'index' sheet, and saves all results
    into a single Excel workbook named 'combined_output.xlsx'.
    Each input sheet becomes one sheet in the output.
"""

import sys
from pathlib import Path
import pandas as pd
from openpyxl import Workbook

MULTIPLIER = 0.0864
OUTPUT_FILE = "output/combined_output.xlsx"

def process_sheet(df_raw, sheet_name):
    """
    Convert one input sheet to daily averaged data × 0.0864 (1 decimal)
    Keeps fixed year columns (1975–2024)
    Returns: (years, daily_df)
    """
    if df_raw.shape[0] < 3 or df_raw.shape[1] < 3:
        return None, None

    # Define fixed year range
    FIXED_YEARS = [str(y) for y in range(1975, 2025)]

    # Extract available years from sheet header (starting column C)
    all_years = df_raw.iloc[0, 2:].astype(str).tolist()

    valid_years = []
    invalid_years = []

    # Separate valid and invalid year labels
    for y in all_years:
        if y.isdigit() and len(y) == 4:
            valid_years.append(y)
        else:
            invalid_years.append(y)

    # Print invalid year names (if any)
    if invalid_years:
        print(f"⚠️ Invalid year names found in sheet '{sheet_name}':")
        for bad in invalid_years:
            print("   →", bad)

    # Continue using valid ones for processing
    available_years = valid_years


    # Keep only columns corresponding to FIXED_YEARS that exist
    valid_years = [y for y in FIXED_YEARS if y in available_years]

    # Data starts from row 2 onward
    data = df_raw.iloc[2:, :].reset_index(drop=True).copy()

    # Parse date
    data.iloc[:, 0] = pd.to_datetime(data.iloc[:, 0], errors='coerce').dt.date

    # Only keep columns for valid years
    year_indices = [available_years.index(y) + 2 for y in valid_years]
    numeric = data.iloc[:, year_indices].apply(pd.to_numeric, errors='coerce')
    numeric["__date__"] = data.iloc[:, 0]

    numeric = numeric.dropna(subset=["__date__"])
    if numeric.empty:
        return FIXED_YEARS, pd.DataFrame()

    # Group by date → daily average
    grouped = numeric.groupby("__date__").mean()

    # Multiply & round
    grouped = (grouped * MULTIPLIER).round(1)

    # Insert missing columns as NaN
    for y in FIXED_YEARS:
        if y not in grouped.columns:
            grouped[y] = None

    # Reorder columns in correct 1975–2024 order
    grouped = grouped[FIXED_YEARS]

    # Reset index → Date as first column
    grouped = grouped.reset_index()
    grouped.rename(columns={"__date__": "Date"}, inplace=True)

    return FIXED_YEARS, grouped



def write_sheet_openpyxl(ws, daily_df):
    """Write processed sheet to openpyxl worksheet"""
    ws.append(list(daily_df.columns))
    for _, row in daily_df.iterrows():
        ws.append(list(row.values))


def convert_folder_to_single_workbook(input_folder: Path):
    input_folder = Path(input_folder)
    if not input_folder.exists():
        raise FileNotFoundError(f"Input folder not found: {input_folder}")

    out_path = input_folder / OUTPUT_FILE

    wb = Workbook()
    default = wb.active
    wb.remove(default)

    excel_files = list(input_folder.glob("*.xls*"))
    if not excel_files:
        print("No Excel files found in", input_folder)
        return

    for file_path in excel_files:
        print(f"Processing workbook: {file_path.name}")
        try:
            xls = pd.ExcelFile(file_path, engine="openpyxl")
        except Exception as e:
            print(f"  ❌ Failed to open {file_path.name}: {e}")
            continue

        for sheet_name in xls.sheet_names:
            if sheet_name.strip().lower() == "index":
                print(f"  ⏩ Skipping sheet '{sheet_name}'")
                continue

            try:
                df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine="openpyxl")
                years, daily_df = process_sheet(df_raw, sheet_name)
                if daily_df is None or daily_df.empty:
                    print(f"  ⚠️ No data in '{sheet_name}'")
                    continue

                ws = wb.create_sheet(title=sheet_name[:31])
                write_sheet_openpyxl(ws, daily_df)
                print(f"  ✅ Added sheet: {sheet_name}")

            except Exception as e:
                print(f"  ⚠️ Skipping {sheet_name}: {e}")
                continue

    wb.save(out_path)
    print(f"\n🎉 Combined output saved as: {out_path}")


if __name__ == "__main__":
    # Default: folder named "input" beside script
    input_folder = "input"
    convert_folder_to_single_workbook(input_folder)
    print("Done.")
