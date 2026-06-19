import numpy as np
import rasterio
from scipy import ndimage as ndi
from skimage.measure import label, regionprops
from rasterio.enums import ColorInterp

# -------------------------
# Input / Output
# -------------------------
input_raster = "digitized_boundary.tif"
output_raster = "digitized_boundary.tif"

# -------------------------
# Parameters
# -------------------------
# Components smaller than this area (in pixels) will be removed.
# This should catch all isolated dots/noise.
DOT_SIZE_THRESHOLD = 80 

def remove_dots(input_path, output_path):
    print(f"Reading {input_path}...")
    with rasterio.open(input_path) as src:
        profile = src.profile
        img = src.read()
    
    # Get binary mask of where any color exists
    mask = np.any(img > 0, axis=0)
    
    print("Labeling components and identifying dots...")
    labels, count = ndi.label(mask)
    if count == 0:
        print("No foreground found.")
        return

    # Using regionprops to quickly get areas
    props = regionprops(labels)
    
    mask_to_remove = np.zeros_like(mask, dtype=bool)
    dots_removed = 0
    total_area_removed = 0
    
    for p in props:
        if p.area < DOT_SIZE_THRESHOLD:
            mask_to_remove[labels == p.label] = True
            dots_removed += 1
            total_area_removed += p.area
            
    if dots_removed == 0:
        print("No dots found with current threshold.")
        return

    print(f"Removing {dots_removed} dots (Total pixels cleared: {total_area_removed})...")
    
    # Apply removal to all bands
    for i in range(img.shape[0]):
        img[i][mask_to_remove] = 0
    
    # Save result
    profile.update(compress='lzw')
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(img)
    
    print(f"Successfully saved to {output_path}")

if __name__ == "__main__":
    remove_dots(input_raster, output_raster)
