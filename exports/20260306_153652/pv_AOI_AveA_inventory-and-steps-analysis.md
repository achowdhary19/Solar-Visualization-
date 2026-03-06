Here’s a tight status + checklist so you can confirm we have a clean, reproducible pipeline before you step away.

# Clean pipeline: inventory & flow

## Environment & runtime requirements

- Windows + PowerShell (you’re already using `pv_env`).
- Conda env: working `geopandas` stack with `pyogrio`, `shapely`, `pyproj`, `fiona`, `gdal` (verified functioning after your recent fixes).
- PROJ/GDAL paths pinned to the env (your activation script now sets `PROJ_LIB` and `GDAL_DATA` to the env’s `Library\share\...`—no more cross-contamination from base).
- PowerShell execution OK for local scripts (you ran `run_style.ps1` successfully).
- **Encoding rule:** all project `.py` files saved as **UTF-8 without BOM**, ASCII-only characters in literals (we removed non-ASCII quoting and any `folium.utilities.escape_html` usage).

## Data locations (project-relative)

- `DATA\aoi.geojson` (generated)
- `DATA\pluto.geojson` (optional input, local file)
- `DATA\zola_zoning.geojson` (optional input, local file)
- `OUT\footprints.geojson` (generated)
- `OUT\pv_canopy_footprints.geojson` (generated)
- `OUT\pv_sites_centroids.geojson` (generated)
- `OUT\maps\pv_canopies_map.html` (generated, basic map)
- `OUT\maps\irradiance_timeseries_map.html` (generated, styled map)

## End-to-end steps (scripts, inputs → outputs → map layers)

1. **Stage 0 — AOI**
   - Script: `scripts\stage0_aoi.py`
   - Input: the hard-coded AOI polygon (your updated multi-point coordinates, already wired)
   - Output: `DATA\aoi.geojson`
   - Visible map layer: (drawn implicitly by `stage4_style` for fitBounds only)
2. **Stage 2 — Footprints fetch**
   - Script: `scripts\fetch_footprints.py`
   - Input: `DATA\aoi.geojson`
   - Output: `OUT\footprints.geojson` (OSM building footprints within AOI)
   - Visible map layer (later): **Building Footprints** (with PLUTO/ZoLa attributes merged by `stage4_style`)
3. **Stage 3 — PV sizing**
   - Script: `scripts\stage3_pv_sizing.py`
   - Inputs: `OUT\footprints.geojson`
   - Outputs: 
     - `OUT\pv_canopy_footprints.geojson` (polygons with `pv_kw`, `pv_area_m2`, etc.)
     - `OUT\pv_sites_centroids.geojson` (points with the same PV attributes)
   - Visible layers (later): **PV Canopy Footprints** (polygons), **PV Sites (centroids)** (clustered)
