# pv-potentials-3d — Ruleset v1.0 (Windows-first)

**Date:** 2025-10-07  
 **Scope:** Prevent repeat errors; standardize environment, paths, CRS handling, and notebooks; ensure 3D map reliability; mirror the last known-good reference package patterns.

---

## 1) Environment & Launch (Windows-first)

- Work from **Anaconda PowerShell Prompt** with the env active:
  - `conda activate pvpot3d`
  - Launch Jupyter **from the env** (avoid `conda run` for Jupyter):  
     `jupyter lab notebooks\<the_notebook>.ipynb`
- Make the env self-contained:
  - `conda install -n pvpot3d -c conda-forge proj proj-data pyproj ipykernel`
  - `python -m ipykernel install --user --name pvpot3d --display-name "Python (pvpot3d)"`
- If using a `.bat` launcher, it must:
  1. `call "%CONDA_ROOT%\Scripts\activate.bat" "%CONDA_PREFIX%"`
  2. `conda activate pvpot3d`
  3. `jupyter lab notebooks\00_bootstrap.ipynb`  
      Never assume `conda` is on PATH without activation.

## 2) PROJ / CRS (root cause of many crashes)

- **Never** import `pyproj`/`geopandas` before setting PROJ path (first cell in every notebook):
  - Set `PROJ_LIB=%CONDA_PREFIX%\Library\share\proj`
  - Set `PYPROJ_NETWORK=OFF`
  - Programmatically: detect `sys.prefix` → set `os.environ["PROJ_LIB"]` → `pyproj.datadir.set_data_dir(...)`.
- Prefer **Proj4 CRS strings** for core steps (e.g., `+proj=utm +zone=18 ...`) so we don’t depend on EPSG DB. Use `EPSG:` only after a sanity check.
- If a source file has **no CRS**, never guess silently:
  - MapPLUTO fallback (documented): **NAD83 / New York Long Island (ft-US)** Proj4.
  - 3D buildings: do **not** assume; require explicit CRS from metadata or skip with a clear warning.

**Top cell template (paste as Cell 0 in every notebook):**

```
# Step 0 — PROJ bootstrap (PowerShell-friendly)
import os, sys, pathlib, warnings
os.environ["PYPROJ_NETWORK"] = "OFF"
for c in [pathlib.Path(sys.prefix)/"Library"/"share"/"proj", pathlib.Path(sys.prefix)/"share"/"proj"]:
    if c.exists():
        os.environ["PROJ_LIB"] = str(c); break
from pyproj import datadir
if os.environ.get("PROJ_LIB"):
    try: datadir.set_data_dir(os.environ["PROJ_LIB"])
    except Exception as e: print("[WARN] set_data_dir failed:", e)
warnings.filterwarnings("ignore", message="pyproj unable to set PROJ database path.", category=UserWarning, module="pyproj")
print("PYPROJ_NETWORK:", os.environ.get("PYPROJ_NETWORK"))
print("PROJ_LIB:", os.environ.get("PROJ_LIB"))
print("pyproj dir:", datadir.get_data_dir())
```

## 3) Directory Structure (standardize & never deviate)

Mirror the reference package layout:

```
project_root/
  env/environment.yml
  config/config.yaml
  data_raw/           # unmodified inputs (gpkg/shp/gdb/tiles)
  data_work/          # parquet, clipped/intermediate
  notebooks/
  scripts/
  outputs/            # logs, figures, exports
  web/                # tiles/static assets for map
```

- **Never** read/write outside `project_root`.
- Use `pathlib.Path` + config keys; **no** hard-coded absolute paths.

## 4) Config Schema (defensive & explicit)

`config/config.yaml` must include:

```
project: { crs_analysis, crs_display, aoi_name }
aoi_bbox_wgs84: { min_lon, min_lat, max_lon, max_lat }
paths: { raw_dir, work_dir }
data_sources: { mappluto: [...], nyc_3d_buildings: [...] }
```

- On load, **merge defaults** so missing keys don’t crash.
- Validate types & ranges; fail with a clear message.

## 5) Data Ingest (robust, not brittle)

- **Primary**: user-supplied files in `data_raw/` (manual drop-in takes precedence).
- **Optional** auto-fetch: treat as best-effort; if a landing page changes, **log & stop** with guidance.
- GDB support: require `fiona`; list layers; select by name heuristic; log chosen layer.

## 6) Geometry Handling (safe & reproducible)

