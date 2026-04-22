import sys
sys.path.insert(0, r'C:\Users\hamza.rizwan')
from redshift_client import run_query
import pandas as pd

pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 200)

TEAM_TO_MANAGER = {
    'Sherif - TL Jeddah':              'Sherif Hassan',
    'Khalil - TL Jeddah':              'Mohamad Ghannoum (JM3)',
    'Telesales-Abdelfattah Khaiyal':   'Sulaiman Aljurbua (TS)',
    'AbdulMajed - TL Riyadh':          'Abdulmajed Alghusen',
    'Al Khateeb - TL Riyadh':          'Abdulmajed Alghusen',
    'El-Kallas - M4':                   'Mohammad El-Kallas (M4)',
    'Telesales Manager':               'Sulaiman Aljurbua (TS)',
    'Kareem - TL Eastern':             'Mohammed Abdelkader (Eastern)',
    'Mohammed Abdelkader - Eastern':   'Mohammed Abdelkader (Eastern)',
    'Reham AL Harbi - M2':             'Reham AL Harbi (M2)',
    'Telesales - Abdullah Altamimi':   'Sulaiman Aljurbua (TS)',
    'Telesales - Sulaiman Aljurbua':   'Sulaiman Aljurbua (TS)',
    'Aminah - TL Riyadh':              'Reham AL Harbi (M2)',
    'Mohamad Ghannoum - JM3':          'Mohamad Ghannoum (JM3)',
    'Othman - TL Medina':              'Mohamad Ghannoum (JM3)',
    'Othman - TL Medina ':             'Mohamad Ghannoum (JM3)',
    'Sherif - TL Makkah':              'Sherif Hassan',
    'AlHourani - TL Riyadh':           'Mohamed Abdullah (M3)',
    'Mohamed Abdullah - M3':           'Mohamed Abdullah (M3)',
    'Alaa - JM1':                      'Alaa Alsaber (JM1)',
    'Mohammed Subhi - TL Jeddah':      'Mohammed Subhi (TL Jeddah)',
    'Rola - TL Riyadh':                'Mohammad El-Kallas (M4)',
    'Saif- M5 - Riyadh':              'Saif Alyahya (M5)',
    'Hussain - TL PK':                 'Hussain Ali (TS-PK)',
    'Mohsin - TL PK':                  'Mohsin Hassan Shah (TS-PK)',
    'Hussam El Kalache - JM1':         'Hussam El Kalache (JM1)',
    'Telesales - Abdullah Rawass':     'Sulaiman Aljurbua (TS)',
    'Najib Spiridon - M4':             'Mohammad El-Kallas (M4)',
    'Nasser Abualwafa - M1':           'Sherif Hassan',
    'Mazen Matar - JM2':              'Mohamad Ghannoum (JM3)',
    'CSD 1':                           'Mohamad Ghannoum (JM3)',
    'CSD 2':                           'Mohamad Ghannoum (JM3)',
    'CSDs Pak':                        'Hussain Ali (TS-PK)',
    'Bayut Associates':                'Sulaiman Aljurbua (TS)',
    'Online Team':                     'Online / Unattributed',
}

# CSV waterfall totals — AUTHORITATIVE for closed months (Jan-Mar)
CSV_TOTALS = {
    'Jan-26': 863716, 'Feb-26': 818460, 'Mar-26': 888913,
}
CLOSED_MONTHS = {'Jan-26', 'Feb-26', 'Mar-26'}   # scale entire month to CSV total

# For open months: old cohorts (collected before the month) are scaled to the
# Excel waterfall baseline; only the current month's new collections use DWH live.
# Apr-26: 861,553 - 26,773 (Apr-26 DWH cohort to Apr) = 834,780
# May-26 onwards: full Excel column total (no same-month cohort yet in the waterfall)
# Aug-26 to Apr-27: from updated Excel after Feb-26/Mar-26 row extensions
CSV_OLD_COHORT_TOTALS = {
    'Apr-26': 834780,
    'May-26': 815776,
    'Jun-26': 737050,
    'Jul-26': 688753,
    'Aug-26': 615539,
    'Sep-26': 523311,
    'Oct-26': 463705,
    'Nov-26': 361371,
    'Dec-26': 285984,
    'Jan-27': 188344,
    'Feb-27': 110132,
    'Mar-27':  53738,
    'Apr-27':   3643,
}

