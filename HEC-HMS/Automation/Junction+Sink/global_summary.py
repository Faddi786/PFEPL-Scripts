# -*- coding: utf-8 -*-
print("✅ SCRIPT STARTED: global_summary.py is running")

import os
import shutil
import re
import io
from hms.model import Project
import gc
import time
import sys, os
import os, sys

import os, sys
print("✅ CONFIG IMPORT SUCCESS")

#  Safe path detection: works in CPython and Jython
#  Safe base_dir detection for Python, Jython, and HEC-HMS
if "__file__" in globals():
    base_dir = os.path.dirname(os.path.abspath(__file__))
elif len(sys.argv) > 0:
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    #  Last fallback: current working directory (works inside HEC-HMS)
    base_dir = os.getcwd()


#  Add script folder to sys.path
if base_dir not in sys.path:
    sys.path.append(base_dir)

#  Now safe to import config
# from config import RAW_DIR, proj_dir, target_file, projectPath, runName, years, startMD, endMD, timeStr, controlFile, output_dss_file


def log(msg):
    try:
        print("[auto] " + msg)
    except:
        pass

def _month_full(mon3):
    return {
        "Jan":"January","Feb":"February","Mar":"March","Apr":"April",
        "May":"May","Jun":"June","Jul":"July","Aug":"August",
        "Sep":"September","Oct":"October","Nov":"November","Dec":"December"
    }.get(mon3, mon3)


import csv


def remove_model_dss_file(output_dss_file, target_file, proj_dir):

    if os.path.exists(output_dss_file):
        try:
            os.remove(output_dss_file)
            print("[auto] Removed old DSS file: {}".format(target_file))
        except Exception as e:
            print("[auto] Could not remove DSS file {}: {}".format(target_file, e))
    else:
        print("[auto] No DSS file named {} found in {}".format(target_file, proj_dir))


def export_time_series(proj, run_name, output_folder):
    # Create folder if not exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for element in proj.getBasinElements():
        if element.getType().lower() == "junction" and "dam":
            name = element.getName()
            log("Exporting time series for junction: " + name)
            results = proj.getElementResults(run_name, name)
            if results is None:
                continue

            # results is often a list of dicts or tuples
            out_path = os.path.join(output_folder, name + ".csv")
            with open(out_path, "w") as f:
                writer = csv.writer(f)
                # write header
                if len(results) > 0 and isinstance(results[0], dict):
                    writer.writerow(results[0].keys())
                    for row in results:
                        writer.writerow(row.values())
                else:
                    for row in results:
                        writer.writerow(row)
            log("Saved: " + out_path)



def _set_control_window(ctrl_path, year,startMD, endMD):
    """Update control file start/end dates for given year and specify the DSS file path with wildcard"""
    with io.open(ctrl_path, "r", encoding="utf-8") as f:
        txt = f.read()

    # Debugging: Show part of original control file
    print("\nOriginal control file content for year %d:" % year)
    print(txt[:500])

    # ------------------ Update Start & End Date ------------------
    sDay, sMon3 = startMD
    eDay, eMon3 = endMD

    start_date_pattern = r"^\s*Start Date:\s*(\d{1,2})\s+(\w+)\s+(\d{4})\s*$"
    end_date_pattern = r"^\s*End Date:\s*(\d{1,2})\s+(\w+)\s+(\d{4})\s*$"

    if re.search(start_date_pattern, txt, flags=re.MULTILINE):
        txt = re.sub(start_date_pattern, "Start Date: %s %s %d" % (sDay, _month_full(sMon3), year), txt, flags=re.MULTILINE)
    else:
        print("WARNING: Start Date pattern not found.")

    if re.search(end_date_pattern, txt, flags=re.MULTILINE):
        txt = re.sub(end_date_pattern, "End Date: %s %s %d" % (eDay, _month_full(eMon3), year), txt, flags=re.MULTILINE)
    else:
        print("WARNING: End Date pattern not found.")

    # ------------------ Normalize Start/End Time ------------------
    # Replace any existing time (like 24:00) with 00:00
    txt = re.sub(r"^\s*Start Time:\s*\d{1,2}:\d{2}\s*$", "Start Time: 00:00", txt, flags=re.MULTILINE)
    txt = re.sub(r"^\s*End Time:\s*\d{1,2}:\d{2}\s*$", "End Time: 00:00", txt, flags=re.MULTILINE)

    # ------------------ Update DSS File Path ------------------
    # dss_full_path = base_dss_path
    # print("Setting DSS path to: %s" % dss_full_path)

    # if "DSSFilePath" in txt:
    #     txt = re.sub(r"^.*DSSFilePath.*$", "DSSFilePath: %s" % dss_full_path, txt, flags=re.MULTILINE)
    # else:
    #     txt += "\nDSSFilePath: %s" % dss_full_path

    # ------------------ Debug Final Control File ------------------
    print("\nUpdated control file for year %d:" % year)
    preview = "\n".join([line for line in txt.splitlines() if "Start" in line or "End" in line or "DSSFilePath" in line])
    print(preview)

    # ------------------ Save Changes ------------------
    with io.open(ctrl_path, "w", encoding="utf-8") as f:
        f.write(txt)

    print("Control file updated and saved successfully for year %d." % year)


def _cleanup_results_folder(res_dir):
    """Remove any existing .results files before/after each run"""
    if os.path.isdir(res_dir):
        for f in os.listdir(res_dir):
            if f.lower().endswith(".results"):
                try:
                    os.remove(os.path.join(res_dir, f))
                    log("Deleted old result file: {}".format(f))
                except Exception as e:
                    log("⚠️ Could not delete {}: {}".format(f, e))


