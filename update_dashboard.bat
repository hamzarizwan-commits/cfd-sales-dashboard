@echo off
setlocal
set WORKDIR=C:\Users\hamza.rizwan
set LOG=%WORKDIR%\dashboard_update.log
set PYTHON=C:\Users\hamza.rizwan\AppData\Local\Python\pythoncore-3.14-64\python.exe

cd /d %WORKDIR%

echo [%date% %time%] ===== Refresh started ===== >> %LOG%

echo [%date% %time%] Step 1: Fetching data from Redshift... >> %LOG%
%PYTHON% build_manager_tl_views.py >> %LOG% 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: build_manager_tl_views.py failed (exit %errorlevel%) >> %LOG%
    exit /b 1
)
echo [%date% %time%] Step 1 complete. >> %LOG%

echo [%date% %time%] Step 2: Rebuilding dashboard HTML... >> %LOG%
%PYTHON% generate_dashboard.py >> %LOG% 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: generate_dashboard.py failed (exit %errorlevel%) >> %LOG%
    exit /b 1
)
echo [%date% %time%] Step 2 complete. >> %LOG%

echo [%date% %time%] Step 3: Merging with meetings audit... >> %LOG%
%PYTHON% build_cfd_merged.py >> %LOG% 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: build_cfd_merged.py failed (exit %errorlevel%) >> %LOG%
    exit /b 1
)
echo [%date% %time%] Step 3 complete. >> %LOG%

echo [%date% %time%] Step 4: Copying to desktop backup... >> %LOG%
xcopy /Y "%WORKDIR%\CFD_Sales_Dashboard_2026_MERGED.html" "C:\Users\hamza.rizwan\Desktop\CFD_Dashboard_Live\" >> %LOG% 2>&1
xcopy /Y "%WORKDIR%\CFD_Sales_Dashboard_2026.html" "C:\Users\hamza.rizwan\Desktop\CFD_Dashboard_Live\" >> %LOG% 2>&1
echo [%date% %time%] Step 4 complete. >> %LOG%

echo [%date% %time%] ===== Refresh complete — CFD_Sales_Dashboard_2026_MERGED.html updated ===== >> %LOG%
echo. >> %LOG%
endlocal
