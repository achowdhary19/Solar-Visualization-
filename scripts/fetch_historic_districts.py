#!/usr/bin/env python3

import json
import urllib.parse
import urllib.request
from pathlib import Path

DATASET = "skyk-mpzq"
BASE = "https://data.cityofnewyork.us/resource/"

N_LAT = 40.807402
S_LAT = 40.702263
W_LON = -74.016405
E_LON = -73.963928

# bigger 
# N_LAT =  40.713896
# S_LAT =40.648803
# W_LON =  -74.000534
# E_LON = -73.901401


bbox = [W_LON, S_LAT, E_LON, N_LAT]



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

out = {
    "type": "FeatureCollection",
    "features": gj.get("features", [])
}

outp = Path("historic_districts.geojson")

outp.write_text(
    json.dumps(out),
    encoding="utf-8"
)

print("wrote", outp, "features", len(out["features"]))