MONTHS = [
    ('Jan-26', '2026-01-01', '2026-02-01'),
    ('Feb-26', '2026-02-01', '2026-03-01'),
    ('Mar-26', '2026-03-01', '2026-04-01'),
    ('Apr-26', '2026-04-01', '2026-05-01'),
    ('May-26', '2026-05-01', '2026-06-01'),
    ('Jun-26', '2026-06-01', '2026-07-01'),
    ('Jul-26', '2026-07-01', '2026-08-01'),
    ('Aug-26', '2026-08-01', '2026-09-01'),
    ('Sep-26', '2026-09-01', '2026-10-01'),
    ('Oct-26', '2026-10-01', '2026-11-01'),
    ('Nov-26', '2026-11-01', '2026-12-01'),
    ('Dec-26', '2026-12-01', '2027-01-01'),
    ('Jan-27', '2027-01-01', '2027-02-01'),
    ('Feb-27', '2027-02-01', '2027-03-01'),
    ('Mar-27', '2027-03-01', '2027-04-01'),
    ('Apr-27', '2027-04-01', '2027-05-01'),
]

all_data = []

for mth_label, m_start, m_end in MONTHS:
    q = f"""
    WITH payments_rev AS (
        SELECT s.jarvis_id AS assignee_id,
            fp.amount * 1.0 *
                GREATEST(0, DATEDIFF('day',
                    GREATEST(dc.date_starting_nk, '{m_start}'::date),
                    LEAST(dc.date_ending_nk,      '{m_end}'::date)
                )) / DATEDIFF('day', dc.date_starting_nk, dc.date_ending_nk) AS monthly_rev,
            CASE WHEN DATE_TRUNC('month', fp.time_collected_at_local) < '{m_start}'::date
                 THEN 'old' ELSE 'new' END AS cohort_type
        FROM podl_bayutsa.fact_payments fp
        JOIN podl_bayutsa.dim_contracts dc ON fp.contract_sk = dc.contract_sk
        JOIN podl_bayutsa.dim_staff s ON dc.assignee_staff_sk = s.staff_sk
        WHERE fp.status_sk LIKE '%|372'
          AND dc.date_starting_nk IS NOT NULL AND dc.date_ending_nk IS NOT NULL
          AND dc.date_ending_nk > dc.date_starting_nk
          AND dc.date_starting_nk < '{m_end}'::date AND dc.date_ending_nk > '{m_start}'::date
          AND s.staff_sk LIKE '%bayutsa%'
          AND (fp.time_deleted_at_local IS NULL OR fp.time_deleted_at_local = '9999-12-31')
          AND fp.time_verified_at_local IS NOT NULL AND fp.time_verified_at_local != '9999-12-31'
    ),
    team_current AS (
        SELECT h.user_id, t.name AS team_name, h.operation_type,
            ROW_NUMBER() OVER (PARTITION BY h.user_id ORDER BY h.operation_timestamp DESC) AS rn
        FROM jarvis_empg.jarvis_empg__crm_team_members__history h
        JOIN jarvis_empg.jarvis_empg__crm_teams t ON h.team_id = t.id
        WHERE h.operation_timestamp < '{m_end}'::timestamp AND h.operation_type IN ('insert', 'delete')
    ),
    current_teams AS (SELECT user_id, team_name FROM team_current WHERE rn = 1 AND operation_type = 'insert'),
    team_ever AS (
        SELECT h.user_id, t.name AS team_name,
            ROW_NUMBER() OVER (PARTITION BY h.user_id ORDER BY h.operation_timestamp DESC) AS rn
        FROM jarvis_empg.jarvis_empg__crm_team_members__history h
        JOIN jarvis_empg.jarvis_empg__crm_teams t ON h.team_id = t.id
        WHERE h.operation_type = 'insert'
    ),
    last_known_teams AS (SELECT user_id, team_name FROM team_ever WHERE rn = 1)
    SELECT
        pr.assignee_id,
        COALESCE(ct.team_name, lkt.team_name, 'Truly Unassigned') AS team_name,
        pr.cohort_type,
        SUM(pr.monthly_rev) AS revenue
    FROM payments_rev pr
    LEFT JOIN current_teams ct ON pr.assignee_id = ct.user_id
    LEFT JOIN last_known_teams lkt ON pr.assignee_id = lkt.user_id AND ct.user_id IS NULL
    GROUP BY 1, 2, 3
    """
    df = run_query(q)
    dwh_total = df['revenue'].sum()

    if mth_label in CLOSED_MONTHS:
        # Scale entire month to CSV total
        csv_total = CSV_TOTALS[mth_label]
        scale_factor = csv_total / dwh_total if dwh_total > 0 else 1.0
        df['revenue'] = df['revenue'] * scale_factor
        print(f"{mth_label}: DWH={int(dwh_total):,}  CSV={csv_total:,}  scale={scale_factor:.4f} [CLOSED]")

    elif mth_label in CSV_OLD_COHORT_TOTALS:
        # Scale old cohorts (pre-month collections) to CSV baseline
        # Keep new cohort (this month's collections) as live DWH
        csv_old = CSV_OLD_COHORT_TOTALS[mth_label]
        old_mask = df['cohort_type'] == 'old'
        dwh_old = df.loc[old_mask, 'revenue'].sum()
        dwh_new = df.loc[~old_mask, 'revenue'].sum()
        scale_old = csv_old / dwh_old if dwh_old > 0 else 1.0
        df.loc[old_mask, 'revenue'] = df.loc[old_mask, 'revenue'] * scale_old
        final_total = df['revenue'].sum()
        print(f"{mth_label}: old={int(dwh_old):,} -> {int(csv_old):,} (x{scale_old:.4f})  new={int(dwh_new):,}  total={int(final_total):,} [OPEN]")

    else:
        print(f"{mth_label}: DWH={int(dwh_total):,}  [OPEN - DWH direct]")

    # Collapse cohort_type — combine old+new per assignee+team
    df = df.groupby(['assignee_id', 'team_name'])['revenue'].sum().reset_index()
    df['revenue'] = df['revenue'].round()
    df['month'] = mth_label
    df['manager'] = df['team_name'].map(TEAM_TO_MANAGER).fillna('Other: ' + df['team_name'])

    all_data.append(df)

