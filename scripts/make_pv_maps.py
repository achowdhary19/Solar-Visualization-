# Stage 4 — PV + selection overlays (clear highlighting, robustness)
import os, json
import geopandas as gpd
import folium
from folium.plugins import MiniMap, MeasureControl, Fullscreen, MousePosition, MarkerCluster

def _read(path):
    if not os.path.exists(path):
        print("[MISS]", path); return None
    try:
        g = gpd.read_file(path)
        if g is None or len(g)==0:
            print("[EMPTY]", path); return None
        return g
    except Exception as e:
        print("[ERR]", path, e); return None

# Load artifacts
fp  = _read("footprints.geojson")                        # Stage 2
pv  = _read("pv_canopy_footprints.geojson")              # Stage 3
cen = _read("pv_canopy_centroids.geojson")               # Stage 3
sel_gj = _read("all_walkups_6story.geojson")             # Stage 1 (optional)

# Build selection points if needed from CSV lat/lon
if sel_gj is None and os.path.exists("all_walkups_6story.csv"):
    import pandas as pd
    sel_df = pd.read_csv("all_walkups_6story.csv")
    if {"latitude","longitude"}.issubset({c.lower() for c in sel_df.columns.map(str.lower)}):
        latcol = [c for c in sel_df.columns if c.lower()=="latitude"][0]
        loncol = [c for c in sel_df.columns if c.lower()=="longitude"][0]
        sel_gj = gpd.GeoDataFrame(
            sel_df.copy(),
            geometry=gpd.points_from_xy(sel_df[loncol], sel_df[latcol], crs="EPSG:4326")
        )
        print("[INFO] Built selection points from CSV.")
    else:
        print("[INFO] No lat/lon in selection CSV; selection points will be omitted.")

# Sanity + CRS to 4326
layers = [("Footprints", fp), ("PV footprints", pv), ("PV centroids", cen), ("Selection", sel_gj)]
for name,g in layers:
    if g is not None:
        if g.crs is None: g.set_crs(4326, inplace=True)
        elif g.crs.to_epsg()!=4326: g.to_crs(4326, inplace=True)
        print(f"[INFO] {name}: {len(g)} features")

# Spatial join: flag footprints that contain a selection point
selected_fp = None
if fp is not None and sel_gj is not None and len(fp)>0 and len(sel_gj)>0:
    try:
        # Use projected CRS for reliable point-in-poly, then back to 4326
        fp2263   = fp.to_crs(2263)
        sel2263  = sel_gj.to_crs(2263)
        joined   = gpd.sjoin(sel2263, fp2263, how="inner", predicate="within")
        sel_ids  = set(joined.index_right.dropna().astype(int).tolist())
        if sel_ids:
            selected_fp = fp.iloc[list(sel_ids)].copy().to_crs(4326)
            print(f"[INFO] Selected footprints flagged: {len(selected_fp)}")
        else:
            print("[INFO] No selection points fell within footprints; highlight layer will be empty.")
    except Exception as e:
        print("[WARN] Spatial join failed:", e)

# Compute overall bounds from whatever we have
cands = [g for g in [fp,pv,cen,sel_gj] if g is not None and len(g)>0]
if not cands:
    raise RuntimeError("No layers to map. Generate earlier stages first.")
minx=miny=1e9; maxx=maxy=-1e9
for g in cands:
    mnx,mny,mxx,mxy = g.total_bounds
    minx,miny,maxx,maxy = min(minx,mnx),min(miny,mny),max(maxx,mxx),max(maxy,mxy)
ctr_lat=(miny+maxy)/2; ctr_lon=(minx+maxx)/2

# Build map
m = folium.Map(location=[ctr_lat,ctr_lon], zoom_start=15, tiles="OpenStreetMap", control_scale=True)
Fullscreen().add_to(m)
MiniMap(toggle_display=True, position="bottomright").add_to(m)
MeasureControl(primary_length_unit="meters").add_to(m)
MousePosition(prefix="Lat/Lon", position="bottomleft").add_to(m)

# Draw layers
def add_geojson(g, name, fill, stroke, weight=1, fill_opacity=0.3, show=True, tooltip_fields=None):
    gj = folium.GeoJson(
        data=json.loads(g.to_json()),
        name=name,
        show=show,
        style_function=lambda _:{ "fillColor":fill, "color":stroke, "weight":weight, "fillOpacity":fill_opacity }
    )
    if tooltip_fields:
        gj.add_child(folium.features.GeoJsonTooltip(fields=tooltip_fields[:10]))
    gj.add_to(m)

# 1) base footprints (light)
if fp is not None and len(fp)>0:
    add_geojson(fp, "Footprints (all)", fill="#9ecae1", stroke="#6baed6", weight=1, fill_opacity=0.15, show=False,
                tooltip_fields=[c for c in fp.columns if c!="geometry"])

# 2) pv polygons (orange)
if pv is not None and len(pv)>0:
    add_geojson(pv, "PV Canopy Footprints", fill="#ffb347", stroke="#f59f00", weight=1, fill_opacity=0.35, show=True,
                tooltip_fields=[c for c in pv.columns if c!="geometry"])

# 3) selected footprints (bold blue)
if selected_fp is not None and len(selected_fp)>0:
    add_geojson(selected_fp, "Selected Footprints (6-story C*)", fill="#3182bd", stroke="#08519c", weight=3, fill_opacity=0.20, show=True,
                tooltip_fields=[c for c in selected_fp.columns if c!="geometry"])

# 4) centroids (markers)
if cen is not None and len(cen)>0:
    grp = folium.FeatureGroup(name="PV Centroids", show=False)
    for _,row in cen.iterrows():
        try:
            lat = row.geometry.y; lon = row.geometry.x
            popup = folium.Popup(
                html="<b>PV</b>: {:.1f} kW<br><b>Annual</b>: {:.0f} kWh".format(
                    float(row.get("pv_kw_dc",0)), float(row.get("annual_kwh",0))
                ), max_width=250
            )
            folium.CircleMarker([lat,lon], radius=5, color="#7b1fa2", fill=True, fill_opacity=0.8, popup=popup).add_to(grp)
        except Exception:
            continue
    grp.add_to(m)

# 5) selection points (cluster)
if sel_gj is not None and len(sel_gj)>0 and sel_gj.geom_type.isin(["Point"]).any():
    cl = MarkerCluster(name="Selection Points", show=False)
    for _,r in sel_gj.iterrows():
        try:
            lat=r.geometry.y; lon=r.geometry.x
            folium.Marker([lat,lon]).add_to(cl)
        except Exception:
            continue
    cl.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
m.fit_bounds([[miny,minx],[maxy,maxx]])

os.makedirs("maps", exist_ok=True)
m.save("maps/pv_overlays_map.html")
print("Saved maps/pv_overlays_map.html")

# Extra: zoomed on selected if available
if selected_fp is not None and len(selected_fp)>0:
    mnx,mny,mxx,mxy = selected_fp.total_bounds
    m2 = folium.Map(location=[(mny+mxy)/2,(mnx+mxx)/2], zoom_start=17, tiles="OpenStreetMap")
    add_geojson(selected_fp, "Selected Footprints (6-story C*)", fill="#3182bd", stroke="#08519c", weight=3, fill_opacity=0.25, show=True,
                tooltip_fields=[c for c in selected_fp.columns if c!="geometry"])
    folium.LayerControl().add_to(m2)
    m2.fit_bounds([[mny,mnx],[mxy,mxx]])
    m2.save("maps/pv_overlays_map_selected.html")
    print("Saved maps/pv_overlays_map_selected.html")
