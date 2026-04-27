#!/usr/bin/env python3
"""
build_cfd_merged.py
Merges Meetings Audit Dashboard (index.html) into CFD Sales Dashboard (CFD_Sales_Dashboard_2026.html)
Output: CFD_Sales_Dashboard_2026_MERGED.html
"""
import re

# ─────────────────────────────────────────
# A. Read both files
# ─────────────────────────────────────────
CFD_PATH = r'C:\Users\hamza.rizwan\CFD_Sales_Dashboard_2026.html'
IDX_PATH = r'C:\Users\hamza.rizwan\Aurangzeb.fake.meetings\Claude\meetings-audit-dashboard\index.html'
OUT_PATH = r'C:\Users\hamza.rizwan\CFD_Sales_Dashboard_2026_MERGED.html'

print("Reading source files...")
with open(CFD_PATH, encoding='utf-8') as f:
    cfd = f.read()
with open(IDX_PATH, encoding='utf-8') as f:
    idx = f.read()

print(f"  CFD: {len(cfd):,} chars")
print(f"  IDX: {len(idx):,} chars")

# ─────────────────────────────────────────
# B. Extract sections from index.html
# ─────────────────────────────────────────

# B1. Extract CSS from index.html (between <style> and </style>)
idx_css_m = re.search(r'<style>(.*?)</style>', idx, re.DOTALL)
if not idx_css_m:
    raise ValueError("Could not find <style> in index.html")
idx_css_raw = idx_css_m.group(1)

# B1b. Extract the CSV upload header bar (green gradient + Upload CSV button)
# It sits between dashboardMain opening and the tab-pane, lines 280-294 of index.html
csv_header_m = re.search(
    r'(<div style="background:linear-gradient\(to right,#17a05a[^"]*"[^>]*>.*?</div>\s*\n<div style="height:22px"></div>)',
    idx, re.DOTALL
)
csv_header_html = csv_header_m.group(1) if csv_header_m else ''

# B2. Extract tab-overview content (between opening tag and its closing </div>)
tab_ov_m = re.search(r'<div class="tab-pane active" id="tab-overview">(.*?)\n</div><!-- /tab-overview -->', idx, re.DOTALL)
if not tab_ov_m:
    # fallback: simpler end marker
    tab_ov_m = re.search(r'<div class="tab-pane active" id="tab-overview">(.*?)</div>\s*\n\s*<div class="tab-pane" id="tab-vm">', idx, re.DOTALL)
if not tab_ov_m:
    raise ValueError("Could not find tab-overview content in index.html")
tab_overview_content = tab_ov_m.group(1)

# B3. Extract tab-vm content — stop at <!-- /tab-vm --> NOT <!-- /dashboardMain -->
# (dashboardMain closes AFTER the <script> block, so using it would accidentally include all JS)
tab_vm_m = re.search(r'<div class="tab-pane" id="tab-vm">(.*?)\n</div><!-- /tab-vm -->', idx, re.DOTALL)
if not tab_vm_m:
    raise ValueError("Could not find tab-vm content in index.html (missing <!-- /tab-vm --> marker)")
tab_vm_content = tab_vm_m.group(1)

print(f"  tab-overview: {len(tab_overview_content):,} chars")
print(f"  tab-vm: {len(tab_vm_content):,} chars")

# B4. Extract data constants — lines 547-560 from the second <script> block
# Find the second <script> block (the data+functions one, starting at line 546)
# We need: SC_RAW, SC_DETAIL, RAW, TOTAL_ALL, TOTAL_VERIFIED, SC_EXTRA,
#          VM_SC_ROLES, VM_COVERAGE, VM_CALLED_CLIENTS, VM_QCALLS, VM_FAILED, VM_ROSTER, VM_RAW_DATA
const_names = ['SC_RAW', 'SC_DETAIL', 'RAW', 'TOTAL_ALL', 'TOTAL_VERIFIED', 'SC_EXTRA',
               'VM_SC_ROLES', 'VM_COVERAGE', 'VM_CALLED_CLIENTS', 'VM_QCALLS',
               'VM_FAILED', 'VM_ROSTER', 'VM_RAW_DATA']

idx_lines = idx.splitlines()
data_const_lines = []
for line in idx_lines:
    stripped = line.strip()
    if stripped.startswith('const ') and any(stripped.startswith(f'const {c}') for c in const_names):
        data_const_lines.append(line)

