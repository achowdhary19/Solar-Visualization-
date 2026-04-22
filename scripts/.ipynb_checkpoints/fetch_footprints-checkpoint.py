#!/usr/bin/env python3
# scripts/fetch_footprints.py

import os
import json
import requests
import geopandas as gpd

from shapely.geometry import shape, Polygon, MultiPolygon, GeometryCollection
from shapely.errors import TopologicalError
from shapely.ops import polygonize, unary_union

# ---------------------------
# Study area (env overrides)
# ---------------------------
N_LAT = float(os.getenv("PV_N_LAT", "40.73230"))
S_LAT = float(os.getenv("PV_S_LAT", "40.71700"))
W_LON = float(os.getenv("PV_W_LON", "-73.98660"))
E_LON = float(os.getenv("PV_E_LON", "-73.97400"))

# Drop polygons smaller than this area (m^2)
MIN_AREA_M2 = float(os.getenv("PV_MIN_POLY_AREA_M2", "1.0"))

# ---------------------------
# Socrata dataset
# ---------------------------
FOOTPRINTS_ID = "5zhs-2jue"
FOOTPRINTS_URL = f"https://data.cityofnewyork.us/resource/{FOOTPRINTS_ID}.geojson"

APP_TOKEN = os.getenv("NYC_SODA_APP_TOKEN", "").strip()
HEADERS = {"Accept": "application/json"}
if APP_TOKEN:
    HEADERS["X-App-Token"] = APP_TOKEN

# ---------------------------
# make_valid compatibility
# ---------------------------
try:
    from shapely import make_valid  # Shapely 2.x
except Exception:
    def make_valid(geom):
        try:
            return geom.buffer(0)
        except Exception:
            return geom

# ---------------------------
# Helpers
# ---------------------------
def _params_where(geom_col):
    if geom_col:
        where = f"within_box({geom_col},{S_LAT},{W_LON},{N_LAT},{E_LON})"
    else:
        where = f"latitude between {S_LAT} and {N_LAT} AND longitude between {W_LON} and {E_LON}"
    return {"$select": "*", "$where": where, "$limit": 50000}

def _fetch_geojson(geom_col):
    r = requests.get(FOOTPRINTS_URL, params=_params_where(geom_col), headers=HEADERS, timeout=180)
    r.raise_for_status()
    return r.json()

def _to_float(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x)
        except ValueError:
            return x
    if isinstance(x, (list, tuple)):
        return [_to_float(v) for v in x]
    if isinstance(x, dict):
        return {k: _to_float(v) for k, v in x.items()}
    return x

def _validate_soft(geom):
    try:
        return (not geom.is_empty) and (geom.area > 0)
    except Exception:
        return False

def _extract_polygons(geom):
    if geom is None or geom.is_empty:
        return None
    try:
        gv = make_valid(geom)
    except Exception:
        gv = geom
    if isinstance(gv, (Polygon, MultiPolygon)) and (gv.is_valid or _validate_soft(gv)):
        return gv
    if isinstance(gv, GeometryCollection):
        polys = [g for g in gv.geoms if isinstance(g, (Polygon, MultiPolygon))]
        if polys:
            try:
                u = unary_union(polys)
                if isinstance(u, (Polygon, MultiPolygon)) and (u.
tures(gj, crs="EPSG:4326")
    gdf.to_file("footprints.geojson", driver="GeoJSON")
    print("Wrote footprints.geojson with {} features".format(len(gdf)))

if __name__ == "__main__":
    main()
nts.geojson", driver="GeoJSON")
    print(f"Wrote footprints.geojson with {len(gdf)} features")

if __name__ == "__main__":
    main()
