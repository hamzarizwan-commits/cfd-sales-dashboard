"""refresh_vm_data.py — Pull missing verified-meetings data from Redshift and
re-embed all VM JS variables into the meetings-audit-dashboard source HTML.

Runs as Step 2b in runner.py (after generate_dashboard.py, before build_cfd_merged.py).
Pulls every date from max(existing)+1 through yesterday in a single batch per variable.
"""

import json, re, sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from redshift_client import run_query

HTML_PATH = Path(r'C:\Users\hamza.rizwan\Aurangzeb.fake.meetings\Claude\meetings-audit-dashboard\index.html')

# ── 1. Parse all VM variables out of the current HTML ────────────────────────

def extract_var_line(content, var_name):
    """Return the JS value string for a const declaration on a single line."""
    m = re.search(rf'^const {re.escape(var_name)}\s*=(.*);[ \t]*$', content, re.MULTILINE)
    if not m:
        raise ValueError(f'{var_name} not found in HTML')
    return m.group(1).strip()

def parse_json_var(content, var_name):
    return json.loads(extract_var_line(content, var_name))

html = HTML_PATH.read_text(encoding='utf-8')

vm_raw    = parse_json_var(html, 'VM_RAW_DATA')       # list of {consultant,task_date,manager,senior_manager,team_name,success_vms}
vm_roster = parse_json_var(html, 'VM_ROSTER')          # {name: [dates]}
vm_failed = parse_json_var(html, 'VM_FAILED')          # {name: {date: count}}
vm_qcalls = parse_json_var(html, 'VM_QCALLS')          # {name: {date: count}}
vm_called = parse_json_var(html, 'VM_CALLED_CLIENTS')  # {team: count}

all_dates = sorted({r['task_date'] for r in vm_raw})
max_date  = all_dates[-1] if all_dates else '2025-08-31'
print(f'Current VM_RAW_DATA: {len(vm_raw):,} records, max date = {max_date}')

# ── 2. Work out which dates are missing ───────────────────────────────────────

today     = date.today()
yesterday = today - timedelta(days=1)
from_date = date.fromisoformat(max_date) + timedelta(days=1)

if from_date > yesterday:
    print('VM data already up to date — nothing to fetch.')
    sys.exit(0)

print(f'Fetching {from_date} to {yesterday} ({(yesterday - from_date).days + 1} days)')

# ── 3. Build name-normalisation map from existing data ───────────────────────

# consultant_map: name -> (latest_date, manager, senior_manager, team_name)
consultant_map = {}
for row in vm_raw:
    name = row['consultant']
    if name not in consultant_map or row['task_date'] > consultant_map[name][0]:
        consultant_map[name] = (row['task_date'], row['manager'], row['senior_manager'], row['team_name'])

# canonical name lookup for companion vars (strip+lower -> existing key)
name_key = {}
for name in consultant_map:
    name_key[name.strip().lower()] = name
for ds in (vm_roster, vm_failed, vm_qcalls):
    for k in ds:
        norm = k.strip().lower()
        if norm not in name_key:
            name_key[norm] = k

def canonical(name):
    return name_key.get(name.strip().lower(), name)

# ── 4. Shared CTE to exclude team leads ──────────────────────────────────────

TL_CTE = """WITH team_leads AS (
  SELECT DISTINCT SPLIT_PART(team_lead_staff_sk,'|',5) AS lead_email
  FROM podl_bayutsa.dim_teams
  WHERE team_lead_staff_sk IS NOT NULL AND team_lead_staff_sk LIKE '%@%'
)"""

fd, yd = str(from_date), str(yesterday)

# ── 5. VM_RAW_DATA ────────────────────────────────────────────────────────────

print('\nQuerying VM_RAW_DATA ...')
df_raw = run_query(f"""
{TL_CTE}
SELECT
  sp.salesperson_name_en             AS consultant,
  TO_CHAR(m.task_date, 'YYYY-MM-DD') AS task_date,
  COALESCE(t.team_name_en,'Unknown') AS team_name_rs,
  COUNT(*)                           AS success_vms
FROM (
  SELECT f.date_task_nk AS task_date,
         SPLIT_PART(f.staff_sk,'|',5) AS staff_email,
         f.team_sk
  FROM   podl_bayutsa.fact_tasks f
  JOIN   podl_bayutsa.dim_task_types   tt  ON f.task_type_sk    = tt.task_type_sk
  JOIN   podl_bayutsa.dim_task_outcome tod ON f.task_outcome_sk = tod.task_outcome_sk
  WHERE  tt.task_type_name_en = 'Meeting'
    AND  f.is_verified = 1
    AND  tod.task_outcome_name_en NOT IN ('Failed Attempt','POC Unavailable')
    AND  f.date_task_nk BETWEEN '{fd}' AND '{yd}'
) m
JOIN   podl_bayutsa.dim_salesperson sp ON m.staff_email = sp.email
LEFT JOIN podl_bayutsa.dim_teams    t  ON m.team_sk     = t.team_sk
WHERE  sp.team_type_name_en IN ('Sales','unknown')
  AND  m.staff_email NOT IN (SELECT lead_email FROM team_leads)
GROUP BY 1,2,3
ORDER BY 1,2
""")
print(f'  Returned {len(df_raw)} rows across {df_raw["task_date"].nunique() if len(df_raw) else 0} days')

