# =============================================================================
# TIFF → Clean Shapefile (removes ALL white dots & clusters automatically)
# Preserves main boundary lines/polygons perfectly + original CRS
# =============================================================================

import numpy as np
import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
import cv2
from skimage.morphology import area_opening, disk, binary_opening

def tiff_to_clean_shapefile(
    input_tif: str,
    output_shp: str,
    min_pixel_area: int = 80,           # MAIN CONTROL: remove polygons smaller than this (pixels)
                                        # ↑ Increase to 120–300 if clusters/dots remain
    brightness_threshold: int = 140,    # lower = keep fainter lines
    output_clean_tif: str = None        # optional: save super-clean raster
):
    print(f"Processing: {input_tif}")

    with rasterio.open(input_tif) as src:
        profile = src.profile.copy()
        count = src.count
        crs = src.crs
        transform = src.transform
        height, width = src.height, src.width

        print(f"  CRS: {crs}")

        # Read as grayscale
        if count == 1:
            gray = src.read(1).astype(np.uint8)
        else:
            rgb = np.moveaxis(src.read(), 0, -1).astype(np.uint8)
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

        # Step 1: Light bilateral filter to weaken small clusters without blurring lines
        print("Applying light smoothing...")
        gray_smoothed = cv2.bilateralFilter(gray, d=3, sigmaColor=50, sigmaSpace=50)

        # Step 2: Area opening (removes small bright objects based on pixel count)
        print(f"Area opening (remove < {min_pixel_area} pixel regions)...")
        cleaned_gray = area_opening(gray_smoothed, area_threshold=min_pixel_area, connectivity=2)

        # Step 3: Threshold to binary
        _, binary = cv2.threshold(cleaned_gray, brightness_threshold, 255, cv2.THRESH_BINARY)
        binary = binary.astype(np.uint8) // 255   # to 0/1

        # Optional: extra tiny opening to remove any leftover 1–2 px specks
        binary = binary_opening(binary, footprint=disk(1))

        # Optional: save the cleaned binary raster for checking
        if output_clean_tif:
            clean_profile = profile.copy()
            clean_profile.update(count=1, dtype='uint8', compress='lzw')
            with rasterio.open(output_clean_tif, 'w', **clean_profile) as dst:
                dst.write(binary[None, :, :])
            print(f"   Saved cleaned raster preview: {output_clean_tif}")

        # ===================== VECTORIZATION + NOISE FILTER =====================
        print("Vectorizing polygons and filtering small ones...")
        polygons = []
        for geom_dict, value in shapes(binary, transform=transform):
            if value > 0:  # foreground
                poly = shape(geom_dict)
                # Approximate pixel area (accurate enough for filtering)
                approx_pixel_area = poly.area / (abs(transform[0]) * abs(transform[4]))
                if approx_pixel_area >= min_pixel_area:
                    polygons.append(poly)

        if not polygons:
            print("Warning: No polygons met the size criteria. Try lowering min_pixel_area or brightness_threshold.")
            return

        gdf = gpd.GeoDataFrame(geometry=polygons, crs=crs)
        print(f"   → Kept {len(gdf)} features (removed small noise polygons)")

        # Optional: dissolve to merge touching polygons into one multipart feature
        # gdf = gdf.dissolve()

        gdf.to_file(output_shp)
        print(f"✅ Clean shapefile saved: {output_shp}")
        print("   Open in QGIS/ArcGIS — dots and clusters should be gone.")


# ====================== RUN EXAMPLE ======================
if __name__ == "__main__":
    tiff_to_clean_shapefile(
        input_tif="digitized_boundary_78.tif",
        output_shp="clean_boundary_78.shp",
        min_pixel_area=80,                  # ↑ try 120–250 if dots/clusters still appear
        brightness_threshold=140,
        output_clean_tif="cleaned_raster_preview.tif"  # optional, for visual check
    )