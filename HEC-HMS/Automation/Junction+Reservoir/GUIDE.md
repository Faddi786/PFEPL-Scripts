# HEC-HMS Automation — Junction + Reservoir Pipeline — User Guide

## Overview

Same automation pipeline as the **Reservoir** variant, but extracts volumes for both **Junction** and **Reservoir** element types.

**Entry point:** `main_run.bat` → `config.py`

---

## Difference from Reservoir Folder

| Aspect | Reservoir | Junction+Reservoir |
|--------|-----------|-------------------|
| Element filter | `Type == 'reservoir'` | `Type in ['junction', 'reservoir']` |
| Use when | Dam/reservoir outflows only | Both junction and reservoir elements needed |

All other steps, prerequisites, inputs, and outputs are identical.

---

## Prerequisites

Same as Reservoir guide:
- HEC-HMS 4.13, conda env `hmsenv`, valid `.hms` project
- Edit `main_run.bat` and `run_command.bat` paths before first run

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\HEC-HMS\Automation\Junction+Reservoir"
main_run.bat
```

See **Reservoir\GUIDE.md** for full interactive input examples, output structure, and troubleshooting.

---

## Important Notes

- Ensure `run_command.bat` in `config.py` prompt points to **this folder's** `run_command.bat`, not the Reservoir one.
- `from csv to transposed data.py` in this folder may still filter `reservoir` only — use the main pipeline's `excel.py` for consistent junction+reservoir filtering.

---

## Utility Scripts

Same independent utilities as Reservoir folder (no `excel_summary.py` in this variant):
- `extract_results_to_csv.py`
- `from csv to transposed data.py`
- `combining_all_batches.py`
