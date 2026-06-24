"""
Use gapIt to fill missing discharge: you give your Excel path, we run gapIt and get Excel out.

  python fill_with_gapit.py "C:\path\to\your\data.xlsx"

What happens:
  1. Your Excel is converted to gapIt format (zeros/empty = missing) and gapIt is started.
  2. In gapIt: use the app to fill gaps, then Export → Export ARFF. Save as "filled_output.arff"
     in this folder (or remember the path).
  3. Back in the terminal: press Enter. The script converts gapIt's output to Excel.

To only convert an already-exported ARFF to Excel:
  python fill_with_gapit.py --to-excel "C:\path\to\filled_output.arff"

Limitation: gapIt has no batch mode. You must do the "fill" and "Export" once in the gapIt window.
"""
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
GAPIT_DIR = SCRIPT_DIR / "gapit"
OUTPUT_DIR = GAPIT_DIR / "ulhas_data"
FILLED_ARFF_DEFAULT = SCRIPT_DIR / "output" / "filled_output.arff"
OUTPUT_EXCEL = SCRIPT_DIR / "output" / "ulhas_discharge_filled.xlsx"
DISC_COLS = ["discharge (m3/sec)", "discharge (m3 sec)"]


def detect_stations_and_convert(excel_path: Path):
    """Convert Excel to ARFF; auto-detect sheet names (stations) and discharge column. Return station list or None."""
    if not excel_path.exists():
        print(f"Excel not found: {excel_path}")
        return None
    xl = pd.ExcelFile(excel_path)
    sheets = [s for s in xl.sheet_names if s.strip()]
    if not sheets:
        print("No sheets found in Excel.")
        return None

    all_dates = set()
    data_by_station = {}
    for sheet in sheets:
        df = pd.read_excel(excel_path, sheet_name=sheet)
        date_col = "date" if "date" in df.columns else df.columns[0]
        disc_col = None
        for c in DISC_COLS:
            if c in df.columns:
                disc_col = c
                break
        if disc_col is None:
            for c in df.columns:
                if "discharge" in c.lower():
                    disc_col = c
                    break
        if disc_col is None:
            continue
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
        df = df.dropna(subset=[date_col])
        data_by_station[sheet] = df.set_index(date_col)[disc_col]
        all_dates.update(data_by_station[sheet].index.tolist())

    if not data_by_station:
        print("No date/discharge columns found in any sheet.")
        return None

    stations = list(data_by_station.keys())
    all_dates = sorted(all_dates)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    arff_lines = ["@relation ulhas_gauges_discharge", ""]
    for s in stations:
        arff_lines.append(f"@attribute {s}_val numeric")
    arff_lines.append("@attribute timestamp date dd-MM-yyyy-HH:mm:ss")
    arff_lines.append("")
    arff_lines.append("@data")
    for d in all_dates:
        row = []
        for s in stations:
            if d in data_by_station[s].index:
                v = data_by_station[s].loc[d]
                if pd.isna(v) or (isinstance(v, (int, float)) and v == 0):
                    row.append("?")
                else:
                    row.append(f"{float(v):.6f}")
            else:
                row.append("?")
        ts = pd.Timestamp(d).strftime("%d-%m-%Y-00:00:00")
        row.append(ts)
        arff_lines.append(",".join(row))

    (OUTPUT_DIR / "all_valid_q_series_complete2.arff").write_text("\n".join(arff_lines), encoding="utf-8")

    coords_path = OUTPUT_DIR / "stations_coordinates_new.txt"
    with open(coords_path, "w") as f:
        f.write("STATIONS\tX_LUREF\tY_LUREF\n")
        for i, s in enumerate(stations):
            f.write(f"{s}\t{10000 + i * 5000}\t{70000 + i * 5000}\n")

    kdb_lines = [
        "@relation stream", "",
        f"@attribute serieName {{{','.join(s+'_val' for s in stations)}}}",
        "@attribute serieX numeric", "@attribute serieY numeric", "@attribute gapSize numeric",
        "@attribute gapPosition numeric", "@attribute season {Spring,Summer,Autumn,Winter}",
        "@attribute year numeric", "@attribute isDuringRising {false,true}",
        "@attribute flow {low,middle,high}", "@attribute hasDownstream {false,true}",
        "@attribute hasUpstream {false,true}",
        "@attribute algo {Interpolation,EM,REG,REPTREE,M5P,ZeroR,ANN,NEARESTNEIGHBOUR}",
        "@attribute useDiscretizedTime {false,true}", "@attribute useMostSimilar {false,true}",
        "@attribute useNearest {true,false}", "@attribute useDownstream {false,true}",
        "@attribute useUpstream {false,true}", "@attribute MAE numeric", "@attribute RMSE numeric",
        "@attribute RSR numeric", "@attribute PBIAS numeric", "@attribute NashSutcliffe numeric",
        "@attribute indexOfAgreement numeric", "@attribute wasTheBestSolution {false,true}", "", "@data",
    ]
    for s in stations:
        kdb_lines.append(f"{s}_val,10000,70000,2,50,Summer,2010,false,middle,false,false,Interpolation,false,false,true,false,false,0.1,0.1,0.5,0,0.8,0.9,false")
    (OUTPUT_DIR / "knowledgeDB20-discharge.arff").write_text("\n".join(kdb_lines), encoding="utf-8")

    return stations


