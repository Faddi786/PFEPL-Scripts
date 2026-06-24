"""
Prepare and evaluate a 20-point masked validation for gapIt output.

Usage:
  1) Prepare masked input + ground truth:
     python validate_20_points.py prepare --input "A.xlsx" --points 20 --seed 42

  2) Run gapIt flow on the prepared file and export ARFF.

  3) Evaluate exported ARFF against ground truth:
     python validate_20_points.py evaluate --arff "filled_output.arff"
"""

import argparse
import math
import re
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_INPUT = INPUT_DIR / "sample_gauges.xlsx"
DEFAULT_MASKED = OUTPUT_DIR / "validation_masked.xlsx"
DEFAULT_GROUND_TRUTH = OUTPUT_DIR / "validation_points_20.csv"
DEFAULT_REPORT = OUTPUT_DIR / "validation_report_20.csv"


def _find_discharge_col(df: pd.DataFrame) -> str:
    for c in ("discharge (m3/sec)", "discharge (m3 sec)"):
        if c in df.columns:
            return c
    for c in df.columns:
        if "discharge" in c.lower():
            return c
    raise ValueError("Discharge column not found.")


def _read_arff(path: Path) -> pd.DataFrame:
    lines = path.read_text(encoding="utf-8").splitlines()
    attrs = []
    data_rows = []
    in_data = False

    for raw in lines:
        line = raw.strip()
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

    n_attrs = len(attrs)
    records = []
    for row in data_rows:
        parts = [p.strip() for p in row.split(",")]
        if len(parts) < 2:
            continue
        values = parts[:n_attrs]
        ts = parts[-1] if len(parts) > n_attrs else ""
        try:
            dd, mm, yyyy = ts.split("-")[:3]
            date = pd.to_datetime(f"{yyyy}-{mm}-{dd}", errors="coerce")
        except Exception:
            date = pd.to_datetime(ts, errors="coerce")
        rec = {"date": date}
        for i, attr in enumerate(attrs):
            station = attr[:-4] if attr.endswith("_val") else attr
            raw_val = values[i] if i < len(values) else "?"
            if raw_val in ("?", ""):
                rec[station] = None
            else:
                try:
                    rec[station] = float(raw_val)
                except ValueError:
                    rec[station] = None
        records.append(rec)
    df = pd.DataFrame(records)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def prepare(input_path: Path, points: int, seed: int, output_xlsx: Path, truth_csv: Path) -> None:
    df = pd.read_excel(input_path, sheet_name=0)
    date_col = "date" if "date" in df.columns else df.columns[0]
    disc_col = _find_discharge_col(df)

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df[disc_col] = pd.to_numeric(df[disc_col], errors="coerce")
    df = df.dropna(subset=[date_col, disc_col]).copy()

    # Keep only non-zero candidates for masking (zero means missing in current pipeline).
    candidates = df.index[df[disc_col] != 0].tolist()
    if len(candidates) < points:
        raise ValueError(
            f"Only {len(candidates)} non-zero points available, cannot pick {points} points."
        )

    sample_idx = (
        df.loc[candidates, [date_col, disc_col]]
        .sample(n=points, random_state=seed)
        .index
        .tolist()
    )

    gt = df.loc[sample_idx, [date_col, disc_col]].copy()
    gt = gt.sort_values(date_col).rename(
        columns={date_col: "date", disc_col: "actual_discharge"}
    )
    gt["date"] = gt["date"].dt.normalize()

    prepared = df.copy()
    prepared.loc[sample_idx, disc_col] = 0.0
    prepared = prepared.sort_values(date_col)
    prepared[date_col] = prepared[date_col].dt.normalize()

    output_xlsx = output_xlsx.resolve()
    truth_csv = truth_csv.resolve()
    prepared.to_excel(output_xlsx, index=False)
    gt.to_csv(truth_csv, index=False)

    print(f"Prepared file: {output_xlsx}")
    print(f"Ground truth: {truth_csv}")
    print(f"Masked points: {len(gt)}")


def evaluate(arff_path: Path, truth_csv: Path, report_csv: Path) -> None:
    pred = _read_arff(arff_path)
    if pred.empty:
        raise ValueError("ARFF output has no readable rows.")

    station_cols = [c for c in pred.columns if c != "date"]
    if not station_cols:
        raise ValueError("No station column found in ARFF.")
    station_col = station_cols[0]

    pred = pred[["date", station_col]].rename(columns={station_col: "predicted_discharge"})
    pred["date"] = pd.to_datetime(pred["date"], errors="coerce").dt.normalize()
    pred["predicted_discharge"] = pd.to_numeric(pred["predicted_discharge"], errors="coerce")

    gt = pd.read_csv(truth_csv)
    gt["date"] = pd.to_datetime(gt["date"], errors="coerce").dt.normalize()
    gt["actual_discharge"] = pd.to_numeric(gt["actual_discharge"], errors="coerce")

    merged = gt.merge(pred, on="date", how="left")
    merged["error"] = merged["predicted_discharge"] - merged["actual_discharge"]
    merged["abs_error"] = merged["error"].abs()
    merged["sq_error"] = merged["error"] ** 2

    valid = merged.dropna(subset=["actual_discharge", "predicted_discharge"]).copy()
    if valid.empty:
        raise ValueError("No overlapping date points found between ground truth and ARFF output.")

    mae = valid["abs_error"].mean()
    rmse = math.sqrt(valid["sq_error"].mean())

    report_csv = report_csv.resolve()
    merged.sort_values("date").to_csv(report_csv, index=False)

    print(f"Validation points requested: {len(merged)}")
    print(f"Validation points matched:   {len(valid)}")
    print(f"MAE:  {mae:.6f}")
    print(f"RMSE: {rmse:.6f}")
    print(f"Detailed report: {report_csv}")


def main() -> None:
    parser = argparse.ArgumentParser(description="20-point validation helper for gapIt output.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_prepare = sub.add_parser("prepare", help="Create masked test file and ground-truth points.")
    p_prepare.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p_prepare.add_argument("--points", type=int, default=20)
    p_prepare.add_argument("--seed", type=int, default=42)
    p_prepare.add_argument("--output-xlsx", type=Path, default=DEFAULT_MASKED)
    p_prepare.add_argument("--truth-csv", type=Path, default=DEFAULT_GROUND_TRUTH)

    p_eval = sub.add_parser("evaluate", help="Score exported ARFF against ground truth.")
    p_eval.add_argument("--arff", type=Path, default=SCRIPT_DIR / "filled_output.arff")
    p_eval.add_argument("--truth-csv", type=Path, default=DEFAULT_GROUND_TRUTH)
    p_eval.add_argument("--report-csv", type=Path, default=DEFAULT_REPORT)

    args = parser.parse_args()

    if args.cmd == "prepare":
        prepare(args.input, args.points, args.seed, args.output_xlsx, args.truth_csv)
    elif args.cmd == "evaluate":
        evaluate(args.arff, args.truth_csv, args.report_csv)


if __name__ == "__main__":
    main()

