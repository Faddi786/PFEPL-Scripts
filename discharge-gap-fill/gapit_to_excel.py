"""
Convert gapIt-exported ARFF (or CSV) back to Excel with discharge (m3/sec) per station.
Run after you have filled gaps in gapIt and exported: File/Export → Export ARFF (or CSV).

Usage:
  python gapit_output_to_excel.py [path_to_exported.arff_or_csv]

If no path is given, looks for filled_output.arff in this folder (save your gapIt export there).
Output: ulhas_discharge_filled.xlsx (one sheet per station: date, discharge (m3/sec))
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_INPUT = OUTPUT_DIR / "filled_output.arff"
OUTPUT_EXCEL = OUTPUT_DIR / "ulhas_discharge_filled.xlsx"


def read_arff(path: Path) -> pd.DataFrame:
    """Parse ARFF into a DataFrame. Expects attributes like titwala_val, kaman_val, ..., timestamp."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.splitlines()
    attrs = []  # attribute names in order (excluding timestamp)
    in_data = False
    data_rows = []
    for line in lines:
        line = line.strip()
        if line.lower().startswith("@attribute"):
            m = re.match(r"@attribute\s+(\S+)\s+", line, re.I)
            if m:
                name = m.group(1).strip("'\"")
                if name.lower() != "timestamp":
                    attrs.append(name)
        if line.lower() == "@data":
            in_data = True
            continue
        if in_data and line and not line.startswith("%"):
            data_rows.append(line)
    # Parse data rows: comma-separated, last column is timestamp dd-MM-yyyy-HH:mm:ss
    records = []
    n_attrs = len(attrs)
    for row in data_rows:
        parts = [p.strip() for p in row.split(",")]
        if len(parts) < 2:
            continue
        ts = parts[-1] if len(parts) > n_attrs else ""
        values = parts[:n_attrs]
        try:
            day, month, year = ts.split("-")[:3]
            date = f"{year}-{month}-{day}"
        except Exception:
            date = ts
        rec = {"date": date}
        for i, attr in enumerate(attrs):
            station = attr.replace("_val", "") if attr.endswith("_val") else attr
            raw = values[i] if i < len(values) else "?"
            if raw == "?" or raw == "" or (isinstance(raw, str) and raw.strip() == ""):
                rec[station] = None
            else:
                try:
                    rec[station] = float(raw)
                except ValueError:
                    rec[station] = None
        records.append(rec)
    return pd.DataFrame(records)


def _fill_series_with_edge_extrapolation(series: pd.Series) -> pd.Series:
    """Fill internal gaps by interpolation and edge gaps by linear extrapolation."""
    s = pd.to_numeric(series, errors="coerce").astype(float).copy()
    s = s.interpolate(method="linear", limit_area="inside")
    vals = s.to_numpy(dtype=float)
    idx = np.arange(len(vals))
    mask = ~np.isnan(vals)

    if mask.sum() == 0:
        return pd.Series(np.zeros(len(vals), dtype=float), index=s.index)
    if mask.sum() == 1:
        only_val = vals[mask][0]
        vals[np.isnan(vals)] = only_val
        return pd.Series(vals, index=s.index)

    first = idx[mask][0]
    last = idx[mask][-1]
    fit_n = min(5, int(mask.sum()))
    fit_start_idx = idx[mask][:fit_n]
    fit_end_idx = idx[mask][-fit_n:]

    if first > 0:
        a0, b0 = np.polyfit(fit_start_idx.astype(float), vals[fit_start_idx], 1)
        for i in range(first - 1, -1, -1):
            vals[i] = a0 * i + b0

    if last < len(vals) - 1:
        a1, b1 = np.polyfit(fit_end_idx.astype(float), vals[fit_end_idx], 1)
        for i in range(last + 1, len(vals)):
            vals[i] = a1 * i + b1

    out = pd.Series(vals, index=s.index)
    out = out.interpolate(method="linear", limit_direction="both").ffill().bfill()
    return out


def _pick_output_path(path: Path) -> Path:
    try:
        with open(path, "ab"):
            pass
        return path
    except PermissionError:
        return path.with_name(f"{path.stem}_new{path.suffix}")


def main():
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    else:
        input_path = DEFAULT_INPUT

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        print("Usage: python gapit_output_to_excel.py [path_to_exported.arff_or_csv]")
        print("After filling gaps in gapIt, use Export → Export ARFF and save as filled_output.arff here,")
        print("or pass the path to your exported file.")
        sys.exit(1)

    if input_path.suffix.lower() == ".csv":
        df_wide = pd.read_csv(input_path)
        # CSV from Weka usually has columns like titwala_val, ..., timestamp
        # Normalize date column
        if "timestamp" in df_wide.columns:
            ts = df_wide["timestamp"]
            if ts.dtype == object or str(ts.dtype).startswith("str"):
                df_wide["date"] = pd.to_datetime(ts, format="%d-%m-%Y-%H:%M:%S", errors="coerce")
            else:
                df_wide["date"] = pd.to_datetime(ts, errors="coerce")
        else:
            df_wide["date"] = pd.to_datetime(df_wide.iloc[:, -1], errors="coerce")
    else:
        df_wide = read_arff(input_path)
        df_wide["date"] = pd.to_datetime(df_wide["date"], errors="coerce")

    df_wide = df_wide.dropna(subset=["date"]).sort_values("date")

    # Build one sheet per station: date, discharge (m3/sec)
    station_cols = [c for c in df_wide.columns if c not in ("date", "timestamp") and ("_val" in c or c in ["titwala", "kaman", "pise", "naldhe", "badlapur"])]
    if not station_cols:
        station_cols = [c for c in df_wide.columns if c != "date" and c != "timestamp"]

    output_path = _pick_output_path(OUTPUT_EXCEL)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for col in station_cols:
            name = col.replace("_val", "") if col.endswith("_val") else col
            sheet_df = pd.DataFrame({
                "date": df_wide["date"],
                "discharge (m3/sec)": df_wide[col].values,
            })
            sheet_df["discharge (m3/sec)"] = _fill_series_with_edge_extrapolation(
                sheet_df["discharge (m3/sec)"]
            )
            sheet_df.to_excel(writer, sheet_name=name[:31], index=False)

    print(f"Wrote {output_path} with sheets: {[s.replace('_val','') for s in station_cols]}")
    print("Columns per sheet: date, discharge (m3/sec)")


if __name__ == "__main__":
    main()