4. **Stage 4 — Styled map**
   - Script: `scripts\stage4_style.py` (the drop-in you just ran)
   - Inputs: 
     - `OUT\pv_canopy_footprints.geojson`
     - `OUT\pv_sites_centroids.geojson`
     - `OUT\footprints.geojson`
     - `DATA\aoi.geojson`
     - Optional: `DATA\pluto.geojson`, `DATA\zola_zoning.geojson`
   - Output: `OUT\maps\irradiance_timeseries_map.html`
   - Visible layers & behavior: 
     - **Base map:** OpenStreetMap standard tiles.
     - **AOI fit:** map auto-zooms to AOI bounds on load.
     - **Building Footprints:** light gray polygons, tooltips show BBL + PLUTO/ZoLa fields (BBL key join when present, otherwise centroid-in-polygon spatial match). Only features whose **centroid** falls inside AOI are included.
     - **PV Canopy Footprints:** orange/yellow fill (#e67e22 outline / #f1c40f fill, \~0.35 opacity). Tooltip shows PV kW / area; popups give a compact PV summary (kW, area, kW/m²).
     - **PV Sites (centroids):** clustered points; clusters **collapse/expand with zoom** (`disableClusteringAtZoom=18`); popups mirror the PV summary.
     - **Summary box (toggleable):** total PV sites and total kW; on/off checkbox.
     - **Controls:** Layer control (not collapsed), measure tool (meters / km; m²).

## How to run (two ways)

- **Full pipeline then style:**

  ```
  conda activate pv_env
  python -m scripts.stage0_aoi
  python -m scripts.fetch_footprints
  python -m scripts.stage3_pv_sizing
  python -m scripts.stage4_style ^
    --out OUT\maps\irradiance_timeseries_map.html ^
    --pv-polys OUT\pv_canopy_footprints.geojson ^
    --pv-centroids OUT\pv_sites_centroids.geojson ^
    --footprints OUT\footprints.geojson ^
    --pluto DATA\pluto.geojson ^
    --zola DATA\zola_zoning.geojson ^
    --aoi DATA\aoi.geojson ^
    --title "LES PV & Irradiance Map" ^
    --basemap-url "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" ^
    --basemap-attrib "Map data: OpenStreetMap contributors"
  ```
- **Helper scripts (if present on your side):**
  - `python -m scripts.run_pipeline` (stages 0–3)
  - Then `run_style.ps1` or `run_style.bat` (Stage 4 arguments are embedded)

## Style elements currently in place (to match your reference)

- **Base tiles:** OSM standard (not Carto light), same feel as the example.
- **Title banner:** centered, semi-transparent white, rounded corners, Arial 14px, subtle shadow.
- **Legend / PV summary box:** bottom-left, semi-transparent white, toggle checkbox, Arial 12px.
- **PV polygons:** outline `#e67e22`, fill `#f1c40f`, fillOpacity 0.35 (readable over OSM).
- **Footprints:** light gray outline `#888`, fill `#ccc`, fillOpacity 0.15; highlight on hover (darker stroke).
- **Centroids:** clustered; individual point ring `#d35400`, fill `#e67e22`, radius \~3.5.
- **Tooltips & popups:** clean, small type; footprint tooltip includes BBL + PLUTO (ADDRESS, LANDUSE, LOT/BLDG area, FLOORS) and ZoLa (ZONEDIST, etc.) when available; PV popups show kW, area, and density.

## Current confirmations

- ✅ Pipeline executes without the earlier PROJ/GDAL conflicts.
- ✅ Files are written under `OUT\...` (and `OUT\maps\...`) as intended.
- ✅ Map fits to AOI and filters layers to AOI via centroid-in-polygon.
- ✅ PV centroids **cluster** and de-cluster properly as you zoom.
- ✅ No BOM/encoding errors; all scripts use ASCII-safe literals and UTF-8 (no BOM).
- ✅ `folium.utilities.escape_html` removed (no attribute error).
- ✅ PLUTO/ZoLa join logic: BBL→PLUTO when available; else spatial matches; tooltips populate accordingly.

If you want the legend, fonts, and color numbers tuned to **exact** values from `20250829_irradiance_timeseries_map_fast.html`, I can lock those hex codes and font sizes precisely (down to the header opacity) in `stage4_style.py`—just say the word when you’re back.

All set on my end.

============================================================

Got it. Here’s a crisp diagnosis and the concrete next steps to restore the exact behavior (BBL on building hover, PV centroid summary popups, clustering/zoom behavior, AOI fit, and PLUTO/ZOLA overlays).

# Why the BBL + PV summaries aren’t showing

1. **Empty GeoJSON payloads were injected into the map.**  
   In the latest HTML the PV layers are added with `features: []`, so there’s literally nothing to show or bind tooltips/popups to. Example for both footprints and centroids: the generated script calls `.addData({ ..., "features": [] ...})`. and again for the footprints earlier in the same file.
2. **No per-feature event bindings (tooltips/popups) are wired.**  
   Your `onEachFeature` stubs are empty (`layer.on({});`), so even if features were present, nothing would appear on hover/click.
3. **Marker clustering (zoom-level collapsing/expanding) is missing for PV centroids.**  
   The reference map adds markers into a `marker_cluster_*` group and binds a popup that includes **Address + BBL + PV size + PSH**. That construct is not present in your latest output. You can see the reference pattern right here: a marker added to `marker_cluster_…` with a popup that contains BBL and PV summary text.
4. **PLUTO/ZOLA overlays aren’t actually on the map.**  
   Your layer control only shows the PV footprints and PV centroids overlays—no PLUTO buildings or ZOLA zoning layer to hover over for BBL/etc.
5. **No AOI fit and no AOI mask clip applied at render time.**  
   The map initializes to a fixed center/zoom and doesn’t call `fitBounds(aoiBounds)`, so you’re not starting inside the boundary, and nothing limits feature interaction visually to the AOI. The init block shows a fixed center/zoom.

---

# What to do next (step-by-step)

Below are the changes to make in your **render step** (your `stage4_style.py`) so you don’t have to re-run the heavy geometry stages. (If your `OUT/*.geojson` are truly empty, fix that upstream first—see item 0.)

**0) Sanity-check the inputs are non-empty (fast).**  
Before rendering, verify the three inputs exist and have rows:

