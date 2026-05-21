#!/usr/bin/env python3

import json
import urllib.parse
import urllib.request
import time
from pathlib import Path

from shapely.geometry import shape, mapping

# --------------------------------------------------
# MANUAL STUDY AREA / BOUNDING BOX
# --------------------------------------------------
# Change these values directly to control
# the area downloaded from ZoLa / ArcGIS
# --------------------------------------------------

N_LAT = 40.76
S_LAT = 40.69
W_LON = -74.03
E_LON = -73.93

# bbox format:
# [west, south, east, north]

BBOX = [W_LON, S_LAT, E_LON, N_LAT]


# --------------------------------------------------
# OPTIONAL POLYGON CLIPPING
# --------------------------------------------------
# If True:
#     layers are clipped to polygon_coords
#
# If False:
#     layers use ONLY bounding box filtering
# --------------------------------------------------

USE_POLYGON_CLIP = False


# --------------------------------------------------
# OPTIONAL CUSTOM POLYGON AOI
# --------------------------------------------------

polygon_coords = [
    (-73.99075, 40.73474),
    (-73.97209, 40.72689),
    (-73.97770, 40.71314),
    (-73.98249, 40.71468),
    (-73.99411, 40.71371),
    (-73.99484, 40.71580),
    (-73.99860, 40.71711),
    (-74.00187, 40.71939),
    (-73.99143, 40.73179),
    (-73.99075, 40.73474)
]

try:
    from shapely.geometry import Polygon
    STUDY_POLY = Polygon(polygon_coords)
except Exception:
    STUDY_POLY = None


# --------------------------------------------------
# ARCGIS FEATURE SERVICES
# --------------------------------------------------

ARCGIS_FEATURES = {

    "zoning_districts":
        "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nyzd/FeatureServer/0",

    "commercial_overlays":
        "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nyco/FeatureServer/0",

    "special_purpose":
        "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nysp/FeatureServer/0",

    "limited_height":
        "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nylh/FeatureServer/0",

    "mih":
        "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nycmih/FeatureServer/0",

    "edesignations":
        "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nyedesignations/FeatureServer/0",

    "effective_firm_2007":
        "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/2007_Effective_FIRMs/FeatureServer/0",

    # ---------------------------------------
    # NEW REQUESTED LAYERS
    # ---------------------------------------

    # "accessibility_zones":
    #     "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nyza/FeatureServer/0",

    # "manufacturing_districts":
    #     "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nyzd/FeatureServer/0",

    # "residence_districts":
    #     "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nyzd/FeatureServer/0",

    # "parks":
    #     "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/nypp/FeatureServer/0"
}


# --------------------------------------------------
# ATTRIBUTES TO KEEP
# --------------------------------------------------

OUT_ATTRS = {

    "zoning_districts":
        ["ZONEDIST"],

    "commercial_overlays":
        ["OVERLAY"],

    "special_purpose":
        ["SDNAME", "SDLBL"],

    "limited_height":
        ["LHNAME"],

    "mih":
        ["MIH"],

    "edesignations":
        ["ENUMBER", "PRIMARY_CEQR_CATEGORY", "SUBCATEGORY"],

    "effective_firm_2007":
        ["FLD_ZONE", "ZONE_SUBTY"],

    "accessibility_zones":
        ["ZA_CODE"],

    "manufacturing_districts":
        ["ZONEDIST"],

    "residence_districts":
        ["ZONEDIST"],

    "parks":
        ["SIGNNAME"]
}


# --------------------------------------------------
# FETCH GEOJSON FROM ARCGIS
# --------------------------------------------------

def query_geojson(url, bbox, fields):

    params = {
        "where": "1=1",

        "geometry":
            f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",

        "geometryType":
            "esriGeometryEnvelope",

        "inSR":
            "4326",

        "spatialRel":
            "esriSpatialRelIntersects",

        "outFields":
            ",".join(fields),

        "returnGeometry":
            "true",

        "outSR":
            "4326",

        "f":
            "geojson"
    }

    q = (
        url.rstrip("/")
        + "/query?"
        + urllib.parse.urlencode(params)
    )

    print("\nFetching:")
    print(q)

    with urllib.request.urlopen(q) as r:
        return json.loads(r.read().decode("utf-8"))


# --------------------------------------------------
# OPTIONAL CLIP TO POLYGON
# --------------------------------------------------

def clip_to_poly(gj, poly):

    feats = []

    for f in gj.get("features", []):

        try:
            geom = shape(f.get("geometry"))

        except Exception:
            continue

        inter = geom.intersection(poly)

        if inter.is_empty:
            continue

        feats.append({
            "type": "Feature",
            "geometry": mapping(inter),
            "properties": dict(f.get("properties") or {})
        })

    return {
        "type": "FeatureCollection",
        "features": feats
    }


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    out_dir = Path("DATA") / "zola"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n--------------------------------")
    print("BOUNDING BOX")
    print("--------------------------------")
    print(BBOX)

    for key, url in ARCGIS_FEATURES.items():

        print("\n==============================")
        print("LAYER:", key)
        print("==============================")

        # fields = OUT_ATTRS.get(key, ["*"])
        fields = ["*"]

        gj = query_geojson(url, BBOX, fields)

        # ----------------------------------
        # OPTIONAL POLYGON CLIPPING
        # ----------------------------------

        if USE_POLYGON_CLIP and STUDY_POLY is not None:

            print("Applying polygon clip...")

            try:
                gj = clip_to_poly(gj, STUDY_POLY)

            except Exception as e:
                print("Polygon clip failed:", e)

        outp = out_dir / f"{key}.geojson"

        outp.write_text(
            json.dumps(gj),
            encoding="utf-8"
        )

        print(
            "wrote",
            outp,
            "features",
            len(gj.get("features", []))
        )

        time.sleep(0.3)

    print("\nDone.")


if __name__ == "__main__":
    main()