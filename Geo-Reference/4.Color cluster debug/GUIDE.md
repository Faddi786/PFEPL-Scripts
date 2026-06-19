# Color Cluster Debug — User Guide

## Overview

`app3.py` is a **debugging/visualization tool** for analyzing color clusters in map rasters. Helps identify the correct hex/HSV values to use in CRZ digitization scripts before running batch extraction.

**Single independent script.**

---

## Prerequisites

```powershell
pip install numpy matplotlib opencv-python Pillow scikit-learn
```

---

## Input Format

Edit image path at top of script:

```python
image_path = "output_polynomial_MH_78.tif"
# or PNG export:
image_path = "MH_78_map.png"
```

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Geo-Reference\4.Color cluster debug"
python app3.py
```

---

## Expected Output

- Console output listing dominant color clusters with hex/RGB values
- Visualization plots showing color distribution (matplotlib windows)

**Sample console:**

```
Analyzing: output_polynomial_MH_78.tif
Found 8 dominant color clusters:
  Cluster 1: #78C3DD (RGB 120, 195, 221) — 12.3% of boundary pixels
  Cluster 2: #AFC8F5 (RGB 175, 200, 245) — 8.7%
  ...
```

Use these hex values in `1.first.py` or Alternate Approach `first.py`.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Image not found | Wrong path | Update image_path |
| Memory error | Very large TIFF | Use cropped PNG subset |
| sklearn missing | Cluster analysis dependency | `pip install scikit-learn` |

---

## When to Use

Run this **before** CRZ digitization when:
- Working with a new map sheet edition
- Standard hex values don't extract boundaries correctly
- You need to sample actual colors from the rendered map

---

## Tips

- Copy identified hex values directly into `target_hexes` in CRZ digitization scripts.
- Run on the same resolution/DPI as your production pipeline for accurate color sampling.
