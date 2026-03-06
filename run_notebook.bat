\
@echo off
setlocal
set ENV_NAME=pv_env
set NB=PV_Systematic_TestRig.ipynb
call conda activate %ENV_NAME%
if errorlevel 1 (
  echo [INFO] Could not activate %ENV_NAME%. If using venv, run: .venv\Scripts\activate
)
jupyter lab "%CD%\%NB%"
endlocal