data_constants_js = '\n'.join(data_const_lines)
print(f"  Data constants: {len(data_const_lines)} lines extracted")

# B5. Extract ALL JS functions from the main script block
# The main script block starts at line 546 (0-indexed: 545)
# Find it: second <script> after line 275
scripts_found = list(re.finditer(r'<script>', idx))
# scripts_found[0] is login script at line 229, scripts_found[1] is main at line 546
main_script_start_tag = scripts_found[1]  # index 1 = second <script>
main_script_text_start = main_script_start_tag.end()
# Find the closing </script> after this
main_script_end = idx.find('</script>', main_script_text_start)
main_script_block = idx[main_script_text_start:main_script_end]

# Extract from 'function updateMgrTriggerLabel' through end of functions
# but exclude: doLogin, dashFilterData, DASH_USERS, tab switching logic, DOMContentLoaded at end
# Find where function updateMgrTriggerLabel starts
func_start_m = re.search(r'function updateMgrTriggerLabel\b', main_script_block)
if not func_start_m:
    raise ValueError("Could not find function updateMgrTriggerLabel in main script block")

# Extract state vars (they come before the functions but after constants)
state_vars_section = main_script_block[:func_start_m.start()]

# Get only the state variable declarations (let selMgrs, let ch2, etc.)
state_var_lines = []
for line in state_vars_section.splitlines():
    stripped = line.strip()
    if stripped.startswith('let selMgrs') or stripped.startswith('let calYear') or \
       stripped.startswith('let ch2') or stripped.startswith('let lastFiltered') or \
       stripped.startswith('let mgrTrendHidden'):
        state_var_lines.append(line)

# Also grab ALL_MGRS and DATA_DATES init from state_vars_section
for line in state_vars_section.splitlines():
    stripped = line.strip()
    if stripped.startswith('const ALL_MGRS=') or stripped.startswith('const DATA_DATES=') or \
       stripped.startswith('selMgrs=new Set(ALL_MGRS)'):
        state_var_lines.append(line)

state_vars_js = '\n'.join(state_var_lines)

# Extract all functions from updateMgrTriggerLabel to end of script (excluding the IIFE at the end)
js_functions_raw = main_script_block[func_start_m.start():]

# Remove the CSV upload IIFE at the very end (the self-invoking function at the end)
# Find the last "})();" which closes the upload IIFE and everything after
# The end is the csvUploadBtn event listener + IIFE:  (function(){  ...  })();
# Find the point where the upload/DOMContentLoaded IIFE starts
# It starts with: document.getElementById('csvUploadBtn') or similar
# Actually: the IIFE wrapping CSV upload code starts after the last vm_ function
# Let's find last occurrence of "})();" which closes the main iife
last_iife_end = js_functions_raw.rfind('})();')
if last_iife_end != -1:
    js_functions_raw = js_functions_raw[:last_iife_end + 5]

# Convert the CSV upload IIFE to a named function ma_csvInit() so it can be
# called lazily from ma_init() rather than running at page load.
upload_iife_m = re.search(r'\n\(function\(\)\{', js_functions_raw)
if upload_iife_m:
    csv_tail = js_functions_raw[upload_iife_m.start():]
    # Replace "(function(){" opener with "function ma_csvInit(){"
    csv_tail = '\nfunction ma_csvInit(){' + csv_tail[len('\n(function(){'):]
    # Remove the self-invoking tail "})();"
    last_close = csv_tail.rfind('})();')
    if last_close != -1:
        csv_tail = csv_tail[:last_close] + '}'
    js_functions_raw = js_functions_raw[:upload_iife_m.start()] + csv_tail

# Also remove the renderCal section and the inline event listener code that
# directly calls document.getElementById without being in a function (lines 615-634)
# We'll keep only actual function definitions and the state vars
# Lines that directly attach event listeners to specific IDs at top level should be removed
# since they reference old IDs. The ma_init() function we provide will replace them.
# Remove block: from "document.getElementById('mgrAllBtn').addEventListener"
#  through "document.getElementById('calReset').addEventListener..."
# This is between buildMgrList and the next section marker

