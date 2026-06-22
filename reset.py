# reset.py
import shutil
from pathlib import Path

def reset_project():
    print("Cleaning generated artifacts...")
    
    # 1. Delete specific file types in the root directory
    # todo merge with (2.) so we just delete data output directories 
    for ext in ["*.csv", "*.geojson", "*.md", "*.png"]:
        for file_path in Path('.').glob(ext):
            try:
                file_path.unlink()
            except OSError:
                pass

    # 2. Delete directories if they exist
    directories_to_remove = ["maps", "exports", Path("DATA") / "processed"]
    for dir_name in directories_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            shutil.rmtree(dir_path, ignore_errors=True)

    # 3. Recreate the DATA/processed directory
    processed_dir = Path("DATA") / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    print("Cleanup complete.")

if __name__ == "__main__":
    reset_project()
