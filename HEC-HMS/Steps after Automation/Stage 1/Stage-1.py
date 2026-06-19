import os
import pandas as pd
from datetime import datetime

# === CONFIG ===
input_folder = r"C:\Users\Swapnali\Desktop\Stages (HEC-HMS)\Stage 1\input\junction12"   # <-- change this
output_file = r"C:\Users\Swapnali\Desktop\Stages (HEC-HMS)\Stage 1\output\outputcombined_transposed_junction12.xlsx"
junction_file = r"C:\Users\Swapnali\Desktop\Stages (HEC-HMS)\Stage 1\junction_names.xlsx"  # <-- Excel file with names in first column

# === DATE RANGE LIMITS ===
START_MONTH, START_DAY = 6, 1   # June 1
END_MONTH, END_DAY = 10, 31     # October 31


# ======================================================
# Function to read allowed junction names from Excel file
# ======================================================
def get_allowed_junctions(excel_path):
    """Read the first column of an Excel file and return a list of allowed junction names."""
    try:
        df = pd.read_excel(excel_path, header=None)
        allowed = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
        print(f"✅ Loaded {len(allowed)} allowed junctions from {excel_path}")
        return allowed
    except Exception as e:
        print(f"⚠️ Error reading junction names file: {e}")
        return []


# === Load allowed junctions ===
allowed_junctions = get_allowed_junctions(junction_file)

# === Create ExcelWriter to hold all sheets ===
# , engine='xlsxwriter'
writer = pd.ExcelWriter(output_file)

# === Loop through all input files ===
for file in os.listdir(input_folder):
    if not file.endswith(".xlsx"):
        continue

    workbook_name = os.path.splitext(file)[0]

    # ✅ Skip if workbook name not in allowed list
    if workbook_name not in allowed_junctions:
        print(f"⏩ Skipping workbook (not in list): {workbook_name}")
        continue

    input_path = os.path.join(input_folder, file)
    print(f"Processing workbook: {workbook_name}")

    # Collect all years' data
    all_years_data = {}
    xls = pd.ExcelFile(input_path)

    for sheet in xls.sheet_names:
        # Skip any sheet named "index"
        if sheet.strip().lower() == "index":
            print(f"⏩ Skipping sheet '{sheet}'")
            continue

        try:
            df = pd.read_excel(xls, sheet_name=sheet)
            if "FLOW" not in df.columns or "Date" not in df.columns:
                print(f"⚠️ Skipping sheet {sheet}: Missing columns.")
                continue

            # Convert Date to datetime
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date", "FLOW"])

            # Filter only between June 1 and Oct 31
            df = df[df["Date"].dt.month.between(START_MONTH, END_MONTH)]
            df = df[(df["Date"].dt.month > START_MONTH) | (df["Date"].dt.day >= START_DAY)]
            df = df[(df["Date"].dt.month < END_MONTH) | (df["Date"].dt.day <= END_DAY)]

            if df.empty:
                continue

            # Compute daily average
            daily_avg = df.groupby("Date")["FLOW"].mean().reset_index()
            daily_avg["FLOW"] = (daily_avg["FLOW"] * 0.0864)

            # ✅ Convert to "D-Mon" format (e.g., 1-Jun)
            # Use platform-safe formatting
            import platform
            if platform.system() == "Windows":
                daily_avg["MonthDay"] = daily_avg["Date"].dt.strftime("%#d-%b")
            else:
                daily_avg["MonthDay"] = daily_avg["Date"].dt.strftime("%-d-%b")

            # Keep only MonthDay and FLOW
            all_years_data[int(sheet)] = daily_avg[["MonthDay", "FLOW"]]

        except Exception as e:
            print(f"Error reading sheet {sheet}: {e}")

    # === Create base date template (D-Mon only) ===
    date_range = pd.date_range("1975-06-01", "1975-10-31")

    # Use same "D-Mon" format for merging
    import platform
    if platform.system() == "Windows":
        base_dates = date_range.strftime("%#d-%b")
    else:
        base_dates = date_range.strftime("%-d-%b")

    final_df = pd.DataFrame({"MonthDay": base_dates})

    # === Merge each year's data based on MonthDay ===
    for year in sorted(all_years_data.keys()):
        temp = all_years_data[year].copy()
        temp.rename(columns={"FLOW": year}, inplace=True)
        final_df = pd.merge(final_df, temp, on="MonthDay", how="left")

    # === Rename columns ===
    final_df.rename(columns={"MonthDay": "Date"}, inplace=True)

    # === Write to output workbook ===
    sheet_name = workbook_name[:31]
    final_df.to_excel(writer, index=False, sheet_name=sheet_name)
    print(f"✅ Added sheet: {sheet_name}")

# === Save final combined workbook ===
writer.close()
print(f"\n🎉 All allowed workbooks combined into: {output_file}")
