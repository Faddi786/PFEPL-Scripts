# fill_form.py

**Standalone** — fills a tender submission template from a cleaned tender list.

## Input
Place in `input/`:
- `cleaned_tenderlist.xlsx` — source tender data
- `tender_form_template.xlsx` — blank form template

## Run
```bash
cd reports/tender-form
python fill_form.py
```

## Output
`output/tender_form_filled.xlsx` (or `tender_form_filled_alt.xlsx` if the main file is open in Excel).

## Notes
- Only fills existing rows in the template (no extra rows added)
- Extra cleaned rows beyond the template capacity are skipped

## Dependencies
`pandas`, `openpyxl`
