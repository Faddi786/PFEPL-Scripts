# -*- coding: utf-8 -*-
"""
Parse XML-based HEC-HMS *.results files and export summary metrics to CSV.
Author: PFEPL Automation
"""

import os
import csv
import xml.etree.ElementTree as ET

# === Paths ===
RAW_DIR = r"C:\Users\USER\Desktop\sakina_script\Hec_hms_model_run_automation\results_raw"
OUT_DIR = r"C:\Users\USER\Desktop\sakina_script\Hec_hms_model_run_automation\results_csv"

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

def safe_text(elem, attr):
    """Return float or text safely"""
    if elem is None:
        return ""
    val = elem.attrib.get(attr, "")
    try:
        return float(val)
    except:
        return val

def parse_results_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    rows = []
    for basin in root.findall("BasinElement"):
        name = basin.attrib.get("name", "")
        btype = basin.attrib.get("type", "")
        area_elem = basin.find("DrainageArea")
        area = safe_text(area_elem, "area")

        # Find desired metrics inside <Statistics>
        stats = {m.attrib.get("displayString"): m.attrib for m in basin.findall("Statistics/StatisticMeasure")}

        # Extract key measures
        peak_discharge = stats.get("Maximum Outflow", {}).get("value", "")
        time_of_peak   = stats.get("Time of Maximum Outflow", {}).get("value", "")
        volume_m3      = stats.get("Outflow Volume", {}).get("value", "")
        volume_units   = stats.get("Outflow Volume", {}).get("units", "M3")
        vol_mm         = stats.get("Outflow Depth", {}).get("value", "")

        rows.append({
            "Hydrologic Element": name,
            "Type": btype,
            "Drainage Area (KM2)": area,
            "Peak Discharge (M3/S)": peak_discharge,
            "Time of Peak": time_of_peak,
            "Volume (MM)": vol_mm,
            "Volume (M3)": volume_m3,
            "Volume Units": volume_units
        })
    return rows

def main():
    for file in os.listdir(RAW_DIR):
        if not file.lower().endswith(".results"):
            continue
        path = os.path.join(RAW_DIR, file)
        try:
            rows = parse_results_xml(path)
            if not rows:
                print(f"⚠️ No BasinElements found in {file}")
                continue

            out_csv = os.path.join(OUT_DIR, file.replace(".results", ".csv"))
            with open(out_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            print(f"✅ Parsed {file} → {out_csv} ({len(rows)} elements)")

        except Exception as e:
            print(f"❌ Failed {file}: {e}")

    print("\nAll done! CSVs in:", OUT_DIR)

if __name__ == "__main__":
    main()
