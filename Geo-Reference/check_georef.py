#!/usr/bin/env python3
"""Check whether GeoTIFFs in Output/ are properly geo-referenced."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def configure_proj_environment() -> None:
    try:
        import pyproj.datadir

        proj_data = pyproj.datadir.get_data_dir()
    except ImportError:
        return

    if (Path(proj_data) / "proj.db").is_file():
        os.environ["PROJ_DATA"] = proj_data
        os.environ["PROJ_LIB"] = proj_data

    for var in ("PROJ_DATA", "PROJ_LIB"):
        current = os.environ.get(var, "")
        if "postgis" in current.lower() or "postgresql" in current.lower():
            os.environ[var] = proj_data


configure_proj_environment()

import rasterio
from rasterio.transform import Affine

OUTPUT_DIR = Path(__file__).resolve().parent / "Output"


def check_file(path: Path) -> bool:
    print("=" * 60)
    print(path.name)

    with rasterio.open(path) as src:
        has_crs = src.crs is not None
        has_transform = src.transform != Affine.identity()
        bounds = src.bounds

        print(f"  CRS present       : {has_crs}")
        if has_crs:
            print(f"  CRS               : {src.crs}")
        print(f"  Geotransform set  : {has_transform}")
        print(f"  Transform         : {src.transform}")
        print(
            "  Bounds            : "
            f"west={bounds.left:.6f}, south={bounds.bottom:.6f}, "
            f"east={bounds.right:.6f}, north={bounds.top:.6f}"
        )
        print(f"  Size              : {src.width} x {src.height} px")

        ok = has_crs and has_transform
        print(f"  Status            : {'OK - geo-referenced' if ok else 'FAIL - not geo-referenced'}")
        return ok


def main() -> int:
    files = sorted(OUTPUT_DIR.glob("*_georef.tif"))
    if not files:
        print(f"No GeoTIFF files found in {OUTPUT_DIR}")
        return 1

    results = [check_file(path) for path in files]
    print()
    print(f"Checked {len(files)} file(s): {sum(results)} OK, {len(files) - sum(results)} failed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
