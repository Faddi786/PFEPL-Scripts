# KTB Estimates Template Filler — User Guide

## Overview

`KTB_fill_template.py` batch-fills **KTB estimate workbooks** from a data Excel file into a template using `{{placeholder}}` syntax. It embeds an emblem, forces Excel formula recalculation via COM, and extracts the final Amount from each generated workbook.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python env | Conda environment **`estimates`** |
| Packages | `pandas`, `openpyxl`, `pywin32` |
| Microsoft Excel | Must be installed (COM automation) |
| Required files in folder | `KTB_Data_Latest.xlsx`, `KTB_Template.xlsx`, `emblem.png` |

---

## Input Format

**`KTB_Data_Latest.xlsx`** — data rows starting at **header row 4**. Column names must match `{{placeholder}}` names in the template.

**Example data (row 4 = headers):**

| Project Name | Location | Estimated Cost | ... |
|--------------|----------|----------------|-----|
| Road Widening Phase 1 | Thane | 4500000 | |
| Bridge Repair | Palghar | 2300000 | |

**`KTB_Template.xlsx`** — must contain:
- Placeholders like `{{Project Name}}`, `{{Location}}`
- Cover sheet named **`cover`** (lowercase)
- **`Recapitulation Sheet`** with Amount in cell **C20**

---

## How to Run

**Option A — Batch file (recommended):**

Double-click `KTB_Run.bat`

**Option B — Manual:**

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Estimates\KTB"
conda activate estimates
python KTB_fill_template.py
```

---

## Expected Output

Folder: `output_KTB_data_1-25_{timestamp}\`

- One filled `.xlsx` per data row
- `0.data_copy.xlsx` with extracted Amount values

**Sample console:**

```
Processing row 1: Road Widening Phase 1
  Saved: output_KTB_data_1-25_20240615\Road_Widening_Phase_1.xlsx
  Amount extracted: 4523000
All 25 rows processed.
```

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Conda env `estimates` missing | Environment not created | Create conda env with required packages |
| Excel COM failure | Excel not installed or busy | Close Excel; ensure Office installed |
| `emblem.png` not found | Missing image file | Place emblem.png in KTB folder |
| Cover sheet error | Sheet named `Cover` not `cover` | Rename to lowercase `cover` |
| Amount = ERROR | Recapitulation Sheet missing/wrong cell | Verify template structure |
