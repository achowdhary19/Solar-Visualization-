#!/usr/bin/env python3
import os, pandas as pd, geopandas as gpd
from pathlib import Path
COVERAGE = float(os.getenv("PV_COVERAGE", "0.85"))
SPECIFIC_POWER = float(os.getenv("PV_SPECIFIC_POWER", "0.20"))
SPECIFIC_YIELD = float(os.getenv("PV_SPECIFIC_YIELD", "1238.0"))
PSH_HOURS = float(os.getenv("PV_PSH_HOURS", "4.6"))
AC_DERATE = float(os.getenv("PV_AC_DERATE", "0.80"))
SEL_CSV = "all_walkups_6story.csv"
FP_GEOJSON = "footprints.geojson"
def ensure_bbl(fp: gpd.GeoDataFrame, lots: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    import geopandas as gpd
    if "bbl" in fp.columns and fp["bbl"].notna().all():
        fp["bbl"] = fp["bbl"].astype(str); return fp
    if "bbl" not in lots.columns:
        for c in lots.columns:
            if c.lower() == "bbl": lots = lots.rename(columns={c:"bbl"}); break
    lots["bbl"] = lots["bbl"].astype(str)
    miss = fp.copy().to_crs(2263); lotsp = lots.to_crs(2263)
    j = gpd.sjoin(miss, lotsp[["bbl","geometry"]], predicate="intersects", how="left")
    j = j.drop(columns=[c for c in j.columns if c.startswith("index_")], errors="ignore").to_crs(4326)
    j["bbl"] = j["bbl"].astype(str); return j
def main():
    if not Path(SEL_CSV).exists(): raise FileNotFoundError("Selection CSV not found: " + SEL_CSV)
    if not Path(FP_GEOJSON).exists(): raise FileNotFoundError("Footprints GeoJSON not found: " + FP_GEOJSON)
    sel = pd.read_csv(SEL_CSV); sel.columns = [c.lower() for c in sel.columns]; sel["bbl"] = sel["bbl"].astype(str)
    fp = gpd.read_file(FP_GEOJSON)
    lots = gpd.read_file("all_walkups_6story.geojson") if Path("all_walkups_6story.geojson").exists() else None
    if lots is None:
        from shapely.geometry import Point
        lots = gpd.GeoDataFrame(sel, geometry=[Point(-73.98,40.72)]*len(sel), crs="EPSG:4326")
    fp = ensure_bbl(fp, lots)
    areas = fp.to_crs(2263); areas["roof_area_m2_actual"] = areas.geometry.area * 0.09290304; areas = areas.to_crs(4326)
    per_bbl = areas.groupby("bbl", as_index=False)["roof_area_m2_actual"].sum()
    merged = sel.merge(per_bbl, on="bbl", how="inner")
    pv = merged.copy(); pv["canopy_area_m2"] = pv["roof_area_m2_actual"] * COVERAGE; pv["pv_kw_dc"] = pv["canopy_area_m2"] * SPECIFIC_POWER
    pv["annual_kwh"] = pv["pv_kw_dc"] * SPECIFIC_YIELD; pv["avg_daily_kwh"] = pv["annual_kwh"] / 365.0; pv["psh_daily_kwh"] = pv["pv_kw_dc"] * PSH_HOURS * AC_DERATE
    cols = [c for c in ["bbl","address","bldgclass","numfloors","yearbuilt","roof_area_m2_actual","canopy_area_m2","pv_kw_dc","annual_kwh","avg_daily_kwh","psh_daily_kwh"] if c in pv.columns]
    out = pv[cols].sort_values("pv_kw_dc", ascending=False); out.to_csv("pv_footprints_by_building.csv", index=False)
    attrs = out[["bbl","pv_kw_dc","annual_kwh","avg_daily_kwh","psh_daily_kwh","canopy_area_m2"]]
    fp_attr = fp.merge(attrs, on="bbl", how="inner").to_crs(4326)
    if "address" in sel.columns or "bldgclass" in sel.columns: fp_attr = fp_attr.merge(sel[["bbl","address","bldgclass"]].drop_duplicates(), on="bbl", how="left")
    fp_attr.to_file("pv_canopy_footprints.geojson", driver="GeoJSON")
    fp_proj = fp_attr.to_crs(2263).copy(); gcent = fp_proj.copy(); gcent["geometry"] = gcent.geometry.centroid; gcent = gcent.to_crs(4326)
    gcent.to_file("pv_canopy_centroids.geojson", driver="GeoJSON"); gcent2 = gcent.copy(); gcent2["lon"] = gcent2.geometry.x; gcent2["lat"] = gcent2.geometry.y
    keep = [c for c in ["bbl","address","bldgclass","pv_kw_dc","annual_kwh","avg_daily_kwh","psh_daily_kwh","canopy_area_m2","roof_area_m2_actual","lat","lon"] if c in gcent2.columns]
    gcent2[keep].to_csv("pv_canopy_centroids.csv", index=False); print("PV artifacts written.")
if __name__ == "__main__": main()
