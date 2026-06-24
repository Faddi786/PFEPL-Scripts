@echo off
cd /d "%~dp0"
echo Filling all missing and zero discharge automatically...
echo.
python fill_auto.py
echo.
if exist "output\ulhas_discharge_filled.xlsx" (
    echo Opening output file...
    start "" "output\ulhas_discharge_filled.xlsx"
) else (
    echo Output file was not created. Check errors above.
)
pause
