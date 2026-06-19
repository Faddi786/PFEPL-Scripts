import os
import pandas as pd

def create_summary(folder_path):
    """
    Creates a Summary.xlsx file from Excel files in the given folder.
    
    :param folder_path: Path to the folder containing the Excel files.
    """
    summary_file = os.path.join(folder_path, 'Summary.xlsx')
    with pd.ExcelWriter(summary_file, engine='openpyxl') as writer:
        for filename in os.listdir(folder_path):
            if filename.endswith('.xlsx') and filename != 'Summary.xlsx':
                file_path = os.path.join(folder_path, filename)
                sheet_name = os.path.splitext(filename)[0]  # e.g., 'Vaitarna Dam'
                
                try:
                    xl = pd.ExcelFile(file_path)
                    headers = None
                    data_rows = []
                    
                    for sheet in xl.sheet_names:
                        if sheet.lower() != 'index':  # Case-insensitive check
                            df = pd.read_excel(file_path, sheet_name=sheet)
                            if headers is None:
                                headers = df.columns.tolist()
                            if not df.empty:
                                last_row = df.iloc[-1].tolist()
                                data_rows.append(last_row)
                    
                    if headers and data_rows:
                        summary_df = pd.DataFrame(data_rows, columns=headers)
                        summary_df.to_excel(writer, sheet_name=sheet_name, index=False)
                        print(f"Processed file: {filename} -> Sheet: {sheet_name}")
                
                except Exception as e:
                    print(f"Error processing {filename}: {e}")

# Example usage: Replace with your actual folder path
create_summary(r"C:\Users\Swapnali\Desktop\Sakina Maam Work\Dam Automation\output\Pise_(27_February_2026)_(04_06_PM)_try_5\all_years_timeseries")