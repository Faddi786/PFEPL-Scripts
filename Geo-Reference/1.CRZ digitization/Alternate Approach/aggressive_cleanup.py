import numpy as np
import rasterio
from skimage.measure import label, regionprops
from rasterio.enums import ColorInterp

# -------------------------
# Input / Output
# -------------------------
input_raster = "digitized_boundary.tif"
output_raster = "digitized_boundary.tif"

def aggressive_cleanup(input_path, output_path):
    print(f"Reading {input_path}...")
    with rasterio.open(input_path) as src:
        profile = src.profile
        img = src.read()
    
    # Get binary mask of where any color exists
    # Use a small threshold in case there's very dark noise
    mask = np.any(img > 10, axis=0)
    
    pixel_count = np.sum(mask)
    print(f"Total foreground pixels: {pixel_count}")
    
    if pixel_count == 0:
        print("No foreground found. Skipping cleanup.")
        return

    print("Labeling components...")
    labels = label(mask)
    props = regionprops(labels)
    count = len(props)
    
    print(f"Found {count} components. Filtering for boundary lines...")
    
    mask_to_keep = np.zeros_like(mask, dtype=bool)
    kept_count = 0
    removed_count = 0
    
    for p in props:
        # HEURISTIC TO KEEP BOUNDARY LINES:
        # 1. Large area (likely a main boundary)
        # 2. Long major axis (likely a line segment even if area is small)
        if p.area > 1500 or p.major_axis_length > 150:
            coords = p.coords
            mask_to_keep[coords[:, 0], coords[:, 1]] = True
            kept_count += 1
        else:
            removed_count += 1
            
    print(f"Keeping {kept_count} components (lines).")
    print(f"Removing {removed_count} components (dots and text).")

    # The mask to remove is (original mask) AND NOT (mask to keep)
    mask_to_remove = mask & (~mask_to_keep)
    
    # Apply removal to all bands
    for i in range(img.shape[0]):
        img[i][mask_to_remove] = 0
    
    # Save result
    profile.update(compress='lzw')
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(img)
    
    print(f"Successfully saved cleaned image to {output_path}")

if __name__ == "__main__":
    aggressive_cleanup(input_raster, output_raster)