# Remove top-level event listener calls (not in functions)
# Pattern: remove lines like document.getElementById('mgrAllBtn').addEventListener...
# and const mgrTrigger=... mgrTrigger.addEventListener...
# and document.addEventListener('click',e=>{if(!document.getElementById('mgrDropdown')...

lines_to_remove_patterns = [
    r"document\.getElementById\('mgrAllBtn'\)\.addEventListener",
    r"const mgrTrigger=document\.getElementById",
    r"mgrTrigger\.addEventListener",
    r"document\.addEventListener\('click',e=>\{if\(!document\.getElementById\('mgrDropdown'\)",
    r"^// ═+$",
    r"^// OVERVIEW — CALENDAR$",
    r"^// ═+$",
    r"function renderCal\b",
]

# Instead, do a targeted removal of the top-level code block (lines 615-634)
# which is between buildMgrList's closing brace and the renderCal function
js_functions_raw = re.sub(
    r"document\.getElementById\('mgrAllBtn'\)\.addEventListener.*?\n"
    r"const mgrTrigger=document\.getElementById\('mgrTrigger'\),mgrPanel=document\.getElementById\('mgrPanel'\);\n"
    r"mgrTrigger\.addEventListener.*?\n"
    r"document\.addEventListener\('click',e=>\{if\(!document\.getElementById\('mgrDropdown'\)\.contains\(e\.target\)\)\{mgrTrigger\.classList\.remove\('open'\);mgrPanel\.classList\.remove\('open'\);\}\}\);\n",
    '\n',
    js_functions_raw
)

# Remove renderCal function (it references old IDs and is replaced by ma_init)
js_functions_raw = re.sub(
    r"// ═+\n// OVERVIEW — CALENDAR\n// ═+\nfunction renderCal\(\)\{.*?\}\n",
    '\n',
    js_functions_raw,
    flags=re.DOTALL
)
# Also remove the _dateFrom/_dateTo event listeners
js_functions_raw = re.sub(
    r"const _dateFrom=document\.getElementById\('dateFrom'\);\n"
    r"const _dateTo=document\.getElementById\('dateTo'\);\n"
    r"_dateFrom\.addEventListener.*?\n"
    r"_dateTo\.addEventListener.*?\n"
    r"document\.getElementById\('calReset'\)\.addEventListener.*?\n",
    '\n',
    js_functions_raw
)

# Remove the top-level INIT block that runs MA init at page load
# (rangeStart=DEFAULT_FROM; buildMgrList(); updateMgrTriggerLabel(); renderCal(); update();)
# This was init code from index.html that we now handle inside ma_init() lazily.
js_functions_raw = re.sub(
    r"// ═+\s*\n// INIT\s*\n// ═+\s*\n"
    r"rangeStart\s*=\s*DEFAULT_FROM;\s*\n"
    r"rangeEnd\s*=\s*DEFAULT_TO;\s*\n"
    r"buildMgrList\(\);\s*\n"
    r"updateMgrTriggerLabel\(\);\s*\n"
    r"(?:renderCal\(\);\s*\n)?"
    r"update\(\);\s*\n",
    '\n',
    js_functions_raw
)

print(f"  JS functions block: {len(js_functions_raw):,} chars")

# ─────────────────────────────────────────
# C. Build CSS additions
# ─────────────────────────────────────────

ma_css_vars = """
/* ===== MEETINGS AUDIT / VERIFIED MEETINGS — scoped styles ===== */
#v-meetings, #v-vm {
  --bg: #ffffff; --surface: #f8f9fc; --surface2: #f0f2f7; --surface3: #e8ebf3;
  --border: rgba(0,0,0,0.08); --border2: rgba(0,0,0,0.14);
  --text: #1a1d2e; --muted: #7a7f94; --muted2: #4a4f66;
  --accent: #3b7ef0; --green: #1eb866; --red: #e03535; --amber: #d4880a; --purple: #7c5ce4;
  --green-dim: rgba(30,184,102,0.10); --red-dim: rgba(224,53,53,0.10);
  --amber-dim: rgba(212,136,10,0.10); --accent-dim: rgba(59,126,240,0.10);
  background: #ffffff; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; color: #1a1d2e; padding: 24px 28px 60px;
}
#v-meetings *, #v-vm * { box-sizing: border-box; }
"""

# Process index.html CSS:
# 1. Remove :root { ... } block
# 2. Remove body { ... } line
# 3. Prefix each top-level selector with #v-meetings and #v-vm
idx_css = idx_css_raw

