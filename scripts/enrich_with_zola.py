#!/usr/bin/env python3
from pathlib import Path
import geopandas as gpd
ZOLA = {
    "zoning_districts": "DATA/zola/zoning_districts.geojson",
    "commercial_overlays": "DATA/zola/commercial_overlays.geojson",
    "special_purpose": "DATA/zola/special_purpose.geojson",
    "limited_height": "DATA/zola/limited_height.geojson",
    "mih": "DATA/zola/mih.geojson",
    "edesignations": "DATA/zola/edesignations.geojson",
    "effective_firm_2007": "DATA/zola/effective_firm_2007.geojson",
    "historic_districts": "DATA/zola/historic_districts.geojson"
}
def load_opt(p):
    pth = Path(p)
    if not pth.exists(): return None
    g = gpd.read_file(str(pth)); 
    if g.crs is None: g = g.set_crs(4326)
    return g.to_crs(4326)
def join_multi(src, over, field, out_col):
    if over is None or over.empty or field not in over.columns: src[out_col] = None; return src
    j = gpd.overlay(src, over[[field, "geometry"]], how="intersection")
    if j.empty: src[out_col] = None; return src
    agg = j.groupby(j.index).agg({field: lambda s: ",".join(sorted({str(x) for x in s if x}))})
    src = src.join(agg, how="left"); src = src.rename(columns={field: out_col}); return src
def join_flag(src, over, out_col):
    if over is None or over.empty: src[out_col] = False; return src
    j = gpd.overlay(src, over[["geometry"]], how="intersection"); flags = j.groupby(j.index).size()
    src[out_col] = src.index.map(lambda i: bool(flags.get(i, 0))); return src
def main():
    cands = [Path("DATA/processed/footprints_selected.geojson"), Path("DATA/processed/footprints.geojson"), Path("outputs/footprints_selected.geojson"), Path("outputs/footprints.geojson"), Path("pv_canopy_footprints.geojson")]
    fp = next((p for p in cands if p.exists()), None)
    if fp is None: raise SystemExit("expected building footprints at DATA/processed/footprints_selected.geojson")
    g = gpd.read_file(str(fp)); 
    if g.crs is None: g = g.set_crs(4326)
    g = g.to_crs(4326).reset_index(drop=True)
    layers = {k: load_opt(v) for k, v in ZOLA.items()}
    g = join_multi(g, layers["zoning_districts"], "ZONEDIST", "zoning_dist")
    g = join_multi(g, layers["commercial_overlays"], "OVERLAY", "commercial_overlay")
    g = join_multi(g, layers["special_purpose"], "SDNAME", "special_purpose")
    g = join_multi(g, layers["limited_height"], "LHNAME", "limited_height")
    g = join_flag(g, layers["mih"], "in_mih")
    g = join_flag(g, layers["edesignations"], "has_edesignation")
    g = join_multi(g, layers["effective_firm_2007"], "FLD_ZONE", "fema_firm_zone")
    g = join_flag(g, layers["historic_districts"], "in_historic_district")
    out_dir = Path("DATA")/"processed"; out_dir.mkdir(parents=True, exist_ok=True)
    g.to_file(str(out_dir/"footprints_enriched_zola.geojson"), driver="GeoJSON")
    cols = [c for c in g.columns if c != "geometry"]; g[cols].to_csv(str(out_dir/"footprints_enriched_zola.csv"), index=False)
    print("wrote", out_dir/"footprints_enriched_zola.geojson"); print("wrote", out_dir/"footprints_enriched_zola.csv")
if __name__ == "__main__": main()
