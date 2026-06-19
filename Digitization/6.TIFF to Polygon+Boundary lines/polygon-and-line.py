from osgeo import gdal, ogr
import geopandas as gpd

input_raster = "output_85.tif"
output_shapefile = "output_85_vector.shp"

# Open raster
src_ds = gdal.Open(input_raster)
srcband = src_ds.GetRasterBand(1)

# Create shapefile
driver = ogr.GetDriverByName("ESRI Shapefile")
dst_ds = driver.CreateDataSource(output_shapefile)
dst_layer = dst_ds.CreateLayer("polygonized", srs=None)

# Add attribute field
field = ogr.FieldDefn("DN", ogr.OFTInteger)
dst_layer.CreateField(field)

# Polygonize
gdal.Polygonize(srcband, None, dst_layer, 0)

gdf = gpd.read_file("output_85_vector.shp")

# Convert polygon boundaries to lines
gdf["geometry"] = gdf.boundary

gdf.to_file("MH_85_boundary_lines.shp")

# Close files
dst_ds = None
src_ds = None






