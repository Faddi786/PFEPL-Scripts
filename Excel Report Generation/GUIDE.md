# Excel Report Generation — User Guide

## Overview

Hybrid **Python + Excel VBA** pipeline that converts a marked-up input workbook into a professionally formatted A3 report with section dividers, optimized table widths, table of contents, and cover page with header/footer images.

```
Step1.py → Step2.py → Step3.py → VBA Step4_Part_1 → Step4Part2.py → VBA Step5 → VBA Step6
```

Orchestrated end-to-end via VBA macro **`Run_Full_Report`**.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python 3.11 | Path configured in VBA `Run_Full_Report` |
| Packages | `openpyxl` |
| Microsoft Excel | With VBA macros enabled |
| VBA modules | Import from `vba\` folder (`.txt` files) |

**Required files in project folder:**

| File | Purpose |
|------|---------|
| `input.xlsx` | Source data with START/END markers |
| `section_config.json` | Section divider configuration |
| `Image_1.png`, `Image_2.png`, `Image_3.png` | Cover/header/footer images |
| Controller workbook | Excel file with imported VBA modules |

---

## Input Format

### `input.xlsx`

Each worksheet uses column A markers:

| Marker | Meaning |
|--------|---------|
| `start` | Beginning of a table block |
| `end` | End of a table block |
| `repeat` | Optional repeat header row |

**Example column A:**

```
start
Header Row 1
Data row 1
Data row 2
end
start
Another table...
end
```

### `section_config.json`

```json
{
  "sections": [
    {
      "position": "before",
      "table": "Table_1",
      "text": "Section 1: Introduction"
    },
    {
      "position": "after",
      "table": "Table_3",
      "text": "Section 2: Results"
    }
  ]
}
```

---

## How to Run

### Manual step-by-step

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Excel Report Generation"
python Step1.py      # Validate markers
python Step2.py      # Extract tables → output.xlsx
python Step3.py      # Insert section dividers
```

Then in Excel (with `output.xlsx` open):
1. Run VBA macro **Step4_Part_1** (measures page widths → Optimization_Log)

```powershell
python Step4Part2.py  # Shrink wide tables → output_formatted.xlsx
```

Then in Excel:
2. Run VBA **Step5** (Table of Contents)
3. Run VBA **Step6** (Cover, headers/footers)

### Full automated run

Open the controller workbook → run VBA **`Run_Full_Report`** (runs all steps including Python calls).

---

## Expected Output

| Stage | Output file |
|-------|-------------|
| After Step 2 | `output.xlsx` (Table_N sheets) |
| After Step 4 | `output_formatted.xlsx` |
| After Step 6 | Final report saved to path in `Run_Full_Report` |

**Sample Step1 validation:**

```
Validating input.xlsx...
Sheet 'Data': 5 table blocks found — OK
All sheets validated successfully.
```

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ValueError` unmatched START/END | Missing `end` marker | Fix column A markers in input.xlsx |
| Log sheet missing (Step4Part2) | VBA Step4 skipped | Run VBA Step4_Part_1 first |
| Invalid section config | Table_N not found | Match table names in section_config.json |
| Image files not found | PNGs missing from folder | Add Image_1/2/3.png |
| Python path wrong in VBA | Different Python install | Edit path in Run_Full_Report |

---

## VBA Module Import

Import these files via Excel VBA editor (File → Import):
- `vba\Run_Full_Report.txt`
- `vba\Step4_Part_1.txt`
- `vba\Step5_TOC.txt`
- `vba\Step6_Cover_Header.txt`
