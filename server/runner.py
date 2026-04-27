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

run_step('Step 1b: Rebuilding revenue waterfall...', 'test_rev_waterfall.py')
log('Step 1b complete.')

run_step('Step 2: Rebuilding dashboard HTML...', 'generate_dashboard.py')
log('Step 2 complete.')

run_step('Step 2b: Refreshing verified meetings data...', 'refresh_vm_data.py')
log('Step 2b complete.')

run_step('Step 3: Merging with meetings audit...', 'build_cfd_merged.py')
log('Step 3 complete.')

log('Step 4: Copying to desktop backup...')
dest = r'C:\Users\hamza.rizwan\Desktop\CFD_Dashboard_Live'
shutil.copy2(os.path.join(WORKDIR, 'CFD_Sales_Dashboard_2026_MERGED.html'), dest)
try: shutil.copy2(os.path.join(WORKDIR, 'CFD_Sales_Dashboard_2026.html'), dest)
except: pass
log('Step 4 complete.')

log('Step 5: Deploying to live server (bayutksareports.com/cfddashboard)...')
import urllib.request, urllib.error, json, base64

GH_TOKEN  = os.environ.get('GH_TOKEN', '')  # set in environment
GH_REPO   = 'SectorLabs/bayut-sa-bse-dashboards'
GH_PATH   = 'public/cfddashboard/index.html'
GH_BRANCH = 'master'
today_label = datetime.now().strftime('%Y-%m-%d %H:%M')

def gh_api(method, endpoint, body=None):
    url = f'https://api.github.com{endpoint}'
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'Authorization': f'Bearer {GH_TOKEN}',
        'Accept': 'application/vnd.github+json',
        'Content-Type': 'application/json',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

deploy_ok = True
try:
    # 1. Get current file SHA (needed for the update API)
    current = gh_api('GET', f'/repos/{GH_REPO}/contents/{GH_PATH}?ref={GH_BRANCH}')
    file_sha = current['sha']
    # 2. Read and encode the built dashboard
    with open(os.path.join(WORKDIR, 'CFD_Sales_Dashboard_2026_MERGED.html'), 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode()
    # 3. Push via GitHub Contents API — creates a commit directly
    result = gh_api('PUT', f'/repos/{GH_REPO}/contents/{GH_PATH}', {
        'message': f'CFD dashboard auto-refresh {today_label}',
        'content': content_b64,
        'sha': file_sha,
        'branch': GH_BRANCH,
    })
    log(f"Step 5 complete — live server updated. Commit: {result['commit']['sha'][:7]}")
except Exception as e:
    log(f'ERROR: GitHub API deploy failed — {e}')
    deploy_ok = False
    log('Step 5 FAILED — live server not updated. Desktop backup is still current.')

log('===== Refresh complete - CFD_Sales_Dashboard_2026_MERGED.html updated =====')
with open(LOG, 'a', encoding='utf-8') as f: f.write('\n')
