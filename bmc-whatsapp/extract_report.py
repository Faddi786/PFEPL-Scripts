#Script to be used in google colab to avoid warnings and obtain results 

from google.colab import files
import re
import csv
import nltk
from nltk.corpus import words
from datetime import datetime
from pathlib import Path

nltk.download('words')

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Upload file from local system
print("Please upload your WhatsApp Chat .txt file:")
uploaded = files.upload()

# Automatically get the uploaded filename
file_name = list(uploaded.keys())[0]

# Read file content
with open(file_name, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# === CONFIGURATION ===
OUTPUT_FILE = str(OUTPUT_DIR / "report_extracted_data.csv")

FIELDS = [
    "Date", "Ward Name", "Team No.", "Team Name",
    "DGPS", "GIS", "Labour Provider", "Labour Count",
    "Manhole DGPS Surveyed", "Manhole GIS Surveyed", "Remarks"
]

ENGLISH_WORDS = set(words.words())

def extract_non_english_names(line):
    tokens = re.findall(r"\b[A-Z][a-z]+\b", line)
    return [t for t in tokens if t.lower() not in ENGLISH_WORDS]

def match_multiple(pattern, text):
    return [m.group(1).strip() for m in re.finditer(pattern, text, re.IGNORECASE)]

def clean_join(values):
    return ", ".join(sorted(set(values)))

def standardize_date(date_str):
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%d/%m/%Y")
        except:
            continue
    return date_str  # fallback if unrecognized

def extract_fields(section, base_date=""):
    results = []
    row_data = {field: "" for field in FIELDS}
    row_data["Date"] = standardize_date(base_date)

    # Split into blocks for each team
    team_blocks = re.split(r"(?=\bTeam\s*(?:No)?[:\-\s]*\d+\b)", section, flags=re.IGNORECASE)
    for block in team_blocks:
        data = row_data.copy()

        # Extract Team No.
        team_no_match = re.search(r"\bTeam\s*(?:No)?[:\-\s]*\s*(\d{1,3})\b", block, re.IGNORECASE)
        if team_no_match:
            data["Team No."] = team_no_match.group(1).strip()

        # Extract Team Name
        names = []
        for line in block.splitlines():
            if "Team" in line:
                names += extract_non_english_names(line)
        data["Team Name"] = clean_join(names)

        # Extract Ward Name (ensure uppercase)
        for line in block.splitlines():
            ward_match = re.search(r"\b(?:Ward\s*Name|Ward)\s*[:\-]?\s*([A-Z]{1,3}(?:/[A-Z]{1,3})?)\b", line, re.IGNORECASE)
            if ward_match:
                data["Ward Name"] = ward_match.group(1).upper().strip()
                break

        # DGPS Names
        for line in block.splitlines():
            if "DGPS" in line and re.match(r"^[A-Za-z:\-\s]+$", line):
                if not re.search(r"Remarks|Note", line, re.IGNORECASE):
                    names = extract_non_english_names(line)
                    if names:
                        data["DGPS"] += clean_join(names)

        # GIS Names
        for line in block.splitlines():
            if "GIS" in line and re.match(r"^[A-Za-z:\-\s]+$", line):
                if not re.search(r"Remarks|Note", line, re.IGNORECASE):
                    names = extract_non_english_names(line)
                    if names:
                        data["GIS"] += clean_join(names)

        # Labour Info
        for line in block.splitlines():
            if re.search(r"Labour|Labor|Labours", line, re.IGNORECASE):
                if re.match(r"^[A-Za-z:\-\s]+$", line):
                    if not re.search(r"Remarks|Note", line, re.IGNORECASE):
                        names = extract_non_english_names(line)
                        if names:
                            data["Labour Provider"] += clean_join(names)
                count_match = re.search(r"\b(\d{1,3})\b", line)
                if count_match:
                    data["Labour Count"] = count_match.group(1)

        # Manhole Counts
        for line in block.splitlines():
            gis_match = re.search(r"Manhole\s+GIS\s+(?:surveyed|count)[\s:\-]*([\d]+)", line, re.IGNORECASE)
            dgps_match = re.search(r"Manhole\s+DGPS\s+(?:surveyed|count)[\s:\-]*([\d]+)", line, re.IGNORECASE)
            if gis_match:
                data["Manhole GIS Surveyed"] = gis_match.group(1).strip()
            if dgps_match:
                data["Manhole DGPS Surveyed"] = dgps_match.group(1).strip()

        # Remarks
        for line in block.splitlines():
            if re.search(r"Remarks|Note", line, re.IGNORECASE):
                rem = re.split(r"Remarks if any[:\-]?|Remarks[:\-]?|Note[:\-]?", line, flags=re.IGNORECASE)
                if rem and len(rem) > 1:
                    if not re.search(r"Labour|Labor|Labours", rem[1], re.IGNORECASE):
                        data["Remarks"] += rem[1].strip()

        # === Final Filters ===
        dgps_count = int(data["Manhole DGPS Surveyed"]) if data["Manhole DGPS Surveyed"].isdigit() else 0
        gis_count = int(data["Manhole GIS Surveyed"]) if data["Manhole GIS Surveyed"].isdigit() else 0

        if dgps_count > 200 or gis_count > 200:
            continue  # Skip this row

        # Count filled fields (excluding empty strings)
        filled_fields = sum(1 for v in data.values() if v.strip())
        if filled_fields <= 3:
            continue  # Skip this row

        results.append(data)
    return results

# === READ FILE ===
with open(file_name, "r", encoding="utf-8") as f:
    content = f.read()

# Split by date occurrences
sections = re.split(r"(?=\b\d{2}[/\-.]\d{2}[/\-.]\d{4}\b)", content)

all_rows = []
for section in sections:
    if not section.strip():
        continue

    base_date_match = re.search(r"\b\d{2}[/\-.]\d{2}[/\-.]\d{4}\b", section)
    base_date = base_date_match.group(0) if base_date_match else ""

    extracted = extract_fields(section, base_date)
    all_rows.extend(extracted)

# === WRITE TO CSV ===
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(all_rows)

print(f"✅ Cleaned & filtered data saved to '{OUTPUT_FILE}'")

# Download the output CSV
files.download(OUTPUT_FILE)