"""
Update Created and Modified timestamps for all regular files in a folder (optionally recursive).

Windows only: File Explorer shows Created from the Windows creation time, which cannot be
changed with os.utime(). This script uses SetFileTime to update Created and Modified together.

Safety: This script never deletes, renames, moves, or overwrites file contents.
It only changes file timestamps; bytes inside each file are untouched.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from datetime import date, datetime
from pathlib import Path
import sys


DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
]

FILE_WRITE_ATTRIBUTES = 0x00000100
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x00000080
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
EPOCH_DIFF_SECONDS = 11644473600
HUNDREDS_OF_NANOSECONDS = 10_000_000


class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]


kernel32 = ctypes.windll.kernel32


def ensure_windows() -> None:
    if sys.platform != "win32":
        raise OSError("This script only works on Windows (Created time requires SetFileTime).")


def parse_date(raw: str) -> datetime:
    value = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError("Invalid date format. Use one of: yyyy-mm-dd, yyyy-mm-dd HH:MM, yyyy-mm-dd HH:MM:SS")


def parse_new_date_only(raw: str) -> date:
    return parse_date(raw).date()


def file_created_datetime(file_path: Path) -> datetime:
    return datetime.fromtimestamp(file_path.stat().st_ctime)


def file_modified_datetime(file_path: Path) -> datetime:
    return datetime.fromtimestamp(file_path.stat().st_mtime)


def combine_new_date_with_existing_time(existing: datetime, new_calendar_date: date) -> datetime:
    return datetime.combine(new_calendar_date, existing.time())


def datetime_to_filetime(dt: datetime) -> FILETIME:
    hundred_ns = int((dt.timestamp() + EPOCH_DIFF_SECONDS) * HUNDREDS_OF_NANOSECONDS)
    return FILETIME(hundred_ns & 0xFFFFFFFF, hundred_ns >> 32)


def set_windows_file_times(
    file_path: Path,
    *,
    created: datetime | None = None,
    accessed: datetime | None = None,
    modified: datetime | None = None,
) -> None:
    handle = kernel32.CreateFileW(
        str(file_path),
        FILE_WRITE_ATTRIBUTES,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle == INVALID_HANDLE_VALUE:
        error_code = kernel32.GetLastError()
        raise OSError(error_code, f"Cannot open file for timestamp update: {file_path}")

    try:
        created_ft = ctypes.byref(datetime_to_filetime(created)) if created else None
        accessed_ft = ctypes.byref(datetime_to_filetime(accessed)) if accessed else None
        modified_ft = ctypes.byref(datetime_to_filetime(modified)) if modified else None

        if not kernel32.SetFileTime(handle, created_ft, accessed_ft, modified_ft):
            error_code = kernel32.GetLastError()
            raise OSError(error_code, f"SetFileTime failed for: {file_path}")
    finally:
        kernel32.CloseHandle(handle)


def ask_yes_no(prompt: str, default_no: bool = True) -> bool:
    answer = input(prompt).strip().lower()
    if not answer:
        return not default_no
    return answer in {"y", "yes"}


def get_files(folder: Path, recurse: bool) -> list[Path]:
    if recurse:
        return [p for p in folder.rglob("*") if p.is_file()]
    return [p for p in folder.iterdir() if p.is_file()]


def set_created_modified_same_datetime(files: list[Path], target: datetime) -> int:
    updated = 0
    for file_path in files:
        stat = file_path.stat()
        accessed = datetime.fromtimestamp(stat.st_atime)
        set_windows_file_times(
            file_path,
            created=target,
            accessed=accessed,
            modified=target,
        )
        updated += 1
    return updated


def set_created_modified_date_only_per_file(files: list[Path], new_calendar_date: date) -> int:
    updated = 0
    for file_path in files:
        stat = file_path.stat()
        created = combine_new_date_with_existing_time(file_created_datetime(file_path), new_calendar_date)
        modified = combine_new_date_with_existing_time(file_modified_datetime(file_path), new_calendar_date)
        accessed = datetime.fromtimestamp(stat.st_atime)
        set_windows_file_times(
            file_path,
            created=created,
            accessed=accessed,
            modified=modified,
        )
        updated += 1
    return updated


def main() -> int:
    try:
        ensure_windows()

        raw_path = input("Enter folder path (or press Enter for current folder): ").strip()
        if raw_path.startswith('"') and raw_path.endswith('"'):
            raw_path = raw_path[1:-1]
        folder = Path(raw_path) if raw_path else Path.cwd()
        folder = folder.expanduser().resolve()

        if not folder.exists() or not folder.is_dir():
            raise FileNotFoundError(f"Folder path not found: {folder}")

        date_only = ask_yes_no(
            "Change only the calendar date and keep each file's current time? (Y/N, default Y): ",
            default_no=False,
        )

        if date_only:
            raw_date = input(
                "Enter new date (yyyy-mm-dd). Time is ignored; each file keeps its own Created/Modified time: "
            ).strip()
            new_day = parse_new_date_only(raw_date)
        else:
            raw_date = input(
                "Enter new Created and Modified date/time for ALL files "
                "(example: 2025-02-18 07:22:16): "
            ).strip()
            target_dt = parse_date(raw_date)

        recurse = ask_yes_no("Include subfolders? (Y/N, default N): ", default_no=True)

        files = get_files(folder, recurse)
        if not files:
            print(f"No files found in: {folder}")
            input("Press Enter to close...")
            return 0

        print(
            f"About to update Created and Modified time on {len(files)} file(s). "
            "No files will be deleted and contents will not be changed."
        )
        confirm = ask_yes_no("Continue? (Y/N, default Y): ", default_no=False)
        if not confirm:
            print("Cancelled. No files were changed.")
            input("Press Enter to close...")
            return 0

        if date_only:
            updated_count = set_created_modified_date_only_per_file(files, new_day)
            print(
                f"Updated Created and Modified date for {updated_count} file(s): "
                f"date set to {new_day.isoformat()}, time kept per file"
            )
        else:
            updated_count = set_created_modified_same_datetime(files, target_dt)
            print(
                f"Updated Created and Modified date/time for {updated_count} file(s) to: "
                f"{target_dt.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        input("Done. Press Enter to close...")
        return 0
    except Exception as exc:
        print(f"\nERROR: {exc}")
        input("Press Enter to close...")
        return 1


if __name__ == "__main__":
    sys.exit(main())
