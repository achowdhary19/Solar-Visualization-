#!/usr/bin/env python3
import argparse, pandas as pd
from pathlib import Path
DEF_SEL = "all_walkups_6story.csv"; DEF_PV  = "pv_footprints_by_building.csv"
def main():
    parser = argparse.ArgumentParser(add_help=True, description="Verify expected input files exist and are readable.")
    parser.add_argument("--sel", default=DEF_SEL); parser.add_argument("--pv", default=DEF_PV); args, _u = parser.parse_known_args()
    sel_path = Path(args.sel); pv_path  = Path(args.pv); ok = True
    if not sel_path.exists(): print("[ERROR] Selection CSV not found:", sel_path); ok = False
    else:
        sel = pd.read_csv(sel_path); sel.columns = [c.lower() for c in sel.columns]
        print("[OK] Selection CSV:", sel_path, "rows=", len(sel), "cols=", len(sel.columns))
    if not pv_path.exists(): print("[NOTE] PV CSV not found at:", pv_path)
    else:
        pv = pd.read_csv(pv_path); pv.columns = [c.lower() for c in pv.columns]
        print("[OK] PV CSV:", pv_path, "rows=", len(pv), "cols=", len(pv.columns))
    if not ok: raise SystemExit(1)
if __name__ == "__main__": main()
