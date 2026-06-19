# Dependability 75% by Month — User Guide

## Overview

`dependability_75_by_month.py` performs **75% dependability analysis** on monthly junction data. Each calendar month is a separate input sheet; the script creates per-junction dependability tables and a summary sheet with hyperlinks.

This script is **independent** — use when data is organized by month (Jan, Feb, …).

---

## Prerequisites

```powershell
pip install pandas openpyxl
```

---

## Input Format

Edit `INPUT_PATH` and `MONTHS` at the bottom of the script.

```python
INPUT_PATH = r"C:\Data\Monthly_Junction_Volumes.xlsx"
MONTHS = ["Jun", "Jul", "Aug", "Sep", "Oct"]
```

**Each month sheet:**

| Year | Junction-A | Junction-B | Junction-C |
|------|------------|------------|------------|
| 2016 | 12.5 | 8.3 | 15.2 |
| 2017 | 10.1 | 9.0 | 14.8 |

Must have a **`Year`** column plus junction volume columns.

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Dependibility"
python dependability_75_by_month.py
```

---

## Expected Output

One Excel file per month:

- `Jun.xlsx`, `Jul.xlsx`, etc.

Each contains:
- One sheet per junction with ranked values and 75% row highlighted
- Summary sheet: `75_Percent_Dependibility_{Month}` with hyperlinks to junction sheets

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Missing month sheet | Sheet name not in workbook | Align `MONTHS` list with actual sheet names |
| Missing Year column | Header mismatch | Ensure first column is named `Year` |
| Empty junction sheets | All NaN values for a junction | Verify data exists for that junction |
