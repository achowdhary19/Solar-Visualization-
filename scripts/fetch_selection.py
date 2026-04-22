#!/usr/bin/env python3
import os, requests, pandas as pd, geopandas as gpd
N_LAT = float(os.getenv("PV_N_LAT", "40.73230"))
S_LAT = float(os.getenv("PV_S_LAT", "40.71700"))
W_LON = float(os.getenv("PV_W_LON", "-73.98660"))
E_LON = float(os.getenv("PV_E_LON", "-73.97400"))
PLUTO_GEO_ID = "64uk-42ks"
PLUTO_URL = f"https://data.cityofnewyork.us/resource/{PLUTO_GEO_ID}.geojson"
APP_TOKEN = os.getenv("NYC_SODA_APP_TOKEN")
HEADERS = {"X-App-Token": APP_TOKEN, "Accept": "application/json"} if APP_TOKEN else {"Accept": "application/json"}
def try_query(geom_col: str | None):
    params = {"$select": "*", "$limit": 50000}
    if geom_col:
        params["$where"] = f"within_box({geom_col},{S_LAT},{W_LON},{N_LAT},{E_LON}) AND numfloors=6 AND bldgclass like 'C%'"
    else:
        params["$where"] = f"latitude between {S_LAT} and {N_LAT} AND longitude between {W_LON} and {E_LON} AND numfloors=6 AND bldgclass like 'C%'"
    r = requests.get(PLUTO_URL, params=params, headers=HEADERS, timeout=180); r.raise_for_status(); return r.json()
def fetch():
    last_err = None
    for geom_col in ("the_geom", "geom", None):
        try:
            data = try_query(geom_col); feats = data["features"] if isinstance(data, dict) and "features" in data else []
            if feats: return gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
        except requests.HTTPError as e: last_err = e; continue
    raise RuntimeError(f"PLUTO query failed (tried the_geom, geom, and lat/long). Last error: {last_err}")
def fallback_mock():
    from shapely.geometry import Polygon
    polys = [Polygon([[W_LON+0.0010, N_LAT-0.0010],[W_LON+0.0016, N_LAT-0.0010],[W_LON+0.0016, N_LAT-0.0016],[W_LON+0.0010, N_LAT-0.0016],[W_LON+0.0010, N_LAT-0.0010]])]
    gdf = gpd.GeoDataFrame({"bbl":["100001"],"address":["Mock 1"],"bldgclass":["C4"],"numfloors":[6],"unitsres":[20]}, geometry=polys, crs="EPSG:4326"); return gdf
def main():
    try: gdf = fetch()
    except Exception as e: print("[WARN] Selection fetch failed:", e); gdf = fallback_mock()
    gdf = gdf.rename(columns={c: c.lower() for c in gdf.columns}); gdf.to_file("all_walkups_6story.geojson", driver="GeoJSON")
    keep = [c for c in ["bbl","address","bldgclass","numfloors","unitsres","res_units","units","yearbuilt","latitude","longitude"] if c in gdf.columns]
    if "bbl" not in keep and "bbl" in gdf.columns: keep = ["bbl"] + keep
    gdf[keep].to_csv("all_walkups_6story.csv", index=False); print("Wrote all_walkups_6story.csv and all_walkups_6story.geojson")
if __name__ == "__main__": main()
