import pandas as pd
from pathlib import Path

# =========================
# CONFIG
# =========================
INPUT_FOLDER = r"C:\path\to\excel_folder"
OUTPUT_FILE = r"final_output.xlsx"

COLUMN_TO_EXTRACT = 3     # Column D (0-based)
MULTIPLIER = 0.0864

# =========================
# CREATE DATE COLUMN
# =========================
date_range = pd.date_range(
    start="2000-06-01",
    end="2000-10-31",
    freq="D"
)

base_df = pd.DataFrame({
    "Date": date_range.strftime("%d-%b")
})

# =========================
# EXCEL WRITER
# =========================
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:

    for excel_file in Path(INPUT_FOLDER).glob("*.xls*"):
        print(f"\n📘 Processing file: {excel_file.name}")

        final_df = base_df.copy()

        try:
            xls = pd.ExcelFile(excel_file)

            for sheet_name in xls.sheet_names:
                try:
                    df = pd.read_excel(xls, sheet_name=sheet_name)

                    # Extract Column D
                    data = df.iloc[:, COLUMN_TO_EXTRACT]

                    # Convert & multiply
                    data = pd.to_numeric(data, errors="coerce") * MULTIPLIER

                    # Align with date range
                    data = data.iloc[:len(final_df)].reset_index(drop=True)

                    # Add column (year)
                    final_df[str(sheet_name)] = data

                except Exception as e:
                    print(f"  ⚠️ Skipped sheet {sheet_name}: {e}")

            # Sheet name = file name (without extension)
            sheet_output_name = excel_file.stem[:31]

            final_df.to_excel(
                writer,
                sheet_name=sheet_output_name,
                index=False
            )

            print(f"  ✅ Sheet created: {sheet_output_name}")

        except Exception as e:
            print(f"❌ Failed to process {excel_file.name}: {e}")

print(f"\n🎉 Final Excel created: {OUTPUT_FILE}")
