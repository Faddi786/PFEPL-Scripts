import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io
import os
import pandas as pd
import re
from pathlib import Path
import tempfile
import shutil


# ========================= CONFIG =========================
# Default paths (can be overridden by Excel data)
FONT_PATH = r"C:\Windows\Fonts\arial.ttf"
FONT_SIZE = 13

# Graph Date Change (Residuals) Settings
GRAPH_RECT_H_PADDING = 8
GRAPH_RECT_V_PADDING = 4
GRAPH_DATE_Y_SHIFT = 5          # Positive = move text DOWN

# Report Date Change (Tracking Summary) Settings
REPORT_RECT_H_PADDING = 8
REPORT_RECT_V_PADDING = 4
REPORT_LEFT_X = 90              # X coordinate of left date
REPORT_LEFT_Y = 6               # Y coordinate of left date
REPORT_RIGHT_PADDING = 11       # Distance from RIGHT edge of image
REPORT_RIGHT_Y = 6              # Y coordinate of right date
# =========================================================


def get_file_path(prompt, file_type="file"):
    """Get file path from user input"""
    path = input(prompt).strip().strip('"')
    
    if path.lower() == 'done':
        return None
    
    while not os.path.exists(path):
        print(f"File not found: {path}")
        path = input(prompt).strip().strip('"')
        if path.lower() == 'done':
            return None
    
    return path


def get_residuals_data_from_excel(excel_path):
    """Extract Residuals data from Excel file"""
    try:
        df = pd.read_excel(excel_path, sheet_name='Residuals')
        residuals_data = []
        
        for idx, row in df.iterrows():
            merged_range = row['Merged Date-Time Range']
            start_page = int(row['Start Page'])
            end_page = int(row['End Page'])
            
            # Parse merged range to get the date-time string
            if pd.notna(merged_range):
                new_date = merged_range
            else:
                modified_start = row['Modified Start Date-Time']
                modified_end = row['Modified End Date-Time']
                if pd.notna(modified_start) and pd.notna(modified_end):
                    new_date = f"{modified_start} - {modified_end}"
                else:
                    continue
            
            residuals_data.append({
                'new_date': new_date,
                'start_page': start_page,
                'end_page': end_page
            })
        
        return residuals_data
    except Exception as e:
        print(f"Error reading Residuals sheet: {e}")
        return []


def get_tracking_summary_data_from_excel(excel_path):
    """Extract Tracking Summary data from Excel file"""
    try:
        df = pd.read_excel(excel_path, sheet_name='Tracking Summary')
        tracking_data = []
        
        for idx, row in df.iterrows():
            modified_start = row['Modified Start Date-Time']
            modified_end = row['Modified End Date-Time']
            start_page = int(row['Start Page'])
            end_page = int(row['End Page'])
            
            if pd.notna(modified_start) and pd.notna(modified_end):
                tracking_data.append({
                    'new_left_date': modified_start,
                    'new_right_date': modified_end,
                    'start_page': start_page,
                    'end_page': end_page
                })
        
        return tracking_data
    except Exception as e:
        print(f"Error reading Tracking Summary sheet: {e}")
        return []


def update_graph_date_on_page(page, new_date, font):
    """Update date on a single graph page"""
    image_list = page.get_images(full=True)
    processed = 0
    
    for img_info in image_list:
        xref = img_info[0]
        base_image = page.parent.extract_image(xref)
        image_bytes = base_image["image"]
        
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = pil_img.size
        
        draw = ImageDraw.Draw(pil_img)
        text_width = draw.textlength(new_date, font=font)
        x = (width - text_width) // 2
        
        # Bottom date positioning
        y_lower = height - 42 + 8 + GRAPH_DATE_Y_SHIFT
        draw.rectangle([
            (x - GRAPH_RECT_H_PADDING, y_lower - GRAPH_RECT_V_PADDING),
            (x + text_width + GRAPH_RECT_H_PADDING, y_lower + 22 + GRAPH_RECT_V_PADDING)
        ], fill="white")
        draw.text((x, y_lower), new_date, font=font, fill=(0, 0, 0))
        
        # Replace image in PDF
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format="PNG", optimize=False)
        page.replace_image(xref, stream=img_byte_arr.getvalue())
        processed += 1
    
    return processed


