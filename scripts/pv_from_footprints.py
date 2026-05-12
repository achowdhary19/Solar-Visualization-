#!/usr/bin/env python3

import os
from pathlib import Path

import pandas as pd
import geopandas as gpd


# =========================
# CONFIG
# =========================

COVERAGE = float(os.getenv("PV_COVERAGE", "0.85"))
SPECIFIC_POWER = float(os.getenv("PV_SPECIFIC_POWER", "0.20"))     # kW per m²
SPECIFIC_YIELD = float(os.getenv("PV_SPECIFIC_YIELD", "1238.0"))  # kWh per kW per year
PSH_HOURS = float(os.getenv("PV_PSH_HOURS", "4.6"))
AC_DERATE = float(os.getenv("PV_AC_DERATE", "0.80"))

SEL_CSV = "all_walkups_6story.csv"
FP_GEOJSON = "footprints.geojson"


# =========================
# UTILITIES
# =========================

def normalize_bbl(series):
    return (
        series.astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.split(".").str[0]
        .str.strip()
        .str.zfill(10)
    )


def to_utm_area_m2(gdf):
    """Convert geometry to NYC local projection for area calculation."""
    return gdf.to_crs(2263).geometry.area * 0.09290304  # ft² → m²


# =========================
# MAIN PIPELINE
# =========================

def main():

    # -------------------------
    # LOAD DATA
    # -------------------------
    if not Path(SEL_CSV).exists():
        raise FileNotFoundError(f"Missing {SEL_CSV}")

    if not Path(FP_GEOJSON).exists():
        raise FileNotFoundError(f"Missing {FP_GEOJSON}")

    sel = pd.read_csv(SEL_CSV)
    sel.columns = [c.lower() for c in sel.columns]

    fp = gpd.read_file(FP_GEOJSON)

    # -------------------------
    # CLEAN KEYS
    # -------------------------
    sel["bbl"] = normalize_bbl(sel["bbl"])
    fp["bbl"] = normalize_bbl(fp["bbl"])

    # keep only usable footprint rows
    fp = fp.dropna(subset=["geometry"])

    # -------------------------
    # JOIN ATTRIBUTES → GEOMETRY
    # -------------------------
    merged = fp.merge(
        sel.drop(columns=["geometry"], errors="ignore"),
        on="bbl",
        how="inner"
    )

    # -------------------------
    # AREA CALCULATION
    # -------------------------
    merged["roof_area_m2"] = to_utm_area_m2(merged)

    # aggregate per building
    roof_by_bbl = merged.groupby("bbl", as_index=False)["roof_area_m2"].sum()

    merged = merged.drop(columns=["roof_area_m2"]).merge(
        roof_by_bbl,
        on="bbl",
        how="left"
    )

    # -------------------------
    # PV MODEL
    # -------------------------
    pv = merged.copy()

    pv["canopy_area_m2"] = pv["roof_area_m2"] * COVERAGE
    pv["pv_kw_dc"] = pv["canopy_area_m2"] * SPECIFIC_POWER
    pv["annual_kwh"] = pv["pv_kw_dc"] * SPECIFIC_YIELD
    pv["avg_daily_kwh"] = pv["annual_kwh"] / 365.0
    pv["psh_daily_kwh"] = pv["pv_kw_dc"] * PSH_HOURS * AC_DERATE

    # -------------------------
    # OUTPUT TABLE
    # -------------------------
    cols = [
        "bbl",
        "address",
        "bldgclass",
        "numfloors",
        "yearbuilt",
        "roof_area_m2",
        "canopy_area_m2",
        "pv_kw_dc",
        "annual_kwh",
        "avg_daily_kwh",
        "psh_daily_kwh"
    ]

    out = pv[[c for c in cols if c in pv.columns]].copy()

    out.to_csv("pv_footprints_by_building.csv", index=False)

    # -------------------------
    # GEOJSON OUTPUT (FOOTPRINTS WITH PV)
    # -------------------------
    pv_fp = merged.merge(
        out[["bbl", "pv_kw_dc", "annual_kwh", "avg_daily_kwh", "psh_daily_kwh", "canopy_area_m2"]],
        on="bbl",
        how="left"
    )

    pv_fp.to_file("pv_canopy_footprints.geojson", driver="GeoJSON")

    # -------------------------
    # CENTROIDS
    # -------------------------
    centroids = pv_fp.copy()
    centroids["geometry"] = centroids.geometry.centroid

    centroids = centroids.to_crs(4326)

    centroids["lon"] = centroids.geometry.x
    centroids["lat"] = centroids.geometry.y

    centroids.to_file("pv_canopy_centroids.geojson", driver="GeoJSON")

    keep = [
        "bbl",
        "address",
        "pv_kw_dc",
        "annual_kwh",
        "avg_daily_kwh",
        "psh_daily_kwh",
        "canopy_area_m2",
        "roof_area_m2",
        "lat",
        "lon"
    ]

    centroids[keep].to_csv("pv_canopy_centroids.csv", index=False)

    # -------------------------
    # DEBUG OUTPUT
    # -------------------------
    print("Buildings processed:", len(out))
    print("PV footprints:", len(pv_fp))
    print("Centroids:", len(centroids))
    print("Pipeline complete ✔")


if __name__ == "__main__":
    main()