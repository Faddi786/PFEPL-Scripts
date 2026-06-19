# PDF to Excel Coordinate Extraction — User Guide

## Overview

Despite the folder name, `app.py` extracts **survey coordinate tables** from PDF files (WGS84 latitude/longitude and projected Northing/Easting), merges them on Station ID, and writes a combined Excel workbook.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.8+ |
| Packages | `pdfplumber`, `pandas`, `openpyxl` |

```powershell
pip install pdfplumber pandas openpyxl
```

---

## Input Format

Place `Input.xlsx` in the script folder with PDF paths in **column A** (one path per row; blank rows are ignored).

**Example `Input.xlsx`:**

| A (PDF Path) |
|--------------|
| C:\Surveys\Station_Adjustment_Report_2024.pdf |
| C:\Surveys\Baseline_Survey_MH80.pdf |
| |

**PDF content requirements:**

Each PDF must contain tables with headers containing:

- **WGS84 table:** `WGS84 Latitude` (and typically Longitude)
- **Projected table:** `Northing` (and typically Easting)

Both table types should share a **Station** identifier column for merging.

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\PDF to Excel Date Extraction"
python app.py
```

Ensure `Input.xlsx` is in the same directory.

---

## Expected Output

- `Output_{timestamp}.xlsx` created in the script folder

**Workbook sheets:**

| Sheet | Content |
|-------|---------|
| `Adjusted Coordinates` | Merged WGS84 + projected coordinates per station |
| `PDF List Used` | List of PDFs that were processed |

**Sample extracted data:**

| Station | WGS84 Latitude | WGS84 Longitude | Northing | Easting |
|---------|----------------|-----------------|----------|---------|
| BM-01 | 19.123456 | 72.987654 | 2103456.78 | 345678.90 |
| BM-02 | 19.124567 | 72.988765 | 2103567.89 | 345789.01 |

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `PDF Not Found` | Invalid path in Input.xlsx | Verify full absolute paths |
| Empty output / missing rows | Tables not detected in PDF | Check PDF has extractable tables with expected headers |
| Partial extraction | Only WGS84 or only projected table found | Ensure both table types exist in PDF |
| `Input.xlsx` not found | File missing from script folder | Create Input.xlsx with column A paths |

---

## Tips

- Use full absolute paths in `Input.xlsx` to avoid path resolution issues.
- PDFs from scanned images without table structure may not extract correctly — text-based PDFs work best.
