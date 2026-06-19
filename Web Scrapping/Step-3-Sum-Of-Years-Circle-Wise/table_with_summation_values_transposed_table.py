import pandas as pd
import os
from pathlib import Path
import re
import numpy as np

def process_circle_sheet(df_circle, circle_name):
    """
    Process a circle sheet: calculate total rainfall for each year
    df_circle has dates as rows, years as columns
    """
    # Make a copy to avoid modifying original
    df = df_circle.copy()
    
    # Calculate totals for each year column
    totals = {}
    for year_col in df.columns:
        # Convert column to numeric, coerce errors to NaN
        numeric_col = pd.to_numeric(df[year_col], errors='coerce')
        # Sum ignoring NaN
        total = numeric_col.sum()
        if pd.notna(total) and total != 0:
            totals[year_col] = total
        else:
            totals[year_col] = ''
    
    return totals

def process_district_file(file_path):
    """
    Process a district Excel file: read all sheets (circles) and calculate total rainfall per year
    """
    district_name = Path(file_path).stem
    print(f"  Processing: {district_name}")
    
    try:
        excel_file = pd.ExcelFile(file_path)
        sheets = excel_file.sheet_names
        
        # Dictionary to store total rainfall for each circle
        circle_totals = {}
        
        for sheet_name in sheets:
            # Read sheet with date as index
            df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=0)
            
            # Clean up column names (years) - remove any non-digit characters
            df.columns = [str(col).strip() for col in df.columns]
            
            # Filter only year columns (4-digit numbers)
            year_columns = [col for col in df.columns if col.isdigit() and len(col) == 4]
            
            if not year_columns:
                print(f"    Warning: No year columns found in sheet '{sheet_name}', skipping")
                continue
            
            # Keep only year columns
            df = df[year_columns]
            
            # Calculate totals for this circle
            totals = process_circle_sheet(df, sheet_name)
            
            # Add to dictionary
            circle_totals[sheet_name] = totals
        
        if not circle_totals:
            print(f"    No valid data found in {district_name}")
            return None
        
        # Create DataFrame from circle_totals
        # Get all unique years across all circles
        all_years = set()
        for totals in circle_totals.values():
            all_years.update(totals.keys())
        all_years = sorted([int(y) for y in all_years if y])
        
        # Build the dataframe
        data = []
        for circle_name, totals in circle_totals.items():
            row = {'Circle': circle_name}
            for year in all_years:
                year_str = str(year)
                value = totals.get(year_str, '')
                # Convert to number if possible
                if value != '' and pd.notna(value):
                    row[year] = value
                else:
                    row[year] = ''
            data.append(row)
        
        # Create DataFrame
        result_df = pd.DataFrame(data)
        result_df.set_index('Circle', inplace=True)
        
        # Sort years
        year_cols = sorted([col for col in result_df.columns if isinstance(col, int) or col.isdigit()])
        result_df = result_df[year_cols]
        
        # Replace empty strings with NaN
        result_df = result_df.replace('', np.nan)
        
        print(f"    Processed {len(circle_totals)} circles")
        return result_df
    
    except Exception as e:
        print(f"    Error processing {district_name}: {str(e)}")
        return None

def create_monsoon_summation(input_folder, output_folder):
    """
    Create Monsoon_Summation.xlsx with district sheets
    """
    print("\n" + "=" * 70)
    print("CREATING MONSOON SUMMATION FILE")
    print("=" * 70)
    
    # Find all Excel files
    excel_files = list(input_folder.glob('*.xlsx')) + list(input_folder.glob('*.xls'))
    
    if not excel_files:
        print(f"\nERROR: No Excel files found in {input_folder}")
        return False
    
    print(f"\nFound {len(excel_files)} Excel files")
    print("-" * 50)
    
    # Store all district summaries
    district_summaries = {}
    
    for excel_file in excel_files:
        district_df = process_district_file(excel_file)
        if district_df is not None and not district_df.empty:
            district_name = Path(excel_file).stem
            district_summaries[district_name] = district_df
            print(f"    ✓ {district_name}: {district_df.shape[0]} circles × {district_df.shape[1]} years")
        else:
            print(f"    ✗ Failed to process {excel_file.name}")
    
    if not district_summaries:
        print("\nERROR: No valid district data generated")
        return False
    
    # Create output file
    output_file = output_folder / "Monsoon_Summation.xlsx"
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for district_name, summary_df in district_summaries.items():
            # Sheet name limited to 31 characters
            sheet_name = district_name[:31]
            summary_df.to_excel(writer, sheet_name=sheet_name)
            print(f"  ✓ Added sheet: {district_name}")
    
    print(f"\n{'=' * 70}")
    print(f"SUCCESS! Monsoon Summation file created:")
    print(f"  Location: {output_file}")
    print(f"  Sheets: {', '.join(district_summaries.keys())}")
    
    return True

