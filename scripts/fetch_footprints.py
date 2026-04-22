#!/usr/bin/env python3
# scripts/fetch_footprints.py — v4-11a
# Robust Socrata fetch for NYC Building Footprints (5zhs-2jue) with multi-column fallback.

import os, json, requests, geopandas as gpd
from shapely.geometry import shape, Polygon, MultiPolygon

N_LAT = float(os.getenv("PV_N_LAT", "40.73230"))
S_LAT = float(os.getenv("PV_S_LAT", "40.71700"))
W_LON = float(os.getenv("PV_W_LON", "-73.98660"))
E_LON = float(os.getenv("PV_E_LON", "-73.97400"))
PV_DEBUG = os.getenv("PV_DEBUG", "0") == "1"

# keep tiny features unless explicitly set higher (prevents over-pruning)
MIN_AREA_M2 = float(os.getenv("PV_MIN_POLY_AREA_M2", "0.1"))

FOOTPRINTS_URL = "https://data.cityofnewyork.us/resource/5zhs-2jue.geojson"
APP_TOKEN = os.getenv("NYC_SODA_APP_TOKEN", "").strip()
HEADERS = {"Accept": "application/json"}
if APP_TOKEN:
    HEADERS["X-App-Token"] = APP_TOKEN

GEOM_COLS = ["the_geom", "geom", "geometry"]

def _params(col):
    # within_box(south, west, north, east)
    w = f"within_box({col}, {S_LAT}, {W_LON}, {N_LAT}, {E_LON})"
    return {"$select":"*", "$where": w, "$limit": 50000}

def _to_float(x):
    if isinstance(x, (int,float)): return float(x)
    if isinstance(x, str):
        try: return float(x)
        except ValueError: return x
    if isinstance(x, (list,tuple)): return [_to_float(v) for v in x]
    if isinstance(x, dict): return {k:_to_float(v) for k,v in x.items()}
    return x

def _clean_features(feats):
    kept=[]; c_none=c_notpoly=c_invalid=c_sliver=0
    for f in feats:
        g = f.get("geometry")
        if not g: c_none += 1; continue
        g = _to_float(g)
        try:
            geom = shape(g)
        except Exception:
            c_invalid += 1; continue
        if not isinstance(geom, (Polygon, MultiPolygon)):
            c_notpoly += 1; continue
        if geom.is_empty:
            c_invalid += 1; continue
        # area guard (EPSG:2263 feet -> m2)
        try:
            a_ft2 = gpd.GeoDataFrame(geometry=[geom], crs=4326).to_crs(2263).area.iloc[0]
            if a_ft2 * 0.09290304 < MIN_AREA_M2:
                c_sliver += 1; continue
        except Exception:
            pass
        kept.append({
            "type":"Feature",
            "geometry": json.loads(json.dumps(geom.__geo_interface__)),
            "properties": f.get("properties") or {}
        })
    if PV_DEBUG:
        print(f"[DEBUG] Cleaned: kept={len(kept)} none={c_none} notpoly={c_notpoly} invalid={c_invalid} sliver={c_sliver}")
    return kept

def _try_fetch(col):
    params = _params(col)
    if PV_DEBUG:
        from urllib.parse import urlencode
        print("[DEBUG] URL:", FOOTPRINTS_URL + "?" + urlencode(params))
    r = requests.get(FOOTPRINTS_URL, params=params, headers=HEADERS, timeout=180)
    r.raise_for_status()
    gj = r.json()
    feats = gj.get("features") or []
    kept = _clean_features(feats)
    return kept

def main():
    kept = []
    last_err = None
    for col in GEOM_COLS:
        try:
            kept = _try_fetch(col)
            if kept:
                break
        except Exception as e:
            last_err = e
            if PV_DEBUG:
                print(f"[DEBUG] Attempt with {col} failed:", e)

    if kept:
        gdf = gpd.GeoDataFrame.from_features({"type":"FeatureCollection","features":kept}, crs=4326)
        gdf.to_file("footprints.geojson", driver="GeoJSON")
        print(f"Wrote footprints.geojson with {len(gdf)} features")
        return

    # final fallback: small mock so pipeline continues
    from shapely.geometry import Polygon
    p1 = Polygon([[W_LON+0.0013, N_LAT-0.0013],[W_LON+0.0016, N_LAT-0.0013],[W_LON+0.0016, N_LAT-0.0016],[W_LON+0.0013, N_LAT-0.0016]])
    p2 = Polygon([[W_LON+0.0018, N_LAT-0.0014],[W_LON+0.0021, N_LAT-0.0014],[W_LON+0.0021, N_LAT-0.0017],[W_LON+0.0018, N_LAT-0.0017]])
    gpd.GeoDataFrame({"mock_id":[1,2]}, geometry=[p1,p2], crs=4326).to_file("footprints.geojson", driver="GeoJSON")
    print("[WARN] Footprints query failed; wrote 2 mock squares. Set PV_DEBUG=1 and re-run to see URLs.")
    if last_err:
        print("[WARN] Last error:", last_err)

if __name__ == "__main__":
    main()
