$WORKDIR = 'C:\Users\hamza.rizwan'
$LOG     = "$WORKDIR\dashboard_update.log"
$PYTHON  = 'C:\Users\hamza.rizwan\AppData\Local\Python\pythoncore-3.14-64\python.exe'

Set-Location $WORKDIR

function Log($msg) {
    $line = "[$((Get-Date).ToString('ddd MM/dd/yyyy HH:mm:ss.ff'))] $msg"
    Add-Content -Path $LOG -Value $line -Encoding UTF8
}

function RunStep($label, $script) {
    Log $label
    $out = & $PYTHON $script 2>&1
    $rc  = $LASTEXITCODE
    if ($out) { $out | ForEach-Object { Add-Content -Path $LOG -Value $_ -Encoding UTF8 } }
    if ($rc -ne 0) {
        Log "ERROR: $script failed (exit $rc)"
        exit 1
    }
}

Log "===== Refresh started ====="

RunStep "Step 1: Fetching data from Redshift..." "build_manager_tl_views.py"
Log "Step 1 complete."

RunStep "Step 2: Rebuilding dashboard HTML..." "generate_dashboard.py"
Log "Step 2 complete."

RunStep "Step 3: Merging with meetings audit..." "build_cfd_merged.py"
Log "Step 3 complete."

Log "Step 4: Copying to desktop backup..."
Copy-Item "$WORKDIR\CFD_Sales_Dashboard_2026_MERGED.html" "C:\Users\hamza.rizwan\Desktop\CFD_Dashboard_Live\" -Force
Copy-Item "$WORKDIR\CFD_Sales_Dashboard_2026.html" "C:\Users\hamza.rizwan\Desktop\CFD_Dashboard_Live\" -Force -ErrorAction SilentlyContinue
Log "Step 4 complete."

Log "===== Refresh complete - CFD_Sales_Dashboard_2026_MERGED.html updated ====="
Add-Content -Path $LOG -Value "" -Encoding UTF8
