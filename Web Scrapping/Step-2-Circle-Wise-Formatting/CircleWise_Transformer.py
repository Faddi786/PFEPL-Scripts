import pandas as pd
import os
import shutil
from pathlib import Path
import re
from datetime import datetime
from collections import defaultdict
from openpyxl import load_workbook

def delete_columns_and_transpose(df, sheet_name, year):
    """
    Delete columns A,B,C,E and last 3 columns based on sheet name,
    then transpose the dataframe and create proper dates
    """
    # Get column indices (0-based)
    all_columns = df.columns.tolist()
    
    # Columns to delete: A, B, C, E (indices 0, 1, 2, 4)
    cols_to_delete_indices = [0, 1, 2, 4]
    cols_to_delete_names = [all_columns[i] for i in cols_to_delete_indices if i < len(all_columns)]
    
    # Determine last 3 columns based on sheet name
    if sheet_name in ['June', 'September']:
        last_3_indices = [-3, -2, -1]
    elif sheet_name in ['July', 'August', 'October']:
        last_3_indices = [-3, -2, -1]
    else:
        last_3_indices = []
    
    last_3_names = [all_columns[i] for i in last_3_indices if abs(i) <= len(all_columns)]
    
    # Combine all columns to delete
    cols_to_delete = cols_to_delete_names + last_3_names
    
    # Drop the columns
    df_cleaned = df.drop(columns=cols_to_delete, errors='ignore')
    
    if df_cleaned.empty:
        return pd.DataFrame()
    
    # Get the circle names (first column after deletion)
    circle_col_name = df_cleaned.columns[0]
    
    # Set the first column (Circle) as index
    df_cleaned.set_index(circle_col_name, inplace=True)
    
    # Clean up column names (day numbers)
    df_cleaned.columns = df_cleaned.columns.astype(str)
    
    # Transpose
    df_transposed = df_cleaned.T
    
    # Reset index to make day column a regular column
    df_transposed.reset_index(inplace=True)
    df_transposed.rename(columns={'index': 'Day'}, inplace=True)
    
    # Convert day column to integer
    df_transposed['Day'] = pd.to_numeric(df_transposed['Day'], errors='coerce')
    df_transposed = df_transposed.dropna(subset=['Day'])
    df_transposed['Day'] = df_transposed['Day'].astype(int)
    
    # Create proper date column (e.g., "01-Jun", "02-Jun", etc.)
    month_map = {
        'June': 6, 'July': 7, 'August': 8, 'September': 9, 'October': 10
    }
    
    month_num = month_map.get(sheet_name, 6)
    # Create datetime objects and format as "DD-Mon"
    df_transposed['Date'] = df_transposed['Day'].apply(
        lambda d: datetime(year, month_num, d).strftime('%d-%b')
    )
    
    # Keep only Date and circle columns
    result_df = df_transposed[['Date'] + [col for col in df_transposed.columns if col not in ['Day', 'Date']]]
    
    return result_df

def process_district_file(file_path, year):
    """
    Process a single district Excel file - combine all months into one dataframe
    """
    sheet_names = ['June', 'July', 'August', 'September', 'October']
    all_months_data = []
    
    try:
        excel_file = pd.ExcelFile(file_path)
        
        for sheet_name in sheet_names:
            if sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                df_processed = delete_columns_and_transpose(df, sheet_name, year)
                
                if not df_processed.empty:
                    all_months_data.append(df_processed)
        
        if all_months_data:
            # Combine all months for this district
            combined_df = pd.concat(all_months_data, ignore_index=True)
            
            # Sort by date
            # Convert Date string to datetime for sorting
            combined_df['Date_Sort'] = pd.to_datetime(
                combined_df['Date'] + f'-{year}', 
                format='%d-%b-%Y'
            )
            combined_df = combined_df.sort_values('Date_Sort')
            combined_df = combined_df.drop('Date_Sort', axis=1)
            
            # Reset index
            combined_df = combined_df.reset_index(drop=True)
            
            # Make column names unique (handle duplicate circle names within same district)
            # Keep first occurrence of each circle, drop duplicates
            # Get circle columns (all except Date)
            circle_cols = [col for col in combined_df.columns if col != 'Date']
            
            # If there are duplicate circle names, keep the first one
            seen = set()
            unique_circle_cols = []
            for col in circle_cols:
                if col not in seen:
                    seen.add(col)
                    unique_circle_cols.append(col)
            
            # Keep only unique circle columns
            combined_df = combined_df[['Date'] + unique_circle_cols]
            
            return combined_df
    
    except Exception as e:
        print(f"    Error processing {file_path.name}: {str(e)}")
    
    return pd.DataFrame()

