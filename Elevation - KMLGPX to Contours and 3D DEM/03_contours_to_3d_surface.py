import geopandas as gpd
import numpy as np
import pyvista as pv
from shapely.geometry import LineString
from scipy.spatial import Delaunay

# --------------------------------------------------
# INPUT
# --------------------------------------------------
shapefile_path = "contours.shp"
elevation_field = "Contour"   # <-- change to your contour height column

import geopandas as gpd

gdf = gpd.read_file("contours.shp")

print("Available columns:")
print(gdf.columns)

# --------------------------------------------------
# LOAD SHAPEFILE
# --------------------------------------------------
gdf = gpd.read_file(shapefile_path)

# --------------------------------------------------
# EXTRACT 3D POINTS FROM CONTOURS
# --------------------------------------------------
points = []

for _, row in gdf.iterrows():
    elev = float(row[elevation_field])
    geom = row.geometry

    if isinstance(geom, LineString):
        for x, y in geom.coords:
            points.append([x, y, elev])

points = np.array(points)

print(f"Extracted {len(points)} 3D points from contours")

# --------------------------------------------------
# CREATE TIN USING DELAUNAY TRIANGULATION
# --------------------------------------------------
xy = points[:, :2]
z = points[:, 2]

tri = Delaunay(xy)

# Create PyVista mesh
mesh = pv.PolyData(points)
mesh.faces = np.hstack(
    [np.full((len(tri.simplices), 1), 3), tri.simplices]
)

# --------------------------------------------------
# VISUALIZE 3D SURFACE
# --------------------------------------------------
plotter = pv.Plotter()
plotter.add_mesh(
    mesh,
    scalars=z,
    cmap="terrain",
    show_edges=False
)
plotter.add_axes()
plotter.show_grid()
plotter.show()

# --------------------------------------------------
# EXPORT 3D MODEL
# --------------------------------------------------
mesh.save("terrain_surface.obj")
print("3D model exported: terrain_surface.obj")