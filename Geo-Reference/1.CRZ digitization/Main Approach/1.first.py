import numpy as np
import rasterio
from rasterio.enums import ColorInterp
from skimage.color import rgb2hsv
from skimage.morphology import closing, disk
from skimage.measure import regionprops
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

# -------------------------
# Input / Output
# -------------------------
input_raster = "output_polynomial_MH_78.tif"
output_raster = "digitized_boundary_78.tif"

# -------------------------
# Target HEX colors (MH78: CRZ-IVA + CRZ-IVB)
# -------------------------
target_hexes = [
    "#99e5f2",
    "#b3e4f2",
    "#d0eee8",
    "#9cd7d2",
    "#9bd3cb"
    # "#78C3DD",  # CRZ-IVA
    # "#AFC8F5",  # CRZ-IVB (light blue/lavender)
]

# -------------------------
# Target HEX colors (MH80: CRZ-IVA + CRZ-IVB)
# -------------------------
# target_hexes = [
#     "#A9DBEE",  # CRZ-IVA
#     "#73d9f7",  # CRZ-IVB (light blue/lavender)
# ]

# target_hexes = [
#     "#5fdaf0",
#     "#77cbdd"  # MH 85 CRZ-IVA  # CRZ-IVB (light blue/lavender)
# ]

# -------------------------
# Target HEX colors (MH78: CRZ-IVA + CRZ-IVB) [179, 230, 251]
# -------------------------
# target_hexes = [
#     "#B3E6FB"
# ]

# -------------------------
# Tolerance values
# -------------------------
H_TOL = 0.035
S_TOL = 0.20
V_TOL = 0.30

# RGB fallback distance catches anti-aliased shades around the target color.
RGB_DIST_TOL = 20.0

# Soft reference mask for safe gap stitching.
SOFT_H_TOL = 0.060
SOFT_S_TOL = 0.32
SOFT_V_TOL = 0.45
SOFT_RGB_DIST_TOL = 55.0

# -------------------------
# Noise removal parameter (KEY)
# -------------------------
MIN_NOISE_AREA = 40   # remove dotted fragments while preserving boundary runs
# Remove large dense filled regions (water-like blobs).
BLOB_MIN_AREA = 250
BLOB_DENSITY_THRESHOLD = 0.35

# Bridge tiny pixel gaps in the extracted linework.
MASK_CLOSE_RADIUS = 1
MAX_GAP_CONNECT_PIXELS = 14
MIN_SUPPORT_RATIO = 0.55
SUPPORT_DILATION_PIXELS = 1

# -------------------------
# Convert HEX → RGB → HSV
# -------------------------
def remove_small_components(mask, min_pixels):
    """Remove connected components smaller than min_pixels."""
    if min_pixels <= 1:
        return mask
    labels, _ = ndi.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    counts = np.bincount(labels.ravel())
    keep = counts >= min_pixels
    keep[0] = False
    return keep[labels]


def remove_blob_components(mask, min_area, density_threshold):
    """
    Remove large dense components (filled patches) and keep thin line-like ones.
    This helps suppress water fills while retaining border lines.
    """
    labels, num = ndi.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    if num == 0:
        return mask

    props = regionprops(labels)
    out = np.zeros_like(mask, dtype=bool)
    for p in props:
        area = p.area
        if area == 0:
            continue

        min_r, min_c, max_r, max_c = p.bbox
        r_span = max_r - min_r
        c_span = max_c - min_c
        bbox_area = r_span * c_span
        density = area / max(1, bbox_area)

        is_blob = (area >= min_area) and (density >= density_threshold)
        if not is_blob:
            coords = p.coords
            out[coords[:, 0], coords[:, 1]] = True

    return out


def bresenham_line(r0, c0, r1, c1):
    points = []
    dr = abs(r1 - r0)
    dc = abs(c1 - c0)
    sr = 1 if r0 < r1 else -1
    sc = 1 if c0 < c1 else -1
    err = dr - dc
    r, c = r0, c0

    while True:
        points.append((r, c))
        if r == r1 and c == c1:
            break
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            r += sr
        if e2 < dr:
            err += dr
            c += sc
    return points


def bridge_gaps_with_reference(mask, support_mask, max_gap, min_support_ratio):
    """Connect endpoint pairs only if reference colors support the bridge."""
    labels, _ = ndi.label(mask, structure=np.ones((3, 3), dtype=np.uint8))

    neighbor_count = ndi.convolve(mask.astype(np.uint8), np.ones((3, 3), dtype=np.uint8), mode="constant") - mask.astype(np.uint8)
    endpoint_rows, endpoint_cols = np.where(mask & (neighbor_count == 1))
    endpoints = list(zip(endpoint_rows, endpoint_cols))
    if len(endpoints) < 2:
        return mask, 0

    tree = cKDTree(endpoints)
    used = set()
    bridges = 0
    max_gap2 = max_gap * max_gap

    for i, (r1, c1) in enumerate(endpoints):
        if i in used:
            continue

        candidates = tree.query_ball_point((r1, c1), r=max_gap)
        best_idx = None
        best_d2 = None
        for j in candidates:
            if j == i or j in used:
                continue
            r2, c2 = endpoints[j]
            if labels[r1, c1] == labels[r2, c2]:
                continue
            d2 = (r2 - r1) * (r2 - r1) + (c2 - c1) * (c2 - c1)
            if d2 == 0 or d2 > max_gap2:
                continue
            if best_d2 is None or d2 < best_d2:
                best_idx = j
                best_d2 = d2

        if best_idx is None:
            continue

        r2, c2 = endpoints[best_idx]
        line_pts = bresenham_line(r1, c1, r2, c2)
        support_hits = sum(1 for rr, cc in line_pts if support_mask[rr, cc])
        support_ratio = support_hits / max(1, len(line_pts))
        if support_ratio < min_support_ratio:
            continue

        for rr, cc in line_pts:
            mask[rr, cc] = True
        used.add(i)
        used.add(best_idx)
        bridges += 1

    return mask, bridges


