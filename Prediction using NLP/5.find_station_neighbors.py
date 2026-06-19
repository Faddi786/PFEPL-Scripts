from __future__ import annotations

import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SHAPEFILES_DIR = ROOT_DIR / "Shapefiles"
REQUIRED_INFO_DIR = ROOT_DIR / "Required Station Info"
OUTPUT_FILE = ROOT_DIR / "Excel Files" / "station_neighbors_report.xlsx"
FINAL_MAPPED_FILE = ROOT_DIR / "Excel Files" / "Final_Mapped.xlsx"

EMPTY_COUNT_COL = "Number of empty cells, in the rainfall value column"


def _normalize_name(name: str) -> str:
    return " ".join(str(name).strip().split()).casefold()


def _remove_brackets(name: str) -> str:
    return re.sub(r"\([^)]*\)", "", str(name)).strip()


def _alnum_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _normalize_name(name))


def _name_keys(name: str) -> list[str]:
    n1 = _normalize_name(name)
    n2 = _normalize_name(_remove_brackets(name))
    n3 = _alnum_key(name)
    n4 = _alnum_key(_remove_brackets(name))
    return list(dict.fromkeys([k for k in [n1, n2, n3, n4] if k]))


def _candidate_station_columns(columns: list[str]) -> list[str]:
    lower_map = {c.lower(): c for c in columns}
    priority = ["name", "station", "station_name", "stn_name", "name_1"]
    out: list[str] = []
    for p in priority:
        if p in lower_map and lower_map[p] not in out:
            out.append(lower_map[p])
    for c in columns:
        lc = c.lower()
        if (("name" in lc) or ("station" in lc)) and c not in out:
            out.append(c)
    return out


