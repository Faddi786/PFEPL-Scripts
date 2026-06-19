# CRZ Digitization — Alternate Approach — User Guide

## Overview

Alternative CRZ boundary digitization workflow with separate scripts for extraction, cleanup, and post-processing. More modular than the Main Approach — run only the scripts you need.

**Scripts (typical order):**

```
first.py  →  second.py  →  third.py  →  fourth.py
```

**Optional cleanup scripts (run as needed):**
- `remove_text.py` — remove text artifacts
- `remove_dots.py` — remove speckle/dots
- `aggressive_cleanup.py` — aggressive noise removal

---

## Prerequisites

```powershell
pip install numpy rasterio scikit-image scipy
```

---

## Script: `first.py` — Initial Color Extraction

### Input

```python
input_raster = "output_polynomial_MH_78.tif"
output_raster = "digitized_boundary.tif"

target_hexes = [
    "#78C3DD",  # CRZ-IVA
    "#AFC8F5",  # CRZ-IVB
]
H_TOL = 0.035
S_TOL = 0.20
V_TOL = 0.30
```

### Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Geo-Reference\1.CRZ digitization\Alternate Approach"
python first.py
```

---

## Script: `second.py` — Refinement

Further processes the boundary raster from `first.py`. Edit INPUT/OUTPUT paths to chain from previous step.

---

## Script: `third.py` — Additional Processing

Continues refinement (region filtering, morphology). Chain paths from `second.py` output.

---

## Script: `fourth.py` — Final Output

Produces final delivery raster. Edit paths to accept `third.py` output.

---

## Optional Cleanup Scripts

| Script | Purpose | When to use |
|--------|---------|-------------|
| `remove_text.py` | Removes text label artifacts | Map has visible station/label text in extraction |
| `remove_dots.py` | Removes small dot noise | Speckle after color extraction |
| `aggressive_cleanup.py` | Heavy denoising | Noisy scans with many artifacts |

Run cleanup scripts between main steps as needed — not all are required for every map.

---

## How to Run Full Alternate Workflow

```powershell
python first.py
python second.py
python third.py
python fourth.py
# Optional:
python remove_dots.py
python aggressive_cleanup.py
```

Edit input/output paths in each script between runs to chain outputs.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Wrong colors extracted | Hex tolerance too wide/narrow | Adjust H_TOL, S_TOL, V_TOL |
| Output path mismatch, for next step | Paths not updated between scripts | Match OUTPUT of step N to INPUT of step N+1 |
| Over-cleaned boundaries | aggressive_cleanup too strong | Use remove_dots.py instead |

---

## Main vs Alternate Approach

| | Main Approach | Alternate Approach |
|---|---------------|-------------------|
| Structure | Fixed 4-step numbered pipeline | Modular with optional cleanup |
| Best for | Standard MH map sheets | Maps needing extra cleanup passes |
