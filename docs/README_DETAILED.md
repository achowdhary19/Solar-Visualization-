# README_DETAILED — PV Systematic v4 (Full Pipeline)

**Includes:** core PV pipeline, ZoLa overlays, enrichment, QA, auto-export, reset helper. ASCII-only code.

## Quick Start (Windows 11 + Anaconda)
```bat
conda config --add channels conda-forge
conda config --set channel_priority strict
conda env create -f environment_win.yml
conda activate pv_env
python -m ipykernel install --user --name pv_env --display-name "Python 3 (pv_env)"
run_notebook.bat
```

### Run Order
PV_Systematic_TestRig.ipynb → Stages 1..10 (Stage 10 exports to exports/<timestamp>)

### Reset
Use reset_project.bat to clean outputs and relaunch.

### Notes
- Socrata geometry auto-detect (the_geom/geom/lat+lon)
- within_box order fixed (south, west, north, east)
- Centroids in EPSG:2263 projected to 4326
- Jupyter-safe argparse
- QA checklist
- Auto-export stamp folder
