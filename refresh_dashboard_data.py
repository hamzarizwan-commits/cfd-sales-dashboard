"""
refresh_dashboard_data.py
=========================
Fetches fresh data from Redshift and patches the data constants inside
CFD_Sales_Dashboard_2026_MERGED.html in-place — preserving all HTML/CSS/JS
customisations.

Steps
  1. Re-run build_manager_tl_views.py  (writes CSV + JSON data files)
  2. Read the updated CSV/JSON files
  3. Rebuild the same JS data blocks that generate_dashboard.py would embed
  4. Regex-replace each const block in the MERGED HTML
  5. Update the "Data as of" date label
  6. Write the patched file back

Run manually:   python refresh_dashboard_data.py
Run via Task Scheduler: see run_daily_refresh.bat
"""

import subprocess, sys, os, re, json, math
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# ─── paths ───────────────────────────────────────────────────────────────────
WORKDIR      = r'C:\Users\hamza.rizwan'
PYTHON       = sys.executable
LOG_FILE     = os.path.join(WORKDIR, 'dashboard_refresh.log')
MERGED_HTML  = os.path.join(WORKDIR, 'CFD_Sales_Dashboard_2026_MERGED.html')

CSV_PATH          = os.path.join(WORKDIR, 'sales_consultants_jan_to_apr_2026.csv')
DAILY_COLL_PATH   = os.path.join(WORKDIR, 'daily_collections_2026.json')
PKG_MIX_PATH      = os.path.join(WORKDIR, 'package_mix_2026.json')
PKG_DISC_PATH     = os.path.join(WORKDIR, 'pkg_discount_by_filter.json')
REV_TL_PATH       = os.path.join(WORKDIR, 'revenue_by_tl_2026.csv')

# ─── logging ─────────────────────────────────────────────────────────────────
def log(msg):
    ts   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

# ─── helper: replace a single-line JS const ──────────────────────────────────
def replace_const(html, name, new_value_str):
    """Replace  const NAME = <anything up to first ;>;  on the same line."""
    pattern     = rf'^(const {re.escape(name)}\s*=\s*).*?;'
    replacement = rf'const {name} = {new_value_str};'
    new_html, n = re.subn(pattern, replacement, html, count=1, flags=re.MULTILINE)
    if n == 0:
        log(f'  WARNING: could not find "const {name}" in HTML — skipped')
    return new_html

# ─── step 1a: re-run data fetch ──────────────────────────────────────────────
def run_data_fetch():
    log('Running build_manager_tl_views.py ...')
    result = subprocess.run(
        [PYTHON, 'build_manager_tl_views.py'],
        cwd=WORKDIR, capture_output=True, text=True, encoding='utf-8',
    )
    for line in (result.stdout or '').splitlines():
        log('  ' + line)
    if result.returncode != 0:
        log(f'ERROR: build_manager_tl_views.py failed (exit {result.returncode})')
        for line in (result.stderr or '').splitlines():
            log('  ERR: ' + line)
        return False
    log('build_manager_tl_views.py — done.')
    return True

# ─── step 1b: re-run revenue waterfall ───────────────────────────────────────
def run_revenue_fetch():
    log('Running test_rev_waterfall.py ...')
    result = subprocess.run(
        [PYTHON, 'test_rev_waterfall.py'],
        cwd=WORKDIR, capture_output=True, text=True, encoding='utf-8',
    )
    for line in (result.stdout or '').splitlines():
        log('  ' + line)
    if result.returncode != 0:
        log(f'WARNING: test_rev_waterfall.py failed (exit {result.returncode}) — revenue data may be stale')
        for line in (result.stderr or '').splitlines():
            log('  ERR: ' + line)
        return False
    log('test_rev_waterfall.py — done.')
    return True

