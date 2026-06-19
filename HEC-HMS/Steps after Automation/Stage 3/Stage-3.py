# -*- coding: utf-8 -*-
import os
import pandas as pd
import re
import warnings

# ---------------- Configuration ----------------
input_folder = r"C:\Users\Swapnali\Desktop\Stages (HEC-HMS)\Stage 1\output"
output_file = "combined_output_for_all_years_ulhas.xlsx"

warnings.simplefilter(action='ignore', category=FutureWarning)  # silence harmless warnings

# ---------------- Gather all Excel files ----------------
excel_files = [f for f in os.listdir(input_folder) if f.endswith(('.xlsx', '.xls'))]

if not excel_files:
    raise FileNotFoundError("No Excel files found in the given folder.")

# ---------------- Process ----------------
all_sheets_data = {}

for file in excel_files:
    file_path = os.path.join(input_folder, file)
    xls = pd.ExcelFile(file_path)
    print(f"Reading workbook: {file}")
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        if "Date" not in df.columns:
            continue
        
        df = df.dropna(how='all')

        # 🔹 Convert "1-Jun" etc. safely to a datetime with dummy year (e.g., 2000)
        try:
            df["_date_sort"] = pd.to_datetime(df["Date"].astype(str) + "-2000", format="%d-%b-%Y", errors="coerce")
        except Exception:
            df["_date_sort"] = pd.NaT
        
        if sheet_name not in all_sheets_data:
            all_sheets_data[sheet_name] = []
        all_sheets_data[sheet_name].append(df)

# ---------------- Combine sheets ----------------
writer = pd.ExcelWriter(output_file, engine='openpyxl')

for sheet_name, dfs in all_sheets_data.items():
    print(f"Combining sheet: {sheet_name}")
    
    # Merge all DataFrames on Date
    merged_df = dfs[0]
    for next_df in dfs[1:]:
        merged_df = pd.merge(merged_df, next_df, on="Date", how="outer", suffixes=("", "_dup"))

    # ✅ Ensure all column names are strings
    merged_df.columns = merged_df.columns.map(str)

    # 🔹 Drop unwanted helper or duplicate columns
    merged_df = merged_df.loc[:, ~merged_df.columns.str.contains("_date_sort", case=False, regex=True)]
    merged_df = merged_df.loc[:, ~merged_df.columns.str.endswith("_dup")]

    # 🔹 Sort by date (month-day order)
    merged_df["_date_sort"] = pd.to_datetime(merged_df["Date"].astype(str) + "-2000", format="%d-%b-%Y", errors="coerce")
    merged_df = merged_df.sort_values(by="_date_sort").drop(columns=["_date_sort"])

    # 🔹 Sort year columns numerically ascending
    date_col = ["Date"]
    other_cols = [col for col in merged_df.columns if col != "Date"]
    
    # Identify 4-digit numeric year columns
    year_cols = sorted([c for c in other_cols if re.match(r'^\d{4}$', c)], key=int)
    non_year_cols = [c for c in other_cols if c not in year_cols]
    
    # Final column order: Date, sorted years, other leftovers
    merged_df = merged_df[date_col + year_cols + non_year_cols]

    # Remove duplicates just in case
    merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]

    # Write to Excel
    merged_df.to_excel(writer, sheet_name=sheet_name, index=False)

writer.close()
print(f"\n✅ Combined workbook saved successfully: {output_file}")
