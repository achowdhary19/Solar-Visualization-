#!/usr/bin/env python3
import sys
from pathlib import Path
CHECKS = [
    ("Stage 1", ["all_walkups_6story.csv","all_walkups_6story.geojson"]),
    ("Stage 2", ["footprints.geojson"]),
    ("Stage 3", ["pv_footprints_by_building.csv","pv_canopy_footprints.geojson","pv_canopy_centroids.geojson","pv_canopy_centroids.csv"]),
    ("Stage 4", ["maps/pv_canopies_map.html"]),
    ("Stage 5", ["totals_summary.md","totals_bar.png"]),
    ("Stage 6", ["DATA/zola/zoning_districts.geojson"]),
    ("Stage 8", ["DATA/processed/footprints_enriched_zola.geojson","DATA/processed/footprints_enriched_zola.csv"])
]
def check_file(p): path = Path(p); return path.exists() and path.stat().st_size > 0
def main():
    ok_all = True
    for stage, files in CHECKS:
        print(f"== {stage} ==")
        for f in files:
            ok = check_file(f); print(f" {f}: {'OK' if ok else 'MISSING'}"); ok_all &= ok
    if ok_all: print("All required outputs found."); sys.exit(0)
    else: print("Some outputs missing. Re-run relevant stage(s)."); sys.exit(1)
if __name__ == "__main__": main()
