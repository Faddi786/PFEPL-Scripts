@echo off
echo Fixing PATH for GDAL...

REM ---- PROJ database path (CRITICAL) ----
set PROJ_LIB=C:\Users\Swapnali\miniconda3\envs\hmsenv\Lib\site-packages\pyproj\proj_dir\share\proj
set PATH=C:\Program Files\HEC\HEC-HMS\4.13\bin\gdal;%PATH%
set PATH=C:\Program Files\HEC\HEC-HMS\4.13\bin;%PATH%

echo Starting HEC-HMS with automation script...

"C:\Program Files\HEC\HEC-HMS\4.13\jre\bin\java.exe" ^
    -Dsun.java2d.d3d=false ^
    -DMapPanel.NoVolatileImage=true ^
    -Dpython.import.site=false ^
    -Xms32M ^
    -Dpython.path="C:\Program Files\HEC\HEC-HMS\4.13\hms.jar;C:\Program Files\HEC\HEC-HMS\4.13\lib\*" ^
    -Djava.library.path="C:\Program Files\HEC\HEC-HMS\4.13\bin;C:\Program Files\HEC\HEC-HMS\4.13\bin\gdal;C:\Program Files\HEC\HEC-HMS\4.13\bin\hdf" ^
    -classpath "C:\Program Files\HEC\HEC-HMS\4.13\hms.jar;C:\Program Files\HEC\HEC-HMS\4.13\lib\*" ^
    hms.Hms -script "C:\Users\Swapnali\Desktop\Sakina Maam Work\Dam and Junction Automation\global_summary.py"

echo HEC-HMS script finished.
pause