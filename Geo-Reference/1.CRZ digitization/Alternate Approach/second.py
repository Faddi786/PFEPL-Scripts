import cv2
import numpy as np
import rasterio
from rasterio.enums import ColorInterp
from skimage.morphology import skeletonize

# --------------------------------------
# Input / Output
# --------------------------------------
input_polygon_raster = "digitized_boundary.tif"
output_centerline_raster = "red_median_line.tif"

# --------------------------------------
# USER CONTROL: centerline width (pixels)
# --------------------------------------
LINE_WIDTH_PIXELS = 1   # <<< change this number as needed

# --------------------------------------
# Read polygon raster
# --------------------------------------
with rasterio.open(input_polygon_raster) as src:
    profile = src.profile
    img = src.read()

# --------------------------------------
# Convert to binary polygon mask
# --------------------------------------
polygon_rgb = np.transpose(img[:3], (1, 2, 0))
polygon_binary = polygon_rgb[:, :, 0] > 0  # red channel only

# --------------------------------------
# Skeletonize → median line (1 pixel)
# --------------------------------------
centerline = skeletonize(polygon_binary).astype(np.uint8)

# --------------------------------------
# Thicken centerline to desired width
# --------------------------------------
kernel = cv2.getStructuringElement(
    cv2.MORPH_ELLIPSE,
    (LINE_WIDTH_PIXELS, LINE_WIDTH_PIXELS)
)

centerline_thick = cv2.dilate(centerline, kernel, iterations=1)

# --------------------------------------
# Create output image (pure red)
# --------------------------------------
output = np.zeros(
    (centerline_thick.shape[0], centerline_thick.shape[1], 3),
    dtype=np.uint8
)

output[centerline_thick > 0] = (255, 0, 0)  # pure red

# --------------------------------------
# Convert back to raster format
# --------------------------------------
output = np.transpose(output, (2, 0, 1))

profile.update(
    dtype=rasterio.uint8,
    count=3,
    compress="lzw"
)

# --------------------------------------
# Write GeoTIFF
# --------------------------------------
with rasterio.open(output_centerline_raster, "w", **profile) as dst:
    dst.write(output)
    dst.colorinterp = (
        ColorInterp.red,
        ColorInterp.green,
        ColorInterp.blue
    )

print(f"Saved median line (width = {LINE_WIDTH_PIXELS}px): {output_centerline_raster}")
