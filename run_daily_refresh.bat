@echo off
REM run_daily_refresh.bat
REM Triggered by Windows Task Scheduler on logon.
REM Skips if a successful refresh already ran today.

cd /d "C:\Users\hamza.rizwan"

REM Build today's date stamp (YYYY-MM-DD) to match log format
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DT=%%I
set TODAY=%DT:~0,4%-%DT:~4,2%-%DT:~6,2%

REM Check if log already contains a "Refresh complete" entry for today
findstr /C:"[%TODAY%"] dashboard_refresh.log | findstr /C:"Refresh complete" >nul 2>&1
if not errorlevel 1 (
    echo [%TODAY%] Refresh already ran today — skipping.
    exit /b 0
)

"C:\Users\hamza.rizwan\AppData\Local\Python\pythoncore-3.14-64\python.exe" refresh_dashboard_data.py >> dashboard_refresh.log 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] refresh_dashboard_data.py failed — check dashboard_refresh.log
) ELSE (
    echo [OK] Refresh complete
)