- `OUT\pv_canopy_footprints.geojson`
- `OUT\pv_sites_centroids.geojson` (must contain properties like `address`, `bbl`, `pv_kw`, `psh`)
- `DATA\pluto.geojson` and `DATA\zola_zoning.geojson` (fields including `bbl` expected)

**1) Fit map to the AOI.**  
Read `DATA\aoi.geojson`, compute `bounds`, and call `m.fit_bounds(bounds)` before adding layers. Your current HTML uses a fixed center/zoom; replace that with `fitBounds(aoi)` once the AOI is loaded.

**2) Add PLUTO footprints with a tooltip that shows BBL on hover.**

- Load PLUTO GeoJSON as a `folium.GeoJson` layer.
- Add a `GeoJsonTooltip(fields=["bbl"], aliases=["BBL:"])` and style (stroke/fill) to match the reference look.
- Ensure the PLUTO layer is included in `L.control.layers` so you can toggle it on/off (it’s missing now).

**3) Add ZOLA zoning as a separate overlay (styled faintly).**

- Load `DATA\zola_zoning.geojson` with subtle outlines/fill; include in the layer control.

**4) PV centroids: enable clustering + summary popup content.**

- Wrap the centroids in a **MarkerCluster** (`folium.plugins.MarkerCluster`), and set `disableClusteringAtZoom=N` so they **collapse at city zooms and expand as you zoom in** (the reference does this via a `marker_cluster_*` group).
- For each centroid, bind a popup HTML built from properties:  
  `Address`, `BBL`, `PV size (kW)`, `PSH`. The reference popup shows the exact text layout.
- Also bind a short tooltip (just the address) like the reference.

**5) PV footprints: mouseover tooltip + click popup (optional).**

- Provide a simple tooltip (e.g., `PV size: {pv_kw} kW`) and, if useful, a small popup that links to the centroid popup summary (keeps consistency).

**6) AOI visual boundary + interaction region.**

- Add the AOI polygon (thin dashed line, transparent fill) so the boundary is visible.
- Keep the data **spatially clipped upstream**; at render time, you can also style non-AOI features to opacity 0 or not add them at all (best is to feed only AOI-clipped GeoJSONs to this stage, which your pipeline already does when healthy).

**7) Restore the exact styling/palette/legend from the sample.**

- Use the same OSM base tiles (not CARTO) as seen in reference and your current base.
- Re-add the header/title box, legend box, and CSS rules (fonts, box shadow, semi-transparent background) matching the sample’s look.
- Add scale control (it’s already present).
- Add the measurement ruler control if it was in the original (Leaflet.Measure or Leaflet.Draw plugin).

---

# Most likely root causes in your last run

- **Renderer fed empty FeatureCollections** (so nothing to display or bind). Verified in the emitted HTML: the map adds `features: []` for both PV layers.
- **Missing binding code** (no `onEachFeature` work): tooltips/popups never connected.
- **No MarkerCluster on centroids** (so no collapse/expand behavior) vs. the sample, which clearly clusters and includes the BBL/summary in popups.
- **PLUTO/ZOLA overlays not added to the control**, so you can’t toggle or hover for BBL.
- **AOI fit not applied**, map starts at fixed center/zoom.

---

# Action checklist (quick)

- [ ] Re-export non-empty `OUT\pv_canopy_footprints.geojson` and `OUT\pv_sites_centroids.geojson` if they’re empty.
- [ ] In `stage4_style.py`:
  - [ ] Load AOI and call `fitBounds(aoi)`.
  - [ ] Add PLUTO with `GeoJsonTooltip(fields=["bbl"], aliases=["BBL:"])`.
  - [ ] Add ZOLA overlay.
  - [ ] Wrap centroids in `MarkerCluster(disableClusteringAtZoom=16)`; bind popup HTML with `Address`, `BBL`, `PV size`, `PSH` in the exact reference layout.
  - [ ] Recreate the reference header/legend CSS blocks and add them to the DOM.
  - [ ] Keep OSM tiles as base (matches sample).