# ─── step 2: rebuild DATA json array (same logic as generate_dashboard.py) ───
def build_data_json():
    log(f'Reading {CSV_PATH} ...')
    df = pd.read_csv(CSV_PATH)
    records = []
    for _, r in df.iterrows():
        mgr_val = r.get('manager_reporting', '')
        if pd.isna(mgr_val) or mgr_val == '':
            continue
        rec = {
            'email':      str(r['staff_email'])            if pd.notna(r.get('staff_email'))            else '',
            'name':       str(r['staff_name_en'])          if pd.notna(r.get('staff_name_en'))          else '',
            'status':     str(r['status'])                 if pd.notna(r.get('status'))                 else '',
            'team':       str(r['team_name_en'])           if pd.notna(r.get('team_name_en'))           else '',
            'mgr':        str(mgr_val),
            'tl_name':    str(r['tl_name'])                if pd.notna(r.get('tl_name'))                else '',
            'mgr_name':   str(r['manager_name'])           if pd.notna(r.get('manager_name'))           else '',
            'region':     str(r['region'])                 if pd.notna(r.get('region'))                 else '',
            'is_ts':      bool(r.get('is_telesales', False)) if pd.notna(r.get('is_telesales'))         else False,
            'is_leader':  bool(r.get('is_leader', False))  if pd.notna(r.get('is_leader'))              else False,
            'desig':      str(r.get('designation', ''))    if pd.notna(r.get('designation'))            else '',
            'active_eom': bool(r.get('active_eom', True))  if pd.notna(r.get('active_eom'))             else True,
            'month':      int(r['month']),
            'doj':        str(r.get('doj', ''))[:10]       if pd.notna(r.get('doj'))                    else '',
            'days':       int(r.get('days_worked', 0))     if pd.notna(r.get('days_worked'))            else 0,
            'coll':       round(float(r.get('collections_achieved',   0)), 2) if pd.notna(r.get('collections_achieved'))   else 0,
            'target':     round(float(r.get('collection_target',       0)), 2) if pd.notna(r.get('collection_target'))      else 0,
            'net_gain':   round(float(r.get('client_net_gain_achieved',0)), 2) if pd.notna(r.get('client_net_gain_achieved')) else 0,
            'net_gain_t': round(float(r.get('client_net_gain_target',  0)), 2) if pd.notna(r.get('client_net_gain_target'))  else 0,
            'calls':      int(r.get('calls_count',              0)) if pd.notna(r.get('calls_count'))               else 0,
            'uqc':        int(r.get('unique_qualified_calls',   0)) if pd.notna(r.get('unique_qualified_calls'))    else 0,
            'nqc':        int(r.get('non_qualified_calls',      0)) if pd.notna(r.get('non_qualified_calls'))       else 0,
            'rej':        int(r.get('rejected_calls',           0)) if pd.notna(r.get('rejected_calls'))            else 0,
            'unan':       int(r.get('unanswered_calls',         0)) if pd.notna(r.get('unanswered_calls'))          else 0,
            'dtt':        round(float(r.get('total_talk_time',  0)), 2) if pd.notna(r.get('total_talk_time'))       else 0,
            'mtg_t':      int(r.get('total_meetings',           0)) if pd.notna(r.get('total_meetings'))            else 0,
            'vm':         int(r.get('verified_meetings',        0)) if pd.notna(r.get('verified_meetings'))         else 0,
            'uvm':        int(r.get('unique_verified_meetings', 0)) if pd.notna(r.get('unique_verified_meetings'))  else 0,
            'mtg_f':      int(r.get('failed_meetings',          0)) if pd.notna(r.get('failed_meetings'))           else 0,
            'pkg':        int(r.get('packages_sold',            0)) if pd.notna(r.get('packages_sold'))             else 0,
            'disc':       round(float(r.get('discounted_pct',   0)), 4) if pd.notna(r.get('discounted_pct'))        else 0,
            'renewed':    int(r.get('renewed_clients',          0)) if pd.notna(r.get('renewed_clients'))           else 0,
            'cov':        int(r.get('coverage_clients',         0)) if pd.notna(r.get('coverage_clients'))          else 0,
            'assigned':   int(r.get('current_assigned_clients', 0)) if pd.notna(r.get('current_assigned_clients'))  else 0,
            'pend_ren':   int(r.get('pending_renewal_clients',  0)) if pd.notna(r.get('pending_renewal_clients'))   else 0,
        }
        records.append(rec)
    log(f'  {len(records)} records built from CSV')
    return json.dumps(records, separators=(',', ':')), df

# ─── step 3: build dynamic ALL_MONTHS + MONTH_NAMES ─────────────────────────
def build_month_meta():
    today = date.today()
    month_names_list = ['January','February','March','April','May','June',
                        'July','August','September','October','November','December']
    start = date(2026, 1, 1)
    month_name_map = {}
    m, mn = start, 1
    while m <= today.replace(day=1):
        is_current = (m.year == today.year and m.month == today.month)
        label = month_names_list[m.month - 1] + (' (MTD)' if is_current else '')
        month_name_map[mn] = label
        m  += relativedelta(months=1)
        mn += 1
    month_name_map[-2] = 'October 2025'
    month_name_map[-1] = 'November 2025'
    month_name_map[0]  = 'December 2025'

    all_months_js    = '[' + ','.join(str(k) for k in month_name_map if k >= 1) + ']'
    month_names_js   = '{' + ','.join(f'"{k}":"{v}"' for k, v in month_name_map.items()) + '}'
    # MONTH_BOUNDS: used by custom date range filter
    month_bounds = {}
    m2, mn2 = date(2026, 1, 1), 1
    while m2 <= today.replace(day=1):
        eom = (m2 + relativedelta(months=1)) - relativedelta(days=1)
        month_bounds[mn2] = [m2.strftime('%Y-%m-%d'), eom.strftime('%Y-%m-%d')]
        m2  += relativedelta(months=1)
        mn2 += 1
    month_bounds_js = '{' + ','.join(f'{k}:["{v[0]}","{v[1]}"]' for k, v in month_bounds.items()) + '}'

    return all_months_js, month_names_js, month_bounds_js

