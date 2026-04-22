"""
Generate CFD Sales Dashboard HTML with embedded data.
Reads from the latest sales_consultants CSV and produces a self-contained HTML dashboard.
"""
import json, math
import pandas as pd
from datetime import date
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
  --bg:#f5f7fc;--card:#ffffff;--card2:#eef1f8;--border:#dde3ef;
  --text:#0f172a;--muted:#64748b;--accent:#3b50d1;--accent2:#2d40b8;
  --green:#15803d;--red:#b91c1c;--amber:#c2610c;--blue:#1d4ed8;--teal:#0d9488;
  --shadow-sm:0 1px 3px rgba(15,23,42,0.07),0 1px 2px rgba(15,23,42,0.04);
  --shadow-md:0 4px 16px rgba(15,23,42,0.09),0 2px 6px rgba(15,23,42,0.05);
  --shadow-lg:0 8px 32px rgba(15,23,42,0.10),0 4px 12px rgba(15,23,42,0.05);
  --radius:12px;
}}
body{{background:var(--bg);color:var(--text);font-family:'Inter','Segoe UI',system-ui,sans-serif;font-size:13.5px;min-height:100vh;-webkit-font-smoothing:antialiased;line-height:1.5}}
.nav{{background:#fff;border-bottom:1px solid var(--border);box-shadow:0 2px 16px rgba(15,23,42,0.06);padding:0 32px;display:flex;align-items:center;gap:0;position:sticky;top:0;z-index:100}}
.nav-brand{{font-size:15px;font-weight:800;color:#0f172a;padding:16px 0;margin-right:40px;white-space:nowrap;letter-spacing:-0.03em}}
.nav-brand span{{color:var(--accent);font-weight:500;letter-spacing:-0.01em}}
.nav-tab{{padding:18px 20px;font-size:12.5px;font-weight:500;color:var(--muted);cursor:pointer;border-bottom:2.5px solid transparent;transition:all .2s;white-space:nowrap}}
.nav-tab:hover{{color:var(--text)}}
.nav-tab.active{{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}}
.view{{display:none;padding:28px 32px}}
.view.active{{display:block}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:14px;margin-bottom:24px}}
.kpi-card{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px;border-top:3px solid transparent;box-shadow:var(--shadow-sm);transition:box-shadow .2s,transform .2s}}
.kpi-card:hover{{box-shadow:var(--shadow-md);transform:translateY(-1px)}}
.kpi-card.highlight{{border-top-color:var(--accent);background:linear-gradient(160deg,#f0f2ff 0%,#fff 70%)}}
.kpi-label{{font-size:10.5px;color:var(--muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:.06em;font-weight:600}}
.kpi-val{{font-size:25px;font-weight:700;line-height:1;letter-spacing:-0.02em}}
.kpi-sub{{font-size:11.5px;color:var(--muted);margin-top:5px}}
.sec-header{{display:flex;align-items:center;gap:10px;margin-bottom:14px;margin-top:28px;padding-left:12px;border-left:3px solid var(--accent)}}
.sec-title{{font-size:14px;font-weight:700;letter-spacing:-0.01em}}
.sec-badge{{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600}}
.hard-badge{{background:#e8eaf6;color:#3949ab;border:1px solid #c5cae9}}
.soft-badge{{background:#e0f2f1;color:#00695c;border:1px solid #b2dfdb}}
.filter-bar{{background:#fff;border:1px solid var(--border);border-radius:var(--radius);padding:16px 20px;margin-bottom:22px;display:flex;flex-wrap:wrap;gap:18px;align-items:flex-end;box-shadow:var(--shadow-sm)}}
.filter-group{{display:flex;flex-direction:column;gap:5px}}
.filter-label{{font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:700}}
select{{background:#fff;border:1.5px solid var(--border);color:var(--text);padding:8px 12px;border-radius:8px;font-size:12.5px;cursor:pointer;min-width:145px;font-family:inherit;font-weight:500;transition:border-color .15s,box-shadow .15s}}
select:focus{{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(59,80,209,0.1)}}
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
.pill-exc{{background:#dcfce7;color:#14532d}}.pill-vg{{background:#dbeafe;color:#1e3a8a}}
.pill-good{{background:#ccfbf1;color:#134e4a}}.pill-above{{background:#e0e7ff;color:#3730a3}}
.pill-avg{{background:#fef3c7;color:#92400e}}.pill-below{{background:#fce7f3;color:#831843}}
.pill-poor{{background:#fee2e2;color:#7f1d1d}}.pill-active{{background:#dcfce7;color:#14532d;font-size:10px}}
.pill-inactive{{background:#fee2e2;color:#7f1d1d;font-size:10px}}
.pill-field{{background:#e0e7ff;color:#3730a3;font-size:10px}}.pill-ts{{background:#ccfbf1;color:#134e4a;font-size:10px}}
.tbl-wrap{{overflow-x:auto;border:1px solid var(--border);border-radius:var(--radius);max-height:600px;overflow-y:auto;box-shadow:var(--shadow-sm)}}
/* Report Cards */
.rc-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px;margin-bottom:26px}}
.rc-grid-wide{{display:grid;grid-template-columns:repeat(auto-fill,minmax(700px,1fr));gap:18px;margin-bottom:26px}}
.rc-scroll-row{{display:flex;gap:16px;overflow-x:auto;padding-bottom:10px;margin-bottom:22px;align-items:start}}
.rc-scroll-row .rc-card{{min-width:260px;max-width:280px;flex-shrink:0}}
.rc-card{{background:#fff;border:1px solid var(--border);border-radius:var(--radius);padding:20px;transition:box-shadow .2s,transform .15s;position:relative;box-shadow:var(--shadow-sm)}}
.rc-card:hover{{box-shadow:var(--shadow-md);transform:translateY(-2px)}}
.rc-card-header{{display:flex;align-items:center;gap:8px;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--border);position:relative}}
.rc-card-title{{font-size:13.5px;font-weight:700;color:var(--text)}}
.rc-card-subtitle{{font-size:10.5px;color:var(--muted)}}
.rc-row{{display:flex;justify-content:space-between;padding:4px 0;font-size:12.5px}}
.rc-row-label{{color:var(--muted)}}
.rc-row-val{{font-weight:600}}
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
.tl-branch-btn:hover{{border-color:var(--accent);background:#eef0fd;box-shadow:var(--shadow-md)}}
.tl-branch-btn.active{{border-color:var(--accent);background:var(--accent);color:#fff;box-shadow:0 4px 18px rgba(59,80,209,0.38)}}
.tl-branch-btn .tl-cash{{font-size:11px;color:var(--muted);font-weight:500}}
.tl-branch-btn.active .tl-cash{{color:rgba(255,255,255,0.8)}}
.tl-min-btn{{width:22px;height:22px;border-radius:50%;border:1.5px solid var(--border);background:var(--bg);color:var(--muted);font-size:14px;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .15s;padding:0;flex-shrink:0}}
.tl-min-btn:hover{{border-color:var(--accent);color:var(--accent);background:#eef0fd}}
.mgr-direct-card{{border:2px solid #059669!important;}}
.mgr-direct-card .rc-card-title{{color:#059669}}
.mgr-direct-card .rc-section-title{{color:#059669}}
.mgr-tl-connector{{flex:0 0 40px;display:flex;align-items:center;justify-content:center}}
.mgr-tl-connector-line{{width:100%;height:2px;background:var(--accent);position:relative}}
.mgr-tl-connector-line::before,.mgr-tl-connector-line::after{{content:'';position:absolute;top:50%;transform:translateY(-50%);width:7px;height:7px;border-radius:50%;background:var(--accent)}}
.mgr-tl-connector-line::before{{left:0}}
.mgr-tl-connector-line::after{{right:0}}
.mgr-tl-card{{border:2px solid var(--accent)!important;box-shadow:0 4px 20px rgba(59,80,209,0.13)!important;animation:slideIn .2s ease}}
@keyframes slideIn{{from{{opacity:0;transform:translateY(-8px)}}to{{opacity:1;transform:translateY(0)}}}}
table{{width:100%;border-collapse:collapse;font-size:12.5px;white-space:nowrap}}
thead th{{background:#1e293b;color:#94a3b8;padding:10px 13px;text-align:left;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;border-bottom:none;position:sticky;top:0;z-index:1}}
tbody tr{{border-bottom:1px solid #f0f3f8}}
tbody tr:hover{{background:#f8fafd}}
tbody td{{padding:9px 13px;vertical-align:middle}}
.num{{text-align:right}}.pos{{color:#15803d}}.neg{{color:#b91c1c}}
.th-hard{{background:#1e3a5f !important;color:#93c5fd !important}}.th-soft{{background:#064e3b !important;color:#6ee7b7 !important}}
.mgr-card{{background:#fff;border:1px solid var(--border);border-radius:var(--radius);padding:22px;margin-bottom:22px;box-shadow:var(--shadow-sm)}}
.mgr-card h3{{font-size:17px;margin-bottom:4px;font-weight:700;letter-spacing:-0.01em}}.mgr-card .subtitle{{color:var(--muted);font-size:12.5px}}
/* ── Overview drill-down ── */
.ov-drill-wrap{{cursor:pointer;display:block}}
.ov-drill-wrap:hover .rc-card{{box-shadow:var(--shadow-md);border-color:var(--accent);transform:translateY(-2px);transition:all .15s}}
.ov-breadcrumb{{display:none;align-items:center;gap:10px;margin-bottom:18px;padding:10px 16px;background:#fff;border:1px solid var(--border);border-radius:var(--radius);font-size:12px;box-shadow:var(--shadow-sm)}}
.ov-back-btn{{background:none;border:1.5px solid var(--border);border-radius:7px;padding:5px 12px;font-size:11.5px;font-weight:600;color:var(--muted);cursor:pointer;transition:all .15s;display:flex;align-items:center;gap:5px;font-family:inherit}}
.ov-back-btn:hover{{border-color:var(--accent);color:var(--accent);background:#eef0fd}}
.ov-bc-sep{{color:var(--border);font-size:14px}}
.ov-bc-item{{color:var(--muted)}}
.ov-bc-item.active{{color:var(--text);font-weight:700}}
.ov-drill-hint{{font-size:9px;color:var(--accent);text-transform:uppercase;letter-spacing:.08em;margin-top:4px;font-weight:700;opacity:.7}}
/* ── Agent Performance Table ── */
.apt-group{{text-align:center;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;padding:7px 4px;border-left:2px solid rgba(255,255,255,0.12)}}
.meetings-group{{background:#065f46;color:#a7f3d0}}.calls-group{{background:#1e3a5f;color:#93c5fd}}.coll-group{{background:#78350f;color:#fde68a}}
.meetings-sub{{background:#f0fdf4!important;color:#14532d}}.calls-sub{{background:#eff6ff!important;color:#1e3a8a}}.coll-sub{{background:#fffbeb!important;color:#78350f}}
.apt-delta-pos{{color:#15803d;font-weight:700}}.apt-delta-neg{{color:#b91c1c;font-weight:700}}.apt-delta-na{{color:var(--muted)}}
</style>
</head>
<body>

<div class="nav">
  <div class="nav-brand">CFD <span>Sales Dashboard</span></div>
  <div class="nav-tab active">Overview</div>
  <div style="margin-left:auto;display:flex;align-items:center;gap:8px;padding:0 4px">
    <span style="font-size:11px;color:var(--muted);font-weight:500;letter-spacing:0.01em">Data as of</span>
    <span style="font-size:11px;font-weight:700;color:var(--text);background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:3px 9px;letter-spacing:0.01em">{_today.strftime('%d %b %Y')}</span>
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
      <div class="filter-label">Team Type</div>
      <select id="f-type" onchange="render()">
        <option value="all">All</option>
        <option value="field">Field Sales</option>
        <option value="ts">Telesales</option>
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
  </div>

  <!-- Drill-down breadcrumb (hidden at top level) -->
  <div id="ov-breadcrumb" class="ov-breadcrumb">
    <button class="ov-back-btn" onclick="backOv()">&#8592; Back</button>
    <span class="ov-bc-sep">/</span>
    <span id="ov-bc-month" class="ov-bc-item"></span>
    <span id="ov-bc-sep2" class="ov-bc-sep" style="display:none">/</span>
    <span id="ov-bc-mgr" class="ov-bc-item active" style="display:none"></span>
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
      <div class="chart-title" id="ov-trend-title">Collections Trend</div>
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

  <!-- Row: Renewals | Employee Productivity -->
  <div style="display:flex;gap:16px;margin-bottom:20px;align-items:stretch">
    <!-- Renewals trend -->
    <div class="chart-card" id="ov-renewals-chart" style="flex:1;min-width:0;font-family:'Geist Mono',monospace">
      <div class="chart-title" style="margin-bottom:16px">Renewals — Monthly Trend</div>
      <div style="position:relative;height:320px">
        <canvas id="chart-renewals"></canvas>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:12px 28px;align-items:center;margin-top:14px;padding-top:12px;border-top:1px solid #e5e1d8;font-size:0.7rem;color:#8f8b80">
        <div style="display:flex;align-items:center;gap:6px">
          <span style="width:11px;height:11px;border-radius:2px;background:#2a9d6f;flex-shrink:0"></span>
          Renewed Clients
        </div>
        <div style="display:flex;align-items:center;gap:6px">
          <span style="width:11px;height:11px;border-radius:2px;background:#e8a838;flex-shrink:0"></span>
          Pending Renewals
        </div>
        <div style="display:flex;align-items:center;gap:6px">
          <span style="width:20px;height:2px;background:#1b1a17;flex-shrink:0;position:relative;display:inline-block">
            <span style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:7px;height:7px;border-radius:50%;background:#1b1a17;border:2px solid #fff;display:block"></span>
          </span>
          Renewal Rate % (right axis)
        </div>
        <div style="margin-left:auto;display:flex;align-items:center;gap:5px;font-size:0.62rem;color:#b0aa9e">
          <span style="width:14px;height:5px;border-radius:2px;background:#1b1a17;opacity:.12;display:inline-block"></span>
          Avg rate band shown
        </div>
      </div>
    </div>

    <!-- Employee Productivity -->
    <div class="chart-card" style="flex:1;min-width:0;font-family:'Geist Mono',monospace">
      <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:16px">
        <div class="chart-title">Employee Productivity — Monthly Trend</div>
        <div style="font-size:0.62rem;color:#8f8b80;letter-spacing:0.06em;text-transform:uppercase;line-height:1.6;text-align:right">Per BOM headcount</div>
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
  <div id="ov-soft-kpi-trends" style="display:none;margin-bottom:20px"></div>

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
        <select id="apt-type" onchange="renderAgentTable()">
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
const PKG_MIX = {_pkg_mix_json};

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

const MONTH_NAMES = {{{_month_names_js}}};

const MGR_TEAMS = {{
  'Alaa - JM1':['Alaa - JM1'],
  'El-Kallas - M4':['El-Kallas - M4','Rola - TL Riyadh'],
  'Mohammed Abdelkader - Eastern':['Mohammed Abdelkader - Eastern','Kareem - TL Eastern'],
  'Reham AL Harbi - M2':['Reham AL Harbi - M2','Aminah - TL Riyadh'],
  'Mohamad Ghannoum - JM3':['Mohamad Ghannoum - JM3','Khalil - TL Jeddah','Othman - TL Medina'],
  'Mohamed Abdullah - M3':['Mohamed Abdullah - M3','AlHourani - TL Riyadh'],
  'AbdulMajed - TL Riyadh':['AbdulMajed - TL Riyadh','Al Khateeb - TL Riyadh'],
  'Telesales - Sulaiman Aljurbua':['Telesales - Sulaiman Aljurbua','Telesales Manager','Telesales-Abdelfattah Khaiyal','Telesales - Abdullah Altamimi'],
  'Hussain - TL PK':['Hussain - TL PK'],
  'Mohsin - TL PK':['Mohsin - TL PK'],
}};

const MGR_NAMES = {{
  'Alaa - JM1':'Alaa Alsaber','El-Kallas - M4':'Mohammad El-Kallas',
  'Mohammed Abdelkader - Eastern':'Mohammed Abdelkader','Reham AL Harbi - M2':'Reham AL Harbi',
  'Mohamad Ghannoum - JM3':'Mohamad Ghannoum','Mohamed Abdullah - M3':'Mohamed Abdullah',
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
function pct(a,b){{ return b>0 ? (a/b*100).toFixed(1)+'%' : '-'; }}

function tvaRating(v){{ if(v>=1) return 'Excellent'; if(v>=0.75) return 'Good'; if(v>=0.5) return 'Average'; return 'Poor'; }}
function tvaColor(v){{ if(v>=1) return 'pill-exc'; if(v>=0.75) return 'pill-good'; if(v>=0.5) return 'pill-avg'; return 'pill-poor'; }}

function kpiCard(label, val, sub, regHtml){{ return `<div class="kpi-card"><div class="kpi-label">${{label}}</div><div class="kpi-val">${{val}}</div>${{sub?`<div class="kpi-sub">${{sub}}</div>`:''}}` + (regHtml||'') + '</div>'; }}
function softCard(label, val, sub, regHtml){{ return `<div class="soft-kpi-card"><div class="kpi-label">${{label}}</div><div class="kpi-val">${{val}}</div>${{sub?`<div class="kpi-sub">${{sub}}</div>`:''}}` + (regHtml||'') + '</div>'; }}



function reportCard(title, subtitle, m, isTS, tlBreakdown, extraClass, hideRoster, horizontal, headerExtra='', revenue=null) {{
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
    ${{revenue !== null ? rc('Deferred Revenue', fmt(revenue), 'Pro-rata revenue from verified active contracts in this period (SAR)') : ''}}
    ${{rc('Cash / Employee', m.bom>0 ? fmt(m.cash/m.bom) : '-', 'Cash collection divided by BOM headcount (SAR per head)')}}
    ${{rc('Packages Sold', m.pkgSold, 'New contracts signed this period (excludes revivals and promo packages)')}}
    ${{rc('Avg Discount', m.avgDisc>0 ? pctPill(Math.round(m.avgDisc*100)+'%', discColor(Math.round(m.avgDisc*100))) : '-', 'Avg discount % = sum of discount values / sum of contract values, for staff who sold packages')}}
    ${{rc('Net Client Gain', Math.round(m.netGain), 'Active clients at end of month minus active clients at start of month')}}
    ${{tlSection}}`; // used for vertical layout only
  const teamSection = `
    <div class="rc-section-title">Team</div>
    ${{hideRoster ? '' : rc('Active (EOM)', m.active, 'Clients assigned to the team at end of month with Active CRM status')}}
    ${{hideRoster ? '' : rc('BOM (Target>0)', m.bom, 'Staff counted in the team with a collection target > 0 (measured after the 6th of the month)')}}
    ${{rc('Productive Team (>=4K)', m.productive+' '+( m.bom>0 ? pctPill(Math.round(m.productivity)+'%', prodColor(Math.round(m.productivity))) : '' ), 'Consultants who collected >= SAR 4,000 this period. % = productive / BOM')}}
    ${{rc('Coverage %', pctPill(Math.round(m.covPct)+'%', covColor(Math.round(m.covPct))), 'Clients contacted (at least 1 qualified call) / total assigned clients x 100')}}
    ${{rc('Renewed / Pending', m.renewed+' / '+m.pendRen, 'Renewed: clients who signed a new contract this month. Pending: clients with a contract expiring this month who have not yet renewed')}}`;
  const activitySection = horizontal
    ? `<div class="rc-section-title">Activity (Avg / Day)</div>
    ${{rc('UQC / Day', m.avgUqc.toFixed(1), 'Unique Qualified Calls per working day (avg)', 'Total this period: '+m.totalUqc.toLocaleString()+' UQC')}}
    ${{rc('DTT / Day', m.avgDtt.toFixed(1)+' mins', 'Daily Talk Time per working day in minutes (avg)', 'Total this period: '+fmt(m.totalDtt)+' min')}}
    ${{isTS ? '' : rc('VM / Day', m.avgVm!==null ? m.avgVm.toFixed(1) : 'N/A', 'Verified in-person meetings per working day (avg)', m.avgVm!==null ? 'Total this period: '+m.totalUvm.toLocaleString()+' meetings' : '') }}`
    : `<div class="rc-section-title">Activity (Avg/Day)</div>
    ${{rc('UQC / Day', m.avgUqc.toFixed(1), 'Unique Qualified Calls per working day (avg)', 'Total this period: '+m.totalUqc.toLocaleString()+' UQC')}}
    ${{rc('DTT / Day', m.avgDtt.toFixed(1)+' min', 'Daily Talk Time per working day in minutes (avg)', 'Total this period: '+fmt(m.totalDtt)+' min')}}
    ${{isTS ? '' : rc('VM / Day', m.avgVm!==null ? m.avgVm.toFixed(1) : 'N/A', 'Verified in-person meetings per working day (avg)', m.avgVm!==null ? 'Total this period: '+m.totalUvm.toLocaleString()+' meetings' : '')}}
    ${{rc('Total UQC', m.totalUqc.toLocaleString(), 'Total unique qualified calls made this period')}}
    ${{rc('Total DTT', fmt(m.totalDtt)+' min', 'Total daily talk time accumulated this period (minutes)')}}
    ${{isTS ? '' : rc('Total UVM', m.totalUvm.toLocaleString(), 'Total verified in-person meetings this period')}}`;
  const bodyHtml = horizontal
    ? `<div style="display:flex;gap:0;align-items:stretch;margin-top:10px">
        <div style="flex:1;display:flex;flex-direction:column;justify-content:space-between">
          ${{financialSection}}
        </div>
        <div style="flex:1;border-left:1px dashed var(--border);padding-left:14px;margin-left:14px">
          ${{teamSection}}
          <div style="margin-top:10px;padding-top:8px;border-top:1px dashed var(--border)">${{activitySection}}</div>
        </div>
       </div>`
    : `${{financialSection}}
       <div class="rc-section">${{teamSection}}</div>
       <div class="rc-section">${{activitySection}}</div>`;
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
  const vmPool = members.filter(r => r.uvm > 0 && r.days > 0 && !r.is_ts);
  const avgUqc = uqcPool.length > 0 ? uqcPool.reduce((s,r) => s + r.uqc/r.days, 0)/uqcPool.length : 0;
  const avgDtt = dttPool.length > 0 ? dttPool.reduce((s,r) => s + r.dtt/r.days, 0)/dttPool.length : 0;
  const avgVm = vmPool.length > 0 ? vmPool.reduce((s,r) => s + r.uvm/r.days, 0)/vmPool.length : null;

  // Totals — full pool (including leaders)
  const totalUqc = pool.reduce((s,r) => s+r.uqc, 0);
  const totalDtt = pool.reduce((s,r) => s+r.dtt, 0);
  const totalUvm = pool.reduce((s,r) => s+r.uvm, 0);

  return {{ active:active.length, bom:withTarget.length, productive:productive.length,
    cash, target, tva, pkgSold, avgDisc, netGain, cov, assigned, renewed, pendRen, renRate,
    avgUqc, avgDtt, avgVm, totalUqc, totalDtt, totalUvm, poolSize:pool.length,
    membersCount:members.length,
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

function drillOvMonth(mn) {{
  _ovDrillMonth = mn;
  _ovDrillMgr   = '';
  render();
}}

function drillOvMgr(mg) {{
  _ovDrillMgr = mg;
  render();
}}

function backOv() {{
  if(_ovDrillMgr !== '') {{
    _ovDrillMgr = '';
  }} else {{
    _ovDrillMonth = 0;
  }}
  render();
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
          ticks: {{color:'#8f8b80', font:{{size:12}}, maxRotation:0}},
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
let _discPkgSel = null;   // persists across contract-type switches

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
          filter: item => _discPkgSel === null || cats[item.datasetIndex].name === _discPkgSel,
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
          border: {{ color: '#e5e1d8' }},
          ticks: {{ color: '#8f8b80', font: {{ family: "'Geist Mono', monospace", size: 11 }}, maxRotation: 0 }}
        }},
        y: {{
          grid: {{ color: '#f0ede6' }},
          border: {{ color: '#e5e1d8' }},
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

  function applyDiscSelection(name) {{
    _discPkgSel = name;
    cats.forEach((c, j) => {{
      const active = (name === null || c.name === name);
      discTrendChart.data.datasets[j].borderColor          = active ? c.color : c.color + '1a';
      discTrendChart.data.datasets[j].pointBorderColor     = active ? c.color : c.color + '1a';
      discTrendChart.data.datasets[j].pointBackgroundColor = active ? '#ffffff' : c.color + '1a';
      discTrendChart.data.datasets[j].borderWidth          = active && name !== null ? 3 : (active ? 2.5 : 1);
      discTrendChart.data.datasets[j].pointRadius          = active && name !== null ? 6 : (active ? 5 : 2);
    }});
    discTrendChart.update('none');

    // sync pill styles
    Array.from(pillsEl.children).forEach(el => {{
      const isAll  = el.dataset.pkg === '__all__';
      const active = (name === null && isAll) || el.dataset.pkg === name;
      const cat    = cats.find(c => c.name === el.dataset.pkg);
      if(isAll) {{
        el.style.background  = name === null ? '#1b1a17' : '';
        el.style.color       = name === null ? '#f7f6f2' : '#8f8b80';
        el.style.borderColor = name === null ? '#1b1a17' : '#e5e1d8';
      }} else {{
        el.style.background  = active ? cat.color : '';
        el.style.color       = active ? '#fff'     : '#8f8b80';
        el.style.borderColor = active ? cat.color  : '#e5e1d8';
      }}
    }});

    // sync legend styles
    Array.from(legendEl.children).forEach((el, j) => {{
      el.style.opacity = (name === null || cats[j].name === name) ? '1' : '0.25';
    }});
  }}

  // "All" pill
  const allPill = document.createElement('button');
  allPill.dataset.pkg = '__all__';
  allPill.textContent = 'All';
  allPill.style.cssText = 'font-family:inherit;font-size:0.68rem;font-weight:600;padding:3px 12px;border-radius:20px;border:1px solid #1b1a17;background:#1b1a17;color:#f7f6f2;cursor:pointer;transition:all 0.15s;letter-spacing:0.04em';
  allPill.addEventListener('click', () => applyDiscSelection(null));
  pillsEl.appendChild(allPill);

  // One pill per package
  cats.forEach(cat => {{
    const pill = document.createElement('button');
    pill.dataset.pkg = cat.name;
    pill.textContent = cat.name;
    pill.style.cssText = `font-family:inherit;font-size:0.68rem;font-weight:500;padding:3px 12px;border-radius:20px;border:1px solid #e5e1d8;background:;color:#8f8b80;cursor:pointer;transition:all 0.15s;letter-spacing:0.04em`;
    pill.addEventListener('click', () => {{
      applyDiscSelection(_discPkgSel === cat.name ? null : cat.name);
    }});
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
      applyDiscSelection(_discPkgSel === cat.name ? null : cat.name);
    }});

    item.addEventListener('mouseenter', () => {{
      if(_discPkgSel !== null) return;   // pill is active — don't override
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
      if(_discPkgSel !== null) return;   // pill is active — restore to pill state
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

  // Reapply any previously selected package so switching contract type keeps the selection
  if(_discPkgSel !== null) applyDiscSelection(_discPkgSel);
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

function renderSoftKpiTrends(type, region, month) {{
  const el = document.getElementById('ov-soft-kpi-trends');
  const isTS = type === 'ts';

  // Compute per-month averages from DATA
  const monthData = ALL_MONTHS.map(mn => {{
    const pool = applyFilters(DATA.filter(r => r.month === mn && r.mgr !== ''), type, region);
    const m = calcMetrics(pool);
    return {{ mn, avgDtt: m.avgDtt, avgUqc: m.avgUqc, avgVm: m.avgVm }};
  }});

  const labels  = ALL_MONTHS.map(mn => MONTH_NAMES[mn]);
  const dttData = monthData.map(d => parseFloat(d.avgDtt.toFixed(1)));
  const uqcData = monthData.map(d => parseFloat(d.avgUqc.toFixed(1)));
  const vmData  = isTS ? null : monthData.map(d => d.avgVm !== null ? parseFloat(d.avgVm.toFixed(1)) : null);

  // Determine selected index for header stats
  const selIdx = (month && month > 0) ? ALL_MONTHS.indexOf(month) : ALL_MONTHS.length - 1;
  const selLabel = labels[selIdx];

  const kpis = [
    {{ id:'dtt', label:'Daily Talk Time',        unit:'avg mins / day',     color:'#f0a050', data:dttData, targetLow:30, targetHigh:45, yMin:0, yMax:null }},
    {{ id:'uqc', label:'Unique Qualified Calls', unit:'avg calls / day',    color:'#4f5fcc', data:uqcData, targetLow:4,  targetHigh:8,  yMin:0, yMax:null }},
    ...( isTS ? [] : [{{ id:'vm', label:'Verified Meetings', unit:'avg meetings / day', color:'#00897b', data:vmData, targetLow:1, targetHigh:4, yMin:0, yMax:null }}] )
  ];

  el.innerHTML = `<div class="chart-title" style="margin-bottom:12px;font-size:13px;font-weight:600;color:var(--text)">Soft KPI Trends — Monthly Averages</div>`;

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
      : `<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:6px;background:#f4f5fb;color:#8f8b80">— flat</span>`;
    const slicedData = kpi.data.slice(0, selIdx + 1).filter(v => v !== null);
    const periodAvg = slicedData.length ? (slicedData.reduce((a,b)=>a+b,0)/slicedData.length).toFixed(1) : '—';
    const canvasId = `chart-softkpi-${{kpi.id}}`;

    const validData = kpi.data.filter(v=>v!==null);
    const dataMin = Math.min(...validData);
    const dataMax = Math.max(...validData);
    const dataRange = dataMax - dataMin || 1;
    const yMin = Math.max(0, Math.floor((Math.min(dataMin, kpi.targetLow) - dataRange * 0.4) * 10) / 10);
    const yMax = Math.ceil((Math.max(dataMax, kpi.targetHigh) + dataRange * 0.4) * 10) / 10;

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
  const dayKeys = Object.keys(DAILY_COLL).filter(d => d.startsWith(prefix)).sort();
  const labels = dayKeys.map(d => {{
    const day = parseInt(d.split('-')[2]);
    const dow = DAY_SHORT[new Date(d).getDay()];
    return dow+' '+day;
  }});
  const amounts = dayKeys.map(d => {{
    const dc = DAILY_COLL[d] || {{}};
    if(type==='ts') return dc.ts||0;
    if(type==='field') return dc.field||0;
    return (dc.ts||0)+(dc.field||0);
  }});
  return {{ labels, amounts, dayKeys }};
}}

// Compute smart axis max (round up to nice number)
function niceMax(v) {{
  if(v<=0) return 100000;
  const mag = Math.pow(10, Math.floor(Math.log10(v)));
  return Math.ceil(v/mag)*mag;
}}

function renderTrendMonthly(type, region) {{
  document.getElementById('ov-trend-title').textContent = 'Cash Collection — Monthly';
  const labels = ALL_MONTHS.map(mn => MONTH_NAMES[mn]);
  const totals = ALL_MONTHS.map(mn => {{
    if(region && region !== 'all') {{
      // Region filter active — compute from DATA (DAILY_COLL has no region dimension)
      return applyFilters(DATA.filter(r => r.month===mn && r.mgr!==''), type, region)
        .reduce((s,r) => s+r.coll, 0);
    }}
    // No region filter — use DAILY_COLL (authoritative source)
    const calMo = String(mn).padStart(2,'0');
    const prefix = '2026-'+calMo+'-';
    const dayKeys = Object.keys(DAILY_COLL).filter(d => d.startsWith(prefix));
    return dayKeys.reduce((s,d) => {{
      const dc = DAILY_COLL[d]||{{}};
      if(type==='ts') return s+(dc.ts||0);
      if(type==='field') return s+(dc.field||0);
      return s+(dc.ts||0)+(dc.field||0);
    }}, 0);
  }});
  if(trendChart) trendChart.destroy();
  trendChart = new Chart(document.getElementById('chart-trend'), {{
    type:'bar',
    data:{{ labels, datasets:[
      {{
        type:'bar',
        label:'Cash Collection',
        data:totals,
        backgroundColor:'#2a9d8fcc',
        borderRadius:6,
        barPercentage:0.5,
        categoryPercentage:0.6,
        order:2,
        datalabels:{{display:false}},
      }},
      {{
        type:'line',
        label:'Trend',
        data:totals,
        borderColor:'#000',
        backgroundColor:'transparent',
        borderWidth:2,
        pointRadius:6,
        pointBackgroundColor:'#ffffff',
        pointBorderColor:'#000',
        pointBorderWidth:2,
        pointHoverRadius:8,
        tension:0.3,
        order:1,
        datalabels:{{display:false}},
      }}
    ]}},
    options:{{
      responsive:true,
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:ctx=>fmt(ctx.parsed.y)}}}},
        datalabels:{{display:false}},
      }},
      scales:{{y:{{beginAtZero:true,ticks:{{callback:v=>fmt(v)}}}}}}
    }}
  }});
}}


function renderTrendDaily(month, type) {{
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

function renderOvMgrCards(type, region) {{
  document.getElementById('ov-report-cards').style.display = '';
  document.getElementById('ov-single-top').style.display = 'none';
  document.getElementById('ov-single-month').style.display = 'none';
  document.getElementById('ov-soft-kpi-trends').style.display = '';
  if(collChart) collChart.destroy();
  if(tvaChart) tvaChart.destroy();
  renderSoftKpiTrends(type, region, _ovDrillMonth);
  const mn = _ovDrillMonth;
  let cards = '';
  for(const mg of Object.keys(MGR_TEAMS)) {{
    let p = applyFilters(DATA.filter(r => r.month === mn && r.mgr === mg), type, region);
    if(p.length === 0) continue;
    const m = calcMetrics(p);
    const mgrName = MGR_NAMES[mg] || mg;
    const mgrRev  = getRevenue(MGR_TEAMS[mg] || [], mn, type, region);
    cards += `<div class="ov-drill-wrap" onclick="drillOvMgr('${{mg}}')">
      ${{reportCard(mgrName, mg+' &mdash; '+MONTH_NAMES[mn]+' &mdash; '+p.length+' consultants', m, p.some(r=>r.is_ts), null, '', false, true, '', mgrRev)}}
      <div class="ov-drill-hint">Click to view TL breakdown &#8250;</div>
    </div>`;
  }}
  if(!cards) cards = '<p style="color:var(--muted);padding:20px;font-size:13px">No data for this selection.</p>';
  document.getElementById('ov-report-cards').innerHTML = '<div class="rc-grid-wide">'+cards+'</div>';
}}

function renderOvTlCards(type, region) {{
  document.getElementById('ov-report-cards').style.display = '';
  document.getElementById('ov-single-top').style.display = 'none';
  document.getElementById('ov-single-month').style.display = 'none';
  document.getElementById('ov-soft-kpi-trends').style.display = '';
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
    cards += reportCard(tlName + (isDirect ? ' (Direct)' : ''), tl+' &mdash; '+MONTH_NAMES[mn]+' &mdash; '+p.length+' members', m, p.some(r=>r.is_ts), null, '', false, true, '', tlRev);
  }}
  if(!cards) cards = '<p style="color:var(--muted);padding:20px;font-size:13px">No data for this selection.</p>';
  document.getElementById('ov-report-cards').innerHTML = '<div class="rc-grid-wide">'+cards+'</div>';
}}

function render() {{
  const month  = +document.getElementById('f-month').value;
  const type   = document.getElementById('f-type').value;
  const region = document.getElementById('f-region').value;

  _ovSetBreadcrumb();

  // Drill-down: TL cards for a manager
  if(_ovDrillMgr !== '') {{
    renderOvTlCards(type, region);
    return;
  }}

  // Drill-down: manager cards for a month
  if(_ovDrillMonth !== 0) {{
    renderOvMgrCards(type, region);
    return;
  }}

  // All Months -> report cards per month, then monthly trend chart
  if(month === 0) {{
    _ovDrillMonth = 0; _ovDrillMgr = ''; _ovSetBreadcrumb();
    document.getElementById('ov-report-cards').style.display = '';
    document.getElementById('ov-single-top').style.display = 'none';
    document.getElementById('ov-single-month').style.display = 'none';
    if(collChart) collChart.destroy();
    if(tvaChart) tvaChart.destroy();

    let cards = '';
    for(const mn of ALL_MONTHS) {{
      let p = applyFilters(DATA.filter(r => r.month === mn && r.mgr !== ''), type, region);
      if(p.length === 0) continue;
      const m      = calcMetrics(p);
      const mnRev  = getRevenue(Object.keys(REV_TL), mn, type, region);
      cards += `<div class="ov-drill-wrap" onclick="drillOvMonth(${{mn}})">
        ${{reportCard(MONTH_NAMES[mn], p.length+' consultants', m, type === 'ts', null, '', true, true, '', mnRev)}}
        <div class="ov-drill-hint">Click to view managers &#8250;</div>
      </div>`;
    }}
    document.getElementById('ov-report-cards').innerHTML = '<div class="rc-grid-wide">'+cards+'</div>';
    renderTrendMonthly(type, region);
    renderActiveGainChart(type, region, 0);
    renderRenewalsTrend(type, region, 0);
    renderPkgOv(0, type);
    renderEmpProdChart(type, region, 0);
    initDiscountTrendChart(type, region);
    document.getElementById('ov-soft-kpi-trends').style.display = '';
    renderSoftKpiTrends(type, region, 0);
    return;
  }}

  // Specific month selected via dropdown — reset any drill state
  _ovDrillMonth = 0;
  _ovDrillMgr   = '';
  _ovSetBreadcrumb();

  // Specific month -> KPI tiles + daily trend + manager charts
  document.getElementById('ov-report-cards').style.display = 'none';
  document.getElementById('ov-single-top').style.display = '';
  document.getElementById('ov-single-month').style.display = 'none';
  document.getElementById('ov-soft-kpi-trends').style.display = '';
  renderSoftKpiTrends(type, region, month);
  renderTrendDaily(month, type);
  renderActiveGainChart(type, region, month);
  renderRenewalsTrend(type, region, month);
  renderPkgOv(month, type);
  renderEmpProdChart(type, region, month);
  initDiscountTrendChart(type, region);

  let pool = applyFilters(DATA.filter(r => r.month === month && r.mgr !== ''), type, region);

  const m = calcMetrics(pool);
  const isTS = type === 'ts';

  // KPI tiles for selected month
  const tile = (label, val, sub, highlight) =>
    `<div class="kpi-card${{highlight?' highlight':''}}">
      <div class="kpi-label">${{label}}</div>
      <div class="kpi-val">${{val}}</div>
      ${{sub ? `<div class="kpi-sub">${{sub}}</div>` : ''}}
    </div>`;

  const hardTiles =
    tile('Cash Collection', fmt(m.cash), 'Target: '+fmt(m.target), true) +
    tile('TvA', pct(m.cash,m.target), tvaRating(m.tva)) +
    tile('Packages Sold', m.pkgSold, 'Avg Discount: '+(m.avgDisc>0?Math.round(m.avgDisc*100)+'%':'-')) +
    tile('Net Client Gain', Math.round(m.netGain), '') +
    tile('Cash / Employee', m.bom>0 ? fmt(m.cash/m.bom) : '-', '') +
    tile('Active (EOM)', m.active, '') +
    tile('BOM (Target>0)', m.bom, '') +
    tile('Productivity', m.bom>0 ? Math.round(m.productivity)+'%' : '-', 'Productive (≥4K): '+m.productive) +
    tile('Coverage %', Math.round(m.covPct)+'%', '') +
    tile('Renewal Rate', (m.renewed+m.pendRen>0?Math.round(m.renewed/(m.renewed+m.pendRen)*100)+'%':'-'), 'Renewed: '+m.renewed+' · Pending: '+m.pendRen);

  const softTiles =
    tile('Avg UQC / Day', m.avgUqc.toFixed(1), 'Total: '+m.totalUqc.toLocaleString()) +
    tile('Avg DTT / Day', m.avgDtt.toFixed(1)+' min', 'Total: '+fmt(m.totalDtt)+' min') +
    (!isTS ? tile('Avg VM / Day', m.avgVm!==null ? m.avgVm.toFixed(1) : 'N/A', 'Total: '+m.totalUvm.toLocaleString()) : '');

  const regionLabel = region !== 'all' ? ' · '+region : '';
  const grid5 = `display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:16px`;
  document.getElementById('ov-kpi-tiles').innerHTML =
    `<div class="sec-header"><div class="sec-title">${{MONTH_NAMES[month]}}${{regionLabel}} — ${{pool.length}} consultants</div><div class="sec-badge hard-badge">Financial</div></div>
     <div style="${{grid5}}">${{hardTiles}}</div>
     <div class="sec-header"><div class="sec-title">Activity</div><div class="sec-badge soft-badge">Avg / Day</div></div>
     <div style="${{grid5}}">${{softTiles}}</div>`;

  // Charts - Collection by Manager (filtered by region)
  const allMgrs = Object.keys(MGR_TEAMS);
  const mgrData = allMgrs.map(mg => {{
    const p = applyFilters(DATA.filter(r => r.month===month && r.mgr===mg), type, region);
    return {{ mg, p, cash: p.reduce((s,r)=>s+r.coll,0), target: p.reduce((s,r)=>s+r.target,0) }};
  }}).filter(d => d.p.length > 0);

  const mgrs      = mgrData.map(d => d.mg);
  const mgrCash   = mgrData.map(d => d.cash);
  const mgrTarget = mgrData.map(d => d.target);
  const mgrLabels = mgrs.map(mg => MGR_NAMES[mg]||mg);

  if(collChart) collChart.destroy();
  collChart = new Chart(document.getElementById('chart-coll'), {{
    type:'bar',
    data:{{ labels:mgrLabels, datasets:[
      {{label:'Collection',data:mgrCash,backgroundColor:'#5c6bc0'}},
      {{label:'Target',data:mgrTarget,backgroundColor:'#e8eaf6'}}
    ]}},
    options:{{ responsive:true, plugins:{{legend:{{position:'bottom',labels:{{font:{{size:10}}}}}}}}, scales:{{y:{{ticks:{{callback:v=>fmt(v)}}}}}} }}
  }});

  const mgrTva = mgrData.map(d => d.target > 0 ? d.cash/d.target*100 : 0);
  if(tvaChart) tvaChart.destroy();
  tvaChart = new Chart(document.getElementById('chart-tva'), {{
    type:'bar',
    data:{{ labels:mgrLabels, datasets:[
      {{label:'TvA %',data:mgrTva,backgroundColor:mgrTva.map(v => v>=100?'#66bb6a':v>=75?'#42a5f5':'#ef5350')}}
    ]}},
    options:{{ responsive:true, plugins:{{legend:{{display:false}}}}, scales:{{y:{{max:200,ticks:{{callback:v=>v+'%'}}}}}} }}
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
}}

function renderAgentTable() {{
  const currMn = +document.getElementById('apt-month').value;
  const type   = document.getElementById('apt-type').value;
  const tlF    = document.getElementById('apt-tl').value;
  const mgrF   = document.getElementById('apt-mgr').value;
  if(currMn === '' || currMn === null || isNaN(currMn)) return;

  const prevMn = currMn - 1;  // Dec 2025 = month 0 when Jan (1) selected
  const m3Mns  = [currMn-2, currMn-1, currMn].filter(m => m >= -2);  // include Oct-Dec 2025

  // Group records by consultant key
  const byKey = {{}};
  for(const r of DATA) {{
    if(!r.mgr) continue;
    if(type === 'field' && r.is_ts) continue;
    if(type === 'ts'    && !r.is_ts) continue;
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

    const curr     = cons.recs[currMn] || null;
    const prev     = (cons.recs[prevMn] !== undefined) ? cons.recs[prevMn] : null;
    const hasPrev  = prev !== null;
    const currDays = curr ? curr.days : 0;
    const prevDays = prev ? prev.days : 0;

    // UVM
    const cUvm    = curr ? curr.uvm : 0;
    const pUvm    = hasPrev ? prev.uvm : null;
    const cAvgUvm = currDays>0 ? cUvm/currDays : 0;
    const pAvgUvm = (hasPrev && prevDays>0) ? pUvm/prevDays : null;
    const uvmD    = (pAvgUvm!==null && pAvgUvm>0) ? (cAvgUvm-pAvgUvm)/pAvgUvm*100 : null;

    // UQC
    const cUqc    = curr ? curr.uqc : 0;
    const pUqc    = hasPrev ? prev.uqc : null;
    const cAvgUqc = currDays>0 ? cUqc/currDays : 0;
    const pAvgUqc = (hasPrev && prevDays>0) ? pUqc/prevDays : null;
    const uqcD    = (pAvgUqc!==null && pAvgUqc>0) ? (cAvgUqc-pAvgUqc)/pAvgUqc*100 : null;

    // DTT
    const cDtt    = curr ? curr.dtt : 0;
    const pDtt    = hasPrev ? prev.dtt : null;
    const cAvgDtt = currDays>0 ? cDtt/currDays : 0;
    const pAvgDtt = (hasPrev && prevDays>0) ? pDtt/prevDays : null;
    const dttD    = (pAvgDtt!==null && pAvgDtt>0) ? (cAvgDtt-pAvgDtt)/pAvgDtt*100 : null;

    // Collection
    const cColl = curr ? curr.coll : 0;
    const m3C   = m3Mns.reduce((s,m) => {{ const rc=cons.recs[m]; return s+(rc?rc.coll:0); }}, 0) / 3;
    const tDate = Object.values(cons.recs).filter(rc => rc.month <= currMn).reduce((s,rc)=>s+rc.coll, 0);
    const cPkg  = curr ? curr.pkg : 0;
    const m3P   = m3Mns.reduce((s,m) => {{ const rc=cons.recs[m]; return s+(rc?rc.pkg:0); }}, 0) / 3;

    rows.push({{
      name: info.name, age: calcAge(info.doj),
      tl: info.tl_name || info.mgr_name || '-', mgr: info.mgr_name || '-',
      pUvm, pAvgUvm, cUvm, cAvgUvm, uvmD,
      pUqc, pAvgUqc, cUqc, cAvgUqc, pAvgDtt, cAvgDtt, uqcD, dttD,
      cColl, m3C, tDate, cPkg, m3P, _s: cColl
    }});
  }}

  rows.sort((a,b) => b._s - a._s);

  const mn = MONTH_NAMES[currMn] || '';

  // Render current-avg cell with inline trend arrow + capped % change
  const trendCell = (val, delta, bg) => {{
    if(delta === null) return '<td class="num ' + bg + '">' + val + '</td>';
    const capped = Math.max(-100, Math.min(100, delta));
    const arrow  = delta >= 0 ? '\u2191' : '\u2193';
    const sign   = delta >= 0 ? '+' : '';
    const c      = delta >= 0 ? 'apt-delta-pos' : 'apt-delta-neg';
    return '<td class="num ' + bg + '">' + val +
      '<span class="' + c + '" style="font-size:10px;margin-left:4px">' +
      arrow + ' ' + sign + capped.toFixed(1) + '%' + '</span></td>';
  }};

  let tbl = '<table><thead>' +
    '<tr><th colspan="19" style="text-align:left;padding:10px 14px;font-size:13px;font-weight:700;background:var(--accent-light,#eef2ff);color:var(--accent,#3b5bdb);border-bottom:1px solid var(--border)">' +
    'Consultant Performance Metrics \u2014 ' + mn + ' \u2014 ' + rows.length + ' consultants</th></tr>' +
    '<tr>' +
    '<th rowspan="2" style="min-width:140px">Name</th>' +
    '<th rowspan="2">Age</th>' +
    '<th rowspan="2" style="min-width:120px">Team Lead</th>' +
    '<th rowspan="2" style="min-width:120px">Manager</th>' +
    '<th colspan="4" class="apt-group meetings-group">MEETINGS (Unique Verified)</th>' +
    '<th colspan="6" class="apt-group calls-group">CALLS</th>' +
    '<th colspan="5" class="apt-group coll-group">COLLECTION</th>' +
    '</tr><tr>' +
    '<th class="num meetings-sub">Prev Total</th>' +
    '<th class="num meetings-sub">Prev Avg/d</th>' +
    '<th class="num meetings-sub">Curr Total</th>' +
    '<th class="num meetings-sub">Curr Avg/d</th>' +
    '<th class="num calls-sub">Prev UQC</th>' +
    '<th class="num calls-sub">Prev Avg/d</th>' +
    '<th class="num calls-sub">Curr UQC</th>' +
    '<th class="num calls-sub">Curr Avg/d</th>' +
    '<th class="num calls-sub">Prev DTT/d</th>' +
    '<th class="num calls-sub">Curr DTT/d</th>' +
    '<th class="num coll-sub">' + mn + ' Coll</th>' +
    '<th class="num coll-sub">3M Avg Coll</th>' +
    '<th class="num coll-sub">Till Date</th>' +
    '<th class="num coll-sub">' + mn + ' Pkgs</th>' +
    '<th class="num coll-sub">3M Avg Pkgs</th>' +
    '</tr></thead><tbody>';

  if(!rows.length) {{
    tbl += '<tr><td colspan="19" style="text-align:center;color:var(--muted);padding:24px">No data for this selection.</td></tr>';
  }} else {{
    for(const r of rows) {{
      tbl +=
        '<tr>' +
        '<td class="td-name">' + r.name + '</td>' +
        '<td class="td-muted" style="white-space:nowrap">' + r.age + '</td>' +
        '<td class="td-muted">' + r.tl + '</td>' +
        '<td class="td-muted">' + r.mgr + '</td>' +
        '<td class="num meetings-sub">' + (r.pUvm===null?'-':r.pUvm) + '</td>' +
        '<td class="num meetings-sub">' + (r.pAvgUvm===null?'-':r.pAvgUvm.toFixed(2)) + '</td>' +
        '<td class="num meetings-sub">' + r.cUvm + '</td>' +
        trendCell(r.cAvgUvm.toFixed(2), r.uvmD, 'meetings-sub') +
        '<td class="num calls-sub">' + (r.pUqc===null?'-':r.pUqc) + '</td>' +
        '<td class="num calls-sub">' + (r.pAvgUqc===null?'-':r.pAvgUqc.toFixed(1)) + '</td>' +
        '<td class="num calls-sub">' + r.cUqc + '</td>' +
        trendCell(r.cAvgUqc.toFixed(1), r.uqcD, 'calls-sub') +
        '<td class="num calls-sub">' + (r.pAvgDtt===null?'-':r.pAvgDtt.toFixed(1)+'m') + '</td>' +
        trendCell(r.cAvgDtt.toFixed(1)+'m', r.dttD, 'calls-sub') +
        '<td class="num coll-sub">' + fmt(r.cColl) + '</td>' +
        '<td class="num coll-sub">' + fmt(r.m3C) + '</td>' +
        '<td class="num coll-sub">' + fmt(r.tDate) + '</td>' +
        '<td class="num coll-sub">' + r.cPkg + '</td>' +
        '<td class="num coll-sub">' + r.m3P.toFixed(1) + '</td>' +
        '</tr>';
    }}
  }}

  tbl += '</tbody></table>';
  document.getElementById('ov-agent-table').innerHTML = tbl;
}}

// ============ INIT ============
(function init() {{
  populateAptFilters();
  renderAgentTable();
  render();
}})();
</script>
</body>
</html>'''

with open('C:/Users/hamza.rizwan/CFD_Sales_Dashboard_2026.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Dashboard saved: {len(html)/1024:.0f}KB")
