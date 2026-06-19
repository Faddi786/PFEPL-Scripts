from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
REQUIRED_DIR = ROOT_DIR / "Required Station Info"


def _pick_date_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if str(col).strip().casefold() == "date":
            return col
    # fallback: first datetime-like column
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None


def _pick_rainfall_column(df: pd.DataFrame) -> str | None:
    # preferred exact name
    for col in df.columns:
        if str(col).strip().casefold() == "rainfall value":
            return col

    # heuristic: column containing "rain"
    for col in df.columns:
        if "rain" in str(col).casefold():
            return col

    # fallback: if there are exactly 2 columns and one is Date, pick the other
    date_col = _pick_date_column(df)
    if date_col and len(df.columns) == 2:
        other = [c for c in df.columns if c != date_col]
        if other:
            return other[0]
    return None


def _sheet_summary(df: pd.DataFrame) -> dict[str, int]:
    date_col = _pick_date_column(df)
    rain_col = _pick_rainfall_column(df)

    if not date_col or not rain_col:
        return {
            "Total Number of rows With Dates": 0,
            "Number of cells that a rainfall value for the dates": 0,
            "Number of empty cells, in the rainfall value column": 0,
            "Number of cells that have zero as the rainfall value": 0,
        }

    dates = pd.to_datetime(df[date_col], errors="coerce")
    date_mask = dates.notna()

    rain = df.loc[date_mask, rain_col]
    rain_num = pd.to_numeric(rain, errors="coerce")

    total_rows_with_dates = int(date_mask.sum())
    filled_rain = int(rain.notna().sum())
    empty_rain = int(rain.isna().sum())
    zero_rain = int((rain_num == 0).sum())

    return {
        "Total Number of rows With Dates": total_rows_with_dates,
        "Number of cells that a rainfall value for the dates": filled_rain,
        "Number of empty cells, in the rainfall value column": empty_rain,
        "Number of cells that have zero as the rainfall value": zero_rain,
    }


def add_summary_sheet_to_workbook(path: Path) -> None:
    xls = pd.ExcelFile(path)
    sheet_names = [s for s in xls.sheet_names if s.strip().casefold() != "summary"]

    rows: list[dict[str, object]] = []
    for s in sheet_names:
        df = pd.read_excel(path, sheet_name=s)
        stats = _sheet_summary(df)
        rows.append({"Sheet Names": s, **stats})

    summary_df = pd.DataFrame(rows)

    with pd.ExcelWriter(path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)


def main() -> None:
    if not REQUIRED_DIR.exists():
        raise FileNotFoundError(f"Folder not found: {REQUIRED_DIR}")

    files = sorted(REQUIRED_DIR.glob("*.xlsx"))
    if not files:
        raise FileNotFoundError(f"No .xlsx files found in: {REQUIRED_DIR}")

    for f in files:
        add_summary_sheet_to_workbook(f)
        print(f"Updated Summary sheet: {f.name}")


if __name__ == "__main__":
    main()