# Remove :root { ... } block
idx_css = re.sub(r':root\s*\{[^}]*\}', '', idx_css, flags=re.DOTALL)

# Remove body { ... } line
idx_css = re.sub(r'^body\{[^\n]*\n?', '', idx_css, flags=re.MULTILINE)

# Remove *,*::before,*::after{ ... } (already handled by #v-meetings *, #v-vm *)
idx_css = re.sub(r'^\*,\*::[^{]+\{[^\n]*\n?', '', idx_css, flags=re.MULTILINE)

# Replace #tab-vm with #v-vm in selectors
idx_css = idx_css.replace('#tab-vm', '#v-vm')

# Prefix ALL top-level selectors using a brace-depth-tracking parser.
# Handles minified CSS with multiple rules per line (e.g. ".a{...}.b{...}").
def scope_css(css, prefixes=('#v-meetings', '#v-vm')):
    """Walk CSS char-by-char, tracking brace depth.
    At depth=0, accumulate selector text; when we hit '{', emit prefixed selector.
    At depth>0, emit content verbatim.  Skip @-rules and :root blocks entirely."""
    out = []
    depth = 0
    sel_buf = []       # accumulates selector chars at depth==0
    i = 0
    n = len(css)
    while i < n:
        c = css[i]
        if depth == 0:
            if c == '{':
                sel = ''.join(sel_buf).strip()
                sel_buf = []
                if not sel or sel.startswith('@') or sel.startswith(':root'):
                    # Emit as-is; skip until matching }
                    out.append(sel + '{')
                    depth = 1
                else:
                    # Prefix every comma-separated part
                    parts = [p.strip() for p in sel.split(',') if p.strip()]
                    expanded = []
                    for p in parts:
                        for pfx in prefixes:
                            # Avoid double-prefixing #v-vm
                            if p.startswith('#v-vm') or p.startswith('#v-meetings'):
                                expanded.append(p)
                                break
                            else:
                                expanded.append(f'{pfx} {p}')
                    out.append(', '.join(expanded) + ' {')
                    depth = 1
            elif c == '}':
                # Stray } at depth 0 — emit verbatim
                sel_buf = []
                out.append(c)
            else:
                sel_buf.append(c)
        else:
            out.append(c)
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
        i += 1
    return ''.join(out)

idx_css = scope_css(idx_css)

# Fix double-prefixing of #v-vm (replace #v-meetings #v-vm with #v-vm)
idx_css = idx_css.replace('#v-meetings #v-vm', '#v-vm')
idx_css = idx_css.replace('#v-vm #v-vm', '#v-vm')

ma_css_addition = ma_css_vars + '\n' + idx_css

# ─────────────────────────────────────────
# C2. Nav tab additions
# ─────────────────────────────────────────
# Original: <div class="nav-tab active">Overview</div>
# Replace with 3 tabs using data-view attributes and onclick=switchView(...)
new_nav_tabs = (
    '<div class="nav-tab active" data-view="overview" onclick="switchView(\'overview\')">CFD Overview</div>\n'
    '  <div class="nav-tab" data-view="meetings" onclick="switchView(\'meetings\')">Meetings Audit</div>\n'
    '  <div class="nav-tab" data-view="vm" onclick="switchView(\'vm\')">Verified Meetings</div>'
)
cfd = cfd.replace(
    '<div class="nav-tab active">Overview</div>',
    new_nav_tabs
)

