from __future__ import annotations

from pathlib import Path
from typing import Iterable

import geopandas as gpd
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SHAPEFILES_DIR = ROOT_DIR / "Shapefiles"
OUTPUT_EXCEL = ROOT_DIR / "Excel Files" / "stations_by_folder.xlsx"


def _candidate_station_columns(columns: Iterable[str]) -> list[str]:
    """Return likely station-name columns in priority order."""
    cols = list(columns)
    lower_map = {c.lower(): c for c in cols}
    priority_exact = [
        "name",
        "station",
        "station_name",
        "stn_name",
        "name_1",
    ]
    matches: list[str] = []

    for key in priority_exact:
        if key in lower_map and lower_map[key] not in matches:
            matches.append(lower_map[key])

    for col in cols:
        lowered = col.lower()
        if (
            lowered not in priority_exact
            and ("name" in lowered or "station" in lowered)
            and col not in matches
        ):
            matches.append(col)

    return matches


def _extract_station_names(shapefile_path: Path) -> list[str]:
    gdf = gpd.read_file(shapefile_path)
    candidate_cols = _candidate_station_columns(gdf.columns)
    if not candidate_cols:
        return []

    names = pd.Series(dtype=str)
    for col in candidate_cols:
        values = gdf[col].dropna().astype(str).str.strip()
        values = values[values != ""]
        names = pd.concat([names, values], ignore_index=True)

    unique_sorted = sorted(set(names.tolist()), key=lambda x: x.casefold())
    return unique_sorted


def build_station_workbook(shapefiles_dir: Path, output_excel: Path) -> None:
    if not shapefiles_dir.exists():
        raise FileNotFoundError(f"Shapefiles directory not found: {shapefiles_dir}")

    output_excel.parent.mkdir(parents=True, exist_ok=True)

    folder_paths = sorted([p for p in shapefiles_dir.iterdir() if p.is_dir()])
    if not folder_paths:
        raise ValueError(f"No subfolders found in: {shapefiles_dir}")

    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        for folder_path in folder_paths:
            all_stations: list[str] = []
            shapefiles = sorted(folder_path.glob("*.shp"))

            for shp in shapefiles:
                all_stations.extend(_extract_station_names(shp))

            unique_stations = sorted(set(all_stations), key=lambda x: x.casefold())
            sheet_df = pd.DataFrame({"Station Name": unique_stations})

            # Excel sheet names are limited to 31 chars.
            sheet_name = folder_path.name[:31]
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Excel created successfully: {output_excel}")


if __name__ == "__main__":
    build_station_workbook(SHAPEFILES_DIR, OUTPUT_EXCEL)
