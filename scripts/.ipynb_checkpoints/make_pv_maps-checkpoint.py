#!/usr/bin/env python3
import json
from pathlib import Path
CENTER_LAT, CENTER_LON = 40.72465, -73.98030
ZOOM_START = 14
POLY = "pv_canopy_footprints.geojson"
CENT = "pv_canopy_centroids.geojson"
OUT = "maps/pv_canopies_map.html"
def main():
    import folium; Path("maps").mkdir(parents=True, exist_ok=True)
    m = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=ZOOM_START, control_scale=True)
    if Path(POLY).exists(): folium.GeoJson(json.loads(Path(POLY).read_text()), name="PV Canopy Footprints").add_to(m)
    else: folium.Marker([CENTER_LAT, CENTER_LON], tooltip="No canopy footprints yet").add_to(m)
    if Path(CENT).exists(): folium.GeoJson(json.loads(Path(CENT).read_text()), name="PV Canopy Centroids").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m); m.save(OUT); print("Wrote", OUT)
if __name__ == "__main__": main()