- Force **2D** before spatial ops (drop Z).
- Reproject **after** CRS is known & validated; print source/target CRS to logs.
- Clip flow:
  1. Build AOI in WGS84 Proj4 → reproject to **UTM 18N Proj4** (metric analysis CRS).
  2. Reproject sources → AOI CRS.
  3. `geopandas.clip` with explicit checks (empty result → warn, don’t crash).

**Proj4 strings used:**

- WGS84: `+proj=longlat +datum=WGS84 +no_defs +type=crs`
- UTM 18N: `+proj=utm +zone=18 +datum=WGS84 +units=m +no_defs +type=crs`
- MapPLUTO fallback:  
   `+proj=lcc +lat_1=41.03333333333333 +lat_2=40.66666666666666 +lat_0=40.16666666666666 +lon_0=-74 +x_0=300000.0 +y_0=0.0 +datum=NAD83 +units=us-ft +no_defs +type=crs`

## 7) Logging & Error Hygiene

- Every script/notebook step prints `[INFO]/[WARN]/[ERROR]` for:
  - Paths used; CRS in/out; row counts; elapsed times.
- Append exceptions to `outputs/errors_history.log` with timestamps.
- Never swallow exceptions silently; include the **actionable next step**.

## 8) Notebook Conventions (Jupyter Lab)

- **Cell 0**: PROJ bootstrap (env vars + datadir) — **must run first**.
- **Cell 1**: versions (Python, geopandas, shapely, pyproj).
- **Cell 2**: config load + default merge; echo effective config.
- Cells are **idempotent** (safe to re-run).
- Avoid reliance on magics (`%%writefile`) when uncertain; prefer `Path.write_text()`.

## 9) Windows-Specific Rules

- PowerShell vs Bash: use PowerShell here-strings & pipes (`$py | python -`) in docs.
- Quote paths with spaces; prefer `Path` joins.
- Don’t assume Git is installed; avoid Git-dependent steps unless required.

## 10) 3D Map Rendering (why prior attempts failed & the fix)

- `ipyleaflet` is primarily **2D**; true 3D/tiling needs **pydeck/deck.gl** (or Cesium/kepler.gl).
- New workflow:
  1. **Prove the viewer first**: minimal **pydeck** notebook with `PolygonLayer` and `get_elevation` working (interactive).
  2. Then connect NYC data; finally add timeseries/irradiance logic.
- If 3D tiles are needed: use deck.gl **Tile3DLayer** and test with a tiny sample.
- Always maintain a **2D fallback** (choropleth by irradiance) to keep progress unblocked by WebGL.

## 11) Style, Toggles, Tools

- Each layer gets a **toggle**, **legend**, and short **help** tooltip.
- Tools: **distance measure**, **selection** (single/multi), **canopy % slider** (applies to current selection).
- Default AOI: Lower Manhattan (14th St → Canal St, east to FDR), via config.

## 12) Solar Workflow (data & algorithms)

- Timeseries ingestion: validate timestamps, timezone, units; document resampling.
- Shadow/light (phase 1): simplified horizon/extrusion around roofs to estimate daily/seasonal envelopes; document assumptions.
- PV potential: expose assumptions (panel efficiency, derate, canopy %) and allow overrides per run.

## 13) Quality Gates (strict code checking)

- `black` + `ruff` pre-commit; move reusable logic to `scripts/`.
- Sanity cell assertions:
  - `proj.db` is reachable *or* Proj4 fallback active,
  - AOI CRS is **projected** (meters),
  - Outputs exist & have **> 0** rows.

## 14) Path/Name Mistakes to Avoid

- Always build paths via `Path(root)/"scripts"/"clip_aoi.py"`.
- When using `runpy.run_module`, insert `project_root` into `sys.path` first.
- Double-check path separators and quoted strings (PowerShell).

---

## Reference Package Elements to Mirror

- Canonical folder layout (env/config/notebooks/scripts/data_raw/data_work/outputs).
- Startup pattern (`00_bootstrap.ipynb` + launcher) — keep, but prefer launching from an **activated** env.
- Environment pinning via `env/environment.yml` — keep; ensure `proj` + `proj-data`.

---

## Pause Point — Quick Summary for Review

- Launch from **pvpot3d** env; kernel **Python (pvpot3d)**.
- Set **PROJ** before imports; use **Proj4** strings; avoid EPSG reliance.
- Standardize dirs/config; defensive CRS & clipping; verbose logs.
- Validate **pydeck** 3D with a tiny synthetic layer first; keep a 2D fallback.

**Next choice (your call):**

1. Mirror the reference env pins/launcher **verbatim**; or
2. Build a minimal **pydeck 3D “proof” notebook** to validate WebGL & interactivity before wiring NYC data.