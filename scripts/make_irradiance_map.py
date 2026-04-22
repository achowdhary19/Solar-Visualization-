#!/usr/bin/env python3
# scripts/make_irradiance_map.py — v4-11a (no external PNGs)

import os, datetime as dt, folium

OUT_HTML = "maps/irradiance_timeseries_map.html"

def _sparkline_svg(values):
    # simple inline SVG sparkline (values in kWh/m^2)
    w,h = 180, 40
    if not values: return ""
    vmin, vmax = min(values), max(values)
    span = (vmax - vmin) or 1.0
    pts=[]
    for i,v in enumerate(values):
        x = int(i * (w-10) / max(1, len(values)-1)) + 5
        y = int(h - 5 - ((v - vmin) / span) * (h-10))
        pts.append(f"{x},{y}")
    poly = " ".join(pts)
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polyline points="{poly}" fill="none" stroke="#1f77b4" stroke-width="2"/></svg>'

def main():
    n = float(os.getenv("PV_N_LAT","40.73230"))
    s = float(os.getenv("PV_S_LAT","40.71700"))
    w = float(os.getenv("PV_W_LON","-73.98660"))
    e = float(os.getenv("PV_E_LON","-73.97400"))
    lat = (s+n)/2.0; lon = (w+e)/2.0

    days = [dt.date.today() - dt.timedelta(days=i) for i in range(13,-1,-1)]
    vals = [4.1 for _ in days]  # flat mock
    table = "<br>".join([f"{d.isoformat()}: {v:.2f} kWh/m^2" for d,v in zip(days,vals)])
    svg  = _sparkline_svg(vals)

    html = f"<b>Irradiance last 14 days</b><br>{svg}<br>{table}"
    m = folium.Map(location=[lat,lon], zoom_start=14, tiles="OpenStreetMap")
    folium.Marker([lat,lon], popup=folium.Popup(html, max_width=320)).add_to(m)
    os.makedirs("maps", exist_ok=True)
    m.save(OUT_HTML)
    print("Saved:", OUT_HTML)

if __name__ == "__main__":
    main()
