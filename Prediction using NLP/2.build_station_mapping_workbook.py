from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
STATIONS_FILE = ROOT_DIR / "Excel Files" / "stations_by_folder.xlsx"
SOURCE_DIR = ROOT_DIR / "Excel Files" / "Excels with required date range"
MAPPING_FILE = ROOT_DIR / "Excel Files" / "station_mapping.xlsx"


def _normalize_station_name(name: str) -> str:
    return " ".join(str(name).strip().split()).casefold()


def _strip_parentheses_text(s: str) -> str:
    return re.sub(r"\([^)]*\)", "", s).strip()


def _normalize_punct_insensitive(name: str) -> str:
    # Remove everything except letters/digits; helps dot/underscore/hyphen differences.
    return re.sub(r"[^a-z0-9]+", "", _normalize_station_name(name))


def _read_station_list_by_group(stations_file: Path) -> dict[str, list[str]]:
    station_map: dict[str, list[str]] = {}
    xls = pd.ExcelFile(stations_file)
    for sheet in xls.sheet_names:
        df = pd.read_excel(stations_file, sheet_name=sheet)
        if "Station Name" not in df.columns:
            station_map[sheet] = []
            continue
        names = df["Station Name"].dropna().astype(str).map(lambda x: x.strip())
        names = names[names != ""]
        station_map[sheet] = sorted(set(names.tolist()), key=lambda x: x.casefold())
    return station_map


def _station_sheets_in_source(group_name: str, source_dir: Path) -> list[str]:
    source_file = source_dir / f"{group_name}.xlsx"
    if not source_file.exists():
        return []
    xls = pd.ExcelFile(source_file)
    return [s for s in xls.sheet_names if _normalize_station_name(s) != "overview"]


def _propose_match(station: str, source_sheets: list[str]) -> str:
    """
    Return a proposed sheet name for this station or "".
    Matching order:
      1) exact (case/space normalized)
      2) remove bracketed text on both sides
      3) punctuation-insensitive (dots/underscores/hyphens etc.)
    """
    if not source_sheets:
        return ""

    # Build lookups for deterministic single-match proposals.
    exact_lookup: dict[str, list[str]] = {}
    nobr_lookup: dict[str, list[str]] = {}
    punct_lookup: dict[str, list[str]] = {}

    for sheet in source_sheets:
        exact_lookup.setdefault(_normalize_station_name(sheet), []).append(sheet)
        nobr_lookup.setdefault(_normalize_station_name(_strip_parentheses_text(sheet)), []).append(sheet)
        punct_lookup.setdefault(_normalize_punct_insensitive(sheet), []).append(sheet)

    # 1) exact
    key = _normalize_station_name(station)
    matches = sorted(set(exact_lookup.get(key, [])), key=lambda x: x.casefold())
    if len(matches) == 1:
        return matches[0]

    # 2) without bracketed text
    key2 = _normalize_station_name(_strip_parentheses_text(station))
    matches2 = sorted(set(nobr_lookup.get(key2, [])), key=lambda x: x.casefold())
    if len(matches2) == 1:
        return matches2[0]

    # 3) punctuation-insensitive
    key3 = _normalize_punct_insensitive(station)
    matches3 = sorted(set(punct_lookup.get(key3, [])), key=lambda x: x.casefold())
    if len(matches3) == 1:
        return matches3[0]

    return ""


def build_mapping_workbook(
    stations_file: Path = STATIONS_FILE,
    source_dir: Path = SOURCE_DIR,
    mapping_file: Path = MAPPING_FILE,
) -> None:
    if not stations_file.exists():
        raise FileNotFoundError(f"Stations file not found: {stations_file}")
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    station_map = _read_station_list_by_group(stations_file)
    mapping_file.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(mapping_file, engine="openpyxl") as writer:
        for group_name, stations in station_map.items():
            source_sheets = _station_sheets_in_source(group_name, source_dir)
            rows: list[dict[str, str]] = []
            proposed_used: set[str] = set()
            for st in stations:
                proposed = _propose_match(st, source_sheets)
                if proposed:
                    proposed_used.add(_normalize_station_name(proposed))
                rows.append(
                    {
                        "Shapefile Station Name": st,
                        "Excel Station Sheet Name": proposed,
                    }
                )

            remaining = sorted(
                [s for s in source_sheets if _normalize_station_name(s) not in proposed_used],
                key=lambda x: x.casefold(),
            )

            # Put remaining sheet names into Column E (i.e. 5th column).
            # We keep Columns C and D empty as visual spacing for manual mapping edits.
            max_len = max(len(rows), len(remaining))
            df_left = pd.DataFrame(rows)
            df_left = df_left.reindex(range(max_len))

            df_out = pd.DataFrame(
                {
                    "Shapefile Station Name": df_left["Shapefile Station Name"],
                    "Excel Station Sheet Name": df_left["Excel Station Sheet Name"],
                    "": [""] * max_len,   # Column C spacer
                    "  ": [""] * max_len,  # Column D spacer
                    "Remaining Excel Sheet Names": remaining + [""] * (max_len - len(remaining)),
                }
            )

            df_out.to_excel(writer, sheet_name=group_name[:31], index=False)

    print(f"Mapping workbook created: {mapping_file}")


if __name__ == "__main__":
    build_mapping_workbook()

