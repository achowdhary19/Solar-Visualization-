#!/usr/bin/env python3
from pathlib import Path
CENTER_LAT, CENTER_LON = 40.72465, -73.98030
ZOOM_START = 14
PNG_IN = "irradiance_last14d.png"
OUT_HTML = "maps/irradiance_timeseries_map.html"
def main():
    import folium
    from folium.plugins import FloatImage
    Path("maps").mkdir(parents=True, exist_ok=True)
    m = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=ZOOM_START, control_scale=True)
    p = Path(PNG_IN)
    if p.exists():
        target = Path("maps") / p.name
        if not target.exists(): target.write_bytes(p.read_bytes())
        FloatImage(str(target), bottom=5, left=65).add_to(m)
    else:
        folium.Marker([CENTER_LAT, CENTER_LON], tooltip="irradiance_last14d.png not found").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m); m.save(OUT_HTML); print("Wrote", OUT_HTML)
if __name__ == "__main__": main()
