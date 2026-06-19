import pandas as pd
from datetime import datetime

# =========================
# CONFIG
# =========================
INPUT_FILE = "input.xlsx"      # your source file
OUTPUT_FILE = "output.xlsx"    # final result file
COLUMN_TO_EXTRACT = 3          # Column D (0-based index)

# =========================
# CREATE DATE COLUMN
# =========================
date_range = pd.date_range(
    start="2000-06-01",
    end="2000-10-31",
    freq="D"
)

date_column = date_range.strftime("%d-%b")
final_df = pd.DataFrame({"Date": date_column})

# =========================
# READ EXCEL & PROCESS SHEETS
# =========================
xls = pd.ExcelFile(INPUT_FILE)

for sheet_name in xls.sheet_names:
    try:
        df = pd.read_excel(
            xls,
            sheet_name=sheet_name,
            header=0
        )

        # Extract Column D
        year_data = df.iloc[:, COLUMN_TO_EXTRACT]

        # Trim or pad to match date range length
        year_data = year_data.iloc[:len(final_df)].reset_index(drop=True)

        # Add to final dataframe
        final_df[str(sheet_name)] = year_data

        print(f"Processed sheet: {sheet_name}")

    except Exception as e:
        print(f"Skipping sheet {sheet_name}: {e}")

# =========================
# SAVE OUTPUT
# =========================
final_df.to_excel(OUTPUT_FILE, index=False)

print(f"\n✅ Final Excel file created: {OUTPUT_FILE}")