def update_report_dates_on_page(page, new_left_date, new_right_date, font):
    """Update dates on a single report page"""
    image_list = page.get_images(full=True)
    processed = 0
    
    for img_info in image_list:
        xref = img_info[0]
        base_image = page.parent.extract_image(xref)
        image_bytes = base_image["image"]
        
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = pil_img.size
        
        draw = ImageDraw.Draw(pil_img)
        
        # Left date
        left_width = draw.textlength(new_left_date, font=font)
        draw.rectangle([
            (REPORT_LEFT_X - REPORT_RECT_H_PADDING, REPORT_LEFT_Y - REPORT_RECT_V_PADDING),
            (REPORT_LEFT_X + left_width + REPORT_RECT_H_PADDING, REPORT_LEFT_Y + 22 + REPORT_RECT_V_PADDING)
        ], fill="white")
        draw.text((REPORT_LEFT_X, REPORT_LEFT_Y), new_left_date, font=font, fill=(0, 0, 0))
        
        # Right date
        right_width = draw.textlength(new_right_date, font=font)
        RIGHT_X = width - right_width - REPORT_RIGHT_PADDING
        draw.rectangle([
            (RIGHT_X - REPORT_RECT_H_PADDING, REPORT_RIGHT_Y - REPORT_RECT_V_PADDING),
            (RIGHT_X + right_width + REPORT_RECT_H_PADDING, REPORT_RIGHT_Y + 22 + REPORT_RECT_V_PADDING)
        ], fill="white")
        draw.text((RIGHT_X, REPORT_RIGHT_Y), new_right_date, font=font, fill=(0, 0, 0))
        
        # Replace image
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format="PNG", optimize=False)
        page.replace_image(xref, stream=img_byte_arr.getvalue())
        processed += 1
    
    return processed


def process_pdf_updates(pdf_path, residuals_data, tracking_data, output_pdf_path):
    """Apply all date updates to a single PDF and save as new file"""
    
    # Create a temporary copy of the PDF
    temp_dir = tempfile.mkdtemp()
    temp_pdf = os.path.join(temp_dir, "temp_working_copy.pdf")
    shutil.copy2(pdf_path, temp_pdf)
    
    # Open the temporary PDF for editing
    doc = fitz.open(temp_pdf)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    
    total_graph_updates = 0
    total_report_updates = 0
    
    # Process Graph (Residuals) updates
    if residuals_data:
        print("\n📊 PROCESSING GRAPHS (Residuals Section)")
        print("-" * 40)
        
        for item in residuals_data:
            start_page = item['start_page']
            end_page = item['end_page']
            new_date = item['new_date']
            
            print(f"  Pages {start_page}-{end_page}: {new_date}")
            
            for page_num in range(start_page - 1, end_page):
                if page_num < len(doc):
                    page = doc[page_num]
                    processed = update_graph_date_on_page(page, new_date, font)
                    total_graph_updates += processed
                    if processed > 0:
                        print(f"    Page {page_num + 1}: updated {processed} image(s)")
    
    # Process Report (Tracking Summary) updates
    if tracking_data:
        print("\n📄 PROCESSING REPORTS (Tracking Summary Section)")
        print("-" * 40)
        
        for item in tracking_data:
            start_page = item['start_page']
            end_page = item['end_page']
            new_left_date = item['new_left_date']
            new_right_date = item['new_right_date']
            
            print(f"  Pages {start_page}-{end_page}: {new_left_date} | {new_right_date}")
            
            for page_num in range(start_page - 1, end_page):
                if page_num < len(doc):
                    page = doc[page_num]
                    processed = update_report_dates_on_page(page, new_left_date, new_right_date, font)
                    total_report_updates += processed
                    if processed > 0:
                        print(f"    Page {page_num + 1}: updated {processed} image(s)")
    
    # Save the final PDF
    doc.save(output_pdf_path, garbage=4, deflate=True, clean=True)
    doc.close()
    
    # Clean up temporary files
    shutil.rmtree(temp_dir)
    
    return total_graph_updates, total_report_updates