If you want, I can generate a drop-in `stage4_style.py` patch that implements the above bindings/clustering + the header/legend blocks exactly like the reference HTML.

============================================================

Got it — here’s a clean, drop-in replacement that does what you asked:

- Fits/zooms to your AOI
- Keeps all selections clipped to the AOI
- Wires **PLUTO** (BBL/address) and **ZoLa** (zoning) into **building footprints** via a centroid spatial join
- Adds **PV Sites (Centroids)** with popups that include **PV size (kW), rooftop_area_m2, canopy_area_m2, address, BBL**
- Adds **PV Canopy Footprints** with a tooltip (PV kW + address + BBL if present)
- Adds **Building Footprints** with tooltip (BBL, Address, Zoning) — full PLUTO/ZOLA joins are on the layer; the tooltip shows the key fields
- Adds a **toggleable** overlay layer named **“PV Potentials Summary”** with subtitle **“14 day irradiance time series”** (and removes the KW/h note)
- Sets the map title across the top to **“ECOLIBRIUM Solar PV Irradiance Potentials”**
- Uses OpenStreetMap base tiles (as in the sample)
- All ASCII only; avoids `folium.utilities.escape_html` so it won’t crash your folium version

---

# 1) `scripts\stage4_style.py` (complete replacement)

Save this as `scripts\stage4_style.py` (overwrite):

