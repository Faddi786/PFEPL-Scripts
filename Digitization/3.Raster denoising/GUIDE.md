# Raster Denoising — User Guide

## Overview

`Denoising.py` removes white dots, speckle, and small clusters from georeferenced GeoTIFF maps while preserving thin continuous lines (boundaries, contours). Uses multi-scale area opening and morphological processing.

**Single independent script.**

---

## Prerequisites

```powershell
pip install numpy rasterio scikit-image opencv-python
```

---

## Input Format

Edit the function call at the bottom of the script or the `input_path` / `output_path` variables:

```python
aggressive_remove_dots_clusters(
    input_path="digitized_boundary_78.tif",
    output_path="digitized_boundary_78_denoised.tif",
    area_threshold=80,        # Remove features smaller than this (pixels)
    base_threshold=140,
    max_kernel_diam=9,
    preserve_intensity=True
)
```

| Parameter | Typical range | Effect |
|-----------|---------------|--------|
| `area_threshold` | 50–300 | Higher = removes larger speckle |
| `base_threshold` | 100–180 | Lower = catches fainter dots |
| `max_kernel_diam` | 5, 7, 9, 11 | Larger = more aggressive opening |

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Digitization\3.Raster denoising"
python Denoising.py
```

---

## Expected Output

**Sample console:**

```
Opening: digitized_boundary_78.tif
  CRS       : EPSG:4326
  Shape     : 8500 × 8200 × 3 bands
  Data type : uint8
Processing band 1...
Saved: digitized_boundary_78_denoised.tif
```

Denoised GeoTIFF with same CRS and dimensions as input.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Lines broken/thinned | area_threshold too high | Reduce threshold |
| Dots remain | threshold too low | Increase area_threshold or lower base_threshold |
| Memory error | Very large raster | Process tiles or reduce resolution |

---

## Tips

- Start with `area_threshold=80` and adjust visually in QGIS.
- Run after color-based extraction but before vectorization steps.
