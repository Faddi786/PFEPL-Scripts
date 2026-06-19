# HEC-HMS Automation — Reservoir Pipeline — User Guide

## Overview

Automates multi-year **HEC-HMS reservoir simulations**, extracts `.results` to CSV/Excel, computes **75% dependability**, and exports **DSS time series** to Excel workbooks with a navigation index.

**Entry point:** `main_run.bat` → `config.py`

This folder extracts **Reservoir** element types only. Use `Junction+Reservoir` or `Junction+Sink` folders for other element types.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| HEC-HMS | Version **4.13** |
| Conda env | **`hmsenv`** with `pandas`, `openpyxl`, `pydsstools` |
| Java | Bundled with HEC-HMS |
| HEC-HMS project | Valid `.hms` project with pre-configured run |

**Before first run — edit paths in:**

- `main_run.bat` line 9: `cd /d "..."` → your automation folder
- `run_command.bat`: `-script` path to `global_summary.py`, PROJ_LIB, Java classpath

---

## Input Format (Interactive Prompts)

When you run `main_run.bat` or `config.py`:

| Prompt | Example |
|--------|---------|
| `.hms` project path | `C:\Projects\Vaitarna\Vaitarna.hms` |
| Control file | `Vaitarna.control` |
| Run name | `Vaitarna Run (W-Dams)` |
| Start year | `2016` |
| End year | `2024` |
| Stop years (optional) | `2018,2020` |
| `run_command.bat` path | `C:\...\Reservoir\run_command.bat` |
| Output folder suffix | `Vaitarna_Run_2016_2024` |

**Simulation window (hardcoded):** June 1 – October 31 each year.

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\HEC-HMS\Automation\Reservoir"
main_run.bat
```

Or:

```powershell
conda activate hmsenv
python config.py
```

---

## Pipeline Flow

```
config.py
  ├─ Creates inputs_csv.csv + output directories
  ├─ run_command.bat → HEC-HMS runs global_summary.py (year-by-year)
  ├─ excel.result_to_csv() + csvs_transposed() → global_summary.xlsx
  ├─ seventy_five_dependiblity() → 75% sheets
  ├─ timeseries() ×2 (75% year + all years)
  └─ excel.build_navigation_index() → index.xlsx
```

---

## Expected Output

| Path | Content |
|------|---------|
| `output\{Project}_{timestamp}_{suffix}\index.xlsx` | Navigation hyperlinks |
| `output\...\global_summary.xlsx` | Pivoted volumes (MCM) + 75% sheets |
| `output\...\timeseries_excel.xlsx` | 75% dependability year time series |
| `output\...\all_years_timeseries\{Element}.xlsx` | Per-element multi-year series |
| `{ProjectDir}\{RunName}.dss` | DSS output from HMS |

**Sample console:**

```
Enter HMS project path: C:\Projects\Vaitarna\Vaitarna.hms
Running year 2016... OK
Running year 2017... OK
...
Building global summary...
75% dependability complete.
Time series extracted for 8 elements.
Done. Output: output\Vaitarna_20240615_Vaitarna_Run
```

---

## Independent Utility Scripts

| Script | When to use |
|--------|-------------|
| `extract_results_to_csv.py` | Re-parse existing `.results` without re-running HMS |
| `from csv to transposed data.py` | Build pivot Excel from CSV folder only |
| `combining_all_batches.py` | Merge multiple era `global_summary.xlsx` files |
| `excel_summary.py` | Summarize `all_years_timeseries/` into `Summary.xlsx` |

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ERROR: pydsstools missing!` | Conda env incomplete | `pip install pydsstools` in hmsenv |
| HMS fails silently | Wrong Java/PROJ paths in run_command.bat | Update paths for your machine |
| Run name mismatch | HMS run name differs | Match exact case/spacing |
| Excel file locked | Workbook open during autofit | Close Excel before running |
| End year missing | Known parsing bug (`range(start,end)`) | Verify last year ran; may need manual fix |

---

## Configuration Files

- `config.py` — orchestrator (edit simulation dates if needed)
- `run_command.bat` — HMS launcher
- `global_summary.py` — Jython script run inside HMS (not standalone Python)
