import os
from osgeo import ogr, gdal

gdal.UseExceptions()

# ------------------ INPUT ------------------
INPUT_LINES = r"C:\Users\user\Desktop\Georeferenced RF SS - Copy (input is tiff) (for crz boundary)\output\red_median_line\shapefiles\boundary_middle_line_connected_v2.shp"
# -------------------------------------------

# ------------------ OUTPUT -----------------
OUTPUT_POLYGONS = r"C:\Users\user\Desktop\Georeferenced RF SS - Copy (input is tiff) (for crz boundary)\output\red_median_line\shapefiles\enclosed_polygons_v2.shp"
# -------------------------------------------

# ==========================================================
# OPEN INPUT SHAPEFILE
# ==========================================================
driver = ogr.GetDriverByName("ESRI Shapefile")

ds = driver.Open(INPUT_LINES, 0)
if ds is None:
    raise RuntimeError("Could not open input shapefile")

layer = ds.GetLayer()
spatial_ref = layer.GetSpatialRef()

# ==========================================================
# COLLECT ALL LINES INTO ONE GEOMETRY
# ==========================================================
multi = ogr.Geometry(ogr.wkbMultiLineString)
line_count = 0

for feat in layer:
    geom = feat.GetGeometryRef()
    if geom is None:
        continue

    g = geom.Clone()

    # Fix invalid geometries
    if not g.IsValid():
        g = g.MakeValid()

    if g.Length() > 0:
        multi.AddGeometry(g)
        line_count += 1

print("Lines collected")
print(f"Valid line features: {line_count}")

if line_count == 0:
    raise RuntimeError("No valid line geometries found in input shapefile")

# ==========================================================
# UNARY UNION (CRITICAL STEP)
# This snaps endpoints & builds planar topology
# ==========================================================
# GDAL/OGR 3.4.x provides UnionCascaded (not UnaryUnion)
def robust_unary_union(multiline):
    """Run union with lightweight fallbacks (fast path)."""
    union_geom = multiline.UnionCascaded()
    if union_geom is not None:
        return union_geom, "UnionCascaded"

    # Some datasets recover after MakeValid on the collection.
    try:
        valid_multi = multiline.MakeValid()
        if valid_multi is not None:
            union_geom = valid_multi.UnionCascaded()
            if union_geom is not None:
                return union_geom, "MakeValid + UnionCascaded"
    except Exception:
        pass

    return None, "UnionCascaded unavailable"


union, union_method = robust_unary_union(multi)
print(f"Topology method: {union_method}")

# ==========================================================
# POLYGONIZE USING GEOS
# ==========================================================
polygons = None
polygon_sources = []
if union is not None:
    polygon_sources.append(("unified geometry", union))
polygon_sources.append(("raw multiline geometry", multi))

for label, polygon_source in polygon_sources:
    try:
        polygons = polygon_source.Polygonize()
    except Exception:
        polygons = None

    if polygons is not None and polygons.GetGeometryCount() > 0:
        print(f"Polygonized from {label}")
        break
    else:
        print(f"No polygons from {label}")

if polygons is None or polygons.GetGeometryCount() == 0:
    raise RuntimeError("No polygons created")

print(f"Polygons found: {polygons.GetGeometryCount()}")

# ==========================================================
# CREATE OUTPUT SHAPEFILE
# ==========================================================
if os.path.exists(OUTPUT_POLYGONS):
    driver.DeleteDataSource(OUTPUT_POLYGONS)

out_ds = driver.CreateDataSource(OUTPUT_POLYGONS)
out_layer = out_ds.CreateLayer(
    "polygons",
    srs=spatial_ref,
    geom_type=ogr.wkbPolygon
)

out_layer.CreateField(ogr.FieldDefn("id", ogr.OFTInteger))
out_layer.CreateField(ogr.FieldDefn("area", ogr.OFTReal))

# ==========================================================
# WRITE POLYGONS
# ==========================================================
for i in range(polygons.GetGeometryCount()):
    poly = polygons.GetGeometryRef(i)

    feat = ogr.Feature(out_layer.GetLayerDefn())
    feat.SetField("id", i + 1)
    feat.SetField("area", poly.GetArea())
    feat.SetGeometry(poly)
    out_layer.CreateFeature(feat)
    feat = None

# ==========================================================
# CLEANUP
# ==========================================================
ds = None
out_ds = None

print("DONE")
print("Closed polygons successfully created from SHP")
print(f"Saved to: {OUTPUT_POLYGONS}")
