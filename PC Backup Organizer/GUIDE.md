# PC Backup Organizer — User Guide

## Overview

Two-step pipeline to organize messy backup folders by file type, then merge two organized backups into one unified destination.

```
Step-1.py (organize one source)  →  Step-2.py (merge two organized backups)
```

Run Step-1 twice (once per source) before Step-2.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.6+ |
| Packages | None (stdlib only) |

---

## Step 1 — Organize Files (`Step-1.py`)

### Overview

Moves **root-level files only** from a source folder into typed category subfolders inside an existing backup directory. Root subfolders are moved into a `Folders\` subfolder.

### Input (Interactive)

| Prompt | Example |
|--------|---------|
| SOURCE path | `D:\OldBackup\Desktop_Dump` |
| BACKUP path (must exist) | `D:\Organized\Backup_PC1` |

### File Categories Created

Images, PDFs, Word_Docs, Excel_Sheets, PowerPoint, Videos, Audio, Archives, Code, Other, and `Folders\` for subdirectories.

### How to Run

```powershell
cd "c:\Users\RAK\Desktop\Only Scripts\PC Backup Organizer"
python Step-1.py
```

### Expected Output

```
D:\Organized\Backup_PC1\
  Images\
  PDFs\
  Word_Docs\
  Excel_Sheets\
  ...
  Folders\
    Projects\
    Downloads\
```

**Sample console:**

```
SOURCE: D:\OldBackup\Desktop_Dump
BACKUP: D:\Organized\Backup_PC1
Moved report.pdf → PDFs\
Moved photo.jpg → Images\
Moved Projects\ → Folders\Projects\
Done. 142 files organized.
```

---

## Step 2 — Merge Backups (`Step-2.py`)

### Overview

Merges matching category folders from two organized backup sources into a final destination.

### Input (Interactive)

| Prompt | Example |
|--------|---------|
| Source 1 | `D:\Organized\Backup_PC1` |
| Source 2 | `D:\Organized\Backup_PC2` |
| Final Destination (must exist) | `D:\Organized\Final_Merged` |

### How to Run

```powershell
python Step-2.py
```

### Expected Output

Unified folder with merged contents. Name conflicts are auto-suffixed (`file_1.pdf`, `file_2.pdf`).

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Backup folder must exist | Destination not created | Create empty backup/destination folder first |
| Permission denied | File open in another program | Close applications using the files |
| Only root level processed | Files deep in subfolders skipped | Step-1 only handles root-level files by design |
| Path not found (Step 2) | One of three paths invalid | Verify all three paths exist |

---

## Full Workflow

1. Create empty backup folder for PC1
2. Run `Step-1.py` with PC1 source → organized backup
3. Create empty backup folder for PC2
4. Run `Step-1.py` with PC2 source → organized backup
5. Create final destination folder
6. Run `Step-2.py` to merge both into final destination
