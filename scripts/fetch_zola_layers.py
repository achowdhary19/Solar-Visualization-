#!/usr/bin/env python3
import json, urllib.parse, urllib.request, time
from pathlib import Path
from shapely.geometry import shape, mapping
from scripts.common_bbox import study_area_bbox, study_area_polygon
ARCGIS_FEATURES = {
    "zoning_districts": "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nyzd/FeatureServer/0",
    "commercial_overlays": "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nyco/FeatureServer/0",
    "special_purpose": "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nysp/FeatureServer/0",
    "limited_height": "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nylh/FeatureServer/0",
    "mih": "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nycmih/FeatureServer/0",
    "edesignations": "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nyedesignations/FeatureServer/0",
    "effective_firm_2007": "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/2007_Effective_FIRMs/FeatureServer/0"
}
OUT_ATTRS = {"zoning_districts":["ZONEDIST"],"commercial_overlays":["OVERLAY"],"special_purpose":["SDNAME","SDLBL"],"limited_height":["LHNAME"],"mih":["MIH"],"edesignations":["ENUMBER","PRIMARY_CEQR_CATEGORY","SUBCATEGORY"],"effective_firm_2007":["FLD_ZONE","ZONE_SUBTY"]}
def query_geojson(url, bbox, fields):
    params = {"where":"1=1","geometry": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}","geometryType":"esriGeometryEnvelope","inSR":"4326","spatialRel":"esriSpatialRelIntersects","outFields":",".join(fields),"returnGeometry":"true","outSR":"4326","f":"geojson"}
    q = url.rstrip('/') + "/query?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(q) as r: return json.loads(r.read().decode("utf-8"))
def clip_to_poly(gj, poly):
    feats = []
    for f in gj.get("features", []):
        try: geom = shape(f.get("geometry"))
        except Exception: continue
        inter = geom.intersection(poly)
        if inter.is_empty: continue
        feats.append({"type":"Feature","geometry":mapping(inter),"properties":dict(f.get("properties") or {})})
    return {"type":"FeatureCollection","features":feats}
def main():
    out_dir = Path("DATA")/"zola"; out_dir.mkdir(parents=True, exist_ok=True)
    bbox = study_area_bbox(); poly = study_area_polygon()
    for key, url in ARCGIS_FEATURES.items():
        fields = OUT_ATTRS.get(key, ["*"]); gj = query_geojson(url, bbox, fields); clipped = clip_to_poly(gj, poly)
        outp = out_dir / f"{key}.geojson"; outp.write_text(json.dumps(clipped), encoding="utf-8"); print("wrote", outp, "features", len(clipped.get("features", []))); time.sleep(0.3)
    print("done.")
if __name__ == "__main__": main()
