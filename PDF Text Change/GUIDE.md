# PDF Text Change — User Guide

## Overview

`PDF_Text_ID_Replacer.py` finds and replaces text strings throughout a PDF document — including standalone keywords, partial phrases, multi-line table cells, and filenames. It redacts the old text and re-inserts the replacement using matched fonts for a clean result.

Default use case: replace an ID like `DB_GM5505L` with `DB_GM5505L_2`.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.8+ |
| Packages | `PyMuPDF` (`pip install pymupdf`) |
| Fonts | Windows system fonts (Arial, Arial Unicode, Times New Roman) |

---

## Input Format

The script is **interactive**. You provide:

| Prompt | Description | Example |
|--------|-------------|---------|
| Search text | Exact string to find | `DB_GM5505L` |
| Replacement text | New string | `DB_GM5505L_2` |
| Output folder | Where updated PDFs are saved | `C:\Users\YourName\Desktop\PDF Output` |
| PDF paths | One path per prompt; type `done` to finish | `C:\Reports\report_v1.pdf` |

**Input PDF requirements:**

- Standard text-based or scanned PDF with extractable text layers
- PDF must not already contain the `_2` suffix variant (those are skipped)

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\PDF Text Change"
python PDF_Text_ID_Replacer.py
```

Example session:

```
Enter text to search: DB_GM5505L
Enter replacement text: DB_GM5505L_2
Enter output folder [C:\Users\Swapnali\Desktop\PDF Output]: C:\Output\Updated
Enter PDF path (or 'done'): C:\Reports\Survey_DB_GM5505L.pdf
Enter PDF path (or 'done'): done
```

---

## Expected Output

- Updated PDF(s) saved to the output folder
- If the old search text appears in the filename, it is swapped in the output filename too

**Sample console output:**

```
Processing: C:\Reports\Survey_DB_GM5505L.pdf
  Found 14 occurrences across 8 pages
  Saved: C:\Output\Updated\Survey_DB_GM5505L_2.pdf
All files processed.
```

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| No matches found | Search string not present or different casing/spacing | Verify exact text in PDF |
| Font overflow in table cells | Replacement longer than original | Shorten replacement or manually adjust |
| Already-updated IDs skipped | Text already has `_2` suffix | Expected behavior |
| Output folder not writable | Permissions or path doesn't exist | Create folder or choose valid path |

---

## Tips

- Process one PDF at a time for easier verification.
- Keep originals as backup before batch replacement.
- For scanned PDFs without a text layer, results may be limited.
