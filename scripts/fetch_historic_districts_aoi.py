#!/usr/bin/env python3

import json
import urllib.parse
import urllib.request
from pathlib import Path

from shapely.geometry import shape, mapping, Polygon

DATASET = "skyk-mpzq"
BASE = "https://data.cityofnewyork.us/resource/"

# use notebook bbox values
N_LAT = 40.7358876957036
S_LAT = 40.71195687391828
W_LON = -74.00188877257987
E_LON = -73.9721415592451
bbox = [W_LON, S_LAT, E_LON, N_LAT]

# use notebook polygon coordinates
polygon_coords = [
    (-73.99075, 40.73474), #A: 14th & Broadway 
    ( -73.97209, 40.72689), #B: 14th and FDR 
    (-73.9777,  40.71314), #C: Grand & FDR 
    (-73.98249,  40.71468), #D: Grand and E Broadway  
    (-73.99411, 40.71371), # E : E broadway and Manhattan Bridge  
    (-73.99484, 40.7158), #F: Canal and Manhattan bridge
    (-73.9986, 40.71711),  # G: Canal and Mulberry  
    (-74.00187, 40.71939),  # H: Canal and Broadway  
    (-73.99143, 40.73179),  # I: Broadway and 10th 
     (-73.99075, 40.73474)  #A: 14th & Broadway, close polygon
]
poly = Polygon(polygon_coords)

where = "within_box(the_geom,{},{},{},{})".format(
    bbox[1],
    bbox[0],
    bbox[3],
    bbox[2]
)

params = {
    "$select": "*",
    "$where": where,
    "$limit": 50000
}

url = BASE + DATASET + ".geojson?" + urllib.parse.urlencode(params)

try:
    with urllib.request.urlopen(url) as r:
        gj = json.loads(r.read().decode("utf-8"))

except Exception as e:
    print("historic districts fetch failed:", e)

out_feats = []

for f in gj.get("features", []):

    try:
        geom = shape(f.get("geometry"))

    except Exception:
        continue

    inter = geom.intersection(poly)

    if inter.is_empty:
        continue

    out_feats.append({
        "type": "Feature",
        "geometry": mapping(inter),
        "properties": dict(f.get("properties") or {})
    })

out = {
    "type": "FeatureCollection",
    "features": out_feats
}

outp = Path("historic_districts.geojson")

outp.write_text(
    json.dumps(out),
    encoding="utf-8"
)

print("Wrote to {}".format(outp), "features", len(out_feats))