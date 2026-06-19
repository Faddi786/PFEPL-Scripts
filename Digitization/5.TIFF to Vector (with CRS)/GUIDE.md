# TIFF to Vector (with CRS) — User Guide

## Overview

`polygons_with_CRS.py` converts classified/digitized raster TIFFs into polygon shapefiles while preserving the coordinate reference system from the source raster.

**Single independent script.**

---

## Prerequisites

```powershell
pip install rasterio geopandas shapely numpy scikit-image opencv-python
```

---

## Input Format

Edit paths at top of script:

```python
input_raster = "digitized_boundary_78.tif"
output_shapefile = "boundary_polygons_78.shp"
```

**Input requirements:**
- Georeferenced GeoTIFF with classified regions (non-zero pixels = features)
- Valid CRS embedded in raster

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Digitization\5.TIFF to Vector (with CRS)"
python polygons_with_CRS.py
```

---

## Expected Output

Shapefile (`.shp` + sidecar files) with polygon geometries in the same CRS as the input raster.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Empty shapefile | No non-zero pixels in raster | Verify input is classified/binary |
| CRS missing | Input not georeferenced | Re-run georeferencing pipeline |
| GDAL/Fiona error | Shapefile path invalid | Ensure output directory exists and is writable |

---

## Tips

- Run after denoising (Step 3) for cleaner polygons.
- Inspect output in QGIS before downstream analysis.
