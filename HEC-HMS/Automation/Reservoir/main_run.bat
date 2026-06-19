@echo off
echo.
echo ==================================================
echo     STARTING HEC-HMS AUTOMATION
echo ==================================================
echo.

:: Change to your project folder
cd /d "C:\Users\Swapnali\Desktop\Sakina Maam Work\Trial_2"

:: This is the magic line for Anaconda users (works 100% of the time)
call "%USERPROFILE%\miniconda3\Scripts\activate.bat" hmsenv

:: Optional: show that everything is loaded
echo.
echo Checking if all packages are available...
python -c "import pandas, openpyxl, pydsstools; print('All packages loaded successfully!')" 2>nul || echo ERROR: pydsstools missing!

echo.
echo ==================================================
echo               RUNNING CONFIG.PY
echo ==================================================
echo.

:: Run your script
python config.py

echo.
echo ==================================================
echo                  ALL DONE!
echo ==================================================
pause