all_df = pd.concat(all_data, ignore_index=True)

# Manager pivot
mgr_df = all_df.groupby(['manager', 'month'])['revenue'].sum().reset_index()
mgr_pivot = mgr_df.pivot(index='manager', columns='month', values='revenue').fillna(0)
month_cols = [m[0] for m in MONTHS]
mgr_pivot = mgr_pivot.reindex(columns=month_cols, fill_value=0)
mgr_pivot['Total'] = mgr_pivot.sum(axis=1)
mgr_pivot = mgr_pivot.sort_values('Jan-26', ascending=False)

# Team lead pivot
tl_df = all_df.groupby(['team_name', 'manager', 'month'])['revenue'].sum().reset_index()
tl_pivot = tl_df.pivot_table(index=['manager','team_name'], columns='month', values='revenue', aggfunc='sum').fillna(0)
tl_pivot = tl_pivot.reindex(columns=month_cols, fill_value=0)
tl_pivot['Total'] = tl_pivot.sum(axis=1)

def fmt(x): return f"{int(x):,}" if x > 0.5 else "-"

print("\n" + "="*155)
print("MANAGER BREAKDOWN — Deferred Revenue Waterfall (SAR)")
print("Jan-Mar: scaled to CSV waterfall totals (closed months)  |  Apr-27: old cohorts scaled to Excel baseline + live new-month collections")
print("="*155)
print(f"\n{'Manager':<35} " + "  ".join(f"{m:>10}" for m in month_cols) + f"  {'Total':>12}")
print("-" * 155)
for mgr, row in mgr_pivot.iterrows():
    if row['Total'] < 500:
        continue
    marker = " ***" if mgr.startswith('Other:') or mgr == 'Online / Unattributed' else ""
    print(f"{mgr:<35} " + "  ".join(f"{fmt(row[m]):>10}" for m in month_cols) + f"  {fmt(row['Total']):>12}{marker}")
