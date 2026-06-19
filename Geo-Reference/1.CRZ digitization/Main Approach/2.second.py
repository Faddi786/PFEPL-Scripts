import numpy as np
import rasterio
from rasterio.enums import ColorInterp
from scipy.spatial.distance import cdist
import random

# ────────────────────────────────────────────────
#  CONFIGURATION ─ tune these based on YOUR image
# ────────────────────────────────────────────────

INPUT_FILE  = "digitized_boundary_75.tif"
OUTPUT_FILE = "digitized_boundary_75_color_selected.tif"

# === Define the wanted blue shade(s) here ===
# Format: list of [R, G, B] — values from 0 to 255
# Pick colors from your wanted line (use image editor / QGIS / paint to sample)

def generate_color_gradient(base_rgb, count=9, spread=18):
    """
    Creates a gradient centered around base_rgb by shifting each channel ±spread
    """
    r, g, b = base_rgb
    
    colors = []
    
    for i in range(count):
        # Center at i = count//2
        step = i - (count - 1) / 2
        factor = step / ((count - 1) / 2) if count > 1 else 0
        
        nr = int(r + factor * spread * random.uniform(0.7, 1.3))
        ng = int(g + factor * spread * random.uniform(0.7, 1.3))
        nb = int(b + factor * spread * random.uniform(0.7, 1.3))
        
        # Clamp to valid range
        nr = max(0, min(255, nr))
        ng = max(0, min(255, ng))
        nb = max(0, min(255, nb))
        
        colors.append([nr, ng, nb])
    
    random.shuffle(colors)  # so it doesn't look strictly ordered
    return colors


# Usage:
# base = [162, 216, 228]          # ≈ middle of your original list
# base = [179, 230, 251] # MH 75
# base = [187, 227, 243] # MH 78
# base = [112, 216, 248] # MH 80
#base = [113, 223, 250] # MH 84
#base = [111, 213, 242] # MH 85

TARGET_COLORS = generate_color_gradient(base, count=10, spread=16)

# Tolerance: how close a pixel must be to ANY target color (Euclidean RGB distance)
# Start with 20–35; increase if wanted line has variation / gets broken
RGB_DISTANCE_TOL = 28.0

# Optional: very small area filter after color selection (safety net)
# Set to 1–5 if you still have tiny leftover dots
MIN_AREA_AFTER_COLOR = 5

# ────────────────────────────────────────────────

with rasterio.open(INPUT_FILE) as src:
    profile = src.profile
    data = src.read()  # shape (bands, h, w)

    if data.shape[0] != 3:
        raise ValueError("Input must be 3-band RGB")

    # Reshape to (h*w, 3) for distance calculation
    h, w = data.shape[1], data.shape[2]
    pixels = data.transpose(1,2,0).reshape(-1, 3).astype(np.float32)

    # Mask: only consider non-black pixels
    is_foreground = np.any(pixels > 0, axis=1)

    if not np.any(is_foreground):
        raise ValueError("No non-black pixels found in input")

    fg_pixels = pixels[is_foreground]

    # Compute distance to nearest target color
    targets = np.array(TARGET_COLORS, dtype=np.float32)
    dists = cdist(fg_pixels, targets, metric='euclidean')
    min_dists = np.min(dists, axis=1)

    # Keep only pixels close enough to at least one target color
    keep_fg = min_dists <= RGB_DISTANCE_TOL

    # Build full image mask
    keep_mask = np.zeros(h * w, dtype=bool)
    keep_mask[is_foreground] = keep_fg

    keep_mask_2d = keep_mask.reshape(h, w)

    # Optional: remove tiny remaining components
    if MIN_AREA_AFTER_COLOR > 1:
        from skimage.measure import label
        labels = label(keep_mask_2d)
        sizes = np.bincount(labels.ravel())
        mask_small = sizes < MIN_AREA_AFTER_COLOR
        mask_small[0] = False
        remove = mask_small[labels]
        keep_mask_2d[remove] = False

# ─── Create output ───────────────────────────────────────────
output = np.zeros_like(data, dtype=np.uint8)
for b in range(3):
    output[b][keep_mask_2d] = data[b][keep_mask_2d]

profile.update(
    dtype=rasterio.uint8,
    compress="lzw"
)

with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
    dst.write(output)
    dst.colorinterp = [
        ColorInterp.red,
        ColorInterp.green,
        ColorInterp.blue
    ]

print(f"Saved color-filtered result to: {OUTPUT_FILE}")
print(f"Kept pixels within RGB distance {RGB_DISTANCE_TOL} of targets")
print(f"Target colors used: {TARGET_COLORS}")