def load_all_station_points(shapefiles_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for group_dir in sorted([p for p in shapefiles_dir.iterdir() if p.is_dir()]):
        for shp in sorted(group_dir.glob("*.shp")):
            gdf = gpd.read_file(shp)
            name_cols = _candidate_station_columns(list(gdf.columns))
            if not name_cols:
                continue

            # Use row-wise fallback across candidate columns.
            use_cols = [c for c in name_cols if c in gdf.columns]
            work = gdf[use_cols + ["geometry"]].copy()

            def pick_name(row: pd.Series) -> str | None:
                for c in use_cols:
                    val = row.get(c)
                    if pd.notna(val):
                        txt = str(val).strip()
                        if txt != "":
                            return txt
                return None

            work["station_name_raw"] = work.apply(pick_name, axis=1)
            work = work[work["station_name_raw"].notna() & work["geometry"].notna()]
            work["station_name_raw"] = work["station_name_raw"].astype(str).str.strip()
            work = work[work["station_name_raw"] != ""]
            work["source_group"] = group_dir.name

            # Normalize each shapefile to a common projected CRS independently.
            if work.crs is None:
                # fallback assumption if CRS metadata is missing
                work = work.set_crs("EPSG:4326", allow_override=True)
            work = work.to_crs(epsg=3857)
            work["x"] = work.geometry.x
            work["y"] = work.geometry.y
            work = work[np.isfinite(work["x"]) & np.isfinite(work["y"])].copy()

            rows.extend(work[["station_name_raw", "source_group", "x", "y"]].to_dict("records"))

    points = pd.DataFrame(rows)
    points["station_name_norm"] = points["station_name_raw"].map(_normalize_name)
    points["station_name_no_br"] = points["station_name_raw"].map(lambda s: _normalize_name(_remove_brackets(s)))
    points["station_name_alnum"] = points["station_name_raw"].map(_alnum_key)
    points["station_name_no_br_alnum"] = points["station_name_raw"].map(lambda s: _alnum_key(_remove_brackets(s)))
    return points


def load_targets_with_empty_counts(required_info_dir: Path) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for xlsx in sorted(required_info_dir.glob("*.xlsx")):
        if xlsx.name.startswith("~$"):
            continue
        xls = pd.ExcelFile(xlsx)
        if "Summary" not in xls.sheet_names:
            continue
        summary = pd.read_excel(xlsx, sheet_name="Summary")
        if "Sheet Names" not in summary.columns or EMPTY_COUNT_COL not in summary.columns:
            continue

        for _, row in summary.iterrows():
            station = row.get("Sheet Names")
            if pd.isna(station):
                continue
            records.append(
                {
                    "target_group": xlsx.stem,
                    "target_station": str(station).strip(),
                    "empty_cells_count": int(pd.to_numeric(row.get(EMPTY_COUNT_COL), errors="coerce") or 0),
                }
            )
    return pd.DataFrame(records)


def load_final_mapped_lookup(final_mapped_file: Path) -> dict[str, dict[str, str]]:
    """
    Reads Final_Mapped.xlsx and returns:
      group -> { normalized(excel_sheet_name): shapefile_station_name }
    We use this to resolve the 'true' shapefile station name for a given
    station sheet in Required Station Info.
    """
    if not final_mapped_file.exists():
        return {}

    out: dict[str, dict[str, str]] = {}
    xls = pd.ExcelFile(final_mapped_file)
    for sheet in xls.sheet_names:
        df = pd.read_excel(final_mapped_file, sheet_name=sheet)
        if "Shapefile Station Name" not in df.columns or "Excel Station Sheet Name" not in df.columns:
            continue
        group_map: dict[str, str] = {}
        for _, row in df.iterrows():
            shp_name = row.get("Shapefile Station Name")
            xls_name = row.get("Excel Station Sheet Name")
            if pd.isna(shp_name) or str(shp_name).strip() == "":
                continue
            if pd.isna(xls_name) or str(xls_name).strip() == "":
                continue
            group_map[_normalize_name(str(xls_name))] = str(shp_name).strip()
        out[sheet] = group_map
    return out


def resolve_target_coordinates(
    target_group: str,
    target_station_sheet_name: str,
    points: pd.DataFrame,
    final_map: dict[str, dict[str, str]],
) -> tuple[float | None, float | None, str]:
    """
    Resolve coordinates for a station sheet name.

    Strategy:
      1) Use Final_Mapped.xlsx (group sheet) to map Excel sheet -> shapefile station name.
      2) Resolve coordinate from shapefiles using that shapefile station name.
         If multiple coords exist, prefer the point whose source_group == target_group.
      3) If no mapping exists, fall back to using the sheet name directly.

    Returns: (x, y, used_name_for_lookup)
    """
    used_name = target_station_sheet_name
    group_map = final_map.get(target_group, {})
    mapped = group_map.get(_normalize_name(target_station_sheet_name))
    if mapped:
        used_name = mapped

    # Try progressively relaxed match keys.
    keys = _name_keys(used_name)
    for i, k in enumerate(keys):
        if i == 0:
            matches = points[points["station_name_norm"] == k]
        elif i == 1:
            matches = points[points["station_name_no_br"] == k]
        elif i == 2:
            matches = points[points["station_name_alnum"] == k]
        else:
            matches = points[points["station_name_no_br_alnum"] == k]

        if matches.empty:
            continue

        # Prefer same source group when ambiguous.
        same_group = matches[
            matches["source_group"].astype(str).str.casefold() == str(target_group).casefold()
        ]
        if not same_group.empty:
            uniq = same_group[["x", "y"]].drop_duplicates()
            if len(uniq) >= 1:
                rec = same_group.sort_values(["x", "y"]).iloc[0]
                return float(rec["x"]), float(rec["y"]), used_name

        uniq = matches[["x", "y"]].drop_duplicates()
        if len(uniq) == 1:
            rec = uniq.iloc[0]
            return float(rec["x"]), float(rec["y"]), used_name

    return None, None, used_name


def find_neighbors_for_target(
    target_station_lookup_name: str,
    target_x: float,
    target_y: float,
    points: pd.DataFrame,
    max_neighbors: int = 4,
) -> dict[str, object]:
    work = points.copy()
    work["distance_km"] = (((work["x"] - target_x) ** 2 + (work["y"] - target_y) ** 2) ** 0.5) / 1000.0

    # Exclude self by resolved lookup name and by exact same coordinate.
    target_norm = _normalize_name(target_station_lookup_name)
    work = work[work["station_name_norm"] != target_norm]
    work = work[(work["x"] != target_x) | (work["y"] != target_y)]
    work = work[np.isfinite(work["distance_km"]) & (work["distance_km"] > 0)]

    # Keep nearest row per station name to avoid duplicates from repeated points.
    work = work.sort_values("distance_km").drop_duplicates(subset=["station_name_raw"], keep="first")

    within_30 = work[work["distance_km"] <= 30].sort_values("distance_km")
    neigh_30 = within_30.head(max_neighbors)

    picked = neigh_30.copy()
    needed = max_neighbors - len(picked)
    neigh_50_count = 0
    used_radius_more_than_50 = False

    if needed > 0:
        within_50 = work[(work["distance_km"] > 30) & (work["distance_km"] <= 50)].sort_values("distance_km")
        extra_50 = within_50.head(needed)
        neigh_50_count = len(extra_50)
        if len(extra_50) > 0:
            picked = pd.concat([picked, extra_50], ignore_index=True)
        needed = max_neighbors - len(picked)

    if needed > 0:
        # Fallback: take nearest neighbors even beyond 50 km.
        beyond_50 = work[work["distance_km"] > 50].sort_values("distance_km")
        extra_any = beyond_50.head(needed)
        if len(extra_any) > 0:
            used_radius_more_than_50 = True
            picked = pd.concat([picked, extra_any], ignore_index=True)

    out: dict[str, object] = {
        "No. of neighbours from 30km radius": len(neigh_30),
        "No. of neighbours from 50km radius": neigh_50_count,
        "Used radius more than 50km": used_radius_more_than_50,
    }

    picked = picked.reset_index(drop=True)
    for i in range(4):
        idx = i + 1
        if i < len(picked):
            out[f"Neighbour_{idx}_Name"] = picked.loc[i, "station_name_raw"]
            out[f"Neighbour_{idx}_Distance_from_Target_km"] = round(float(picked.loc[i, "distance_km"]), 3)
        else:
            out[f"Neighbour_{idx}_Name"] = ""
            out[f"Neighbour_{idx}_Distance_from_Target_km"] = ""

    return out


def build_neighbors_report() -> None:
    if not SHAPEFILES_DIR.exists():
        raise FileNotFoundError(f"Shapefiles folder not found: {SHAPEFILES_DIR}")
    if not REQUIRED_INFO_DIR.exists():
        raise FileNotFoundError(f"Required Station Info folder not found: {REQUIRED_INFO_DIR}")

    points = load_all_station_points(SHAPEFILES_DIR)
    targets = load_targets_with_empty_counts(REQUIRED_INFO_DIR)
    if targets.empty:
        raise ValueError("No targets found from Summary sheets.")
    final_map = load_final_mapped_lookup(FINAL_MAPPED_FILE)

    rows: list[dict[str, object]] = []
    for _, t in targets.iterrows():
        group = str(t["target_group"])
        station = str(t["target_station"])
        x, y, used_name = resolve_target_coordinates(group, station, points, final_map)
        base = {
            "Target Station": station,
            EMPTY_COUNT_COL: int(t["empty_cells_count"]),
            "Shapefile Station Name (used for coords)": used_name,
        }

        if x is None or y is None:
            rows.append(
                {
                    **base,
                    "No. of neighbours from 30km radius": 0,
                    "No. of neighbours from 50km radius": 0,
                    "Used radius more than 50km": False,
                    "Neighbour_1_Name": "",
                    "Neighbour_1_Distance_from_Target_km": "",
                    "Neighbour_2_Name": "",
                    "Neighbour_2_Distance_from_Target_km": "",
                    "Neighbour_3_Name": "",
                    "Neighbour_3_Distance_from_Target_km": "",
                    "Neighbour_4_Name": "",
                    "Neighbour_4_Distance_from_Target_km": "",
                }
            )
            continue

        neigh = find_neighbors_for_target(used_name, x, y, points, max_neighbors=4)
        rows.append({**base, **neigh})

    out_df = pd.DataFrame(rows)
    out_df = out_df.sort_values(["Target Station"]).reset_index(drop=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        out_df.to_excel(OUTPUT_FILE, index=False)
        print(f"Neighbor report created: {OUTPUT_FILE}")
    except PermissionError:
        # Typically happens when the Excel file is open in Excel.
        alt = OUTPUT_FILE.with_name(f"{OUTPUT_FILE.stem}_v2{OUTPUT_FILE.suffix}")
        out_df.to_excel(alt, index=False)
        print(f"Neighbor report created (original was locked): {alt}")


if __name__ == "__main__":
    build_neighbors_report()