new_rows, unmapped = [], []
for _, row in df_raw.iterrows():
    name = row['consultant']
    mapping = consultant_map.get(name)
    if mapping:
        _, mgr, sr_mgr, team = mapping
        new_rows.append({
            'consultant':      name,
            'task_date':       row['task_date'],
            'manager':         mgr,
            'senior_manager':  sr_mgr,
            'team_name':       team,
            'success_vms':     int(row['success_vms']),
        })
        if row['task_date'] > consultant_map[name][0]:
            consultant_map[name] = (row['task_date'], mgr, sr_mgr, team)
    else:
        unmapped.append(name)

if unmapped:
    print(f'  NOTE: {len(set(unmapped))} unmapped consultants (no history) skipped: {sorted(set(unmapped))}')

vm_raw.extend(new_rows)
print(f'  VM_RAW_DATA: {len(vm_raw):,} total records')

# ── 6. VM_ROSTER ──────────────────────────────────────────────────────────────

print('\nQuerying VM_ROSTER ...')
df_roster = run_query(f"""
{TL_CTE}
SELECT DISTINCT sp.salesperson_name_en AS name,
                TO_CHAR(f.date_task_nk,'YYYY-MM-DD') AS dt
FROM   podl_bayutsa.fact_tasks f
JOIN   podl_bayutsa.dim_task_types   tt ON f.task_type_sk = tt.task_type_sk
JOIN   podl_bayutsa.dim_salesperson  sp ON SPLIT_PART(f.staff_sk,'|',5) = sp.email
WHERE  f.date_task_nk BETWEEN '{fd}' AND '{yd}'
  AND  tt.task_type_name_en = 'Meeting'
  AND  f.is_verified = 1
  AND  sp.team_type_name_en IN ('Sales','unknown')
  AND  SPLIT_PART(f.staff_sk,'|',5) NOT IN (SELECT lead_email FROM team_leads)
""")
for _, row in df_roster.iterrows():
    key = canonical(row['name'])
    dt  = row['dt']
    if key not in vm_roster:
        vm_roster[key] = []
    if dt not in vm_roster[key]:
        vm_roster[key].append(dt)
        vm_roster[key].sort()
print(f'  VM_ROSTER: {len(vm_roster)} consultants')

# ── 7. VM_FAILED ──────────────────────────────────────────────────────────────

print('\nQuerying VM_FAILED ...')
df_failed = run_query(f"""
{TL_CTE}
SELECT sp.salesperson_name_en AS name,
       TO_CHAR(f.date_task_nk,'YYYY-MM-DD') AS dt,
       COUNT(*) AS n
FROM   podl_bayutsa.fact_tasks f
JOIN   podl_bayutsa.dim_task_types   tt  ON f.task_type_sk    = tt.task_type_sk
JOIN   podl_bayutsa.dim_task_outcome tod ON f.task_outcome_sk = tod.task_outcome_sk
JOIN   podl_bayutsa.dim_salesperson  sp  ON SPLIT_PART(f.staff_sk,'|',5) = sp.email
WHERE  f.date_task_nk BETWEEN '{fd}' AND '{yd}'
  AND  tt.task_type_name_en = 'Meeting'
  AND  f.is_verified = 1
  AND  tod.task_outcome_name_en IN ('Failed Attempt','POC Unavailable')
  AND  sp.team_type_name_en IN ('Sales','unknown')
  AND  SPLIT_PART(f.staff_sk,'|',5) NOT IN (SELECT lead_email FROM team_leads)
GROUP BY 1,2
""")
for _, row in df_failed.iterrows():
    key = canonical(row['name'])
    dt  = row['dt']
    if key not in vm_failed:
        vm_failed[key] = {}
    vm_failed[key][dt] = int(row['n'])
print(f'  VM_FAILED: {len(vm_failed)} consultants')

