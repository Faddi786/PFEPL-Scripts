# export_report.py

**Standalone** — builds a formatted Excel subbasin report from Thiessen polygon area data.

## Input
`input/theissen_polygons.xlsx` — columns: `name_1` (subbasin), `Name` (station), `Shape_Area`.

## Run
```bash
cd reports/subbasin
python export_report.py
```

## Output
`output/subbasin_report.xlsx` — styled report with subbasin name, station name, areas, merged cells per subbasin group.

## Dependencies
`pandas`, `openpyxl`
