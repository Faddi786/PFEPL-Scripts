# CRZ Blue Boundary Extraction — User Guide

## Overview

`app2.py` extracts **CRZ blue boundary lines** from RGB map images using HSV color detection, morphological cleanup, and skeletonization. Designed for PNG/JPG map exports.

**Single independent script.**

---

## Prerequisites

```powershell
pip install numpy scipy scikit-image Pillow matplotlib opencv-python
```

---

## Input Format

Edit the call at the bottom of the script or pass paths directly:

```python
extract_crz_boundary(
    image_path="MH_78_map.png",
    output_path="extracted_crz_line.png"
)
```

**Input:** RGB image (PNG/JPG) of a map sheet with blue CRZ boundary lines.

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Geo-Reference\3.CRZ blue boundary"
python app2.py
```

---

## Expected Output

**Sample console:**

```
Image loaded: 8500x8200 pixels
Blue pixels detected: 124567
After cleanup: 98234
Saved: extracted_crz_line.png
```

PNG with extracted CRZ boundary lines.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| No blue detected | HSV range too narrow | Broaden lower_blue/upper_blue in script |
| Too much noise | Range too wide | Tighten saturation/value thresholds |
| Broken lines | Over-aggressive morphology | Reduce morphological kernel sizes |

---

## HSV Defaults (in script)

- Primary blue: Hue 80–150, Sat/Val 30+
- Dark blue pass: Hue 100–160 for navy tones

Adjust these for your specific map color palette.

---

## Tips

- Works on non-georeferenced PNG exports — georeference separately afterward.
- Compare results with Main Approach CRZ digitization for georeferenced TIFF inputs.
