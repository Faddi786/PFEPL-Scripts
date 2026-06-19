import rasterio
import numpy as np

def save_mask(mask, profile, output_path):

    profile.update(
        dtype=rasterio.uint8,
        count=1
    )

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(mask.astype("uint8"), 1)