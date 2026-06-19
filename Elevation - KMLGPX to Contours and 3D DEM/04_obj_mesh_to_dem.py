import pyvista as pv
import numpy as np
# import os

# os.environ["PROJ_LIB"] = r"C:\Users\Swapnali\AppData\Roaming\Python\Python314\site-packages\pyproj\proj_dir\share\proj"

import rasterio
from rasterio.transform import from_origin
# --------------------------------------------------
# INPUTS
# --------------------------------------------------
obj_file = "terrain_surface.obj"
output_dem = "terrain_dem.tif"

# DEM resolution (meters per pixel)
pixel_size = 5.0   # change to 2, 10, etc.

# CRS of your terrain (VERY IMPORTANT)
# crs_epsg = "EPSG:32643"   # <-- CHANGE to your UTM zone

crs_epsg = (
    'PROJCS["WGS 84 / UTM zone 43N",'
    'GEOGCS["WGS 84",'
    'DATUM["WGS_1984",'
    'SPHEROID["WGS 84",6378137,298.257223563]],'
    'PRIMEM["Greenwich",0],'
    'UNIT["degree",0.0174532925199433]],'
    'PROJECTION["Transverse_Mercator"],'
    'PARAMETER["latitude_of_origin",0],'
    'PARAMETER["central_meridian",75],'
    'PARAMETER["scale_factor",0.9996],'
    'PARAMETER["false_easting",500000],'
    'PARAMETER["false_northing",0],'
    'UNIT["metre",1]]'
)

# --------------------------------------------------
# LOAD OBJ
# --------------------------------------------------
mesh = pv.read(obj_file)

points = mesh.points
x = points[:, 0]
y = points[:, 1]
z = points[:, 2]

# --------------------------------------------------
# CREATE GRID
# --------------------------------------------------
xmin, xmax = x.min(), x.max()
ymin, ymax = y.min(), y.max()

width = int((xmax - xmin) / pixel_size) + 1
height = int((ymax - ymin) / pixel_size) + 1

grid_x = np.linspace(xmin, xmax, width)
grid_y = np.linspace(ymax, ymin, height)  # top to bottom

dem = np.full((height, width), np.nan)

# --------------------------------------------------
# INTERPOLATE Z VALUES (nearest neighbor)
# --------------------------------------------------
for i in range(len(points)):
    col = int((x[i] - xmin) / pixel_size)
    row = int((ymax - y[i]) / pixel_size)
    dem[row, col] = z[i]

# Fill gaps
mask = np.isnan(dem)
dem[mask] = np.nanmean(dem)

# --------------------------------------------------
# WRITE GEOTIFF
# --------------------------------------------------
transform = from_origin(xmin, ymax, pixel_size, pixel_size)

with rasterio.open(
    output_dem,
    "w",
    driver="GTiff",
    height=dem.shape[0],
    width=dem.shape[1],
    count=1,
    dtype=dem.dtype,
    crs=crs_epsg,
    transform=transform,
) as dst:
    dst.write(dem, 1)

print("DEM created:", output_dem)