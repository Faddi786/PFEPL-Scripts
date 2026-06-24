# build_summary.py

**Standalone** — aggregates IT team daily progress report (DPR) entries per person across dated Excel sheets.

## Input
`input/it_team_dpr.xlsx` — one sheet per date; columns: Name, project name, task description, tomorrow task.

## Run
```bash
cd reports/it-team-dpr
python build_summary.py
```

## Output
`output/it_team_dpr_summary.xlsx` — per-person summary of tasks and projects over time.

## Dependencies
`openpyxl`
