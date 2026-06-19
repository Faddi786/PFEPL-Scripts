# Web Scrapping — Rainfall Data Pipeline — User Guide

## Overview

Three-step pipeline to scrape Maharashtra rainfall data from the MahaRain website, format it circle-wise, and produce summation tables.

```
Step-1: scrape_rain_data.py
    ↓
Step-2: CircleWise_Transformer.py
    ↓
Step-3: table_with_summation_values.py  (+ optional transposed variant)
```

---

## Prerequisites

| Step | Requirements |
|------|-------------|
| Step 1 | `selenium`, `pandas`, `openpyxl`, **Google Chrome** + ChromeDriver |
| Step 2–3 | `pandas`, `openpyxl` |

```powershell
pip install selenium pandas openpyxl
```

ChromeDriver must match your Chrome version (Selenium 4+ can auto-manage in many setups).

---

## Step 1 — Web Scraping (`Step-1-Web_Scrapping\scrape_rain_data.py`)

### Overview

Scrapes daily circle-wise rainfall from https://maharain.maharashtra.gov.in for configured districts and years.

### Configuration (in script)

- `target_districts`: `['Thane', 'Palghar', 'Nashik', 'Raigadh', 'Pune']`
- `base_output_dir`: `CircleWise_DailyRain_Data_2014`

### How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Web Scrapping\Step-1-Web_Scrapping"
python scrape_rain_data.py
```

### Expected Output

```
CircleWise_DailyRain_Data_2014\
  Thane\
    2014_06.xlsx
    2014_07.xlsx
  Palghar\
    ...
```

**Sample console:**

```
✓ Browser started
✓ Created base output directory: CircleWise_DailyRain_Data_2014
Processing: Thane, Year 2014, Month June
  ✓ Selected 'Thane'
  ✓ Data saved: CircleWise_DailyRain_Data_2014\Thane\2014_06.xlsx
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| ChromeDriver mismatch | Browser/driver version differ | Update Chrome and driver |
| Dropdown selection failed | Website layout changed | Inspect page IDs; update selectors |
| Timeout | Slow network | Increase wait times in script |

---

## Step 2 — Circle-Wise Formatting (`Step-2-Circle-Wise-Formatting\CircleWise_Transformer.py`)

### Overview

Processes raw scraped Excel files into standardized circle-wise formatted workbooks.

### How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Web Scrapping\Step-2-Circle-Wise-Formatting"
python CircleWise_Transformer.py
```

Edit input/output paths at the top of the script to point to Step 1 output.

### Expected Output

Formatted Excel files ready for aggregation (paths configured in script).

---

## Step 3 — Summation Tables (`Step-3-Sum-Of-Years-Circle-Wise\`)

### Scripts

| Script | Output |
|--------|--------|
| `table_with_summation_values.py` | Standard summation table |
| `table_with_summation_values_transposed_table.py` | Transposed layout variant |

### How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Web Scrapping\Step-3-Sum-Of-Years-Circle-Wise"
python table_with_summation_values.py
```

Or for transposed output:

```powershell
python table_with_summation_values_transposed_table.py
```

---

## Full Workflow Checklist

1. Install Chrome + Selenium dependencies
2. Run Step 1 — wait for all districts/months to scrape
3. Configure Step 2 paths → run formatting
4. Run Step 3 summation (choose standard or transposed)
5. Verify output Excel totals against source data

---

## Notes

- Step 1 requires an active internet connection and the MahaRain website to be accessible.
- Scraping may take significant time for multiple districts × years × months.
- Website structure changes may require script updates to dropdown selectors.
