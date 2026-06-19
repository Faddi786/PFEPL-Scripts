# Geo-Reference — PDF to GeoTIFF — User Guide

## Overview

Main geo-referencing pipeline at the Geo-Reference root. Converts PDF map sheets to georeferenced GeoTIFFs by clicking four map corners and applying coordinates from a text file.

**Entry point:** `georeference.py`

Supporting modules: `corner_picker.py`, `image_enhance.py`, `check_georef.py`

---

## Prerequisites

Install from `requirements.txt`:

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Geo-Reference"
pip install -r requirements.txt
```

| Package | Purpose |
|---------|---------|
| rasterio, pyproj | GeoTIFF writing and CRS |
| pymupdf | PDF rendering |
| matplotlib, Pillow | Display and image handling |
| opencv-contrib-python | Optional AI upscale (`--upscale`) |

---

## Input Format

### Folder structure

```
Geo-Reference\
  Input\                          ← Place PDF files here
  Decimal Coordinates.txt         ← Four corner coords per map
  Output\                         ← GeoTIFFs written here
```

### `Decimal Coordinates.txt`

One block per PDF with four corner coordinates (decimal degrees, WGS84):

```
MH_78.pdf
NW: 19.523456, 72.812345
NE: 19.523456, 73.045678
SE: 19.312345, 73.045678
SW: 19.312345, 72.812345

MH_80.pdf
NW: 19.601234, 72.901234
...
```

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Geo-Reference"
python georeference.py
```

**Optional flags:**

```powershell
python georeference.py --quality high      # 900 DPI render
python georeference.py --quality max       # 1200 DPI
python georeference.py --upscale           # AI enhancement (requires opencv-contrib)
```

For each PDF:
1. Script opens the rendered map
2. You click the four corners (NW, NE, SE, SW order)
3. GeoTIFF is written to `Output/`

---

## Expected Output

```
Output\
  MH_78_georef.tif
  MH_80_georef.tif
```

**Sample console:**

```
Processing: MH_78.pdf
  Render DPI: 600
  Click NW corner...
  Click NE corner...
  Click SE corner...
  Click SW corner...
  Written: Output\MH_78_georef.tif
```

---

## Verification

Run `check_georef.py` to validate output GeoTIFF georeferencing:

```powershell
python check_georef.py
```

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| PROJ database error on Windows | PostGIS PROJ conflict | Script auto-configures pyproj; reinstall if persists |
| PDF not in Input/ | Wrong folder | Move PDFs to Input/ |
| Missing coordinates | PDF not in Decimal Coordinates.txt | Add coordinate block |
| Corner click window too small | High-res PDF | Use `--quality draft` for picking, then re-run high quality |
| opencv import error with --upscale | Missing contrib build | `pip install opencv-contrib-python` |

---

## Related Sub-Pipelines

See separate guides in subfolders:
- `1.CRZ digitization\` — CRZ boundary digitization from georeferenced rasters
- `2.Line extraction (CLI)\` — CLI line extraction
- `3.CRZ blue boundary\` — Blue boundary detection
- `4.Color cluster debug\` — Color debugging tool