# ── 8. VM_QCALLS ──────────────────────────────────────────────────────────────

print('\nQuerying VM_QCALLS ...')
df_qcalls = run_query(f"""
{TL_CTE}
SELECT sp.salesperson_name_en AS name,
       TO_CHAR(c.date_call_nk,'YYYY-MM-DD') AS dt,
       COUNT(*) AS n
FROM   podl_bayutsa.fact_calltracking_staff_logs c
JOIN   podl_bayutsa.dim_salesperson sp ON SPLIT_PART(c.staff_sk,'|',5) = sp.email
WHERE  c.date_call_nk BETWEEN '{fd}' AND '{yd}'
  AND  c.calltracking_status_sk = 'connected'
  AND  c.connected_duration >= 60
  AND  (c.is_fake_call IS NULL OR c.is_fake_call = FALSE)
  AND  sp.team_type_name_en IN ('Sales','unknown')
  AND  SPLIT_PART(c.staff_sk,'|',5) NOT IN (SELECT lead_email FROM team_leads)
GROUP BY 1,2
""")
for _, row in df_qcalls.iterrows():
    key = canonical(row['name'])
    dt  = row['dt']
    if key not in vm_qcalls:
        vm_qcalls[key] = {}
    vm_qcalls[key][dt] = int(row['n'])
print(f'  VM_QCALLS: {len(vm_qcalls)} consultants')

# ── 9. VM_CALLED_CLIENTS (full current-month MTD re-pull) ─────────────────────

month_start = date(today.year, today.month, 1)
print(f'\nQuerying VM_CALLED_CLIENTS ({month_start} to {yesterday}) ...')
cov_teams = set(vm_called.keys())

df_called = run_query(f"""
SELECT COALESCE(t.team_name_en,'Unknown') AS team,
       COUNT(DISTINCT c.account_sk)        AS n
FROM   podl_bayutsa.fact_calltracking_staff_logs c
LEFT JOIN podl_bayutsa.dim_teams t ON c.team_sk = t.team_sk
WHERE  c.date_call_nk BETWEEN '{month_start}' AND '{yesterday}'
  AND  SPLIT_PART(c.calltracking_status_sk,'|',6) = '540'
  AND  c.connected_duration >= 60
  AND  c.account_sk IS NOT NULL AND c.account_sk <> 'unknown'
GROUP BY 1
""")
new_called = {team: 0 for team in cov_teams}
for _, row in df_called.iterrows():
    team = row['team']
    if team in cov_teams:
        new_called[team] = int(row['n'])
    else:
        stripped = team.strip()
        for ct in cov_teams:
            if ct.strip() == stripped:
                new_called[ct] = int(row['n'])
                break
vm_called = new_called
print(f'  VM_CALLED_CLIENTS: {len(vm_called)} teams, total {sum(vm_called.values()):,} clients')

# ── 10. VM_SC_ROLES — add any new consultant names ────────────────────────────

sc_val = extract_var_line(html, 'VM_SC_ROLES')
existing_sc = set(re.findall(r'"([^"]+)"', sc_val))
new_names = {r['consultant'] for r in vm_raw} - existing_sc
if new_names:
    existing_sc |= new_names
    print(f'\nAdded {len(new_names)} new name(s) to VM_SC_ROLES')
sc_new_val = 'new Set(' + json.dumps(sorted(existing_sc), ensure_ascii=False, separators=(',', ':')) + ')'

# ── 11. Embed all updated variables back into HTML ────────────────────────────

def embed_var(content, var_name, value):
    new_val = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    new_line = f'const {var_name} = {new_val};\n'
    pattern  = rf'^const {re.escape(var_name)}\s*=.*\n'
    result, n = re.subn(pattern, new_line, content, flags=re.MULTILINE)
    if n != 1:
        raise ValueError(f'Expected 1 match for {var_name}, got {n}')
    return result

print('\nEmbedding updated variables into HTML ...')
html = embed_var(html, 'VM_RAW_DATA',       vm_raw)
html = embed_var(html, 'VM_SC_ROLES',       sc_new_val)
html = embed_var(html, 'VM_ROSTER',         vm_roster)
html = embed_var(html, 'VM_FAILED',         vm_failed)
html = embed_var(html, 'VM_QCALLS',         vm_qcalls)
html = embed_var(html, 'VM_CALLED_CLIENTS', vm_called)

HTML_PATH.write_text(html, encoding='utf-8')

new_max = max(r['task_date'] for r in vm_raw)
print(f'\nDone. VM data now covers 2025-09-01 to {new_max}')
print(f'File size: {HTML_PATH.stat().st_size:,} bytes')
