"""
Generate CFD Sales Dashboard HTML with embedded data.
Reads from the latest sales_consultants CSV and produces a self-contained HTML dashboard.
"""
import json, math
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

print("Building JSON from latest consultant CSV...")
import os
df = pd.read_csv('C:/Users/hamza.rizwan/sales_consultants_jan_to_apr_2026.csv')

# Build dynamic month names: completed months get full name, current month gets "(MTD)"
_today = date.today()
_month_names_list = ['January','February','March','April','May','June',
                     'July','August','September','October','November','December']
_start = date(2026, 1, 1)
_month_name_map = {}
_m = _start
_mn = 1
while _m <= _today.replace(day=1):
    is_current = (_m.year == _today.year and _m.month == _today.month)
    label = _month_names_list[_m.month - 1] + (' (MTD)' if is_current else '')
    _month_name_map[_mn] = label
    _m += relativedelta(months=1)
    _mn += 1
# Add Oct/Nov/Dec 2025 as negative month numbers for prev-month lookups.
# These are in DATA (for Agent Table prev-month calculations) but NOT in any dropdown.
_month_name_map[-2] = 'October 2025'
_month_name_map[-1] = 'November 2025'
_month_name_map[0]  = 'December 2025'
_month_names_js = ','.join(f'"{k}":"{v}"' for k,v in _month_name_map.items())

# Compute working days per month (Sun–Thu week: skip weekday 4=Fri, 5=Sat)
def _count_wd(start, end):
    from datetime import timedelta
    count, d = 0, start
    while d < end:
        if d.weekday() not in (4, 5): count += 1
        d += timedelta(days=1)
    return count

_wd_per_month = {}
_wm = date(2026, 1, 1)
_wmn = 1
while _wm <= _today.replace(day=1):
    _wd_per_month[_wmn] = _count_wd(_wm, _wm + relativedelta(months=1))
    _wm += relativedelta(months=1)
    _wmn += 1