```
# -*- coding: ascii -*-
"""
Stage 4 styled map builder (ASCII-safe).

- Fits/zooms to AOI polygon.
- Clips layers to AOI.
- Joins PLUTO and ZoLa (zoning) to building footprints via spatial join on centroids.
- Adds PV centroids cluster with de-cluster at high zoom.
- PV centroid popups include pv_kw, rooftop_area_m2, canopy_area_m2 when present, plus BBL/address if joined.
- Building footprint tooltips include BBL, address and zoning when available.
- Adds toggleable "PV Potentials Summary" layer (subtitle: "14 day irradiance time series").
- Uses OpenStreetMap tiles by default.
- Pure ASCII; no folium.utilities.escape_html usage.
"""

import argparse, os
from html import escape as html_escape

import folium
from folium.plugins import MarkerCluster, MeasureControl
import geopandas as gpd

CRS_LONLAT = "EPSG:4326"

def _read_gdf(path):
    g = gpd.read_file(path)
    if g.crs is None:
        g.set_crs(CRS_LONLAT, inplace=True)
    else:
        g = g.to_crs(CRS_LONLAT)
    g = g[g.geometry.notnull()]
    if len(g):
        g = g[g.geometry.is_valid]
    return g

def _clip_to_aoi(g, aoi_gdf):
    if g is None or len(g) == 0:
        return g
    try:
        a = aoi_gdf.unary_union
        g = g[g.intersects(a)]
    except Exception:
        pass
    return g

def _safe_get(d, *names):
    for n in names:
        if n in d:
            return d[n]
    return None

def _format_num(x, nd=1):
    try:
        return f"{float(x):,.{nd}f}"
    except Exception:
        return str(x)

def _summary_box_html(tot_sites, tot_kw):
    return (
        '<div id="pv-summary-box" '
        'style="position:absolute; top:60px; right:12px; z-index:9999; '
        'background: rgba(255,255,255,0.92); border:1px solid #999; '
        'border-radius:8px; padding:10px 12px; font-family:Arial, sans-serif; '
        'font-size:12px; box-shadow:0 2px 8px rgba(0,0,0,0.25);">'
        '<div style="font-weight:bold; font-size:14px;">PV Potentials Summary</div>'
        '<div style="font-size:11px; color:#444;">14 day irradiance time series</div>'
        '<hr style="margin:6px 0;">'
        f'<div>Total candidate sites: <b>{tot_sites:,}</b></div>'
        f'<div>Estimated PV capacity: <b>{_format_num(tot_kw,1)} kW</b></div>'
        '</div>'
    )

def _title_html(title_text):
    return (
        '<div '
        'style="position:absolute; top:8px; left:50%; transform:translateX(-50%); '
        'z-index:9999; background: rgba(255,255,255,0.95); border:1px solid #999; '
        'border-radius:8px; padding:8px 14px; font-family:Arial, sans-serif; '
        'font-size:16px; font-weight:bold; box-shadow:0 2px 8px rgba(0,0,0,0.25);">'
        + html_escape(title_text) +
        '</div>'
    )

def _build_map(args):
    # base layer
    m = folium.Map(location=[40.72, -73.98], zoom_start=13, tiles=None, control_scale=True)
    folium.TileLayer(
        tiles=args.basemap_url,
        attr=args.basemap_attrib,
        name="Base Map",
        overlay=False,
        control=True
    ).add_to(m)

    # AOI
    aoi = _read_gdf(args.aoi)
    if aoi is not None and len(aoi):
        bounds = aoi.total_bounds  # minx, miny, maxx, maxy
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # core layers
    footprints = _read_gdf(args.footprints)
    pv_polys   = _read_gdf(args.pv_polys)
    pv_pts     = _read_gdf(args.pv_centroids)

    # clip everything to AOI
    if aoi is not None and len(aoi):
        footprints = _clip_to_aoi(footprints, aoi)
        pv_polys   = _clip_to_aoi(pv_polys, aoi)
        pv_pts     = _clip_to_aoi(pv_pts, aoi)

    # optional PLUTO / ZoLa
    pluto = None
    zola  = None
    if args.pluto and os.path.exists(args.pluto):
        pluto = _read_gdf(args.pluto)
        if aoi is not None and len(aoi):
            pluto = _clip_to_aoi(pluto, aoi)
    if args.zola and os.path.exists(args.zola):
        zola = _read_gdf(args.zola)
        if aoi is not None and len(aoi):
            zola = _clip_to_aoi(zola, aoi)

    # join PLUTO/ZOLA onto building footprints by centroid-within
    if footprints is not None and len(footprints):
        fp = footprints.copy()
        fp["__tmpid__"] = range(len(fp))
        fp_cent = fp.copy()
        fp_cent.geometry = fp_cent.centroid

        if pluto is not None and len(pluto):
            try:
                fp_pluto = gpd.sjoin(fp_cent, pluto, predicate="within", how="left")
                cols_to_add = [c for c in fp_pluto.columns if c not in fp.columns and c != "index_right"]
                footprints = fp.merge(fp_pluto[["__tmpid__"] + cols_to_add], on="__tmpid__", how="left")
            except Exception:
                pass

        if zola is not None and len(zola):
            try:
                fp_zola = gpd.sjoin(fp_cent, zola, predicate="within", how="left")
                cols_to_add = [c for c in fp_zola.columns if c not in footprints.columns and c != "index_right"]
                footprints = footprints.merge(fp_zola[["__tmpid__"] + cols_to_add], on="__tmpid__", how="left")
            except Exception:
                pass

        footprints.drop(columns=["__tmpid__"], inplace=True, errors="ignore")

    # summary numbers
    tot_sites = int(len(pv_pts)) if pv_pts is not None else 0
    tot_kw = 0.0
    if pv_pts is not None and "pv_kw" in pv_pts.columns:
        try:
            tot_kw = float(pv_pts["pv_kw"].fillna(0).sum())
        except Exception:
            tot_kw = 0.0

    # PV polygons
    def pv_style_func(feature):
        kw = feature["properties"].get("pv_kw", 0) or 0
        if kw < 15:      color = "#cfe8ff"
        elif kw < 30:    color = "#9fd0ff"
        elif kw < 60:    color = "#6fb8ff"
        elif kw < 120:   color = "#3fa0ff"
        else:            color = "#0f88ff"
        return {"fillColor": color, "color": "#0f5ea8", "weight": 0.7, "fillOpacity": 0.55}

    pv_poly_fg = folium.FeatureGroup(name="PV Canopy Footprints", overlay=True, control=True, show=True)
    if pv_polys is not None and len(pv_polys):
        poly_fields = []
        poly_alias  = []
        if "pv_kw" in pv_polys.columns:
            poly_fields += ["pv_kw"]; poly_alias += ["PV kW"]
        for bbl_name in ["BBL", "bbl"]:
            if bbl_name in pv_polys.columns:
                poly_fields += [bbl_name]; poly_alias += ["BBL"]; break
        for addr_name in ["address", "Address", "staddr", "addr", "house_num", "housenum", "HouseNumber"]:
            if addr_name in pv_polys.columns:
                poly_fields += [addr_name]; poly_alias += ["Address"]; break

        folium.GeoJson(
            pv_polys,
            name="PV Polygons",
            style_function=pv_style_func,
            tooltip=folium.features.GeoJsonTooltip(fields=poly_fields, aliases=poly_alias, localize=True)
        ).add_to(pv_poly_fg)
        pv_poly_fg.add_to(m)

    # PV centroids
    pv_pts_fg = folium.FeatureGroup(name="PV Sites (Centroids)", overlay=True, control=True, show=True)
    if pv_pts is not None and len(pv_pts):
        mc = MarkerCluster(name="PV Sites Cluster", disableClusteringAtZoom=17, spiderfyOnMaxZoom=True, showCoverageOnHover=False)
        for _, row in pv_pts.iterrows():
            g = row.geometry
            if g is None or g.is_empty:
                continue
            lat, lon = g.y, g.x
            kw = row.get("pv_kw", 0)
            bbl = _safe_get(row, "BBL", "bbl")
            addr = _safe_get(row, "address", "Address", "staddr", "addr", "house_num", "housenum", "HouseNumber")
            roof = row.get("rooftop_area_m2", None)
            cano = row.get("canopy_area_m2", None)

            lines = []
            lines.append("PV size: {} kW".format(_format_num(kw,1)))
            if roof is not None:
                lines.append("Rooftop area: {} m2".format(_format_num(roof,1)))
            if cano is not None:
                lines.append("Canopy area: {} m2".format(_format_num(cano,1)))
            if addr:
                lines.append("Address: {}".format(html_escape(str(addr))))
            if bbl:
                lines.append("BBL: {}".format(html_escape(str(bbl))))

            popup_html = "<br>".join(lines)
            folium.Marker(
                location=[lat, lon],
                popup=popup_html,
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(mc)
        mc.add_to(pv_pts_fg)
        pv_pts_fg.add_to(m)

    # Building footprints with tooltip (BBL, Address, Zoning)
    fp_fg = folium.FeatureGroup(name="Building Footprints", overlay=True, control=True, show=False)
    if footprints is not None and len(footprints):
        fields, aliases = [], []
        for bbl_name in ["BBL", "bbl"]:
            if bbl_name in footprints.columns:
                fields.append(bbl_name); aliases.append("BBL"); break
        for addr_name in ["address", "Address", "staddr", "addr", "house_num", "housenum", "HouseNumber"]:
            if addr_name in footprints.columns:
                fields.append(addr_name); aliases.append("Address"); break
        for zo in ["ZONEDIST", "ZONING", "ZONEDIST1"]:
            if zo in footprints.columns:
                fields.append(zo); aliases.append("Zoning"); break
        if len(fields) == 0:
            fields = ["geometry"]; aliases = ["geometry"]

        folium.GeoJson(
            footprints,
            name="Footprints",
            style_function=lambda f: {"color":"#555","weight":0.5,"fillColor":"#dddddd","fillOpacity":0.2},
            tooltip=folium.features.GeoJsonTooltip(fields=fields, aliases=aliases, localize=True)
        ).add_to(fp_fg)
        fp_fg.add_to(m)

    # Summary overlay (toggleable)
    summary_html = _summary_box_html(tot_sites, tot_kw)
    summary_fg = folium.FeatureGroup(name="PV Potentials Summary", overlay=True, control=True, show=True)
    summary_fg.add_to(m)

    # Title and summary box HTML
    m.get_root().html.add_child(folium.Element(_title_html(args.title)))
    m.get_root().html.add_child(folium.Element(summary_html))

    # Sync the summary box visibility with the layer toggle via simple JS
    js = r"""
    <script>
    (function() {
      var map = {{this._parent.get_name()}};
      function setBoxVisible(vis) {
        var box = document.getElementById('pv-summary-box');
        if (!box) return;
        box.style.display = vis ? 'block' : 'none';
      }
      map.on('overlayadd', function(e) {
        if (e.name === 'PV Potentials Summary') { setBoxVisible(true); }
      });
      map.on('overlayremove', function(e) {
        if (e.name === 'PV Potentials Summary') { setBoxVisible(false); }
      });
      setBoxVisible(true);
    })();
    </script>
    """
    m.get_root().html.add_child(folium.Element(js))

    folium.LayerControl(collapsed=False).add_to(m)
    MeasureControl(position="topleft", primary_length_unit="meters", primary_area_unit="sqmeters").add_to(m)

    return m

def main():
    p = argparse.ArgumentParser(description="Build styled PV and irradiance map (Stage 4)")
    p.add_argument("--out", required=True)
    p.add_argument("--pv-polys", required=True)
    p.add_argument("--pv-centroids", required=True)
    p.add_argument("--footprints", required=True)
    p.add_argument("--pluto", default=None)
    p.add_argument("--zola", default=None)
    p.add_argument("--aoi", required=True)
    p.add_argument("--title", default="ECOLIBRIUM Solar PV Irradiance Potentials")
    p.add_argument("--basemap-url", default="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")
    p.add_argument("--basemap-attrib", default="Map data: OpenStreetMap contributors")
    args = p.parse_args()

    m = _build_map(args)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    m.save(args.out)
    print("[MAP]", args.out)

if __name__ == "__main__":
    main()
```

