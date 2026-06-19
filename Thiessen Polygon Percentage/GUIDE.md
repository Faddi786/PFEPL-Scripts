# Thiessen Polygon Percentage — User Guide

## Overview

Pipeline to generate a **subbasin-station area report** from Thiessen polygon data and optionally calculate **station percentage contributions** per subbasin via Excel VBA.

```
export_subbasin_report.py  →  run_all.py (optional VBA percentage step)
```

Entry point: **`run_report.bat`** or **`run_all.py`**

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.8+ with `pandas`, `openpyxl` |
| pywin32 | Required for VBA step (`pip install pywin32`) |
| Microsoft Excel | For percentage calculation macro |
| Input Excel | `Theissen Polygons_Calculate percent & total area.xlsx` |

---

## Input Format

**`Theissen Polygons_Calculate percent & total area.xlsx`**

Required columns (read from row 0, data from row 1):

| name_1 (Subbasin) | Name (Station) | Shape_Area |
|-------------------|----------------|------------|
| Subbasin-1 | Station-A | 45.23 |
| Subbasin-1 | Station-B | 32.10 |
| Subbasin-2 | Station-C | 78.55 |

Edit `input_file` in `export_subbasin_report.py` if your filename differs.

---

## How to Run

**Recommended:**

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Thiessen Polygon Percentage"
run_report.bat
```

**Or manually:**

```powershell
python run_all.py
```

When prompted **"Do you want to calculate percentage? (Y/N)"** — answer `Y` to run the VBA macro.

---

## Expected Output

| File | Content |
|------|---------|
| `Subbasin_Report_with_Percentage.xlsx` | Formatted report with subbasin sections, station areas, totals |
| After VBA | Percentage column filled per station within each subbasin |

**Sample console:**

```
▶ Running report generation script...
✔ Report generated successfully

Do you want to calculate percentage? (Y/N): Y
▶ Running VBA percentage calculation...
✔ Percentage calculated and Excel file saved

✅ Task completed successfully.
```

**Sample report structure:**

| Subbasin-1 | | |
| Station | Area (sq km) | Percentage |
| Station-A | 45.23 | 58.5% |
| Station-B | 32.10 | 41.5% |
| **Total** | **77.33** | **100%** |

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Input file not found | Missing Thiessen polygon Excel | Place input file in script folder |
| VBA macro fails | Excel trust settings / macro security | Enable macros; trust VBProject access |
| Sheet name mismatch | VBA targets wrong sheet | Verify Report sheet exists after Python step |
| pywin32 not installed | Missing package | `pip install pywin32` |

---

## Files in This Folder

| File | Role |
|------|------|
| `export_subbasin_report.py` | Python report generator |
| `run_all.py` | Orchestrates Python + optional VBA |
| `run_report.bat` | Windows launcher |
| `theisan plygon percentage nikalo.txt` | VBA macro source code |
