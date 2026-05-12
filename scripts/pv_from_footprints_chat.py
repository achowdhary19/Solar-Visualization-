#!/usr/bin/env python3
# im confused and this isn't working . chat version . 
print("RUNNING FILE:", __file__)
"""
PV analysis from selected walkup buildings.

Architecture:
- all_walkups_6story.geojson / csv
    = selected buildings + attributes from PLUTO

- footprints.geojson
    = accurate footprint geometry

Workflow:
1. Load selected buildings (walkups)
2. Load all footprint geometries
3. Match footprints to selected buildings by BBL
4. Calculate roof area ONLY for selected buildings
5. Calculate PV metrics
6. Write PV outputs
"""

import os
from pathlib import Path

import pandas as pd
import geopandas as gpd


# ---------------------------------------------------
# PV assumptions
# ---------------------------------------------------

COVERAGE = float(os.getenv("PV_COVERAGE", "0.85"))
SPECIFIC_POWER = float(os.getenv("PV_SPECIFIC_POWER", "0.20"))
SPECIFIC_YIELD = float(os.getenv("PV_SPECIFIC_YIELD", "1238.0"))
PSH_HOURS = float(os.getenv("PV_PSH_HOURS", "4.6"))
AC_DERATE = float(os.getenv("PV_AC_DERATE", "0.80"))


# ---------------------------------------------------
# Input files
# ---------------------------------------------------

SEL_CSV = "all_walkups_6story.csv"
SEL_GEOJSON = "all_walkups_6story.geojson"
FP_GEOJSON = "footprints.geojson"


# ---------------------------------------------------
# Normalize BBL formatting
# ---------------------------------------------------

def normalize_bbl(series):
    return (
        series.astype(str)
        .str.replace(".0", "", regex=False)
        .str.split(".").str[0]
        .str.strip()
        .str.zfill(10)
    )


# ---------------------------------------------------
# Ensure footprint layer has BBLs
# ---------------------------------------------------

