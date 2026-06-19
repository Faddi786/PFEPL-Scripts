import subprocess
import win32com.client as win32
import os
import sys

# ---------------- CONFIG ----------------
PYTHON_SCRIPT = "export_subbasin_report.py"
EXCEL_FILE = "Subbasin_Report_with_Percentage.xlsx"
VBA_TXT_FILE = "theisan plygon percentage nikalo.txt"
VBA_MACRO_NAME = "CalculateStationPercentage"
# ---------------------------------------


def run_python_report():
    print("▶ Running report generation script...")
    subprocess.check_call([sys.executable, PYTHON_SCRIPT])
    print("✔ Report generated successfully\n")


def run_vba_macro():
    print("▶ Running VBA percentage calculation...")

    # Read VBA code
    with open(VBA_TXT_FILE, "r", encoding="utf-8") as f:
        vba_code = f.read()

    excel = win32.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    wb = excel.Workbooks.Open(os.path.abspath(EXCEL_FILE))

    # Add VBA module
    vb_module = wb.VBProject.VBComponents.Add(1)  # 1 = Standard Module
    vb_module.CodeModule.AddFromString(vba_code)

    # Run macro
    excel.Application.Run(VBA_MACRO_NAME)

    # Save and close
    wb.Save()
    wb.Close()
    excel.Quit()

    print("✔ Percentage calculated and Excel file saved\n")


def main():
    run_python_report()

    choice = input("Do you want to calculate percentage? (Y/N): ").strip().lower()

    if choice in ["y", "yes"]:
        run_vba_macro()
    else:
        print("ℹ Percentage calculation skipped.")

    print("✅ Task completed successfully.")


if __name__ == "__main__":
    main()