def process_year_folder(year_folder_path, temp_output_folder):
    """
    Process all Excel files in a year folder and create one Excel file
    with each district as a separate sheet
    """
    year = int(Path(year_folder_path).name)
    print(f"Processing year: {year}")
    
    # Dictionary to store data for each district
    district_data = {}
    
    # Look for Excel files in the folder
    excel_files = sorted(list(Path(year_folder_path).glob('*.xlsx')) + \
                         list(Path(year_folder_path).glob('*.xls')))
    
    for excel_file in excel_files:
        district_name = Path(excel_file).stem  # e.g., 'Nashik', 'Palghar', etc.
        print(f"  Processing: {excel_file.name}")
        
        df_district = process_district_file(excel_file, year)
        
        if not df_district.empty:
            district_data[district_name] = df_district
            print(f"    → {df_district.shape[0]} rows, {df_district.shape[1]} columns")
    
    if district_data:
        # Create Excel file with multiple sheets
        output_file = temp_output_folder / f"{year}_Rainfall_Data.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for district_name, df in district_data.items():
                # Clean sheet name (Excel sheet names have 31 char limit and can't have certain chars)
                sheet_name = district_name[:31].replace('/', '_').replace('\\', '_')
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"  ✓ Saved: {output_file.name} ({len(district_data)} sheets)")
        return True
    
    return False

def get_all_districts(temp_year_folder):
    """
    Scan all year files to get the list of all districts present
    """
    districts = set()
    year_files = list(Path(temp_year_folder).glob('*_Rainfall_Data.xlsx'))
    
    for year_file in year_files:
        try:
            excel_file = pd.ExcelFile(year_file)
            districts.update(excel_file.sheet_names)
        except Exception as e:
            print(f"  Warning: Could not read {year_file.name}: {str(e)}")
    
    return sorted(list(districts))

def create_district_file(district_name, temp_year_folder, temp_district_folder, all_years):
    """
    Create a single Excel file for a district with sheets for each year
    """
    district_file = temp_district_folder / f"{district_name}.xlsx"
    
    with pd.ExcelWriter(district_file, engine='openpyxl') as writer:
        years_processed = []
        
        for year in all_years:
            year_file = temp_year_folder / f"{year}_Rainfall_Data.xlsx"
            
            if not year_file.exists():
                continue
            
            try:
                # Read the specific sheet for this district
                df_year = pd.read_excel(year_file, sheet_name=district_name)
                
                # Write to the district file as a sheet named by year
                sheet_name = str(year)
                df_year.to_excel(writer, sheet_name=sheet_name, index=False)
                years_processed.append(year)
                
            except Exception as e:
                # Sheet might not exist for this district in this year
                continue
    
    return len(years_processed) > 0

