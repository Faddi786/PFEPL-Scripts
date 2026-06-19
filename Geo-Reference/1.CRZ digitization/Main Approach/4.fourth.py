import numpy as np
import rasterio
from rasterio.enums import ColorInterp

# ────────────────────────────────────────────────
#  CONFIGURATION
# ────────────────────────────────────────────────

# INPUT_FILE  = "digitized_boundary_78_color_selected.tif"
INPUT_FILE  =  "digitized_boundary_78.tif"
OUTPUT_FILE = "digitized_boundary_78_highlighted_uniform.tif"

# Choose ONE strong, visible blue shade (RGB 0–255)
# These are popular high-visibility choices:
HIGHLIGHT_RGB = [0, 180, 255]      # bright cyan-blue
# Alternatives you can try:
# [60, 180, 255]     # lighter sky blue
# [0, 120, 255]      # strong electric blue
# [30, 144, 255]     # dodger blue – very visible
# [0, 255, 255]      # pure cyan – extremely striking

# Optional: slight glow / outline effect (makes lines pop more)
ADD_GLOW = True                     # set False if you want perfectly sharp lines
GLOW_RADIUS = 1                     # 1–2 pixels

# ────────────────────────────────────────────────

with rasterio.open(INPUT_FILE) as src:
    profile = src.profile
    data = src.read()  # (bands, h, w)

    # Assume 3-band RGB
    if data.shape[0] != 3:
        raise ValueError("Input must be 3-band RGB")

    # Create mask of all non-black pixels (any blue line pixel)
    mask = np.any(data > 0, axis=0)

    # Create new output array (all black)
    out = np.zeros_like(data, dtype=np.uint8)  # shape (3, h, w)

    # Set all line pixels to the chosen uniform color
    for b, val in enumerate(HIGHLIGHT_RGB):
        out[b][mask] = val

    # Optional glow / outline (dilate slightly + blend)
    if ADD_GLOW and GLOW_RADIUS > 0:
        from scipy.ndimage import binary_dilation
        import cv2  # for gaussian blur glow (fallback if needed)

        # Dilate mask a bit
        dilated = binary_dilation(mask, iterations=GLOW_RADIUS)

        # Create glow layer (slightly dimmer version)
        glow = np.zeros_like(out)
        for b, val in enumerate(HIGHLIGHT_RGB):
            glow[b][dilated] = int(val * 0.6)  # 60% intensity for glow

        # Combine: glow underneath + sharp line on top
        out = np.maximum(out, glow)

# ─── Save result ─────────────────────────────────────────────
profile.update(
    dtype=rasterio.uint8,
    compress="lzw"
)

with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
    dst.write(out)
    dst.colorinterp = [
        ColorInterp.red,
        ColorInterp.green,
        ColorInterp.blue
    ]

print(f"Done. Highlighted version saved as: {OUTPUT_FILE}")
print(f"Used uniform color: RGB{HIGHLIGHT_RGB}")
print(f"Glow effect: {'enabled' if ADD_GLOW else 'disabled'}")