def ensure_bbl(
    fp: gpd.GeoDataFrame,
    lots: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:

    print(fp["bbl"].dtype)
    # already has usable BBLs
    if "bbl" in fp.columns and fp["bbl"].notna().all():
        fp["bbl"] = normalize_bbl(fp["bbl"])
        return fp

    # spatial join fallback
    miss = fp.copy().to_crs(2263)
    lotsp = lots.to_crs(2263)

    joined = gpd.sjoin(
        miss,
        lotsp[["bbl", "geometry"]],
        predicate="intersects",
        how="left"
    )

    joined = joined.drop(
        columns=[c for c in joined.columns if c.startswith("index_")],
        errors="ignore"
    )

    joined = joined.to_crs(4326)

    joined["bbl"] = normalize_bbl(joined["bbl"])

    return joined


# ---------------------------------------------------
# Main
# ---------------------------------------------------

def main():

    # ---------------------------
    # Validate files
    # ---------------------------

    if not Path(SEL_CSV).exists():
        raise FileNotFoundError(f"Missing {SEL_CSV}")

    if not Path(SEL_GEOJSON).exists():
        raise FileNotFoundError(f"Missing {SEL_GEOJSON}")

    if not Path(FP_GEOJSON).exists():
        raise FileNotFoundError(f"Missing {FP_GEOJSON}")


    # ---------------------------
    # Load selected buildings
    # ---------------------------

    sel = pd.read_csv(SEL_CSV)
    sel.columns = [c.lower() for c in sel.columns]



    print(sel["bbl"].dtype)

    sel["bbl"] = normalize_bbl(sel["bbl"])


    # geojson version contains geometry + attributes
    lots = gpd.read_file(SEL_GEOJSON)
    lots.columns = [c.lower() for c in lots.columns]

    print(lots["bbl"].dtype)


    lots["bbl"] = normalize_bbl(lots["bbl"])


    # ---------------------------
    # Load footprint geometry
    # ---------------------------

    fp = gpd.read_file(FP_GEOJSON)
    fp.columns = [c.lower() for c in fp.columns]

    fp = ensure_bbl(fp, lots)


    # ---------------------------------------------------
    # KEY STEP:
    # Keep ONLY selected buildings,
    # but preserve accurate footprint geometry
    # ---------------------------------------------------

    selected_fp = fp.merge(
        sel.drop(
            columns=[c for c in ["geometry"] if c in sel.columns],
            errors="ignore"
        ),
        on="bbl",
        how="inner"
    )


    # ---------------------------------------------------
    # Calculate roof areas
    # ---------------------------------------------------

    areas = selected_fp.to_crs(2263)

    # square feet → square meters
    areas["roof_area_m2_actual"] = (
        areas.geometry.area * 0.09290304
    )

    areas = areas.to_crs(4326)


    # total roof area per building
    per_bbl = areas.groupby(
        "bbl",
        as_index=False
    )["roof_area_m2_actual"].sum()


    # ---------------------------------------------------
    # Merge areas back
    # ---------------------------------------------------

    merged = selected_fp.merge(
        per_bbl,
        on="bbl",
        how="inner"
    )


    # ---------------------------------------------------
    # PV calculations
    # ---------------------------------------------------

    pv = merged.copy()

    pv["canopy_area_m2"] = (
        pv["roof_area_m2_actual"] * COVERAGE
    )

    pv["pv_kw_dc"] = (
        pv["canopy_area_m2"] * SPECIFIC_POWER
    )

    pv["annual_kwh"] = (
        pv["pv_kw_dc"] * SPECIFIC_YIELD
    )

    pv["avg_daily_kwh"] = (
        pv["annual_kwh"] / 365.0
    )

    pv["psh_daily_kwh"] = (
        pv["pv_kw_dc"] * PSH_HOURS * AC_DERATE
    )


    # ---------------------------------------------------
    # CSV output
    # ---------------------------------------------------

    cols = [
        c for c in [
            "bbl",
            "address",
            "bldgclass",
            "numfloors",
            "yearbuilt",
            "roof_area_m2_actual",
            "canopy_area_m2",
            "pv_kw_dc",
            "annual_kwh",
            "avg_daily_kwh",
            "psh_daily_kwh"
        ]
        if c in pv.columns
    ]

    out = (
        pv[cols]
        .sort_values("pv_kw_dc", ascending=False)
    )

    out.to_csv(
        "pv_footprints_by_building.csv",
        index=False
    )


    # ---------------------------------------------------
    # PV footprint polygons
    # ---------------------------------------------------

    attrs = out[
        [
            "bbl",
            "pv_kw_dc",
            "annual_kwh",
            "avg_daily_kwh",
            "psh_daily_kwh",
            "canopy_area_m2"
        ]
    ]

    fp_attr = selected_fp.merge(
        attrs,
        on="bbl",
        how="inner"
    )

    fp_attr.to_file(
        "pv_canopy_footprints.geojson",
        driver="GeoJSON"
    )


    # ---------------------------------------------------
    # PV centroids
    # ---------------------------------------------------

    fp_proj = fp_attr.to_crs(2263)

    gcent = fp_proj.copy()

    gcent["geometry"] = gcent.geometry.centroid

    gcent = gcent.to_crs(4326)

    gcent.to_file(
        "pv_canopy_centroids.geojson",
        driver="GeoJSON"
    )


    # ---------------------------------------------------
    # Centroid CSV
    # ---------------------------------------------------

    gcent2 = gcent.copy()

    gcent2["lon"] = gcent2.geometry.x
    gcent2["lat"] = gcent2.geometry.y

    keep = [
        c for c in [
            "bbl",
            "address",
            "bldgclass",
            "pv_kw_dc",
            "annual_kwh",
            "avg_daily_kwh",
            "psh_daily_kwh",
            "canopy_area_m2",
            "roof_area_m2_actual",
            "lat",
            "lon"
        ]
        if c in gcent2.columns
    ]

    gcent2[keep].to_csv(
        "pv_canopy_centroids.csv",
        index=False
    )


    # ---------------------------------------------------
    # Debugging / sanity checks
    # ---------------------------------------------------

    print()
    print("===== PV PIPELINE SUMMARY =====")

    print("Selected buildings (CSV rows):", len(sel))
    print("Selected buildings unique BBLs:", sel["bbl"].nunique())

    print()

    print("Selected footprints rows:", len(selected_fp))
    print("Selected footprints unique BBLs:",
          selected_fp["bbl"].nunique())

    print()

    print("PV footprints rows:", len(fp_attr))
    print("PV footprints unique BBLs:",
          fp_attr["bbl"].nunique())

    print()

    print(
        "Missing addresses in PV footprints:",
        fp_attr["address"].isna().sum()
    )

    print()

    print("PV artifacts written.")


if __name__ == "__main__":
    main()