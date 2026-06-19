# -*- coding: utf-8 -*-

import arcpy
import os
import sys

# -------------------------------------------------
# USER INPUTS
# -------------------------------------------------
kml_file = r"C:\Users\Swapnali\Desktop\Sakina Maam Work\Elevation\KML_to_Contour\input_path.kml"
workspace = r"C:\Users\Swapnali\Desktop\Sakina Maam Work\Elevation\KML_to_Contour\output"
z_field = "Z"   # CHANGE if needed

# -------------------------------------------------
# ENVIRONMENT
# -------------------------------------------------
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True

if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
else:
    raise Exception("Spatial Analyst not available")

# -------------------------------------------------
# OUTPUT PATHS
# -------------------------------------------------
gdb = os.path.join(workspace, "temp.gdb")
kml_layer = os.path.join(workspace, "kml_layer")
kriging_raster = os.path.join(workspace, "kriging.tif")
contours = os.path.join(workspace, "contours.shp")

# -------------------------------------------------
# STEP 1: KML → LAYER
# -------------------------------------------------
print("Converting KML to Layer...")

# arcpy.KMLToLayer_conversion(
#     in_kml_file=kml_file,
#     out_folder=workspace,
#     out_name="kml_layer"
# )
arcpy.KMLToLayer_conversion(kml_file, workspace, "kml_layer")

# -------------------------------------------------
# STEP 2: GET POLYLINE FEATURE
# -------------------------------------------------
fc_line = os.path.join(kml_layer + ".gdb", "Placemarks", "Polylines")

# -------------------------------------------------
# STEP 3: LINE → POINTS
# -------------------------------------------------
if not arcpy.Exists(gdb):
    arcpy.CreateFileGDB_management(workspace, "temp.gdb")

points_fc = os.path.join(gdb, "track_points")

print("Extracting vertices as points...")
arcpy.FeatureVerticesToPoints_management(
    fc_line,
    points_fc,
    "ALL"
)

# -------------------------------------------------
# STEP 4: VERIFY CRS
# -------------------------------------------------
sr = arcpy.Describe(points_fc).spatialReference
print("Detected CRS:", sr.name)

if sr.factoryCode != 4326:
    raise Exception("CRS is not GCS_WGS_1984")

print("CRS verified: GCS_WGS_1984")

# -------------------------------------------------
# STEP 5: KRIGING
# -------------------------------------------------
print("Running Kriging...")

from arcpy.sa import Kriging, KrigingModelOrdinary

kriging = Kriging(
    in_point_features=points_fc,
    z_field=z_field,
    kriging_model=KrigingModelOrdinary("SPHERICAL")
)

kriging.save(kriging_raster)

# -------------------------------------------------
# STEP 6: CONTOURS
# -------------------------------------------------
interval = float(raw_input("Enter contour interval: "))

print("Generating contours...")
arcpy.sa.Contour(
    kriging_raster,
    contours,
    interval
)

arcpy.CheckInExtension("Spatial")

print("\nPROCESS COMPLETED SUCCESSFULLY")