# ─────────────────────────────────────────
# C3. Rename IDs in tab-overview content
# ─────────────────────────────────────────
id_renames = {
    '"dateFrom"': '"ma_dateFrom"',
    '"dateTo"': '"ma_dateTo"',
    '"calReset"': '"ma_calReset"',
    '"mgrDropdown"': '"ma_mgrDropdown"',
    '"mgrTrigger"': '"ma_mgrTrigger"',
    '"mgrTriggerLabel"': '"ma_mgrTriggerLabel"',
    '"mgrPanel"': '"ma_mgrPanel"',
    '"mgrAllBtn"': '"ma_mgrAllBtn"',
    '"mgrList"': '"ma_mgrList"',
    '"filterSummary"': '"ma_filterSummary"',
    '"kTotal"': '"ma_kTotal"',
    '"kVerified"': '"ma_kVerified"',
    '"kReviewed"': '"ma_kReviewed"',
    '"kFake"': '"ma_kFake"',
    '"kTotalPill"': '"ma_kTotalPill"',
    '"kVerifiedPill"': '"ma_kVerifiedPill"',
    '"kReviewedPill"': '"ma_kReviewedPill"',
    '"kFakePill"': '"ma_kFakePill"',
    '"kReviewedSub"': '"ma_kReviewedSub"',
    '"fTotal"': '"ma_fTotal"',
    '"fVerified"': '"ma_fVerified"',
    '"fReviewed"': '"ma_fReviewed"',
    '"fLegit"': '"ma_fLegit"',
    '"fFake"': '"ma_fFake"',
    '"fVerifiedPct"': '"ma_fVerifiedPct"',
    '"fReviewedPct"': '"ma_fReviewedPct"',
    '"fLegitPct"': '"ma_fLegitPct"',
    '"fFakePct"': '"ma_fFakePct"',
    '"bar2insights"': '"ma_bar2insights"',
    '"dualAxis"': '"ma_dualAxis"',
    '"mgrTrendLegend"': '"ma_mgrTrendLegend"',
    '"mgrTrendChart"': '"ma_mgrTrendChart"',
    '"mgrOverviewBody"': '"ma_mgrOverviewBody"',
    '"matrixBody"': '"ma_matrixBody"',
}

tab_overview_renamed = tab_overview_content
for old, new in id_renames.items():
    tab_overview_renamed = tab_overview_renamed.replace(old, new)

# ─────────────────────────────────────────
# C4. Build HTML additions
# ─────────────────────────────────────────
html_additions = f"""

<!-- ==================== MEETINGS AUDIT ==================== -->
<div id="v-meetings" class="view">
{csv_header_html}
{tab_overview_renamed}
</div>

<!-- ==================== VERIFIED MEETINGS ==================== -->
<div id="v-vm" class="view">
{tab_vm_content}
</div>
"""

# ─────────────────────────────────────────
# C5. Build JS additions
# ─────────────────────────────────────────

# Apply renames to js_functions_raw
js = js_functions_raw

# Step 1: Rename function names FIRST
func_renames = [
    ('function update()', 'function ma_update()'),
    ('function renderMgrOverview(', 'function ma_renderMgrOverview('),
    ('function renderMatrix(', 'function ma_renderMatrix('),
    ('function trendLine(', 'function ma_trendLine('),
    ('function updateMgrTriggerLabel(', 'function ma_updateMgrTriggerLabel('),
    ('function buildMgrList(', 'function ma_buildMgrList('),
    ('function getWeekStart(', 'function ma_getWeekStart('),
    ('function getVisibleWeeks(', 'function ma_getVisibleWeeks('),
    ('function computeScWeekData(', 'function ma_computeScWeekData('),
]
for old, new in func_renames:
    js = js.replace(old, new)

