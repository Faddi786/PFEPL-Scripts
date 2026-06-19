# CRZ Digitization — Main Approach — User Guide

## Overview

Four-step pipeline to digitize **CRZ (Coastal Regulation Zone) boundaries** from georeferenced map rasters using hex color matching, color selection, water body removal, and uniform highlighting.

```
1.first.py  →  2.second.py  →  3.third.py  →  4.fourth.py
```

---

## Prerequisites

```powershell
pip install numpy rasterio scikit-image scipy
```

Input: Georeferenced GeoTIFF from `Geo-Reference\georeference.py` or Digitization pipeline.

---

## Step 1 — Color-Based Boundary Extraction (`1.first.py`)

### Input

```python
input_raster = "output_polynomial_MH_78.tif"
output_raster = "digitized_boundary_78.tif"

target_hexes = [
    "#99e5f2",
    "#b3e4f2",
    # ... CRZ zone colors for your map sheet
]
```

Edit `target_hexes` for your map edition (MH78, MH80, MH85 have different color codes — see commented blocks in script).

### Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Geo-Reference\1.CRZ digitization\Main Approach"
python 1.first.py
```

### Output

Binary/classified raster with CRZ boundary pixels extracted.

---

## Step 2 — Color Selection (`2.second.py`)

### Input

```python
INPUT_FILE  = "digitized_boundary_75.tif"
OUTPUT_FILE = "digitized_boundary_75_color_selected.tif"
```

Selects specific blue shade(s) from the extracted boundary.

**Known issue:** Script references undefined `base` variable in gradient function — if you get a NameError, define `base_rgb` or fix the gradient call before running.

### Output

Color-filtered boundary raster.

---

## Step 3 — Water Body Removal (`3.third.py`)

### Input

```python
INPUT_FILE  = "output_78.tif"
OUTPUT_FILE = "digitized_boundary_78_no_water_final.tif"

WATER_MIN_AREA = 2000
WATER_MIN_SOLIDITY = 0.68
```

Removes compact filled regions identified as water bodies.

### Output

Boundary raster with water polygons removed.

---

## Step 4 — Uniform Highlighting (`4.fourth.py`)

### Input

```python
INPUT_FILE  = "digitized_boundary_78.tif"
OUTPUT_FILE = "digitized_boundary_78_highlighted_uniform.tif"
HIGHLIGHT_RGB = [0, 180, 255]
```

Applies uniform blue highlight color for visualization/delivery.

### Output

Final highlighted boundary GeoTIFF.

---

## Full Example (MH78)

1. Edit all scripts to use consistent naming (`78` / `MH_78`)
2. Set correct `target_hexes` in Step 1 for MH78 CRZ colors
3. Run 1 → 2 → 3 → 4
4. Import final TIFF in QGIS for verification

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| No boundary pixels | Wrong hex colors | Sample colors from map; update target_hexes |
| `NameError: base` in Step 2 | Script bug | Define base_rgb before gradient call |
| Water not removed | Thresholds too strict | Lower WATER_MIN_AREA |
| Thin lines disappearing | WATER_MIN_AREA too low | Increase threshold carefully |

---

## Tips

- Uncomment the correct `target_hexes` block for your map sheet in Step 1.
- Tune water removal parameters in Step 3 using printed region stats in console.
