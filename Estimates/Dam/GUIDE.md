# Dam Estimates Template Filler — User Guide

## Overview

`Dam_fill_template.py` batch-fills **dam estimate workbooks** from `Dam_Data.xlsx` into `Dam_Template.xlsx`. Same workflow as KTB estimates but with dam-specific template structure and Amount extracted from cell **E14**.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python env | Conda environment **`estimates`** |
| Packages | `pandas`, `openpyxl`, `pywin32` |
| Microsoft Excel | Must be installed |
| Required files | `Dam_Data.xlsx`, `Dam_Template.xlsx`, `emblem.png` |

---

## Input Format

**`Dam_Data.xlsx`** — header at **row 4**. Columns 0 and 4 are used for output filename identification.

**Example:**

| ID | Project | ... | Code | Total Cost |
|----|---------|-----|------|------------|
| DAM-01 | Upper Vaitarna | ... | UV-2024 | 85000000 |

**`Dam_Template.xlsx`** — placeholders matching data columns, cover sheet named **`Cover`** (capital C), **`Recapitulation Sheet`** with Amount in **E14**.

---

## How to Run

**Option A:** Double-click `Dam_Run.bat`

**Option B:**

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Estimates\Dam"
conda activate estimates
python Dam_fill_template.py
```

---

## Expected Output

Folder: `output_Dam_{timestamp}\` with one filled workbook per data row.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Worksheet 'Recapitulation Sheet' not found` | Template missing sheet | Add Recapitulation Sheet to template |
| Amount reads as ERROR | Wrong cell reference | Verify Amount is in E14 |
| Same as KTB errors | Conda/Excel/emblem issues | See KTB guide troubleshooting |
