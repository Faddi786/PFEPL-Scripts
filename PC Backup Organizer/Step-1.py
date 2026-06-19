import os
import shutil
from pathlib import Path

def organize_root_level(source_dir: str, backup_dir: str):
    """
    Moves root-level files into category folders and root-level folders 
    into a 'Folders' folder inside the backup directory.
    Creates folders only if they don't already exist.
    """
    
    source_path = Path(source_dir).resolve()
    backup_path = Path(backup_dir).resolve()
    
    if not source_path.exists() or not source_path.is_dir():
        print(f"❌ Invalid source folder: {source_path}")
        return
    
    if not backup_path.exists() or not backup_path.is_dir():
        print(f"❌ Backup folder does not exist. Please create it first: {backup_path}")
        return
    
    # ====================== FILE CATEGORIES ======================
    categories = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".heic"],
        "PDFs": [".pdf"],
        "Word_Docs": [".doc", ".docx", ".odt", ".rtf"],
        "Excel_Sheets": [".xls", ".xlsx", ".csv", ".ods"],
        "PowerPoint": [".ppt", ".pptx", ".odp"],
        "Text_Files": [".txt", ".md", ".log"],
        "Zips": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "Shortcuts": [".lnk"],
        "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
        "Audio": [".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"],
        "Executables": [".exe", ".msi", ".bat", ".cmd"],
        "Scripts_Code": [".py", ".js", ".html", ".css", ".php", ".sh", ".java", ".cpp", ".c"],
        "Other": []   # unknown file types
    }
    
    # Create category folders ONLY if they don't already exist
    print("Checking/Creating category folders inside Backup...")
    for cat in categories.keys():
        cat_folder = backup_path / cat
        if not cat_folder.exists():
            cat_folder.mkdir()
            print(f"   ✓ Created: {cat}")
        else:
            print(f"   ✓ Already exists: {cat}")
    
    # Special "Folders" directory for all subfolders
    folders_dir = backup_path / "Folders"
    if not folders_dir.exists():
        folders_dir.mkdir()
        print("   ✓ Created: Folders")
    else:
        print("   ✓ Already exists: Folders")
    
    print(f"\n✅ Starting MOVE operation (root level only)")
    print(f"   Source : {source_path}")
    print(f"   Backup : {backup_path}\n")
    
    moved_files = 0
    moved_folders = 0
    errors = 0
    
    for item in os.listdir(source_path):
        item_path = source_path / item
        
        try:
            if item_path.is_dir():
                # Move folder into "Folders" category
                dest = folders_dir / item
                if dest.exists():
                    counter = 1
                    while (folders_dir / f"{item}_{counter}").exists():
                        counter += 1
                    dest = folders_dir / f"{item}_{counter}"
                
                shutil.move(str(item_path), str(dest))
                print(f"📁 Moved folder → Folders : {item}")
                moved_folders += 1
                
            else:
                # It's a file → categorize
                ext = item_path.suffix.lower()
                category = "Other"
                for cat_name, ext_list in categories.items():
                    if ext in ext_list:
                        category = cat_name
                        break
                
                dest_file = backup_path / category / item
                
                # Handle duplicate names
                if dest_file.exists():
                    base = dest_file.stem
                    suffix = dest_file.suffix
                    counter = 1
                    while dest_file.exists():
                        dest_file = backup_path / category / f"{base}_{counter}{suffix}"
                        counter += 1
                
                shutil.move(str(item_path), str(dest_file))
                print(f"✅ Moved → {category} : {item}")
                moved_files += 1
                
        except Exception as e:
            print(f"❌ Error moving {item} → {e}")
            errors += 1
    
    print("\n" + "="*80)
    print("🎉 OPERATION COMPLETE!")
    print(f"Files moved to categories : {moved_files}")
    print(f"Folders moved to 'Folders': {moved_folders}")
    print(f"Errors encountered        : {errors}")
    print(f"\nOrganized backup location : {backup_path}")
    print("="*80)
    print("\nNote: Only root-level items were processed. No deeper levels were touched.")


# ====================== RUN ======================
if __name__ == "__main__":
    print("=== Root-Level Organizer (Move + Smart Folder Creation) ===\n")
    print("Files → sorted by type")
    print("Folders → moved into 'Folders' folder")
    print("Category folders are created only if missing.\n")
    
    source = input("Enter SOURCE folder path:\n→ ").strip().strip('"')
    
    backup = input("\nEnter BACKUP folder path (must exist):\n→ ").strip().strip('"')
    
    if source and backup:
        organize_root_level(source, backup)
    else:
        print("❌ Both paths are required!")