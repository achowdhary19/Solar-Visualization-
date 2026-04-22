#!/usr/bin/env python3
import json, urllib.parse, urllib.request
from pathlib import Path
from shapely.geometry import shape, mapping
from scripts.common_bbox import study_area_bbox, study_area_polygon
DATASET = "skyk-mpzq"; BASE = "https://data.cityofnewyork.us/resource/"
def main():
    bbox = study_area_bbox()
    where = "within_box(the_geom,{},{},{},{})".format(bbox[1], bbox[0], bbox[3], bbox[2])
    params = {"$select":"*", "$where": where, "$limit": 50000}
    url = BASE + DATASET + ".geojson?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url) as r: gj = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print("historic districts fetch failed:", e); return
    poly = study_area_polygon(); out_feats = []
    for f in gj.get("features", []):
        try: geom = shape(f.get("geometry"))
        except Exception: continue
        inter = geom.intersection(poly)
        if inter.is_empty: continue
        out_feats.append({"type":"Feature","geometry":mapping(inter),"properties":dict(f.get("properties") or {})})
    out = {"type":"FeatureCollection","features":out_feats}
    outp = Path("DATA")/"zola"/"historic_districts.geojson"; outp.parent.mkdir(parents=True, exist_ok=True); outp.write_text(json.dumps(out), encoding="utf-8")
    print("wrote", outp, "features", len(out_feats))
if __name__ == "__main__": main()
