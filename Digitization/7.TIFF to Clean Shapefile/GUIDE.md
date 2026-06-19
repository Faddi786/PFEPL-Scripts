# TIFF to Clean Shapefile — User Guide

## Overview

`Shapfile_Creation.py` converts raster digitization output into a **cleaned, topologically simplified** shapefile suitable for GIS delivery.

**Single independent script** — typically the final vectorization step.

---

## Prerequisites

```powershell
pip install rasterio geopandas shapely numpy scikit-image
```

---

## Input Format

Edit paths at top of script:

```python
input_raster = "digitized_boundary_78_denoised.tif"
output_shp = "CRZ_boundary_78_clean.shp"
```

**Input:** Denoised, georeferenced classified TIFF from upstream pipeline.

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Digitization\7.TIFF to Clean Shapefile"
python Shapfile_Creation.py
```

---

## Expected Output

Clean shapefile ready for QGIS/ArcGIS import with simplified geometries and valid topology.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Invalid geometries | Self-intersecting polygons | Adjust simplification tolerance in script |
| Empty output | No features in raster | Check upstream color extraction/denoising |
| Write permission denied | Output path locked | Close shapefile in GIS software |

---

## Recommended Pipeline Order

```
PDF → GeoTIFF (folder 1) → Blue line extract (folder 2) → Denoise (folder 3)
  → Vectorize (folder 5/6/7) → Clean shapefile (this script)
```

Use folder 4 (GUI) anytime to tune color parameters.