def reorganize_to_district_wise(temp_year_folder, temp_district_folder, years):
    """
    Reorganize data from year-wise to district-wise
    """
    print("\n" + "=" * 70)
    print("STEP 2: Creating district-wise Excel files...")
    print("=" * 70)
    
    # Get all districts
    print("\nScanning for districts across all years...")
    districts = get_all_districts(temp_year_folder)
    print(f"Found {len(districts)} districts")
    
    # Create a file for each district
    print("\nCreating district-wise Excel files...")
    print("-" * 50)
    
    successful_districts = []
    
    for district in districts:
        try:
            if create_district_file(district, temp_year_folder, temp_district_folder, years):
                successful_districts.append(district)
                if len(successful_districts) % 20 == 0:
                    print(f"  Processed {len(successful_districts)}/{len(districts)} districts...")
        except Exception as e:
            print(f"  ✗ Error creating {district}.xlsx: {str(e)}")
    
    print(f"\n✓ Created {len(successful_districts)} district files")
    
    return len(successful_districts) > 0

def get_all_years_from_district_files(temp_district_folder):
    """
    Get all years available in the district-wise folder
    """
    years = set()
    district_files = list(temp_district_folder.glob('*.xlsx'))
    
    for file in district_files:
        try:
            excel_file = pd.ExcelFile(file)
            for sheet in excel_file.sheet_names:
                if sheet.isdigit() and len(sheet) == 4:
                    years.add(sheet)
        except Exception as e:
            continue
    
    return sorted(years)

def get_all_circles_for_district(district_file):
    """
    Get all circle names that appear across all years for a district
    """
    circles = set()
    
    try:
        excel_file = pd.ExcelFile(district_file)
        
        for year_sheet in excel_file.sheet_names:
            if year_sheet.isdigit() and len(year_sheet) == 4:
                df_year = pd.read_excel(district_file, sheet_name=year_sheet)
                # Get all circle columns (excluding Date column)
                circle_cols = [col for col in df_year.columns if col != 'Date']
                circles.update(circle_cols)
    except Exception as e:
        print(f"    Error reading {district_file.name}: {str(e)}")
    
    return sorted(list(circles))

def create_circle_sheet_for_district(district_file, final_output_folder, all_years):
    """
    Create an Excel file for a district with sheets for each circle
    Each sheet has years as columns and dates as rows
    """
    district_name = district_file.stem
    output_file = final_output_folder / f"{district_name}_Circle_Wise.xlsx"
    
    # Get all circles for this district
    all_circles = get_all_circles_for_district(district_file)
    
    if not all_circles:
        return False
    
    # Dictionary to store data for each circle
    circle_data = {}
    
    # Initialize structure for each circle
    for circle in all_circles:
        circle_data[circle] = {}
    
    # Read data for each year
    years_processed = []
    
    try:
        excel_file = pd.ExcelFile(district_file)
        
        for year_sheet in sorted([s for s in excel_file.sheet_names if s.isdigit() and len(s) == 4]):
            year = year_sheet
            years_processed.append(year)
            
            # Read data for this year
            df_year = pd.read_excel(district_file, sheet_name=year_sheet)
            
            # Get all circle columns for this year
            circle_cols = [col for col in df_year.columns if col != 'Date']
            
            # For each circle, add the data for this year
            for circle in circle_cols:
                if circle not in circle_data:
                    # New circle appears in later years
                    circle_data[circle] = {}
                
                # Create a Series with Date as index and rainfall as values
                for _, row in df_year.iterrows():
                    date = row['Date']
                    rainfall = row[circle]
                    key = (year, date)
                    circle_data[circle][key] = rainfall
    
    except Exception as e:
        print(f"  Error processing {district_name}: {str(e)}")
        return False
    
    # Create Excel file with sheets for each circle
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        circles_processed = 0
        
        for circle in sorted(circle_data.keys()):
            # Build dataframe for this circle
            # Structure: rows = dates, columns = years
            data_dict = {}
            
            for year in all_years:
                if year in years_processed:
                    # Get all dates for this year
                    year_data = {}
                    for (y, date), rainfall in circle_data[circle].items():
                        if y == year:
                            year_data[date] = rainfall
                    
                    # Convert to Series
                    data_dict[year] = pd.Series(year_data)
                else:
                    # Year not available in district file
                    data_dict[year] = pd.Series(dtype='float64')
            
            # Create DataFrame
            df_circle = pd.DataFrame(data_dict)
            
            # Fill NaN with appropriate values
            df_circle = df_circle.fillna('NA')
            
            # Sort index (dates) chronologically
            # Convert date strings to datetime for sorting
            try:
                # Try to parse dates like "01-Jun"
                df_circle.index = pd.to_datetime(df_circle.index + f"-{all_years[0]}", format='%d-%b-%Y', errors='ignore')
                df_circle = df_circle.sort_index()
                # Convert back to original date format
                df_circle.index = df_circle.index.strftime('%d-%b')
            except:
                # If sorting fails, keep as is
                pass
            
            # Write to Excel
            sheet_name = circle[:31]  # Excel sheet name limit
            df_circle.to_excel(writer, sheet_name=sheet_name)
            circles_processed += 1
    
    return circles_processed > 0

