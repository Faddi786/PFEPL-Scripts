# =============================================================================
# Aggressive removal of remaining white dots & clusters in GeoTIFF
# Uses multi-scale area opening + grayscale processing
# Preserves thin continuous lines as much as possible
# =============================================================================

import numpy as np
import rasterio
from skimage.morphology import area_opening, disk, binary_closing
import cv2

def aggressive_remove_dots_clusters(
    input_path: str,
    output_path: str,
    area_threshold: int = 80,           # min area (pixels) to KEEP → remove anything smaller
                                        # ↑ this is now the main control: 50–300 typical
    base_threshold: int = 140,          # lower to catch fainter dots/clusters
    max_kernel_diam: int = 9,           # largest opening kernel (odd number: 5,7,9,11)
    preserve_intensity: bool = True     # True = keep original values; False = binarize output
):
    print(f"Opening: {input_path}")
    with rasterio.open(input_path) as src:
        profile = src.profile.copy()
        count = src.count
        dtype = src.dtypes[0]
        height, width = src.height, src.width

        print(f"  CRS       : {src.crs}")
        print(f"  Shape     : {height} × {width} × {count} bands")
        print(f"  Data type : {dtype}")

        img = src.read()  # (bands, H, W)

        # Grayscale
        if count == 1:
            gray = img[0].astype(np.uint8)
        else:
            gray = cv2.cvtColor(np.moveaxis(img.astype(np.uint8), 0, -1), cv2.COLOR_RGB2GRAY)

        # Optional: very light bilateral to reduce cluster cohesion without blurring lines much
        gray = cv2.bilateralFilter(gray, d=3, sigmaColor=50, sigmaSpace=50)

        # Multi-scale area opening in grayscale (preserves thin structures better than binary)
        print(f"Applying multi-scale area opening (threshold={area_threshold})...")
        cleaned_gray = gray.copy()
        for diam in range(3, max_kernel_diam + 1, 2):  # 3,5,7,9,...
            print(f"  → Opening iteration with diam={diam}")
            footprint = disk(diam // 2 + 1)
            # area_opening on grayscale removes small bright peaks
            cleaned_gray = area_opening(cleaned_gray, area_threshold, footprint=footprint)

        # Final binary decision on the cleaned grayscale
        _, binary_clean = cv2.threshold(cleaned_gray, base_threshold, 255, cv2.THRESH_BINARY)

        keep_mask = binary_clean.astype(bool) > 0

        # Optional: tiny closing to reconnect any broken line bits (very conservative)
        if max_kernel_diam > 5:
            keep_mask = binary_closing(keep_mask, footprint=disk(1))

        pixels_removed = np.sum(~keep_mask)
        pixels_total = height * width
        print(f"  → Removing ≈ {pixels_removed:,} / {pixels_total:,} pixels ({pixels_removed/pixels_total*100:.2f}%)")

        # Re-apply to original image
        if preserve_intensity:
            cleaned = np.where(
                keep_mask[None, :, :],
                img,
                0
            ).astype(dtype)
        else:
            # If you want strict black/white output (for vectorization later)
            cleaned = np.repeat(keep_mask[None, :, :] * 255, count, axis=0).astype(dtype)

        profile.update({
            'compress': 'lzw',
            'predictor': 2 if 'uint' in dtype or 'int' in dtype else None,
        })

        print(f"Writing: {output_path}")
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(cleaned)

    print("Done.")
    print("Main tuning parameters:")
    print("  • area_threshold = 50–300 (higher → more dots/clusters removed)")
    print("  • base_threshold = 120–180 (lower → catch fainter noise)")
    print("  • max_kernel_diam = 7–15 (higher → larger clusters targeted)")
    print("  • preserve_intensity = True (keep original colors) or False (pure B/W)")


if __name__ == "__main__":
    aggressive_remove_dots_clusters(
        input_path="digitized_boundary_78.tif",
        output_path="cleaned_aggressive_dots_clusters_78.tif",
        area_threshold=120,           # ← start here, increase to 150–250 if clusters remain
        base_threshold=140,
        max_kernel_diam=11,           # ← increase to 13–15 if still dots left
        preserve_intensity=True
    )