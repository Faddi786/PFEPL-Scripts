# Dependability 75% from Global Summary — User Guide

## Overview

`dependability_75_from_global_summary.py` reads a **`global_summary`** sheet from an existing workbook, adds per-junction dependability sheets and a **`75_Percent_Dependibility`** summary — **in-place** (updates the same file).

This script is **independent** — typically used after HEC-HMS automation output.

---

## Prerequisites

```powershell
pip install pandas openpyxl
```

**Note:** This script imports `autofit_columns` from a local `excel` module. If you get `ModuleNotFoundError: excel`, copy `excel.py` from `HEC-HMS\Automation\Reservoir\` into the Dependibility folder, or comment out the autofit call.

---

## Input Format

Edit `INPUT_PATH` at the bottom of the script:

```python
INPUT_PATH = r"C:\Output\Vaitarna_Run\global_summary.xlsx"
```

**Required sheet: `global_summary`**

| Year | Junction-A (MCM) | Junction-B (MCM) | ... |
|------|------------------|------------------|-----|
| 2016 | 125.4 | 98.2 | |
| 2017 | 110.3 | 105.6 | |

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Dependibility"
python dependability_75_from_global_summary.py
```

**Close the Excel file before running** — the script writes in-place.

---

## Expected Output

The input workbook is updated with:
- New sheets per junction (dependability tables)
- `75_Percent_Dependibility` summary sheet

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: excel` | Missing helper module | Copy `excel.py` from HEC-HMS folder |
| File locked | Workbook open in Excel | Close Excel before running |
| Missing `global_summary` sheet | Wrong workbook or sheet name | Verify HEC-HMS output structure |