# Step 2: Rename element IDs in getElementById calls
elem_renames = [
    ("getElementById('dualAxis')", "getElementById('ma_dualAxis')"),
    ("getElementById('mgrTrendChart')", "getElementById('ma_mgrTrendChart')"),
    ("getElementById('mgrTrendLegend')", "getElementById('ma_mgrTrendLegend')"),
    ("getElementById('mgrOverviewBody')", "getElementById('ma_mgrOverviewBody')"),
    ("getElementById('matrixBody')", "getElementById('ma_matrixBody')"),
    ("getElementById('bar2insights')", "getElementById('ma_bar2insights')"),
    ("getElementById('kTotal')", "getElementById('ma_kTotal')"),
    ("getElementById('kVerified')", "getElementById('ma_kVerified')"),
    ("getElementById('kReviewed')", "getElementById('ma_kReviewed')"),
    ("getElementById('kFake')", "getElementById('ma_kFake')"),
    ("getElementById('kTotalPill')", "getElementById('ma_kTotalPill')"),
    ("getElementById('kVerifiedPill')", "getElementById('ma_kVerifiedPill')"),
    ("getElementById('kReviewedPill')", "getElementById('ma_kReviewedPill')"),
    ("getElementById('kReviewedSub')", "getElementById('ma_kReviewedSub')"),
    ("getElementById('kFakePill')", "getElementById('ma_kFakePill')"),
    ("getElementById('fTotal')", "getElementById('ma_fTotal')"),
    ("getElementById('fVerified')", "getElementById('ma_fVerified')"),
    ("getElementById('fReviewed')", "getElementById('ma_fReviewed')"),
    ("getElementById('fLegit')", "getElementById('ma_fLegit')"),
    ("getElementById('fFake')", "getElementById('ma_fFake')"),
    ("getElementById('fVerifiedPct')", "getElementById('ma_fVerifiedPct')"),
    ("getElementById('fReviewedPct')", "getElementById('ma_fReviewedPct')"),
    ("getElementById('fLegitPct')", "getElementById('ma_fLegitPct')"),
    ("getElementById('fFakePct')", "getElementById('ma_fFakePct')"),
    ("getElementById('filterSummary')", "getElementById('ma_filterSummary')"),
    ("getElementById('mgrList')", "getElementById('ma_mgrList')"),
    ("getElementById('mgrAllBtn')", "getElementById('ma_mgrAllBtn')"),
    ("getElementById('mgrTrigger')", "getElementById('ma_mgrTrigger')"),
    ("getElementById('mgrPanel')", "getElementById('ma_mgrPanel')"),
    ("getElementById('mgrDropdown')", "getElementById('ma_mgrDropdown')"),
    ("getElementById('dateFrom')", "getElementById('ma_dateFrom')"),
    ("getElementById('dateTo')", "getElementById('ma_dateTo')"),
    ("getElementById('calReset')", "getElementById('ma_calReset')"),
    ("getElementById('mgrTriggerLabel')", "getElementById('ma_mgrTriggerLabel')"),
]
for old, new in elem_renames:
    js = js.replace(old, new)

# Step 3: Variable renames using word boundaries
var_renames = [
    (r'\bselMgrs\b', 'ma_selMgrs'),
    (r'\brangeStart\b', 'ma_rangeStart'),
    (r'\brangeEnd\b', 'ma_rangeEnd'),
    (r'\bALL_MGRS\b', 'ma_ALL_MGRS'),
    (r'\blastFiltered\b', 'ma_lastFiltered'),
    (r'\bch2\b', 'ma_ch2'),
    (r'\bch4\b', 'ma_ch4'),
    (r'\bmgrTrendHidden\b', 'ma_mgrTrendHidden'),
    (r'\bgetWeekStart\b', 'ma_getWeekStart'),
    (r'\bgetVisibleWeeks\b', 'ma_getVisibleWeeks'),
    (r'\bcomputeScWeekData\b', 'ma_computeScWeekData'),
    (r'\bALL_WEEKS\b', 'ma_ALL_WEEKS'),
    (r'\bDATA_DATES\b', 'ma_DATA_DATES'),
]
for pattern, replacement in var_renames:
    js = re.sub(pattern, replacement, js)

# Fix: make sure ma_ch4.update() doesn't become ma_ch4.ma_update()
# The .update() is a Chart.js method call on a chart instance, not our function
# After variable rename, any remaining `.update()` calls that were `.update()`
# before should stay as `.update()`. Our function is `ma_update()` standalone.
# Fix: revert `.ma_update()` back to `.update()` when it's a method call (preceded by .)
js = re.sub(r'\.ma_update\(\)', '.update()', js)
js = re.sub(r'\.ma_trendLine\b', '.trendLine', js)  # trendLine is not renamed as a method

# Also rename internal calls to the renamed functions
js = re.sub(r'\bupdate\(\)', 'ma_update()', js)
# But don't rename Chart.js .update() — already fixed above
# Don't rename renderMgrOverview, renderMatrix, trendLine, updateMgrTriggerLabel, buildMgrList calls
# They are already covered by the function rename + \b pattern
# Actually let's rename the call sites too:
call_renames = [
    (r'\brenderMgrOverview\(', 'ma_renderMgrOverview('),
    (r'\brenderMatrix\(', 'ma_renderMatrix('),
    (r'\btrendLine\(', 'ma_trendLine('),
    (r'\bupdateMgrTriggerLabel\(', 'ma_updateMgrTriggerLabel('),
    (r'\bbuildMgrList\(', 'ma_buildMgrList('),
]
for pattern, replacement in call_renames:
    js = re.sub(pattern, replacement, js)

# Fix again: .update() method calls should not be ma_update()
js = re.sub(r'\.ma_update\(\)', '.update()', js)

