@echo off
title Subbasin Report Automation

REM Go to the folder where the BAT file is located
cd /d "%~dp0"

echo =========================================
echo  Subbasin Report Automation
echo =========================================
echo.

REM Check if Python exists
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b
)

REM Run the main Python controller
python run_all.py

echo.
echo ✅ Process finished.
pause
