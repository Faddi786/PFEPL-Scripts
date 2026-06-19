import os
import shutil
from pathlib import Path

def merge_category_folders(source1: str, source2: str, final_dest: str):
    """
    Merges contents from matching category folders of two sources into one final folder.
    Example: Source1\PDFs + Source2\PDFs  →  Final\PDFs
    """
    
    src1 = Path(source1).resolve()
    src2 = Path(source2).resolve()
    dest = Path(final_dest).resolve()
    
    if not src1.exists() or not src1.is_dir():
        print(f"❌ Source Folder 1 not found: {src1}")
        return
    if not src2.exists() or not src2.is_dir():
        print(f"❌ Source Folder 2 not found: {src2}")
        return
    if not dest.exists() or not dest.is_dir():
        print(f"❌ Final destination folder not found. Create it first: {dest}")
        return
    
    # ====================== CATEGORIES ======================
    categories = [
        "Images", "PDFs", "Word_Docs", "Excel_Sheets", "PowerPoint",
        "Text_Files", "Zips", "Shortcuts", "Videos", "Audio",
        "Executables", "Scripts_Code", "Other", "Folders"
    ]
    
    # Create all category folders in final destination (only if missing)
    print("Creating category folders in Final Destination...")
    for cat in categories:
        cat_path = dest / cat
        if not cat_path.exists():
            cat_path.mkdir()
            print(f"   ✓ Created: {cat}")
        else:
            print(f"   ✓ Already exists: {cat}")
    
    print(f"\n✅ Starting merge into final destination: {dest}\n")
    
    total_moved = 0
    errors = 0
    
    for cat in categories:
        print(f"\n📂 Processing category: **{cat}**")
        
        # Process Source 1
        src1_cat = src1 / cat
        if src1_cat.exists() and src1_cat.is_dir():
            print(f"   → Moving from Source 1 \\ {cat}")
            for item in os.listdir(src1_cat):
                item_path = src1_cat / item
                dest_path = dest / cat / item
                
                try:
                    # Handle name conflicts
                    if dest_path.exists():
                        base = dest_path.stem
                        suffix = dest_path.suffix if dest_path.is_file() else ""
                        counter = 1
                        while (dest / cat / f"{base}_{counter}{suffix}").exists():
                            counter += 1
                        dest_path = dest / cat / f"{base}_{counter}{suffix}"
                    
                    shutil.move(str(item_path), str(dest_path))
                    print(f"      ✅ Moved: {item}")
                    total_moved += 1
                except Exception as e:
                    print(f"      ❌ Failed: {item} → {e}")
                    errors += 1
        else:
            print(f"   → Source 1 \\ {cat} not found or empty (skipped)")
        
        # Process Source 2
        src2_cat = src2 / cat
        if src2_cat.exists() and src2_cat.is_dir():
            print(f"   → Moving from Source 2 \\ {cat}")
            for item in os.listdir(src2_cat):
                item_path = src2_cat / item
                dest_path = dest / cat / item
                
                try:
                    if dest_path.exists():
                        base = dest_path.stem
                        suffix = dest_path.suffix if dest_path.is_file() else ""
                        counter = 1
                        while (dest / cat / f"{base}_{counter}{suffix}").exists():
                            counter += 1
                        dest_path = dest / cat / f"{base}_{counter}{suffix}"
                    
                    shutil.move(str(item_path), str(dest_path))
                    print(f"      ✅ Moved: {item}")
                    total_moved += 1
                except Exception as e:
                    print(f"      ❌ Failed: {item} → {e}")
                    errors += 1
        else:
            print(f"   → Source 2 \\ {cat} not found or empty (skipped)")
    
    print("\n" + "="*85)
    print("🎉 MERGE OPERATION COMPLETE!")
    print(f"Total items moved : {total_moved}")
    print(f"Errors encountered : {errors}")
    print(f"\nFinal organized backup location: {dest}")
    print("="*85)
    print("\nAll matching folders from both sources have been merged into single folders in the final destination.")


# ====================== RUN ======================
if __name__ == "__main__":
    print("=== Merge Category Folders from Two Sources ===\n")
    print("This will combine same category folders from both sources into one.\n")
    
    source1 = input("Enter path of Source Folder 1:\n→ ").strip().strip('"')
    
    source2 = input("\nEnter path of Source Folder 2:\n→ ").strip().strip('"')
    
    final_dest = input("\nEnter path of Final Destination folder (create this empty folder first):\n→ ").strip().strip('"')
    
    if source1 and source2 and final_dest:
        merge_category_folders(source1, source2, final_dest)
    else:
        print("❌ All three paths are required!")