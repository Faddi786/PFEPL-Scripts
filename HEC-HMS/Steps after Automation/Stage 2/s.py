"""
hourly_to_daily.py (Simplified Output)

Usage:
    python hourly_to_daily.py /path/to/input_folder

Output:
    For each Excel workbook in input_folder, creates an output workbook in input_folder/output/
    with the same name appended by "_output". Each sheet is converted from hourly to daily
    averages and multiplied by 0.0864.

Changes:
    - Removed second row and second column from output.
    - First cell (A1) = "Date".
    - Data starts immediately below A1.
    - Date format changed to 'D-Mon' (e.g., 1-Jun, 15-Nov, 30-Dec).
"""

import sys
from pathlib import Path
import pandas as pd
from openpyxl import Workbook

MULTIPLIER = 0.0864


def process_sheet(df_raw):
    if df_raw.shape[0] < 3 or df_raw.shape[1] < 3:
        return None, None, None

    years = df_raw.iloc[0, 2:].astype(str).tolist()
    second_row = df_raw.iloc[1, :].astype(str).tolist()
    data = df_raw.iloc[2:, :].reset_index(drop=True).copy()

    dates_series = pd.to_datetime(data.iloc[:, 0], errors="coerce").dt.date
    numeric = data.iloc[:, 2:].apply(pd.to_numeric, errors="coerce")
    numeric["__date__"] = dates_series.values
    numeric = numeric.dropna(subset=["__date__"])

    if numeric.empty:
        return years, second_row, pd.DataFrame()

    grouped = numeric.groupby("__date__").mean()
    if "__date__" in grouped.columns:
        grouped = grouped.drop(columns="__date__")

    grouped = grouped * MULTIPLIER
    grouped.columns = years[: grouped.shape[1]]
    return years, second_row, grouped


def write_sheet_openpyxl(ws, years, second_row, daily_df):
    """
    Simplified output:
    - Remove second row and second column.
    - Put 'Date' in A1, then years start from B1.
    - Date format = 'D-Mon' (e.g., 1-Jun, 15-Nov, 30-Dec).
    """
    import platform

    # Header row
    header_row = ["Date"] + years
    ws.append(header_row)

    # Data rows
    for idx, row in daily_df.iterrows():
        # Format date properly depending on OS
        try:
            if platform.system() == "Windows":
                date_str = pd.to_datetime(idx).strftime("%#d-%b")  # Windows-friendly
            else:
                date_str = pd.to_datetime(idx).strftime("%-d-%b")  # Linux/Mac
        except Exception:
            # Fallback if both fail
            date_str = pd.to_datetime(idx).strftime("%d-%b").lstrip("0")

        values = []
        for v in row.values:
            values.append("" if pd.isna(v) else float(v))
        ws.append([date_str] + values)



def convert_folder(input_folder: Path):
    input_folder = Path(input_folder)
    if not input_folder.exists():
        raise FileNotFoundError(f"Input folder not found: {input_folder}")

    out_folder = input_folder / "output"
    out_folder.mkdir(exist_ok=True)

    excel_files = list(input_folder.glob("*.xls*"))
    if not excel_files:
        print("No Excel files found in", input_folder)
        return

    for file_path in excel_files:
        print("Processing:", file_path.name)
        try:
            xls = pd.ExcelFile(file_path, engine="openpyxl")
        except Exception as e:
            print(f"  Failed to open {file_path.name}: {e}")
            continue

        wb = Workbook()
        default = wb.active
        wb.remove(default)

        for sheet_name in xls.sheet_names:
            try:
                df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine="openpyxl")
            except Exception as e:
                print(f"  Skipping sheet {sheet_name} due to read error: {e}")
                continue

            years, second_row, daily_df = process_sheet(df_raw)
            if years is None:
                print(f"  Sheet {sheet_name} skipped (too small or empty).")
                continue

            ws = wb.create_sheet(title=sheet_name[:31])
            write_sheet_openpyxl(ws, years, second_row, daily_df)

        out_name = file_path.stem + "_output" + file_path.suffix
        out_path = out_folder / out_name
        wb.save(out_path)
        print("  Saved:", out_path)


if __name__ == "__main__":
    input_folder = r"input"
    convert_folder(input_folder)
    print("Done.")
