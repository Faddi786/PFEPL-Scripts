# fill_auto.py

**Standalone** — fills missing and zero discharge values using Python interpolation. No gapIt, no manual steps.

## Input
`input/ulhas_gauges.xlsx` — one sheet per station (`titwala`, `kaman`, `pise`, `naldhe`, `badlapur`), columns: `date`, `discharge (m3/sec)`.

Or pass any Excel path:
```bash
python fill_auto.py "path/to/your.xlsx"
```

## Run
```bash
cd hydrology/discharge-gap-fill
python fill_auto.py
```
Or double-click `run_auto.bat`.

## Output
`output/ulhas_discharge_filled.xlsx` — one sheet per station with filled discharge series.

## When to use
Quick, fully automatic gap fill. For donor-station / hydrology-grade infilling, use the [gapIt pipeline](GAPIT_PIPELINE.md) instead.