print("-" * 155)
totals = mgr_pivot.sum()
print(f"{'TOTAL':<35} " + "  ".join(f"{fmt(totals[m]):>10}" for m in month_cols) + f"  {fmt(totals['Total']):>12}")
all_csv = {**CSV_TOTALS, **CSV_OLD_COHORT_TOTALS,
           'Apr-26': 861553, 'May-26': 815776, 'Jun-26': 737050, 'Jul-26': 688753}
csv_row = [all_csv.get(m, 0) for m in month_cols]
print(f"{'CSV WATERFALL':<35} " + "  ".join(f"{fmt(v):>10}" for v in csv_row))

print("\n\n" + "="*165)
print("TEAM LEAD BREAKDOWN (within each Manager)")
print("="*165)
print(f"\n{'Team Lead':<45} " + "  ".join(f"{m:>10}" for m in month_cols) + f"  {'Total':>12}")
print("-" * 165)

# Iterate managers in same order as manager breakdown
for mgr in mgr_pivot.index:
    mgr_row = mgr_pivot.loc[mgr]
    if mgr_row['Total'] < 500:
        continue
    marker = " ***" if mgr.startswith('Other:') or mgr == 'Online / Unattributed' else ""
    # Manager header row (same column format as TL rows)
    print(f"\n  {mgr:<43} " + "  ".join(f"{fmt(mgr_row[m]):>10}" for m in month_cols) + f"  {fmt(mgr_row['Total']):>12}{marker}")
    print("  " + "-" * 163)
    # TL rows under this manager, sorted by Jan-26 desc
    mgr_tls = tl_pivot.xs(mgr, level='manager') if mgr in tl_pivot.index.get_level_values('manager') else None
    if mgr_tls is not None:
        for tl, tl_row in mgr_tls.sort_values('Jan-26', ascending=False).iterrows():
            if tl_row['Total'] < 500:
                continue
            print(f"    {tl:<43} " + "  ".join(f"{fmt(tl_row[m]):>10}" for m in month_cols) + f"  {fmt(tl_row['Total']):>12}")
    # Subtotal row confirming TLs sum to manager
    tl_sub = tl_pivot.xs(mgr, level='manager').sum() if mgr in tl_pivot.index.get_level_values('manager') else None
    if tl_sub is not None:
        print("  " + "-" * 163)
        print(f"  {'  SUBTOTAL':<43} " + "  ".join(f"{fmt(tl_sub[m]):>10}" for m in month_cols) + f"  {fmt(tl_sub['Total']):>12}")

print("\n" + "=" * 165)
tl_grand = tl_pivot.groupby('month', axis=1, level=0).sum() if False else tl_pivot.reindex(columns=month_cols+['Total'], fill_value=0).sum()
print(f"{'TOTAL':<45} " + "  ".join(f"{fmt(tl_grand[m]):>10}" for m in month_cols) + f"  {fmt(tl_grand['Total']):>12}")

# Save
mgr_pivot.to_csv(r'C:\Users\hamza.rizwan\revenue_by_manager_2026.csv')
tl_pivot.to_csv(r'C:\Users\hamza.rizwan\revenue_by_tl_2026.csv')
print(f"\n\nSaved: revenue_by_manager_2026.csv, revenue_by_tl_2026.csv")
