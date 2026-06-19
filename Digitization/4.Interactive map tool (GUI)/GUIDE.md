# Interactive Map Tool (GUI) — User Guide

## Overview

PyQt6-based GUI for interactively viewing georeferenced TIFF maps, selecting colors, detecting boundaries/shades, and generating cleaned output rasters. Useful for tuning color detection parameters before batch processing.

**Entry point:** `main.py`

---

## Prerequisites

```powershell
pip install PyQt6 numpy rasterio opencv-python scikit-image
```

---

## Input Format

On launch, a file dialog opens. Select a georeferenced TIFF:

- Supported: `*.tif`, `*.tiff`
- Must be readable by rasterio (with or without CRS)

**Example input:**

```
C:\Maps\output_polynomial_MH_78.tif
```

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Digitization\4.Interactive map tool (GUI)"
python main.py
```

---

## GUI Workflow

1. **Open map** — file dialog selects input TIFF
2. **View** — pan/zoom the map in the viewer
3. **Color selection** — pick target colors for boundary detection
4. **Processing** — run shade detection, mask generation
5. **Export** — save processed TIFF via tif_writer

---

## Expected Output

Processed GeoTIFF saved to user-chosen path via the GUI export function.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: PyQt6` | Missing GUI library | `pip install PyQt6` |
| Blank viewer | Unsupported TIFF format | Verify file opens in QGIS first |
| No file selected | Cancelled dialog | Re-run and select a file |

---

## Module Structure

| Module | Role |
|--------|------|
| `main.py` | Entry point, file dialog |
| `ui/viewer.py` | Map display |
| `ui/color_selector.py` | Color picking |
| `processing/color_detection.py` | HSV/color masks |
| `processing/shade_detection.py` | Shade analysis |
| `processing/mask_generator.py` | Combined masks |
| `file_io/tif_loader.py`, `tif_writer.py` | I/O |

---

## Tips

- Use this tool to visually calibrate HSV ranges before running batch scripts in folders 2, 5, 6, or 7.
- Large TIFFs may load slowly — consider using a cropped subset for testing.