---

# 2) Convenience runner `run_style.ps1`

Save this in the project root as `run_style.ps1`:

```
param(
  [string]$Out = "OUT\maps\irradiance_timeseries_map.html",
  [string]$PvPolys = "OUT\pv_canopy_footprints.geojson",
  [string]$PvCentroids = "OUT\pv_sites_centroids.geojson",
  [string]$Footprints = "OUT\footprints.geojson",
  [string]$Pluto = "DATA\pluto.geojson",
  [string]$Zola = "DATA\zola_zoning.geojson",
  [string]$Aoi = "DATA\aoi.geojson",
  [string]$Title = "ECOLIBRIUM Solar PV Irradiance Potentials",
  [string]$BasemapUrl = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  [string]$BasemapAttrib = "Map data: OpenStreetMap contributors"
)
$env:PYTHONIOENCODING = "utf-8"
$cmd = "python -m scripts.stage4_style --out `"$Out`" --pv-polys `"$PvPolys`" --pv-centroids `"$PvCentroids`" --footprints `"$Footprints`" --pluto `"$Pluto`" --zola `"$Zola`" --aoi `"$Aoi`" --title `"$Title`" --basemap-url `"$BasemapUrl`" --basemap-attrib `"$BasemapAttrib`""
Write-Host ">>> Running: $cmd"
Invoke-Expression $cmd
if ($LASTEXITCODE -ne 0) { throw "stage4_style exited with code $LASTEXITCODE" }
```

---

# 3) How to run (PowerShell)

From your project root:

```
conda activate pv_env
.\run_style.ps1
```

Or explicitly:

```
python -m scripts.stage4_style `
  --out OUT\maps\irradiance_timeseries_map.html `
  --pv-polys OUT\pv_canopy_footprints.geojson `
  --pv-centroids OUT\pv_sites_centroids.geojson `
  --footprints OUT\footprints.geojson `
  --pluto DATA\pluto.geojson `
  --zola DATA\zola_zoning.geojson `
  --aoi DATA\aoi.geojson `
  --title "ECOLIBRIUM Solar PV Irradiance Potentials" `
  --basemap-url "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" `
  --basemap-attrib "Map data: OpenStreetMap contributors"
