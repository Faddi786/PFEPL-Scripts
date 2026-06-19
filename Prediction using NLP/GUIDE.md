# Prediction using NLP — User Guide

## Overview

Seven-step pipeline for **rainfall station data preparation and gap-filling** using fuzzy station mapping, geographic neighbor detection, and MLP neural network interpolation with temporal and spatial fallbacks.

```
1 → 2 → [MANUAL: Final_Mapped.xlsx] → 3 → 4 → 5 → 6 → 7
```

**Important:** Data folders live at the **`Only Scripts\`** level (parent of this folder), not inside `Prediction using NLP\`.

---

## Prerequisites

```powershell
pip install pandas openpyxl geopandas scikit-learn numpy
```

---

## Required Folder Structure

Create these sibling folders under `Only Scripts\`:

```
Only Scripts\
├── Shapefiles\                    # Step 1 input
│   └── {GroupName}\*.shp
├── Excel Files\
│   ├── stations_by_folder.xlsx    # Step 1 output
│   ├── Excels with required date range\
│   │   └── {GroupName}.xlsx       # Step 2–3 input
│   ├── station_mapping.xlsx       # Step 2 output (draft)
│   └── Final_Mapped.xlsx          # Step 3 input (user-curated)
├── Required Station Info\         # Step 3–5 output
├── Filled Values\                 # Step 6–7 output
└── Prediction using NLP\          # Scripts 1–7
```

---

## Step-by-Step Guide

### Step 1 — Extract Station Lists

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Prediction using NLP"
python "1.extract_station_lists.py"
```

**Input:** `Only Scripts\Shapefiles\{GroupName}\*.shp` with station name column (`name`, `station`, etc.)

**Output:** `Excel Files\stations_by_folder.xlsx`

---

### Step 2 — Build Station Mapping (Draft)

```powershell
python "2.build_station_mapping_workbook.py"
```

**Input:** `stations_by_folder.xlsx` + `Excel Files\Excels with required date range\{Group}.xlsx`

**Output:** `Excel Files\station_mapping.xlsx` with proposed fuzzy matches

**MANUAL STEP:** Review mappings, fill blanks, save as **`Final_Mapped.xlsx`**

---

### Step 3 — Extract Required Station Info

```powershell
python "3.extract_required_station_info.py"
```

Optional date filter:

```powershell
python "3.extract_required_station_info.py" --start-date 2010-01-01 --end-date 2020-12-31
```

**Input:** `Final_Mapped.xlsx` + source Excel workbooks

**Output:** `Required Station Info\{Group}.xlsx` (one sheet per station; header row 2 in source)

---

### Step 4 — Add Summary Sheets

```powershell
python "4.add_summary_to_required_station_excels.py"
```

Adds/replaces **`Summary`** sheet with row counts and rainfall fill statistics.

---

### Step 5 — Find Station Neighbors

```powershell
python "5.find_station_neighbors.py"
```

**Output:** `Excel Files\station_neighbors_report.xlsx` (4 nearest neighbors per station, ≤30 km preferred)

---

### Step 6 — Fill Missing Rainfall

```powershell
python "6.fill_missing_rainfall_values.py"
```

**Output:** `Filled Values\{Group}.xlsx` + `Filled Values\Error_Summary_All_Stations.xlsx`

**Fill method codes:** `O`=observed, `F`=MLP, `T`=temporal, `AA`=arithmetic avg, `IW`=inverse distance, `NR`=normalized ratio

---

### Step 7 — Merge All Filled Workbooks

```powershell
python "7.merge_required_station_excels.py"
```

**Output:** `Filled Values\Filled_Values_Merged.xlsx` with hyperlinked index

---

## Input Format Examples

**Source station sheet (in `Excels with required date range\{Group}.xlsx`):**

| Date | Rainfall Value |
|------|----------------|
| 2016-06-01 | 12.5 |
| 2016-06-02 | 0.0 |
| 2016-06-03 | |

Header is on **row 2** (not row 1).

**Final_Mapped.xlsx (per group sheet):**

| Shapefile Station Name | Excel Station Sheet Name |
|------------------------|--------------------------|
| STN_001 | Station Alpha |
| STN_002 | Station Beta |

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Shapefiles directory not found | Missing `Only Scripts\Shapefiles\` | Create folder structure |
| `Final_Mapped.xlsx` missing | Manual step skipped | Complete Step 2 review and save |
| MLP skipped | Fewer than 60 training rows | Expected for sparse stations |
| PermissionError on neighbor report | File open in Excel | Close Excel |
| Wrong rainfall column | Not named `Rainfall Value` | Rename column in source sheets |

---

## Sample Console (Step 6)

```
Starting fill pipeline (MLP + temporal + AA/IW/NR)...
Processing group: Vaitarna
  Station Alpha: 45 filled (F=30, T=10, AA=5)
  Station Beta: 12 filled (T=12)
Fill pipeline completed.
```