def reorganize_to_circle_wise(temp_district_folder, final_output_folder):
    """
    Reorganize data from district-year to district-circle structure
    """
    print("\n" + "=" * 70)
    print("STEP 3: Creating circle-wise Excel files (FINAL OUTPUT)...")
    print("=" * 70)
    
    # Get all district files
    district_files = list(temp_district_folder.glob('*.xlsx'))
    
    if not district_files:
        print(f"\nERROR: No Excel files found")
        return False
    
    print(f"\nFound {len(district_files)} district files")
    
    # Get all years from all files
    print("\nScanning for available years...")
    all_years = get_all_years_from_district_files(temp_district_folder)
    print(f"Found {len(all_years)} years: {all_years[0]} - {all_years[-1]}")
    
    # Create final output folder
    final_output_folder.mkdir(exist_ok=True)
    
    # Process each district
    print("\nCreating circle-wise Excel files...")
    print("-" * 50)
    
    successful_districts = []
    
    for district_file in district_files:
        try:
            if create_circle_sheet_for_district(district_file, final_output_folder, all_years):
                successful_districts.append(district_file.stem)
                if len(successful_districts) % 10 == 0:
                    print(f"  Processed {len(successful_districts)}/{len(district_files)} districts...")
        except Exception as e:
            print(f"  ✗ Error processing {district_file.stem}: {str(e)}")
    
    print(f"\n✓ Created {len(successful_districts)} circle-wise district files")
    
    return len(successful_districts) > 0

def cleanup_temp_folders(temp_folders):
    """
    Delete temporary folders after processing
    """
    print("\n" + "=" * 70)
    print("Cleaning up temporary files...")
    print("=" * 70)
    
    for folder in temp_folders:
        if folder and folder.exists():
            try:
                shutil.rmtree(folder)
                print(f"  ✓ Deleted: {folder.name}")
            except Exception as e:
                print(f"  ✗ Could not delete {folder.name}: {str(e)}")