# Fix: renderCal() was stripped; remove orphaned calls in applyDataset (CSV upload path)
js = js.replace('ma_buildMgrList();ma_updateMgrTriggerLabel();renderCal();ma_update();',
                'ma_buildMgrList();ma_updateMgrTriggerLabel();ma_update();')

# ─────────────────────────────────────────
# Build state vars for MA (renamed)
# ─────────────────────────────────────────
ma_state_vars_js = """
// ═══════════════════════════════════════════════
// MEETINGS AUDIT — STATE
// ═══════════════════════════════════════════════
let ma_selMgrs = new Set();
let ma_rangeStart = null, ma_rangeEnd = null;
let ma_ch2 = null, ma_ch4 = null;
let ma_lastFiltered = [];
let ma_mgrTrendHidden = new Set();
const ma_ALL_MGRS = [...new Set(RAW.map(r=>r.manager))].filter(m=>m&&m!=='-'&&m!=='nan').sort();
const ma_DATA_DATES = new Set(RAW.map(r=>r.date));
// Note: ma_ALL_WEEKS is defined in the extracted MA JS below (renamed from ALL_WEEKS)
"""

# ─────────────────────────────────────────
# Build ma_init() function
# ─────────────────────────────────────────
ma_init_js = """
function ma_init() {
  const today = new Date();
  const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  const yesterday = new Date(today); yesterday.setDate(today.getDate()-1);
  const isoDate = d => d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
  ma_rangeStart = isoDate(firstOfMonth);
  ma_rangeEnd = isoDate(yesterday);
  ma_selMgrs = new Set(ma_ALL_MGRS);
  ma_buildMgrList();
  ma_updateMgrTriggerLabel();
  document.getElementById('ma_dateFrom').value = ma_rangeStart;
  document.getElementById('ma_dateTo').value = ma_rangeEnd;
  document.getElementById('ma_dateFrom').addEventListener('change', function(){ ma_rangeStart = this.value||null; ma_update(); });
  document.getElementById('ma_dateTo').addEventListener('change', function(){ ma_rangeEnd = this.value||null; ma_update(); });
  document.getElementById('ma_calReset').addEventListener('click', function(){ ma_rangeStart=null; ma_rangeEnd=null; document.getElementById('ma_dateFrom').value=''; document.getElementById('ma_dateTo').value=''; ma_update(); });
  const mgrTrig = document.getElementById('ma_mgrTrigger');
  const mgrPnl = document.getElementById('ma_mgrPanel');
  mgrTrig.addEventListener('click', e=>{ e.stopPropagation(); mgrTrig.classList.toggle('open'); mgrPnl.classList.toggle('open'); });
  document.addEventListener('click', e=>{ if(!document.getElementById('ma_mgrDropdown').contains(e.target)){ mgrTrig.classList.remove('open'); mgrPnl.classList.remove('open'); }});
  document.getElementById('ma_mgrAllBtn').addEventListener('click', ()=>{ ma_selMgrs.size===ma_ALL_MGRS.length?ma_selMgrs.clear():ma_selMgrs=new Set(ma_ALL_MGRS); ma_buildMgrList(); ma_updateMgrTriggerLabel(); ma_update(); });
  ma_update();
  ma_csvInit();
}
"""

# ─────────────────────────────────────────
# switchView + admin stubs
# ─────────────────────────────────────────
switch_view_js = """
// ═══════════════════════════════════════════════
// MEETINGS AUDIT — VIEW SWITCHER
// ═══════════════════════════════════════════════
function switchView(v) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.toggle('active', t.dataset.view === v));
  document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
  document.getElementById('v-' + v).classList.add('active');
  if (v === 'meetings' && !_maInited) { _maInited = true; ma_init(); }
  if (v === 'vm' && !_vmInited) { _vmInited = true; vm_init(); }
}
let _maInited = false, _vmInited = false;

// Admin role stubs (no login screen in CFD)
const DASH_ROLE = 'admin';
const DASH_TEAM = null;
function dashFilterData(data) { return data; }
"""

