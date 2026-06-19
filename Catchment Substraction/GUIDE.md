# Catchment Substraction — User Guide

## Overview

This two-step pipeline calculates **upstream utilization** for catchment lifting points. Step 1 merges rainfall/upstream values from Excel into a point shapefile. Step 2 spatially sums upstream values for points inside each catchment polygon and compares them against Gross Yield values from Excel.

```
1.Merge_Shapefiles.py  →  2.Upstream_Calculation.py
```

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.9+ recommended |
| Packages | `geopandas`, `pandas`, `openpyxl` |
| GDAL/Fiona | Required for shapefile read/write (installed with geopandas) |

Install dependencies:

```powershell
pip install geopandas pandas openpyxl
```

---

## Step 1 — Merge Shapefiles (`1.Merge_Shapefiles.py`)

### Input Format

Edit the three paths at the top of the script before running.

| Input | Format | Required columns/structure |
|-------|--------|---------------------------|
| Point shapefile | `.shp` | Column **`Name`** (junction/lifting point names) |
| Excel file | `.xlsx` | Column 0 = `NAME`, Column 1 = rainfall/upstream value |
| Output shapefile | `.shp` path | Will be created |

**Example Excel content:**

| NAME | rainfall |
|------|----------|
| Junction-1 | 12.5 |
| Junction-2 | 8.3 |
| Lifting Point 15 | 4.1 |

**Example shapefile attribute (`Name` column):**

| Name |
|------|
| Junction-1 |
| Junction-2 |
| Lifting Point 15 |

Matching uses normalized text (lowercase, no spaces/hyphens) with numeric ID fallback.

### How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Catchment Substraction"
python 1.Merge_Shapefiles.py
```

### Expected Output

- Shapefile at `output_path` with a new column **`upstream_u`**
- Console log showing sample matched rows

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `KeyError: 'Name'` | Shapefile uses `NAME` instead of `Name` | Rename column or edit script |
| File not found | Hardcoded paths invalid | Update paths at top of script |
| Duplicate Excel keys | Multiple rows share same normalized name | Inspect Excel; deduplicate before merge |

---

## Step 2 — Upstream Calculation (`2.Upstream_Calculation.py`)

### Input Format

Edit the `CONFIG` block at the top of the script.

| Input | Format | Details |
|-------|--------|---------|
| Excel file | `.xlsx` | Columns: `Sr. No.`, `Name of Lifting Points`, `Gross Yield (MCM)` |
| Catchment folder | Folder of `.shp` files | One shapefile per catchment; filename must match Excel catchment name (normalized) |
| Points folder | Single `.shp` | Must contain **`upstream_u`** column from Step 1 |

**Example Excel:**

| Sr. No. | Name of Lifting Points | Gross Yield (MCM) |
|---------|------------------------|-------------------|
| 1 | Ulhas Upper | 450.2 |
| 2 | Vaitarna Lower | 320.8 |

**Catchment folder example:**

```
Catchments\
  Ulhas_Upper.shp
  Vaitarna_Lower.shp
```

**Points folder example:**

```
Points\
  Vaitarna_With_Upstream.shp   ← output from Step 1
```

### How to Run

Run Step 1 first, then:

```powershell
python 2.Upstream_Calculation.py
```

### Expected Output

- Excel file (default: `Ulhas_Gross_Yield_of_Catchments_with_upstream.xlsx`) with a **Summary** sheet
- Each row shows catchment name, summed upstream utilization, and Gross Yield comparison

**Sample console output:**

```
Processing catchment: Ulhas Upper
  Points found: 12, Sum upstream_u: 85.4 MCM
Processing catchment: Vaitarna Lower
  Points found: 8, Sum upstream_u: 62.1 MCM
Summary written to Ulhas_Gross_Yield_of_Catchments_with_upstream.xlsx
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `KeyError: upstream_u` | Step 1 not run | Run `1.Merge_Shapefiles.py` first |
| `FileNotFoundError` | No `.shp` in points folder | Verify folder path and file exists |
| Rows marked `NA` | Catchment name mismatch | Align shapefile names with Excel names |
| CRS warnings | Mixed coordinate systems | Script attempts reprojection; verify both inputs use valid CRS |

---

## Full Workflow Checklist

1. Prepare point shapefile with `Name` column
2. Prepare Excel with junction names and upstream/rainfall values
3. Edit paths in `1.Merge_Shapefiles.py` → run Step 1
4. Prepare catchment polygon shapefiles (one per catchment)
5. Prepare Gross Yield Excel
6. Edit paths in `2.Upstream_Calculation.py` → run Step 2
7. Open output Excel and verify Summary sheet