def verify_output(output_file):
    """
    Verify the output file
    """
    if not output_file.exists():
        print(f"\nERROR: Output file not found: {output_file}")
        return
    
    print("\n" + "=" * 70)
    print("VERIFYING OUTPUT")
    print("=" * 70)
    
    excel_file = pd.ExcelFile(output_file)
    print(f"\nFile: {output_file.name}")
    print(f"Sheets: {', '.join(excel_file.sheet_names)}")
    
    # Show preview of first sheet
    first_sheet = excel_file.sheet_names[0]
    df_sample = pd.read_excel(output_file, sheet_name=first_sheet, index_col=0)
    
    print(f"\nPreview of '{first_sheet}' sheet:")
    print(f"  Shape: {df_sample.shape[0]} circles × {df_sample.shape[1]} years")
    
    # Show year range
    year_cols = df_sample.columns.tolist()
    if year_cols:
        print(f"  Year range: {year_cols[0]} - {year_cols[-1]}")
    
    print(f"  First 3 circles: {', '.join(df_sample.index[:3])}")
    print(f"\n  Sample data (first 3 circles, first 3 years):")
    print(df_sample.iloc[:3, :3])

def main():
    """
    Main function
    """
    print("\n" + "=" * 70)
    print("MONSOON SUMMATION GENERATOR")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Read all Excel files from the input folder")
    print("  2. Each file represents a district, each sheet is a circle")
    print("  3. Calculate total rainfall per circle per year")
    print("  4. Create Monsoon_Summation.xlsx with one sheet per district")
    print("=" * 70)
    
    # Get input folder from user
    print("\nPlease enter the path to the folder containing district Excel files")
    print("(Each file should be named after a district, with circle sheets inside)")
    input_path = input("\nEnter path: ").strip()
    input_path = input_path.strip('"').strip("'")
    
    input_folder = Path(input_path)
    
    # Validate input folder
    if not input_folder.exists():
        print(f"\nERROR: Input folder does not exist: {input_folder}")
        return
    
    if not input_folder.is_dir():
        print(f"\nERROR: Path is not a directory: {input_folder}")
        return
    
    # Get script location for output
    script_location = Path(__file__).parent.absolute()
    output_folder = script_location / "Monsoon_Summation_Output"
    output_folder.mkdir(exist_ok=True)
    
    print(f"\nInput folder: {input_folder}")
    print(f"Output folder: {output_folder}")
    print("=" * 70)
    
    # Create Monsoon Summation file
    success = create_monsoon_summation(input_folder, output_folder)
    
    if success:
        output_file = output_folder / "Monsoon_Summation.xlsx"
        
        # Verify the output
        print("\n" + "=" * 70)
        verify_output = input("Would you like to verify the output? (Y/n): ").strip().lower()
        if verify_output != 'n':
            verify_output(output_file)
        
        print("\n" + "=" * 70)
        print("PROCESSING COMPLETE!")
        print("=" * 70)
        print(f"\nOutput location: {output_folder}")
        print("\nOutput file: Monsoon_Summation.xlsx")
        print("  - One sheet per district")
        print("  - Rows: Circle names")
        print("  - Columns: Years")
        print("  - Values: Total rainfall for that circle in that year")
    else:
        print("\nERROR: Failed to create Monsoon Summation file")

if __name__ == "__main__":
    main()