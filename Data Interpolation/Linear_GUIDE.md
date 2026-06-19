# SPS/PMP Linear Interpolation — User Guide

## Overview

`Linear.py` performs **linear interpolation** of SPS/PMP grid values for Vaitarna and Ulhas query points. It reads grid sheets and a query points sheet, interpolates values at each query location, and writes separate output sheets per basin.

This script is **independent** — use when you need linear (not PCHIP) interpolation.

---

## Prerequisites

```powershell
pip install pandas numpy scipy openpyxl
```

---

## Input Format

Place `input.xlsx` in the script folder with these sheets:

**`Vaitarna_Grid` / `Ulhas_Grid`:**

Grid with distance/area columns and SPS/PMP value columns (headers like `SPS_1`, `SPS_2`, etc. — renamed automatically to station-specific names).

**`Query_Points`:**

| Query Name | Query Value | ... |
|------------|-------------|-----|
| Station-A | 45.2 | |
| Station-B | 78.5 | |

Named columns required for query identification.

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Data Interpolation"
python Linear.py
```

---

## Expected Output

- `output_Linear_3.xlsx` with sheets **`Vaitarna`** and **`Ulhas`**

Each output sheet contains interpolated SPS/PMP values for every query point at every grid duration/return period.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Column rename mismatch | Grid headers differ from expected `SPS_1` pattern | Align grid column names or edit rename map in script |
| Empty output rows | Query points with NaN values | Fill query values; script drops NaN rows |
| Sheet not found | Missing grid or query sheet | Verify sheet names in input.xlsx |
