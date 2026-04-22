#!/usr/bin/env python3
import argparse, pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
DEF_PV = "pv_footprints_by_building.csv"; DEF_SEL = "all_walkups_6story.csv"
def main():
    parser = argparse.ArgumentParser(add_help=True); parser.add_argument("--pv", default=DEF_PV); parser.add_argument("--sel", default=DEF_SEL); args, _u = parser.parse_known_args()
    pv_path = Path(args.pv); sel_path = Path(args.sel)
    if not pv_path.exists(): raise FileNotFoundError("Missing PV CSV: " + str(pv_path))
    pv = pd.read_csv(pv_path); pv.columns = [c.lower() for c in pv.columns]
    req = {"bbl","pv_kw_dc","annual_kwh"}; 
    if not req.issubset(pv.columns): raise KeyError("PV CSV missing required columns: " + str(req))
    total_buildings = len(pv); total_pv_kw = float(pv["pv_kw_dc"].sum()); total_pv_kwh = float(pv["annual_kwh"].sum())
    total_units = None
    if sel_path.exists():
        sel = pd.read_csv(sel_path); sel.columns = [c.lower() for c in sel.columns]
        unit_cols = [c for c in ["unitsres","res_units","units"] if c in sel.columns]
        if unit_cols: total_units = int(sel[unit_cols[0]].fillna(0).sum())
    lines = ["# Aggregate Totals","","## Bulleted Summary",
             "- Total buildings in select set: " + f"{total_buildings:,}",
             "- Total apartments (units): " + (f"{total_units:,}" if total_units is not None else "n/a"),
             "- Aggregate solar PV capacity (kW DC): " + f"{total_pv_kw:,.1f} kW",
             "- Aggregate solar PV annual generation (kWh): " + f"{total_pv_kwh:,.0f} kWh","",
             "## Table","| Metric | Value |","|---|---:|",
             "| Number of 6-story buildings | " + f"{total_buildings:,}" + " |",
             "| Total residential units (apartments) | " + (f"{total_units:,}" if total_units is not None else "n/a") + " |",
             "| Rooftop PV capacity (kW DC) | " + f"{total_pv_kw:,.1f}" + " |",
             "| PV annual generation (kWh) | " + f"{total_pv_kwh:,.0f}" + " |"]
    Path("totals_summary.md").write_text("\n".join(lines), encoding="utf-8")
    labels = ["Buildings","Apartments" if total_units is not None else "Apartments (n/a)","PV kW (DC)","Annual kWh"]
    values = [total_buildings, total_units if total_units is not None else 0, total_pv_kw, total_pv_kwh]
    plt.figure(figsize=(8,5)); plt.bar(labels, values); plt.title("Aggregate Totals - LES / East Village / Chinatown (6-story walk-ups)")
    plt.ylabel("Value"); plt.xticks(rotation=20); plt.tight_layout(); plt.savefig("totals_bar.png", dpi=150); plt.close()
    print("Wrote totals_summary.md and totals_bar.png")
if __name__ == "__main__": main()
