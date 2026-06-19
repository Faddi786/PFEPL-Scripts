# Dependability 75/95/98 by Location — User Guide

## Overview

`dependability_75_95_98_by_location.py` computes **dependability analysis** per location sheet in an Excel workbook. For each location, it ranks yearly MCM values, calculates dependability percentages, and writes Excel formulas for **75%, 95% (interpolated), and 98% dependable** values.

This script is **independent** — use when your data is organized as one sheet per location.

---

## Prerequisites

```powershell
pip install pandas openpyxl
```

---

## Input Format

Edit `INPUT_EXCEL` and `LOCATIONS` list at the bottom of the script.

**Example configuration:**

```python
INPUT_EXCEL = r"C:\Data\Reservoir_Volumes.xlsx"
LOCATIONS = ["Vaitarna", "Ulhas", "Tansa"]
```

**Each location sheet must have:**

| Year | ... (MCM) column ... |
|------|----------------------|
| 2016 | 125.4 |
| 2017 | 98.2 |
| 2018 | 142.7 |

Column headers must contain **`(MCM)`** for volume columns to be detected.

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Dependibility"
python dependability_75_95_98_by_location.py
```

---

## Expected Output

One Excel file per location in the working directory:

- `Vaitarna.xlsx`
- `Ulhas.xlsx`
- `Tansa.xlsx`

Each file contains one sheet per MCM column with ranked values, dependability %, and formula rows for 75%/95%/98% thresholds.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Sheet not found | Location name doesn't match sheet | Verify `LOCATIONS` list matches sheet names exactly |
| No `(MCM)` columns | Column headers missing marker | Rename headers to include `(MCM)` |
| Interpolation row lookup fails | Too few data years ${(< 4 years)}$ | Add more years of data |
