from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
STATIONS_FILE = ROOT_DIR / "Excel Files" / "stations_by_folder.xlsx"
SOURCE_DIR = ROOT_DIR / "Excel Files" / "Excels with required date range"
OUTPUT_DIR = ROOT_DIR / "Required Station Info"
MAPPING_FILE = ROOT_DIR / "Excel Files" / "station_mapping.xlsx"
FINAL_MAPPING_FILE = ROOT_DIR / "Excel Files" / "Final_Mapped.xlsx"


def _normalize_station_name(name: str) -> str:
    return " ".join(str(name).strip().split()).casefold()


def _normalize_without_brackets(name: str) -> str:
    return re.sub(r"\([^)]*\)", "", name).strip()


def _normalize_alnum_only(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name)


def _build_exact_lookup(sheet_names: list[str]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for sheet in sheet_names:
        if _normalize_station_name(sheet) == "overview":
            continue
        key = _normalize_station_name(sheet)
        lookup.setdefault(key, []).append(sheet)
    return lookup


def _build_no_bracket_lookup(sheet_names: list[str]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for sheet in sheet_names:
        if _normalize_station_name(sheet) == "overview":
            continue
        key = _normalize_station_name(_normalize_without_brackets(sheet))
        if key:
            lookup.setdefault(key, []).append(sheet)
    return lookup


def _resolve_station_sheet(
    station: str,
    exact_lookup: dict[str, list[str]],
    no_bracket_lookup: dict[str, list[str]],
) -> tuple[str | None, str | None]:
    # 1) Exact match first (case/spacing normalized only).
    exact_key = _normalize_station_name(station)
    exact_matches = sorted(set(exact_lookup.get(exact_key, [])), key=lambda x: x.casefold())
    if len(exact_matches) == 1:
        return exact_matches[0], None
    if len(exact_matches) > 1:
        return None, f"Ambiguous exact match in source file: {', '.join(exact_matches)}"

    # 2) Fallback: match after removing bracketed text.
    no_bracket_key = _normalize_station_name(_normalize_without_brackets(station))
    relaxed_matches = sorted(set(no_bracket_lookup.get(no_bracket_key, [])), key=lambda x: x.casefold())
    if len(relaxed_matches) == 1:
        return relaxed_matches[0], None
    if len(relaxed_matches) > 1:
        return None, f"Ambiguous bracket-insensitive match in source file: {', '.join(relaxed_matches)}"

    return None, None


def _read_station_list_by_group(stations_file: Path) -> dict[str, list[str]]:
    station_map: dict[str, list[str]] = {}
    xls = pd.ExcelFile(stations_file)

    for sheet in xls.sheet_names:
        df = pd.read_excel(stations_file, sheet_name=sheet)
        if "Station Name" not in df.columns:
            station_map[sheet] = []
            continue

        names = (
            df["Station Name"]
            .dropna()
            .astype(str)
            .map(lambda x: x.strip())
        )
        names = names[names != ""]
        station_map[sheet] = sorted(set(names.tolist()), key=lambda x: x.casefold())

    return station_map


def _read_mapping_by_group(mapping_file: Path) -> dict[str, dict[str, str]]:
    """
    Reads mapping workbook created by build_station_mapping_workbook.py.
    Expected per-sheet columns:
      - Shapefile Station Name
      - Excel Station Sheet Name
    Returns: group -> { normalized(shapefile_station): excel_sheet_name }
    """
    if not mapping_file.exists():
        return {}

    mapping: dict[str, dict[str, str]] = {}
    xls = pd.ExcelFile(mapping_file)
    for sheet in xls.sheet_names:
        df = pd.read_excel(mapping_file, sheet_name=sheet)
        if "Shapefile Station Name" not in df.columns or "Excel Station Sheet Name" not in df.columns:
            continue
        group_map: dict[str, str] = {}
        for _, row in df.iterrows():
            left = row.get("Shapefile Station Name")
            right = row.get("Excel Station Sheet Name")
            if pd.isna(left) or str(left).strip() == "":
                continue
            if pd.isna(right) or str(right).strip() == "":
                continue
            group_map[_normalize_station_name(str(left))] = str(right).strip()
        mapping[sheet] = group_map
    return mapping


def _read_final_mapping_by_group(final_mapping_file: Path) -> dict[str, dict[str, str]]:
    """
    Reads user-curated mapping workbook (Final_Mapped.xlsx).
    Expected per-sheet columns:
      - Shapefile Station Name
      - Excel Station Sheet Name
    Returns: group -> { normalized(shapefile_station): excel_sheet_name }
    Notes:
      - Rows with blank Excel Station Sheet Name are ignored (user chose to leave unmapped).
    """
    return _read_mapping_by_group(final_mapping_file)


def _filter_by_date(df: pd.DataFrame, start_date: str | None, end_date: str | None) -> pd.DataFrame:
    if "Date" not in df.columns or (start_date is None and end_date is None):
        return df

    date_series = pd.to_datetime(df["Date"], errors="coerce")
    mask = pd.Series(True, index=df.index)

    if start_date:
        start = pd.to_datetime(start_date)
        mask &= date_series >= start

    if end_date:
        end = pd.to_datetime(end_date)
        mask &= date_series <= end

    filtered = df.loc[mask].copy()
    return filtered


def build_required_station_files(
    stations_file: Path,
    source_dir: Path,
    output_dir: Path,
    start_date: str | None = None,
    end_date: str | None = None,
) -> None:
    if not stations_file.exists():
        raise FileNotFoundError(f"Stations file not found: {stations_file}")
    if not source_dir.exists():
        raise FileNotFoundError(f"Source folder not found: {source_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    # We still use stations_by_folder.xlsx to define which groups exist,
    # but station selection comes from Final_Mapped.xlsx.
    station_map = _read_station_list_by_group(stations_file)
    mapping_by_group = _read_final_mapping_by_group(FINAL_MAPPING_FILE)

    missing_records: list[dict[str, str]] = []

    for group_name, stations in station_map.items():
        source_file = source_dir / f"{group_name}.xlsx"
        output_file = output_dir / f"{group_name}.xlsx"

        if not source_file.exists():
            for station in stations:
                missing_records.append(
                    {
                        "Group": group_name,
                        "Station Name": station,
                        "Reason": f"Source workbook not found: {source_file.name}",
                    }
                )
            continue

        source_xls = pd.ExcelFile(source_file)
        exact_lookup = _build_exact_lookup(source_xls.sheet_names)
        no_bracket_lookup = _build_no_bracket_lookup(source_xls.sheet_names)
        available_sheets_norm = {_normalize_station_name(s): s for s in source_xls.sheet_names}

        matched_count = 0
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            group_map = mapping_by_group.get(group_name, {})
            if not group_map:
                pd.DataFrame({"Info": [f"No mappings found for group: {group_name}"]}).to_excel(
                    writer, sheet_name="NoMappings", index=False
                )
                continue

            for station, mapped_sheet_name in group_map.items():
                mapped_sheet = available_sheets_norm.get(_normalize_station_name(mapped_sheet_name))
                if not mapped_sheet:
                    missing_records.append(
                        {
                            "Group": group_name,
                            "Station Name": station,
                            "Reason": f"Mapped sheet not found in {source_file.name}: {mapped_sheet_name}",
                        }
                    )
                    continue

                # Station sheets in source workbooks use the second row as header.
                station_df = pd.read_excel(source_file, sheet_name=mapped_sheet, header=1)
                station_df = _filter_by_date(station_df, start_date=start_date, end_date=end_date)
                station_df.to_excel(writer, sheet_name=mapped_sheet[:31], index=False)
                matched_count += 1

            if matched_count == 0:
                pd.DataFrame({"Info": ["No matching station sheets found"]}).to_excel(
                    writer, sheet_name="NoData", index=False
                )

    if missing_records:
        missing_df = pd.DataFrame(missing_records)
        missing_path = output_dir / "missing_stations_report.xlsx"
        missing_df.to_excel(missing_path, index=False)
        print(f"Missing stations report created: {missing_path}")
    else:
        print("No missing stations. All listed stations were found as sheets.")

    print(f"Required station files created in: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create per-group station Excel files from stations_by_folder.xlsx."
    )
    parser.add_argument(
        "--start-date",
        default=None,
        help="Optional start date (YYYY-MM-DD). Applied to Date column if present.",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="Optional end date (YYYY-MM-DD). Applied to Date column if present.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_required_station_files(
        stations_file=STATIONS_FILE,
        source_dir=SOURCE_DIR,
        output_dir=OUTPUT_DIR,
        start_date=args.start_date,
        end_date=args.end_date,
    )
