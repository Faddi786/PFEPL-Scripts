from osgeo import gdal, ogr, osr

# input_raster = "output_85.tif"
input_raster = r"C:\Users\Swapnali\Desktop\Sakina Maam Work\Digitization\0. data\output_78.tif"
output_shapefile = "output_78_vector-with_CRS.shp"

# Open raster
src_ds = gdal.Open(input_raster)
srcband = src_ds.GetRasterBand(1)

# Get projection from raster
proj = src_ds.GetProjection()
srs = osr.SpatialReference()
srs.ImportFromWkt(proj)

# Create shapefile
driver = ogr.GetDriverByName("ESRI Shapefile")
dst_ds = driver.CreateDataSource(output_shapefile)

dst_layer = dst_ds.CreateLayer(
    "polygonized",
    srs=srs,
    geom_type=ogr.wkbPolygon
)

# Add attribute field
field = ogr.FieldDefn("DN", ogr.OFTInteger)
dst_layer.CreateField(field)

# Polygonize
gdal.Polygonize(srcband, None, dst_layer, 0)

# Close
dst_ds = None
src_ds = None