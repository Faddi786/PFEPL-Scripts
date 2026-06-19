# PDF to Georeferenced Map Image — User Guide

## Overview

Six-step pipeline to convert PDF map sheets into georeferenced GeoTIFF images through cropping, coordinate extraction, and polynomial georeferencing.

```
1.outside_cropping_skewed.py
    ↓
2.coordinates_user_inputs.py
    ↓
3.corner_values.py
    ↓
4.inside_cropping.py
    ↓
5.img_map_coordinates.py
    ↓
6.make_geotiff_polynomial.py
```

---

## Prerequisites

```powershell
pip install opencv-python pdf2image numpy pytesseract rasterio pyproj Pillow
```

Also required:
- **Poppler** (for pdf2image PDF conversion)
- **Tesseract OCR** (for coordinate extraction in Step 2)

---

## Step 1 — Outside Cropping (`1.outside_cropping_skewed.py`)

### Input

Edit at top of script:

```python
pdf_path = "MH_80.pdf"
output_path = "outside_cropped_MH80.png"
```

### Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Digitization\1.PDF to Georeferenced Map Image"
python 1.outside_cropping_skewed.py
```

### Output

PNG with map border cropped and deskewed (e.g. `outside_cropped_MH80.png`)

---

## Step 2 — Coordinate OCR (`2.coordinates_user_inputs.py`)

### Input

```python
image_path = "outside_cropped_MH80.png"   # from Step 1
output_txt = "boundary_coordinates_MH80.txt"
```

Reads coordinate labels from map boundary strips via OCR.

### Output

Text file with extracted boundary coordinates.

---

## Step 3 — Corner Values (`3.corner_values.py`)

Processes boundary coordinates into four corner map coordinates. Edit input/output paths to match your map ID.

---

## Step 4 — Inside Cropping (`4.inside_cropping.py`)

Crops the inner map area (inside the coordinate frame). Input: Step 1 PNG. Output: inner cropped image.

---

## Step 5 — Map Coordinates (`5.img_map_coordinates.py`)

Associates pixel positions with geographic coordinates from Step 3 output.

---

## Step 6 — GeoTIFF Creation (`6.make_geotiff_polynomial.py`)

### Input

Inner cropped image + corner/control points from previous steps.

### Output

Georeferenced GeoTIFF (note: script may write `rough.tif` — verify actual output filename in script).

---

## Full Workflow Example

For map sheet **MH_80**:

1. Place `MH_80.pdf` in script folder
2. Edit all scripts to use `MH80` / `MH_80` naming consistently
3. Run steps 1 → 6 in order
4. Verify output GeoTIFF in QGIS or `check_georef`-style tool

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Poppler not found | pdf2image dependency missing | Install Poppler; add to PATH |
| OCR garbage | Low quality scan | Increase DPI in Step 1; clean PDF source |
| Brown border not detected | Different map color scheme | Adjust HSV thresholds in Step 1 |
| Wrong georef | Corner coords misread | Manually verify boundary_coordinates txt |

---

## Tips

- Use consistent map ID suffix (e.g. `MH80`) across all six scripts for one map sheet.
- Run each step and visually inspect output before proceeding.
- Step 1 DPI default is 300 — increase for finer coordinate OCR.
