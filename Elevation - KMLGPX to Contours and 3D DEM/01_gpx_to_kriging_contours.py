# -*- coding: utf-8 -*-

import arcpy
import os

# -------------------------------------------------
# USER INPUTS
# -------------------------------------------------
gpx_file = r"C:\Users\Swapnali\Desktop\Sakina Maam Work\Elevation\KML_to_Contour\input_gpx_file.gpx"
output_folder = r"C:\Users\Swapnali\Desktop\Sakina Maam Work\Elevation\KML_to_Contour\output"

# -------------------------------------------------
# ENVIRONMENT
# -------------------------------------------------
arcpy.env.workspace = output_folder
arcpy.env.overwriteOutput = True

if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
else:
    raise Exception("Spatial Analyst extension not available")

# -------------------------------------------------
# OUTPUT GDB
# -------------------------------------------------
gdb = os.path.join(output_folder, "gpx_data.gdb")

if not arcpy.Exists(gdb):
    arcpy.CreateFileGDB_management(output_folder, "gpx_data.gdb")

# -------------------------------------------------
# STEP 1: GPX → FEATURES
# -------------------------------------------------
print("Converting GPX to features...")
arcpy.GPXtoFeatures_conversion(gpx_file, gdb)

# -------------------------------------------------
# STEP 2: FIND POINT FEATURE CLASS
# -------------------------------------------------
point_fc = None
candidates = ["track_points", "route_points", "waypoints"]

for name in candidates:
    fc_path = os.path.join(gdb, name)
    if arcpy.Exists(fc_path):
        point_fc = fc_path
        break

if point_fc is None:
    raise Exception("No point feature class found in GPX output")

print("Using point feature class:", os.path.basename(point_fc))

# -------------------------------------------------
# STEP 3: FIND ELEVATION FIELD
# -------------------------------------------------
fields = arcpy.ListFields(point_fc)
numeric_fields = [f.name for f in fields if f.type in ("Double", "Single", "Integer", "SmallInteger")]

possible_elevation_fields = ["Elevation", "ele", "elevation", "Altitude", "altitude"]

z_field = None
for f in possible_elevation_fields:
    if f in numeric_fields:
        z_field = f
        break

if z_field is None:
    raise Exception("No numeric elevation field found")

print("Using elevation field:", z_field)

# -------------------------------------------------
# STEP 4: KRIGING
# -------------------------------------------------
print("Running Kriging...")

from arcpy.sa import Kriging, KrigingModelOrdinary

kriging_raster = os.path.join(output_folder, "kriging.tif")

kriging = Kriging(
    point_fc,
    z_field,
    KrigingModelOrdinary("SPHERICAL")
)

kriging.save(kriging_raster)

print("Kriging raster created")

# -------------------------------------------------
# STEP 5: CONTOURS
# -------------------------------------------------
interval = float(raw_input("Enter contour interval: "))

contours_fc = os.path.join(output_folder, "contours.shp")

print("Generating contours...")
arcpy.sa.Contour(
    kriging_raster,
    contours_fc,
    interval
)

arcpy.CheckInExtension("Spatial")

print("\nPROCESS COMPLETED SUCCESSFULLY")