# extract_report.py

**Standalone** — parses BMC field survey WhatsApp chat exports into structured CSV.

**Runs in Google Colab** (uses `google.colab.files.upload()`).

## Input
Upload a WhatsApp chat `.txt` export when prompted. Sample files can be kept in `input/` for reference.

## Run (Colab)
1. Upload `extract_report.py` to a Colab notebook
2. Run the script
3. Upload your WhatsApp `.txt` when asked

## Output
`output/report_extracted_data.csv`

## Fields extracted
Date, Ward Name, Team No., Team Name, DGPS, GIS, Labour Provider, Labour Count, Manhole DGPS Surveyed, Manhole GIS Surveyed, Remarks.

## Dependencies
`nltk`, `google.colab`
