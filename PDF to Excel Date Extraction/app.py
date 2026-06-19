import pdfplumber
import pandas as pd
from datetime import datetime
import os

input_file = "Input.xlsx"
# Fix 1: Filter out 'nan' rows from the input file to stop the PDF Not Found errors
pdf_list_df = pd.read_excel(input_file).dropna(how='all')
pdf_list_df.iloc[:, 0] = pdf_list_df.iloc[:, 0].astype(str) # Ensure paths are strings

final_output = pd.DataFrame(columns=[
    "Station", "WGS84 Latitude", "WGS84 Longitude", "Ellip. Height [m]",
    "Northing [m]", "Easting [m]", "Ortho. Height [m]"
])


def autofit_columns(filepath):
    """
    Smart auto-fit that measures only VISIBLE text in hyperlink cells.
    Perfect for index.xlsx – columns stay narrow and beautiful.
    """
    import openpyxl
    from openpyxl.utils import get_column_letter
    import time

    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"Auto-fitting columns in: {os.path.basename(filepath)}")

    for attempt in range(1, 16):
        try:
            wb = openpyxl.load_workbook(filepath)

            for ws in wb.worksheets:
                for col in ws.columns:
                    column_letter = col[0].column_letter
                    max_length = 0

                    for cell in col:
                        if cell.value is None:
                            continue

                        # === SMART TEXT EXTRACTION ===
                        if cell.hyperlink:  # This is a real hyperlink cell
                            # Use the display text if available, otherwise fallback
                            display_text = getattr(cell, "value", "")
                            if isinstance(display_text, str) and display_text.startswith('=HYPERLINK'):
                                # Try to extract the friendly name from the formula
                                try:
                                    # Extract text between the last quote and )
                                    display_text = display_text.split('"')[-2]
                                except:
                                    pass
                            visible_text = str(display_text)
                        else:
                            visible_text = str(cell.value)

                        max_length = max(max_length, len(visible_text))

                    # === BEAUTIFUL WIDTH LOGIC (especially for index.xlsx) ===
                    if "index" in filepath.lower() or "navigation" in filepath.lower():
                        # For index.xlsx: tighter caps, nicer look
                        adjusted_width = min(max_length + 3, 40)   # Max 40 is perfect
                        if column_letter == "A":   # Junction names
                            adjusted_width = min(max_length + 4, 45)
                    else:
                        # For all other files: generous but safe
                        adjusted_width = min(max_length + 3, 60)

                    ws.column_dimensions[column_letter].width = adjusted_width

            wb.save(filepath)
            wb.close()
            print("Columns auto-fitted beautifully!")
            return

        except (PermissionError, IOError, OSError):
            print(f"  File locked by Excel... retry {attempt}/15")
            time.sleep(2.5)
        except Exception as e:
            print(f"Autofit error: {e}")
            break

    print("Could not auto-fit – close the file in Excel and retry.")


def clean_columns(df):
    """Cleans column names by stripping whitespace and removing degree symbols."""
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.replace("°", "", regex=True)
    )
    return df

def find_col(df, keyword):
    """Returns the best-matching column for a keyword."""
    for col in df.columns:
        if keyword.lower() in col.lower():
            return col
    return None

for index, row in pdf_list_df.iterrows():
    pdf_path = str(row.iloc[0]).strip()

    if not os.path.isfile(pdf_path):
        print(f"⚠️ PDF Not Found: {pdf_path}")
        continue

    print(f"\n📄 Processing: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        extracted_wgs84 = None
        extracted_proj = None

        for page in pdf.pages:
            tables = page.extract_tables()

            for t in tables:
                df = pd.DataFrame(t)

                # Basic check for empty or very narrow tables
                if df.shape[1] < 3:
                    continue

                df = df.map(lambda x: str(x).strip() if x else x)

                # WGS84 table check: Removed the strict df.shape[1] == 4 filter
                if df.iloc[0].astype(str).str.contains("WGS84 Latitude", case=False).any():
                    df.columns = df.iloc[0]
                    df = df.drop(0)
                    df = clean_columns(df)

                    # Fix 2: Explicitly selecting the first 4 columns needed
                    col_station = find_col(df, "Station")
                    col_lat = find_col(df, "WGS84 Latitude")
                    col_lon = find_col(df, "WGS84 Longitude")
                    col_ellip = find_col(df, "Ellip")
                    
                    if all([col_station, col_lat, col_lon, col_ellip]):
                        extracted_wgs84 = df[[col_station, col_lat, col_lon, col_ellip]]
                        extracted_wgs84.columns = ["Station", "WGS84 Latitude", "WGS84 Longitude", "Ellip. Height [m]"]

                # Projected table check: Removed the strict df.shape[1] == 4 filter
                elif df.iloc[0].astype(str).str.contains("Northing", case=False).any():
                    df.columns = df.iloc[0]
                    df = df.drop(0)
                    df = clean_columns(df)

                    # Fix 2: Explicitly selecting the first 4 columns needed
                    col_station = find_col(df, "Station")
                    col_north = find_col(df, "Northing")
                    col_east = find_col(df, "Easting")
                    col_ortho = find_col(df, "Ortho") or find_col(df, "Orthometric") or find_col(df, "Height")

                    if all([col_station, col_north, col_east, col_ortho]):
                        extracted_proj = df[[col_station, col_north, col_east, col_ortho]]
                        extracted_proj.columns = ["Station", "Northing [m]", "Easting [m]", "Ortho. Height [m]"]

            # Break out of page loop once both tables are found
            if extracted_wgs84 is not None and extracted_proj is not None:
                break


        if extracted_wgs84 is not None and extracted_proj is not None:
            # Drop NaN rows before merging to ensure a clean merge
            extracted_wgs84.dropna(subset=['Station'], inplace=True)
            extracted_proj.dropna(subset=['Station'], inplace=True)
            
            merged = pd.merge(extracted_wgs84, extracted_proj, on="Station", how="inner")
            final_output = pd.concat([final_output, merged], ignore_index=True)
        else:
            print(f"⚠️ Adjusted Coordinates (WGS84 or Projected) not fully found in: {pdf_path}")

timestamp = datetime.now().strftime("(%d-%B-%Y)_(%H-%M-%S)")
output_filename = f"Output_{timestamp}.xlsx"

with pd.ExcelWriter(output_filename) as writer:
    final_output.to_excel(writer, sheet_name="Adjusted Coordinates", index=False)
    pdf_list_df.to_excel(writer, sheet_name="PDF List Used", index=False)

autofit_columns(output_filename)
print(f"\n✅ Done! Output saved as: {output_filename}\n")


