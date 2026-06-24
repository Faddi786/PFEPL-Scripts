# validate.py

**Standalone** — optional quality check for gapIt gap-filling accuracy using masked test points.

## Step 1 — Prepare masked data
```bash
cd hydrology/discharge-gap-fill
python validate.py prepare --input input/sample_gauges.xlsx --points 20 --seed 42
```
Creates:
- `output/validation_masked.xlsx` (gaps injected)
- `output/validation_points_20.csv` (ground truth)

## Step 2 — Fill with gapIt
Run the [gapIt pipeline](GAPIT_PIPELINE.md) on the masked file and export ARFF to `output/filled_output.arff`.

## Step 3 — Evaluate
```bash
python validate.py evaluate --arff output/filled_output.arff
```
Creates `output/validation_report_20.csv` with error metrics per point.

## When to use
Before trusting gapIt results on production data — measures how well infilled values match known values at 20 randomly masked locations.
