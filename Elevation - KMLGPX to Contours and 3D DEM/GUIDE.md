# Elevation — KML/GPX to Contours and 3D DEM — User Guide

## Overview

Four-script workflow for converting GPS tracks (GPX or KML) into kriging contours, 3D surfaces, and DEM rasters using **ArcPy (ArcGIS)**.

```
01_gpx_to_kriging_contours.py  ─┐
02_kml_to_kriging_contours.py  ─┤  (choose one entry point)
                                ↓
03_contours_to_3d_surface.py
                                ↓
04_obj_mesh_to_dem.py
```

Scripts **01** and **02** are alternative entry points. Scripts **03** and **04** form a sequential sub-pipeline.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| ArcGIS Desktop / Pro | With **Spatial Analyst** extension |
| Python | ArcGIS-bundled Python with `arcpy` |
| Extension | Spatial Analyst must be available mem out |

---

## Script 01 — GPX to Kriging Contours

### Input

Edit paths at top of script:

```python
gpx_file = r"C:\Data\input_gpx_file.gpx"
output_folder = r"C:\Data\output"
```

**GPX requirements:** Must contain track points, route points, or waypoints with elevation data.

### How to Run

Run from ArcGIS Python environment:

```python
# ArcGIS Python prompt or IDE
exec(open(r"C:\...\01_gpx_to_kriging_contours.py").read())
```

### Output

```
output\
  gpx_data.gdb\          # Point features from GPX
  kriging.tif            # Interpolated elevation raster
  contours.shp           # Contour lines
```

---

## Script 02 — KML to Kriging Contours

Same workflow as Script 01 but for **KML** input. Edit `kml_file` and `output_folder` at script top.

Use **either** 01 or 02 — not both for the same dataset.

---

## Script 03 — Contours to 3D Surface

### Input

Contour shapefile from Script 01/02 output.

Edit paths at top of script to point to `contours.shp` and output locations.

### Output

3D surface mesh (OBJ format) from contour lines.

---

## Script 04 — OBJ Mesh to DEM

### Input

OBJ mesh from Script 03.

### Output

Digital Elevation Model raster.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Spatial Analyst not available | Extension not licensed | Check out Spatial Analyst in ArcGIS |
| No elevation field found | GPX/KML lacks Z values | Verify elevation in source file |
| No point feature class | Empty GPX | Check GPX has track/route/waypoint data |
| Hardcoded paths invalid | Paths point to another machine | Update all path variables |

---

## Sample Workflow

1. Prepare GPX with elevation: `survey_track.gpx`
2. Edit paths in `01_gpx_to_kriging_contours.py`
3. Run in ArcGIS Python → get `kriging.tif` + `contours.shp`
4. Edit paths in `03_contours_to_3d_surface.py` → run
5. Edit paths in `04_obj_mesh_to_dem.py` → run → final DEM

---

## Notes

- All scripts use hardcoded Windows paths — update for your machine.
- Requires ArcGIS license; not runnable with standard Python/pip alone.
