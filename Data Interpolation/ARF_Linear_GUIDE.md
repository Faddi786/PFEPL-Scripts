# ARF Linear Interpolation — User Guide

## Overview

`ARF_Linear.py` performs **linear interpolation** of Area Reduction Factor (ARF) values. It reads an ARF lookup scale and applies it to area values in a data sheet, writing interpolated ARF values to a new column.

This script is **independent** — run only this file when you need ARF linear interpolation (not the SPS/PMP scripts).

---

## Prerequisites

```powershell
pip install pandas numpy scipy openpyxl
```

---

## Input Format

Place `input.xlsx` in the script folder with two sheets:

**Sheet `ARF_Scale`:**

| Column A (Area km²) | Column B (ARF) |
|---------------------|----------------|
| 10 | 0.85 |
| 50 | 0.72 |
| 100 | 0.65 |
| 500 | 0.55 |

**Sheet `Data`:**

| ... | Column C (Area km²) | ... |
|-----|---------------------|-----|
| Row data | 25 | |
| Row data | 150 | |
| Row data | 800 | |

Column 6 of `Data` will receive the interpolated ARF values.

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Data Interpolation"
python ARF_Linear.py
```

---

## Expected Output

- `output_ARF.xlsx` — both sheets preserved; `Data` sheet column 6 contains interpolated ARF

**Sample output (Data sheet, column 6):**

| Area km² | Interpolated ARF |
|----------|------------------|
| 25 | 0.79 |
| 150 | 0.63 |
| 800 | 0.55 (clamped to max scale) |

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `KeyError` for sheet name | Missing `ARF_Scale` or `Data` sheet | Rename sheets to match exactly |
| Edge values flattened | Query area outside scale range | Values clamped to min/max — extend scale if needed |
| Empty output column | No numeric area values in column 3 | Check Data sheet column C |
