# Line Extraction (CLI) — User Guide

## Overview

`app1.py` is a command-line tool to extract lines from map images by **HSV color range** or **line width/thickness**. Outputs skeletonized line masks suitable for further vectorization.

**Single independent script.**

---

## Prerequisites

```powershell
pip install opencv-python numpy scikit-image
```

---

## Input Format

Run with command-line arguments:

```powershell
python app1.py --image "map.png" --mode color --lower 90,50,50 --upper 130,255,255 --output "lines.png"
```

Or for width-based extraction:

```powershell
python app1.py --image "map.png" --mode width --min-width 2 --max-width 8 --output "lines.png"
```

| Argument | Description | Example |
|----------|-------------|---------|
| `--image` | Input image path | `C:\Maps\MH80.png` |
| `--mode` | `color` or `width` | `color` |
| `--lower` | HSV lower bound (color mode) | `90,50,50` |
| `--upper` | HSV upper bound (color mode) | `130,255,255` |
| `--min-width` / `--max-width` | Pixel width range (width mode) | `2` / `8` |
| `--output` | Output image path | `extracted_lines.png` |

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Geo-Reference\2.Line extraction (CLI)"
python app1.py --image "input.png" --mode color --lower 90,50,50 --upper 130,255,255 --output "output_lines.png"
```

---

## Expected Output

PNG image with skeletonized extracted lines (white lines on black background).

**Sample console:**

```
Loading: input.png
Mode: color
HSV range: [90,50,50] - [130,255,255]
Extracted lines saved: output_lines.png
```

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Could not load image | Invalid path or format | Verify image exists and is readable |
| Empty output | HSV range doesn't match line color | Adjust --lower/--upper values |
| scikit-image missing | skeletonize import fails | `pip install scikit-image` |

---

## Tips

- Use the Interactive Map Tool (Digitization folder 4) to identify HSV values visually.
- Color mode works best for consistently colored boundary lines on maps.
