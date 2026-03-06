\
@echo off
setlocal
echo Cleaning generated artifacts...
for %%F in ("*.csv" "*.geojson" "*.md" "*.png") do (
  del /q %%F 2>nul
)
if exist maps rd /s /q maps
if exist exports rd /s /q exports
if exist DATA\processed rd /s /q DATA\processed
mkdir DATA\processed 2>nul
call run_notebook.bat
endlocal