def main():
    print("=" * 70)
    print("PDF Date Updater - Single Output PDF")
    print("=" * 70)
    print("\nThis script reads Excel files from the extraction process and")
    print("updates dates in both Graphs (Residuals) and Reports (Tracking Summary).")
    print("All changes are applied to a SINGLE output PDF.")
    print("\nEnter 'done' at any prompt to exit.\n")
    
    processed_summary = []
    
    while True:
        print("\n" + "=" * 50)
        
        # Get Excel file path
        excel_path = get_file_path("\nEnter Excel file path: ")
        if excel_path is None:
            break
        
        # Get PDF file path
        pdf_path = get_file_path("Enter PDF file path: ")
        if pdf_path is None:
            break
        
        # Get output PDF path
        default_output = pdf_path.replace(".pdf", "_Date_Updated.pdf")
        output_prompt = f"Enter output PDF path (press Enter for default: {os.path.basename(default_output)}): "
        output_path = input(output_prompt).strip().strip('"')
        
        if not output_path:
            output_path = default_output
        
        print(f"\n{'='*50}")
        print(f"Excel: {os.path.basename(excel_path)}")
        print(f"PDF: {os.path.basename(pdf_path)}")
        print(f"Output: {os.path.basename(output_path)}")
        print(f"{'='*50}")
        
        # Get data from Excel
        residuals_data = get_residuals_data_from_excel(excel_path)
        tracking_data = get_tracking_summary_data_from_excel(excel_path)
        
        if not residuals_data and not tracking_data:
            print("  No data found in Excel file.")
            continue
        
        # Show summary of what will be updated
        print("\n📋 UPDATE SUMMARY:")
        if residuals_data:
            print(f"  Graphs to update: {len(residuals_data)} section(s)")
            for r in residuals_data:
                print(f"    - Pages {r['start_page']}-{r['end_page']}: {r['new_date']}")
        
        if tracking_data:
            print(f"  Reports to update: {len(tracking_data)} section(s)")
            for t in tracking_data:
                print(f"    - Pages {t['start_page']}-{t['end_page']}: {t['new_left_date']} | {t['new_right_date']}")
        
        confirm = input("\nProceed with updates? (y/n): ").strip().lower()
        if confirm != 'y':
            print("  Skipping...")
            continue
        
        # Process all updates
        try:
            graph_updated, report_updated = process_pdf_updates(
                pdf_path, residuals_data, tracking_data, output_path
            )
            
            processed_summary.append({
                'excel': os.path.basename(excel_path),
                'pdf': os.path.basename(pdf_path),
                'output': os.path.basename(output_path),
                'graph_sections': len(residuals_data),
                'report_sections': len(tracking_data),
                'graph_images': graph_updated,
                'report_images': report_updated
            })
            
            print(f"\n{'='*50}")
            print(f"✓ SUCCESS! PDF updated and saved as:")
            print(f"  {output_path}")
            print(f"\n  Summary:")
            print(f"  - Graph sections: {len(residuals_data)} ({graph_updated} images updated)")
            print(f"  - Report sections: {len(tracking_data)} ({report_updated} images updated)")
            print(f"{'='*50}")
            
        except Exception as e:
            print(f"\n  ✗ Error processing PDF: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("PROCESSING SUMMARY")
    print("=" * 70)
    
    if processed_summary:
        print(f"\nSuccessfully processed {len(processed_summary)} PDF(s):\n")
        for i, summary in enumerate(processed_summary, 1):
            print(f"{i}. Excel: {summary['excel']}")
            print(f"   Input PDF: {summary['pdf']}")
            print(f"   Output PDF: {summary['output']}")
            print(f"   - Graph sections: {summary['graph_sections']} ({summary['graph_images']} images)")
            print(f"   - Report sections: {summary['report_sections']} ({summary['report_images']} images)\n")
    else:
        print("\nNo files were processed.")
    
    print("=" * 70)


if __name__ == "__main__":
    main()