# ─────────────────────────────────────────
# Full JS addition block
# ─────────────────────────────────────────
js_addition = f"""
// ═══════════════════════════════════════════════
// MEETINGS AUDIT DATA CONSTANTS
// ═══════════════════════════════════════════════
{data_constants_js}

{switch_view_js}

{ma_state_vars_js}

{ma_init_js}

// ═══════════════════════════════════════════════
// MEETINGS AUDIT FUNCTIONS (renamed)
// ═══════════════════════════════════════════════
{js}
"""

# ─────────────────────────────────────────
# D. Insert additions into CFD
# ─────────────────────────────────────────

# D1. Insert CSS before </style>
if '</style>' not in cfd:
    raise ValueError("Could not find </style> in CFD")
cfd = cfd.replace('</style>', ma_css_addition + '\n</style>', 1)

# D2. Insert extra CDN scripts for Choices.js, date-fns adapter, and DM Sans font (needed by MA/VM tabs)
cdn_scripts = """<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/choices.js@10.2.0/public/assets/scripts/choices.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/choices.js@10.2.0/public/assets/styles/choices.min.css">
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>"""
# Insert after the existing chart.js script line
cfd = cfd.replace(
    '<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>',
    '<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>\n' + cdn_scripts
)

# D3. Insert HTML additions after the closing </div> of #v-overview
# The v-overview div is: <div id="v-overview" class="view active">...</div>
# We need to find the closing </div> of v-overview
# Strategy: find the last occurrence before the </body> that closes the view
# The structure ends: </div>\n\n<script>
# Let's insert after </div>\n\n<script> boundary won't work...
# Actually find the pattern: after v-overview there's \n\n<script>
# So insert just before the <script> tag that starts the JS

# Find position of the main </script> end
# The CFD html ends: ... } </script></body></html>
# We want to insert HTML before the <script> block
script_tag_pos = cfd.rfind('<script>')
if script_tag_pos == -1:
    raise ValueError("Could not find <script> in CFD for HTML insertion")

cfd = cfd[:script_tag_pos] + html_additions + '\n\n' + cfd[script_tag_pos:]

# D4. Insert JS before </script>
last_script_close = cfd.rfind('</script>')
if last_script_close == -1:
    raise ValueError("Could not find </script> in CFD")

cfd = cfd[:last_script_close] + '\n\n' + js_addition + '\n' + cfd[last_script_close:]

# D5. Patch ChartDataLabels registration to default display:false
# This prevents the global plugin from adding unwanted labels to MA/VM charts.
# CFD charts that need it already set display:true explicitly per dataset.
cfd = cfd.replace(
    "if(typeof ChartDataLabels !== 'undefined') Chart.register(ChartDataLabels);",
    "if(typeof ChartDataLabels !== 'undefined') {\n"
    "  Chart.register(ChartDataLabels);\n"
    "  // Default off — CFD charts that need it set display:true per dataset\n"
    "  Chart.defaults.plugins.datalabels.display = false;\n"
    "}"
)

# ─────────────────────────────────────────
# E. Write output
# ─────────────────────────────────────────
print(f"\nWriting output to {OUT_PATH} ...")
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(cfd)

print(f"Done. Output size: {len(cfd):,} chars")

# ─────────────────────────────────────────
# F. Verify
# ─────────────────────────────────────────
print("\n--- VERIFICATION ---")
line_count = cfd.count('\n') + 1
print(f"Line count: {line_count}")

checks = [
    ('id="v-meetings"', 'id="v-meetings" present'),
    ('id="v-vm"', 'id="v-vm" present'),
    ('switchView', 'switchView present'),
    ('DASH_ROLE', 'DASH_ROLE present'),
    ('ma_init', 'ma_init present'),
    ('vm_init', 'vm_init present'),
]
for search, label in checks:
    count = cfd.count(search)
    print(f"  {label}: {count} occurrences")

# Check for var DASH_ROLE or var DASH_TEAM (should be 0)
bad_var = len(re.findall(r'\bvar DASH_ROLE\b|\bvar DASH_TEAM\b', cfd))
print(f"  var DASH_ROLE/DASH_TEAM occurrences (should be 0): {bad_var}")

# Check for .ma_update() method calls (should be 0)
bad_method = len(re.findall(r'\.ma_update\(\)', cfd))
print(f"  .ma_update() method calls (should be 0): {bad_method}")

if line_count < 4000:
    print(f"WARNING: Line count {line_count} is less than 4000!")
else:
    print(f"  Line count > 4000: OK")

print("\nBuild complete!")