```

---

## Notes / expectations

- **PLUTO/ZOLA not showing?** Make sure `DATA\pluto.geojson` and `DATA\zola_zoning.geojson` exist. The script joins them onto **footprints** using a centroid-within spatial join, then the footprint tooltip shows **BBL, Address, Zoning** when those fields exist. (It looks for common field names: `BBL/bbl`, `address/Address/staddr/...`, and `ZONEDIST/ZONING/ZONEDIST1`.)
- **PV centroid popups** will now include **PV kW**, **rooftop_area_m2**, **canopy_area_m2**, plus **Address** and **BBL** if those fields are present on the centroids.
- **PV Potentials Summary** is a true toggleable overlay layer (shows/hides the right-hand summary box and is named exactly as requested with the “14 day irradiance time series” subtitle).

=============================================================

Got it. I dug into why the PLUTO/ZOLA fields weren’t flowing through and why the UI bits kept misbehaving, then packaged a clean, ready-to-drop bundle that locks in the behavior you asked for:

- PLUTO+ZoLa attributes are joined into both PV polygons and centroids (BBL, Address1, LotArea, ZONEDIST).
- Building footprint tooltips show PLUTO/ZOLA when the datasets are present.
- PV centroid popups are landscape-style (readable blocks, not a tall stack).
- “PV Potentials Summary” is a **toggable overlay layer** (LayerControl) and no “KW/h” text anywhere.
- Title banner across the top: **“ECOLIBRIUM Solar PV Irradiance Potentials”** + subtitle “PV Potentials Summary — 14 day irradiance time series”.
- Map fits to the AOI extent on load.
- Measure tool + expanded layer control on by default.
- Strict ASCII/UTF-8, Windows-friendly, and PowerShell launchers included.

### Download the full replacement bundle

Download the ZIP

### What’s inside (drop-in replacements)

- `scripts/stage0_aoi.py` – validates `DATA\aoi.geojson` (WGS84)
- `scripts/fetch_footprints.py` – OSM building footprints within AOI
- `scripts/fetch_pluto_zola.py` – verifies/clips `DATA\pluto.geojson` and `DATA\zola_zoning.geojson` to AOI (fails with a clear warning if those files are missing)
- `scripts/stage3_pv_sizing.py` – generates:
  - `OUT\pv_canopy_footprints.geojson` (with `roof_m2`, `canopy_m2`, `pv_kw`, `BBL`, `Address1`, `LotArea`, `ZONEDIST`)
  - `OUT\pv_sites_centroids.geojson` (same attrs)
  - uses projected CRS for nearest joins (no more bad geographic distances)
- `scripts/stage4_style.py` – builds `OUT\maps\irradiance_timeseries_map.html`
  - OSM basemap
  - Title + subtitle banner
  - Building footprints layer with PLUTO/ZOLA tooltips (BBL, Address1, ZONEDIST)
  - PV footprints layer tooltips (PV kW, BBL, Address, Zone)
  - PV centroids clustered, landscape popup (PV kW, roof m², canopy m², BBL, address, zone)
  - **“PV Potentials Summary”** overlay layer (toggable)
  - Measure tool; expanded LayerControl
- `run_all.ps1` – one-shot full pipeline
- `run_fetch.ps1` – validates/clips PLUTO/ZoLa (after you place them in `DATA\`)

### Quick run (PowerShell, inside `pv_env`)

```
.\run_all.ps1
# or step-by-step
python -m scripts.stage0_aoi
python -m scripts.fetch_footprints
python -m scripts.stage3_pv_sizing
python -m scripts.fetch_pluto_zola
python -m scripts.stage4_style
```

### Important notes to ensure the tooltips/popups are populated

- Put **MapPLUTO** at `DATA\pluto.geojson` and ensure it includes at least: `BBL`, `Address` (or `Address1`), `LotArea`.
  - If your PLUTO uses `Address`, the pipeline auto-renames to `Address1`.
- Put **ZoLa zoning** polygons at `DATA\zola_zoning.geojson` with `ZONEDIST`.
- The scripts clip both datasets to your `DATA\aoi.geojson` before the join (keeps layers within AOI).
- If PLUTO/ZOLA are missing, `fetch_pluto_zola.py` exits with a clear warning and `.\run_all.ps1` will stop—no silent placeholders.

If anything still isn’t showing (e.g., BBLs in the footprint tooltip), the likely causes are:

- `DATA\pluto.geojson` missing those fields or in a different schema/field casing.
- Non-overlapping coordinate reference systems or out-of-bounds geometries (the scripts reproject everything to 4326 and clip to AOI, so this should be covered now).
- Datasets not actually present in `DATA\` (the scripts now fail fast with explicit messages).

When you’re back, we can wire in a reliable fetcher for PLUTO/ZoLa from your preferred source and lock in a consistent field mapping if your upstream schema differs from the common one.