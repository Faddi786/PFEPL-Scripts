# gapIt gap-fill pipeline

**Pipeline** — multi-step workflow using the gapIt Java app for hydrology-grade discharge gap filling.

Scripts run in this order (or use `fill_with_gapit.py` as orchestrator):

| Step | Script / tool | Action |
|------|---------------|--------|
| 1 | `convert_to_gapit.py` | Excel → gapIt ARFF + station metadata in `gapit/ulhas_data/` |
| 2 | `gapit/run.bat` | Open gapIt GUI (requires Java JDK) |
| 3 | *(manual in gapIt)* | Missing values → Fill short gaps → Export ARFF |
| 4 | `gapit_to_excel.py` | ARFF → `output/ulhas_discharge_filled.xlsx` |

## Input
`input/ulhas_gauges.xlsx` (same format as `fill_auto.md`).

## Quick run (orchestrator)
```bash
cd hydrology/discharge-gap-fill
python fill_with_gapit.py input/ulhas_gauges.xlsx
```
Then complete steps 3–4 in gapIt; press Enter when ARFF is saved to `output/filled_output.arff`.

## Step-by-step
```bash
python convert_to_gapit.py
cd gapit && run.bat
# In gapIt: expand "Missing values" → "Fill short gaps by interpolation"
# Export → Export ARFF → save as ../output/filled_output.arff
cd ..
python gapit_to_excel.py output/filled_output.arff
```

## gapIt folder
`gapit/` is the third-party Java application (source, JAR, config). Only required for this pipeline — not for `fill_auto.py`.

## Output
`output/ulhas_discharge_filled.xlsx`

## Optional validation
See [validate.md](validate.md) after exporting from gapIt.
