# PDF Date Change — User Guide

## Overview

Two-step pipeline to **extract dates from survey PDFs via OCR**, prepare an Excel mapping, then **redraw updated dates** on the PDF images.

```
Input_Excel_Generation.py (Step 1 — Extract)  →  PDF_Date_Changer.py (Step 2 — Apply)
```

Used for updating "Tracking Summary" and "Residuals" section dates in baseline PDF reports.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python packages | `pandas`, `pdfplumber`, `Pillow`, `pytesseract`, `PyMuPDF` |
| Tesseract OCR | Installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` |
| Font | Arial at `C:\Windows\Fonts\arial.ttf` |

```powershell
pip install pandas pdfplumber Pillow pytesseract pymupdf
```

Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki

---

## Step 1 — Extract Dates (`Input_Excel_Generation.py`)

### Input

Interactive prompts per PDF:

| Prompt | Format | Example |
|--------|--------|---------|
| PDF path | Full path to baseline PDF | `C:\Reports\Baseline_Survey.pdf` |
| New date | `DD-MM-YYYY` | `15-03-2024` |
| Extra Residuals pages | Optional page numbers | `12,13` |

PDF must contain **"Tracking Summary"** and **"Residuals"** sections detectable by text search.

### How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\PDF Date Change"
python Input_Excel_Generation.py
```

### Output

- `{pdf_basename}.xlsx` in the script folder
- Sheets: **`Tracking Summary`**, **`Residuals`** with page ranges, original dates, and modified dates

**Example Excel (Tracking Summary sheet):**

| Page | Original Date | Modified Date |
|------|---------------|---------------|
| 5 | 01-01-2023 | 15-03-2024 |
| 6 | 01-01-2023 | 15-03-2024 |

---

## Step 2 — Apply Dates (`PDF_Date_Changer.py`)

### Input

Interactive prompts:

| Prompt | Example |
|--------|---------|
| Excel path (from Step 1) | `C:\...\Baseline_Survey.xlsx` |
| Original PDF path | `C:\Reports\Baseline_Survey.pdf` |
| Output PDF path | `C:\Reports\Baseline_Survey_Date_Updated.pdf` |

### How to Run

```powershell
python PDF_Date_Changer.py
```

### Output

- Single updated PDF with dates redrawn on graph bottom-center and report header areas

**Sample console:**

```
Reading Excel: Baseline_Survey.xlsx
Processing page 5 — Tracking Summary date updated
Processing page 8 — Residuals date updated
Saved: Baseline_Survey_Date_Updated.pdf
```

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Tesseract not found | OCR path wrong | Install Tesseract; verify path in script |
| Section pages not detected | PDF layout differs | Manually specify Residuals page numbers in Step 1 |
| OCR garbage on scans | Low-quality scan | Use higher-resolution PDF |
| Date positioned incorrectly | Non-standard PDF layout | May need manual adjustment of positioning constants |
| Empty Excel / no data | Step 1 failed | Re-run extraction with correct PDF |

---

## Workflow Checklist

1. Install Tesseract OCR
2. Run Step 1 for each PDF → verify Excel dates
3. Run Step 2 with Excel + original PDF
4. Visually inspect output PDF before distribution