target_rgbs = []
target_hsvs = []
for hx in target_hexes:
    hx = hx.lstrip("#")
    rgb_val = np.array([
        int(hx[0:2], 16),
        int(hx[2:4], 16),
        int(hx[4:6], 16)
    ], dtype=np.float32)
    target_rgbs.append(rgb_val)
    target_hsvs.append(rgb2hsv((rgb_val / 255.0).reshape(1, 1, 3))[0, 0])

# -------------------------
# Read image
# -------------------------
with rasterio.open(input_raster) as src:
    profile = src.profile
    img = src.read()

# Ensure we always have 3 channels for rgb2hsv.
# Some TIFFs are single-band (grayscale), while others have 3+ bands.
if img.shape[0] == 1:
    rgb = np.repeat(img, 3, axis=0)
elif img.shape[0] >= 3:
    rgb = img[:3]
else:
    raise ValueError(f"Unsupported band count in input raster: {img.shape[0]}")

rgb = np.transpose(rgb, (1, 2, 0)).astype(np.uint8)

# -------------------------
# Convert RGB → HSV
# -------------------------
rgb_float = rgb.astype(np.float32) / 255.0
hsv = rgb2hsv(rgb_float)

H = hsv[:, :, 0]
S = hsv[:, :, 1]
V = hsv[:, :, 2]

# -------------------------
# Color matching mask
# -------------------------
color_mask = np.zeros(H.shape, dtype=bool)
support_mask = np.zeros(H.shape, dtype=bool)

for target_rgb, target_hsv in zip(target_rgbs, target_hsvs):
    target_H, target_S, target_V = target_hsv
    hue_diff = np.abs(H - target_H)
    hue_diff = np.minimum(hue_diff, 1.0 - hue_diff)  # circular hue distance

    hsv_match = (
        (hue_diff <= H_TOL) &
        (np.abs(S - target_S) <= S_TOL) &
        (np.abs(V - target_V) <= V_TOL)
    )

    rgb_diff = rgb.astype(np.float32) - target_rgb.reshape(1, 1, 3)
    rgb_dist = np.sqrt(np.sum(rgb_diff * rgb_diff, axis=2))
    rgb_match = rgb_dist <= RGB_DIST_TOL
    color_mask |= (hsv_match | rgb_match)

    soft_hsv_match = (
        (hue_diff <= SOFT_H_TOL) &
        (np.abs(S - target_S) <= SOFT_S_TOL) &
        (np.abs(V - target_V) <= SOFT_V_TOL)
    )
    soft_rgb_match = rgb_dist <= SOFT_RGB_DIST_TOL
    support_mask |= (soft_hsv_match | soft_rgb_match)

# -------------------------
# NOISE REMOVAL (IMPORTANT)
# -------------------------
# Convert to boolean mask
binary_mask = color_mask.astype(bool)

# Remove small connected components (noise dots / tiny dashes)
clean_mask = remove_small_components(binary_mask, MIN_NOISE_AREA)
clean_mask = remove_blob_components(clean_mask, BLOB_MIN_AREA, BLOB_DENSITY_THRESHOLD)

if MASK_CLOSE_RADIUS > 0:
    clean_mask = closing(clean_mask, footprint=disk(MASK_CLOSE_RADIUS))
    # Re-apply after closing so tiny artifacts do not survive.
    clean_mask = remove_small_components(clean_mask, MIN_NOISE_AREA)
    clean_mask = remove_blob_components(clean_mask, BLOB_MIN_AREA, BLOB_DENSITY_THRESHOLD)

if SUPPORT_DILATION_PIXELS > 0:
    support_mask = ndi.binary_dilation(
        support_mask,
        structure=np.ones((3, 3), dtype=np.uint8),
        iterations=SUPPORT_DILATION_PIXELS
    )

clean_mask, bridges_added = bridge_gaps_with_reference(
    clean_mask.astype(bool),
    support_mask.astype(bool),
    max_gap=MAX_GAP_CONNECT_PIXELS,
    min_support_ratio=MIN_SUPPORT_RATIO
)
clean_mask = remove_small_components(clean_mask, MIN_NOISE_AREA)
clean_mask = remove_blob_components(clean_mask, BLOB_MIN_AREA, BLOB_DENSITY_THRESHOLD)

# -------------------------
# Create output image
# -------------------------
output = np.zeros_like(rgb, dtype=np.uint8)
output[clean_mask] = rgb[clean_mask]

# -------------------------
# Save GeoTIFF
# -------------------------
output = np.transpose(output, (2, 0, 1))

profile.update(
    dtype=rasterio.uint8,
    count=3,
    compress="lzw"
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(output)
    dst.colorinterp = (
        ColorInterp.red,
        ColorInterp.green,
        ColorInterp.blue
    )

print("Color extracted")
print("Noise removed")
print(f"Gaps stitched from reference: {bridges_added}")
print(f"Output saved as: {output_raster}")
