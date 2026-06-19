# TIFF to Polygon + Boundary Lines — User Guide

## Overview

`polygon-and-line.py` extracts both **filled polygon regions** and **boundary line features** from a classified GeoTIFF, outputting separate vector layers.

**Single independent script.**

---

## Prerequisites

```powershell
pip install rasterio geopandas shapely numpy opencv-python scikit-image
```

---

## Input Format

Edit configuration at top of script:

```python
input_tif = "digitized_boundary_78.tif"
output_polygon_shp = "polygons_78.shp"
output_line_shp = "boundary_lines_78.shp"
```

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Digitization\6.TIFF to Polygon+Boundary lines"
python polygon-and-line.py
```

---

## Expected Output

| File | Content |
|------|---------|
| `polygons_78.shp` | Filled region polygons |
| `boundary_lines_78.shp` | Boundary/edge line features |

Both retain CRS from source raster.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| No line features | Raster lacks clear edges | Adjust extraction thresholds in script |
| Fragmented polygons | Noise in raster | Run denoising script first |
| Path not found | Input TIFF missing | Verify path from upstream digitization steps |

---

## Tips

- Useful when you need both area polygons and linear boundaries for CRZ mapping.
- Compare output with `5.TIFF to Vector` — use whichever fits your deliverable format.