_current_mn_num = max(_wd_per_month.keys())
_current_month_start = date(2026, (_current_mn_num - 1) % 12 + 1, 1) if _current_mn_num <= 12 else date(2026 + (_current_mn_num - 1) // 12, (_current_mn_num - 1) % 12 + 1, 1)
_current_month_end = _current_month_start + relativedelta(months=1)
from datetime import timedelta as _td
_remaining_wd = _count_wd(_today + _td(days=1), _current_month_end)
_wd_per_month_js = ','.join(f'"{k}":{v}' for k, v in _wd_per_month.items())
print(f"Working days per month: {_wd_per_month}, remaining in current month: {_remaining_wd}")

records = []
for _, r in df.iterrows():
    mgr_val = r.get('manager_reporting', '')
    if pd.isna(mgr_val) or mgr_val == '':
        continue
    rec = {
        'email': str(r['staff_email']) if pd.notna(r['staff_email']) else '',
        'name': str(r['staff_name_en']) if pd.notna(r['staff_name_en']) else '',
        'status': str(r['status']) if pd.notna(r['status']) else '',
        'team': str(r['team_name_en']) if pd.notna(r.get('team_name_en')) else '',
        'mgr': str(mgr_val),
        'tl_name': str(r['tl_name']) if pd.notna(r.get('tl_name')) else '',
        'mgr_name': str(r['manager_name']) if pd.notna(r.get('manager_name')) else '',
        'region': str(r['region']) if pd.notna(r.get('region')) else '',
        'is_ts': bool(r.get('is_telesales', False)) if pd.notna(r.get('is_telesales')) else False,
        'is_leader': bool(r.get('is_leader', False)) if pd.notna(r.get('is_leader')) else False,
        'active_eom': bool(r.get('active_eom', True)) if pd.notna(r.get('active_eom')) else True,
        'month': int(r['month']),
        'doj': str(r.get('doj',''))[:10] if pd.notna(r.get('doj')) else '',
        'days': int(r.get('days_worked',0)) if pd.notna(r.get('days_worked')) else 0,
        'coll': round(float(r.get('collections_achieved',0)),2) if pd.notna(r.get('collections_achieved')) else 0,
        'target': round(float(r.get('collection_target',0)),2) if pd.notna(r.get('collection_target')) else 0,
        'net_gain': round(float(r.get('client_net_gain_achieved',0)),2) if pd.notna(r.get('client_net_gain_achieved')) else 0,
        'net_gain_t': round(float(r.get('client_net_gain_target',0)),2) if pd.notna(r.get('client_net_gain_target')) else 0,
        'calls': int(r.get('calls_count',0)) if pd.notna(r.get('calls_count')) else 0,
        'uqc': int(r.get('unique_qualified_calls',0)) if pd.notna(r.get('unique_qualified_calls')) else 0,
        'nqc': int(r.get('non_qualified_calls',0)) if pd.notna(r.get('non_qualified_calls')) else 0,
        'rej': int(r.get('rejected_calls',0)) if pd.notna(r.get('rejected_calls')) else 0,
        'unan': int(r.get('unanswered_calls',0)) if pd.notna(r.get('unanswered_calls')) else 0,
        'dtt': round(float(r.get('total_talk_time',0)),2) if pd.notna(r.get('total_talk_time')) else 0,
        'mtg_t': int(r.get('total_meetings',0)) if pd.notna(r.get('total_meetings')) else 0,
        'vm': int(r.get('verified_meetings',0)) if pd.notna(r.get('verified_meetings')) else 0,
        'uvm': int(r.get('unique_verified_meetings',0)) if pd.notna(r.get('unique_verified_meetings')) else 0,
        'mtg_f': int(r.get('failed_meetings',0)) if pd.notna(r.get('failed_meetings')) else 0,
        'pkg': int(r.get('packages_sold',0)) if pd.notna(r.get('packages_sold')) else 0,
        'disc': round(float(r.get('discounted_pct',0)),4) if pd.notna(r.get('discounted_pct')) else 0,
        'renewed': int(r.get('renewed_clients',0)) if pd.notna(r.get('renewed_clients')) else 0,
        'cov': int(r.get('coverage_clients',0)) if pd.notna(r.get('coverage_clients')) else 0,
        'assigned': int(r.get('current_assigned_clients',0)) if pd.notna(r.get('current_assigned_clients')) else 0,
        'pend_ren': int(r.get('pending_renewal_clients',0)) if pd.notna(r.get('pending_renewal_clients')) else 0,
    }
    records.append(rec)

data_json = json.dumps(records, separators=(',',':'))
print(f"JSON built: {len(records)} records, {len(data_json)//1024}KB")

# Load daily collections data
_daily_coll_path = 'C:/Users/hamza.rizwan/daily_collections_2026.json'
if os.path.exists(_daily_coll_path):
    with open(_daily_coll_path, 'r') as _f:
        _daily_coll_json = _f.read()
    print(f"Daily collections loaded from {_daily_coll_path}")
else:
    _daily_coll_json = '{}'
    print("Daily collections file not found — trend chart will be empty")

# Load daily per-consultant metrics (for day-level date filter)
_daily_metrics_path = 'C:/Users/hamza.rizwan/daily_metrics_2026.json'
if os.path.exists(_daily_metrics_path):
    with open(_daily_metrics_path, 'r') as _f:
        _daily_metrics_json = _f.read()
    print(f"Daily metrics loaded from {_daily_metrics_path}")
else:
    _daily_metrics_json = '{}'
    print("Daily metrics file not found — date filter will use month granularity")

# Load active listings snapshot
_al_snap_path = 'C:/Users/hamza.rizwan/active_listings_snapshot.json'
if os.path.exists(_al_snap_path):
    with open(_al_snap_path, 'r') as _f:
        _al_snap = json.load(_f)
    _total_active_listings_val = _al_snap.get('total', 0)
    _cons_active_listings_json = json.dumps(_al_snap.get('by_consultant', {}), separators=(',',':'))
    _cons_active_agencies_json = json.dumps(_al_snap.get('agencies_by_consultant', {}), separators=(',',':'))
    _zero_posters_json = json.dumps(_al_snap.get('zero_posters', {}), separators=(',',':'))
    print(f"Active listings snapshot loaded: total={_total_active_listings_val}")
else:
    _total_active_listings_val = 0
    _cons_active_listings_json = '{}'
    _cons_active_agencies_json = '{}'
    _zero_posters_json = '{}'
    print("Active listings snapshot not found — using defaults")

# Load consultant avg meeting duration
_mtg_dur_path = 'C:/Users/hamza.rizwan/consultant_avg_mtg_duration.json'
if os.path.exists(_mtg_dur_path):
    with open(_mtg_dur_path, 'r') as _f:
        _consultant_avg_mtg_duration_json = _f.read()
    print(f"Consultant avg meeting duration loaded from {_mtg_dur_path}")
else:
    _consultant_avg_mtg_duration_json = '{}'
    print("Consultant avg meeting duration file not found")

_pkg_mix_path = 'C:/Users/hamza.rizwan/package_mix_2026.json'
if os.path.exists(_pkg_mix_path):
    with open(_pkg_mix_path, 'r') as _f:
        _pkg_mix_json = _f.read()
    print(f"Package mix loaded from {_pkg_mix_path}")
else:
    _pkg_mix_json = '{}'
    print("Package mix file not found — package chart will be empty")

_disc_filter_path = 'C:/Users/hamza.rizwan/pkg_discount_by_filter.json'
if os.path.exists(_disc_filter_path):
    with open(_disc_filter_path, 'r') as _f:
        _disc_filter_json = _f.read()
    print(f"Package discount data loaded from {_disc_filter_path}")
else:
    _disc_filter_json = '{}'
    print("Package discount file not found — discount chart will be empty")

# Load online channel collections
_online_monthly_path = 'C:/Users/hamza.rizwan/online_collections_monthly_2026.json'
if os.path.exists(_online_monthly_path):
    with open(_online_monthly_path, 'r') as _f:
        _online_monthly_json = _f.read()
    print(f"Online monthly collections loaded from {_online_monthly_path}")
else:
    _online_monthly_json = '{}'
    print("Online monthly collections file not found — Online filter will show 0")

_online_daily_path = 'C:/Users/hamza.rizwan/online_collections_daily_2026.json'
if os.path.exists(_online_daily_path):
    with open(_online_daily_path, 'r') as _f:
        _online_daily_json = _f.read()
    print(f"Online daily collections loaded from {_online_daily_path}")
else:
    _online_daily_json = '{}'
    print("Online daily collections file not found — Online trend chart will be empty")

_online_pkg_path = 'C:/Users/hamza.rizwan/online_packages_monthly_2026.json'
if os.path.exists(_online_pkg_path):
    with open(_online_pkg_path, 'r') as _f:
        _online_pkg_json = _f.read()
    print(f"Online packages loaded from {_online_pkg_path}")
else:
    _online_pkg_json = '{}'

_online_listings_path = 'C:/Users/hamza.rizwan/online_listings_snapshot.json'
if os.path.exists(_online_listings_path):
    with open(_online_listings_path, 'r') as _f:
        _online_listings_json = _f.read()
    print(f"Online listings snapshot loaded from {_online_listings_path}")
else:
    _online_listings_json = '{{"total":0,"agencies":0}}'

# Load revenue-by-TL data and build lookup dicts
_rev_tl_path = 'C:/Users/hamza.rizwan/revenue_by_tl_2026.csv'
_rev_month_labels = ['Jan-26','Feb-26','Mar-26','Apr-26','May-26','Jun-26','Jul-26','Aug-26',
                     'Sep-26','Oct-26','Nov-26','Dec-26','Jan-27','Feb-27','Mar-27','Apr-27']
# Dynamic mapping: dashboard month number (1=Jan-26, 2=Feb-26, ...) -> revenue CSV label
# Covers all waterfall months so new dashboard months auto-resolve without code changes
_mn_to_label_js = ','.join(f'{i+1}:"{lbl}"' for i, lbl in enumerate(_rev_month_labels))
if os.path.exists(_rev_tl_path):
    _rev_tl_df = pd.read_csv(_rev_tl_path)
    _rev_tl_dict = {}
    for _, _row in _rev_tl_df.iterrows():
        _tname = str(_row['team_name'])
        _rev_tl_dict[_tname] = {
            lbl: int(round(float(_row[lbl]))) for lbl in _rev_month_labels if lbl in _row and pd.notna(_row[lbl])
        }
    _rev_tl_json = json.dumps(_rev_tl_dict, separators=(',',':'))
    print(f"Revenue by TL loaded: {len(_rev_tl_dict)} teams")
else:
    _rev_tl_json = '{}'
    print("revenue_by_tl_2026.csv not found — revenue rows will be hidden")

# Build TEAM_REGION and TEAM_IS_TS from consultant data
_team_region_dict = {}
_team_is_ts_dict = {}
for _, _r in df.iterrows():
    _t = str(_r.get('team_name_en', '')) if pd.notna(_r.get('team_name_en', '')) else ''
    if _t and _t not in _team_region_dict:
        _team_region_dict[_t] = str(_r['region']) if pd.notna(_r.get('region')) else ''
        _team_is_ts_dict[_t] = bool(_r.get('is_telesales', False)) if pd.notna(_r.get('is_telesales')) else False
_team_region_json = json.dumps(_team_region_dict, separators=(',',':'))
_team_is_ts_json  = json.dumps(_team_is_ts_dict,  separators=(',',':'))

# Build dynamic month dropdown options (same list used in all 3 dropdowns)
_month_options_html = ''
_mo2 = date(2026, 1, 1)
_mn3 = 1
while _mo2 <= _today.replace(day=1):
    _is_curr2 = (_mo2.year == _today.year and _mo2.month == _today.month)
    _opt_label = _month_names_list[_mo2.month - 1] + ' ' + str(_mo2.year) + (' (MTD)' if _is_curr2 else '')
    _month_options_html += f'        <option value="{_mn3}">{_opt_label}</option>\n'
    _mo2 += relativedelta(months=1)
    _mn3 += 1
# ALL_MONTHS used in JS for trend charts / overview cards — 2026 months only (mn >= 1)
_all_month_nums_js = ','.join(str(k) for k in _month_name_map.keys() if k >= 1)
# MONTH_BOUNDS: {month_num: ["bom", "eom"]} for JS date filter granularity
_mo_b = date(2026, 1, 1); _mn_b = 1; _mb_parts = []
while _mo_b <= _today.replace(day=1):
    _eom_b = (_mo_b + relativedelta(months=1)) - timedelta(days=1)
    _mb_parts.append(f'{_mn_b}:["{_mo_b.strftime("%Y-%m-%d")}","{_eom_b.strftime("%Y-%m-%d")}"]')
    _mo_b += relativedelta(months=1); _mn_b += 1
_month_bounds_js = '{' + ','.join(_mb_parts) + '}'

# Agent Performance Table — month options with latest month pre-selected (2026 months only)
_max_month_num = max(k for k in _month_name_map.keys() if k >= 1)
_apt_month_options_html = ''
for _mn_k, _mn_v in _month_name_map.items():
    if _mn_k < 1:
        continue  # Oct-Dec 2025 are only for prev-month lookups, not for selection
    _sel = ' selected' if _mn_k == _max_month_num else ''
    _apt_month_options_html += f'        <option value="{_mn_k}"{_sel}>{_mn_v}</option>\n'

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CFD Sales Dashboard — 2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#f4f8f5;--card:#ffffff;--card2:#edf5ef;--border:#c4d8ca;
  --text:#1a2e22;--muted:#506b5a;--accent:#0d7a3f;--accent2:#08643a;
  --green:#0d7a3f;--red:#dc2626;--amber:#d97706;--blue:#1d6cb0;--teal:#10935a;
  --g1:#0d7a3f;--g2:#10935a;--g3:#27a96d;--g4:#5cc08a;--g5:#a8dbbe;--g6:#ddf1e5;
  --bayut-green:#0d7a3f;--bayut-dark:#063d24;
  --shadow-sm:0 1px 3px rgba(13,122,63,0.08),0 1px 2px rgba(13,122,63,0.04);
  --shadow-md:0 4px 16px rgba(13,122,63,0.12),0 2px 6px rgba(13,122,63,0.05);
  --shadow-lg:0 8px 32px rgba(13,122,63,0.14),0 4px 12px rgba(13,122,63,0.06);
  --radius:14px;
}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,-apple-system,sans-serif;font-size:13.5px;min-height:100vh;-webkit-font-smoothing:antialiased;line-height:1.5}}
.nav{{background:linear-gradient(135deg,#063d24,#0d7a3f);border-radius:14px;box-shadow:0 2px 8px rgba(0,80,40,.15);padding:14px 22px;display:flex;align-items:center;gap:0;position:sticky;top:12px;z-index:100;margin:12px 24px 0}}
.nav-brand{{font-size:1.2rem;font-weight:700;color:#fff;padding:0;margin-right:40px;white-space:nowrap;letter-spacing:-0.02em}}
.nav-brand span{{color:rgba(255,255,255,.75);font-weight:500;letter-spacing:-0.01em}}
.nav-tab{{padding:8px 16px;font-size:12.5px;font-weight:500;color:rgba(255,255,255,.65);cursor:pointer;border-bottom:2.5px solid transparent;transition:all .2s;white-space:nowrap;border-radius:6px}}
.nav-tab:hover{{color:#fff;background:rgba(255,255,255,.1)}}
.nav-tab.active{{color:#fff;border-bottom-color:#fff;font-weight:600;background:rgba(255,255,255,.12)}}
.view{{display:none;padding:28px 32px}}
.view.active{{display:block}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:14px;margin-bottom:24px}}
.kpi-card{{background:#ffffff;border:1px solid #c4d8ca;border-radius:14px;padding:18px;box-shadow:0 1px 4px rgba(13,122,63,.06);transition:box-shadow .2s,transform .2s}}
.kpi-card:hover{{box-shadow:var(--shadow-md);transform:translateY(-1px)}}
.kpi-card.highlight{{background:#ffffff}}
.kpi-label{{font-size:.68rem;color:var(--muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px;font-weight:600}}
.kpi-val{{font-size:1.5rem;font-weight:700;line-height:1;color:#111}}
.kpi-sub{{font-size:11.5px;color:var(--muted);margin-top:5px}}
.sec-header{{display:flex;align-items:center;gap:10px;margin-bottom:14px;margin-top:28px;padding-left:12px;border-left:3px solid var(--accent)}}
.sec-title{{font-size:1.1rem;font-weight:700;color:#111}}
.sec-badge{{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600}}
.hard-badge{{background:#d1fae5;color:#064e3b;border:1px solid #a7f3d0}}
.soft-badge{{background:#ddf1e5;color:#065f46;border:1px solid #a7dbbe}}
.filter-bar{{background:#fff;border:1px solid #c4d8ca;border-radius:14px;padding:10px 14px;margin-bottom:22px;display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.filter-group{{display:flex;flex-direction:column;gap:4px}}
.filter-label{{font-size:.6rem;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:600}}
select{{background:#edf5ef;border:1px solid #c4d8ca;color:var(--text);padding:5px 6px;border-radius:6px;font-size:.72rem;cursor:pointer;min-width:145px;font-family:inherit;font-weight:500;height:30px;transition:border-color .15s,box-shadow .15s}}
select:focus{{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(13,122,63,0.12)}}
input[type="date"].ov-date-input{{background:#edf5ef;border:1px solid #c4d8ca;color:var(--text);padding:5px 6px;border-radius:6px;font-size:.72rem;cursor:pointer;font-family:inherit;font-weight:500;height:30px;transition:border-color .15s,box-shadow .15s;min-width:128px}}
input[type="date"].ov-date-input:focus{{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(13,122,63,0.12)}}
.ov-date-row{{display:flex;align-items:center;gap:7px}}
.ov-date-sep{{font-size:11px;color:var(--muted);font-weight:500}}
.ov-date-clear-btn{{background:none;border:1.5px solid #e5e1d8;border-radius:8px;cursor:pointer;color:var(--muted);font-size:12px;padding:6px 9px;line-height:1;transition:border-color .15s,color .15s}}
.ov-date-clear-btn:hover{{border-color:#bbb;color:var(--text)}}
.charts-row{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:26px}}
.chart-card{{background:#fff;border:1px solid var(--border);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow-sm)}}
.chart-title{{font-size:11.5px;font-weight:700;color:var(--muted);margin-bottom:14px;text-transform:uppercase;letter-spacing:.06em}}
.soft-kpi-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px;margin-bottom:22px}}
.soft-kpi-card{{background:#fff;border:1px solid #c0e8e4;border-radius:var(--radius);padding:16px 18px;border-left:4px solid var(--teal);box-shadow:var(--shadow-sm)}}
.soft-kpi-card .kpi-val{{font-size:22px}}
.kpi-region-split{{margin-top:8px;padding-top:7px;border-top:1px dashed var(--border)}}
.kpi-region-row{{display:flex;justify-content:space-between;padding:2px 0;font-size:10.5px;line-height:1.6}}
.kpi-region-label{{color:var(--muted);font-weight:500}}
.kpi-region-val{{font-weight:600;color:var(--text)}}
.pill{{display:inline-block;padding:2px 9px;border-radius:8px;font-size:11px;font-weight:600}}
.pill-exc{{background:#d1fae5;color:#064e3b;border:1px solid #a7f3d0}}.pill-vg{{background:#dcfce7;color:#14532d;border:1px solid #bbf7d0}}
.pill-good{{background:#dcfce7;color:#15803d;border:1px solid #bbf7d0}}.pill-above{{background:#fef9c3;color:#713f12;border:1px solid #fde68a}}
.pill-avg{{background:#ffedd5;color:#9a3412;border:1px solid #fed7aa}}.pill-below{{background:#fee2e2;color:#7f1d1d;border:1px solid #fecaca}}
.pill-poor{{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5}}.pill-active{{background:#dcfce7;color:#14532d;font-size:10px;border:1px solid #bbf7d0}}
.pill-inactive{{background:#fee2e2;color:#7f1d1d;font-size:10px}}
.pill-field{{background:#e0e7ff;color:#3730a3;font-size:10px}}.pill-ts{{background:#ccfbf1;color:#134e4a;font-size:10px}}
.tbl-wrap{{overflow-x:auto;border:1px solid var(--border);border-radius:var(--radius);max-height:600px;overflow-y:auto;box-shadow:var(--shadow-sm)}}
/* Report Cards */
.rc-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:18px;margin-bottom:26px}}
.rc-grid-wide{{display:grid;grid-template-columns:repeat(auto-fill,minmax(700px,1fr));gap:18px;margin-bottom:26px}}
.rc-scroll-row{{display:flex;gap:16px;overflow-x:auto;padding-bottom:10px;margin-bottom:22px;align-items:start}}
.rc-scroll-row .rc-card{{min-width:300px;max-width:320px;flex-shrink:0}}
.rc-card{{background:#ffffff;border:1px solid #c4d8ca;border-radius:14px;padding:14px 16px;transition:box-shadow .2s,transform .15s;position:relative;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.rc-card:hover{{box-shadow:var(--shadow-md);transform:translateY(-2px)}}
.rc-mgr-card{{border-left:4px solid #0d7a3f}}
.rc-tl-card{{border-left:4px solid #1d6cb0}}
.rc-consultant-card{{border-left:4px solid #9ca3af}}
.rc-card-header{{display:flex;align-items:center;gap:8px;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--border);position:relative}}
.rc-card-title{{font-size:.8rem;font-weight:700;color:#063d24}}
.rc-card-subtitle{{font-size:10.5px;color:var(--muted)}}
.rc-row{{display:flex;justify-content:space-between;padding:3px 0;font-size:.76rem;border-bottom:1px solid #f0f0f0}}
.rc-row-label{{color:var(--muted);font-size:.76rem}}
.rc-row-val{{font-weight:700;color:#111;font-size:.76rem}}
/* ── metric tooltips ── */
.tip{{position:relative;cursor:help;text-decoration:underline dotted;text-decoration-color:#b0aa9e;text-underline-offset:2px}}
.tip[data-tip]::after{{content:attr(data-tip);position:absolute;bottom:calc(100% + 6px);left:0;background:#0f172a;color:#f1f5f9;font-size:10px;line-height:1.5;padding:6px 10px;border-radius:7px;width:max-content;max-width:240px;white-space:normal;pointer-events:none;opacity:0;transition:opacity 0.15s;z-index:1000;font-family:'Inter',sans-serif;font-weight:400;box-shadow:0 4px 12px rgba(0,0,0,.2)}}
.tip[data-tip]:hover::after{{opacity:1}}
.tip-r[data-tip]::after{{left:auto;right:0}}
.rc-section{{margin-top:10px;padding-top:8px;border-top:1px dashed var(--border)}}
.rc-section-title{{font-size:9.5px;color:var(--accent);text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;font-weight:700}}
/* Region card colour themes */
.rc-ruh{{border-top:4px solid #5c6bc0;background:linear-gradient(160deg,#f3f4ff 0%,#fff 60%)}}
.rc-ruh .rc-card-title{{color:#5c6bc0}}
.rc-ruh .rc-section-title{{color:#5c6bc0}}
.rc-jed{{border-top:4px solid #ef5350;background:linear-gradient(160deg,#fff4f4 0%,#fff 60%)}}
.rc-jed .rc-card-title{{color:#e53935}}
.rc-jed .rc-section-title{{color:#e53935}}
.rc-dam{{border-top:4px solid #26a69a;background:linear-gradient(160deg,#f0faf9 0%,#fff 60%)}}
.rc-dam .rc-card-title{{color:#00897b}}
.rc-dam .rc-section-title{{color:#00897b}}
.rc-mkh{{border-top:4px solid #ffa726;background:linear-gradient(160deg,#fffbf0 0%,#fff 60%)}}
.rc-mkh .rc-card-title{{color:#f57c00}}
.rc-mkh .rc-section-title{{color:#f57c00}}
.rc-med{{border-top:4px solid #ab47bc;background:linear-gradient(160deg,#fdf3ff 0%,#fff 60%)}}
.rc-med .rc-card-title{{color:#8e24aa}}
.rc-med .rc-section-title{{color:#8e24aa}}
.rc-ts{{border-top:4px solid #78909c;background:linear-gradient(160deg,#f4f6f7 0%,#fff 60%)}}
.rc-ts .rc-card-title{{color:#546e7a}}
.rc-ts .rc-section-title{{color:#546e7a}}
/* Manager Detail Layout */
.mgr-detail-layout{{display:grid;grid-template-columns:340px 1fr;gap:26px;align-items:start}}
@media(max-width:900px){{.mgr-detail-layout{{grid-template-columns:1fr}}}}
/* TL Tree */
.tl-branch-btn{{background:var(--card);border:2px solid var(--border);border-radius:var(--radius);padding:10px 18px;cursor:pointer;font-size:13px;font-weight:600;transition:all .2s;display:flex;align-items:center;gap:10px;white-space:nowrap;box-shadow:var(--shadow-sm);width:100%}}
.tl-branch-btn:hover{{border-color:var(--accent);background:#edf8f2;box-shadow:var(--shadow-md)}}
.tl-branch-btn.active{{border-color:var(--accent);background:var(--accent);color:#fff;box-shadow:0 4px 18px rgba(13,122,63,0.38)}}
.tl-branch-btn .tl-cash{{font-size:11px;color:var(--muted);font-weight:500}}
.tl-branch-btn.active .tl-cash{{color:rgba(255,255,255,0.8)}}
.tl-min-btn{{width:22px;height:22px;border-radius:50%;border:1.5px solid var(--border);background:var(--bg);color:var(--muted);font-size:14px;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .15s;padding:0;flex-shrink:0}}
.tl-min-btn:hover{{border-color:var(--accent);color:var(--accent);background:#edf8f2}}
.mgr-direct-card{{border:2px solid #059669!important;}}
.mgr-direct-card .rc-card-title{{color:#059669}}
.mgr-direct-card .rc-section-title{{color:#059669}}
.mgr-tl-connector{{flex:0 0 40px;display:flex;align-items:center;justify-content:center}}
.mgr-tl-connector-line{{width:100%;height:2px;background:var(--accent);position:relative}}
.mgr-tl-connector-line::before,.mgr-tl-connector-line::after{{content:'';position:absolute;top:50%;transform:translateY(-50%);width:7px;height:7px;border-radius:50%;background:var(--accent)}}
.mgr-tl-connector-line::before{{left:0}}
.mgr-tl-connector-line::after{{right:0}}
.mgr-tl-card{{border:2px solid var(--accent)!important;box-shadow:0 4px 20px rgba(13,122,63,0.16)!important;animation:slideIn .2s ease}}
@keyframes slideIn{{from{{opacity:0;transform:translateY(-8px)}}to{{opacity:1;transform:translateY(0)}}}}
table{{width:100%;border-collapse:collapse;font-size:.76rem;white-space:nowrap}}
thead th{{background:#ddf1e5;color:#0d7a3f;padding:9px 10px;text-align:left;font-size:.66rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid #0d7a3f;position:sticky;top:0;z-index:1}}
.col-sticky{{position:sticky;z-index:1;background:#fff}}
.col-sticky-hd{{position:sticky;z-index:3;background:#ddf1e5}}
.col-sticky-last{{box-shadow:4px 0 8px -2px rgba(0,0,0,0.18)}}
tbody tr:hover .col-sticky{{background:#ddf1e5}}
tbody tr{{border-bottom:1px solid #e5e7eb}}
tbody tr:hover{{background:#ddf1e5}}
tbody td{{padding:7px 10px;vertical-align:middle;font-size:.76rem}}
.num{{text-align:right}}.pos{{color:#15803d}}.neg{{color:#b91c1c}}
.th-hard{{background:#fffbeb !important;color:#d97706 !important;border-bottom-color:#d97706 !important}}.th-soft{{background:#f0fdf4 !important;color:#0d7a3f !important;border-bottom-color:#0d7a3f !important}}
.mgr-card{{background:#fff;border:1px solid var(--border);border-radius:var(--radius);padding:22px;margin-bottom:22px;box-shadow:var(--shadow-sm)}}
.mgr-card h3{{font-size:17px;margin-bottom:4px;font-weight:700;letter-spacing:-0.01em}}.mgr-card .subtitle{{color:var(--muted);font-size:12.5px}}
/* ── Overview drill-down ── */
.ov-drill-wrap{{cursor:pointer;display:block}}
.ov-drill-wrap:hover .rc-card{{box-shadow:var(--shadow-md);border-color:var(--accent);transform:translateY(-2px);transition:all .15s}}
.ov-breadcrumb{{display:none;align-items:center;gap:10px;margin-bottom:18px;padding:10px 16px;background:#fff;border:1px solid var(--border);border-radius:var(--radius);font-size:12px;box-shadow:var(--shadow-sm)}}
.ov-back-btn{{background:none;border:1.5px solid var(--border);border-radius:7px;padding:5px 12px;font-size:11.5px;font-weight:600;color:var(--muted);cursor:pointer;transition:all .15s;display:flex;align-items:center;gap:5px;font-family:inherit}}
.ov-back-btn:hover{{border-color:var(--accent);color:var(--accent);background:#edf8f2}}
.ov-bc-sep{{color:var(--border);font-size:14px}}
.ov-bc-item{{color:var(--muted)}}
.ov-bc-item.active{{color:var(--text);font-weight:700}}
.ov-drill-hint{{font-size:9px;color:var(--accent);text-transform:uppercase;letter-spacing:.08em;margin-top:4px;font-weight:700;opacity:.7}}
/* ── Agent Performance Table ── */
.apt-group{{text-align:center;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;padding:7px 4px;border-left:2px solid rgba(255,255,255,0.12)}}
.meetings-group{{background:#065f46;color:#a7f3d0}}.calls-group{{background:#1e3a5f;color:#93c5fd}}.coll-group{{background:#78350f;color:#fde68a}}
.meetings-sub{{background:#f0fdf4!important;color:#14532d}}.calls-sub{{background:#eff6ff!important;color:#1e3a8a}}.coll-sub{{background:#fffbeb!important;color:#78350f}}
.apt-delta-pos{{color:#15803d;font-weight:700}}.apt-delta-neg{{color:#b91c1c;font-weight:700}}.apt-delta-na{{color:var(--muted)}}
details.rc-collapsible>summary{{list-style:none}}
details.rc-collapsible>summary::-webkit-details-marker{{display:none}}
.rc-caret{{display:inline-block;font-size:10px;transition:transform .15s;line-height:1}}
details.rc-collapsible[open]>.summary .rc-caret,details.rc-collapsible[open]>summary .rc-caret{{transform:rotate(180deg)}}
.ov-mgr-filter{{position:relative;min-width:160px}}
.ov-mgr-trigger{{width:100%;background:#edf5ef;border:1px solid #c4d8ca;border-radius:6px;padding:5px 6px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;font-size:.72rem;font-weight:500;color:var(--text);font-family:inherit;gap:8px;white-space:nowrap;height:30px}}
.ov-mgr-trigger:hover{{border-color:var(--accent)}}
.ov-mgr-trigger .arrow{{font-size:10px;color:var(--muted);transition:transform .15s;flex-shrink:0}}
.ov-mgr-trigger.open .arrow{{transform:rotate(180deg)}}
.ov-mgr-panel{{position:absolute;top:calc(100% + 4px);left:0;min-width:230px;background:#fff;border:1px solid var(--border);border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.12);z-index:200;display:none}}
.ov-mgr-panel.open{{display:block}}
.ov-mgr-panel-top{{padding:8px 10px 6px;border-bottom:1px solid var(--border)}}
.ov-mgr-clear-btn{{width:100%;background:none;border:1px solid var(--border);border-radius:5px;color:var(--muted);font-size:11px;padding:4px 8px;cursor:pointer;font-family:inherit;text-align:center}}
.ov-mgr-clear-btn:hover{{background:#edf8f2;color:var(--text)}}
.ov-mgr-scroll{{max-height:240px;overflow-y:auto;padding:4px}}
.ov-mgr-scroll::-webkit-scrollbar{{width:4px}}
.ov-mgr-scroll::-webkit-scrollbar-thumb{{background:var(--border);border-radius:4px}}
.ov-mgr-item{{display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:6px;cursor:pointer;user-select:none}}
.ov-mgr-item:hover{{background:#edf8f2}}
.ov-mgr-item.disabled-opt{{opacity:.4;pointer-events:none}}
.ov-mgr-cb{{width:14px;height:14px;border-radius:3px;border:1.5px solid var(--border);background:#fff;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .1s}}
.ov-mgr-cb.chk{{background:var(--accent);border-color:var(--accent)}}
.ov-mgr-cb.chk::after{{content:'✓';font-size:9px;color:#fff;line-height:1}}
.ov-mgr-item-label{{font-size:12px;color:var(--text);display:flex;align-items:center;gap:5px}}
.ov-mgr-tag{{display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;color:#fff}}
.ov-compare-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}}
.ov-compare-label{{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:7px 12px;border-radius:8px 8px 0 0;color:#fff;text-align:center}}
.ov-compare-label.mgr-a{{background:#2a9d8f}}
.ov-compare-label.mgr-b{{background:#e76f51}}
.theme-toggle{{display:flex;align-items:center;gap:7px;cursor:pointer;user-select:none}}
.theme-toggle input{{display:none}}
.theme-toggle-track{{width:38px;height:21px;background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.3);border-radius:11px;position:relative;transition:background .25s;flex-shrink:0}}
body.dark .theme-toggle-track{{background:rgba(255,255,255,.38)}}
.theme-toggle-thumb{{position:absolute;top:2px;left:2px;width:15px;height:15px;background:#fff;border-radius:50%;transition:transform .25s;box-shadow:0 1px 4px rgba(0,0,0,.3)}}
.theme-toggle input:checked + .theme-toggle-track .theme-toggle-thumb{{transform:translateX(17px)}}
.theme-toggle-lbl{{font-size:11px;color:rgba(255,255,255,.65);font-weight:500;white-space:nowrap;min-width:42px}}
/* ── Root dark variables ── */
body.dark{{
  --bg:#111815;--card:#192420;--card2:#1f2e28;--border:#2d4038;
  --text:#e0f2eb;--muted:#7aaa90;--accent:#2ee89a;--green:#2ee89a;
  --red:#f06565;--amber:#f5a623;--blue:#5ba4f5;
  --g1:#2ee89a;--g2:#27cc85;--g3:#1fa06a;--g4:#177550;--g5:#1a3028;--g6:#1f2e28;
  --bayut-green:#2ee89a;--bayut-dark:#0d3020;
  --shadow-sm:0 1px 4px rgba(0,0,0,.55);--shadow-md:0 4px 18px rgba(0,0,0,.65);--shadow-lg:0 8px 32px rgba(0,0,0,.7);
  background:#111815;color:#e0f2eb
}}
/* ── Hardcoded colour overrides ── */
body.dark .kpi-val{{color:#e0f2eb}}
body.dark .kpi-sub{{color:#7aaa90}}
body.dark .sec-title{{color:#e0f2eb}}
body.dark .chart-title{{color:#b8d8c8}}
body.dark .rc-card-title{{color:#2ee89a}}
body.dark .rc-row-val{{color:#e0f2eb}}
body.dark .rc-row-label{{color:#7aaa90}}
body.dark .rc-card-subtitle{{color:#7aaa90}}
body.dark .rc-section-title{{color:#2ee89a}}
body.dark .mgr-card h3{{color:#e0f2eb}}
body.dark .mgr-card .subtitle{{color:#7aaa90}}
/* ── Page & surfaces ── */
body.dark .filter-bar{{background:#192420;border-color:#2d4038;box-shadow:0 1px 4px rgba(0,0,0,.4)}}
body.dark .kpi-card{{background:#1f2e28;border-color:#2d4038}}
body.dark .kpi-card.highlight{{background:#1f2e28}}
body.dark .chart-card{{background:#192420;border-color:#2d4038}}
body.dark .soft-kpi-card{{background:#192420;border-color:#2d4038;border-left-color:#2ee89a}}
body.dark .mgr-card{{background:#192420;border-color:#2d4038}}
body.dark .tbl-wrap{{border-color:#2d4038}}
/* ── Inputs & selects ── */
body.dark select{{background:#1f2e28;border-color:#2d4038;color:#e0f2eb}}
body.dark select:focus{{border-color:#2ee89a;box-shadow:0 0 0 3px rgba(46,232,154,.15)}}
body.dark input[type="date"].ov-date-input{{background:#1f2e28;border-color:#2d4038;color:#e0f2eb}}
body.dark .ov-mgr-trigger{{background:#1f2e28;border-color:#2d4038;color:#e0f2eb}}
body.dark .ov-date-clear-btn{{border-color:#2d4038;color:#7aaa90}}
body.dark .ov-date-clear-btn:hover{{border-color:#f06565;color:#f06565}}
/* ── Table ── */
body.dark thead th{{background:#1f2e28;color:#2ee89a;border-bottom-color:#2ee89a}}
body.dark .col-sticky-hd{{background:#1f2e28}}
body.dark .col-sticky{{background:#192420}}
body.dark tbody tr:hover .col-sticky{{background:#1f2e28}}
body.dark tbody tr{{border-bottom-color:#243528}}
body.dark tbody tr:hover{{background:#1f2e28}}
body.dark tbody td{{color:#c8e4d6}}
body.dark .th-hard{{background:rgba(245,166,35,.15)!important;color:#f5a623!important;border-bottom-color:#f5a623!important}}
body.dark .th-soft{{background:rgba(46,232,154,.1)!important;color:#2ee89a!important;border-bottom-color:#2ee89a!important}}
/* ── Report cards — tinted by role for visual distinction ── */
body.dark .rc-card{{background:#192420;border-color:#2d4038}}
body.dark .rc-mgr-card{{background:#172a20;border-left:4px solid #2ee89a;border-color:#253e30}}
body.dark .rc-tl-card{{background:#17202e;border-left:4px solid #5ba4f5;border-color:#253048}}
body.dark .rc-consultant-card{{background:#192420;border-left:4px solid #4b6065;border-color:#2d4038}}
body.dark .rc-card-header{{border-bottom-color:#2d4038}}
body.dark .rc-row{{border-bottom-color:#1e3028}}
body.dark .rc-section{{border-top-color:#2d4038}}
body.dark .rc-card:hover{{box-shadow:0 4px 18px rgba(0,0,0,.55)}}
/* ── Breadcrumb & nav ── */
body.dark .ov-breadcrumb{{background:#192420;border-color:#2d4038}}
body.dark .ov-bc-item{{color:#7aaa90}}
body.dark .ov-bc-item.active{{color:#e0f2eb}}
body.dark .ov-back-btn{{border-color:#2d4038;color:#7aaa90}}
body.dark .ov-back-btn:hover{{border-color:#2ee89a;color:#2ee89a;background:#172a20}}
/* ── TL branch buttons ── */
body.dark .tl-branch-btn{{background:#192420;border-color:#2d4038;color:#e0f2eb}}
body.dark .tl-branch-btn .tl-cash{{color:#7aaa90}}
body.dark .tl-branch-btn:hover{{border-color:#2ee89a;background:#172a20}}
body.dark .tl-branch-btn.active{{background:#2ee89a;border-color:#2ee89a;color:#0d2518}}
body.dark .tl-branch-btn.active .tl-cash{{color:rgba(13,37,24,.75)}}
/* ── Manager filter panel ── */
body.dark .ov-mgr-panel{{background:#192420;border-color:#2d4038;box-shadow:0 8px 28px rgba(0,0,0,.6)}}
body.dark .ov-mgr-item:hover{{background:#1f2e28}}
body.dark .ov-mgr-item-label{{color:#e0f2eb}}
body.dark .ov-mgr-cb{{background:#1f2e28;border-color:#2d4038}}
body.dark .ov-mgr-clear-btn{{border-color:#2d4038;color:#7aaa90}}
body.dark .ov-mgr-clear-btn:hover{{background:#1f2e28;color:#e0f2eb}}
/* ── Comparison labels ── */
body.dark .ov-compare-label.mgr-a{{background:#1a6e5f}}
body.dark .ov-compare-label.mgr-b{{background:#8b3a25}}
/* ── Section header ── */
body.dark .sec-header{{border-left-color:#2ee89a}}
body.dark .mgr-direct-card{{border-color:#2ee89a!important}}
body.dark .mgr-direct-card .rc-card-title{{color:#2ee89a}}
/* ── Reset btn ── */
body.dark #ov-reset-btn{{background:#192420!important}}
body.dark #ov-reset-btn:hover{{background:#f06565!important;border-color:#f06565!important;color:#fff!important}}
/* ── Consultant Performance Metrics table ── */
body.dark .apt-delta-pos{{color:#4ade80}}
body.dark .apt-delta-neg{{color:#f87171}}
body.dark .pos{{color:#4ade80}}
body.dark .neg{{color:#f87171}}
body.dark .td-name{{color:#e0f2eb;font-weight:600}}
body.dark .td-muted{{color:#7aaa90}}
body.dark thead .meetings-sub{{background:rgba(6,95,70,.45)!important;color:#6ee7b7!important}}
body.dark thead .calls-sub{{background:rgba(30,58,95,.5)!important;color:#93c5fd!important}}
body.dark thead .coll-sub{{background:rgba(120,53,15,.45)!important;color:#fcd34d!important}}
body.dark tbody .meetings-sub{{background:rgba(6,95,70,.12)!important;color:#a7e8c0}}
body.dark tbody .calls-sub{{background:rgba(30,58,95,.18)!important;color:#bcd6f8}}
body.dark tbody .coll-sub{{background:rgba(120,53,15,.15)!important;color:#fcd34d}}
body.dark .meetings-group{{background:#044035!important;color:#6ee7b7!important}}
body.dark .calls-group{{background:#0e2342!important;color:#93c5fd!important}}
body.dark .coll-group{{background:#4a1f06!important;color:#fcd34d!important}}
body.dark #ov-agent-table table > thead > tr:first-child th{{background:#1f2e28!important;color:#2ee89a!important;border-bottom-color:#2d4038!important}}
body.dark #ov-mgr-table tbody td{{color:#c8e4d6}}
body.dark #ov-mgr-table .td-name{{color:#e0f2eb;font-weight:600}}
body.dark #ov-mgr-table .td-muted{{color:#7aaa90}}
/* ── Scrollbars ── */
body.dark ::-webkit-scrollbar-track{{background:#111815}}
body.dark ::-webkit-scrollbar-thumb{{background:#2d4038;border-radius:4px}}
body.dark ::-webkit-scrollbar-thumb:hover{{background:#3a5248}}
/* ── Status pills ── */
body.dark .pill-exc{{background:rgba(6,78,59,.6);color:#6ee7b7;border-color:#065f46}}
body.dark .pill-vg{{background:rgba(20,83,45,.5);color:#86efac;border-color:#166534}}
body.dark .pill-above{{background:rgba(113,63,18,.5);color:#fde68a;border-color:#92400e}}
body.dark .pill-avg{{background:rgba(154,52,18,.45);color:#fdba74;border-color:#9a3412}}
body.dark .pill-below{{background:rgba(127,29,29,.5);color:#fca5a5;border-color:#7f1d1d}}
body.dark .pill-poor{{background:rgba(153,27,27,.5);color:#f87171;border-color:#991b1b}}
</style>
</head>
<body>

<div class="nav">
  <div style="display:flex;align-items:center;gap:10px;margin-right:32px;flex-shrink:0">
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
      <circle cx="18" cy="18" r="18" fill="#fff"/>
      <circle cx="18" cy="18" r="16" fill="#0d7a3f"/>
      <polygon points="18,8 8,17 10,17 10,27 16,27 16,21 20,21 20,27 26,27 26,17 28,17" fill="#fff"/>
      <rect x="15" y="12" width="6" height="5" rx="1" fill="#0d7a3f"/>
    </svg>
    <div style="line-height:1.15">
      <div style="font-size:1.05rem;font-weight:800;color:#fff;letter-spacing:-0.01em">bayut</div>
      <div style="font-size:9.5px;color:rgba(255,255,255,.7);font-weight:500;letter-spacing:0.04em;text-transform:uppercase;margin-top:3px">Saudi Arabia</div>
    </div>
  </div>
  <div class="nav-brand">CFD <span>Sales Dashboard</span></div>
  <div class="nav-tab active" data-view="overview" onclick="switchView('overview')">CFD Overview</div>
  <div class="nav-tab" data-view="meetings" onclick="switchView('meetings')">Meetings Audit</div>
  <div class="nav-tab" data-view="vm" onclick="switchView('vm')">Verified Meetings</div>
  <div style="margin-left:auto;display:flex;align-items:center;gap:16px;padding:0 4px">
    <label class="theme-toggle" title="Toggle dark / light theme">
      <input type="checkbox" id="dark-toggle" onchange="toggleDarkMode(this.checked)">
      <span class="theme-toggle-track"><span class="theme-toggle-thumb"></span></span>
      <span class="theme-toggle-lbl" id="dark-toggle-lbl">&#9728; Light</span>
    </label>
    <div style="display:flex;align-items:center;gap:8px">
      <span style="font-size:11px;color:rgba(255,255,255,.65);font-weight:500;letter-spacing:0.01em">Data as of</span>
      <span style="font-size:11px;font-weight:700;color:rgba(255,255,255,.85);background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.3);border-radius:6px;padding:5px 12px;letter-spacing:0.01em">{_today.strftime('%d %b %Y')}</span>
    </div>
  </div>
</div>

<!-- ==================== OVERVIEW ==================== -->
<div id="v-overview" class="view active">
  <div class="filter-bar">
    <div class="filter-group">
      <div class="filter-label">Month</div>
      <select id="f-month" onchange="render()">
        <option value="0" selected>All Months</option>
{_month_options_html}      </select>
    </div>
    <div class="filter-group">
      <div class="filter-label">Date Range</div>
      <div class="ov-date-row">
        <input type="date" id="f-date-from" class="ov-date-input" placeholder="From" oninput="_onDateFilter()" onchange="_onDateFilter()" />
        <span class="ov-date-sep">to</span>
        <input type="date" id="f-date-to" class="ov-date-input" placeholder="To" oninput="_onDateFilter()" onchange="_onDateFilter()" />
        <button class="ov-date-clear-btn" id="ov-date-clear-btn" onclick="_clearDateFilter()" style="display:none" title="Clear dates">&#10005;</button>
      </div>
    </div>
    <div class="filter-group">
      <div class="filter-label">Team Type</div>
      <select id="f-type" onchange="render()">
        <option value="all">All</option>
        <option value="field">Field Sales</option>
        <option value="ts">Telesales</option>
        <option value="online">Online</option>
      </select>
    </div>
    <div class="filter-group">
      <div class="filter-label">Region</div>
      <select id="f-region" onchange="render()">
        <option value="all">All Regions</option>
        <option value="Riyadh">Riyadh</option>
        <option value="Jeddah">Jeddah</option>
        <option value="Dammam">Dammam</option>
        <option value="Makkah">Makkah</option>
        <option value="Medina">Medina</option>
        <option value="Telesales">Telesales</option>
      </select>
    </div>
    <div class="filter-group">
      <div class="filter-label">Team Lead</div>
      <div class="ov-mgr-filter" id="ov-tl-filter">
        <div class="ov-mgr-trigger" id="ov-tl-trigger" onclick="_toggleTlPanel(event)">
          <span id="ov-tl-trigger-label">All Team Leads</span>
          <span class="arrow">&#9660;</span>
        </div>
        <div class="ov-mgr-panel" id="ov-tl-panel">
          <div class="ov-mgr-panel-top">
            <button class="ov-mgr-clear-btn" onclick="_clearTlFilter(event)">Clear selection</button>
          </div>
          <div class="ov-mgr-scroll" id="ov-tl-scroll"></div>
        </div>
      </div>
    </div>
    <div class="filter-group">
      <div class="filter-label">Manager</div>
      <div class="ov-mgr-filter" id="ov-mgr-filter">
        <div class="ov-mgr-trigger" id="ov-mgr-trigger" onclick="_toggleMgrPanel(event)">
          <span id="ov-mgr-trigger-label">All Managers</span>
          <span class="arrow">&#9660;</span>
        </div>
        <div class="ov-mgr-panel" id="ov-mgr-panel">
          <div class="ov-mgr-panel-top">
            <button class="ov-mgr-clear-btn" onclick="_clearMgrFilter(event)">Clear selection</button>
          </div>
          <div class="ov-mgr-scroll" id="ov-mgr-scroll"></div>
        </div>
      </div>
    </div>
    <div style="margin-left:auto;display:flex;align-items:flex-end;padding-bottom:0">
      <button onclick="resetAllFilters()" id="ov-reset-btn" style="display:none;height:30px;padding:0 14px;background:#fff;border:1.5px solid #dc2626;border-radius:6px;color:#dc2626;font-size:.68rem;font-weight:700;font-family:inherit;cursor:pointer;letter-spacing:.5px;text-transform:uppercase;transition:background .15s,color .15s" onmouseover="this.style.background='#dc2626';this.style.color='#fff'" onmouseout="this.style.background='#fff';this.style.color='#dc2626'">&#10005; Reset</button>
    </div>
  </div>

  <!-- Drill-down breadcrumb (hidden at top level) -->
  <div id="ov-breadcrumb" class="ov-breadcrumb">
    <button class="ov-back-btn" onclick="backOv()">&#8592; Back</button>
    <span class="ov-bc-sep">/</span>
    <span id="ov-bc-month" class="ov-bc-item"></span>
    <span id="ov-bc-sep2" class="ov-bc-sep" style="display:none">/</span>
    <span id="ov-bc-mgr" class="ov-bc-item active" style="display:none"></span>
    <span id="ov-bc-sep3" class="ov-bc-sep" style="display:none">/</span>
    <span id="ov-bc-tl" class="ov-bc-item active" style="display:none"></span>
  </div>

  <!-- Report Cards (shown when All Months selected, or during drill-down) -->
  <div id="ov-report-cards"></div>

  <!-- Single month top: KPI tiles -->
  <div id="ov-single-top" style="display:none;margin-bottom:20px">
    <div id="ov-kpi-tiles"></div>
  </div>

  <!-- Trend chart + Active Clients & Net Gain — side by side -->
  <div style="display:flex;gap:16px;margin-bottom:20px;align-items:stretch">
    <div class="chart-card" style="flex:1;min-width:0">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
        <div class="chart-title" id="ov-trend-title" style="margin-bottom:0">Collections Trend</div>
        <button id="btn-mtd-coll" onclick="_toggleMtdColl()" style="font-family:inherit;font-size:0.68rem;font-weight:600;padding:3px 10px;border-radius:20px;border:1px solid #e5e1d8;background:transparent;color:#8f8b80;cursor:pointer;transition:all 0.15s;white-space:nowrap">MTD</button>
      </div>
      <canvas id="chart-trend" style="max-height:400px"></canvas>
    </div>

    <!-- Active Clients & Net Gain combo chart -->
    <div class="chart-card" style="flex:1;min-width:0;font-family:'Geist Mono',monospace">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">
        <div class="chart-title">Active Clients &amp; Net Gain</div>
      </div>
      <div style="position:relative;height:320px">
        <canvas id="chart-active-gain"></canvas>
      </div>
      <div style="display:flex;gap:24px;flex-wrap:wrap;align-items:center;margin-top:14px;padding-top:12px;border-top:1px solid #e5e1d8;font-size:0.7rem;color:#8f8b80">
        <div style="display:flex;align-items:center;gap:6px">
          <span style="width:18px;height:2.5px;background:#1b1a17;border-radius:2px;display:inline-block;position:relative">
            <span style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:7px;height:7px;border-radius:50%;background:#fff;border:1.5px solid #1b1a17;display:block"></span>
          </span>
          Active Clients (right axis)
        </div>
        <div style="display:flex;align-items:center;gap:6px">
          <span style="display:flex;gap:2px;align-items:flex-end">
            <span style="width:7px;height:14px;background:#43a047;border-radius:1px;display:inline-block;opacity:.8"></span>
            <span style="width:7px;height:8px;background:#e53935;border-radius:1px;display:inline-block;opacity:.8"></span>
          </span>
          Net Gain — green = positive, red = negative (left axis)
        </div>
      </div>
    </div>
  </div>

  <!-- Row: Revenue | Employee Productivity -->
  <div style="display:flex;gap:16px;margin-bottom:20px;align-items:stretch">
    <!-- Revenue trend -->
    <div class="chart-card" id="ov-revenue-chart" style="flex:1;min-width:0;font-family:'Geist Mono',monospace">
      <div class="chart-title" style="margin-bottom:16px">Revenue &mdash; Monthly Trend</div>
      <div style="position:relative;height:320px">
        <canvas id="chart-revenue"></canvas>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:12px 28px;align-items:center;margin-top:14px;padding-top:12px;border-top:1px solid #e5e1d8;font-size:0.7rem;color:#8f8b80">
        <div style="display:flex;align-items:center;gap:6px">
          <span style="width:11px;height:11px;border-radius:2px;background:#6366f1;flex-shrink:0"></span>
          Recurring Revenue (SAR)
        </div>
      </div>
    </div>

    <!-- Employee Productivity -->
    <div class="chart-card" style="flex:1;min-width:0;font-family:'Geist Mono',monospace">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <div>
          <div class="chart-title" style="margin-bottom:2px">Employee Productivity &mdash; Monthly Trend</div>
          <div style="font-size:0.62rem;color:#8f8b80;letter-spacing:0.06em;text-transform:uppercase">Per BOM headcount</div>
        </div>
        <button id="btn-mtd-prod" onclick="_toggleMtdProd()" style="font-family:inherit;font-size:0.68rem;font-weight:600;padding:3px 10px;border-radius:20px;border:1px solid #e5e1d8;background:transparent;color:#8f8b80;cursor:pointer;transition:all 0.15s;white-space:nowrap;flex-shrink:0">MTD</button>
      </div>
      <div style="position:relative;height:320px">
        <canvas id="chart-emp-prod"></canvas>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:14px;padding-top:12px;border-top:1px solid #e5e1d8">
        <div style="flex:1;min-width:0;background:#faf9f5;border:1px solid #e5e1d8;border-radius:8px;padding:10px 14px;position:relative;overflow:hidden">
          <div style="position:absolute;top:0;left:0;right:0;height:2px;background:#0d9488"></div>
          <div style="font-size:0.68rem;font-weight:600;color:#1b1a17;margin-bottom:4px">Cash / Employee</div>
          <div style="font-size:0.62rem;color:#8f8b80">Total cash collected &divide; BOM headcount (SAR)</div>
        </div>
        <div style="flex:1;min-width:0;background:#faf9f5;border:1px solid #e5e1d8;border-radius:8px;padding:10px 14px;position:relative;overflow:hidden">
          <div style="position:absolute;top:0;left:0;right:0;height:2px;background:#b91c1c"></div>
          <div style="font-size:0.68rem;font-weight:600;color:#1b1a17;margin-bottom:4px">Packages / Employee</div>
          <div style="font-size:0.62rem;color:#8f8b80">Total packages sold &divide; BOM headcount (right axis)</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Row: Package Mix | Package Discount % -->
  <div style="display:flex;gap:16px;margin-bottom:20px;align-items:stretch">
    <!-- Package mix -->
    <div class="chart-card" style="flex:1;min-width:0;font-family:'Geist Mono',monospace">
      <div class="chart-title" style="margin-bottom:16px">Package Mix — Monthly Trend</div>
      <div style="position:relative;height:320px">
        <canvas id="chart-pkg-ov"></canvas>
      </div>
      <div id="pkg-ov-legend" style="display:flex;flex-wrap:wrap;gap:12px 24px;margin-top:16px;padding-top:14px;border-top:1px solid #e5e1d8;align-items:center;font-size:0.7rem;color:#8f8b80"></div>
    </div>

    <!-- Package Discount % -->
    <div class="chart-card" style="flex:1;min-width:0;font-family:'Geist Mono',monospace">
      <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:10px">
        <div class="chart-title">Package Discount % — Monthly Trend</div>
        <div style="font-size:0.62rem;color:#8f8b80;letter-spacing:0.06em;text-transform:uppercase;line-height:1.6;text-align:right">Jan &ndash; Apr 2026</div>
      </div>
      <div style="display:flex;gap:6px;margin-bottom:10px">
        <button id="disc-ct-all"     onclick="setDiscClientType('all')"     style="font-family:inherit;font-size:0.68rem;font-weight:600;padding:3px 12px;border-radius:20px;border:1px solid #1b1a17;background:#1b1a17;color:#f7f6f2;cursor:pointer;transition:all 0.15s">All</button>
        <button id="disc-ct-new"     onclick="setDiscClientType('new')"     style="font-family:inherit;font-size:0.68rem;font-weight:600;padding:3px 12px;border-radius:20px;border:1px solid #e5e1d8;background:;color:#8f8b80;cursor:pointer;transition:all 0.15s">New</button>
        <button id="disc-ct-renewal" onclick="setDiscClientType('renewal')" style="font-family:inherit;font-size:0.68rem;font-weight:600;padding:3px 12px;border-radius:20px;border:1px solid #e5e1d8;background:;color:#8f8b80;cursor:pointer;transition:all 0.15s">Renewal</button>
      </div>
      <div id="disc-pkg-pills" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px"></div>
      <div style="position:relative;height:320px">
        <canvas id="chart-disc-trend"></canvas>
      </div>
      <div id="disc-trend-legend" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:6px 14px;margin-top:16px;padding-top:14px;border-top:1px solid #e5e1d8"></div>
    </div>
  </div>

  <!-- Soft KPI trends — all months only -->
  <div id="ov-soft-kpi-section" style="display:none;margin-bottom:20px;border:1px solid var(--border);border-radius:10px;overflow:hidden">
    <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 16px;background:var(--card);border-bottom:1px solid var(--border)">
      <div style="font-size:0.72rem;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.06em">Soft KPI Trends</div>
      <div style="display:flex;align-items:center;gap:8px">
        <span style="font-size:0.68rem;color:var(--muted);font-weight:600;white-space:nowrap">Team Type:</span>
        <select id="soft-kpi-type" onchange="_onSoftKpiTypeChange()" style="font-family:inherit;font-size:0.72rem;padding:3px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg);color:var(--text);cursor:pointer">
          <option value="all">All</option>
          <option value="field">Field Sales</option>
          <option value="ts">Telesales</option>
        </select>
      </div>
    </div>
    <div id="ov-soft-kpi-trends"></div>
  </div>

  <!-- ── Agent Performance Table ── -->
  <div id="ov-agent-section" style="margin-bottom:20px">
    <div class="filter-bar" style="border-radius:10px 10px 0 0;margin-bottom:0;padding:10px 16px;gap:16px;border-bottom:none">
      <div class="filter-group">
        <div class="filter-label">Month</div>
        <select id="apt-month" onchange="renderAgentTable()">
{_apt_month_options_html}        </select>
      </div>
      <div class="filter-group">
        <div class="filter-label">Team Type</div>
        <select id="apt-type" onchange="_aptTypeChanged()">
          <option value="all">All</option>
          <option value="field">Field Sales</option>
          <option value="ts">Telesales</option>
        </select>
      </div>
      <div class="filter-group">
        <div class="filter-label">Team Lead</div>
        <select id="apt-tl" onchange="renderAgentTable()"></select>
      </div>
      <div class="filter-group">
        <div class="filter-label">Manager</div>
        <select id="apt-mgr" onchange="renderAgentTable()"></select>
      </div>
      <div class="filter-group" style="flex:1;min-width:180px;max-width:280px">
        <div class="filter-label">Consultant</div>
        <div class="ov-mgr-filter" id="apt-cons-filter" style="min-width:180px">
          <div class="ov-mgr-trigger" id="apt-cons-trigger" onclick="_toggleAptConsPanel(event)">
            <span id="apt-cons-trigger-label" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">All Consultants</span>
            <span class="arrow">&#9660;</span>
          </div>
          <div class="ov-mgr-panel" id="apt-cons-panel" style="min-width:260px;right:0;left:auto">
            <div class="ov-mgr-panel-top" style="padding:8px 10px">
              <input id="apt-cons-search" type="text" placeholder="Search consultant&hellip;"
                style="width:100%;box-sizing:border-box;padding:5px 8px;border:1px solid var(--border);border-radius:5px;font-size:12px;font-family:inherit;outline:none;background:var(--card);color:var(--text)"
                oninput="_onAptConsSearch()" onclick="event.stopPropagation()">
              <button class="ov-mgr-clear-btn" style="margin-top:6px" onclick="_clearAptConsFilter(event)">Clear selection</button>
            </div>
            <div class="ov-mgr-scroll" id="apt-cons-scroll" style="max-height:260px"></div>
          </div>
        </div>
      </div>
    </div>
    <div id="ov-agent-table" class="tbl-wrap" style="border-radius:0 0 10px 10px;max-height:620px;overflow-y:auto"></div>
  </div>

  <!-- Single month detail view: manager charts + table -->
  <div id="ov-single-month">
    <div class="charts-row">
      <div class="chart-card"><div class="chart-title">Cash Collection by Manager</div><canvas id="chart-coll"></canvas></div>
      <div class="chart-card"><div class="chart-title">TvA % by Manager</div><canvas id="chart-tva"></canvas></div>
    </div>

    <div class="sec-header"><div class="sec-title">Manager Summary</div></div>
    <div id="ov-mgr-table" class="tbl-wrap"></div>
  </div>
</div>

<script>
const DATA = {data_json};
const DAILY_COLL = {_daily_coll_json};
const ONLINE_COLL_MONTHLY = {_online_monthly_json};
const ONLINE_COLL_DAILY = {_online_daily_json};
const ONLINE_PKG_MONTHLY = {_online_pkg_json};
const ONLINE_LISTINGS = {_online_listings_json};
const WORKING_DAYS_PER_MONTH = {{{_wd_per_month_js}}};
const REMAINING_WD = {_remaining_wd};
const PKG_MIX = {_pkg_mix_json};
const DAILY_METRICS = {_daily_metrics_json};
const TOTAL_ACTIVE_LISTINGS_SNAPSHOT = {_total_active_listings_val};
const CONSULTANT_ACTIVE_LISTINGS = {_cons_active_listings_json};
const CONSULTANT_ACTIVE_AGENCIES = {_cons_active_agencies_json};
const ZERO_POSTERS = {_zero_posters_json};
const CONSULTANT_AVG_MTG_DURATION = {_consultant_avg_mtg_duration_json};

// Active clients at EOM per month, split by region (Redshift CRM snapshot, status=375, not deleted)
const ACTIVE_CLIENTS_BY_REGION = {{
  "1": {{"Dammam":278,"Jeddah":429,"Makkah":86,"Medina":87,"Riyadh":949,"Telesales":1309}},
  "2": {{"Dammam":297,"Jeddah":428,"Makkah":78,"Medina":86,"Riyadh":931,"Telesales":1343}},
  "3": {{"Dammam":305,"Jeddah":407,"Makkah":92,"Medina":88,"Riyadh":973,"Telesales":1388}},
  "4": {{"Dammam":297,"Jeddah":415,"Makkah":94,"Medina":86,"Riyadh":946,"Telesales":1397}}
}};

// Package discount % by filter — from Redshift dim_contracts, split by team type & region
// Structure: PKG_DISC_BY_FILTER[bucket][month_num_str][pkg_category] = avg_disc_pct
// bucket: "all" | "ts" | "field" | "Riyadh" | "Jeddah" | "Dammam" | "Medina" | "Makkah" | "Telesales"
const PKG_DISC_BY_FILTER = {_disc_filter_json};

function getActiveClients(mn, type, region) {{
  const byReg = ACTIVE_CLIENTS_BY_REGION[String(mn)] || {{}};
  if(region && region !== 'all') return byReg[region] ?? 0;
  if(type === 'ts')    return byReg['Telesales'] ?? 0;
  if(type === 'field') return Object.entries(byReg).filter(([k]) => k !== 'Telesales').reduce((s,[,v]) => s+v, 0);
  return Object.values(byReg).reduce((s,v) => s+v, 0);
}}
const ALL_MONTHS = [{_all_month_nums_js}];
const MONTH_BOUNDS = {_month_bounds_js};

const MONTH_NAMES = {{{_month_names_js}}};

const MGR_TEAMS = {{
  'Alaa - JM1':['Alaa - JM1'],
  'El-Kallas - M4':['El-Kallas - M4','Rola - TL Riyadh'],
  'Mohammed Abdelkader - Eastern':['Mohammed Abdelkader - Eastern','Kareem - TL Eastern'],
  'Reham AL Harbi - M2':['Reham AL Harbi - M2','Aminah - TL Riyadh'],
  'Mohamad Ghannoum - JM3':['Mohamad Ghannoum - JM3','Khalil - TL Jeddah','Othman - TL Medina'],
  'Mohamed Abdullah - M3':['Mohamed Abdullah - M3','AlHourani - TL Riyadh'],
  'AlHourani - TL Riyadh':['AlHourani - TL Riyadh'],
  'AbdulMajed - TL Riyadh':['AbdulMajed - TL Riyadh','Al Khateeb - TL Riyadh'],
  'Telesales - Sulaiman Aljurbua':['Telesales - Sulaiman Aljurbua','Telesales Manager','Telesales-Abdelfattah Khaiyal','Telesales - Abdullah Altamimi'],
  'Hussain - TL PK':['Hussain - TL PK'],
  'Mohsin - TL PK':['Mohsin - TL PK'],
}};

const MGR_NAMES = {{
  'Alaa - JM1':'Alaa Alsaber','El-Kallas - M4':'Mohammad El-Kallas',
  'Mohammed Abdelkader - Eastern':'Mohammed Abdelkader','Reham AL Harbi - M2':'Reham AL Harbi',
  'Mohamad Ghannoum - JM3':'Mohamad Ghannoum','Mohamed Abdullah - M3':'Mohamed Abdullah',
  'AlHourani - TL Riyadh':'Mohammad AlHourani',
  'AbdulMajed - TL Riyadh':'Abdulmajed Alghusen',
  'Telesales - Sulaiman Aljurbua':'Sulaiman Aljurbua',
  'Sherif - TL Jeddah':'Sherif Hassan (Jeddah)','Sherif - TL Makkah':'Sherif Hassan (Makkah)',
  'Hussain - TL PK':'Hussain Ali','Mohsin - TL PK':'Mohsin Hassan Shah',
}};

// Manager aliases (for manager view report cards)
const MGR_LIST = Object.keys(MGR_TEAMS);

// TL teams only (for TL view report cards) - actual team leads, not managers
const TL_LIST = [
  'Khalil - TL Jeddah','Al Khateeb - TL Riyadh','Sherif - TL Makkah','Sherif - TL Jeddah',
  'Kareem - TL Eastern','Aminah - TL Riyadh','Rola - TL Riyadh','Othman - TL Medina',
  'AlHourani - TL Riyadh',
  'Telesales - Abdullah Altamimi','Telesales Manager','Telesales-Abdelfattah Khaiyal'
];

const TL_NAMES = {{
  'Khalil - TL Jeddah':'Khalil Barakat', 'Al Khateeb - TL Riyadh':'Mohammed Alkhateeb',
  'Sherif - TL Makkah':'Sherif Hassan', 'Sherif - TL Jeddah':'Sherif - TL Jeddah',
  'Kareem - TL Eastern':'Kareem Saber', 'Aminah - TL Riyadh':'Aminah Alsheikhi',
  'Rola - TL Riyadh':'Rola Aljaloud', 'Othman - TL Medina':'Othman Zaidan',
  'AlHourani - TL Riyadh':'Mohammad AlHourani', 'Mohammed Subhi - TL Jeddah':'Mohammed Subhi',
  'Telesales - Abdullah Altamimi':'Abdullah Altamimi', 'Telesales-Abdelfattah Khaiyal':'Abdelfattah Khaiyal',
  'El-Kallas - M4':'Mohammad El-Kallas', 'Mohamad Ghannoum - JM3':'Mohamad Ghannoum',
  'Mohamed Abdullah - M3':'Mohamed Abdullah', 'Reham AL Harbi - M2':'Reham AL Harbi',
  'AbdulMajed - TL Riyadh':'Abdulmajed Alghusen', 'Alaa - JM1':'Alaa Alsaber',
  'Telesales - Sulaiman Aljurbua':'Sulaiman Aljurbua', 'Telesales Manager':'Telesales Manager',
  'Mohammed Abdelkader - Eastern':'Mohammed Abdelkader', 'Saif- M5 - Riyadh':'Saif Alyahya',
  'Hussain - TL PK':'Hussain Ali', 'Mohsin - TL PK':'Mohsin Hassan Shah',
}};

const LEADERS = new Set([
  'Khalil Barakat','Mohamad Ghannoum','Othman Zaidan','Sherif Hassan','Mohammed Alkhateeb',
  'Kareem Saber','Aminah Alsheikhi','Rola Aljaloud','Mohammad AlHourani','Mohammed Subhi',
  'Abdullah Altamimi','Abdelfattah Khaiyal','Mohammad El-Kallas','Mohammed Abdelkader',
  'Reham AL Harbi','Mohamed Abdullah','Abdulmajed Alghusen','Sulaiman Aljurbua','Alaa Alsaber',
  'Telesales Manager','Saif Alyahya','Hussain Ali','Mohsin Hassan Shah'
]);

const CONSULTANT_DESIGS = new Set(['Sales Consultant', 'Senior Sales Consultant', 'Telesales Consultant']);

// ============ REVENUE LOOKUP ============
const MN_TO_LABEL = {{{_mn_to_label_js}}};
const REV_TL      = {_rev_tl_json};
const TEAM_REGION = {_team_region_json};
const TEAM_IS_TS  = {_team_is_ts_json};

function getRevenue(teams, mn, type, region) {{
  const label = MN_TO_LABEL[mn];
  if(!label) return null;
  let total = 0;
  for(const t of teams) {{
    if(type==='field' && TEAM_IS_TS[t]) continue;
    if(type==='ts'    && !TEAM_IS_TS[t]) continue;
    if(region!=='all' && TEAM_REGION[t] !== region) continue;
    total += (REV_TL[t] || {{}})[label] || 0;
  }}
  return Math.round(total);
}}

// ============ HELPERS ============
function fmt(n){{ if(n>=1e6) return (n/1e6).toFixed(1)+'M'; if(n>=1e3) return (n/1e3).toFixed(1)+'K'; return Math.round(n).toLocaleString(); }}
function fmtM(n){{ return (n/1e6).toFixed(1)+'M'; }}
function pct(a,b){{ return b>0 ? (a/b*100).toFixed(1)+'%' : '-'; }}

function tvaRating(v){{ if(v>=1) return 'Excellent'; if(v>=0.75) return 'Good'; if(v>=0.5) return 'Average'; return ''; }}
function tvaColor(v){{ if(v>=1) return 'pill-exc'; if(v>=0.75) return 'pill-good'; if(v>=0.5) return 'pill-avg'; return 'pill-poor'; }}

function kpiCard(label, val, sub, regHtml){{ return `<div class="kpi-card"><div class="kpi-label">${{label}}</div><div class="kpi-val">${{val}}</div>${{sub?`<div class="kpi-sub">${{sub}}</div>`:''}}` + (regHtml||'') + '</div>'; }}
function softCard(label, val, sub, regHtml){{ return `<div class="soft-kpi-card"><div class="kpi-label">${{label}}</div><div class="kpi-val">${{val}}</div>${{sub?`<div class="kpi-sub">${{sub}}</div>`:''}}` + (regHtml||'') + '</div>'; }}



function reportCard(title, subtitle, m, isTS, tlBreakdown, extraClass, hideRoster, horizontal, headerExtra='', revenue=null, compact=false, hideTeam=false, hideTotals=false) {{
  const rc = (l, v, tip='', valTip='') => {{
    const lHtml = tip
      ? `<span class="rc-row-label tip" data-tip="${{tip}}">${{l}}</span>`
      : `<span class="rc-row-label">${{l}}</span>`;
    const vHtml = valTip
      ? `<span class="rc-row-val tip tip-r" data-tip="${{valTip}}">${{v}}</span>`
      : `<span class="rc-row-val">${{v}}</span>`;
    return `<div class="rc-row">${{lHtml}}${{vHtml}}</div>`;
  }};
  const pctPill = (val, cls) => `<span class="pill ${{cls}}" style="font-size:10px;padding:1px 6px">${{val}}</span>`;
  const covColor = v => v>=80?'pill-exc':v>=60?'pill-good':v>=40?'pill-avg':'pill-poor';
  const prodColor = v => v>=80?'pill-exc':v>=60?'pill-good':v>=40?'pill-avg':'pill-poor';
  const discColor = v => v<=20?'pill-exc':v<=35?'pill-good':v<=50?'pill-avg':'pill-poor';
  let tlSection = '';
  if(tlBreakdown && tlBreakdown.length > 0) {{
    tlSection = '<div class="rc-section"><div class="rc-section-title">TL Breakdown</div>';
    for(const tl of tlBreakdown) {{
      const pctVal = m.cash > 0 ? Math.round(tl.cash/m.cash*100) : 0;
      tlSection += rc(tl.name, fmt(tl.cash)+' ('+pctVal+'%)');
    }}
    tlSection += '</div>';
  }}
  const financialSection = `
    <div class="rc-section-title">Financial</div>
    ${{rc('Cash Collection', fmt(m.cash), 'Total cash received from clients this period (SAR)')}}
    ${{rc('Target', fmt(m.target), 'Monthly collection target assigned at start of month')}}
    ${{revenue !== null ? rc('Revenue', fmt(revenue), 'Pro-rata revenue from verified active contracts in this period (SAR)') : ''}}
    ${{rc('Cash / Employee', m.bom>0 ? fmt(m.cash/m.bom) : '-', 'Cash collection divided by BOM headcount (SAR per head)')}}
    ${{rc('Packages Sold', m.pkgSold, 'New contracts signed this period (excludes revivals and promo packages)')}}
    ${{rc('Avg Discount (New/Renewed)', m.avgDisc>0 ? pctPill(Math.round(m.avgDisc*100)+'%', discColor(Math.round(m.avgDisc*100))) + (m.avgDiscNew!==null||m.avgDiscRen!==null ? ' <span style="color:#8f8b80;font-size:0.85em">('+(m.avgDiscNew!==null?m.avgDiscNew+'%':'-')+'/'+(m.avgDiscRen!==null?m.avgDiscRen+'%':'-')+')</span>' : '') : '-', 'Avg discount % across all packages sold. Bracket shows split: new clients / renewed clients (from package discount data)')}}
    ${{rc('Net Client Gain', Math.round(m.netGain), 'Active clients at end of month minus active clients at start of month')}}
    ${{tlSection}}`; // used for vertical layout only
  const teamSection = `
    <div class="rc-section-title">Team</div>
    ${{hideRoster ? '' : rc('Active (EOM)', m.active, 'Clients assigned to the team at end of month with Active CRM status')}}
    ${{hideRoster ? '' : rc('BOM (Target>0)', m.bom, 'Staff counted in the team with a collection target > 0 (measured after the 6th of the month)')}}
    ${{rc('Productive Team (>=4K)', m.productive+' '+( m.bom>0 ? pctPill(Math.round(m.productivity)+'%', prodColor(Math.round(m.productivity))) : '' ), 'Consultants who collected >= SAR 4,000 this period. % = productive / BOM')}}
    ${{rc('Coverage %', pctPill(Math.round(m.covPct)+'%', covColor(Math.round(m.covPct))), 'Clients contacted (at least 1 qualified call) / total assigned clients x 100')}}
    ${{rc('Renewed / Pending', m.renewed+' / '+m.pendRen, 'Renewed: clients who signed a new contract this month. Pending: clients with a contract expiring this month who have not yet renewed')}}`;
  const activitySection = (horizontal || hideTotals)
    ? `<div class="rc-section-title">Activity (Avg / Day)</div>
    ${{rc('UQC / Day', m.avgUqc.toFixed(1), 'Unique Qualified Calls per working day (avg)', 'Total this period: '+m.totalUqc.toLocaleString()+' UQC')}}
    ${{rc('DTT / Day', m.avgDtt.toFixed(1)+' mins', 'Daily Talk Time per working day in minutes (avg)', 'Total this period: '+fmt(m.totalDtt)+' min')}}
    ${{isTS ? '' : rc('VM / Day', m.avgVm!==null ? m.avgVm.toFixed(1) : 'N/A', 'Verified in-person meetings per working day (avg)', m.avgVm!==null ? 'Total this period: '+m.totalVm.toLocaleString()+' meetings' : '')}}
    ${{isTS ? '' : rc('Avg Mtg Duration', m.avgMeetingDuration !== null ? m.avgMeetingDuration.toFixed(1)+' min' : 'N/A', 'Average verified meeting duration Jan–Apr 2026 (field sales consultants only)')}}
    ${{isTS ? '' : rc('Meetings / Sale', m.meetingsPerSale !== null ? m.meetingsPerSale.toFixed(1) : 'N/A', 'Unique verified client visits ÷ packages sold (same sources as Overview tab)')}}`
    : `<div class="rc-section-title">Activity (Avg/Day)</div>
    ${{rc('UQC / Day', m.avgUqc.toFixed(1), 'Unique Qualified Calls per working day (avg)', 'Total this period: '+m.totalUqc.toLocaleString()+' UQC')}}
    ${{rc('DTT / Day', m.avgDtt.toFixed(1)+' min', 'Daily Talk Time per working day in minutes (avg)', 'Total this period: '+fmt(m.totalDtt)+' min')}}
    ${{isTS ? '' : rc('VM / Day', m.avgVm!==null ? m.avgVm.toFixed(1) : 'N/A', 'Verified in-person meetings per working day (avg)', m.avgVm!==null ? 'Total this period: '+m.totalVm.toLocaleString()+' meetings' : '')}}
    ${{isTS ? '' : rc('Avg Mtg Duration', m.avgMeetingDuration !== null ? m.avgMeetingDuration.toFixed(1)+' min' : 'N/A', 'Average verified meeting duration Jan–Apr 2026 (field sales consultants only)')}}
    ${{isTS ? '' : rc('Meetings / Sale', m.meetingsPerSale !== null ? m.meetingsPerSale.toFixed(1) : 'N/A', 'Unique verified client visits ÷ packages sold (same sources as Overview tab)')}}
    ${{rc('Total UQC', m.totalUqc.toLocaleString(), 'Total unique qualified calls made this period')}}
    ${{rc('Total DTT', fmt(m.totalDtt)+' min', 'Total daily talk time accumulated this period (minutes)')}}
    ${{isTS ? '' : rc('Total VM', m.totalVm.toLocaleString(), 'Total verified in-person meetings this period')}}`;
  const teamRows =
    (hideRoster ? '' : rc('Active (EOM)', m.active, 'Clients assigned to the team at end of month with Active CRM status')) +
    (hideRoster ? '' : rc('BOM (Target>0)', m.bom, 'Staff counted in the team with a collection target > 0 (measured after the 6th of the month)')) +
    rc('Productive Team (>=4K)', m.productive+' '+(m.bom>0?pctPill(Math.round(m.productivity)+'%',prodColor(Math.round(m.productivity))):''), 'Consultants who collected >= SAR 4,000') +
    rc('Coverage %', pctPill(Math.round(m.covPct)+'%', covColor(Math.round(m.covPct))), 'Clients contacted at least once') +
    rc('Renewed / Pending', m.renewed+' / '+m.pendRen, 'Renewed: clients who signed a new contract this month');
  const activityRows =
    rc('UQC / Day', m.avgUqc.toFixed(1), 'Unique Qualified Calls per working day (avg)', 'Total this period: '+m.totalUqc.toLocaleString()+' UQC') +
    rc('DTT / Day', m.avgDtt.toFixed(1)+' min', 'Daily Talk Time per working day in minutes (avg)', 'Total this period: '+fmt(m.totalDtt)+' min') +
    (isTS ? '' : rc('VM / Day', m.avgVm!==null ? m.avgVm.toFixed(1) : 'N/A', 'Verified in-person meetings per working day (avg)', m.avgVm!==null?'Total this period: '+m.totalVm.toLocaleString()+' meetings':'')) +
    (isTS ? '' : rc('Avg Mtg Duration', m.avgMeetingDuration!==null?m.avgMeetingDuration.toFixed(1)+' min':'N/A', 'Average verified meeting duration Jan–Apr 2026 (field sales consultants only)')) +
    (isTS ? '' : rc('Meetings / Sale', m.meetingsPerSale!==null?m.meetingsPerSale.toFixed(1):'N/A', 'Unique verified client visits ÷ packages sold (same sources as Overview tab)'));
  const _zpPct = m.totalActiveAgencies > 0 ? Math.round(m.zeroPosters / m.totalActiveAgencies * 100) : 0;
  const listingsRows =
    rc('Active Clients', (m.totalActiveAgencies||0).toLocaleString(), 'Active client accounts (agencies, developers, brokers) currently tagged to this team with an active contract') +
    rc('Total Active Listings', (m.totalActiveListings||0).toLocaleString(), 'Total active listings across all clients in this team') +
    rc('Listings / Agency', m.listingsPerAgency!==null?m.listingsPerAgency.toFixed(1):'-', 'Total active listings / active agencies') +
    rc('Zero Posters', m.zeroPosters + ' (' + _zpPct + '%)', 'Paying clients (active contract) with zero active listings on Bayut. % = zero posters / active clients');
  const sumStyle = 'cursor:pointer;user-select:none;font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;padding:4px 0;list-style:none;display:flex;align-items:center;justify-content:space-between';
  const compactBody = compact ? (() => {{
    return `${{financialSection}}
    <details class="rc-collapsible" data-section="team" style="margin-top:8px;border-top:1px dashed var(--border);padding-top:4px" ontoggle="_rcSyncSection('team',this.open)" onclick="event.stopPropagation()">
      <summary style="${{sumStyle}}">Team<span class="rc-caret">&#9662;</span></summary>
      <div style="padding-top:4px">${{teamRows}}</div>
    </details>
    <details class="rc-collapsible" data-section="activity" style="margin-top:2px;border-top:1px dashed var(--border);padding-top:4px" ontoggle="_rcSyncSection('activity',this.open)" onclick="event.stopPropagation()">
      <summary style="${{sumStyle}}">Activity (Avg/Day)<span class="rc-caret">&#9662;</span></summary>
      <div style="padding-top:4px">${{activityRows}}</div>
    </details>
    <details class="rc-collapsible" data-section="listings" style="margin-top:2px;border-top:1px dashed var(--border);padding-top:4px" ontoggle="_rcSyncSection('listings',this.open)" onclick="event.stopPropagation()">
      <summary style="${{sumStyle}}">Listings<span class="rc-caret">&#9662;</span></summary>
      <div style="padding-top:4px">${{listingsRows}}</div>
    </details>`;
  }})() : null;
  const bodyHtml = compact ? compactBody : (horizontal
    ? `<div style="display:flex;gap:0;align-items:stretch;margin-top:10px">
        <div style="flex:1;display:flex;flex-direction:column;justify-content:space-between">
          ${{financialSection}}
        </div>
        <div style="flex:1;border-left:1px dashed var(--border);padding-left:14px;margin-left:14px">
          ${{teamSection}}
          <div style="margin-top:10px;padding-top:8px;border-top:1px dashed var(--border)">${{activitySection}}</div>
        </div>
       </div>`
    : (hideTeam
      ? `${{financialSection}}
         <div class="rc-section">
           <div class="rc-section-title">Activity (Avg/Day)</div>
           ${{activityRows}}
         </div>
         <div class="rc-section"><div class="rc-section-title">Listings</div>${{listingsRows}}</div>`
      : `${{financialSection}}
         <div class="rc-section">${{teamSection}}</div>
         <div class="rc-section">${{activitySection}}</div>`));
  return `<div class="rc-card${{extraClass?' '+extraClass:''}}">
    <div class="rc-card-header">${{headerExtra}}<div style="flex:1;min-width:0"><div class="rc-card-title">${{title}}</div><div class="rc-card-subtitle">${{subtitle}}</div></div><span class="pill ${{tvaColor(m.tva)}}">${{pct(m.cash,m.target)}}</span></div>
    ${{bodyHtml}}
  </div>`;
}}

// Build TL breakdown for a manager's pool in given months (exclude manager's direct team)
function getTlBreakdown(mgAlias, months) {{
  const tls = MGR_TEAMS[mgAlias] || [];
  const breakdown = [];
  for(const tl of tls) {{
    // Skip the manager's own direct team — only show TLs reporting to them
    if(tl === mgAlias) continue;
    let tlPool = [];
    for(const mn of months) {{
      tlPool = tlPool.concat(DATA.filter(r => r.month===mn && r.team===tl));
    }}
    if(tlPool.length === 0) continue;
    const tlCash = tlPool.reduce((s,r) => s+r.coll, 0);
    const tlName = TL_NAMES[tl] || tl;
    breakdown.push({{ name: tlName, cash: tlCash }});
  }}
  return breakdown.sort((a,b) => b.cash - a.cash);
}}

function calcPool(data, month, groupFilter, excludeName) {{
  let pool = data.filter(r => r.month === month && groupFilter(r));
  if(excludeName) pool = pool.filter(r => r.name !== excludeName);
  return pool;
}}

function _discFromFilter(months, bucket, clientType) {{
  const bkt   = (PKG_DISC_BY_FILTER[bucket] || PKG_DISC_BY_FILTER['all'] || {{}});
  const tdata = bkt[clientType] || {{}};
  let total = 0, count = 0;
  for(const mn of months) {{
    const mdata = tdata[String(mn)] || {{}};
    const vals  = Object.values(mdata).filter(v => v > 0);
    if(vals.length) {{ total += vals.reduce((a,b)=>a+b,0)/vals.length; count++; }}
  }}
  return count > 0 ? Math.round(total/count) : null;
}}

function calcMetrics(pool) {{
  // Team members only (exclude leaders) for productivity, soft KPIs, totals
  const members = pool.filter(r => !LEADERS.has(r.name));

  // Hard KPIs — cash/target/TvA/packages use full pool (incl leaders for team total)
  const active = pool.filter(r => r.active_eom);
  const cash = pool.reduce((s,r) => s+r.coll, 0);
  const target = pool.reduce((s,r) => s+r.target, 0);
  const tva = target > 0 ? cash/target : 0;
  const pkgSold = pool.reduce((s,r) => s+r.pkg, 0);
  const pkgHolders = pool.filter(r => r.pkg > 0);
  const avgDisc = pkgHolders.length > 0 ? pkgHolders.reduce((s,r) => s+r.disc, 0)/pkgHolders.length : 0;

  // New / renewal disc split from PKG_DISC_BY_FILTER
  const mnSet  = [...new Set(pool.map(r => r.month))];
  const regs   = [...new Set(pool.map(r => r.region).filter(Boolean))];
  const allTs  = pool.length > 0 && pool.every(r => r.is_ts);
  const allFld = pool.length > 0 && pool.every(r => !r.is_ts);
  let discBkt  = 'all';
  if(regs.length === 1 && regs[0]) discBkt = regs[0];
  else if(allTs)  discBkt = 'ts';
  else if(allFld) discBkt = 'field';
  const avgDiscNew = _discFromFilter(mnSet, discBkt, 'new');
  const avgDiscRen = _discFromFilter(mnSet, discBkt, 'renewal');

  const netGain = pool.reduce((s,r) => s+r.net_gain, 0);
  const cov = pool.reduce((s,r) => s+r.cov, 0);
  const assigned = pool.reduce((s,r) => s+r.assigned, 0);
  const renewed = pool.reduce((s,r) => s+r.renewed, 0);
  const pendRen = pool.reduce((s,r) => s+r.pend_ren, 0);
  const renRate = (renewed+pendRen) > 0 ? renewed/(renewed+pendRen)*100 : 0;

  // Productivity — team members only (exclude leaders)
  const withTarget = members.filter(r => r.target > 0);
  const productive = members.filter(r => r.coll >= 4000);

  // Soft KPIs — team members only, exclude zeros per metric
  const uqcPool = members.filter(r => r.uqc > 0 && r.days > 0);
  const dttPool = members.filter(r => r.dtt > 0 && r.days > 0);
  const vmPool = members.filter(r => r.vm > 0 && r.days > 0 && !r.is_ts);
  const avgUqc = uqcPool.length > 0 ? uqcPool.reduce((s,r) => s + r.uqc/r.days, 0)/uqcPool.length : 0;
  const avgDtt = dttPool.length > 0 ? dttPool.reduce((s,r) => s + r.dtt/r.days, 0)/dttPool.length : 0;
  const avgVm = vmPool.length > 0 ? vmPool.reduce((s,r) => s + r.vm/r.days, 0)/vmPool.length : null;

  // Totals — full pool (including leaders)
  const totalUqc = pool.reduce((s,r) => s+r.uqc, 0);
  const totalDtt = pool.reduce((s,r) => s+r.dtt, 0);
  const totalVm  = pool.reduce((s,r) => s+r.vm,  0);

  // Per-consultant snapshot lookups (unique emails for current pool)
  const uniqueEmails = [...new Set(pool.map(r => r.email).filter(Boolean))];
  const zeroPosters = uniqueEmails.reduce((s,e) => s+(ZERO_POSTERS[e]||0), 0);
  const totalActiveListings = uniqueEmails.reduce((s,e) => s+(CONSULTANT_ACTIVE_LISTINGS[e]||0), 0);
  const totalActiveAgencies = uniqueEmails.reduce((s,e) => s+(CONSULTANT_ACTIVE_AGENCIES[e]||0), 0);
  const listingsPerAgency = totalActiveAgencies > 0 ? Math.round(totalActiveListings/totalActiveAgencies*10)/10 : null;
  const _mtgDurs = uniqueEmails.map(e => CONSULTANT_AVG_MTG_DURATION[e]).filter(v => v !== undefined);
  const avgMeetingDuration = _mtgDurs.length > 0 ? Math.round(_mtgDurs.reduce((s,v)=>s+v,0)/_mtgDurs.length*10)/10 : null;
  const meetingsPerSale = pkgSold > 0 ? Math.round(totalVm/pkgSold*10)/10 : null;

  return {{ active:active.length, bom:withTarget.length, productive:productive.length,
    cash, target, tva, pkgSold, avgDisc, avgDiscNew, avgDiscRen, netGain, cov, assigned, renewed, pendRen, renRate,
    avgUqc, avgDtt, avgVm, totalUqc, totalDtt, totalVm, poolSize:pool.length,
    membersCount:members.length, zeroPosters, totalActiveListings, totalActiveAgencies,
    listingsPerAgency, avgMeetingDuration, meetingsPerSale,
    productivity: withTarget.length > 0 ? productive.length/withTarget.length*100 : 0,
    covPct: assigned > 0 ? cov/assigned*100 : 0
  }};
}}

// ============ REGIONAL SPLIT HELPERS ============
const REGION_ORDER = ['Riyadh','Jeddah','Dammam','Makkah','Medina','Telesales'];
const REGION_SHORT = {{Riyadh:'RUH',Jeddah:'JED',Dammam:'DAM',Makkah:'MKH',Medina:'MED',Telesales:'TS'}};
const REGION_CLASS = {{Riyadh:'rc-ruh',Jeddah:'rc-jed',Dammam:'rc-dam',Makkah:'rc-mkh',Medina:'rc-med',Telesales:'rc-ts'}};

function regSplit(pool, valueFn, fmtFn) {{
  const rows = REGION_ORDER.map(reg => {{
    const rp = pool.filter(r => r.region === reg);
    if(!rp.length) return null;
    const val = valueFn(rp);
    if(val === null || val === undefined || isNaN(val)) return null;
    return {{reg, display: fmtFn(val)}};
  }}).filter(Boolean);
  if(rows.length <= 1) return '';
  return '<div class="kpi-region-split">' +
    rows.map(x => `<div class="kpi-region-row"><span class="kpi-region-label">${{REGION_SHORT[x.reg]||x.reg}}</span><span class="kpi-region-val">${{x.display}}</span></div>`).join('') +
    '</div>';
}}

// ============ OVERVIEW ============
if(typeof ChartDataLabels !== 'undefined') Chart.register(ChartDataLabels);
let collChart, tvaChart, trendChart, pkgOvChart;

// ── Overview drill-down state ──
let _ovDrillMonth = 0;   // 0 = top level
let _ovDrillMgr   = '';  // '' = manager list level
let _ovDrillTl    = '';
let _drillMonthImplicit = false;
let _selTls = [];
let _selMgrs = [];
const _MGR_A_COLOR = '#2a9d8f';
const _MGR_B_COLOR = '#e76f51';
const MGR_POOL_BY_TEAM = new Set(['AlHourani - TL Riyadh']);

// ── Date filter state ──
let _dateFrom = '', _dateTo = '';
let _viewMths = ALL_MONTHS;

function _computeViewMths() {{
  const from = _dateFrom || MONTH_BOUNDS[Math.min(...ALL_MONTHS)][0];
  const to   = _dateTo   || MONTH_BOUNDS[Math.max(...ALL_MONTHS)][1];
  if(!_dateFrom && !_dateTo) return ALL_MONTHS;
  return ALL_MONTHS.filter(mn => {{ const [s,e] = MONTH_BOUNDS[mn]; return from <= e && to >= s; }});
}}
function _onDateFilter() {{
  _dateFrom = document.getElementById('f-date-from').value;
  _dateTo   = document.getElementById('f-date-to').value;
  document.getElementById('ov-date-clear-btn').style.display = (_dateFrom || _dateTo) ? '' : 'none';
  render();
}}
function _clearDateFilter() {{
  _dateFrom = ''; _dateTo = '';
  document.getElementById('f-date-from').value = '';
  document.getElementById('f-date-to').value   = '';
  document.getElementById('ov-date-clear-btn').style.display = 'none';
  render();
}}

// ── Team Lead filter functions ──
function _tlPool(tl, type, region, mn) {{
  const mgTeams = MGR_TEAMS[tl];
  let rows = DATA.filter(r => r.month === mn && (mgTeams ? r.mgr === tl : r.team === tl));
  if(type==='field') rows = rows.filter(r => !r.is_ts);
  if(type==='ts')    rows = rows.filter(r => r.is_ts);
  if(region!=='all') rows = rows.filter(r => r.region === region);
  return rows;
}}

function _toggleTlPanel(e) {{
  e && e.stopPropagation();
  const panel   = document.getElementById('ov-tl-panel');
  const trigger = document.getElementById('ov-tl-trigger');
  if(panel.classList.contains('open')) {{
    panel.classList.remove('open'); trigger.classList.remove('open');
  }} else {{
    panel.classList.add('open'); trigger.classList.add('open');
    setTimeout(() => document.addEventListener('click', _closeTlPanelOutside, {{once:true}}), 0);
  }}
}}

function _closeTlPanelOutside(ev) {{
  const filter = document.getElementById('ov-tl-filter');
  if(filter && !filter.contains(ev.target)) {{
    document.getElementById('ov-tl-panel').classList.remove('open');
    document.getElementById('ov-tl-trigger').classList.remove('open');
  }}
}}

function _clearTlFilter(e) {{
  e && e.stopPropagation();
  _selTls = [];
  _populateTlPanel(); _updateTlTriggerLabel();
  document.getElementById('ov-tl-panel').classList.remove('open');
  document.getElementById('ov-tl-trigger').classList.remove('open');
  _ovDrillMonth = 0; _ovDrillMgr = ''; _ovDrillTl = '';
  render();
}}

function _updateTlTriggerLabel() {{
  const lbl = document.getElementById('ov-tl-trigger-label');
  if(!lbl) return;
  if(_selTls.length === 0) {{
    lbl.textContent = 'All Team Leads';
  }} else if(_selTls.length === 1) {{
    lbl.textContent = TL_NAMES[_selTls[0]] || MGR_NAMES[_selTls[0]] || _selTls[0];
  }} else {{
    const a = (TL_NAMES[_selTls[0]] || MGR_NAMES[_selTls[0]] || _selTls[0]).split(' ')[0];
    const b = (TL_NAMES[_selTls[1]] || MGR_NAMES[_selTls[1]] || _selTls[1]).split(' ')[0];
    lbl.textContent = a + ' vs ' + b;
  }}
}}

function _populateTlPanel() {{
  const scroll = document.getElementById('ov-tl-scroll');
  if(!scroll) return;
  scroll.innerHTML = '';
  const combined = [...new Set([...TL_LIST, ...Object.keys(MGR_TEAMS)])];
  combined.sort((a, b) => {{
    const na = TL_NAMES[a] || MGR_NAMES[a] || a;
    const nb = TL_NAMES[b] || MGR_NAMES[b] || b;
    return na.localeCompare(nb);
  }});
  for(const alias of combined) {{
    const name   = TL_NAMES[alias] || MGR_NAMES[alias] || alias;
    const isChk  = _selTls.includes(alias);
    const isDis  = !isChk && _selTls.length >= 2;
    const idx    = _selTls.indexOf(alias);
    const tagHtml = isChk
      ? `<span class="ov-mgr-tag" style="background:${{idx===0?_MGR_A_COLOR:_MGR_B_COLOR}}">${{idx===0?'A':'B'}}</span>`
      : '';
    const div = document.createElement('div');
    div.className = 'ov-mgr-item' + (isDis ? ' disabled-opt' : '');
    div.innerHTML = `<div class="ov-mgr-cb${{isChk?' chk':''}}"></div><span class="ov-mgr-item-label">${{name}}${{tagHtml}}</span>`;
    div.addEventListener('click', ev => {{ ev.stopPropagation(); _toggleTl(alias); }});
    scroll.appendChild(div);
  }}
}}

function _toggleTl(alias) {{
  if(_selTls.includes(alias)) {{
    _selTls = _selTls.filter(t => t !== alias);
  }} else if(_selTls.length < 2) {{
    _selTls = [..._selTls, alias];
  }}
  _populateTlPanel(); _updateTlTriggerLabel();
  _ovDrillMonth = 0; _ovDrillMgr = '';
  render();
}}

// ── Manager comparison filter functions ──
function _mgrPool(mg, type, region, mn) {{
  let rows = DATA.filter(r => r.month === mn && (MGR_POOL_BY_TEAM.has(mg) ? r.team === mg : r.mgr === mg));
  if(type==='field') rows = rows.filter(r => !r.is_ts);
  if(type==='ts')    rows = rows.filter(r => r.is_ts);
  if(region!=='all') rows = rows.filter(r => r.region === region);
  return rows;
}}

function _toggleMgrPanel(e) {{
  e && e.stopPropagation();
  const panel   = document.getElementById('ov-mgr-panel');
  const trigger = document.getElementById('ov-mgr-trigger');
  if(panel.classList.contains('open')) {{
    panel.classList.remove('open'); trigger.classList.remove('open');
  }} else {{
    panel.classList.add('open'); trigger.classList.add('open');
    setTimeout(() => document.addEventListener('click', _closeMgrPanelOutside, {{once:true}}), 0);
  }}
}}

function _closeMgrPanelOutside(ev) {{
  const filter = document.getElementById('ov-mgr-filter');
  if(filter && !filter.contains(ev.target)) {{
    document.getElementById('ov-mgr-panel').classList.remove('open');
    document.getElementById('ov-mgr-trigger').classList.remove('open');
  }}
}}

function _clearMgrFilter(e) {{
  e && e.stopPropagation();
  _selMgrs = [];
  _populateMgrPanel(); _updateMgrTriggerLabel();
  document.getElementById('ov-mgr-panel').classList.remove('open');
  document.getElementById('ov-mgr-trigger').classList.remove('open');
  _ovDrillMonth = 0; _ovDrillMgr = ''; _ovDrillTl = '';
  render();
}}

function _updateMgrTriggerLabel() {{
  const lbl = document.getElementById('ov-mgr-trigger-label');
  if(!lbl) return;
  if(_selMgrs.length === 0) {{
    lbl.textContent = 'All Managers';
  }} else if(_selMgrs.length === 1) {{
    lbl.textContent = MGR_NAMES[_selMgrs[0]] || _selMgrs[0];
  }} else {{
    const a = (MGR_NAMES[_selMgrs[0]] || _selMgrs[0]).split(' ')[0];
    const b = (MGR_NAMES[_selMgrs[1]] || _selMgrs[1]).split(' ')[0];
    lbl.textContent = a + ' vs ' + b;
  }}
}}

function _populateMgrPanel() {{
  const scroll = document.getElementById('ov-mgr-scroll');
  if(!scroll) return;
  scroll.innerHTML = '';
  for(const mg of Object.keys(MGR_TEAMS)) {{
    const name   = MGR_NAMES[mg] || mg;
    const isChk  = _selMgrs.includes(mg);
    const isDis  = !isChk && _selMgrs.length >= 2;
    const idx    = _selMgrs.indexOf(mg);
    const tagHtml = isChk
      ? `<span class="ov-mgr-tag" style="background:${{idx===0?_MGR_A_COLOR:_MGR_B_COLOR}}">${{idx===0?'A':'B'}}</span>`
      : '';
    const div = document.createElement('div');
    div.className = 'ov-mgr-item' + (isDis ? ' disabled-opt' : '');
    div.innerHTML = `<div class="ov-mgr-cb${{isChk?' chk':''}}"></div><span class="ov-mgr-item-label">${{name}}${{tagHtml}}</span>`;
    div.addEventListener('click', ev => {{ ev.stopPropagation(); _toggleMgr(mg); }});
    scroll.appendChild(div);
  }}
}}

function _toggleMgr(mg) {{
  if(_selMgrs.includes(mg)) {{
    _selMgrs = _selMgrs.filter(m => m !== mg);
  }} else if(_selMgrs.length < 2) {{
    _selMgrs = [..._selMgrs, mg];
  }}
  _populateMgrPanel(); _updateMgrTriggerLabel();
  _ovDrillMonth = 0; _ovDrillMgr = '';
  render();
}}

// ── Daily pool builder (day-level date filter) ──
function _buildDailyPool(type, region) {{
  const from = _dateFrom || MONTH_BOUNDS[Math.min(...ALL_MONTHS)][0];
  const to   = _dateTo   || MONTH_BOUNDS[Math.max(...ALL_MONTHS)][1];
  const refRows = {{}};
  for(const r of DATA) {{
    if(!_viewMths.includes(r.month) || !r.mgr) continue;
    if(!refRows[r.email]) refRows[r.email] = {{target:0,cov:0,assigned:0,net_gain:0,renewed:0,pend_ren:0,_latest:null}};
    refRows[r.email].target   += r.target;
    refRows[r.email].cov      += r.cov;
    refRows[r.email].assigned += r.assigned;
    refRows[r.email].net_gain += r.net_gain;
    refRows[r.email].renewed  += r.renewed;
    refRows[r.email].pend_ren += r.pend_ren;
    if(!refRows[r.email]._latest || r.month > refRows[r.email]._latest.month) refRows[r.email]._latest = r;
  }}
  const pool = [];
  for(const [email, ref] of Object.entries(refRows)) {{
    const lr = ref._latest;
    let c=0,p=0,q=0,t=0,v=0,days=0;
    if(DAILY_METRICS[email]) {{
      for(const [d,dc,dp,dq,dt_,dv] of DAILY_METRICS[email]) {{
        if(d >= from && d <= to) {{ c+=dc; p+=dp; q+=dq; t+=dt_; v+=dv; days++; }}
      }}
    }}
    pool.push({{...lr, coll:c, pkg:p, uqc:q, dtt:t, vm:v, uvm:v, days:Math.max(days,1),
      target:ref.target, cov:ref.cov, assigned:ref.assigned, net_gain:ref.net_gain,
      renewed:ref.renewed, pend_ren:ref.pend_ren}});
  }}
  return pool.filter(r => applyFilters([r], type, region).length > 0);
}}

function drillOvMonth(mn) {{
  _ovDrillMonth = mn;
  _ovDrillMgr   = '';
  render();
}}

function drillOvMgr(mg) {{
  _ovDrillMgr = mg;
  // Skip TL layer when manager has no sub-TLs
  const tls = MGR_TEAMS[mg] || [];
  _ovDrillTl = (tls.length === 1 && tls[0] === mg) ? mg : '';
  render();
}}

function drillOvTl(tl) {{
  _ovDrillTl = tl;
  render();
}}

function backOv() {{
  if(_ovDrillTl !== '') {{
    _ovDrillTl = '';
  }} else if(_ovDrillMgr !== '') {{
    _ovDrillMgr = '';
    if(_drillMonthImplicit) {{ _ovDrillMonth = 0; _drillMonthImplicit = false; }}
  }} else {{
    _ovDrillMonth = 0;
  }}
  render();
}}

function _equalizeCardHeights() {{
  requestAnimationFrame(() => {{
    const cards = [...document.querySelectorAll('#ov-report-cards .rc-card')];
    if (!cards.length) return;
    cards.forEach(c => {{ c.style.minHeight = ''; }});
    const max = Math.max(...cards.map(c => c.offsetHeight));
    if (max > 0) cards.forEach(c => {{ c.style.minHeight = max + 'px'; }});
  }});
}}

function _rcSyncSection(key, isOpen) {{
  document.querySelectorAll('details.rc-collapsible[data-section="'+key+'"]').forEach(d => {{
    if(d.open !== isOpen) d.open = isOpen;
  }});
}}

// Package colour palette
const PKG_COLORS = {{
  'Starter':         '#2a9d8f',
  'Bronze':          '#e07b39',
  'Starter Pro':     '#1565c0',
  'Silver':          '#6a1b9a',
  'Revival':         '#c62828',
  'Platinum Plus':   '#f9a825',
  'Platinum':        '#4a148c',
  'Gold':            '#f57f17',
  'Unknown':         '#546e7a',
  'Other Packages':  '#d81b60',
  'Others':          '#d81b60',
}};

// ── Active Clients & Net Gain combo chart ────────────────────────────────────
let activeGainChart = null;

function renderActiveGainChart(type, region, month) {{
  const months = (month === 0) ? ALL_MONTHS : [month];
  const labels = months.map(mn => MONTH_NAMES[mn]);

  const activeData = months.map(mn => getActiveClients(mn, type, region));
  const gainData   = months.map(mn => {{
    const pool = applyFilters(DATA.filter(r => r.month === mn && r.mgr !== ''), type, region);
    return Math.round(pool.reduce((s,r) => s + r.net_gain, 0));
  }});

  const gainColors  = gainData.map(v => v >= 0 ? 'rgba(67,160,71,0.75)' : 'rgba(229,57,53,0.75)');
  const gainBorders = gainData.map(v => v >= 0 ? '#43a047' : '#e53935');

  // Dynamic y-axis range for active clients
  const validActive = activeData.filter(v => v !== null);
  const acMin = validActive.length ? Math.floor((Math.min(...validActive) - 200) / 100) * 100 : 0;
  const acMax = validActive.length ? Math.ceil ((Math.max(...validActive) + 200) / 100) * 100 : 4000;

  // Net gain symmetric axis
  const maxAbs = Math.max(Math.abs(Math.min(...gainData)), Math.abs(Math.max(...gainData)), 10);
  const gainRange = Math.ceil(maxAbs * 1.4 / 10) * 10;

  const zeroLinePlugin = {{
    id: 'zeroLineAG',
    afterDraw(chart) {{
      const {{ctx, scales: {{x, yGain}}}} = chart;
      const y0 = yGain.getPixelForValue(0);
      ctx.save();
      ctx.strokeStyle = '#e5e1d8';
      ctx.lineWidth = 1;
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.moveTo(x.left, y0);
      ctx.lineTo(x.right, y0);
      ctx.stroke();
      ctx.restore();
    }}
  }};

  if(activeGainChart) {{ activeGainChart.destroy(); activeGainChart = null; }}

  activeGainChart = new Chart(document.getElementById('chart-active-gain'), {{
    plugins: [zeroLinePlugin],
    data: {{
      labels,
      datasets: [
        {{
          type: 'bar',
          label: 'Net Gain',
          data: gainData,
          backgroundColor: gainColors,
          borderColor: gainBorders,
          borderWidth: 1,
          borderRadius: 4,
          borderSkipped: false,
          yAxisID: 'yGain',
          order: 2,
          datalabels: {{
            display: true,
            anchor: ctx => ctx.dataset.data[ctx.dataIndex] >= 0 ? 'end' : 'start',
            align:  ctx => ctx.dataset.data[ctx.dataIndex] >= 0 ? 'end' : 'start',
            formatter: v => (v > 0 ? '+' : '') + v.toLocaleString(),
            color: ctx => ctx.dataset.data[ctx.dataIndex] >= 0 ? '#2e7d32' : '#c62828',
            font: {{ size: 11, weight: '600', family: "'Geist Mono', monospace" }},
          }},
          barPercentage: 0.4,
          categoryPercentage: 0.6,
        }},
        {{
          type: 'line',
          label: 'Active Clients',
          data: activeData,
          borderColor: '#1b1a17',
          backgroundColor: 'rgba(27,26,23,0.05)',
          borderWidth: 2.5,
          pointBackgroundColor: '#ffffff',
          pointBorderColor: '#1b1a17',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.4,
          fill: true,
          spanGaps: true,
          yAxisID: 'yClients',
          order: 1,
          datalabels: {{display:false}},
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{mode:'index', intersect:false}},
      plugins: {{
        legend: {{display:false}},
        datalabels: {{display:false}},
        tooltip: {{
          backgroundColor: '#1b1a17',
          titleColor: '#f7f6f2',
          bodyColor: '#a09d94',
          padding: 14,
          callbacks: {{
            label: ctx => {{
              if(ctx.dataset.label === 'Active Clients')
                return '  Active Clients: ' + (ctx.parsed.y !== null ? ctx.parsed.y.toLocaleString() : 'N/A');
              const v = ctx.parsed.y;
              return '  Net Gain: ' + (v > 0 ? '+' : '') + v.toLocaleString() + '  ' + (v > 0 ? '▲' : v < 0 ? '▼' : '—');
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          grid: {{display:false}},
          border: {{color:'#e5e1d8'}},
          ticks: {{color:'#8f8b80', font:{{size:11}}, maxRotation:0}}
        }},
        yGain: {{
          position: 'left',
          min: -gainRange,
          max:  gainRange,
          grid: {{color:'#f0ede6'}},
          border: {{color:'#e5e1d8'}},
          title: {{display:true, text:'Net Gain (clients)', color:'#8f8b80', font:{{size:10}}}},
          ticks: {{
            color: '#8f8b80',
            font: {{size:10}},
            callback: v => (v > 0 ? '+' : '') + v.toLocaleString()
          }}
        }},
        yClients: {{
          position: 'right',
          min: acMin,
          max: acMax,
          grid: {{display:false}},
          border: {{color:'#e5e1d8', dash:[4,4]}},
          title: {{display:true, text:'Active Clients', color:'#1b1a17', font:{{size:10}}}},
          ticks: {{color:'#1b1a17', font:{{size:10}}, callback: v => v.toLocaleString()}}
        }}
      }}
    }}
  }});
}}

// ── Design-system datalabel presets ─────────────────────────────────────────
const _DL_BAR  = {{anchor:'end',align:'top',display:true,color:'#1f2937',font:{{size:10,weight:700}},backgroundColor:'rgba(255,255,255,.85)',borderRadius:3,padding:{{left:4,right:4,top:2,bottom:2}}}};
const _DL_LINE = {{anchor:'end',align:'top',display:true,color:'#1f2937',font:{{size:9,weight:700}},backgroundColor:'rgba(255,255,255,.85)',borderRadius:3,padding:{{left:3,right:3,top:2,bottom:2}}}};

// ── Package mix overview chart — responds to month filter ───────────────────
const PKG_CATEGORIES = ['Starter','Starter Pro','Bronze','Silver','Gold','Platinum','Platinum Plus','Other Packages'];
const PKG_CAT_COLORS = ['#4f5fcc','#00897b','#1e88e5','#43a047','#fb8c00','#8e24aa','#e53935','#90a4ae'];

// Build legend once (static)
(function() {{
  const legendEl = document.getElementById('pkg-ov-legend');
  PKG_CATEGORIES.forEach((cat,ci) => {{
    legendEl.innerHTML += `<div style="display:flex;align-items:center;gap:6px">
      <span style="width:10px;height:10px;border-radius:2px;background:${{PKG_CAT_COLORS[ci]}};flex-shrink:0"></span>
      ${{cat}}
    </div>`;
  }});
  legendEl.innerHTML += `<div style="display:flex;align-items:center;gap:6px;margin-left:auto">
    <span style="width:18px;height:2px;background:#1b1a17;flex-shrink:0;position:relative">
      <span style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:6px;height:6px;border-radius:50%;background:#ffffff;border:1.5px solid #1b1a17"></span>
    </span>
    Total packages (right axis)
  </div>`;
}})();

function renderPkgOv(month, type) {{
  // month=0 → show all months; month=N → show only that month
  // type: 'all'|'field'|'ts'
  const bucket = (type === 'ts') ? 'ts' : (type === 'field') ? 'field' : 'all';
  const mixData = PKG_MIX[bucket] || PKG_MIX || {{}};

  const months = (month === 0) ? ALL_MONTHS : [month];
  const labels  = months.map(mn => MONTH_NAMES[mn]);

  const SALES = {{}};
  PKG_CATEGORIES.forEach(cat => {{
    SALES[cat] = months.map(mn => (mixData[String(mn)]||{{}})[cat]||0);
  }});

  // Totals from raw mixData (all package keys, including any not in PKG_CATEGORIES)
  // so the trend line matches report card pkg numbers exactly
  const TOTALS = months.map(mn =>
    Object.values(mixData[String(mn)]||{{}}).reduce((s,v) => s+v, 0)
  );

  const barDatasets = PKG_CATEGORIES.map((cat,ci) => ({{
    type: 'bar',
    label: cat,
    data: SALES[cat],
    backgroundColor: PKG_CAT_COLORS[ci] + 'cc',
    hoverBackgroundColor: PKG_CAT_COLORS[ci],
    borderWidth: 0,
    borderRadius: 4,
    borderSkipped: false,
    yAxisID: 'y',
    order: 2,
  }}));

  const lineDataset = {{
    type: 'line',
    label: 'Total Packages',
    data: TOTALS,
    borderColor: '#1b1a17',
    backgroundColor: '#1b1a17',
    borderWidth: 2.5,
    pointBackgroundColor: '#ffffff',
    pointBorderColor: '#1b1a17',
    pointBorderWidth: 2,
    pointRadius: 6,
    pointHoverRadius: 8,
    tension: 0.35,
    yAxisID: 'yLine',
    order: 1,
    z: 10,
    datalabels: {{..._DL_LINE, formatter:v=>v>0?v:''}},
  }};

  // Divider plugin — vertical dashed lines between month clusters
  const dividerPlugin = {{
    id: 'monthDividers',
    afterDraw(chart) {{
      if(months.length < 2) return;
      const {{ctx, scales: {{x, y}}}} = chart;
      ctx.save();
      ctx.strokeStyle = '#e5e1d8';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      for(let m = 1; m < months.length; m++) {{
        const xPos = x.left + m * (x.width / months.length);
        ctx.beginPath();
        ctx.moveTo(xPos, y.top);
        ctx.lineTo(xPos, y.bottom);
        ctx.stroke();
      }}
      ctx.restore();
    }}
  }};

  if(pkgOvChart) {{ pkgOvChart.destroy(); pkgOvChart = null; }}

  pkgOvChart = new Chart(document.getElementById('chart-pkg-ov'), {{
    plugins: [dividerPlugin],
    data: {{ labels, datasets: [...barDatasets, lineDataset] }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      layout: {{padding: {{top:28}}}},
      interaction: {{mode:'index', intersect:false}},
      plugins: {{
        legend: {{display:false}},
        datalabels: {{display:false}},
        tooltip: {{
          backgroundColor: '#1b1a17',
          titleColor: '#f7f6f2',
          bodyColor: '#a09d94',
          padding: 12,
          callbacks: {{
            afterTitle: items => {{
              const mi = items[0].dataIndex;
              return '  Total: ' + TOTALS[mi] + ' packages';
            }},
            label: () => null,
            afterBody: items => {{
              const mi = items[0].dataIndex;
              const total = TOTALS[mi] || 1;
              return PKG_CATEGORIES
                .map(cat => ({{ cat, v: SALES[cat][mi] }}))
                .sort((a,b) => b.v - a.v)
                .map(o => '  ' + o.cat + ': ' + o.v + '  (' + ((o.v/total)*100).toFixed(1) + '%)');
            }},
          }},
        }},
      }},
      scales: {{
        x: {{
          grid: {{display:false}},
          border: {{color:'#e5e1d8'}},
          ticks: {{color:'#8f8b80', font:{{size:10}}, maxRotation:45, minRotation:0, autoSkip:false}},
        }},
        y: {{
          position: 'left',
          grid: {{color:'#f0ede6'}},
          border: {{color:'#e5e1d8'}},
          title: {{display:true, text:'Packages per category', color:'#8f8b80', font:{{size:10}}}},
          ticks: {{color:'#8f8b80', font:{{size:11}}}},
        }},
        yLine: {{
          position: 'right',
          beginAtZero: true,
          grid: {{display:false}},
          border: {{color:'#e5e1d8', dash:[4,4]}},
          title: {{display:true, text:'Total packages sold', color:'#1b1a17', font:{{size:10}}}},
          ticks: {{color:'#1b1a17', font:{{size:11}}}},
        }},
      }},
    }},
  }});

}}

// ── Package Discount % Trend ──────────────────────────────────────────────────
let discTrendChart = null;
let _discClientType  = 'all';
let _lastDiscType    = 'all';
let _lastDiscRegion  = null;
let _discPkgSel = new Set();   // persists across contract-type switches (multi-select)

function setDiscClientType(ct) {{
  _discClientType = ct;
  ['all','new','renewal'].forEach(t => {{
    const btn = document.getElementById('disc-ct-' + t);
    if(!btn) return;
    const active = (t === ct);
    btn.style.background  = active ? '#1b1a17' : '';
    btn.style.color       = active ? '#f7f6f2' : '#8f8b80';
    btn.style.borderColor = active ? '#1b1a17' : '#e5e1d8';
  }});
  initDiscountTrendChart(_lastDiscType, _lastDiscRegion);
}}

const DISC_PKG_CATS = [
  {{ name: 'Starter',       color: '#4f5fcc' }},
  {{ name: 'Starter Pro',   color: '#00897b' }},
  {{ name: 'Bronze',        color: '#1e88e5' }},
  {{ name: 'Silver',        color: '#43a047' }},
  {{ name: 'Gold',          color: '#fb8c00' }},
  {{ name: 'Platinum',      color: '#8e24aa' }},
  {{ name: 'Platinum Plus', color: '#e53935' }},
  {{ name: 'Other Packages',color: '#90a4ae' }},
];
const DISC_MONTHS_LABELS = ["Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026 (MTD)"];
const DISC_MONTH_KEYS    = ["1", "2", "3", "4"];

function getDiscBucket(type, region) {{
  if(region && region !== 'all') return region;
  if(type === 'ts')    return 'ts';
  if(type === 'field') return 'field';
  return 'all';
}}

function initDiscountTrendChart(type, region) {{
  _lastDiscType = type; _lastDiscRegion = region;
  if(discTrendChart) {{ discTrendChart.destroy(); discTrendChart = null; }}

  const bucket = getDiscBucket(type, region);
  const bucketData = (PKG_DISC_BY_FILTER[bucket] || {{}})[_discClientType] || {{}};

  const cats = DISC_PKG_CATS;
  const datasets = cats.map(cat => {{
    const data = DISC_MONTH_KEYS.map(mn => {{
      const v = (bucketData[mn] || {{}})[cat.name];
      return (v !== undefined && v !== null) ? v : null;
    }});
    return {{
      label: cat.name,
      data,
      borderColor: cat.color,
      backgroundColor: 'transparent',
      pointBackgroundColor: '#ffffff',
      pointBorderColor: cat.color,
      pointBorderWidth: 2,
      pointRadius: 5,
      pointHoverRadius: 7,
      borderWidth: 2.5,
      tension: 0.35,
      spanGaps: false,
      datalabels: {{..._DL_LINE, formatter:v=>v!==null?v.toFixed(1)+'%':''}},
    }};
  }});

  // Dynamic y-axis: tight range around actual data for better readability
  const allVals = datasets.flatMap(ds => ds.data).filter(v => v !== null);
  const dataMin = allVals.length ? Math.min(...allVals) : 0;
  const dataMax = allVals.length ? Math.max(...allVals) : 70;
  const dataRange = dataMax - dataMin || 10;
  const yMin = Math.max(0, Math.floor((dataMin - dataRange * 0.4) * 10) / 10);
  const yMax = Math.ceil((dataMax + dataRange * 0.4) * 10) / 10;

  discTrendChart = new Chart(document.getElementById('chart-disc-trend'), {{
    type: 'line',
    data: {{ labels: DISC_MONTHS_LABELS, datasets }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ display: false }},
        datalabels: {{ display: false }},
        tooltip: {{
          backgroundColor: '#1b1a17',
          titleColor: '#f7f6f2',
          bodyColor: '#a09d94',
          titleFont: {{ family: "'Instrument Serif', serif", size: 14, style: 'italic' }},
          bodyFont:  {{ family: "'Geist Mono', monospace", size: 12 }},
          padding: 14,
          filter: item => _discPkgSel.size === 0 || _discPkgSel.has(cats[item.datasetIndex].name),
          itemSort: (a, b) => (b.parsed.y ?? -1) - (a.parsed.y ?? -1),
          callbacks: {{
            label: ctx => ctx.parsed.y !== null
              ? `  ${{ctx.dataset.label}}: ${{ctx.parsed.y.toFixed(1)}}%`
              : null
          }}
        }}
      }},
      scales: {{
        x: {{
          grid: {{ display: false }},
          border:{{color:_bc}},
          ticks:{{color:_tc, font: {{ family: "'Geist Mono', monospace", size: 11 }}, maxRotation: 0 }}
        }},
        y: {{
          grid:{{color:_gc}},
          border:{{color:_bc}},
          min: yMin,
          max: yMax,
          ticks: {{
            color: '#8f8b80',
            font: {{ family: "'Geist Mono', monospace", size: 11 }},
            callback: v => v + '%'
          }},
          title: {{
            display: true,
            text: 'Avg Discount %',
            color: '#8f8b80',
            font: {{ family: "'Geist Mono', monospace", size: 10 }}
          }}
        }}
      }}
    }}
  }});

  // ── Package filter pills ──────────────────────────────────────────────────
  const pillsEl  = document.getElementById('disc-pkg-pills');
  const legendEl = document.getElementById('disc-trend-legend');
  pillsEl.innerHTML  = '';
  legendEl.innerHTML = '';

  // ── Pure visual render: applies current _discPkgSel state to chart + pills + legend ──
  function _renderDiscVisuals() {{
    const sel = _discPkgSel.size;
    cats.forEach((c, j) => {{
      const active = sel === 0 || _discPkgSel.has(c.name);
      discTrendChart.data.datasets[j].borderColor          = active ? c.color : c.color + '1a';
      discTrendChart.data.datasets[j].pointBorderColor     = active ? c.color : c.color + '1a';
      discTrendChart.data.datasets[j].pointBackgroundColor = active ? '#ffffff' : c.color + '1a';
      discTrendChart.data.datasets[j].borderWidth          = (active && sel > 0) ? 3 : (active ? 2.5 : 1);
      discTrendChart.data.datasets[j].pointRadius          = (active && sel > 0) ? 6 : (active ? 5 : 2);
      // data labels only for explicitly selected packages
      discTrendChart.data.datasets[j].datalabels = {{
        ..._DL_LINE,
        display: sel > 0 && _discPkgSel.has(c.name),
        formatter: v => v !== null ? v.toFixed(1) + '%' : '',
      }};
    }});
    discTrendChart.update('none');

    // sync pill styles
    Array.from(pillsEl.children).forEach(el => {{
      const isAll = el.dataset.pkg === '__all__';
      if(isAll) {{
        const allActive = sel === 0;
        el.style.background  = allActive ? '#1b1a17' : '';
        el.style.color       = allActive ? '#f7f6f2' : '#8f8b80';
        el.style.borderColor = allActive ? '#1b1a17' : '#e5e1d8';
      }} else {{
        const cat    = cats.find(c => c.name === el.dataset.pkg);
        const active = _discPkgSel.has(el.dataset.pkg);
        el.style.background  = active ? cat.color : '';
        el.style.color       = active ? '#fff'    : '#8f8b80';
        el.style.borderColor = active ? cat.color : '#e5e1d8';
      }}
    }});

    // sync legend styles
    Array.from(legendEl.children).forEach((el, j) => {{
      el.style.opacity = (sel === 0 || _discPkgSel.has(cats[j].name)) ? '1' : '0.25';
    }});
  }}

  // ── Toggle a package in/out of the selection ──
  function applyDiscSelection(name) {{
    if(name === null) {{
      _discPkgSel = new Set(); // "All" — clear selection
    }} else {{
      if(_discPkgSel.has(name)) _discPkgSel.delete(name);
      else _discPkgSel.add(name);
    }}
    _renderDiscVisuals();
  }}

  // "All" pill
  const allPill = document.createElement('button');
  allPill.dataset.pkg = '__all__';
  allPill.textContent = 'All';
  allPill.style.cssText = 'font-family:inherit;font-size:0.68rem;font-weight:600;padding:3px 12px;border-radius:20px;border:1px solid #1b1a17;background:#1b1a17;color:#f7f6f2;cursor:pointer;transition:all 0.15s;letter-spacing:0.04em';
  allPill.addEventListener('click', () => applyDiscSelection(null));
  pillsEl.appendChild(allPill);

  // One pill per package — multi-select: click toggles in/out of selection
  cats.forEach(cat => {{
    const pill = document.createElement('button');
    pill.dataset.pkg = cat.name;
    pill.textContent = cat.name;
    pill.style.cssText = `font-family:inherit;font-size:0.68rem;font-weight:500;padding:3px 12px;border-radius:20px;border:1px solid #e5e1d8;background:;color:#8f8b80;cursor:pointer;transition:all 0.15s;letter-spacing:0.04em`;
    pill.addEventListener('click', () => applyDiscSelection(cat.name));
    pillsEl.appendChild(pill);
  }});

  // ── Legend — name + swatch, with hover-focus (suppressed when pill is active)
  cats.forEach((cat, i) => {{
    const item = document.createElement('div');
    item.style.cssText = 'display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:6px;cursor:pointer;border:1px solid transparent;transition:background 0.15s,opacity 0.15s';
    item.innerHTML = `
      <div style="width:20px;height:2.5px;background:${{cat.color}};border-radius:2px;flex-shrink:0;position:relative">
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:7px;height:7px;border-radius:50%;background:#fff;border:2px solid ${{cat.color}}"></div>
      </div>
      <span style="font-size:0.7rem;font-weight:500;color:#1b1a17">${{cat.name}}</span>`;

    item.addEventListener('click', () => {{
      applyDiscSelection(cat.name);
    }});

    item.addEventListener('mouseenter', () => {{
      if(_discPkgSel.size > 0) return;   // selection active — don't override
      cats.forEach((c, j) => {{
        discTrendChart.data.datasets[j].borderColor          = j === i ? c.color : c.color + '28';
        discTrendChart.data.datasets[j].pointBorderColor     = j === i ? c.color : c.color + '28';
        discTrendChart.data.datasets[j].pointBackgroundColor = j === i ? '#ffffff' : c.color + '28';
        discTrendChart.data.datasets[j].borderWidth          = j === i ? 3 : 1.5;
        discTrendChart.data.datasets[j].pointRadius          = j === i ? 6 : 3;
      }});
      discTrendChart.update('none');
      Array.from(legendEl.children).forEach((el, j) => {{
        el.style.opacity    = j === i ? '1' : '0.3';
        el.style.background = j === i ? '#f7f6f2' : '';
        el.style.borderColor= j === i ? '#e5e1d8' : 'transparent';
      }});
    }});

    item.addEventListener('mouseleave', () => {{
      if(_discPkgSel.size > 0) {{
        // restore to current selection state rather than full-all
        _renderDiscVisuals();
        Array.from(legendEl.children).forEach(el => {{
          el.style.background  = '';
          el.style.borderColor = 'transparent';
        }});
        return;
      }}
      cats.forEach((c, j) => {{
        discTrendChart.data.datasets[j].borderColor          = c.color;
        discTrendChart.data.datasets[j].pointBorderColor     = c.color;
        discTrendChart.data.datasets[j].pointBackgroundColor = '#ffffff';
        discTrendChart.data.datasets[j].borderWidth          = 2.5;
        discTrendChart.data.datasets[j].pointRadius          = 5;
      }});
      discTrendChart.update('none');
      Array.from(legendEl.children).forEach(el => {{
        el.style.opacity    = '1';
        el.style.background = '';
        el.style.borderColor= 'transparent';
      }});
    }});

    legendEl.appendChild(item);
  }});

  // Reapply current selection visuals (persists across contract-type switches)
  _renderDiscVisuals();
}}

// ── Employee Productivity dual-axis line chart ────────────────────────────────
let empProdChart = null;

function renderEmpProdChart(type, region, month) {{
  if(empProdChart) {{ empProdChart.destroy(); empProdChart = null; }}

  const months = month && month > 0 ? [month] : ALL_MONTHS;
  const labels = months.map(mn => MONTH_NAMES[mn]);

  const cashPerEmp = months.map(mn => {{
    const pool = applyFilters(DATA.filter(r => r.month === mn && r.mgr !== ''), type, region);
    const bom  = pool.filter(r => !r.is_leader && r.target > 0).length;
    const cash = pool.reduce((s, r) => s + r.coll, 0);
    return bom > 0 ? Math.round(cash / bom) : null;
  }});

  const pkgsPerEmp = months.map(mn => {{
    const pool = applyFilters(DATA.filter(r => r.month === mn && r.mgr !== ''), type, region);
    const bom  = pool.filter(r => !r.is_leader && r.target > 0).length;
    const pkgs = pool.reduce((s, r) => s + r.pkg, 0);
    return bom > 0 ? +(pkgs / bom).toFixed(2) : null;
  }});

  // Dynamic y-axis for cash
  const cashVals = cashPerEmp.filter(v => v !== null);
  const cashMin  = cashVals.length ? Math.min(...cashVals) : 0;
  const cashMax  = cashVals.length ? Math.max(...cashVals) : 10000;
  const cashPad  = (cashMax - cashMin) * 0.4 || cashMax * 0.2;
  const yCashMin = Math.max(0, Math.floor((cashMin - cashPad) / 500) * 500);
  const yCashMax = Math.ceil((cashMax + cashPad) / 500) * 500;

  // Dynamic y-axis for pkgs — always show a bit above max
  const pkgVals = pkgsPerEmp.filter(v => v !== null);
  const pkgMax  = pkgVals.length ? Math.max(...pkgVals) : 2;
  const pkgMin  = pkgVals.length ? Math.min(...pkgVals) : 0;
  const pkgPad  = (pkgMax - pkgMin) * 0.4 || 0.2;
  const yPkgMin = Math.max(0, +((pkgMin - pkgPad).toFixed(1)));
  const yPkgMax = +((pkgMax + pkgPad).toFixed(1));

  empProdChart = new Chart(document.getElementById('chart-emp-prod'), {{
    type: 'line',
    data: {{
      labels,
      datasets: [
        {{
          label: 'Cash / Employee',
          data: cashPerEmp,
          borderColor: '#0d9488',
          backgroundColor: 'rgba(13,148,136,0.07)',
          borderWidth: 2.5,
          pointBackgroundColor: '#ffffff',
          pointBorderColor: '#0d9488',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.4,
          fill: true,
          yAxisID: 'yCash',
          order: 1,
          datalabels: {{ display: false }},
        }},
        {{
          label: 'Packages / Employee',
          data: pkgsPerEmp,
          borderColor: '#b91c1c',
          backgroundColor: 'rgba(185,28,28,0.07)',
          borderWidth: 2.5,
          pointBackgroundColor: '#ffffff',
          pointBorderColor: '#b91c1c',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.4,
          fill: true,
          yAxisID: 'yPkgs',
          order: 2,
          datalabels: {{ display: false }},
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ display: false }},
        datalabels: {{ display: false }},
        tooltip: {{
          backgroundColor: '#1b1a17',
          titleColor: '#f7f6f2',
          bodyColor: '#a09d94',
          titleFont: {{ family: "'Instrument Serif', serif", size: 14, style: 'italic' }},
          bodyFont:  {{ family: "'Geist Mono', monospace", size: 12 }},
          padding: 14,
          callbacks: {{
            label: ctx => {{
              if(ctx.dataset.label === 'Cash / Employee')
                return `  Cash / emp: SAR ${{ctx.parsed.y !== null ? ctx.parsed.y.toLocaleString() : '—'}}`;
              return `  Pkgs / emp: ${{ctx.parsed.y !== null ? ctx.parsed.y.toFixed(2) : '—'}}`;
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          grid: {{ display: false }},
          border: {{ color: '#e5e1d8' }},
          ticks: {{ color: '#8f8b80', font: {{ family: "'Geist Mono', monospace", size: 11 }}, maxRotation: 0 }}
        }},
        yCash: {{
          position: 'left',
          min: yCashMin,
          max: yCashMax,
          grid: {{ color: '#f0ede6' }},
          border: {{ color: '#e5e1d8' }},
          title: {{ display: true, text: 'Cash / Employee (SAR)', color: '#0d9488', font: {{ family: "'Geist Mono', monospace", size: 10 }} }},
          ticks: {{
            color: '#0d9488',
            font: {{ family: "'Geist Mono', monospace", size: 10 }},
            callback: v => v >= 1000 ? (v/1000).toFixed(1)+'K' : v
          }}
        }},
        yPkgs: {{
          position: 'right',
          min: yPkgMin,
          max: yPkgMax,
          grid: {{ display: false }},
          border: {{ color: '#e5e1d8', dash: [4, 4] }},
          title: {{ display: true, text: 'Packages / Employee', color: '#b91c1c', font: {{ family: "'Geist Mono', monospace", size: 10 }} }},
          ticks: {{
            color: '#b91c1c',
            font: {{ family: "'Geist Mono', monospace", size: 10 }},
            callback: v => v.toFixed(1),
            maxTicksLimit: 5,
          }}
        }}
      }}
    }}
  }});
}}

// ── Renewals monthly trend ────────────────────────────────────────────────────
let renewalsChart = null;

function renderRenewalsTrend(type, region, month) {{
  if(renewalsChart) {{ renewalsChart.destroy(); renewalsChart = null; }}

  const months = month && month > 0 ? [month] : ALL_MONTHS;
  const labels  = months.map(mn => MONTH_NAMES[mn]);

  const renewedData  = months.map(mn => {{
    const pool = applyFilters(DATA.filter(r => r.month === mn && r.mgr !== ''), type, region);
    return pool.reduce((s, r) => s + r.renewed, 0);
  }});
  const pendingData  = months.map(mn => {{
    const pool = applyFilters(DATA.filter(r => r.month === mn && r.mgr !== ''), type, region);
    return pool.reduce((s, r) => s + r.pend_ren, 0);
  }});
  const totals = months.map((_, i) => renewedData[i] + pendingData[i]);
  const rates  = months.map((_, i) =>
    totals[i] > 0 ? +((renewedData[i] / totals[i]) * 100).toFixed(1) : 0
  );
  const avgRate = rates.length ? +(rates.reduce((a, b) => a + b, 0) / rates.length).toFixed(1) : 0;

  const avgBandPlugin = {{
    id: 'renewalAvgBand',
    afterDraw(chart) {{
      const {{ ctx, scales }} = chart;
      if(!scales.yRate) return;
      const {{ x, yRate }} = scales;
      const yAvg = yRate.getPixelForValue(avgRate);
      const bandH = Math.abs(yRate.getPixelForValue(avgRate - 3) - yAvg);
      ctx.save();
      ctx.fillStyle = 'rgba(27,26,23,0.06)';
      ctx.fillRect(x.left, yAvg - bandH / 2, x.right - x.left, bandH);
      ctx.strokeStyle = 'rgba(27,26,23,0.2)';
      ctx.lineWidth = 1;
      ctx.setLineDash([5, 4]);
      ctx.beginPath();
      ctx.moveTo(x.left, yAvg);
      ctx.lineTo(x.right, yAvg);
      ctx.stroke();
      ctx.restore();
    }}
  }};

  renewalsChart = new Chart(document.getElementById('chart-renewals'), {{
    plugins: [avgBandPlugin],
    data: {{
      labels,
      datasets: [
        {{
          type: 'bar',
          label: 'Renewed Clients',
          data: renewedData,
          backgroundColor: 'rgba(42,157,111,0.75)',
          hoverBackgroundColor: '#2a9d6f',
          borderWidth: 0,
          borderRadius: {{ topLeft: 0, topRight: 0, bottomLeft: 4, bottomRight: 4 }},
          borderSkipped: false,
          stack: 'renewals',
          yAxisID: 'yCount',
          barPercentage: 0.5,
          categoryPercentage: 0.6,
          order: 2,
          datalabels: {{ display: false }},
        }},
        {{
          type: 'bar',
          label: 'Pending Renewals',
          data: pendingData,
          backgroundColor: 'rgba(232,168,56,0.65)',
          hoverBackgroundColor: '#e8a838',
          borderWidth: 0,
          borderRadius: {{ topLeft: 4, topRight: 4, bottomLeft: 0, bottomRight: 0 }},
          borderSkipped: false,
          stack: 'renewals',
          yAxisID: 'yCount',
          barPercentage: 0.5,
          categoryPercentage: 0.6,
          order: 2,
          datalabels: {{ display: false }},
        }},
        {{
          type: 'line',
          label: 'Renewal Rate %',
          data: rates,
          borderColor: '#1b1a17',
          backgroundColor: 'rgba(27,26,23,0.06)',
          borderWidth: 2.5,
          pointBackgroundColor: rates.map(r => r >= avgRate ? '#2a9d6f' : '#e53935'),
          pointBorderColor: '#ffffff',
          pointBorderWidth: 1.5,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.35,
          fill: false,
          yAxisID: 'yRate',
          order: 1,
          datalabels: {{ display: false }},
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ display: false }},
        datalabels: {{ display: false }},
        tooltip: {{
          backgroundColor: '#1b1a17',
          titleColor: '#f7f6f2',
          bodyColor: '#a09d94',
          titleFont: {{ family: "'Instrument Serif', serif", size: 14, style: 'italic' }},
          bodyFont:  {{ family: "'Geist Mono', monospace", size: 12 }},
          padding: 14,
          callbacks: {{
            label: ctx => {{
              if(ctx.dataset.label === 'Renewal Rate %') {{
                const aboveAvg = ctx.parsed.y >= avgRate;
                return `  Rate: ${{ctx.parsed.y}}%  (${{aboveAvg ? '↑ above' : '↓ below'}} avg ${{avgRate}}%)`;
              }}
              if(ctx.dataset.label === 'Renewed Clients')
                return `  Renewed: ${{ctx.parsed.y.toLocaleString()}}`;
              if(ctx.dataset.label === 'Pending Renewals')
                return [`  Pending: ${{ctx.parsed.y.toLocaleString()}}`, `  Total pool: ${{totals[ctx.dataIndex].toLocaleString()}}`];
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          stacked: true,
          grid: {{ display: false }},
          border: {{ color: '#e5e1d8' }},
          ticks: {{ color: '#8f8b80', font: {{ family: "'Geist Mono', monospace", size: 11 }}, maxRotation: 0 }}
        }},
        yCount: {{
          stacked: true,
          position: 'left',
          grid: {{ color: '#f0ede6' }},
          border: {{ color: '#e5e1d8' }},
          title: {{ display: true, text: 'Clients', color: '#8f8b80', font: {{ family: "'Geist Mono', monospace", size: 10 }} }},
          ticks: {{ color: '#8f8b80', font: {{ family: "'Geist Mono', monospace", size: 10 }}, callback: v => v.toLocaleString() }}
        }},
        yRate: {{
          position: 'right',
          min: 0,
          max: 100,
          grid: {{ display: false }},
          border: {{ color: '#e5e1d8', dash: [4, 4] }},
          title: {{ display: true, text: 'Renewal Rate %', color: '#1b1a17', font: {{ family: "'Geist Mono', monospace", size: 10 }} }},
          ticks: {{ color: '#1b1a17', font: {{ family: "'Geist Mono', monospace", size: 10 }}, callback: v => v + '%', maxTicksLimit: 6 }}
        }}
      }}
    }}
  }});
}}

// ── Soft KPI monthly trend panels ────────────────────────────────────────────
const SOFT_KPI_CHARTS = {{}};

// ── Soft KPI independent team-type filter ────────────────────────────────────
let _softKpiType = 'all';
function _onSoftKpiTypeChange() {{
  _softKpiType = document.getElementById('soft-kpi-type').value;
  const month  = +document.getElementById('f-month').value;
  const region = document.getElementById('f-region').value;
  if(month > 0) {{
    if(_selTls.length > 0)       renderSoftKpiDailyView(month, _softKpiType, region, _selTls,  true);
    else if(_selMgrs.length > 0) renderSoftKpiDailyView(month, _softKpiType, region, _selMgrs, false);
    else                         renderSoftKpiDailyView(month, _softKpiType, region, [],        null);
  }} else {{
    renderSoftKpiTrends(_softKpiType, region, 0);
  }}
}}

function renderSoftKpiTrends(type, region, month) {{
  type = _softKpiType;   // always driven by the dedicated soft KPI type filter
  const el = document.getElementById('ov-soft-kpi-trends');
  const isTS = type === 'ts';

  if(_selTls.length === 2) {{
    const labels    = _viewMths.map(mn => MONTH_NAMES[mn]);
    const mgrColors = [_MGR_A_COLOR, _MGR_B_COLOR];
    const kpiDefs = [
      {{ id:'dtt', label:'Daily Talk Time',        unit:'avg mins / day',  color:'#f0a050', targetLow: isTS?50:15, targetHigh: isTS?70:25 }},
      {{ id:'uqc', label:'Unique Qualified Calls', unit:'avg calls / day', color:'#4f5fcc', targetLow: isTS?20:8,  targetHigh: isTS?30:16 }},
      ...( isTS ? [] : [{{ id:'vm', label:'Verified Meetings', unit:'avg meetings / day', color:'#00897b', targetLow:2.5, targetHigh:4.5 }}] )
    ];
    for(const k of Object.keys(SOFT_KPI_CHARTS)) {{ if(SOFT_KPI_CHARTS[k]) {{ SOFT_KPI_CHARTS[k].destroy(); SOFT_KPI_CHARTS[k]=null; }} }}
    el.innerHTML = `<div style="padding:8px 20px 4px;font-size:11px;font-weight:700;color:#8f8b80;text-transform:uppercase;letter-spacing:.08em">TL Comparison</div>`;
    kpiDefs.forEach(kpi => {{
      const canvasId = `chart-softkpi-${{kpi.id}}`;
      const datasets = _selTls.map((tl, idx) => {{
        const data = _viewMths.map(mn => {{ const m = calcMetrics(_tlPool(tl,type,region,mn)); return parseFloat((kpi.id==='dtt'?m.avgDtt:kpi.id==='uqc'?m.avgUqc:m.avgVm??0).toFixed(1)); }});
        return {{ label: TL_NAMES[tl]||MGR_NAMES[tl]||tl, data, borderColor:mgrColors[idx], backgroundColor:'transparent', borderWidth:2.5, pointBackgroundColor:'#fff', pointBorderColor:mgrColors[idx], pointBorderWidth:2, pointRadius:5, tension:0.4, spanGaps:true, datalabels:{{..._DL_LINE, formatter:v=>v!==null?v.toFixed(1):''}} }};
      }});
      el.innerHTML += `<div style="background:#fff;border:1px solid #e5e1d8;border-radius:12px;overflow:hidden;margin-bottom:14px"><div style="padding:12px 20px 10px;border-bottom:1px solid #e5e1d8;background:#faf9f5;display:flex;align-items:center;gap:10px"><div style="width:3px;height:28px;border-radius:2px;background:${{kpi.color}};flex-shrink:0"></div><div style="font-size:13px;font-weight:600;color:var(--text)">${{kpi.label}}</div></div><div style="padding:16px 20px 14px"><div style="position:relative;height:140px"><canvas id="${{canvasId}}"></canvas></div></div></div>`;
      requestAnimationFrame(() => {{
        const canvas = document.getElementById(canvasId); if(!canvas) return;
        const bandPlugin = {{ id:'tb_'+kpi.id, beforeDraw(chart){{ const {{ctx,scales:{{x,y}}}}=chart; const yT=y.getPixelForValue(kpi.targetHigh); const yB=y.getPixelForValue(kpi.targetLow); ctx.save(); ctx.fillStyle=kpi.color+'22'; ctx.fillRect(x.left,yT,x.right-x.left,yB-yT); ctx.restore(); }} }};
        const _kv=datasets.flatMap(d=>d.data).filter(v=>v>0); const _km=_kv.length?Math.min(..._kv):0; const _kx=_kv.length?Math.max(..._kv):kpi.targetHigh; const _kr=Math.max(_kx-_km,_kx*0.15,0.5); const _kyMin=Math.max(0,Math.floor((_km-_kr*0.4)*10)/10); const _kyMax=Math.ceil((_kx+_kr*0.4)*10)/10;
        SOFT_KPI_CHARTS[kpi.id] = new Chart(canvas, {{ plugins:[bandPlugin], type:'line', data:{{labels,datasets}}, options:{{ responsive:true, maintainAspectRatio:false, plugins:{{ legend:{{position:'bottom',labels:{{font:{{size:11}},usePointStyle:true}}}}, datalabels:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+ctx.parsed.y.toFixed(1)}} }} }}, scales:{{ y:{{min:_kyMin,max:_kyMax,ticks:{{callback:v=>v.toFixed(1)}} }} }} }} }});
      }});
    }});
    return;
  }}
  if(_selMgrs.length === 2) {{
    const labels    = _viewMths.map(mn => MONTH_NAMES[mn]);
    const mgrColors = [_MGR_A_COLOR, _MGR_B_COLOR];
    const kpiDefs = [
      {{ id:'dtt', label:'Daily Talk Time',        unit:'avg mins / day',  color:'#f0a050', targetLow: isTS?50:15, targetHigh: isTS?70:25 }},
      {{ id:'uqc', label:'Unique Qualified Calls', unit:'avg calls / day', color:'#4f5fcc', targetLow: isTS?20:8,  targetHigh: isTS?30:16 }},
      ...( isTS ? [] : [{{ id:'vm', label:'Verified Meetings', unit:'avg meetings / day', color:'#00897b', targetLow:2.5, targetHigh:4.5 }}] )
    ];
    for(const k of Object.keys(SOFT_KPI_CHARTS)) {{ if(SOFT_KPI_CHARTS[k]) {{ SOFT_KPI_CHARTS[k].destroy(); SOFT_KPI_CHARTS[k]=null; }} }}
    el.innerHTML = `<div style="padding:8px 20px 4px;font-size:11px;font-weight:700;color:#8f8b80;text-transform:uppercase;letter-spacing:.08em">Manager Comparison</div>`;
    kpiDefs.forEach(kpi => {{
      const canvasId = `chart-softkpi-${{kpi.id}}`;
      const datasets = _selMgrs.map((mg, idx) => {{
        const data = _viewMths.map(mn => {{ const m = calcMetrics(_mgrPool(mg,type,region,mn)); return parseFloat((kpi.id==='dtt'?m.avgDtt:kpi.id==='uqc'?m.avgUqc:m.avgVm??0).toFixed(1)); }});
        return {{ label: MGR_NAMES[mg]||mg, data, borderColor:mgrColors[idx], backgroundColor:'transparent', borderWidth:2.5, pointBackgroundColor:'#fff', pointBorderColor:mgrColors[idx], pointBorderWidth:2, pointRadius:5, tension:0.4, spanGaps:true, datalabels:{{..._DL_LINE, formatter:v=>v!==null?v.toFixed(1):''}} }};
      }});
      el.innerHTML += `<div style="background:#fff;border:1px solid #e5e1d8;border-radius:12px;overflow:hidden;margin-bottom:14px"><div style="padding:12px 20px 10px;border-bottom:1px solid #e5e1d8;background:#faf9f5;display:flex;align-items:center;gap:10px"><div style="width:3px;height:28px;border-radius:2px;background:${{kpi.color}};flex-shrink:0"></div><div style="font-size:13px;font-weight:600;color:var(--text)">${{kpi.label}}</div></div><div style="padding:16px 20px 14px"><div style="position:relative;height:140px"><canvas id="${{canvasId}}"></canvas></div></div></div>`;
      requestAnimationFrame(() => {{
        const canvas = document.getElementById(canvasId); if(!canvas) return;
        const bandPlugin = {{ id:'tb_'+kpi.id, beforeDraw(chart){{ const {{ctx,scales:{{x,y}}}}=chart; const yT=y.getPixelForValue(kpi.targetHigh); const yB=y.getPixelForValue(kpi.targetLow); ctx.save(); ctx.fillStyle=kpi.color+'22'; ctx.fillRect(x.left,yT,x.right-x.left,yB-yT); ctx.restore(); }} }};
        const _mkv=datasets.flatMap(d=>d.data).filter(v=>v>0); const _mkm=_mkv.length?Math.min(..._mkv):0; const _mkx=_mkv.length?Math.max(..._mkv):kpi.targetHigh; const _mkr=Math.max(_mkx-_mkm,_mkx*0.15,0.5); const _mkyMin=Math.max(0,Math.floor((_mkm-_mkr*0.4)*10)/10); const _mkyMax=Math.ceil((_mkx+_mkr*0.4)*10)/10;
        SOFT_KPI_CHARTS[kpi.id] = new Chart(canvas, {{ plugins:[bandPlugin], type:'line', data:{{labels,datasets}}, options:{{ responsive:true, maintainAspectRatio:false, plugins:{{ legend:{{position:'bottom',labels:{{font:{{size:11}},usePointStyle:true}}}}, datalabels:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+ctx.parsed.y.toFixed(1)}} }} }}, scales:{{ y:{{min:_mkyMin,max:_mkyMax,ticks:{{callback:v=>v.toFixed(1)}} }} }} }} }});
      }});
    }});
    return;
  }}

  // Compute per-month averages from DATA
  const monthData = _viewMths.map(mn => {{
    const pool = applyFilters(DATA.filter(r => r.month === mn && r.mgr !== ''), type, region);
    const m = calcMetrics(pool);
    return {{ mn, avgDtt: m.avgDtt, avgUqc: m.avgUqc, avgVm: m.avgVm }};
  }});

  const labels  = _viewMths.map(mn => MONTH_NAMES[mn]);
  const dttData = monthData.map(d => parseFloat(d.avgDtt.toFixed(1)));
  const uqcData = monthData.map(d => parseFloat(d.avgUqc.toFixed(1)));
  const vmData  = isTS ? null : monthData.map(d => d.avgVm !== null ? parseFloat(d.avgVm.toFixed(1)) : null);

  // Determine selected index for header stats
  const selIdx = (month && month > 0) ? _viewMths.indexOf(month) : _viewMths.length - 1;
  const selLabel = labels[selIdx];

  const kpis = [
    {{ id:'dtt', label:'Daily Talk Time',        unit:'avg mins / day',     color:'#f0a050', data:dttData, targetLow: isTS?50:15, targetHigh: isTS?70:25 }},
    {{ id:'uqc', label:'Unique Qualified Calls', unit:'avg calls / day',    color:'#4f5fcc', data:uqcData, targetLow: isTS?20:8,  targetHigh: isTS?30:16 }},
    ...( isTS ? [] : [{{ id:'vm', label:'Verified Meetings', unit:'avg meetings / day', color:'#00897b', data:vmData, targetLow:2.5, targetHigh:4.5 }}] )
  ];

  el.innerHTML = `<div style="padding:8px 20px 4px;font-size:11px;font-weight:700;color:#8f8b80;text-transform:uppercase;letter-spacing:.08em">Monthly Averages</div>`;

  kpis.forEach(kpi => {{
    // Destroy old chart if exists
    if(SOFT_KPI_CHARTS[kpi.id]) {{ SOFT_KPI_CHARTS[kpi.id].destroy(); SOFT_KPI_CHARTS[kpi.id] = null; }}

    // Stats reflect selected month; period avg uses months up to and including selected
    const latest = kpi.data[selIdx] ?? 0;
    const prev   = selIdx > 0 ? (kpi.data[selIdx - 1] ?? 0) : 0;
    const delta  = latest - prev;
    const deltaPct = prev !== 0 ? Math.abs((delta/prev)*100).toFixed(1) : '0';
    const deltaHtml = delta > 0.05
      ? `<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:6px;background:#e8f5e9;color:#1b5e20">▲ ${{deltaPct}}%</span>`
      : delta < -0.05
      ? `<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:6px;background:#ffebee;color:#b71c1c">▼ ${{deltaPct}}%</span>`
      : `<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:6px;background:#e8f2ec;color:#506b5a">— flat</span>`;
    const slicedData = kpi.data.slice(0, selIdx + 1).filter(v => v !== null);
    const periodAvg = slicedData.length ? (slicedData.reduce((a,b)=>a+b,0)/slicedData.length).toFixed(1) : '—';
    const canvasId = `chart-softkpi-${{kpi.id}}`;

    const validData = kpi.data.filter(v => v !== null && v > 0);
    const dataMin   = validData.length ? Math.min(...validData) : 0;
    const dataMax   = validData.length ? Math.max(...validData) : kpi.targetHigh;
    const dataRange = Math.max(dataMax - dataMin, dataMax * 0.15, 0.5);
    const yMin = Math.max(0, Math.floor((dataMin - dataRange * 0.4) * 10) / 10);
    const yMax = Math.ceil((dataMax + dataRange * 0.4) * 10) / 10;

    el.innerHTML += `
      <div style="background:#fff;border:1px solid #e5e1d8;border-radius:12px;overflow:hidden;margin-bottom:14px">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:14px 20px 12px;border-bottom:1px solid #e5e1d8;background:#faf9f5">
          <div style="display:flex;align-items:center;gap:10px">
            <div style="width:3px;height:36px;border-radius:2px;background:${{kpi.color}};flex-shrink:0"></div>
            <div>
              <div style="font-size:13px;font-weight:600;color:var(--text);letter-spacing:.02em">${{kpi.label}}</div>
              <div style="font-size:10px;color:#8f8b80;text-transform:uppercase;letter-spacing:.08em;margin-top:2px">${{kpi.unit}}</div>
            </div>
          </div>
          <div style="display:flex;gap:24px;align-items:center">
            <div style="text-align:right">
              <div style="font-size:1.4rem;font-weight:700;color:${{kpi.color}};line-height:1">${{latest.toFixed(1)}}</div>
              <div style="font-size:10px;color:#8f8b80;text-transform:uppercase;letter-spacing:.08em;margin-top:2px">${{selLabel}}</div>
            </div>
            <div style="text-align:right">
              <div style="font-size:1.1rem;font-weight:600;color:#8f8b80;line-height:1">${{periodAvg}}</div>
              <div style="font-size:10px;color:#8f8b80;text-transform:uppercase;letter-spacing:.08em;margin-top:2px">period avg</div>
            </div>
            ${{deltaHtml}}
          </div>
        </div>
        <div style="padding:16px 20px 14px">
          <div style="position:relative;height:140px"><canvas id="${{canvasId}}"></canvas></div>
          <div style="font-size:10px;color:#8f8b80;text-transform:uppercase;letter-spacing:.08em;margin-top:8px;display:flex;align-items:center;gap:6px">
            <span style="width:14px;height:6px;border-radius:1px;background:${{kpi.color}};opacity:.3;flex-shrink:0;display:inline-block"></span>
            Target band: ${{kpi.targetLow}} – ${{kpi.targetHigh}} ${{kpi.unit.split('/')[0].trim()}}
          </div>
        </div>
      </div>`;

    // Draw chart after DOM update
    requestAnimationFrame(() => {{
      const canvas = document.getElementById(canvasId);
      if(!canvas) return;
      const bandPlugin = {{
        id: 'targetBand_' + kpi.id,
        beforeDraw(chart) {{
          const {{ctx, scales: {{x, y}}}} = chart;
          const yTop = y.getPixelForValue(kpi.targetHigh);
          const yBot = y.getPixelForValue(kpi.targetLow);
          ctx.save();
          ctx.fillStyle = kpi.color + '22';
          ctx.fillRect(x.left, yTop, x.right - x.left, yBot - yTop);
          ctx.strokeStyle = kpi.color + '55';
          ctx.lineWidth = 1;
          ctx.setLineDash([4,4]);
          [yTop, yBot].forEach(yy => {{
            ctx.beginPath(); ctx.moveTo(x.left, yy); ctx.lineTo(x.right, yy); ctx.stroke();
          }});
          ctx.restore();
        }}
      }};
      SOFT_KPI_CHARTS[kpi.id] = new Chart(canvas, {{
        plugins: [bandPlugin],
        type: 'line',
        data: {{
          labels,
          datasets: [{{
            data: kpi.data,
            borderColor: kpi.color,
            backgroundColor: kpi.color + '18',
            borderWidth: 2,
            pointBackgroundColor: kpi.data.map(v => v !== null && v >= kpi.targetLow && v <= kpi.targetHigh ? kpi.color : '#e53935'),
            pointBorderColor: '#fff',
            pointBorderWidth: 1.5,
            pointRadius: 5,
            pointHoverRadius: 7,
            tension: 0.4,
            fill: true,
            spanGaps: true,
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{display:false}},
            datalabels: {{display:false}},
            tooltip: {{
              backgroundColor: '#1b1a17',
              titleColor: '#f7f6f2',
              bodyColor: '#a09d94',
              padding: 12,
              callbacks: {{
                label: ctx => {{
                  const v = ctx.parsed.y;
                  if(v === null) return '  No data';
                  const inBand = v >= kpi.targetLow && v <= kpi.targetHigh;
                  return '  ' + v.toFixed(1) + ' ' + kpi.unit.split('/')[0].trim() + '  ' + (inBand ? '✓ in target' : '✗ off target');
                }}
              }}
            }}
          }},
          scales: {{
            x: {{
              grid: {{color:'#f0ede6'}},
              border: {{color:'#e5e1d8'}},
              ticks: {{color:'#8f8b80', font:{{size:11}}, maxRotation:0}}
            }},
            y: {{
              min: yMin,
              max: yMax,
              grid: {{color:'#f0ede6'}},
              border: {{color:'#e5e1d8'}},
              ticks: {{color:'#8f8b80', font:{{size:10}}, maxTicksLimit:5, callback: v => v.toFixed(0)}}
            }}
          }}
        }}
      }});
    }});
  }});
}}

// Helper: get daily collection amounts for a date prefix, respecting type filter
const DAY_SHORT = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
function getDailyAmounts(prefix, type) {{
  // For online type use ONLINE_COLL_DAILY, otherwise DAILY_COLL
  const srcKeys = type === 'online'
    ? Object.keys(ONLINE_COLL_DAILY).filter(d => d.startsWith(prefix)).sort()
    : Object.keys(DAILY_COLL).filter(d => d.startsWith(prefix)).sort();
  const dayKeys = type === 'online' ? srcKeys : srcKeys;
  const labels = srcKeys.map(d => {{
    const day = parseInt(d.split('-')[2]);
    const dow = DAY_SHORT[new Date(d).getDay()];
    return dow+' '+day;
  }});
  const amounts = srcKeys.map(d => {{
    if(type === 'online') return ONLINE_COLL_DAILY[d] || 0;
    const dc = DAILY_COLL[d] || {{}};
    if(type==='ts') return dc.ts||0;
    if(type==='field') return dc.field||0;
    return (dc.ts||0)+(dc.field||0);
  }});
  return {{ labels, amounts, dayKeys: srcKeys }};
}}

// Compute smart axis max (round up to nice number)
function niceMax(v) {{
  if(v<=0) return 100000;
  const mag = Math.pow(10, Math.floor(Math.log10(v)));
  const step = mag / 10;
  return Math.ceil(v/step)*step;
}}

let revenueChart = null;
function renderRevenueTrend(type, region, month) {{
  if(revenueChart) {{ revenueChart.destroy(); revenueChart = null; }}

  const months = (month && month > 0) ? [month] : _viewMths;
  const labels  = months.map(mn => MONTH_NAMES[mn]);

  // Determine teams from active TL/manager filters
  let teams;
  if(_selTls.length > 0) {{
    const seen = new Set();
    teams = [];
    for(const tl of _selTls) for(const t of (MGR_TEAMS[tl] || [tl])) if(!seen.has(t)) {{ seen.add(t); teams.push(t); }}
  }} else if(_selMgrs.length > 0) {{
    const seen = new Set();
    teams = [];
    for(const mg of _selMgrs) for(const t of (MGR_TEAMS[mg] || [])) if(!seen.has(t)) {{ seen.add(t); teams.push(t); }}
  }} else {{
    teams = Object.keys(REV_TL);
  }}

  const revData   = months.map(mn => getRevenue(teams, mn, type, region) || 0);
  const validRevs = revData.filter(v => v > 0);
  if(!validRevs.length) return;

  const maxR = Math.max(...validRevs);
  const yMin = 0;
  const yMax = niceMax(maxR * 1.15);

  revenueChart = new Chart(document.getElementById('chart-revenue'), {{
    type: 'bar',
    data: {{ labels, datasets: [
      {{
        type: 'bar',
        label: 'Revenue',
        data: revData,
        backgroundColor: '#6366f1cc',
        borderRadius: 6,
        barPercentage: 0.5,
        categoryPercentage: 0.6,
        order: 2,
        datalabels: {{..._DL_BAR, formatter: v => fmt(v)}},
      }},
      {{
        type: 'line',
        label: 'Trend',
        data: revData,
        borderColor: '#000',
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 6,
        pointBackgroundColor: '#ffffff',
        pointBorderColor: '#000',
        pointBorderWidth: 2,
        pointHoverRadius: 8,
        tension: 0.3,
        order: 1,
        datalabels: {{display: false}},
      }}
    ]}},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      clip: false,
      layout: {{padding: {{top: 24}}}},
      plugins: {{
        legend: {{display: false}},
        tooltip: {{callbacks: {{label: ctx => ctx.dataset.label + ': ' + fmt(ctx.parsed.y)}}}},
        datalabels: {{display: true}},
      }},
      scales: {{
        y: {{min: yMin, max: yMax, ticks: {{callback: v => fmtM(v)}}}}
      }}
    }}
  }});
}}

// ── Daily data helpers ────────────────────────────────────────────────────────
function _dailyWeights(month, type) {{
  if(!MONTH_BOUNDS[month]) return null;
  const prefix = MONTH_BOUNDS[month][0].slice(0,7);
  const days = Object.keys(DAILY_COLL).filter(d => d.startsWith(prefix)).sort();
  if(!days.length) return null;
  const totals = days.map(d => {{
    const dc = DAILY_COLL[d] || {{}};
    return type==='ts' ? (dc.ts||0) : type==='field' ? (dc.field||0) : ((dc.ts||0)+(dc.field||0));
  }});
  const grand = totals.reduce((s,v) => s+v, 0);
  if(!grand) return null;
  return {{ days, labels: days.map(d => d.slice(8)), totals, grand, w: totals.map(v => v/grand) }};
}}
function _entityPool(e, type, region, month, isTl) {{
  return isTl ? _tlPool(e, type, region, month) : _mgrPool(e, type, region, month);
}}
function _entityName(e, isTl) {{
  return isTl ? (TL_NAMES[e] || MGR_NAMES[e] || e) : (MGR_NAMES[e] || e);
}}

// ── Daily Cash Trend — single entity ─────────────────────────────────────────
function renderTrendDailySingle(month, type, region, entity, isTl) {{
  const dw = _dailyWeights(month, type);
  if(!dw) {{ renderTrendMonthly(type, region); return; }}
  const {{ labels, totals }} = dw;
  const pool = _entityPool(entity, type, region, month, isTl);
  const entityMonthly = pool.reduce((s,r) => s+r.coll, 0);
  const allMonthly = DATA.filter(r => r.month===month && r.mgr!=='').reduce((s,r) => s+r.coll, 0);
  const share = allMonthly > 0 ? entityMonthly/allMonthly : 1;
  const data = totals.map(v => Math.round(v*share));
  let cum = 0;
  const cumData = data.map(v => {{ cum+=v; return cum; }});
  const maxBar  = niceMax(Math.max(...data, 1));
  const maxLine = niceMax(Math.max(...cumData, 1));
  const name = _entityName(entity, isTl);
  document.getElementById('ov-trend-title').textContent = 'Daily Collections (est.) \u2014 '+MONTH_NAMES[month]+' \u2014 '+name;
  if(trendChart) trendChart.destroy();
  trendChart = new Chart(document.getElementById('chart-trend'), {{
    type:'bar',
    data:{{ labels, datasets:[
      {{ type:'bar',  label:'Daily',      data,    backgroundColor:'#2a9d8faa', borderRadius:4, yAxisID:'y',  order:2, datalabels:{{display:false}} }},
      {{ type:'line', label:'Cumulative', data:cumData, borderColor:'#000', backgroundColor:'transparent', borderWidth:2, pointRadius:2, tension:0.3, yAxisID:'y2', order:1, datalabels:{{display:false}} }}
    ]}},
    options:{{
      responsive:true, interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label==='Cumulative'?'Cumulative: '+fmt(ctx.parsed.y):'Daily: '+fmt(ctx.parsed.y)}}}}, datalabels:{{display:false}}}},
      scales:{{
        x:{{ticks:{{font:{{size:9}},maxRotation:45,minRotation:45}}}},
        y:{{beginAtZero:true,max:maxBar,ticks:{{callback:v=>fmt(v)}},title:{{display:true,text:'Daily (est.)',font:{{size:10}}}}}},
        y2:{{position:'right',beginAtZero:true,max:maxLine,ticks:{{callback:v=>fmt(v)}},grid:{{display:false}},title:{{display:true,text:'Cumulative',font:{{size:10}}}}}}
      }}
    }}
  }});
}}

// ── Daily Active/Net Gain ─────────────────────────────────────────────────────
function renderActiveGainDailyView(month, type, region, entities, isTl) {{
  const dw = _dailyWeights(month, type);
  if(!dw) {{ renderActiveGainChart(type, region, month); return; }}
  const {{ labels, w }} = dw;
  const mgrColors = [_MGR_A_COLOR, _MGR_B_COLOR];
  const _entsAG = entities.length > 0 ? entities : [null];
  const _poolAllAG = entities.length===0 ? applyFilters(DATA.filter(r => r.month===month && r.mgr!==''), type, region) : null;
  const datasets = _entsAG.map((e, idx) => {{
    const pool = e===null ? _poolAllAG : _entityPool(e, type, region, month, isTl);
    const totalGain = pool.reduce((s,r) => s+r.net_gain, 0);
    const data = w.map(wi => +(totalGain*wi).toFixed(1));
    const col = _entsAG.length > 1 ? mgrColors[idx] : null;
    return {{ type:'bar', label: e===null ? 'Net Gain' : _entityName(e,isTl),
      data,
      backgroundColor: col ? col+'88' : data.map(v => v>=0 ? 'rgba(67,160,71,0.7)' : 'rgba(229,57,53,0.7)'),
      borderColor:     col ? col       : data.map(v => v>=0 ? '#43a047' : '#e53935'),
      borderWidth:1, borderRadius:3, borderSkipped:false, datalabels:{{display:false}} }};
  }});
  const allVals = datasets.flatMap(d => d.data);
  const maxAbs = Math.max(Math.abs(Math.min(...allVals)), Math.abs(Math.max(...allVals)), 1);
  const range = Math.ceil(maxAbs*1.5);
  if(activeGainChart) {{ activeGainChart.destroy(); activeGainChart = null; }}
  activeGainChart = new Chart(document.getElementById('chart-active-gain'), {{
    data:{{ labels, datasets }},
    options:{{
      responsive:true, maintainAspectRatio:false,
      plugins:{{
        legend: _entsAG.length > 1 ? {{position:'bottom',labels:{{font:{{size:11}},usePointStyle:true}}}} : {{display:false}},
        datalabels:{{display:false}},
        tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+(ctx.parsed.y>0?'+':'')+ctx.parsed.y.toFixed(0)}}}}
      }},
      scales:{{
        x:{{ticks:{{font:{{size:9}},maxRotation:45,minRotation:45}}}},
        y:{{min:-range,max:range,ticks:{{callback:v=>(v>0?'+':'')+Math.round(v)}},title:{{display:true,text:'Est. Net Gain (clients)',font:{{size:10}}}}}}
      }}
    }}
  }});
}}

// ── Daily Renewals ────────────────────────────────────────────────────────────
function renderRenewalsDailyView(month, type, region, entities, isTl) {{
  const dw = _dailyWeights(month, type);
  if(!dw) {{ renderRevenueTrend(type, region, month); return; }}
  const {{ labels, w }} = dw;
  const mgrColors = [_MGR_A_COLOR, _MGR_B_COLOR];
  const _entsRD = entities.length > 0 ? entities : [null];
  const _poolAllRD = entities.length===0 ? applyFilters(DATA.filter(r => r.month===month && r.mgr!==''), type, region) : null;
  const datasets = _entsRD.map((e, idx) => {{
    const pool = e===null ? _poolAllRD : _entityPool(e, type, region, month, isTl);
    const total = pool.reduce((s,r) => s+r.renewed, 0);
    const data = w.map(wi => +(total*wi).toFixed(1));
    const col = _entsRD.length > 1 ? mgrColors[idx] : 'rgba(42,157,111,0.75)';
    return {{ type:'bar', label: e===null ? 'Renewed' : _entityName(e,isTl)+' Renewed',
      data, backgroundColor:col, borderColor: _entsRD.length > 1 ? mgrColors[idx] : '#2a9d6f',
      borderWidth:1, borderRadius:3, datalabels:{{display:false}} }};
  }});
  const allVals = datasets.flatMap(d => d.data);
  const yMax = niceMax(Math.max(...allVals, 1)*1.3);
  if(renewalsChart) {{ renewalsChart.destroy(); renewalsChart = null; }}
  renewalsChart = new Chart(document.getElementById('chart-renewals'), {{
    data:{{ labels, datasets }},
    options:{{
      responsive:true, maintainAspectRatio:false,
      plugins:{{
        legend: _entsRD.length > 1 ? {{position:'bottom',labels:{{font:{{size:11}},usePointStyle:true}}}} : {{display:false}},
        datalabels:{{display:false}},
        tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+ctx.parsed.y.toFixed(1)}}}}
      }},
      scales:{{
        x:{{ticks:{{font:{{size:9}},maxRotation:45,minRotation:45}}}},
        y:{{beginAtZero:true,max:yMax,ticks:{{callback:v=>v.toFixed(1)}},title:{{display:true,text:'Est. Daily Renewed',font:{{size:10}}}}}}
      }}
    }}
  }});
}}

// ── Daily Employee Productivity ───────────────────────────────────────────────
function renderEmpProdDailyView(month, type, region, entities, isTl) {{
  const dw = _dailyWeights(month, type);
  if(!dw) {{ renderEmpProdChart(type, region, month); return; }}
  const {{ labels, w }} = dw;
  const mgrColors = [_MGR_A_COLOR, _MGR_B_COLOR];
  const _entsEP = entities.length > 0 ? entities : [null];
  const _poolAllEP = entities.length===0 ? applyFilters(DATA.filter(r => r.month===month && r.mgr!==''), type, region) : null;
  const datasets = _entsEP.map((e, idx) => {{
    const pool = e===null ? _poolAllEP : _entityPool(e, type, region, month, isTl);
    const bom = Math.max(1, pool.filter(r => !r.is_leader && r.target > 0).length);
    const totalColl = pool.reduce((s,r) => s+r.coll, 0);
    const data = w.map(wi => Math.round(totalColl*wi/bom));
    const col = _entsEP.length > 1 ? mgrColors[idx] : '#0d9488';
    return {{ type:'line', label: e===null ? 'Cash/Emp' : _entityName(e,isTl)+' Cash/Emp',
      data, borderColor:col, backgroundColor:col+'18',
      borderWidth:2.5, pointBackgroundColor:'#fff', pointBorderColor:col,
      pointBorderWidth:2, pointRadius:3, pointHoverRadius:5, tension:0.35, fill:true,
      spanGaps:true, datalabels:{{display:false}} }};
  }});
  const allVals = datasets.flatMap(d => d.data).filter(v => v!==null);
  const vMin = allVals.length ? Math.min(...allVals) : 0;
  const vMax = allVals.length ? Math.max(...allVals) : 10000;
  const pad = (vMax-vMin)*0.3 || vMax*0.2;
  const yMin = Math.max(0, Math.floor((vMin-pad)/500)*500);
  const yMax2 = Math.ceil((vMax+pad)/500)*500;
  if(empProdChart) {{ empProdChart.destroy(); empProdChart = null; }}
  empProdChart = new Chart(document.getElementById('chart-emp-prod'), {{
    type:'line', data:{{ labels, datasets }},
    options:{{
      responsive:true, maintainAspectRatio:false,
      plugins:{{
        legend: _entsEP.length > 1 ? {{position:'bottom',labels:{{font:{{size:11}},usePointStyle:true}}}} : {{display:false}},
        datalabels:{{display:false}},
        tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+fmt(ctx.parsed.y)}}}}
      }},
      scales:{{
        x:{{ticks:{{font:{{size:9}},maxRotation:45,minRotation:45}}}},
        y:{{min:yMin,max:yMax2,ticks:{{callback:v=>fmt(v)}},title:{{display:true,text:'Cash / Emp (est.)',font:{{size:10}}}}}}
      }}
    }}
  }});
}}

// ── Daily Soft KPI Trends ─────────────────────────────────────────────────────
function renderSoftKpiDailyView(month, type, region, entities, isTl) {{
  type = _softKpiType;
  const dw = _dailyWeights(month, type);
  if(!dw) {{ renderSoftKpiTrends(type, region, month); return; }}
  const {{ labels, w }} = dw;
  const isTS = type === 'ts';
  const _entsSK = entities.length > 0 ? entities : [null];
  const _poolAllSK = entities.length===0 ? applyFilters(DATA.filter(r => r.month===month && r.mgr!==''), type, region) : null;
  const mgrColors = [_MGR_A_COLOR, _MGR_B_COLOR];
  const el = document.getElementById('ov-soft-kpi-trends');
  for(const k of Object.keys(SOFT_KPI_CHARTS)) {{ if(SOFT_KPI_CHARTS[k]) {{ SOFT_KPI_CHARTS[k].destroy(); SOFT_KPI_CHARTS[k]=null; }} }}
  const kpiDefs = [
    {{ id:'dtt', label:'Daily Talk Time',        unit:'avg mins / day',  color:'#f0a050', field:'dtt', targetLow:30, targetHigh:45 }},
    {{ id:'uqc', label:'Unique Qualified Calls', unit:'avg calls / day', color:'#4f5fcc', field:'uqc', targetLow:4,  targetHigh:8  }},
    ...( isTS ? [] : [{{ id:'vm', label:'Verified Meetings', unit:'avg meetings / day', color:'#00897b', field:'vm', targetLow:1, targetHigh:4 }}] )
  ];
  const legendHtml = _entsSK.length > 1 && _entsSK[0]!==null
    ? _entsSK.map((e,i) => `<span style="display:inline-flex;align-items:center;gap:4px;margin-right:10px;font-size:10px"><span style="width:12px;height:2px;background:${{mgrColors[i]}};display:inline-block;border-radius:1px"></span>${{_entityName(e,isTl)}}</span>`).join('')
    : '';
  el.innerHTML = `<div class="chart-title" style="margin-bottom:12px;font-size:13px;font-weight:600;color:var(--text)">Soft KPI Daily Est. \u2014 ${{MONTH_NAMES[month]}}${{legendHtml ? ' &nbsp; '+legendHtml : ''}}</div>`;
  kpiDefs.forEach(kpi => {{
    const canvasId = `chart-softkpi-${{kpi.id}}`;
    const datasets = _entsSK.map((e, idx) => {{
      const pool = e===null ? _poolAllSK : _entityPool(e, type, region, month, isTl);
      const activePool = pool.filter(r => r[kpi.field] > 0 && r.days > 0);
      const activeCons = Math.max(1, activePool.length);
      const totalKpi = activePool.reduce((s,r) => s+r[kpi.field], 0);
      const data = w.map(wi => +(totalKpi/activeCons*wi).toFixed(2));
      const col = _entsSK.length > 1 ? mgrColors[idx] : kpi.color;
      return {{ label: e===null ? kpi.label : _entityName(e,isTl), data, borderColor:col, backgroundColor:col+'18',
        borderWidth:2, pointBackgroundColor:'#fff', pointBorderColor:col,
        pointBorderWidth:1.5, pointRadius:3, pointHoverRadius:5, tension:0.4, fill:true,
        spanGaps:true, datalabels:{{display:false}} }};
    }});
    const allVals = datasets.flatMap(d => d.data).filter(v => v > 0);
    const kMin = allVals.length ? Math.min(...allVals) : 0;
    const kMax = allVals.length ? Math.max(...allVals) : kpi.targetHigh;
    const kr = kMax-kMin || 1;
    const yMin = Math.max(0, Math.floor((kMin-kr*0.4)*10)/10);
    const yMax = Math.ceil((Math.max(kMax,kpi.targetHigh)+kr*0.3)*10)/10;
    el.innerHTML += `<div style="background:#fff;border:1px solid #e5e1d8;border-radius:12px;overflow:hidden;margin-bottom:14px">
      <div style="padding:12px 20px 10px;border-bottom:1px solid #e5e1d8;background:#faf9f5;display:flex;align-items:center;gap:10px">
        <div style="width:3px;height:28px;border-radius:2px;background:${{kpi.color}};flex-shrink:0"></div>
        <div style="font-size:13px;font-weight:600;color:var(--text)">${{kpi.label}}</div>
        <div style="font-size:10px;color:#8f8b80;margin-left:4px">${{kpi.unit}}</div>
      </div>
      <div style="padding:16px 20px 14px"><div style="position:relative;height:140px"><canvas id="${{canvasId}}"></canvas></div></div>
    </div>`;
    requestAnimationFrame(() => {{
      const canvas = document.getElementById(canvasId); if(!canvas) return;
      const gc='#f0ede6', bc='#e5e1d8', tc='#8f8b80';
      const bandPlugin = {{ id:'tb_'+kpi.id, beforeDraw(chart){{ const {{ctx,scales:{{x,y}}}}=chart; const yT=y.getPixelForValue(kpi.targetHigh); const yB=y.getPixelForValue(kpi.targetLow); ctx.save(); ctx.fillStyle=kpi.color+'22'; ctx.fillRect(x.left,yT,x.right-x.left,yB-yT); ctx.restore(); }} }};
      SOFT_KPI_CHARTS[kpi.id] = new Chart(canvas, {{
        plugins:[bandPlugin], type:'line', data:{{ labels, datasets }},
        options:{{ responsive:true, maintainAspectRatio:false,
          plugins:{{ legend:{{display:false}}, datalabels:{{display:false}},
            tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+ctx.parsed.y.toFixed(1)+' '+kpi.unit.split('/')[0].trim()}} }} }},
          scales:{{
            x:{{grid:{{color:gc}},border:{{color:bc}},ticks:{{color:tc,font:{{size:9}},maxRotation:45,minRotation:45}}}},
            y:{{min:yMin,max:yMax,grid:{{color:gc}},border:{{color:bc}},ticks:{{color:tc,font:{{size:10}},maxTicksLimit:5,callback:v=>v.toFixed(1)}}}}
          }}
        }}
      }});
    }});
  }});
}}

// Daily trend for 2 entities (managers/TLs) — proportional scaling from DAILY_COLL
function renderTrendDailyComparison(month, type, region, entities, isTl) {{
  if(!MONTH_BOUNDS[month]) {{ renderTrendDaily(month, type); return; }}
  const prefix = MONTH_BOUNDS[month][0].slice(0,7);
  const days   = Object.keys(DAILY_COLL).filter(d => d.startsWith(prefix)).sort();
  if(!days.length) {{ renderTrendDaily(month, type); return; }}
  const labels = days.map(d => d.slice(8));
  const colors = [_MGR_A_COLOR, _MGR_B_COLOR];
  const totals = entities.map(e => {{
    const pool = isTl ? _tlPool(e,type,region,month) : _mgrPool(e,type,region,month);
    return pool.reduce((s,r) => s+r.coll, 0);
  }});
  const grandTotal = totals.reduce((s,v) => s+v, 0);
  const datasets = entities.map((e, idx) => {{
    const share = grandTotal > 0 ? totals[idx]/grandTotal : 0.5;
    const data  = days.map(d => {{
      const dc  = DAILY_COLL[d]||{{}};
      const raw = type==='ts' ? (dc.ts||0) : type==='field' ? (dc.field||0) : ((dc.ts||0)+(dc.field||0));
      return Math.round(raw*share);
    }});
    const name = isTl ? (TL_NAMES[e]||MGR_NAMES[e]||e) : (MGR_NAMES[e]||e);
    return {{type:'line',label:name,data,borderColor:colors[idx],backgroundColor:colors[idx]+'18',
      borderWidth:2.5,pointRadius:2,pointHoverRadius:4,tension:0.35,fill:true,datalabels:{{display:false}}}};
  }});
  const allVals = datasets.flatMap(d => d.data);
  const yMax = niceMax(Math.max(...allVals,1)*1.2);
  document.getElementById('ov-trend-title').textContent = 'Daily Collections (est.) \u2014 '+MONTH_NAMES[month]+' \u2014 '+(isTl?'TL':'Manager')+' Comparison';
  if(trendChart) trendChart.destroy();
  trendChart = new Chart(document.getElementById('chart-trend'), {{
    type:'line', data:{{labels,datasets}},
    options:{{responsive:true, interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}},usePointStyle:true}}}},
        tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+fmt(ctx.parsed.y)}}}},datalabels:{{display:false}}}},
      scales:{{x:{{ticks:{{font:{{size:9}},maxRotation:45,minRotation:45}}}},
        y:{{beginAtZero:true,max:yMax,ticks:{{callback:v=>fmt(v)}},
          title:{{display:true,text:'Daily (est.)',font:{{size:10}}}}}}}}}}
  }});
}}

function renderTrendMonthly(type, region) {{
  if(_selTls.length === 1) {{
    document.getElementById('ov-trend-title').textContent = 'Cash Collection — '+(TL_NAMES[_selTls[0]]||MGR_NAMES[_selTls[0]]||_selTls[0]);
    const labels = _viewMths.map(mn => MONTH_NAMES[mn]);
    const _md1 = _getMtdDays();
    const data   = _viewMths.map(mn => _mtdColl(_tlPool(_selTls[0], type, region, mn), _md1, mn));
    if(trendChart) trendChart.destroy();
    trendChart = new Chart(document.getElementById('chart-trend'), {{
      type:'bar',
      data:{{labels, datasets:[
        {{type:'bar', label:'Cash Collection', data, backgroundColor:'#2a9d8fcc', borderRadius:6, barPercentage:0.5, categoryPercentage:0.6, order:2, datalabels:{{..._DL_BAR, formatter:v=>fmt(v)}}}},
        {{type:'line', label:'Trend', data, borderColor:'#000', backgroundColor:'transparent', borderWidth:2, pointRadius:5, pointBackgroundColor:'#fff', pointBorderColor:'#000', pointBorderWidth:2, tension:0.3, order:1, datalabels:{{display:false}}}}
      ]}},
      options:{{responsive:true, clip:false, layout:{{padding:{{top:24}}}}, plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>fmt(ctx.parsed.y)}}}}, datalabels:{{display:true}}}}, scales:{{y:{{beginAtZero:true, max:niceMax(Math.max(...data,1)*1.15), ticks:{{callback:v=>fmtM(v)}}}}}}}}
    }});
    return;
  }}
  if(_selTls.length === 2) {{
    document.getElementById('ov-trend-title').textContent = 'Cash Collection — TL Comparison';
    const labels    = _viewMths.map(mn => MONTH_NAMES[mn]);
    const mgrColors = [_MGR_A_COLOR, _MGR_B_COLOR];
    const _md2 = _getMtdDays();
    const datasets  = _selTls.map((tl, idx) => ({{
      type:'line', label: TL_NAMES[tl]||MGR_NAMES[tl]||tl,
      data: _viewMths.map(mn => _mtdColl(_tlPool(tl, type, region, mn), _md2, mn)),
      borderColor:mgrColors[idx], backgroundColor:'transparent',
      borderWidth:2.5, pointBackgroundColor:'#fff', pointBorderColor:mgrColors[idx],
      pointBorderWidth:2, pointRadius:5, pointHoverRadius:7, tension:0.3, order:idx+1, datalabels:{{..._DL_LINE, formatter:v=>fmt(v)}},
    }}));
    const _tl2v = datasets.flatMap(d=>d.data).filter(v=>v>0);
    const _tl2mn = _tl2v.length ? Math.floor(Math.min(..._tl2v)*0.8/1000)*1000 : 0;
    const _tl2mx = _tl2v.length ? niceMax(Math.max(..._tl2v)*1.2) : undefined;
    if(trendChart) trendChart.destroy();
    trendChart = new Chart(document.getElementById('chart-trend'), {{
      type:'line', data:{{labels, datasets}},
      options:{{responsive:true, plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}},usePointStyle:true}}}}, tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+fmt(ctx.parsed.y)}}}}, datalabels:{{display:false}}}}, scales:{{y:{{min:_tl2mn, max:_tl2mx, ticks:{{callback:v=>fmt(v)}}}}}}}}
    }});
    return;
  }}
  if(_selMgrs.length === 1) {{
    document.getElementById('ov-trend-title').textContent = 'Cash Collection — '+(MGR_NAMES[_selMgrs[0]]||_selMgrs[0]);
    const labels = _viewMths.map(mn => MONTH_NAMES[mn]);
    const _md3 = _getMtdDays();
    const data   = _viewMths.map(mn => _mtdColl(_mgrPool(_selMgrs[0], type, region, mn), _md3, mn));
    if(trendChart) trendChart.destroy();
    trendChart = new Chart(document.getElementById('chart-trend'), {{
      type:'bar',
      data:{{labels, datasets:[
        {{type:'bar', label:'Cash Collection', data, backgroundColor:'#2a9d8fcc', borderRadius:6, barPercentage:0.5, categoryPercentage:0.6, order:2, datalabels:{{..._DL_BAR, formatter:v=>fmt(v)}}}},
        {{type:'line', label:'Trend', data, borderColor:'#000', backgroundColor:'transparent', borderWidth:2, pointRadius:5, pointBackgroundColor:'#fff', pointBorderColor:'#000', pointBorderWidth:2, tension:0.3, order:1, datalabels:{{display:false}}}}
      ]}},
      options:{{responsive:true, clip:false, layout:{{padding:{{top:24}}}}, plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>fmt(ctx.parsed.y)}}}}, datalabels:{{display:true}}}}, scales:{{y:{{beginAtZero:true, max:niceMax(Math.max(...data,1)*1.15), ticks:{{callback:v=>fmtM(v)}}}}}}}}
    }});
    return;
  }}
  if(_selMgrs.length === 2) {{
    document.getElementById('ov-trend-title').textContent = 'Cash Collection — Monthly Comparison';
    const labels   = _viewMths.map(mn => MONTH_NAMES[mn]);
    const mgrColors = [_MGR_A_COLOR, _MGR_B_COLOR];
    const _md4 = _getMtdDays();
    const datasets  = _selMgrs.map((mg, idx) => ({{
      type:'line', label: MGR_NAMES[mg]||mg,
      data: _viewMths.map(mn => _mtdColl(_mgrPool(mg, type, region, mn), _md4, mn)),
      borderColor:mgrColors[idx], backgroundColor:'transparent',
      borderWidth:2.5, pointBackgroundColor:'#fff', pointBorderColor:mgrColors[idx],
      pointBorderWidth:2, pointRadius:5, pointHoverRadius:7, tension:0.3, order:idx+1, datalabels:{{..._DL_LINE, formatter:v=>fmt(v)}},
    }}));
    const _mg2v = datasets.flatMap(d=>d.data).filter(v=>v>0);
    const _mg2mn = _mg2v.length ? Math.floor(Math.min(..._mg2v)*0.8/1000)*1000 : 0;
    const _mg2mx = _mg2v.length ? niceMax(Math.max(..._mg2v)*1.2) : undefined;
    if(trendChart) trendChart.destroy();
    trendChart = new Chart(document.getElementById('chart-trend'), {{
      type:'line', data:{{labels, datasets}},
      options:{{responsive:true, plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}},usePointStyle:true}}}}, tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+fmt(ctx.parsed.y)}}}}, datalabels:{{display:false}}}}, scales:{{y:{{min:_mg2mn, max:_mg2mx, ticks:{{callback:v=>fmt(v)}}}}}}}}
    }});
    return;
  }}
  const _md5 = _getMtdDays();
  const _mtdSuffix = _mtdModeColl ? ` \u2014 MTD (${{_md5}}d left)` : '';
  document.getElementById('ov-trend-title').textContent = 'Cash Collection \u2014 Monthly' + _mtdSuffix;
  const labels = _viewMths.map(mn => MONTH_NAMES[mn]);
  const _latestMn = Math.max(..._viewMths);
  const totals = _viewMths.map(mn => {{
    const hasFilter = (region && region !== 'all') || _selTls.length > 0 || _selMgrs.length > 0;
    if(_mtdModeColl && !hasFilter && mn !== _latestMn) {{
      return _collUpToDay(mn, _md5, type);
    }}
    if(_mtdModeColl && hasFilter) {{
      return _mtdColl(applyFilters(DATA.filter(r => r.month===mn && r.mgr!==''), type, region), _md5, mn);
    }}
    if(!hasFilter) {{
      const calMo = String(mn).padStart(2,'0');
      const prefix = '2026-'+calMo+'-';
      if(type === 'online') {{
        return Object.keys(ONLINE_COLL_DAILY).filter(d => d.startsWith(prefix))
          .reduce((s,d) => s+(ONLINE_COLL_DAILY[d]||0), 0);
      }}
      const dayKeys = Object.keys(DAILY_COLL).filter(d => d.startsWith(prefix));
      const fieldTs = dayKeys.reduce((s,d) => {{
        const dc = DAILY_COLL[d]||{{}};
        if(type==='ts') return s+(dc.ts||0);
        if(type==='field') return s+(dc.field||0);
        return s+(dc.ts||0)+(dc.field||0);
      }}, 0);
      // Add online channel to 'all' total
      const onlineTotal = type === 'all'
        ? Object.keys(ONLINE_COLL_DAILY).filter(d => d.startsWith(prefix))
            .reduce((s,d) => s+(ONLINE_COLL_DAILY[d]||0), 0)
        : 0;
      return fieldTs + onlineTotal;
    }}
    return applyFilters(DATA.filter(r => r.month===mn && r.mgr!==''), type, region)
             .reduce((s,r) => s+r.coll, 0);
  }});
  if(trendChart) trendChart.destroy();
  trendChart = new Chart(document.getElementById('chart-trend'), {{
    type:'bar',
    data:{{ labels, datasets:[
      {{
        type:'bar', label:'Cash Collection', data:totals,
        backgroundColor:'#2a9d8fcc', borderRadius:6, barPercentage:0.5, categoryPercentage:0.6, order:2,
        datalabels:{{..._DL_BAR, formatter:v=>fmt(v)}},
      }},
      {{
        type:'line', label:'Trend', data:totals,
        borderColor:'#000', backgroundColor:'transparent', borderWidth:2,
        pointRadius:6, pointBackgroundColor:'#ffffff', pointBorderColor:'#000',
        pointBorderWidth:2, pointHoverRadius:8, tension:0.3, order:1, datalabels:{{display:false}},
      }}
    ]}},
    options:{{
      responsive:true, clip:false, layout:{{padding:{{top:24}}}},
      plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>fmt(ctx.parsed.y)}}}}, datalabels:{{display:true}}}},
      scales:{{y:{{beginAtZero:true, max:niceMax(Math.max(...totals,1)*1.15), ticks:{{callback:v=>fmtM(v)}}}}}}
    }}
  }});
}}


function renderTrendDaily(month, type) {{
  // DAILY_COLL has no per-manager/per-TL dimension — fall back to monthly view.
  if(_selMgrs.length > 0 || _selTls.length > 0) {{
    const region = document.getElementById('f-region').value;
    renderTrendMonthly(type, region);
    return;
  }}
  const calMo = String(month).padStart(2,'0');
  const prefix = '2026-'+calMo+'-';
  const {{labels, amounts}} = getDailyAmounts(prefix, type);

  let cum = 0;
  const cumAmounts = amounts.map(v => {{ cum+=v; return cum; }});

  const maxBar = niceMax(Math.max(...amounts, 0));
  const maxLine = niceMax(Math.max(...cumAmounts, 0));

  document.getElementById('ov-trend-title').textContent = 'Daily Collections — '+MONTH_NAMES[month];
  if(trendChart) trendChart.destroy();
  trendChart = new Chart(document.getElementById('chart-trend'), {{
    type:'bar',
    data:{{ labels, datasets:[
      {{
        type:'bar',
        label:'Daily Collection',
        data:amounts,
        backgroundColor:'#2a9d8faa',
        borderRadius:4,
        yAxisID:'y',
        order:2,
      }},
      {{
        type:'line',
        label:'Cumulative',
        data:cumAmounts,
        borderColor:'#000',
        backgroundColor:'transparent',
        borderWidth:2,
        pointRadius:2,
        tension:0.3,
        yAxisID:'y2',
        order:1,
      }}
    ]}},
    options:{{
      responsive:true,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{position:'bottom',labels:{{font:{{size:10}}}}}},
        tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+fmt(ctx.parsed.y)}}}},
        datalabels:{{display:false}},
      }},
      scales:{{
        x:{{ticks:{{font:{{size:9}},maxRotation:45,minRotation:45}}}},
        y:{{type:'linear',position:'left',beginAtZero:true,max:maxBar,
           ticks:{{callback:v=>fmt(v)}},title:{{display:true,text:'Daily',font:{{size:10}}}}}},
        y2:{{type:'linear',position:'right',beginAtZero:true,max:maxLine,
            ticks:{{callback:v=>fmt(v)}},title:{{display:true,text:'Cumulative',font:{{size:10}}}},
            grid:{{drawOnChartArea:false}}}}
      }}
    }}
  }});
}}

function applyFilters(rows, type, region) {{
  if(type==='field') rows = rows.filter(r => !r.is_ts);
  if(type==='ts')    rows = rows.filter(r => r.is_ts);
  if(region!=='all') rows = rows.filter(r => r.region === region);
  return rows;
}}

function _ovSetBreadcrumb() {{
  const bc = document.getElementById('ov-breadcrumb');
  const mfg = document.getElementById('f-month').closest('.filter-group');
  if(_ovDrillMonth === 0) {{
    bc.style.display = 'none';
    mfg.style.display = '';
    return;
  }}
  bc.style.display = 'flex';
  mfg.style.display = 'none';
  document.getElementById('ov-bc-month').textContent = MONTH_NAMES[_ovDrillMonth];
  document.getElementById('ov-bc-month').className = 'ov-bc-item' + (_ovDrillMgr ? '' : ' active');
  const hasMgr = _ovDrillMgr !== '';
  document.getElementById('ov-bc-sep2').style.display = hasMgr ? '' : 'none';
  document.getElementById('ov-bc-mgr').style.display  = hasMgr ? '' : 'none';
  if(hasMgr) document.getElementById('ov-bc-mgr').textContent = MGR_NAMES[_ovDrillMgr] || _ovDrillMgr;
}}

function renderOvConsultantCards(type, region) {{
  document.getElementById('ov-report-cards').style.display = '';
  document.getElementById('ov-single-top').style.display = 'none';
  document.getElementById('ov-single-month').style.display = 'none';
  document.getElementById('ov-soft-kpi-section').style.display = '';
  document.getElementById('ov-kpi-tiles').innerHTML = '';
  if(collChart) collChart.destroy();
  if(tvaChart) tvaChart.destroy();
  renderSoftKpiTrends(type, region, _ovDrillMonth);
  const mn     = _ovDrillMonth;
  const tl     = _ovDrillTl;
  const tlName = TL_NAMES[tl] || MGR_NAMES[tl] || tl;
  const pool   = applyFilters(DATA.filter(r => r.month === mn && r.team === tl), type, region);
  let cards = '';
  const tlSelf = pool.find(r => LEADERS.has(r.name));
  if(tlSelf && (tlSelf.coll > 0 || tlSelf.pkg > 0)) {{
    const cm = calcMetrics([tlSelf]);
    cards += reportCard(tlSelf.name+' (Team Lead)', tlName+' &mdash; '+MONTH_NAMES[mn], cm, tlSelf.is_ts, null, 'rc-tl-card', true, false, '', null, false, true);
  }}
  const consultants = pool.filter(r => !LEADERS.has(r.name));
  for(const r of consultants) {{
    const cm = calcMetrics([r]);
    cards += reportCard(r.name, tlName+' &mdash; '+MONTH_NAMES[mn], cm, r.is_ts, null, 'rc-consultant-card', true, false, '', null, false, true);
  }}
  if(!cards) cards = '<p style="color:var(--muted);padding:20px;font-size:13px">No data for this selection.</p>';
  const conGrid = 'display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:16px;margin-bottom:26px';
  document.getElementById('ov-report-cards').innerHTML = '<div style="'+conGrid+'">'+cards+'</div>';
  _equalizeCardHeights();
}}

function renderOvMgrCards(type, region) {{
  document.getElementById('ov-report-cards').style.display = '';
  document.getElementById('ov-single-top').style.display = 'none';
  document.getElementById('ov-single-month').style.display = 'none';
  document.getElementById('ov-soft-kpi-section').style.display = '';
  if(collChart) collChart.destroy();
  if(tvaChart) tvaChart.destroy();
  renderSoftKpiTrends(type, region, _ovDrillMonth);
  const mn = _ovDrillMonth;
  let cards = '';
  for(const mg of Object.keys(MGR_TEAMS)) {{
    // AlHourani is a standalone manager only from April (month=4) onwards;
    // for earlier months he reports through Mohamed Abdullah's card
    if(mg === 'AlHourani - TL Riyadh' && mn < 4) continue;
    if(mg === 'Mohamed Abdullah - M3' && mn >= 4) continue;
    let p = applyFilters(DATA.filter(r => r.month === mn && (MGR_POOL_BY_TEAM.has(mg) ? r.team === mg : r.mgr === mg)), type, region);
    if(p.length === 0) continue;
    const m = calcMetrics(p);
    const mgrName = MGR_NAMES[mg] || mg;
    const mgrRev  = getRevenue(MGR_TEAMS[mg] || [], mn, type, region);
    const _defHint = (MGR_TEAMS[mg]||[]).length===1&&MGR_TEAMS[mg][0]===mg ? 'Click to view consultants' : 'Click to view TL breakdown';
    cards += `<div class="ov-drill-wrap" onclick="drillOvMgr('${{mg}}')">
      ${{reportCard(mgrName, mg+' &mdash; '+MONTH_NAMES[mn]+' &mdash; '+p.length+' consultants', m, p.some(r=>r.is_ts), null, 'rc-mgr-card', false, true, '', mgrRev)}}
      <div class="ov-drill-hint">${{_defHint}} &#8250;</div>
    </div>`;
  }}
  if(!cards) cards = '<p style="color:var(--muted);padding:20px;font-size:13px">No data for this selection.</p>';
  document.getElementById('ov-report-cards').innerHTML = '<div class="rc-grid-wide">'+cards+'</div>';
  _equalizeCardHeights();
}}

function renderOvTlCards(type, region) {{
  document.getElementById('ov-report-cards').style.display = '';
  document.getElementById('ov-single-top').style.display = 'none';
  document.getElementById('ov-single-month').style.display = 'none';
  document.getElementById('ov-soft-kpi-section').style.display = '';
  if(collChart) collChart.destroy();
  if(tvaChart) tvaChart.destroy();
  renderSoftKpiTrends(type, region, _ovDrillMonth);
  const mn  = _ovDrillMonth;
  const mg  = _ovDrillMgr;
  const tls = MGR_TEAMS[mg] || [];
  let cards = '';
  for(const tl of tls) {{
    let p = applyFilters(DATA.filter(r => r.month === mn && r.team === tl), type, region);
    if(p.length === 0) continue;
    const m = calcMetrics(p);
    const tlName = TL_NAMES[tl] || tl;
    const isDirect = tl === mg;
    const tlRev   = getRevenue([tl], mn, type, region);
    cards += `<div class="ov-drill-wrap" onclick="drillOvTl('${{tl}}')">
      ${{reportCard(tlName + (isDirect ? ' (Direct)' : ''), tl+' &mdash; '+MONTH_NAMES[mn]+' &mdash; '+p.length+' members', m, p.some(r=>r.is_ts), null, 'rc-tl-card', false, false, '', tlRev, true)}}
      <div class="ov-drill-hint">Click to view consultants &#8250;</div>
    </div>`;
  }}
  if(!cards) cards = '<p style="color:var(--muted);padding:20px;font-size:13px">No data for this selection.</p>';
  const tlGrid = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:12px;margin-bottom:26px';
  document.getElementById('ov-report-cards').innerHTML = '<div style="'+tlGrid+'">'+cards+'</div>';
  _equalizeCardHeights();
}}

function renderMonthMgrView(month, type, region) {{
  document.getElementById('ov-single-month').style.display = 'none';
  document.getElementById('ov-soft-kpi-section').style.display = '';
  if(collChart) collChart.destroy();
  if(tvaChart)  tvaChart.destroy();

  if(month > 0) {{
    renderSoftKpiDailyView(month, type, region, _selMgrs, false);
    if(_selMgrs.length === 2) renderTrendDailyComparison(month, type, region, _selMgrs, false);
    else renderTrendDailySingle(month, type, region, _selMgrs[0], false);
    renderActiveGainDailyView(month, type, region, _selMgrs, false);
    renderRevenueTrend(type, region, month);
    renderEmpProdDailyView(month, type, region, _selMgrs, false);
  }} else {{
    renderSoftKpiTrends(type, region, month);
    if(_selMgrs.length === 2) renderTrendDailyComparison(month, type, region, _selMgrs, false);
    else renderTrendDaily(month, type);
    renderActiveGainChart(type, region, month);
    renderRevenueTrend(type, region, month);
    renderEmpProdChart(type, region, month);
  }}
  renderPkgOv(month, type);
  initDiscountTrendChart(type, region);

  if(_selMgrs.length === 1) {{
    const mg  = _selMgrs[0];
    const tls = MGR_TEAMS[mg] || [];
    const regionLabel = region !== 'all' ? ' · '+region : '';
    document.getElementById('ov-report-cards').style.display = '';
    document.getElementById('ov-single-top').style.display = 'none';
    document.getElementById('ov-kpi-tiles').innerHTML = '';
    let cards = '';
    for(const tl of tls) {{
      const p = applyFilters(DATA.filter(r => r.month===month && r.team===tl), type, region);
      if(p.length === 0) continue;
      const mm = calcMetrics(p);
      const tlName = TL_NAMES[tl] || tl;
      const isDirect = tl === mg;
      const tlRev = getRevenue([tl], month, type, region);
      cards += reportCard(tlName+(isDirect?' (Direct)':''), tl+' &mdash; '+MONTH_NAMES[month]+regionLabel+' &mdash; '+p.length+' members', mm, p.some(r=>r.is_ts), null, 'rc-tl-card', false, true, '', tlRev);
    }}
    if(!cards) cards = '<p style="color:var(--muted);padding:20px;font-size:13px">No data for this selection.</p>';
    document.getElementById('ov-report-cards').innerHTML = '<div class="rc-grid-wide">'+cards+'</div>';
    _equalizeCardHeights();
  }} else {{
    document.getElementById('ov-report-cards').style.display = '';
    document.getElementById('ov-single-top').style.display = 'none';
    const colorLabels = ['mgr-a', 'mgr-b'];
    let html = '<div class="ov-compare-grid">';
    _selMgrs.forEach((mg, idx) => {{
      const p       = _mgrPool(mg, type, region, month);
      const m       = calcMetrics(p);
      const mgrName = MGR_NAMES[mg] || mg;
      const mgrRev  = getRevenue(MGR_TEAMS[mg] || [], month, type, region);
      html += `<div><div class="ov-compare-label ${{colorLabels[idx]}}">${{mgrName}} &mdash; ${{MONTH_NAMES[month]}}</div>${{reportCard(mgrName, p.length+' consultants', m, p.some(r=>r.is_ts), null, 'rc-mgr-card', false, false, '', mgrRev, false, false, true)}}</div>`;
    }});
    html += '</div>';
    document.getElementById('ov-report-cards').innerHTML = html;
  }}
}}

function renderMonthTlView(month, type, region) {{
  document.getElementById('ov-single-month').style.display = 'none';
  document.getElementById('ov-soft-kpi-section').style.display = '';
  if(collChart) collChart.destroy();
  if(tvaChart)  tvaChart.destroy();

  if(month > 0) {{
    renderSoftKpiDailyView(month, type, region, _selTls, true);
    if(_selTls.length === 2) renderTrendDailyComparison(month, type, region, _selTls, true);
    else renderTrendDailySingle(month, type, region, _selTls[0], true);
    renderActiveGainDailyView(month, type, region, _selTls, true);
    renderRevenueTrend(type, region, month);
    renderEmpProdDailyView(month, type, region, _selTls, true);
  }} else {{
    renderSoftKpiTrends(type, region, month);
    if(_selTls.length === 2) renderTrendDailyComparison(month, type, region, _selTls, true);
    else renderTrendDaily(month, type);
    renderActiveGainChart(type, region, month);
    renderRevenueTrend(type, region, month);
    renderEmpProdChart(type, region, month);
  }}
  renderPkgOv(month, type);
  initDiscountTrendChart(type, region);

  if(_selTls.length === 1) {{
    const tl = _selTls[0];
    const pool = _tlPool(tl, type, region, month);
    const tlName = TL_NAMES[tl] || MGR_NAMES[tl] || tl;
    const regionLabel = region !== 'all' ? ' · '+region : '';
    document.getElementById('ov-report-cards').style.display = '';
    document.getElementById('ov-single-top').style.display = 'none';
    document.getElementById('ov-kpi-tiles').innerHTML = '';
    let cards = '';
    const tlSelf = pool.find(r => LEADERS.has(r.name));
    if(tlSelf && (tlSelf.coll > 0 || tlSelf.pkg > 0)) {{
      const cm = calcMetrics([tlSelf]);
      cards += reportCard(tlSelf.name+' (Team Lead)', tlName+' &mdash; '+MONTH_NAMES[month]+regionLabel, cm, tlSelf.is_ts, null, 'rc-tl-card', true, false, '', null, false, true);
    }}
    const consultants = pool.filter(r => !LEADERS.has(r.name));
    for(const r of consultants) {{
      const cm = calcMetrics([r]);
      cards += reportCard(r.name, tlName+' &mdash; '+MONTH_NAMES[month]+regionLabel, cm, r.is_ts, null, 'rc-consultant-card', true, false, '', null, false, true);
    }}
    if(!cards) cards = '<p style="color:var(--muted);padding:20px;font-size:13px">No data for this selection.</p>';
    document.getElementById('ov-report-cards').innerHTML = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:16px;margin-bottom:26px">'+cards+'</div>';
    _equalizeCardHeights();
  }} else {{
    document.getElementById('ov-report-cards').style.display = '';
    document.getElementById('ov-single-top').style.display = 'none';
    const colorLabels = ['mgr-a', 'mgr-b'];
    let html = '<div class="ov-compare-grid">';
    _selTls.forEach((tl, idx) => {{
      const p      = _tlPool(tl, type, region, month);
      const m      = calcMetrics(p);
      const tlName = TL_NAMES[tl] || MGR_NAMES[tl] || tl;
      const tlRev  = getRevenue(MGR_TEAMS[tl] || [tl], month, type, region);
      html += `<div><div class="ov-compare-label ${{colorLabels[idx]}}">${{tlName}} &mdash; ${{MONTH_NAMES[month]}}</div>${{reportCard(tlName, p.length+' consultants', m, p.some(r=>r.is_ts), null, 'rc-tl-card', false, false, '', tlRev, false, false, true)}}</div>`;
    }});
    html += '</div>';
    document.getElementById('ov-report-cards').innerHTML = html;
  }}
}}

function renderTrendDateRange(from, to, type, region) {{
  // TL/mgr comparison: fall back to monthly comparison chart
  if(_selMgrs.length > 0 || _selTls.length > 0) {{
    renderTrendMonthly(type, region);
    return;
  }}
  const src = type === 'online' ? ONLINE_COLL_DAILY : DAILY_COLL;
  const dayKeys = Object.keys(src).filter(d => d >= from && d <= to).sort();
  if(!dayKeys.length) {{
    document.getElementById('ov-trend-title').textContent = 'Daily Collections — No Data';
    if(trendChart) trendChart.destroy();
    return;
  }}
  const labels = dayKeys.map(d => {{
    const day = parseInt(d.split('-')[2]);
    const dow = DAY_SHORT[new Date(d).getDay()];
    return dow + ' ' + d.slice(5).replace('-','/');
  }});
  const amounts = dayKeys.map(d => {{
    if(type === 'online') return ONLINE_COLL_DAILY[d] || 0;
    const dc = DAILY_COLL[d]||{{}};
    if(type==='ts')    return dc.ts||0;
    if(type==='field') return dc.field||0;
    return (dc.ts||0)+(dc.field||0);
  }});
  let cum = 0;
  const cumAmounts = amounts.map(v => {{ cum += v; return cum; }});
  const maxBar  = niceMax(Math.max(...amounts, 0));
  const maxLine = niceMax(Math.max(...cumAmounts, 0));
  const fromLbl = from.slice(5).replace('-','/');
  const toLbl   = to.slice(5).replace('-','/');
  document.getElementById('ov-trend-title').textContent = `Daily Collections — ${{fromLbl}} to ${{toLbl}}`;
  if(trendChart) trendChart.destroy();
  trendChart = new Chart(document.getElementById('chart-trend'), {{
    type:'bar',
    data:{{labels, datasets:[
      {{type:'bar',  label:'Daily Collection', data:amounts,    backgroundColor:'#2a9d8faa', borderRadius:4, yAxisID:'y',  order:2, datalabels:{{display:false}}}},
      {{type:'line', label:'Cumulative',        data:cumAmounts, borderColor:'#000', backgroundColor:'transparent', borderWidth:2, pointRadius:2, tension:0.3, yAxisID:'y2', order:1, datalabels:{{display:false}}}}
    ]}},
    options:{{
      responsive:true, interaction:{{mode:'index',intersect:false}},
      plugins:{{legend:{{position:'bottom',labels:{{font:{{size:10}}}}}}, tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+fmt(ctx.parsed.y)}}}}, datalabels:{{display:false}}}},
      scales:{{
        x:{{ticks:{{font:{{size:9}},maxRotation:45,minRotation:45}}}},
        y: {{type:'linear',position:'left', beginAtZero:true,max:maxBar,  ticks:{{callback:v=>fmt(v)}},title:{{display:true,text:'Daily',      font:{{size:10}}}}}},
        y2:{{type:'linear',position:'right',beginAtZero:true,max:maxLine, ticks:{{callback:v=>fmt(v)}},title:{{display:true,text:'Cumulative', font:{{size:10}}}},grid:{{drawOnChartArea:false}}}}
      }}
    }}
  }});
}}

// ── Manager comparison drill-down (side-by-side report cards) ────────────────
function renderComparisonDrill(type, region) {{
  document.getElementById('ov-report-cards').style.display = '';
  document.getElementById('ov-single-top').style.display = 'none';
  document.getElementById('ov-single-month').style.display = 'none';
  document.getElementById('ov-soft-kpi-section').style.display = '';
  if(collChart) collChart.destroy();
  if(tvaChart)  tvaChart.destroy();
  renderSoftKpiTrends(type, region, _ovDrillMonth);
  const mn = _ovDrillMonth;
  const colorLabels = ['mgr-a', 'mgr-b'];
  let html = '<div class="ov-compare-grid">';
  _selMgrs.forEach((mg, idx) => {{
    const p       = _mgrPool(mg, type, region, mn);
    const m       = calcMetrics(p);
    const mgrName = MGR_NAMES[mg] || mg;
    const mgrRev  = getRevenue(MGR_TEAMS[mg] || [], mn, type, region);
    html += `<div>
      <div class="ov-compare-label ${{colorLabels[idx]}}">${{mgrName}} &mdash; ${{MONTH_NAMES[mn]}}</div>
      ${{reportCard(mgrName, p.length+' consultants', m, p.some(r=>r.is_ts), null, 'rc-mgr-card', false, false, '', mgrRev, false, false, true)}}
    </div>`;
  }});
  html += '</div>';
  document.getElementById('ov-report-cards').innerHTML = html;
}}

// ── TL comparison drill-down (side-by-side report cards) ─────────────────────
function renderTlComparisonDrill(type, region) {{
  document.getElementById('ov-report-cards').style.display = '';
  document.getElementById('ov-single-top').style.display = 'none';
  document.getElementById('ov-single-month').style.display = 'none';
  document.getElementById('ov-soft-kpi-section').style.display = '';
  if(collChart) collChart.destroy();
  if(tvaChart)  tvaChart.destroy();
  renderSoftKpiTrends(type, region, _ovDrillMonth);
  const mn = _ovDrillMonth;
  const colorLabels = ['mgr-a', 'mgr-b'];
  let html = '<div class="ov-compare-grid">';
  _selTls.forEach((tl, idx) => {{
    const p      = _tlPool(tl, type, region, mn);
    const m      = calcMetrics(p);
    const tlName = TL_NAMES[tl] || MGR_NAMES[tl] || tl;
    const tlRev  = getRevenue(MGR_TEAMS[tl] || [tl], mn, type, region);
    html += `<div>
      <div class="ov-compare-label ${{colorLabels[idx]}}">${{tlName}} &mdash; ${{MONTH_NAMES[mn]}}</div>
      ${{reportCard(tlName, p.length+' consultants', m, p.some(r=>r.is_ts), null, 'rc-tl-card', false, false, '', tlRev, false, false, true)}}
    </div>`;
  }});
  html += '</div>';
  document.getElementById('ov-report-cards').innerHTML = html;
}}

function render() {{
  const month  = +document.getElementById('f-month').value;
  const type   = document.getElementById('f-type').value;
  const region = document.getElementById('f-region').value;

  _viewMths = _computeViewMths();
  _syncResetBtn();
  _ovSetBreadcrumb();

  // Drill-down: consultant cards for a TL
  if(_ovDrillTl !== '') {{
    renderOvConsultantCards(type, region);
    return;
  }}

  // Drill-down: TL cards for a manager
  if(_ovDrillMgr !== '') {{
    renderOvTlCards(type, region);
    return;
  }}

  // Drill-down: manager cards for a month (or side-by-side comparison when 2 selected)
  if(_ovDrillMonth !== 0) {{
    if(_selTls.length === 2) {{ renderTlComparisonDrill(type, region); }}
    else if(_selMgrs.length === 2) {{ renderComparisonDrill(type, region); }}
    else {{ renderOvMgrCards(type, region); }}
    return;
  }}

  // Date filter active → keep default view, aggregate metrics across date-range months
  if(_dateFrom || _dateTo) {{
    _ovDrillMonth = 0; _ovDrillMgr = ''; _ovSetBreadcrumb();
    document.getElementById('ov-report-cards').style.display = '';
    document.getElementById('ov-single-top').style.display = 'none';
    document.getElementById('ov-single-month').style.display = 'none';
    if(collChart) collChart.destroy();
    if(tvaChart)  tvaChart.destroy();

    // Aggregate pool across exact days in date range (day-granular via DAILY_METRICS)
    const pool = _buildDailyPool(type, region);
    const m    = calcMetrics(pool);
    const isTS = type === 'ts';
    const mnRev = _viewMths.reduce((s,mn) => s+(getRevenue(Object.keys(REV_TL),mn,type,region)||0),0)||0;

    const tile = (label, val, sub, highlight) =>
      `<div class="kpi-card${{highlight?' highlight':''}}" style="padding:11px 13px">
        <div class="kpi-label" style="font-size:9.5px">${{label}}</div>
        <div class="kpi-val" style="font-size:19px">${{val}}</div>
        ${{sub ? `<div class="kpi-sub" style="font-size:10px;margin-top:3px;line-height:1.35">${{sub}}</div>` : ''}}
      </div>`;
    const cashPerEmp = m.bom>0 ? fmt(m.cash/m.bom) : '-';
    const hardTiles =
      tile('Cash Collection', fmt(m.cash), 'Target: '+fmt(m.target)+' · /Emp: '+cashPerEmp, true) +
      tile('TvA', pct(m.cash,m.target), tvaRating(m.tva)) +
      (mnRev ? tile('Revenue', fmt(mnRev), '') : '') +
      tile('Packages Sold', m.pkgSold, 'Avg Discount: '+(m.avgDisc>0?Math.round(m.avgDisc*100)+'% ('+(m.avgDiscNew!==null?m.avgDiscNew+'%':'-')+'/'+(m.avgDiscRen!==null?m.avgDiscRen+'%':'-')+')':'-')) +
      tile('Net Client Gain', Math.round(m.netGain), 'Active (EOM): '+m.active) +
      tile('Productivity', m.bom>0 ? Math.round(m.productivity)+'%' : '-', 'Productive (≥4K): '+m.productive+' / BOM: '+m.bom) +
      tile('Coverage %', Math.round(m.covPct)+'%', '') +
      tile('Active Listings', TOTAL_ACTIVE_LISTINGS_SNAPSHOT.toLocaleString(), 'Listings/Agency: '+(m.listingsPerAgency!==null?m.listingsPerAgency.toFixed(1):'-'));
    const softTiles =
      tile('Avg UQC / Day', m.avgUqc.toFixed(1), 'Total: '+m.totalUqc.toLocaleString()) +
      tile('Avg DTT / Day', m.avgDtt.toFixed(1)+' min', 'Total: '+fmt(m.totalDtt)+' min') +
      (!isTS ? tile('Avg VM / Day', m.avgVm!==null ? m.avgVm.toFixed(1) : 'N/A', 'Total: '+m.totalVm.toLocaleString()) : '');
    const regionLabel = region !== 'all' ? ' · '+region : '';
    const totalN = (mnRev?8:7)+(isTS?2:3);
    const allGrid = `display:grid;grid-template-columns:repeat(${{totalN}},minmax(0,1fr));gap:8px;margin-bottom:16px`;
    const dateLabel = _dateFrom.slice(5).replace('-','/')+' \u2013 '+_dateTo.slice(5).replace('-','/');
    const tilesHtml =
      `<div class="sec-header"><div class="sec-title">${{dateLabel}}${{regionLabel}} &mdash; ${{pool.length}} consultants</div><div class="sec-badge hard-badge">Financial &amp; Activity</div></div>
       <div style="${{allGrid}}">${{hardTiles}}${{softTiles}}</div>`;

    // Manager breakdown cards aggregated across date range months
    const latestMn = Math.max(..._viewMths);
    let mgrCards = '';
    for(const mg of Object.keys(MGR_TEAMS)) {{
      let p = pool.filter(r => MGR_POOL_BY_TEAM.has(mg) ? r.team===mg : r.mgr===mg);
      if(p.length === 0) continue;
      const mm     = calcMetrics(p);
      const mgrName = MGR_NAMES[mg] || mg;
      const mgrRev  = _viewMths.reduce((s,mn) => s+(getRevenue(MGR_TEAMS[mg]||[],mn,type,region)||0),0)||0;
      const _defHint = (MGR_TEAMS[mg]||[]).length===1&&MGR_TEAMS[mg][0]===mg ? 'Click to view consultants' : 'Click to view TL breakdown';
      mgrCards += `<div class="ov-drill-wrap" onclick="_ovDrillMonth=${{latestMn}};_drillMonthImplicit=true;drillOvMgr('${{mg}}')">
        ${{reportCard(mgrName, mg+' &mdash; '+dateLabel+' &mdash; '+p.length+' consultants', mm, p.some(r=>r.is_ts), null, 'rc-mgr-card', false, false, '', mgrRev, true)}}
        <div class="ov-drill-hint">${{_defHint}} &#8250;</div>
      </div>`;
    }}
    const mgrGrid = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:12px;margin-bottom:26px';
    const mgrHtml = mgrCards
      ? `<div class="sec-header" style="margin-top:24px"><div class="sec-title">Manager Breakdown &mdash; ${{dateLabel}}</div></div><div style="${{mgrGrid}}">${{mgrCards}}</div>`
      : '';

    document.getElementById('ov-report-cards').innerHTML = tilesHtml+mgrHtml;
    _equalizeCardHeights();
    renderTrendDateRange(_dateFrom, _dateTo, type, region);
    renderActiveGainChart(type, region, 0);
    renderRevenueTrend(type, region, 0);
    renderPkgOv(0, type);
    renderEmpProdChart(type, region, 0);
    initDiscountTrendChart(type, region);
    document.getElementById('ov-soft-kpi-section').style.display = '';
    renderSoftKpiTrends(type, region, 0);
    return;
  }}

  // All Months view
  if(month === 0) {{
    _ovDrillMonth = 0; _ovDrillMgr = ''; _ovSetBreadcrumb();
    document.getElementById('ov-report-cards').style.display = '';
    document.getElementById('ov-single-top').style.display = 'none';
    document.getElementById('ov-single-month').style.display = 'none';
    if(collChart) collChart.destroy();
    if(tvaChart) tvaChart.destroy();

    // Manager filter active in All Months view → show TL/comparison cards using latest month
    if(_selMgrs.length > 0) {{
      renderMonthMgrView(Math.max(...ALL_MONTHS), type, region);
      return;
    }}
    // TL filter active in All Months view → show consultant/comparison cards using latest month
    if(_selTls.length > 0) {{
      renderMonthTlView(Math.max(...ALL_MONTHS), type, region);
      return;
    }}
    // Default view: KPI tiles for current (latest) month + manager breakdown cards for that month
    const curMn  = Math.max(...ALL_MONTHS);
    const tile = (label, val, sub, highlight) =>
      `<div class="kpi-card${{highlight?' highlight':''}}" style="padding:11px 13px">
        <div class="kpi-label" style="font-size:9.5px">${{label}}</div>
        <div class="kpi-val" style="font-size:19px">${{val}}</div>
        ${{sub ? `<div class="kpi-sub" style="font-size:10px;margin-top:3px;line-height:1.35">${{sub}}</div>` : ''}}
      </div>`;

    // --- Online channel: Cash Collection + Packages Sold + Active Listings ---
    if(type === 'online') {{
      const onlineCash     = ONLINE_COLL_MONTHLY[String(curMn)] || 0;
      const onlinePkg      = ONLINE_PKG_MONTHLY[String(curMn)]  || 0;
      const onlineTotal    = ONLINE_LISTINGS.total    || 0;
      const onlineAgencies = ONLINE_LISTINGS.agencies || 0;
      const listPerAgency  = onlineAgencies > 0 ? (onlineTotal / onlineAgencies).toFixed(1) : '-';
      const tilesHtml =
        `<div class="sec-header"><div class="sec-title">${{MONTH_NAMES[curMn]}} &mdash; Online Channel</div><div class="sec-badge hard-badge">Online KPIs</div></div>
         <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-bottom:16px;max-width:700px">
           ${{tile('Cash Collection', fmt(onlineCash), 'Online self-serve payments', true)}}
           ${{tile('Packages Sold', onlinePkg > 0 ? onlinePkg : '-', 'Named packages via online channel')}}
           ${{tile('Active Listings', onlineTotal.toLocaleString(), 'Listings/Agency: ' + listPerAgency)}}
         </div>`;
      document.getElementById('ov-report-cards').innerHTML = tilesHtml;
      _equalizeCardHeights();
      renderTrendDaily(curMn, type);
      document.getElementById('ov-soft-kpi-section').style.display = 'none';
      return;
    }}

    const pool   = applyFilters(DATA.filter(r => r.month === curMn && r.mgr !== ''), type, region);
    const m      = calcMetrics(pool);
    const isTS   = type === 'ts';
    const mnRev  = getRevenue(Object.keys(REV_TL), curMn, type, region);
    // When 'all' selected, add online channel cash to total
    const onlineAddon = type === 'all' ? (ONLINE_COLL_MONTHLY[String(curMn)] || 0) : 0;
    const effectiveCash = m.cash + onlineAddon;
    const effectiveTva  = m.target > 0 ? effectiveCash / m.target : null;
    const cashPerEmp = m.bom>0 ? fmt(effectiveCash/m.bom) : '-';
    const hardTiles =
      tile('Cash Collection', fmt(effectiveCash), 'Target: '+fmt(m.target)+' · /Emp: '+cashPerEmp, true) +
      tile('TvA', pct(effectiveCash,m.target), tvaRating(effectiveTva)) +
      (mnRev ? tile('Revenue', fmt(mnRev), '') : '') +
      tile('Packages Sold', m.pkgSold, 'Avg Discount: '+(m.avgDisc>0?Math.round(m.avgDisc*100)+'% ('+(m.avgDiscNew!==null?m.avgDiscNew+'%':'-')+'/'+(m.avgDiscRen!==null?m.avgDiscRen+'%':'-')+')':'-')) +
      tile('Net Client Gain', Math.round(m.netGain), 'Active (EOM): '+m.active) +
      tile('Productivity', m.bom>0 ? Math.round(m.productivity)+'%' : '-', 'Productive (≥4K): '+m.productive+' / BOM: '+m.bom) +
      tile('Coverage %', Math.round(m.covPct)+'%', '') +
      tile('Active Listings', TOTAL_ACTIVE_LISTINGS_SNAPSHOT.toLocaleString(), 'Listings/Agency: '+(m.listingsPerAgency!==null?m.listingsPerAgency.toFixed(1):'-'));
    const softTiles =
      tile('Avg UQC / Day', m.avgUqc.toFixed(1), 'Total: '+m.totalUqc.toLocaleString()) +
      tile('Avg DTT / Day', m.avgDtt.toFixed(1)+' min', 'Total: '+fmt(m.totalDtt)+' min') +
      (!isTS ? tile('Avg VM / Day', m.avgVm!==null ? m.avgVm.toFixed(1) : 'N/A', 'Total: '+m.totalVm.toLocaleString()) : '');
    const regionLabel = region !== 'all' ? ' · '+region : '';
    const totalN = (mnRev?8:7)+(isTS?2:3);
    const allGrid = `display:grid;grid-template-columns:repeat(${{totalN}},minmax(0,1fr));gap:8px;margin-bottom:16px`;
    const tilesHtml =
      `<div class="sec-header"><div class="sec-title">${{MONTH_NAMES[curMn]}}${{regionLabel}} &mdash; ${{pool.length}} consultants</div><div class="sec-badge hard-badge">Financial &amp; Activity</div></div>
       <div style="${{allGrid}}">${{hardTiles}}${{softTiles}}</div>`;
    // Manager breakdown cards for current month
    let mgrCards = '';
    for(const mg of Object.keys(MGR_TEAMS)) {{
      if(mg === 'AlHourani - TL Riyadh' && curMn < 4) continue;
      if(mg === 'Mohamed Abdullah - M3' && curMn >= 4) continue;
      let p = applyFilters(DATA.filter(r => r.month === curMn && (MGR_POOL_BY_TEAM.has(mg) ? r.team === mg : r.mgr === mg)), type, region);
      if(p.length === 0) continue;
      const mm = calcMetrics(p);
      const mgrName = MGR_NAMES[mg] || mg;
      const mgrRev  = getRevenue(MGR_TEAMS[mg] || [], curMn, type, region);
      const _defHint = (MGR_TEAMS[mg]||[]).length===1&&MGR_TEAMS[mg][0]===mg ? 'Click to view consultants' : 'Click to view TL breakdown';
      mgrCards += `<div class="ov-drill-wrap" onclick="_ovDrillMonth=${{curMn}};_drillMonthImplicit=true;drillOvMgr('${{mg}}')">
        ${{reportCard(mgrName, mg+' &mdash; '+MONTH_NAMES[curMn]+' &mdash; '+p.length+' consultants', mm, p.some(r=>r.is_ts), null, 'rc-mgr-card', false, false, '', mgrRev, true)}}
        <div class="ov-drill-hint">${{_defHint}} &#8250;</div>
      </div>`;
    }}
    const mgrGrid = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:12px;margin-bottom:26px';
    const mgrHtml = mgrCards
      ? `<div class="sec-header" style="margin-top:24px"><div class="sec-title">Manager Breakdown &mdash; ${{MONTH_NAMES[curMn]}}</div></div><div style="${{mgrGrid}}">${{mgrCards}}</div>`
      : '';
    document.getElementById('ov-report-cards').innerHTML = tilesHtml + mgrHtml;
    _equalizeCardHeights();
    renderTrendMonthly(type, region);
    renderActiveGainChart(type, region, 0);
    renderRevenueTrend(type, region, 0);
    renderPkgOv(0, type);
    renderEmpProdChart(type, region, 0);
    initDiscountTrendChart(type, region);
    document.getElementById('ov-soft-kpi-section').style.display = '';
    renderSoftKpiTrends(type, region, 0);
    return;
  }}

  // Specific month selected via dropdown — reset any drill state
  _ovDrillMonth = 0;
  _ovDrillMgr   = '';
  _ovSetBreadcrumb();

  // Specific month + TL filter → report card(s) for selected TL(s)
  if(_selTls.length > 0) {{
    renderMonthTlView(month, type, region);
    return;
  }}

  // Specific month + manager filter → report card view (single or side-by-side)
  if(_selMgrs.length > 0) {{
    renderMonthMgrView(month, type, region);
    return;
  }}

  // Specific month -> KPI tiles + daily trend + manager charts
  document.getElementById('ov-report-cards').style.display = 'none';
  document.getElementById('ov-single-top').style.display = '';
  document.getElementById('ov-single-month').style.display = 'none';
  document.getElementById('ov-soft-kpi-section').style.display = '';
  renderSoftKpiDailyView(month, type, region, [], null);
  renderTrendDaily(month, type);
  renderActiveGainDailyView(month, type, region, [], null);
  renderRevenueTrend(type, region, month);
  renderPkgOv(month, type);
  renderEmpProdDailyView(month, type, region, [], null);
  initDiscountTrendChart(type, region);

  let pool = applyFilters(DATA.filter(r => r.month === month && r.mgr !== ''), type, region);
  const m = calcMetrics(pool);
  const isTS = type === 'ts';
  const monthRev = getRevenue(Object.keys(REV_TL), month, type, region);

  // KPI tiles for selected month — compact sizing matches default (All Months) view
  const tile = (label, val, sub, highlight) =>
    `<div class="kpi-card${{highlight?' highlight':''}}" style="padding:11px 13px">
      <div class="kpi-label" style="font-size:9.5px">${{label}}</div>
      <div class="kpi-val" style="font-size:19px">${{val}}</div>
      ${{sub ? `<div class="kpi-sub" style="font-size:10px;margin-top:3px;line-height:1.35">${{sub}}</div>` : ''}}
    </div>`;

  const onlineAddon = type === 'all' ? (ONLINE_COLL_MONTHLY[String(month)] || 0) : 0;
  const effectiveCash = m.cash + onlineAddon;
  const cashPerEmp = m.bom>0 ? fmt(effectiveCash/m.bom) : '-';
  const hardTiles =
    tile('Cash Collection', fmt(effectiveCash), 'Target: '+fmt(m.target)+' · /Emp: '+cashPerEmp, true) +
    tile('TvA', pct(effectiveCash,m.target), tvaRating(m.tva)) +
    (monthRev ? tile('Revenue', fmt(monthRev), '') : '') +
    tile('Packages Sold', m.pkgSold, 'Avg Discount: '+(m.avgDisc>0?Math.round(m.avgDisc*100)+'% ('+(m.avgDiscNew!==null?m.avgDiscNew+'%':'-')+'/'+(m.avgDiscRen!==null?m.avgDiscRen+'%':'-')+')':'-')) +
    tile('Net Client Gain', Math.round(m.netGain), 'Active (EOM): '+m.active) +
    tile('Productivity', m.bom>0 ? Math.round(m.productivity)+'%' : '-', 'Productive (≥4K): '+m.productive+' / BOM: '+m.bom) +
    tile('Coverage %', Math.round(m.covPct)+'%', '') +
    tile('Active Listings', TOTAL_ACTIVE_LISTINGS_SNAPSHOT.toLocaleString(), 'Listings/Agency: '+(m.listingsPerAgency!==null?m.listingsPerAgency.toFixed(1):'-'));

  const softTiles =
    tile('Avg UQC / Day', m.avgUqc.toFixed(1), 'Total: '+m.totalUqc.toLocaleString()) +
    tile('Avg DTT / Day', m.avgDtt.toFixed(1)+' min', 'Total: '+fmt(m.totalDtt)+' min') +
    (!isTS ? tile('Avg VM / Day', m.avgVm!==null ? m.avgVm.toFixed(1) : 'N/A', 'Total: '+m.totalVm.toLocaleString()) : '');

  const regionLabel = region !== 'all' ? ' · '+region : '';
  const totalN = (monthRev ? 8 : 7) + (isTS ? 2 : 3);
  const allGrid = `display:grid;grid-template-columns:repeat(${{totalN}},minmax(0,1fr));gap:8px;margin-bottom:16px`;
  document.getElementById('ov-kpi-tiles').innerHTML =
    `<div class="sec-header"><div class="sec-title">${{MONTH_NAMES[month]}}${{regionLabel}} \u2014 ${{pool.length}} consultants</div><div class="sec-badge hard-badge">Financial &amp; Activity</div></div>
     <div style="${{allGrid}}">${{hardTiles}}${{softTiles}}</div>`;

  // Charts - Collection by Manager (filtered by region)
  const allMgrs = Object.keys(MGR_TEAMS);
  const mgrData = allMgrs.map(mg => {{
    const p = applyFilters(DATA.filter(r => r.month===month && r.mgr===mg), type, region);
    return {{ mg, p, cash: p.reduce((s,r)=>s+r.coll,0), target: p.reduce((s,r)=>s+r.target,0) }};
  }}).filter(d => d.p.length > 0);

  const mgrCash   = mgrData.map(d => d.cash);
  const mgrTarget = mgrData.map(d => d.target);
  const mgrLabels = mgrData.map(d => MGR_NAMES[d.mg]||d.mg);

  const _collMax = niceMax(Math.max(...mgrCash,...mgrTarget,1)*1.15);
  if(collChart) collChart.destroy();
  collChart = new Chart(document.getElementById('chart-coll'), {{
    type:'bar',
    data:{{ labels:mgrLabels, datasets:[
      {{label:'Collection',data:mgrCash,backgroundColor:'#5c6bc0',datalabels:{{..._DL_BAR, formatter:v=>fmt(v)}}}},
      {{label:'Target',data:mgrTarget,backgroundColor:'#e8eaf6',datalabels:{{..._DL_BAR, formatter:v=>fmt(v)}}}}
    ]}},
    options:{{ responsive:true, clip:false, layout:{{padding:{{top:24}}}}, plugins:{{legend:{{position:'bottom',labels:{{font:{{size:10}}}}}},datalabels:{{display:true}}}}, scales:{{y:{{max:_collMax,ticks:{{callback:v=>fmtM(v)}}}}}} }}
  }});

  const mgrTva = mgrData.map(d => d.target > 0 ? d.cash/d.target*100 : 0);
  const _tvaMax = niceMax(Math.max(...mgrTva,1)*1.15);
  if(tvaChart) tvaChart.destroy();
  tvaChart = new Chart(document.getElementById('chart-tva'), {{
    type:'bar',
    data:{{ labels:mgrLabels, datasets:[
      {{label:'TvA %',data:mgrTva,backgroundColor:mgrTva.map(v => v>=100?'#66bb6a':v>=75?'#42a5f5':'#ef5350'),datalabels:{{..._DL_BAR, formatter:v=>v.toFixed(0)+'%'}}}}
    ]}},
    options:{{ responsive:true, plugins:{{legend:{{display:false}},datalabels:{{display:false}}}}, scales:{{y:{{max:_tvaMax,ticks:{{callback:v=>v+'%'}}}}}} }}
  }});

  // Manager summary table (filtered by region)
  let tbl = '<table><thead><tr><th>Manager</th><th class="num th-hard">Cash</th><th class="num th-hard">Target</th><th class="num th-hard">TvA</th><th class="num">Pkgs</th><th class="num">Active</th><th class="num">BOM</th><th class="num">Prod%</th><th class="num th-soft">UQC</th><th class="num th-soft">DTT</th><th class="num th-soft">VM</th><th class="num">Net Gain</th><th class="num">Cov%</th><th class="num">Renewed</th></tr></thead><tbody>';
  for(const {{mg, p}} of mgrData) {{
    const mgrN = MGR_NAMES[mg]||mg;
    const pm = calcMetrics(p);
    tbl += `<tr><td class="td-name">${{mgrN}}</td><td class="num">${{fmt(pm.cash)}}</td><td class="num">${{fmt(pm.target)}}</td><td class="num"><span class="pill ${{tvaColor(pm.tva)}}">${{pct(pm.cash,pm.target)}}</span></td><td class="num">${{pm.pkgSold}}</td><td class="num">${{pm.active}}</td><td class="num">${{pm.bom}}</td><td class="num">${{Math.round(pm.productivity)}}%</td><td class="num">${{pm.avgUqc.toFixed(1)}}</td><td class="num">${{pm.avgDtt.toFixed(1)}}</td><td class="num">${{pm.avgVm!==null?pm.avgVm.toFixed(1):'N/A'}}</td><td class="num">${{pm.netGain}}</td><td class="num">${{Math.round(pm.covPct)}}%</td><td class="num">${{pm.renewed}}</td></tr>`;
  }}
  tbl += '</tbody></table>';
  document.getElementById('ov-mgr-table').innerHTML = tbl;
}}

// ============ MANAGER VIEW — LAYOUT STATE ============
let _mgrTlState = {{ month: 0, mgr: '', allTls: [], tlCash: {{}}, mgrCash: 0, openTls: new Set(), showDirect: true }};

function selectTlCard(tl, month) {{
  if(_mgrTlState.openTls.has(tl)) _mgrTlState.openTls.delete(tl);
  else _mgrTlState.openTls.add(tl);
  _renderMgrLayout();
}}

function toggleDirect() {{
  _mgrTlState.showDirect = !_mgrTlState.showDirect;
  _renderMgrLayout();
}}

// Horizontal branch connector (manager → right card)
function _hConn() {{
  return `<div style="width:32px;flex-shrink:0;display:flex;align-items:center;justify-content:center">
    <div style="width:100%;height:2px;background:var(--accent);position:relative">
      <div style="position:absolute;top:50%;left:0;transform:translateY(-50%);width:7px;height:7px;border-radius:50%;background:var(--accent)"></div>
      <div style="position:absolute;top:50%;right:0;transform:translateY(-50%);width:7px;height:7px;border-radius:50%;background:var(--accent)"></div>
    </div>
  </div>`;
}}

// Vertical connector (below manager → down to next row)
// showDirectBranch=true: L-shaped branch from manager's right corner to Direct Reportees column.
//   The branch point is at the LEFT EDGE of the 32px gap (= right edge of manager card).
//   All connectors use the same dot-endpoint style as _hConn for visual consistency.
function _vConn(hasRightCol, showDirectBranch) {{
  if(showDirectBranch) {{
    // Left col: straight vertical with dots at top and bottom (for TL2)
    // 32px gap: vertical stub (top→mid) + horizontal (left→right) + dot at corner bend
    // Right col: horizontal (left→center) + vertical (mid→bottom) + dots at T-junction and bottom
    return `<div style="display:flex;height:22px;pointer-events:none;overflow:visible">
      <div style="flex:1;position:relative;display:flex;justify-content:center;overflow:visible">
        <div style="width:2px;height:100%;background:var(--accent);position:relative">
          <div style="position:absolute;top:0;left:50%;transform:translate(-50%,-50%);width:7px;height:7px;border-radius:50%;background:var(--accent)"></div>
          <div style="position:absolute;bottom:0;left:50%;transform:translate(-50%,50%);width:7px;height:7px;border-radius:50%;background:var(--accent)"></div>
        </div>
      </div>
      <div style="width:32px;position:relative;overflow:visible">
        <div style="position:absolute;top:0;left:0;width:2px;height:12px;background:var(--accent)"></div>
        <div style="position:absolute;top:11px;left:0;right:0;height:2px;background:var(--accent)"></div>
        <div style="position:absolute;top:0;left:0;transform:translate(-50%,-50%);width:7px;height:7px;border-radius:50%;background:var(--accent)"></div>
        <div style="position:absolute;top:11px;left:0;transform:translate(-50%,-50%);width:7px;height:7px;border-radius:50%;background:var(--accent)"></div>
      </div>
      <div style="flex:1;position:relative;overflow:visible">
        <div style="position:absolute;top:11px;left:0;width:50%;height:2px;background:var(--accent)"></div>
        <div style="position:absolute;top:11px;left:calc(50% - 1px);width:2px;height:11px;background:var(--accent)"></div>
        <div style="position:absolute;top:11px;left:50%;transform:translate(-50%,-50%);width:7px;height:7px;border-radius:50%;background:var(--accent)"></div>
        <div style="position:absolute;bottom:0;left:50%;transform:translate(-50%,50%);width:7px;height:7px;border-radius:50%;background:var(--accent)"></div>
      </div>
    </div>`;
  }}
  return `<div style="display:flex;height:22px;pointer-events:none;overflow:visible">
    <div style="flex:1;position:relative;display:flex;justify-content:center;overflow:visible">
      <div style="width:2px;height:100%;background:var(--accent);position:relative">
        <div style="position:absolute;top:0;left:50%;transform:translate(-50%,-50%);width:7px;height:7px;border-radius:50%;background:var(--accent)"></div>
        <div style="position:absolute;bottom:0;left:50%;transform:translate(-50%,50%);width:7px;height:7px;border-radius:50%;background:var(--accent)"></div>
      </div>
    </div>
    ${{hasRightCol ? '<div style="width:32px"></div><div style="flex:1"></div>' : ''}}
  </div>`;
}}

// Render a single TL slot (button when collapsed, card when open)
// isBottom=true: button aligns to flex-start so it connects flush with vertical connector above
function _tlSlot(tl, isBottom) {{
  const {{ month, tlCash, mgrCash, openTls }} = _mgrTlState;
  if(!tl) return '<div style="flex:1;min-width:0"></div>';
  if(!openTls.has(tl)) {{
    const cash = tlCash[tl] || 0;
    const pct  = mgrCash > 0 ? Math.round(cash/mgrCash*100) : 0;
    return `<div style="flex:1;min-width:0;display:flex;align-items:${{isBottom?'flex-start':'center'}}">
      <div class="tl-branch-btn" onclick="selectTlCard('${{tl}}',${{month}})" style="width:100%">
        ${{TL_NAMES[tl]||tl}}<span class="tl-cash">${{fmt(cash)}} (${{pct}}%)</span>
      </div>
    </div>`;
  }}
  const tlN = TL_NAMES[tl] || tl;
  const p   = DATA.filter(r => r.month===month && r.team===tl);
  if(!p.length) return '<div style="flex:1;min-width:0"></div>';
  const m   = calcMetrics(p);
  const minBtn = `<button class="tl-min-btn" onclick="selectTlCard('${{tl}}',${{month}})" title="Minimize">&#x2212;</button>`;
  const card = reportCard(tlN, tl+' &mdash; '+MONTH_NAMES[month]+' &mdash; '+p.length+' members',
                          m, p.some(r=>r.is_ts), null, 'mgr-tl-card', false, true, minBtn);
  return `<div style="flex:1;min-width:0;display:flex;flex-direction:column">${{card}}</div>`;
}}

// Full manager 2×2 layout render
function _renderMgrLayout() {{
  const el = document.getElementById('mgr-hard-kpis');
  if(!el) return;
  const {{ month, mgr, allTls, openTls, showDirect }} = _mgrTlState;

  const pool    = DATA.filter(r => r.month===month && r.mgr===mgr);
  const mgrName = MGR_NAMES[mgr] || mgr;
  const pm      = calcMetrics(pool);
  const isTS    = pool.some(r=>r.is_ts);
  const tlBd    = getTlBreakdown(mgr, [month]);
  const mgrCard = reportCard(mgrName, mgr+' &mdash; '+MONTH_NAMES[month]+' &mdash; '+pm.poolSize+' members',
                              pm, isTS, tlBd, '', false, true);

  const tl1      = allTls[0] || null;
  const tl2      = allTls[1] || null;
  const extraTls = allTls.slice(2);

  // Direct reportees: pool members whose team is NOT one of the TL teams
  const directPool = pool.filter(r => r.name !== mgrName && !allTls.includes(r.team));

  // Build direct content: full card (with minimize btn) or collapsed button
  let directContent = '';
  if(directPool.length > 0) {{
    if(showDirect) {{
      const dm = calcMetrics(directPool);
      const minBtn = `<button class="tl-min-btn" onclick="toggleDirect()" title="Minimize">&#x2212;</button>`;
      const card = reportCard('Direct Reportees',
        mgrName+' &mdash; '+MONTH_NAMES[month]+' &mdash; '+directPool.length+' direct',
        dm, directPool.some(r=>r.is_ts), null, 'mgr-direct-card', false, true, minBtn);
      directContent = `<div style="flex:1;min-width:0;display:flex;flex-direction:column">${{card}}</div>`;
    }} else {{
      const cash = directPool.reduce((s,r) => s+r.coll, 0);
      const pct  = _mgrTlState.mgrCash > 0 ? Math.round(cash/_mgrTlState.mgrCash*100) : 0;
      directContent = `<div style="flex:1;min-width:0;display:flex;align-items:flex-start">
        <div class="tl-branch-btn" onclick="toggleDirect()" style="width:100%;border-color:#059669;color:#059669">
          Direct Reportees<span class="tl-cash">${{fmt(cash)}} (${{pct}}%)</span>
        </div>
      </div>`;
    }}
  }}

  let html = '';
  const rightColExists = tl1 !== null;

  // ── Row 1: Manager │ connector │ TL1 (or Direct if no TLs) ──
  html += `<div style="display:flex;align-items:stretch;gap:0">`;
  html += `<div style="flex:1;min-width:0;display:flex;flex-direction:column">${{mgrCard}}</div>`;
  if(tl1) {{
    html += _hConn();
    html += _tlSlot(tl1, false);
  }} else if(directContent) {{
    // No TLs — show direct reportees to the right of manager
    html += _hConn();
    html += directContent;
    directContent = '';
  }}
  html += '</div>';

  // ── Row 2: left col stacks TL2 + all extra TLs; right col has Direct Reportees ──
  // align-items:flex-start keeps the two columns independent — left col height is driven
  // only by the TL buttons/cards, not stretched by the (potentially tall) Direct card.
  const directInRow2Right = !!(tl2 && directContent);
  const hasRow2 = tl2 || directContent || extraTls.length > 0;
  if(hasRow2) {{
    html += _vConn(rightColExists, directInRow2Right);
    html += `<div style="display:flex;align-items:flex-start;gap:0">`;

    if(tl2) {{
      // Left col: TL2 followed by any extra TLs, each separated by a mini-vConn
      html += `<div style="flex:1;min-width:0">`;
      html += _tlSlot(tl2, true);
      for(const tl of extraTls) {{
        html += _vConn(false, false);
        html += _tlSlot(tl, true);
      }}
      html += '</div>';
      // 32px gap + right col (Direct or empty spacer)
      if(directContent) {{
        html += '<div style="width:32px"></div>';
        html += directContent;
        directContent = '';
      }} else if(rightColExists) {{
        html += '<div style="width:32px"></div><div style="flex:1;min-width:0"></div>';
      }}
    }} else if(directContent) {{
      // No TL2 — Direct goes under manager column
      html += `<div style="flex:1;min-width:0">${{directContent}}</div>`;
      directContent = '';
      if(rightColExists) html += '<div style="width:32px"></div><div style="flex:1;min-width:0"></div>';
    }} else {{
      html += '<div style="flex:1;min-width:0"></div>';
      if(rightColExists) html += '<div style="width:32px"></div><div style="flex:1;min-width:0"></div>';
    }}

    html += '</div>';
  }}

  el.style.cssText = 'display:block;grid-template-columns:none;gap:0;margin-bottom:0';
  el.innerHTML = html;
  el.querySelectorAll('.rc-card').forEach(c => {{ c.style.flex = '1'; }});
}}

// ============ AGENT PERFORMANCE TABLE ============
function calcAge(doj) {{
  if(!doj) return '-';
  try {{
    const d = new Date(doj);
    if(isNaN(d.getTime())) return '-';
    const diffMs = Date.now() - d.getTime();
    if(diffMs < 0) return '-';
    const days = Math.floor(diffMs / 86400000);
    if(days < 30) return days + 'd';
    const months = Math.floor(days / 30.44);
    if(months < 12) return months + 'm';
    const years = Math.floor(months / 12);
    const remM  = months % 12;
    return years + 'y' + (remM ? ' ' + remM + 'm' : '');
  }} catch(e) {{ return '-'; }}
}}

let _aptSelCons = [];

function populateAptFilters() {{
  const tlSet  = new Set();
  const mgrMap = {{}};
  DATA.forEach(r => {{
    if(r.tl_name) tlSet.add(r.tl_name);
    if(r.mgr && r.mgr_name) mgrMap[r.mgr] = r.mgr_name;
  }});
  const tlSel = document.getElementById('apt-tl');
  tlSel.innerHTML = '<option value="all">All TLs</option>';
  [...tlSet].sort().forEach(t => {{
    const o = document.createElement('option'); o.value = t; o.textContent = t; tlSel.appendChild(o);
  }});
  const mgrSel = document.getElementById('apt-mgr');
  mgrSel.innerHTML = '<option value="all">All Managers</option>';
  Object.entries(mgrMap).sort((a,b) => a[1].localeCompare(b[1])).forEach(([alias, name]) => {{
    const o = document.createElement('option'); o.value = alias; o.textContent = name; mgrSel.appendChild(o);
  }});
  _refreshAptConsList();
}}

function _aptTypeChanged() {{
  _aptSelCons = [];
  _refreshAptConsList();
  renderAgentTable();
}}

function _refreshAptConsList() {{
  const type = document.getElementById('apt-type').value;
  const search = (document.getElementById('apt-cons-search') || {{}}).value || '';
  _populateAptConsPanel(type, search);
  _updateAptConsTriggerLabel();
}}

function _populateAptConsPanel(type, search) {{
  const scroll = document.getElementById('apt-cons-scroll');
  if(!scroll) return;
  const q = (search || '').toLowerCase();
  const names = new Set();
  DATA.forEach(r => {{
    if(!CONSULTANT_DESIGS.has(r.desig)) return;
    if(type === 'field' && r.is_ts) return;
    if(type === 'ts'    && !r.is_ts) return;
    if(r.name) names.add(r.name);
  }});
  scroll.innerHTML = '';
  [...names].sort().filter(n => !q || n.toLowerCase().includes(q)).forEach(name => {{
    const isChk = _aptSelCons.includes(name);
    const div = document.createElement('div');
    div.className = 'ov-mgr-item';
    div.innerHTML = `<div class="ov-mgr-cb${{isChk ? ' chk' : ''}}"></div><span class="ov-mgr-item-label">${{name}}</span>`;
    div.addEventListener('click', ev => {{ ev.stopPropagation(); _toggleAptCons(name); }});
    scroll.appendChild(div);
  }});
  if(!scroll.children.length) {{
    scroll.innerHTML = '<div style="padding:10px 12px;font-size:12px;color:var(--muted)">No consultants found</div>';
  }}
}}

function _toggleAptCons(name) {{
  if(_aptSelCons.includes(name)) {{
    _aptSelCons = _aptSelCons.filter(n => n !== name);
  }} else {{
    _aptSelCons = [..._aptSelCons, name];
  }}
  _refreshAptConsList();
  renderAgentTable();
}}

function _toggleAptConsPanel(e) {{
  e && e.stopPropagation();
  const panel   = document.getElementById('apt-cons-panel');
  const trigger = document.getElementById('apt-cons-trigger');
  if(panel.classList.contains('open')) {{
    panel.classList.remove('open'); trigger.classList.remove('open');
  }} else {{
    panel.classList.add('open'); trigger.classList.add('open');
    const inp = document.getElementById('apt-cons-search');
    if(inp) setTimeout(() => inp.focus(), 50);
    setTimeout(() => document.addEventListener('click', _closeAptConsPanelOutside, {{once:true}}), 0);
  }}
}}

function _closeAptConsPanelOutside(ev) {{
  const filter = document.getElementById('apt-cons-filter');
  if(filter && !filter.contains(ev.target)) {{
    document.getElementById('apt-cons-panel').classList.remove('open');
    document.getElementById('apt-cons-trigger').classList.remove('open');
  }}
}}

function _clearAptConsFilter(e) {{
  e && e.stopPropagation();
  _aptSelCons = [];
  const inp = document.getElementById('apt-cons-search');
  if(inp) inp.value = '';
  _refreshAptConsList();
  document.getElementById('apt-cons-panel').classList.remove('open');
  document.getElementById('apt-cons-trigger').classList.remove('open');
  renderAgentTable();
}}

function _onAptConsSearch() {{
  const type = document.getElementById('apt-type').value;
  const q    = document.getElementById('apt-cons-search').value;
  _populateAptConsPanel(type, q);
}}

function _updateAptConsTriggerLabel() {{
  const lbl = document.getElementById('apt-cons-trigger-label');
  if(!lbl) return;
  if(_aptSelCons.length === 0)      lbl.textContent = 'All Consultants';
  else if(_aptSelCons.length === 1) lbl.textContent = _aptSelCons[0];
  else                              lbl.textContent = _aptSelCons.length + ' consultants selected';
}}

function kpiColor(val, threshold) {{
  if(threshold === 0 || val === null || val === undefined || isNaN(+val)) return '';
  const diff  = val - threshold;
  const ratio = Math.abs(diff) / threshold;
  if(ratio <= 0.05) return 'color:#ca8a04;font-weight:700';
  const t = Math.min(1, (ratio - 0.05) / 0.45);
  const l = Math.round(42 - t * 18);
  if(diff > 0) return 'color:hsl(142,72%,' + l + '%) !important;font-weight:700';
  else         return 'color:hsl(0,72%,'   + l + '%) !important;font-weight:700';
}}

function renderAgentTable() {{
  const currMn = +document.getElementById('apt-month').value;
  const type   = document.getElementById('apt-type').value;
  const tlF    = document.getElementById('apt-tl').value;
  const mgrF   = document.getElementById('apt-mgr').value;
  if(currMn === '' || currMn === null || isNaN(currMn)) return;

  const prevMn = currMn - 1;
  const m3Mns  = [currMn-2, currMn-1, currMn].filter(m => m >= -2);

  const byKey = {{}};
  for(const r of DATA) {{
    if(!r.mgr) continue;
    if(type === 'field' && r.is_ts) continue;
    if(type === 'ts'    && !r.is_ts) continue;
    if(r.is_leader) continue;
    const key = r.email || r.name;
    if(!byKey[key]) byKey[key] = {{ recs: {{}} }};
    byKey[key].recs[r.month] = r;
    if(!byKey[key].latest || r.month >= byKey[key].latest.month) byKey[key].latest = r;
  }}

  const rows = [];
  for(const cons of Object.values(byKey)) {{
    const info = cons.latest;
    if(!info) continue;
    if(tlF  !== 'all' && (info.tl_name || '') !== tlF) continue;
    if(mgrF !== 'all' && info.mgr !== mgrF) continue;
    if(_aptSelCons.length > 0 && !_aptSelCons.includes(info.name)) continue;

    const curr     = cons.recs[currMn] || null;
    if(!curr || (curr.days === 0 && curr.calls === 0 && curr.coll === 0)) continue;
    const prev     = (cons.recs[prevMn] !== undefined) ? cons.recs[prevMn] : null;
    const hasPrev  = prev !== null;
    const currDays = curr ? curr.days : 0;
    const prevDays = prev ? prev.days : 0;

    const cUvm    = curr ? curr.uvm : 0;
    const pUvm    = hasPrev ? prev.uvm : null;
    const cVm     = curr ? curr.vm : 0;
    const pVm     = hasPrev ? prev.vm : null;
    const cAvgVm  = currDays>0 ? cVm/currDays : 0;
    const pAvgVm  = (hasPrev && prevDays>0) ? pVm/prevDays : null;
    const vmD     = (pAvgVm!==null && pAvgVm>0) ? (cAvgVm-pAvgVm)/pAvgVm*100 : null;

    const cUqc    = curr ? curr.uqc : 0;
    const pUqc    = hasPrev ? prev.uqc : null;
    const cQc     = curr ? curr.nqc : 0;
    const pQc     = hasPrev ? prev.nqc : null;
    const cAvgUqc = currDays>0 ? cUqc/currDays : 0;
    const pAvgUqc = (hasPrev && prevDays>0) ? pUqc/prevDays : null;
    const uqcD    = (pAvgUqc!==null && pAvgUqc>0) ? (cAvgUqc-pAvgUqc)/pAvgUqc*100 : null;

    const cDtt    = curr ? curr.dtt : 0;
    const pDtt    = hasPrev ? prev.dtt : null;
    const cAvgDtt = currDays>0 ? cDtt/currDays : 0;
    const pAvgDtt = (hasPrev && prevDays>0) ? pDtt/prevDays : null;
    const dttD    = (pAvgDtt!==null && pAvgDtt>0) ? (cAvgDtt-pAvgDtt)/pAvgDtt*100 : null;

    const cColl = curr ? curr.coll : 0;
    const m3C   = m3Mns.reduce((s,m) => {{ const rc=cons.recs[m]; return s+(rc?rc.coll:0); }}, 0) / 3;
    const tDate = Object.values(cons.recs).filter(rc => rc.month <= currMn).reduce((s,rc)=>s+rc.coll, 0);
    const cPkg  = curr ? curr.pkg : 0;
    const m3P   = m3Mns.reduce((s,m) => {{ const rc=cons.recs[m]; return s+(rc?rc.pkg:0); }}, 0) / 3;

    rows.push({{
      name: info.name, age: calcAge(info.doj), wdays: currDays,
      tl: info.tl_name || info.mgr_name || '-', mgr: info.mgr_name || '-',
      isTs: !!info.is_ts,
      pUvm, cUvm, pVm, cVm, pAvgVm, cAvgVm, vmD,
      pUqc, pAvgUqc, cUqc, cAvgUqc, pQc, cQc, pAvgDtt, cAvgDtt, uqcD, dttD,
      cColl, m3C, tDate, cPkg, m3P, _s: cColl
    }});
  }}

  rows.sort((a,b) => b._s - a._s);

  const mn = MONTH_NAMES[currMn] || '';

  const trendCell = (val, delta, bg, kpiStyle) => {{
    const sAttr = kpiStyle ? ' style="' + kpiStyle + '"' : '';
    if(delta === null) return '<td class="num ' + bg + '"' + sAttr + '>' + val + '</td>';
    const capped = Math.max(-100, Math.min(100, delta));
    const arrow  = delta >= 0 ? '\u2191' : '\u2193';
    const sign   = delta >= 0 ? '+' : '';
    const c      = delta >= 0 ? 'apt-delta-pos' : 'apt-delta-neg';
    const tip    = sign + capped.toFixed(1) + '%';
    return '<td class="num ' + bg + '"' + sAttr + '>' + val +
      '<span class="' + c + '" style="font-size:12px;margin-left:6px;cursor:help" title="' + tip + '">' +
      arrow + '</span></td>';
  }};

  const showMtg = (type !== 'ts');
  const totalCols = showMtg ? 20 : 16;
  const tblMinW   = showMtg ? '1600px' : '1150px';

  let tbl = '<table style="min-width:' + tblMinW + ';border-collapse:collapse"><thead>' +
    '<tr><th colspan="' + totalCols + '" style="text-align:left;padding:10px 14px;font-size:13px;font-weight:700;background:var(--accent-light,#eef2ff);color:var(--accent,#3b5bdb);border-bottom:1px solid var(--border);position:sticky;left:0;z-index:4">' +
    'Consultant Performance Metrics \u2014 ' + mn + ' \u2014 ' + rows.length + ' consultants</th></tr>' +
    '<tr>' +
    '<th rowspan="2" class="col-sticky-hd" style="width:130px;min-width:130px;max-width:130px;left:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">Name</th>' +
    '<th rowspan="2" class="col-sticky-hd" style="width:90px;min-width:90px;max-width:90px;left:130px">Working Days</th>' +
    '<th rowspan="2" class="col-sticky-hd" style="width:55px;min-width:55px;max-width:55px;left:220px">Age</th>' +
    '<th rowspan="2" class="col-sticky-hd" style="width:150px;min-width:150px;max-width:150px;left:275px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">Team Lead</th>' +
    '<th rowspan="2" class="col-sticky-hd col-sticky-last" style="width:150px;min-width:150px;max-width:150px;left:425px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">Manager</th>' +
    (showMtg ? '<th colspan="4" class="apt-group meetings-group">MEETINGS (Verified)</th>' : '') +
    '<th colspan="6" class="apt-group calls-group">CALLS</th>' +
    '<th colspan="5" class="apt-group coll-group">COLLECTION</th>' +
    '</tr><tr>' +
    (showMtg ? '<th class="num meetings-sub">Total/Uniq (Prev)</th><th class="num meetings-sub">Prev Avg/d</th><th class="num meetings-sub">Total/Uniq (Curr)</th><th class="num meetings-sub">Curr Avg/d</th>' : '') +
    '<th class="num calls-sub">Total/Uniq (Prev)</th>' +
    '<th class="num calls-sub">Prev Avg/d</th>' +
    '<th class="num calls-sub">Total/Uniq (Curr)</th>' +
    '<th class="num calls-sub">Curr Avg/d</th>' +
    '<th class="num calls-sub">Prev DTT/d</th>' +
    '<th class="num calls-sub">Curr DTT/d</th>' +
    '<th class="num coll-sub">' + mn + ' Coll</th>' +
    '<th class="num coll-sub">' + mn + ' Pkgs</th>' +
    '<th class="num coll-sub">3M Avg Coll</th>' +
    '<th class="num coll-sub">3M Avg Pkgs</th>' +
    '<th class="num coll-sub">Till Date</th>' +
    '</tr></thead><tbody>';

  if(!rows.length) {{
    tbl += '<tr><td colspan="' + totalCols + '" style="text-align:center;color:var(--muted);padding:24px">No data for this selection.</td></tr>';
  }} else {{
    for(const r of rows) {{
      const vmStyle  = r.isTs ? '' : kpiColor(r.cAvgVm,  3.5);
      const uqcStyle = kpiColor(r.cAvgUqc, r.isTs ? 25 : 12);
      const dttStyle = kpiColor(r.cAvgDtt, r.isTs ? 60 : 20);
      tbl +=
        '<tr>' +
        '<td class="td-name col-sticky" style="left:0;width:130px;min-width:130px;max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="' + r.name + '">' + r.name + '</td>' +
        '<td class="num col-sticky" style="left:130px;width:90px;min-width:90px;max-width:90px">' + r.wdays + '</td>' +
        '<td class="td-muted col-sticky" style="left:220px;width:55px;min-width:55px;max-width:55px;white-space:nowrap">' + r.age + '</td>' +
        '<td class="td-muted col-sticky" style="left:275px;width:150px;min-width:150px;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="' + r.tl + '">' + r.tl + '</td>' +
        '<td class="td-muted col-sticky col-sticky-last" style="left:425px;width:150px;min-width:150px;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="' + r.mgr + '">' + r.mgr + '</td>' +
        (showMtg ?
          '<td class="num meetings-sub">' + (r.pVm===null?'-':r.pVm + '/' + r.pUvm) + '</td>' +
          '<td class="num meetings-sub">' + (r.pAvgVm===null?'-':r.pAvgVm.toFixed(2)) + '</td>' +
          '<td class="num meetings-sub">' + (r.cVm + '/' + r.cUvm) + '</td>' +
          trendCell(r.cAvgVm.toFixed(2), r.vmD, 'meetings-sub', vmStyle)
        : '') +
        '<td class="num calls-sub">' + (r.pUqc===null?'-':r.pQc + '/' + r.pUqc) + '</td>' +
        '<td class="num calls-sub">' + (r.pAvgUqc===null?'-':r.pAvgUqc.toFixed(1)) + '</td>' +
        '<td class="num calls-sub">' + (r.cQc + '/' + r.cUqc) + '</td>' +
        trendCell(r.cAvgUqc.toFixed(1), r.uqcD, 'calls-sub', uqcStyle) +
        '<td class="num calls-sub">' + (r.pAvgDtt===null?'-':r.pAvgDtt.toFixed(1)+'m') + '</td>' +
        trendCell(r.cAvgDtt.toFixed(1)+'m', r.dttD, 'calls-sub', dttStyle) +
        '<td class="num coll-sub">' + fmt(r.cColl) + '</td>' +
        '<td class="num coll-sub">' + r.cPkg + '</td>' +
        '<td class="num coll-sub">' + fmt(r.m3C) + '</td>' +
        '<td class="num coll-sub">' + r.m3P.toFixed(1) + '</td>' +
        '<td class="num coll-sub">' + fmt(r.tDate) + '</td>' +
        '</tr>';
    }}
  }}

  tbl += '</tbody></table>';
  document.getElementById('ov-agent-table').innerHTML = tbl;
}}

// ── View switcher ──
function switchView(view) {{
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  const el = document.getElementById('v-' + view);
  if(el) el.classList.add('active');
  const tab = document.querySelector('.nav-tab[data-view="' + view + '"]');
  if(tab) tab.classList.add('active');
}}

// ── Chart theme colour variables ──
let _gc = '#f0ede6';
let _bc = '#e5e1d8';
let _tc = '#8f8b80';

function _applyChartTheme(dark) {{
  _gc = dark ? 'rgba(255,255,255,0.07)' : '#f0ede6';
  _bc = dark ? 'rgba(255,255,255,0.12)' : '#e5e1d8';
  _tc = dark ? '#5e8272'                : '#8f8b80';
}}

function toggleDarkMode(on) {{
  document.body.classList.toggle('dark', on);
  const lbl = document.getElementById('dark-toggle-lbl');
  if(lbl) lbl.textContent = on ? '\u263D Dark' : '\u2600 Light';
  _applyChartTheme(on);
  try {{ localStorage.setItem('cfd-theme', on ? 'dark' : 'light'); }} catch(e) {{}}
  render();
}}
(function _restoreTheme() {{
  try {{
    if(localStorage.getItem('cfd-theme') === 'dark') {{
      document.body.classList.add('dark');
      _applyChartTheme(true);
      const tog = document.getElementById('dark-toggle');
      if(tog) tog.checked = true;
      const lbl = document.getElementById('dark-toggle-lbl');
      if(lbl) lbl.textContent = '\u263D Dark';
    }}
  }} catch(e) {{}}
}})();

function _isAnyFilterActive() {{
  const month  = document.getElementById('f-month').value;
  const type   = document.getElementById('f-type').value;
  const region = document.getElementById('f-region').value;
  return month !== '0' || type !== 'all' || region !== 'all' ||
         _dateFrom || _dateTo || _selTls.length > 0 || _selMgrs.length > 0;
}}

function _syncResetBtn() {{
  const btn = document.getElementById('ov-reset-btn');
  if(btn) btn.style.display = _isAnyFilterActive() ? '' : 'none';
}}

// ── MTD normalisation toggles (independent per chart) ────────────────────────
let _mtdModeColl = false;   // cash collection chart
let _mtdModeProd = false;   // employee productivity chart
// Returns remaining working days in current month — the MTD anchor
function _getMtdDays() {{
  return REMAINING_WD;
}}
// For past months: scale to (total_wd_in_month - remainingDays) elapsed days
function _mtdColl(pool, remainingDays, mn) {{
  const latestMn = Math.max(..._viewMths);
  if(!_mtdModeColl || mn === latestMn) return pool.reduce((s,r) => s + r.coll, 0);
  const scaleDays = (WORKING_DAYS_PER_MONTH[String(mn)] || 0) - remainingDays;
  if(scaleDays <= 0) return pool.reduce((s,r) => s + r.coll, 0);
  return pool.filter(r => r.days > 0).reduce((s,r) => s + (r.coll / r.days) * scaleDays, 0);
}}
function _mtdPkg(pool, remainingDays, mn) {{
  const latestMn = Math.max(..._viewMths);
  if(!_mtdModeProd || mn === latestMn) return pool.reduce((s,r) => s + r.pkg, 0);
  const scaleDays = (WORKING_DAYS_PER_MONTH[String(mn)] || 0) - remainingDays;
  if(scaleDays <= 0) return pool.reduce((s,r) => s + r.pkg, 0);
  return pool.filter(r => r.days > 0).reduce((s,r) => s + (r.pkg / r.days) * scaleDays, 0);
}}
function _mtdCollProd(pool, remainingDays, mn) {{
  const latestMn = Math.max(..._viewMths);
  if(!_mtdModeProd || mn === latestMn) return pool.reduce((s,r) => s + r.coll, 0);
  const scaleDays = (WORKING_DAYS_PER_MONTH[String(mn)] || 0) - remainingDays;
  if(scaleDays <= 0) return pool.reduce((s,r) => s + r.coll, 0);
  return pool.filter(r => r.days > 0).reduce((s,r) => s + (r.coll / r.days) * scaleDays, 0);
}}
function _setMtdBtn(btn, active, remainingDays) {{
  btn.style.background  = active ? '#0d9488'   : 'transparent';
  btn.style.color       = active ? '#fff'       : '#8f8b80';
  btn.style.borderColor = active ? '#0d9488'    : '#e5e1d8';
  btn.textContent       = active ? `MTD (${{remainingDays}}d left)` : 'MTD';
}}
function _toggleMtdColl() {{
  _mtdModeColl = !_mtdModeColl;
  _setMtdBtn(document.getElementById('btn-mtd-coll'), _mtdModeColl, _getMtdDays());
  const type   = document.getElementById('f-type').value;
  const region = document.getElementById('f-region').value;
  renderTrendMonthly(type, region);
}}
function _toggleMtdProd() {{
  _mtdModeProd = !_mtdModeProd;
  _setMtdBtn(document.getElementById('btn-mtd-prod'), _mtdModeProd, _getMtdDays());
  const type   = document.getElementById('f-type').value;
  const region = document.getElementById('f-region').value;
  const month  = +document.getElementById('f-month').value;
  renderEmpProdChart(type, region, month);
}}
// Sum DAILY_COLL for month mn, excluding the last remainingDays working-day entries
function _collUpToDay(mn, remainingDays, type) {{
  const calMo  = String(mn).padStart(2, '0');
  const prefix = '2026-' + calMo + '-';
  const dayKeys = Object.keys(DAILY_COLL).filter(d => d.startsWith(prefix)).sort();
  const cutKeys = remainingDays > 0 ? dayKeys.slice(0, dayKeys.length - remainingDays) : dayKeys;
  const fieldTs = cutKeys.reduce((s, d) => {{
    const dc = DAILY_COLL[d] || {{}};
    if(type === 'ts')    return s + (dc.ts    || 0);
    if(type === 'field') return s + (dc.field || 0);
    return s + (dc.ts || 0) + (dc.field || 0);
  }}, 0);
  if(type !== 'all') return fieldTs;
  // Add online for 'all': slice by same date range as cutKeys
  const cutEnd = cutKeys.length ? cutKeys[cutKeys.length - 1] : '';
  const onlineTotal = Object.keys(ONLINE_COLL_DAILY)
    .filter(d => d.startsWith(prefix) && (!cutEnd || d <= cutEnd))
    .reduce((s, d) => s + (ONLINE_COLL_DAILY[d] || 0), 0);
  return fieldTs + onlineTotal;
}}

function resetAllFilters() {{
  document.getElementById('f-month').value  = '0';
  document.getElementById('f-type').value   = 'all';
  document.getElementById('f-region').value = 'all';
  _dateFrom = ''; _dateTo = '';
  document.getElementById('f-date-from').value = '';
  document.getElementById('f-date-to').value   = '';
  document.getElementById('ov-date-clear-btn').style.display = 'none';
  _selTls = [];
  document.getElementById('ov-tl-trigger-label').textContent = 'All Team Leads';
  document.getElementById('ov-tl-panel').classList.remove('open');
  document.getElementById('ov-tl-trigger').classList.remove('open');
  _selMgrs = [];
  document.getElementById('ov-mgr-trigger-label').textContent = 'All Managers';
  document.getElementById('ov-mgr-panel').classList.remove('open');
  document.getElementById('ov-mgr-trigger').classList.remove('open');
  _ovDrillMonth = 0;
  _ovDrillMgr   = '';
  _ovDrillTl    = '';
  _drillMonthImplicit = false;
  if(typeof _discClientType !== 'undefined') {{
    _discClientType = 'all';
    ['all','new','renewal'].forEach(t => {{
      const btn = document.getElementById('disc-ct-' + t);
      if(!btn) return;
      btn.style.background  = t === 'all' ? '#1b1a17' : '';
      btn.style.color       = t === 'all' ? '#f7f6f2' : '#8f8b80';
      btn.style.borderColor = t === 'all' ? '#1b1a17' : '#e5e1d8';
    }});
  }}
  if(typeof _discPkgSel !== 'undefined') _discPkgSel = new Set();
  document.getElementById('ov-reset-btn').style.display = 'none';
  render();
}}

// ============ INIT ============
(function init() {{
  populateAptFilters();
  renderAgentTable();
  render();
  _populateTlPanel();
  _populateMgrPanel();
}})();
</script>
</body>
</html>'''

with open('C:/Users/hamza.rizwan/CFD_Sales_Dashboard_2026.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Dashboard saved: {len(html)/1024:.0f}KB")
