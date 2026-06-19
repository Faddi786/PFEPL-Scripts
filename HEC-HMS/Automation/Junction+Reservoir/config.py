# -*- coding: utf-8 -*-

import os
import subprocess
import shutil
from datetime import datetime
import re

# ---------------- Hardcoded values (as requested) ----------------
startMD = ("01", "Jun")
endMD   = ("31", "Oct")
timeStr = "00:00"

# ---------------- Interactive User Inputs ----------------
print("\n" + "="*60)
print("    HEC-HMS AUTOMATION SETUP - Please enter the details")
print("="*60 + "\n")

projectPath = input("1. Full path to your .hms project file\n   (e.g. C:\\Users\\YourName\\Desktop\\Pise.hms): ").strip()
while not projectPath.lower().endswith(".hms") or not os.path.isfile(projectPath):
    print("   Invalid or file not found! Please enter a valid .hms file path.")
    projectPath = input("   Try again: ").strip()

controlFile = input("\n2. Control file name (usually inside project folder)\n   (e.g. Vaitarna.control): ").strip()
if not controlFile:
    controlFile = "Control.control"  # fallback

runName = input("\n3. Run name in HEC-HMS (exactly as shown in HMS)\n   (e.g. Vaitarna Run (W-Dams)): ").strip()
if not runName:
    print("   Run name cannot be empty!")
    exit(1)

syear_input = input("\n4. Start year (e.g. 2016): ").strip()
eyear_input = input("5. End year (e.g. 2024): ").strip()

try:
    syear = int(syear_input)
    eyear = int(eyear_input)
    if syear > eyear:
        print("   Start year cannot be greater than end year!")
        exit(1)
    years = range(syear, eyear + 1)
except ValueError:
    print("   Please enter valid numbers for years!")
    exit(1)

stop_years_input = input("\n6. Stop years (optional, comma-separated, e.g. 2018,2020)\n   Leave empty for none: ").strip()
stop_years = [int(y.strip()) for y in stop_years_input.split(",") if y.strip().isdigit()] if stop_years_input else []

batch_file_path = input("\n7. Full path to run_command.bat\n   (e.g. C:\\Users\\Swapnali\\Desktop\\HEC-HMS\\OLD_NEW_2016_2024\\run_command.bat): ").strip()
while not os.path.isfile(batch_file_path):
    print("   File not found! Please check the path.")
    batch_file_path = input("   Try again: ").strip()

special_word = input("\n8. Enter the special word to add at the end of the output folder's name: ").strip()

print("\n" + "="*60)
print("   All inputs received! Starting simulation...")
print("="*60 + "\n")

# ---------------- Rest of your original code (unchanged below) ----------------

def run_bat_file(bat_path):
    try:
        process = subprocess.Popen(bat_path, shell=True)
        process.wait()
    except Exception as e:
        print("Error running batch file:", e)

# Lazy imports...
def run_exports(RAW_DIR, CSV_DIR, global_summary_excel):
    from excel import result_to_csv, csvs_transposed
    result_to_csv(RAW_DIR, CSV_DIR)
    junctions_list = csvs_transposed(CSV_DIR, global_summary_excel)
    return junctions_list

def run_global_summary():
    from global_summary import global_summary
    global_summary()

def run_timeseries(global_summary_excel, output_dss_file, timeseries_excel, for_all_years):
    from timeseries import timeseries
    timeseries(global_summary_excel, output_dss_file, timeseries_excel, for_all_years)

def run_dependibility(global_summary_excel):
    from seventy_five_dependiblity import seventy_five_dependiblity
    seventy_five_dependiblity(global_summary_excel)

def run_index(index_excel, global_summary_excel, timeseries_excel, junctions_list):
    from excel import build_navigation_index
    build_navigation_index(
        index_path=index_excel,
        global_summary_path=global_summary_excel,
        timeseries_path=timeseries_excel,
        junctions=junctions_list
    )

# --- Directory creation, CSV save, etc. (your original code continues below) ---
RAW_DIR = None
CSV_DIR = None
current_output_dir = None
index_excel = None
global_summary_excel = None
timeseries_excel = None
output_dss_file = None

import csv

def save_inputs_to_csv(filepath, target_file):
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "value"])
        writer.writerow(["projectPath", projectPath])
        writer.writerow(["RAW_DIR", RAW_DIR])
        writer.writerow(["controlFile", controlFile])
        writer.writerow(["years", f"{syear}-{eyear}"])
        writer.writerow(["output_dss_file", output_dss_file])
        writer.writerow(["runName", runName])
        writer.writerow(["startMD", "01-Jun"])
        writer.writerow(["endMD", "31-Oct"])
        writer.writerow(["target_file", target_file])
        writer.writerow(["stop_years", ",".join(map(str, stop_years))])
    print("Saved inputs to CSV:", filepath)

def create_dirs():
    global RAW_DIR, CSV_DIR, current_output_dir, index_excel, global_summary_excel, timeseries_excel, output_dss_file

    project_name = os.path.splitext(os.path.basename(projectPath))[0]
    timestamp = datetime.now().strftime("(%d_%B_%Y)_(%I_%M_%p)")
    proj_dir = os.path.dirname(projectPath)
    safe_name = re.sub(r'[^A-Za-z0-9]', '_', runName.strip())
    target_file = f"{safe_name}.dss"
    output_dss_file = os.path.join(proj_dir, target_file)

    RAW_DIR = os.path.join(os.getcwd(), f"processing_results_and_csvs\\{project_name}_{timestamp}\\results_raw")
    CSV_DIR = os.path.join(os.getcwd(), f"processing_results_and_csvs\\{project_name}_{timestamp}\\results_csv")
    # special_word = "Vaitarna_Run_1975_1999" # 1975_1999 2016_2024 Vaitarna Ulhas
    current_output_dir = os.path.join(os.getcwd(), "output", "{0}_{1}_{2}".format(project_name, timestamp, special_word))
    # current_output_dir = os.path.join(os.getcwd(), "output", f"{project_name}_{timestamp}_Vaitarna_Run_2016_2024")

    for folder in [current_output_dir, RAW_DIR, CSV_DIR]:
        os.makedirs(folder, exist_ok=True)
        print(f"Created directory: {folder}")

    index_excel = os.path.join(current_output_dir, "index.xlsx")
    global_summary_excel = os.path.join(current_output_dir, "global_summary.xlsx")
    timeseries_excel = os.path.join(current_output_dir, "timeseries_excel.xlsx")

    inputs_path = os.path.join(os.getcwd(), "inputs_csv.csv")
    save_inputs_to_csv(inputs_path, target_file)

def main_gate():
    global RAW_DIR, CSV_DIR, current_output_dir, index_excel, global_summary_excel, timeseries_excel, output_dss_file
    create_dirs()
    run_bat_file(batch_file_path)

    junctions_list = run_exports(RAW_DIR, CSV_DIR, global_summary_excel)
    run_dependibility(global_summary_excel)
    run_timeseries(global_summary_excel, output_dss_file, timeseries_excel, for_all_years=False)
    run_timeseries(global_summary_excel, output_dss_file, timeseries_excel, for_all_years=True)
    run_index(index_excel, global_summary_excel, timeseries_excel, junctions_list)

if __name__ == "__main__":
    import time
    start_time = time.time()
    main_gate()
    total = time.time() - start_time
    h, m = divmod(total, 3600)
    m, s = divmod(m, 60)
    print(f"\nTotal runtime: {int(h):02d}:{int(m):02d}:{int(s):02d}")