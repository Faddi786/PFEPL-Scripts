import numpy as np
import rasterio
from rasterio.enums import ColorInterp
from skimage.measure import label, regionprops
from scipy import ndimage as ndi

# ────────────────────────────────────────────────
#  CONFIGURATION ─ tune these according to your map
# ────────────────────────────────────────────────

INPUT_FILE  = "output_78.tif"
OUTPUT_FILE = "digitized_boundary_78_no_water_final.tif"

# ─── Criteria to identify and REMOVE water bodies ────────────
# (filled/compact regions – adjust after seeing printed stats)

WATER_MIN_AREA          = 2000      # pixels – increase if small creeks remain
                                    # decrease (800–1500) if thin lines start disappearing

WATER_MIN_SOLIDITY      = 0.68      # filled ratio – 0.65–0.85 typical for water
                                    # lower → more tolerant to jagged water edges

WATER_MAX_ECCENTRICITY  = 0.93      # compact = low eccentricity
                                    # increase to 0.95–0.96 if elongated water survives

WATER_ABSOLUTE_MAX_AREA = 150000    # very large areas = almost always water/sea

# Safety net: remove extremely small fragments after processing
MIN_AREA_FINAL_CLEAN    = 15        # remove tiny leftover pieces

# ────────────────────────────────────────────────

with rasterio.open(INPUT_FILE) as src:
    profile = src.profile
    data = src.read()  # (bands, h, w)

    # Create binary mask (non-black pixels)
    if data.shape[0] == 1:
        binary = data[0] > 0
    else:
        binary = np.any(data > 0, axis=0)
    binary = binary.astype(bool)

# ─── Label connected components ──────────────────────────────
labels = label(binary, connectivity=2)

props = regionprops(labels)

print(f"Found {len(props)} connected components in color-selected input")
print("Largest 12 components (area, solidity, eccentricity, perimeter):")

for i, p in enumerate(sorted(props, key=lambda x: x.area, reverse=True)[:12]):
    print(f"  #{i+1:2f}  area={p.area:7,f}   solidity={p.solidity:.3f}   "
          f"ecc={p.eccentricity:.3f}   peri={p.perimeter:.1f}")

# ─── Build keep mask ─────────────────────────────────────────
keep_mask = np.zeros_like(binary, dtype=bool)
removed_water = 0
kept_count = 0

for p in props:
    area = p.area

    # Tiny fragments → remove
    if area < 10:
        continue

    # Check if looks like water body
    is_water = False
    if area >= WATER_MIN_AREA and p.solidity >= WATER_MIN_SOLIDITY:
        is_water = True
    elif area >= WATER_MIN_AREA and p.eccentricity <= WATER_MAX_ECCENTRICITY:
        is_water = True
    elif area >= WATER_ABSOLUTE_MAX_AREA:
        is_water = True

    if is_water:
        removed_water += 1
        continue

    # Keep this component
    coords = p.coords
    keep_mask[coords[:, 0], coords[:, 1]] = True
    kept_count += 1

# ─── Final small clean-up (optional but recommended) ─────────
if MIN_AREA_FINAL_CLEAN > 1:
    keep_labels = label(keep_mask)
    sizes = np.bincount(keep_labels.ravel())
    mask_small = sizes < MIN_AREA_FINAL_CLEAN
    mask_small[0] = False
    keep_mask[mask_small[keep_labels]] = False

# Optional: fill small holes inside remaining lines
keep_mask = ndi.binary_fill_holes(keep_mask)

# ─── Create output raster ────────────────────────────────────
output = np.zeros_like(data, dtype=np.uint8)
for b in range(data.shape[0]):
    output[b][keep_mask] = data[b][keep_mask]

profile.update(
    dtype=rasterio.uint8,
    compress="lzw"
)

with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:
    dst.write(output)
    if data.shape[0] == 3:
        dst.colorinterp = [
            ColorInterp.red,
            ColorInterp.green,
            ColorInterp.blue
        ]

print(f"\nSaved result to: {OUTPUT_FILE}")
print(f"Kept {kept_count} components")
print(f"Removed {removed_water} probable water body components")