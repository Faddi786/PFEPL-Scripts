import json
from osgeo import gdal
from pyproj import Transformer

JSON_PATH = r"C:\Users\Swapnali\Desktop\Digitization\1. Extract Map Image from PDF\Trial 3\grid_output\grid_points_with_latlon.json"
OUTPUT_TIF = "output_polynomial_MH80.tif"

with open(JSON_PATH) as f:
    data = json.load(f)

image_path = data["image"]
points = data["points"]

transformer = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)

gcps = []
for p in points.values():
    x_pix = p["image"]["x"]
    y_pix = p["image"]["y"]
    lon = p["map"]["longitude"]
    lat = p["map"]["latitude"]

    x_map, y_map = transformer.transform(lon, lat)
    gcps.append(gdal.GCP(x_map, y_map, 0, x_pix, y_pix))

src = gdal.Open("inside_cropped_MH80.png")

tmp = gdal.Translate(
    "",
    src,
    format="MEM",
    GCPs=gcps,
    outputSRS="EPSG:32643"
)

gdal.Warp(
    "rough.tif",
    tmp,
    dstSRS="EPSG:32643",
    tps=True,                # 🔥 IMPORTANT
    resampleAlg="cubic"
)

print("✅ Polynomial (order 2) image created:", OUTPUT_TIF)
