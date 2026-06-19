# SPS/PMP PCHIP Interpolation — User Guide

## Overview

`PCHIP.py` performs **PCHIP (monotonic cubic) interpolation** of SPS/PMP grid values for Vaitarna and Ulhas query points. PCHIP preserves monotonicity better than linear interpolation — useful when grid values must not oscillate between points.

This script is **independent** — use instead of `Linear.py` when PCHIP interpolation is preferred.

---

## Prerequisites

```powershell
pip install pandas numpy scipy openpyxl
```

---

## Input Format

Same `input.xlsx` structure as `Linear.py`, except **`Query_Points`** uses the **first two columns** only (no named query columns):

**`Query_Points` (columns A & B):**

| Col A (query x) | Col B (optional) |
|-----------------|------------------|
| 45.2 | |
| 78.5 | |

Grid sheets: `Vaitarna_Grid`, `Ulhas_Grid` (same as Linear.py).

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Data Interpolation"
python PCHIP.py
```

---

## Expected Output

- `output_PCHIP.xlsx` with **`Vaitarna`** and **`Ulhas`** sheets

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Scipy interpolation error | Duplicate or unsorted grid x values | Ensure unique, sorted grid distances |
| Insufficient grid points | Fewer than 2 points for PCHIP | Add more grid rows |
| Different output vs Linear | Expected — PCHIP uses cubic splines | Compare both outputs for your use case |

---

## Linear vs PCHIP

| Script | Method | Query sheet format |
|--------|--------|-------------------|
| `Linear.py` | Linear | Named columns in Query_Points |
| `PCHIP.py` | Monotonic cubic | First two columns of Query_Points |
