# Image Date Modification — User Guide

## Overview

`set_image_created_modified_date.py` updates the Windows **Created** and **Modified** file timestamps for all files in a folder. File contents are not changed — only the filesystem metadata dates are updated. Useful for organizing photo archives, aligning backup timestamps, or batch-correcting file dates.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Operating system | **Windows only** (uses `ctypes` Win32 API) |
| Python | 3.6+ |
| Packages | None (stdlib only) |

---

## Input Format

The script is **fully interactive** — no config file required.

You will be prompted for:

| Prompt | Accepted values | Example |
|--------|-----------------|---------|
| Folder path | Any valid Windows directory | `C:\Photos\Project2024` |
| Date type | `1` = date only (midnight), `2` = full date-time | `2` |
| New date | See formats below | `2024-06-15 14:30:00` |
| Recurse subfolders | `Y` / `N` | `Y` |

**Accepted date formats:**

- `yyyy-mm-dd` → e.g. `2024-03-15`
- `yyyy-mm-dd HH:MM` → e.g. `2024-03-15 09:30`
- `yyyy-mm-dd HH:MM:SS` → e.g. `2024-03-15 09:30:45`

---

## How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\Image Date Modification"
python set_image_created_modified_date.py
```

Follow the on-screen prompts.

---

## Expected Output

**Sample console interaction:**

```
Enter folder path: C:\Photos\Trip2024
Set date only (1) or full date-time (2)? 1
Enter new date (yyyy-mm-dd): 2024-08-01
Recurse into subfolders? (Y/N): Y

Processing 247 files in C:\Photos\Trip2024 ...
Updated: IMG_001.jpg
Updated: IMG_002.jpg
...
Done. 247 files updated, 0 failed.
```

Both **Created** and **Modified** timestamps are set to the specified date/time.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Invalid date format` | Wrong date string | Use one of the accepted formats above |
| `Folder not found` | Path typo or network drive unavailable | Verify path exists |
| `Permission denied` | System/protected files or files open in another app | Close apps; exclude system folders |
| Script exits immediately on Linux/Mac | Windows-only API | Run on Windows |

---

## Important Notes

- Changes are **permanent** — there is no undo. Consider testing on a copy first.
- Affects **all file types** in the folder, not just images (despite the folder name).
- Does not update the **Accessed** date separately; Created and Modified are both set.
