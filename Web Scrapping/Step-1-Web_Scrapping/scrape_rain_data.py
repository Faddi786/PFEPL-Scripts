import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import re
from datetime import datetime
import os
from openpyxl import load_workbook

class CircleDailyRainScraper:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.base_url = "https://maharain.maharashtra.gov.in/test/maharain/previous_year_rain.php"
        self.base_output_dir = "CircleWise_DailyRain_Data_2014"
        
        # Define the specific districts to scrape
        self.target_districts = ['Thane', 'Palghar', 'Nashik', 'Raigadh', 'Pune']
        
        # Create base output directory if it doesn't exist
        if not os.path.exists(self.base_output_dir):
            os.makedirs(self.base_output_dir)
            print(f"✓ Created base output directory: {self.base_output_dir}")
    
    def get_district_value(self, district_name):
        """Get the value attribute for a specific district by its name"""
        try:
            district_dropdown = Select(self.driver.find_element(By.ID, "selDistrict"))
            for option in district_dropdown.options:
                if option.text.strip() == district_name:
                    return option.get_attribute('value')
            return None
        except Exception as e:
            print(f"  ✗ Error getting district value for {district_name}: {e}")
            return None
    
    def start_browser(self):
        """Start the browser"""
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.get(self.base_url)
        time.sleep(3)
        print("✓ Browser started")
    
    def select_dropdown(self, dropdown_id, value):
        """Select a value from dropdown by ID"""
        try:
            dropdown = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, dropdown_id))
            ))
            dropdown.select_by_visible_text(value)
            print(f"  ✓ Selected '{value}'")
            time.sleep(1.5)
            return True
        except Exception as e:
            print(f"  ✗ Failed to select '{value}': {e}")
            return False
    
    def select_dropdown_by_value(self, dropdown_id, value):
        """Select a value from dropdown by actual value attribute"""
        try:
            dropdown = Select(self.wait.until(
                EC.presence_of_element_located((By.ID, dropdown_id))
            ))
            dropdown.select_by_value(str(value))
            print(f"  ✓ Selected district")
            time.sleep(1.5)
            return True
        except Exception as e:
            print(f"  ✗ Failed to select district: {e}")
            return False
    
    def setup_circle_daily_rain(self, year, district_value, district_name, month):
        """Setup the dropdowns for Circle Wise - Daily Rain"""
        print(f"\n--- Setting up for {district_name} - {month} {year} ---")
        
        # Step 1: Select "Circle Wise - Reports" from Past Queries
        if not self.select_dropdown("selReports", "Circle Wise - Reports"):
            return False
        
        # Step 2: Select "Daily Rain" from Report Type
        if not self.select_dropdown("selReportType", "Daily Rain"):
            return False
        
        # Step 3: Select Year
        if not self.select_dropdown("selYear", str(year)):
            return False
        
        # Step 4: Select District
        district_dropdown_id = "selDistrict"
        if not self.select_dropdown_by_value(district_dropdown_id, district_value):
            return False
        
        # Step 5: Select Month
        if not self.select_dropdown("selMonth", month):
            return False
        
        return True
    
    def click_submit(self):
        """Click the submit button"""
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit' and contains(text(), 'Submit')]")
            submit_btn.click()
            print("  ✓ Clicked Submit")
            time.sleep(3)
            return True
        except:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//input[@type='submit' and @value='Submit']")
                submit_btn.click()
                print("  ✓ Clicked Submit")
                time.sleep(3)
                return True
            except Exception as e:
                print(f"  ✗ Failed to click Submit: {e}")
                return False
    
    def extract_table(self):
        """Extract the table data"""
        try:
            table = self.driver.find_element(By.ID, "tableID")
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            if len(rows) <= 1:
                print("  ⚠ No data rows found")
                return None
            
            # Find header row
            headers = []
            header_row_index = 0
            
            for i, row in enumerate(rows):
                th_cells = row.find_elements(By.TAG_NAME, "th")
                if th_cells and len(th_cells) > 1:
                    header_row_index = i
                    for th in th_cells:
                        header_text = th.text.strip()
                        if header_text:
                            headers.append(header_text)
                    break
            
            if not headers:
                for i, row in enumerate(rows[:3]):
                    td_cells = row.find_elements(By.TAG_NAME, "td")
                    if td_cells and len(td_cells) > 1:
                        first_cell = td_cells[0].text.strip()
                        if first_cell in ['Sr', 'District', 'Taluka', 'Circle']:
                            header_row_index = i
                            for td in td_cells:
                                headers.append(td.text.strip())
                            break
            
            # Extract data rows
            data = []
            for row in rows[header_row_index + 1:]:
                cells = row.find_elements(By.TAG_NAME, "td")
                if cells:
                    row_data = [cell.text.strip() for cell in cells]
                    if any(row_data):
                        data.append(row_data)
            
            if not data:
                print("  ⚠ No data extracted")
                return None
            
            # Create DataFrame
            max_cols = max(len(row) for row in data)
            
            if len(headers) < max_cols:
                for i in range(len(headers), max_cols):
                    if i == 0:
                        headers.append("Sr")
                    elif i == 1:
                        headers.append("District")
                    elif i == 2:
                        headers.append("Taluka")
                    elif i == 3:
                        headers.append("Circle")
                    else:
                        headers.append(f"Day_{i-3}")
            elif len(headers) > max_cols:
                headers = headers[:max_cols]
            
            for row in data:
                while len(row) < max_cols:
                    row.append("")
            
            df = pd.DataFrame(data, columns=headers)
            
            # Handle duplicate column names
            new_headers = []
            counter = {}
            for h in df.columns:
                if h in counter:
                    counter[h] += 1
                    new_headers.append(f"{h}_{counter[h]}")
                else:
                    counter[h] = 1
                    new_headers.append(h)
            df.columns = new_headers
            
            print(f"  ✓ Extracted {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            print(f"  ✗ Error extracting table: {e}")
            return None
    
    def save_data_immediately(self, year, district_name, month, df):
        """
        Save data immediately to the appropriate folder structure:
        Year folder -> District Excel file -> Month sheet
        """
        # Create year folder
        year_folder = os.path.join(self.base_output_dir, str(year))
        if not os.path.exists(year_folder):
            os.makedirs(year_folder)
        
        # Create filename for this district
        # Clean district name for filename (remove any invalid characters)
        safe_district_name = re.sub(r'[<>:"/\\|?*]', '_', district_name)
        filename = os.path.join(year_folder, f"{safe_district_name}.xlsx")
        sheet_name = month[:31]  # Excel sheet name limit is 31 characters
        
        try:
            # Check if file already exists
            if os.path.exists(filename):
                # Load existing workbook and add/update sheet
                with pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Auto-adjust column widths
                    workbook = writer.book
                    if sheet_name in workbook.sheetnames:
                        worksheet = workbook[sheet_name]
                        for column in worksheet.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            for cell in column:
                                try:
                                    if len(str(cell.value)) > max_length:
                                        max_length = len(str(cell.value))
                                except:
                                    pass
                            adjusted_width = min(max_length + 2, 50)
                            worksheet.column_dimensions[column_letter].width = adjusted_width
            else:
                # Create new file
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Auto-adjust column widths
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Also save a checkpoint to track progress
            self.save_checkpoint(year, district_name, month)
            
            print(f"  ✓ Saved to {year_folder}/{safe_district_name}.xlsx (sheet: {sheet_name})")
            return True
            
        except Exception as e:
            print(f"  ✗ Error saving to Excel: {e}")
            # Fallback: save as CSV
            csv_filename = os.path.join(year_folder, f"{safe_district_name}_{month}.csv")
            df.to_csv(csv_filename, index=False)
            print(f"  ✓ Saved as CSV backup: {csv_filename}")
            return False
    
    def save_checkpoint(self, year, district_name, month):
        """Save checkpoint to track progress"""
        checkpoint_file = os.path.join(self.base_output_dir, "scraping_progress.txt")
        
        try:
            # Read existing checkpoints if any
            completed = set()
            if os.path.exists(checkpoint_file):
                with open(checkpoint_file, 'r') as f:
                    completed = set([line.strip() for line in f.readlines()])
            
            # Add current
            current = f"{year}_{district_name}_{month}"
            if current not in completed:
                completed.add(current)
            
            # Write all checkpoints
            with open(checkpoint_file, 'w') as f:
                for item in sorted(completed):
                    f.write(f"{item}\n")
                    
        except Exception as e:
            print(f"  ⚠ Could not save checkpoint: {e}")
    
    def load_checkpoint(self):
        """Load previously completed extractions"""
        checkpoint_file = os.path.join(self.base_output_dir, "scraping_progress.txt")
        
        completed = set()
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r') as f:
                completed = set([line.strip() for line in f.readlines()])
        
        return completed
    
    def initialize_district_values(self):
        """Get the value attributes for all target districts"""
        print("\n" + "="*80)
        print("INITIALIZING DISTRICT VALUES")
        print("="*80)
        
        # First, navigate to a state where district dropdown is populated
        self.select_dropdown("selReports", "Circle Wise - Reports")
        time.sleep(1)
        self.select_dropdown("selReportType", "Daily Rain")
        time.sleep(1)
        
        # Get values for each target district
        district_info = []
        for district_name in self.target_districts:
            district_value = self.get_district_value(district_name)
            if district_value:
                district_info.append({
                    'name': district_name,
                    'value': district_value
                })
                print(f"✓ Found district: {district_name} (value: {district_value})")
            else:
                print(f"✗ Could not find district: {district_name}")
        
        return district_info
    
    def scrape_all_data(self, start_year, end_year, months, districts_info, resume=True):
        """
        Scrape data for all years, specified districts, and months
        Saves immediately after each successful extraction
        """
        years_list = list(range(start_year, end_year + 1))
        total_combinations = len(years_list) * len(districts_info) * len(months)
        
        # Load previously completed extractions if resuming
        completed = set()
        if resume:
            completed = self.load_checkpoint()
            if completed:
                print(f"\n✓ Found {len(completed)} previously completed extractions")
        
        print("\n" + "="*80)
        print(f"CIRCLE WISE - DAILY RAIN DATA SCRAPER")
        print("="*80)
        print(f"Years: {start_year} to {end_year}")
        print(f"Districts: {', '.join([d['name'] for d in districts_info])}")
        print(f"Months: {', '.join(months)}")
        print(f"Total combinations: {total_combinations}")
        print(f"Resume mode: {'ON (will skip completed)' if resume else 'OFF'}")
        print("="*80)
        
        current = 0
        successful = 0
        skipped = 0
        failed = 0
        
        for year in years_list:
            for district in districts_info:
                district_name = district['name']
                district_value = district['value']
                
                for month in months:
                    current += 1
                    checkpoint_key = f"{year}_{district_name}_{month}"
                    
                    # Skip if already completed
                    if checkpoint_key in completed:
                        print(f"\n[{current}/{total_combinations}] SKIPPING: {year} - {district_name} - {month} (already done)")
                        skipped += 1
                        continue
                    
                    print(f"\n[{current}/{total_combinations}] Processing: {year} - {district_name} - {month}")
                    
                    try:
                        # Setup dropdowns
                        if not self.setup_circle_daily_rain(year, district_value, district_name, month):
                            print(f"  ✗ Failed to setup")
                            failed += 1
                            continue
                        
                        # Click submit
                        if not self.click_submit():
                            print(f"  ✗ Failed to submit")
                            failed += 1
                            continue
                        
                        # Extract table
                        df = self.extract_table()
                        
                        if df is not None and not df.empty:
                            # Save immediately
                            if self.save_data_immediately(year, district_name, month, df):
                                successful += 1
                                print(f"  ✓ Successfully extracted and saved")
                            else:
                                failed += 1
                        else:
                            print(f"  ⚠ No data found")
                            failed += 1
                            
                    except Exception as e:
                        print(f"  ✗ Error: {e}")
                        failed += 1
                    
                    # Small delay between requests
                    time.sleep(1)
        
        # Print summary
        print("\n" + "="*80)
        print("SCRAPING SUMMARY")
        print("="*80)
        print(f"Total combinations: {total_combinations}")
        print(f"✓ Successful: {successful}")
        print(f"⏭ Skipped (already done): {skipped}")
        print(f"✗ Failed: {failed}")
        print(f"\n📁 Output folder: {self.base_output_dir}")
        print("="*80)
        
        return successful
    
    def run(self, start_year=1997, end_year=2024, resume=True):
        """
        Main execution
        
        Args:
            start_year: Starting year (default: 1997)
            end_year: Ending year (default: 2024)
            resume: Resume from where it left off (default: True)
        """
        # Define months to scrape (June to October)
        months = ['June', 'July', 'August', 'September', 'October']
        
        print("\n" + "="*80)
        print("CIRCLE WISE - DAILY RAIN DATA EXTRACTOR")
        print("="*80)
        print(f"\nConfiguration:")
        print(f"  • Report Type: Circle Wise - Daily Rain")
        print(f"  • Year Range: {start_year} to {end_year}")
        print(f"  • Months: {', '.join(months)}")
        print(f"  • Districts: {', '.join(self.target_districts)}")
        print(f"  • Output Structure: {self.base_output_dir}/Year/District.xlsx (with month sheets)")
        print(f"  • Resume Mode: {'ON (will skip already extracted data)' if resume else 'OFF'}")
        print("="*80)
        
        # Calculate total extractions needed
        years_count = end_year - start_year + 1
        districts_count = len(self.target_districts)
        months_count = len(months)
        total = years_count * districts_count * months_count
        print(f"\nTotal extractions needed: {total:,}")
        
        if resume:
            completed = self.load_checkpoint()
            remaining = total - len(completed)
            print(f"Already completed: {len(completed):,}")
            print(f"Remaining to scrape: {max(0, remaining):,}")
        
        confirm = input(f"\nContinue? (y/n): ")
        
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
        
        try:
            # Start browser
            self.start_browser()
            
            # Initialize district values
            districts_info = self.initialize_district_values()
            
            if not districts_info:
                print("✗ No target districts found! Exiting...")
                return
            
            # Scrape data (saves immediately after each extraction)
            successful = self.scrape_all_data(start_year, end_year, months, districts_info, resume)
            
            if successful > 0:
                print(f"\n✅ Successfully extracted and saved {successful} new data points")
                print(f"📁 Files are saved in: {self.base_output_dir}")
                print(f"\nFolder structure:")
                print(f"  {self.base_output_dir}/")
                for year in range(start_year, min(start_year+3, end_year+1)):
                    print(f"    ├── {year}/")
                    for district in self.target_districts:
                        print(f"    │   └── {district}.xlsx (sheets: June, July, Aug, Sep, Oct)")
                if end_year - start_year > 2:
                    print(f"    └── ...")
            else:
                print("\n❌ No new data was extracted")
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Script interrupted by user!")
            print("✅ Data that was already extracted has been saved.")
            print(f"📁 Check the '{self.base_output_dir}' folder for partial results.")
            print("💡 Run the script again - it will resume from where it left off.")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print("\n✅ Previously extracted data has been saved.")
            print("💡 Run the script again to resume from where it left off.")
        
        finally:
            print("\n" + "="*80)
            input("Press Enter to close the browser...")
            if self.driver:
                self.driver.quit()
                print("Browser closed.")


# Quick version for testing a single district
def quick_test():
    """Test with a single year, district, and month"""
    scraper = CircleDailyRainScraper()
    
    try:
        scraper.start_browser()
        
        # Test parameters
        year = 2024
        district_name = "Thane"
        month = "June"
        
        # Initialize district values
        districts_info = scraper.initialize_district_values()
        
        # Find the district
        district_info = None
        for d in districts_info:
            if d['name'] == district_name:
                district_info = d
                break
        
        if district_info:
            print(f"\n--- Testing: {district_name} - {month} {year} ---")
            
            if scraper.setup_circle_daily_rain(year, district_info['value'], district_name, month):
                if scraper.click_submit():
                    df = scraper.extract_table()
                    if df is not None:
                        scraper.save_data_immediately(year, district_name, month, df)
                        print(f"\n✓ Test data saved to {scraper.base_output_dir}")
                        print("\nPreview:")
                        print(df.head())
        
        input("\nPress Enter to close browser...")
        
    finally:
        scraper.driver.quit()


# Main execution
if __name__ == "__main__":
    print("\n" + "="*80)
    print("CIRCLE WISE - DAILY RAIN DATA EXTRACTOR")
    print("="*80)
    print("\nTarget Districts: Thane, Palghar, Nashik, Raigadh, Pune")
    print("="*80)
    
    print("\nSelect mode:")
    print("1. Full Range - Scrape 1997-2024, specified districts, June-October")
    print("2. Custom Range - Specify your own year range")
    print("3. Quick Test - Test with single year/district/month")
    print("4. Resume Only - Continue from where it left off")
    
    choice = input("\nEnter choice (1, 2, 3, or 4): ").strip()
    
    if choice == "1":
        scraper = CircleDailyRainScraper()
        scraper.run(start_year=1997, end_year=2024, resume=True)
        
    elif choice == "2":
        start = int(input("Enter start year: "))
        end = int(input("Enter end year: "))
        scraper = CircleDailyRainScraper()
        scraper.run(start_year=start, end_year=end, resume=True)
        
    elif choice == "3":
        quick_test()
        
    elif choice == "4":
        scraper = CircleDailyRainScraper()
        start = int(input("Enter start year (or press Enter for 1997): ") or "1997")
        end = int(input("Enter end year (or press Enter for 2024): ") or "2024")
        scraper.run(start_year=start, end_year=end, resume=True)
        
    else:
        print("Invalid choice. Exiting.")