def _remove_stale_lock(proj_dir):
    """Delete any .lock file left from HMS"""
    for f in os.listdir(proj_dir):
        if f.lower().endswith(".lock"):
            try:
                os.remove(os.path.join(proj_dir, f))
                log("Removed stale lock: " + f)
            except Exception as e:
                log("⚠️ Could not remove lock: %s" % e)

import os
import csv

def read_inputs_csv(path):
    """
    Reads key-value pairs from a CSV and returns a dict with correct types.
    """
    data = {}

    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["key"].strip()
            val = row["value"].strip()
            data[key] = val

    # ✅ Parse complex fields

    # Convert years like "2007-2010" → range(2007, 2010)
    if "years" in data:
        yrs = data["years"]
        if "-" in yrs:
            start, end = yrs.split("-")
            data["years"] = range(int(start), int(end))
        else:
            data["years"] = [int(yrs)]

    # Convert "01-Jun" to tuple
    if "startMD" in data:
        d, m = data["startMD"].split("-")
        data["startMD"] = (d, m)

    if "endMD" in data:
        d, m = data["endMD"].split("-")
        data["endMD"] = (d, m)
    
    if "stop_years" in data and data["stop_years"].strip():
        data["stop_years"] = [int(y) for y in data["stop_years"].split(",")]
    else:
        data["stop_years"] = []

    return data



def global_summary(projectPath, RAW_DIR, controlFile, years, output_dss_file, runName, startMD, endMD,target_file,stop_years):
    proj_dir = os.path.dirname(projectPath)
    ctrl_path = os.path.join(proj_dir, controlFile)


    #  Remove DSS file for the run before starting
    remove_model_dss_file(output_dss_file, target_file, proj_dir)

    for year in years:
        results_copied = 0  # Initialize the counter for each year

        # === CHECK IF THIS IS A STOP YEAR ===
        if year in stop_years:
            print("\n" + "="*60)
            print("=== STOP YEAR REACHED: %d ===" % year)
            print("="*60)
            response = raw_input("Continue with remaining years? (y/n): ").strip().lower()
            if response != "y":
                print("User chose to stop. Terminating simulation.")
                return  # Exit function → script ends
            else:
                print("Continuing simulation...\n")

        log("="*50)
        log("=== YEAR %d ===" % year)

        # update control period and DSS path with wildcard
        _set_control_window(ctrl_path, year, startMD, endMD)

        # cleanup previous lock
        _remove_stale_lock(proj_dir)

        # Remove old results before running the model
        res_dir = os.path.join(proj_dir, "results")
        _cleanup_results_folder(res_dir)

        # open project
        proj = Project.open(projectPath)
        if proj is None:
            raise RuntimeError("Could not open project")

        try:
            log("Computing run '%s'..." % runName)
            proj.computeRun(runName)

            # Check if results were generated
            res_dir = os.path.join(proj_dir, "results")
            if not os.path.isdir(res_dir):
                print(" No results folder found.")
            else:
                # Filter result files for 'Run 1' only
                result_files = [f for f in os.listdir(res_dir) if f.lower().endswith(".results")]
                
                if not result_files:
                    print(" No .results files generated for {}.".format(runName))
                else:
                    # Copy results for 'Run 1' and include the year in the result file name
                    # Copy results for 'Run 1' and include the year in the result file name
                    for f in result_files:
                        src = os.path.join(res_dir, f)
                        base, ext = os.path.splitext(f)
                        
                        # Create a new result file name by appending the year
                        result_file_name = "RUN_Run_1_" + str(year) + ".results"
                        
                        # Define the destination where you want to store results (with the year appended)
                        dst = os.path.join(RAW_DIR, result_file_name)  # Use the modified name for the result file
                        
                        # Avoid overwriting by renaming the source file or copying to a new file with year
                        shutil.copy2(src, dst)
                        print("Copied -> " + dst)
                        results_copied += 1  # Increment the counter



            # #  CALL THE EXPORT FUNCTION HERE (after results are generated)
            # time_series_output = os.path.join(RAW_DIR, "time_series_" + str(year) + ".xlsx")
            # export_time_series(proj, runName, time_series_output)


            log(" Completed year %d. Total results copied: %d" % (year, results_copied))

        finally:
            try:
                proj.saveAll()
            except:
                pass

            # Close project & cleanup
            try:
                proj.close()
                log("Closed project successfully.")
            except:
                pass

            # Cleanup: remove copied results from source folder
            _cleanup_results_folder(res_dir)

            gc.collect()
            time.sleep(0)
            _remove_stale_lock(proj_dir)


    log(" All years completed. Results saved in: %s" % RAW_DIR)


def main():
    # 1️⃣ Read config from Excel
    config_path = r"inputs_csv.csv"
    inputs = read_inputs_csv(config_path)

    # 2️⃣ Extract variables
    projectPath = inputs['projectPath']
    RAW_DIR = inputs['RAW_DIR']
    controlFile = inputs['controlFile']
    years = inputs['years']
    output_dss_file = inputs['output_dss_file']
    runName = inputs['runName']
    startMD = inputs['startMD']
    endMD = inputs['endMD']
    target_file = inputs['target_file']
    stop_years      = inputs.get('stop_years', [])

    # 3️⃣ Make sure output folder exists
    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)

    # 4️⃣ Run the model
    global_summary(projectPath, RAW_DIR, controlFile, years, output_dss_file, runName, startMD, endMD,target_file, stop_years)


if __name__ == "__main__":
    main()