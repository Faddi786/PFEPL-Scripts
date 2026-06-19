import pandas as pd

# =========================
# CONFIG
# =========================
INPUT_FILE = "input.xlsx"
OUTPUT_FILE = "output.xlsx"
COLUMN_TO_EXTRACT = 3        # Column D (0-based)
MULTIPLIER = 0.0864

# =========================
# CREATE DATE COLUMN
# =========================
date_range = pd.date_range(
    start="2000-06-01",
    end="2000-10-31",
    freq="D"
)

final_df = pd.DataFrame({
    "Date": date_range.strftime("%d-%b")
})

# =========================
# READ EXCEL & PROCESS SHEETS
# =========================
xls = pd.ExcelFile(INPUT_FILE)

for sheet_name in xls.sheet_names:
    try:
        df = pd.read_excel(xls, sheet_name=sheet_name)

        # Extract Column D
        year_data = df.iloc[:, COLUMN_TO_EXTRACT]

        # Convert to numeric & multiply
        year_data = pd.to_numeric(year_data, errors="coerce") * MULTIPLIER

        # Match date length
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