def main():
    """
    Main function to process all steps sequentially and keep only final output
    """
    print("=" * 70)
    print("COMPLETE RAINFALL DATA PROCESSING PIPELINE")
    print("=" * 70)
    print("\nThis script performs three steps:")
    print("  1. Convert raw Excel files → Year-wise organized files")
    print("  2. Convert year-wise files → District-wise files")
    print("  3. Convert district-wise files → Circle-wise files")
    print("\n⚠️  NOTE: Only the final output (Circle-wise files) will be saved")
    print("   Intermediate files will be automatically deleted")
    print("=" * 70)
    
    # Get script location
    script_location = Path(__file__).parent.absolute()
    
    # STEP 1: Get base path from user input
    print("\n" + "=" * 70)
    print("STEP 1: Processing raw Excel files")
    print("=" * 70)
    
    print("\nPlease enter the path to the folder containing year folders (1997, 1998, etc.)")
    print("Example: C:\\Users\\Swapnali\\Desktop\\Web Scrapping\\Output of Web Scrapping\\All_Years_1997_2024")
    base_path = input("\nEnter path: ").strip()
    
    # Remove quotes if present
    base_path = base_path.strip('"').strip("'")
    
    # Validate base path
    base_path_obj = Path(base_path)
    if not base_path_obj.exists():
        print(f"\nERROR: Path does not exist: {base_path}")
        return
    
    if not base_path_obj.is_dir():
        print(f"\nERROR: Path is not a directory: {base_path}")
        return
    
    print(f"\nBase path accepted: {base_path}")
    
    # Find all year folders
    year_folders = []
    for item in base_path_obj.iterdir():
        if item.is_dir() and re.match(r'^\d{4}$', item.name):
            year_folders.append(item)
    
    if not year_folders:
        print(f"\nERROR: No year folders found in: {base_path}")
        return
    
    year_folders.sort()
    
    print(f"\nFound year folders: {year_folders[0].name} to {year_folders[-1].name}")
    print(f"Total: {len(year_folders)} years")
    
    # Create temporary folders for intermediate processing
    temp_folder = script_location / "__temp_rainfall_processing"
    temp_year_folder = temp_folder / "Year_Wise"
    temp_district_folder = temp_folder / "District_Wise"
    
    temp_year_folder.mkdir(parents=True, exist_ok=True)
    temp_district_folder.mkdir(parents=True, exist_ok=True)
    
    # Create final output folder
    final_output_folder = script_location / "Rainfall_Circle_Wise_Final"
    
    # STEP 1: Process each year folder
    print("\n" + "=" * 70)
    print("STEP 1: Processing raw data into year-wise files...")
    print("=" * 70)
    
    successful_years = []
    
    for year_folder in year_folders:
        print(f"\n{'-' * 50}")
        try:
            if process_year_folder(year_folder, temp_year_folder):
                successful_years.append(year_folder.name)
        except Exception as e:
            print(f"  ✗ Error processing {year_folder.name}: {str(e)}")
    
    print(f"\n✓ Step 1 complete: {len(successful_years)}/{len(year_folders)} years processed")
    
    if not successful_years:
        print("\nERROR: No years were successfully processed")
        cleanup_temp_folders([temp_folder])
        return
    
    # STEP 2: Reorganize to district-wise
    print("\n" + "=" * 70)
    print("STEP 2: Converting to district-wise format...")
    print("=" * 70)
    
    district_success = reorganize_to_district_wise(temp_year_folder, temp_district_folder, successful_years)
    
    if not district_success:
        print("\nERROR: Failed to create district-wise files")
        cleanup_temp_folders([temp_folder])
        return
    
    # STEP 3: Reorganize to circle-wise (FINAL OUTPUT)
    circle_success = reorganize_to_circle_wise(temp_district_folder, final_output_folder)
    
    if not circle_success:
        print("\nERROR: Failed to create final circle-wise files")
        cleanup_temp_folders([temp_folder])
        return
    
    # Clean up temporary folders
    cleanup_temp_folders([temp_folder])
    
    # Print final summary
    print("\n" + "=" * 70)
    print("✅ PROCESSING COMPLETE!")
    print("=" * 70)
    
    print(f"\n📁 FINAL OUTPUT SAVED IN: {final_output_folder}")
    print("\n📊 Output files:")
    print("   Each file is named: [District_Name]_Circle_Wise.xlsx")
    print("   Each file contains:")
    print("     • One sheet per circle in that district")
    print("     • Years as column headers")
    print("     • Dates (01-Jun to 31-Oct) as row headers")
    print("     • Missing data filled with 'NA'")
    
    # List the created files
    final_files = list(final_output_folder.glob('*.xlsx'))
    if final_files:
        print(f"\n📄 Created {len(final_files)} district files:")
        for f in final_files[:10]:  # Show first 10
            print(f"   • {f.name}")
        if len(final_files) > 10:
            print(f"   ... and {len(final_files) - 10} more")
    
    print("\n" + "=" * 70)
    print("✨ Intermediate files have been automatically deleted.")
    print("   Only the final circle-wise output remains.")
    print("=" * 70)

if __name__ == "__main__":
    main()