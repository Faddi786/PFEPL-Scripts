# HEC-HMS Automation — Junction + Sink Pipeline — User Guide

## Overview

Same automation pipeline as other HEC-HMS variants, but extracts volumes for **Junction** and **Sink** element types (outlet/sink elements, no reservoirs).

**Entry point:** `main_run.bat` → `config.py`

---

## Difference from Other Variants

| Aspect | Junction+Sink |
|--------|---------------|
| Element filter | `Type in ['Junction', 'Sink']` |
| Use when | Junction and sink (outlet) elements; no reservoir dams |

---

## Prerequisites & How to Run

Identical to Reservoir and Junction+Reservoir guides.

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\HEC-HMS\Automation\Junction+Sink"
main_run.bat
```

Edit `main_run.bat` (line 9) and `run_command.bat` paths for your machine before first run.

---

## Input Example

| Prompt | Example |
|--------|---------|
| `.hms` project | `C:\Projects\Ulhas\Ulhas.hms` |
| Run name | `Ulhas Run (Junctions)` |
| Years | `2010` to `2020` |

See **Reservoir\GUIDE.md** for complete input/output documentation and error troubleshooting.

---

## Utility Scripts

- `extract_results_to_csv.py` — re-parse `.results` files
- `from csv to transposed data.py` — uses all row types (no reservoir filter)
- `combining_all_batches.py` — merge multi-decade summaries