def launch_gapit():
    run_bat = GAPIT_DIR / "run.bat"
    if not run_bat.exists():
        print(f"gapIt not found: {run_bat}")
        return False
    subprocess.Popen(
        ["cmd", "/c", "run.bat"],
        cwd=str(GAPIT_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    return True


def read_arff(path: Path) -> pd.DataFrame:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    attrs = []
    data_rows = []
    in_data = False
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
            if raw in ("?", "") or (isinstance(raw, str) and raw.strip() == ""):
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


def arff_to_excel(arff_path: Path):
    df = read_arff(arff_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    station_cols = [c for c in df.columns if c != "date"]
    output_path = _pick_output_path(OUTPUT_EXCEL)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for col in station_cols:
            name = (col.replace("_val", "") if col.endswith("_val") else col)[:31]
            sheet_df = pd.DataFrame({"date": df["date"], "discharge (m3/sec)": df[col].values})
            sheet_df["discharge (m3/sec)"] = _fill_series_with_edge_extrapolation(
                sheet_df["discharge (m3/sec)"]
            )
            sheet_df.to_excel(writer, sheet_name=name, index=False)
    print(f"Written: {output_path}")


def main():
    args = []
    excel_arg = None
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--to-excel" and i + 1 < len(sys.argv):
            excel_arg = sys.argv[i + 1]
            i += 2
            continue
        args.append(sys.argv[i])
        i += 1

    if excel_arg is not None:
        arff_path = Path(excel_arg)
        if not arff_path.exists():
            print(f"File not found: {arff_path}")
            sys.exit(1)
        arff_to_excel(arff_path)
        return

    excel_path = Path(args[0]) if args else SCRIPT_DIR / "ulhas_guages_filled_time_series (1).xlsx"
    print(f"Excel: {excel_path}")
    stations = detect_stations_and_convert(excel_path)
    if stations is None:
        sys.exit(1)
    print(f"Stations: {stations}")
    print("Starting gapIt...")
    if not launch_gapit():
        sys.exit(1)
    print("""
In gapIt (the system fills the gaps when you click):
  1. In the LEFT panel, expand "Missing values".
  2. Click "Fill short gaps by interpolation" — gapIt will fill all gaps (wait until it finishes).
  3. Expand "Export" and click "Export ARFF". Save as:  filled_output.arff
  4. Save in this folder:  """ + str(SCRIPT_DIR) + """

When you have saved that file, come back here and press Enter.
""")
    input("Press Enter when done... ")
    arff_path = FILLED_ARFF_DEFAULT
    if len(args) > 1:
        arff_path = Path(args[1])
    if not arff_path.exists():
        print(f"Not found: {arff_path}")
        print("Run:  python fill_with_gapit.py --to-excel path/to/your_export.arff")
        sys.exit(1)
    arff_to_excel(arff_path)
    print("Done. Open: " + str(OUTPUT_EXCEL))


if __name__ == "__main__":
    main()
