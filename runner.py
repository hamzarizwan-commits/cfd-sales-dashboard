"""Pipeline runner — called directly by Task Scheduler."""
import signal, subprocess, sys, os, shutil
signal.signal(signal.SIGINT, signal.SIG_IGN)
from datetime import datetime

WORKDIR = r'C:\Users\hamza.rizwan'
LOG     = os.path.join(WORKDIR, 'dashboard_update.log')
PYTHON  = sys.executable
os.chdir(WORKDIR)

CREATE_NEW_PROCESS_GROUP = 0x00000200

def log(msg):
    line = f"[{datetime.now().strftime('%a %m/%d/%Y %H:%M:%S.%f')[:29]}] {msg}\n"
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line)

def run_step(label, script):
    log(label)
    r = subprocess.run(
        [PYTHON, script], cwd=WORKDIR, capture_output=True, text=True,
        creationflags=CREATE_NEW_PROCESS_GROUP
    )
    if r.stdout: log(r.stdout.strip())
    if r.stderr: log(r.stderr.strip())
    if r.returncode != 0:
        log(f'ERROR: {script} failed (exit {r.returncode})')
        sys.exit(1)

log('===== Refresh started =====')

run_step('Step 1: Fetching data from Redshift...', 'build_manager_tl_views.py')
log('Step 1 complete.')

run_step('Step 2: Rebuilding dashboard HTML...', 'generate_dashboard.py')
log('Step 2 complete.')

run_step('Step 3: Merging with meetings audit...', 'build_cfd_merged.py')
log('Step 3 complete.')

log('Step 4: Copying to desktop backup...')
dest = r'C:\Users\hamza.rizwan\Desktop\CFD_Dashboard_Live'
shutil.copy2(os.path.join(WORKDIR, 'CFD_Sales_Dashboard_2026_MERGED.html'), dest)
try: shutil.copy2(os.path.join(WORKDIR, 'CFD_Sales_Dashboard_2026.html'), dest)
except: pass
log('Step 4 complete.')

log('===== Refresh complete - CFD_Sales_Dashboard_2026_MERGED.html updated =====')
with open(LOG, 'a', encoding='utf-8') as f: f.write('\n')
