# Color-Based Boundary Digitization — User Guide

## Overview

`1.first-extracts_blue_line.py` extracts blue boundary lines from a georeferenced map raster using HSV color range detection, producing a binary/semi-binary output raster of the detected lines.

**Single independent script** — not part of a multi-step numbered pipeline.

---

## Prerequisites

```powershell
pip install opencv-python numpy rasterio
```

---

## Input Format

Edit paths and HSV color range at top of script:

```python
input_tif = "output_polynomial_MH_78.tif"
output_tif = "blue_lines_MH78.tif"

# HSV range for blue lines
lower_blue = np.array([90, 50, 50])
upper_blue = np.array([130, 255, 255])
```

**Input:** Georeferenced GeoTIFF from the PDF-to-GeoTIFF pipeline or Geo-Reference folder.

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Digitization\2.Color-based boundary digitization"
python 1.first-extracts_blue_line.py
```

---

## Expected Output

GeoTIFF with extracted blue line features preserved in geographic coordinates.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| No lines detected | HSV range wrong for your map colors | Sample blue color in image editor; adjust range |
| Too much noise | Range too wide | Narrow saturation/value thresholds |
| CRS lost | Input not georeferenced | Use georeferenced input TIFF |

---

## Tips

- Use QGIS or the Interactive Map Tool (GUI) to visually identify correct HSV values before running.
- Different map editions (MH78 vs MH80) may need different color ranges.