# ─── step 4: load JSON side-files ────────────────────────────────────────────
def load_json_file(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    log(f'  WARNING: {path} not found — using empty object')
    return '{}'

def build_rev_tl_json():
    if not os.path.exists(REV_TL_PATH):
        log(f'  WARNING: {REV_TL_PATH} not found — REV_TL will be empty')
        return '{}'
    rev_month_labels = [
        'Jan-26','Feb-26','Mar-26','Apr-26','May-26','Jun-26',
        'Jul-26','Aug-26','Sep-26','Oct-26','Nov-26','Dec-26',
        'Jan-27','Feb-27','Mar-27','Apr-27',
    ]
    df = pd.read_csv(REV_TL_PATH)
    out = {}
    for _, row in df.iterrows():
        tname = str(row['team_name'])
        out[tname] = {
            lbl: int(round(float(row[lbl])))
            for lbl in rev_month_labels
            if lbl in row and pd.notna(row[lbl])
        }
    return json.dumps(out, separators=(',', ':'))

# ─── step 5: patch HTML ───────────────────────────────────────────────────────
def patch_html(data_json, daily_coll_json, pkg_mix_json, pkg_disc_json,
               rev_tl_json, all_months_js, month_names_js, month_bounds_js):

    log(f'Reading {MERGED_HTML} ...')
    with open(MERGED_HTML, 'r', encoding='utf-8') as f:
        html = f.read()

    today_str = date.today().strftime('%-d %b %Y') if sys.platform != 'win32' else \
                date.today().strftime('%#d %b %Y')

    # Replace data constants
    html = replace_const(html, 'DATA',             data_json)
    html = replace_const(html, 'DAILY_COLL',       daily_coll_json)
    html = replace_const(html, 'PKG_MIX',          pkg_mix_json)
    html = replace_const(html, 'PKG_DISC_BY_FILTER', pkg_disc_json)
    html = replace_const(html, 'REV_TL',           rev_tl_json)
    html = replace_const(html, 'ALL_MONTHS',       all_months_js)
    html = replace_const(html, 'MONTH_NAMES',      month_names_js)
    html = replace_const(html, 'MONTH_BOUNDS',     month_bounds_js)

    # Update "Data as of" label in nav bar
    html = re.sub(
        r'(<span[^>]*>)\d{1,2} \w+ 2026(</span>)',
        lambda m: m.group(1) + today_str + m.group(2),
        html, count=1,
    )

    log(f'Writing patched HTML back to {MERGED_HTML} ...')
    with open(MERGED_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    size_kb = os.path.getsize(MERGED_HTML) // 1024
    log(f'Done. File size: {size_kb} KB')

# ─── main ─────────────────────────────────────────────────────────────────────
def main():
    log('=' * 60)
    log('CFD Dashboard data refresh started')
    log('=' * 60)

    # 1a. Fetch fresh consultant/team data from Redshift
    if not run_data_fetch():
        log('Aborting refresh due to data fetch failure.')
        return False

    # 1b. Refresh revenue waterfall (revenue_by_tl_2026.csv)
    run_revenue_fetch()   # non-fatal: stale file used if this fails

    # 2. Build DATA array from updated CSV
    data_json, _ = build_data_json()

    # 3. Build month metadata
    all_months_js, month_names_js, month_bounds_js = build_month_meta()
    log(f'Month metadata: ALL_MONTHS = {all_months_js}')

    # 4. Load JSON side-files
    daily_coll_json = load_json_file(DAILY_COLL_PATH)
    pkg_mix_json    = load_json_file(PKG_MIX_PATH)
    pkg_disc_json   = load_json_file(PKG_DISC_PATH)
    rev_tl_json     = build_rev_tl_json()

    # 5. Patch the MERGED HTML in place
    patch_html(data_json, daily_coll_json, pkg_mix_json, pkg_disc_json,
               rev_tl_json, all_months_js, month_names_js, month_bounds_js)

    log('Refresh complete.')
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
