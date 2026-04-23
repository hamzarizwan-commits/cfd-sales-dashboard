"""
Build Manager and Team Lead performance views for Jan 2026 onwards (auto-extending monthly).
Uses jarvis_empg + podl_bayutsa as data sources.
"""
import signal; signal.signal(signal.SIGINT, signal.SIG_IGN)
from redshift_client import run_query
import pandas as pd
import numpy as np
from datetime import date
from dateutil.relativedelta import relativedelta

# ============================================================
# DYNAMIC MONTH RANGE: Jan 2026 -> current month (MTD)
# ============================================================
START_YEAR, START_MONTH = 2025, 10
today = date.today()
TODAY = today.strftime('%Y-%m-%d')

# Build list of (month_num, bom_date_str, eom_date_str) from Oct 2025 to current month.
# Month numbering: Oct 2025 = -2, Nov 2025 = -1, Dec 2025 = 0, Jan 2026 = 1, Feb 2026 = 2, ...
# This lets prevMn = currMn - 1 resolve correctly (e.g. Jan -> Dec 2025 = month 0).
# Completed months use their true EOM; current month uses today as cutoff.
MONTHS = []
m = date(START_YEAR, START_MONTH, 1)
mn = -2  # Oct 2025 = -2, Nov = -1, Dec = 0, Jan 2026 = 1, ...
while m <= today.replace(day=1):
    bom = m
    eom = m + relativedelta(months=1)
    is_current = (m.year == today.year and m.month == today.month)
    # Use start of tomorrow so today's events (e.g. 2026-04-10 09:xx) are included via < cutoff
    eom_str = (today + relativedelta(days=1)).strftime('%Y-%m-%d') if is_current else eom.strftime('%Y-%m-%d')
    MONTHS.append((mn, bom.strftime('%Y-%m-%d'), eom_str))
    m = eom
    mn += 1

CURRENT_MONTH_NUM = len(MONTHS)
_DATA_START = date(START_YEAR, START_MONTH, 1).strftime('%Y-%m-%d')   # '2025-10-01'
_DATA_END   = '2026-05-01'  # calendar end of last tracked month (update if range extends)
print(f"Date range: Oct {START_YEAR} -> {today.strftime('%b %Y')} ({CURRENT_MONTH_NUM} months)")

# Build SQL months CTE rows dynamically
def build_months_cte():
    rows = []
    for i, (mn, bom, eom) in enumerate(MONTHS):
        # For the months CTE in main query, use full calendar month_end (not today)
        # so team structure lookups work correctly
        bom_d = date.fromisoformat(bom)
        eom_d = bom_d + relativedelta(months=1)
        row = f"SELECT {mn} as month_num, '{bom}'::date as month_start, '{eom_d.strftime('%Y-%m-%d')}'::date as month_end, {bom_d.year} as yr"
        if i == 0:
            rows.append(row)
        else:
            rows.append(f"UNION ALL {row}")
    return "\n    ".join(rows)

# ============================================================
# 1. TEAM STRUCTURE MAPPINGS (from PDF context doc + CSV)
# ============================================================

# team_name_en -> Manager Reporting alias
TEAM_TO_MANAGER = {
    'Sherif - TL Jeddah': 'Sherif - TL Jeddah',  # leaderless, rolls up directly
    'Khalil - TL Jeddah': 'Mohamad Ghannoum - JM3',
    'Telesales-Abdelfattah Khaiyal': 'Telesales - Sulaiman Aljurbua',
    'AbdulMajed - TL Riyadh': 'AbdulMajed - TL Riyadh',
    'Al Khateeb - TL Riyadh': 'AbdulMajed - TL Riyadh',
    'El-Kallas - M4': 'El-Kallas - M4',
    'Telesales Manager': 'Telesales - Sulaiman Aljurbua',
    'Kareem - TL Eastern': 'Mohammed Abdelkader - Eastern',
    'Mohammed Abdelkader - Eastern': 'Mohammed Abdelkader - Eastern',
    'Reham AL Harbi - M2': 'Reham AL Harbi - M2',
    'Telesales - Abdullah Altamimi': 'Telesales - Abdullah Altamimi',
    'Telesales - Sulaiman Aljurbua': 'Telesales - Sulaiman Aljurbua',
    'Aminah - TL Riyadh': 'Reham AL Harbi - M2',
    'Mohamad Ghannoum - JM3': 'Mohamad Ghannoum - JM3',
    'Othman - TL Medina': 'Mohamad Ghannoum - JM3',
    'Sherif - TL Makkah': 'Sherif - TL Makkah',
    'AlHourani - TL Riyadh': 'Mohamed Abdullah - M3',
    'Mohamed Abdullah - M3': 'Mohamed Abdullah - M3',
    'Alaa - JM1': 'Alaa - JM1',
    'Mohammed Subhi - TL Jeddah': 'Mohammed Subhi - TL Jeddah',
    'Rola - TL Riyadh': 'Rola - TL Riyadh',
    'Saif- M5 - Riyadh': 'Saif- M5 - Riyadh',
    'Hussain - TL PK': 'Hussain - TL PK',
    'Mohsin - TL PK': 'Mohsin - TL PK',
    'Hussam El Kalache - JM1': 'Hussam El Kalache - JM1',
}

# team_name_en -> TL actual name (Actual Name - Manager I)
TEAM_TO_TL_NAME = {
    'Sherif - TL Jeddah': 'Sherif Hassan',
    'Khalil - TL Jeddah': 'Khalil Barakat',
    'Telesales-Abdelfattah Khaiyal': 'Abdelfattah Khaiyal',
    'AbdulMajed - TL Riyadh': 'Abdulmajed Alghusen',
    'Al Khateeb - TL Riyadh': 'Mohammed Alkhateeb',
    'El-Kallas - M4': 'Mohammad El-Kallas',
    'Telesales Manager': 'Telesales Manager',
    'Kareem - TL Eastern': 'Kareem Saber',
    'Mohammed Abdelkader - Eastern': 'Mohammed Abdelkader',
    'Reham AL Harbi - M2': 'Reham AL Harbi',
    'Telesales - Abdullah Altamimi': 'Abdullah Altamimi',
    'Telesales - Sulaiman Aljurbua': 'Sulaiman Aljurbua',
    'Aminah - TL Riyadh': 'Aminah Alsheikhi',
    'Mohamad Ghannoum - JM3': 'Mohamad Ghannoum',
    'Othman - TL Medina': 'Othman Zaidan',
    'Sherif - TL Makkah': 'Sherif Hassan',
    'AlHourani - TL Riyadh': 'Mohammad AlHourani',
    'Alaa - JM1': 'Alaa Alsaber',
    'Mohammed Subhi - TL Jeddah': 'Mohammed Subhi',
    'Rola - TL Riyadh': 'Rola Aljaloud',
    'Hussain - TL PK': 'Hussain Ali',
    'Mohsin - TL PK': 'Mohsin Hassan Shah',
    'Hussam El Kalache - JM1': 'Hussam El Kalache',
}

# Manager Reporting -> Actual Name - Manager II
MANAGER_ALIAS_TO_NAME = {
    'Alaa - JM1': 'Alaa Alsaber',
    'El-Kallas - M4': 'Mohammad El-Kallas',
    'Mohammed Abdelkader - Eastern': 'Mohammed Abdelkader',
    'Reham AL Harbi - M2': 'Reham AL Harbi',
    'Mohamad Ghannoum - JM3': 'Mohamad Ghannoum',
    'Mohamed Abdullah - M3': 'Mohamed Abdullah',
    'AbdulMajed - TL Riyadh': 'Abdulmajed Alghusen',
    'Telesales - Sulaiman Aljurbua': 'Sulaiman Aljurbua',
    'Telesales - Abdullah Altamimi': 'Abdullah Altamimi',
    'Sherif - TL Jeddah': 'Sherif Hassan',
    'Sherif - TL Makkah': 'Sherif Hassan',
    'Mohammed Subhi - TL Jeddah': 'Mohammed Subhi',
    'Rola - TL Riyadh': 'Rola Aljaloud',
    'Saif- M5 - Riyadh': 'Saif Alyahya',
    'Hussain - TL PK': 'Hussain Ali',
    'Mohsin - TL PK': 'Mohsin Hassan Shah',
    'Hussam El Kalache - JM1': 'Hussam El Kalache',
}

# Manager Reporting -> TLs that report to them
MANAGER_TO_TLS = {
    'El-Kallas - M4': ['El-Kallas - M4', 'Rola - TL Riyadh'],
    'Mohammed Abdelkader - Eastern': ['Mohammed Abdelkader - Eastern', 'Kareem - TL Eastern'],
    'Reham AL Harbi - M2': ['Reham AL Harbi - M2', 'Aminah - TL Riyadh'],
    'Mohamad Ghannoum - JM3': ['Mohamad Ghannoum - JM3', 'Khalil - TL Jeddah', 'Othman - TL Medina'],
    'Mohamed Abdullah - M3': ['Mohamed Abdullah - M3', 'AlHourani - TL Riyadh'],
    'AbdulMajed - TL Riyadh': ['AbdulMajed - TL Riyadh', 'Al Khateeb - TL Riyadh'],
    'Telesales - Sulaiman Aljurbua': ['Telesales - Sulaiman Aljurbua', 'Telesales Manager',
                                       'Telesales-Abdelfattah Khaiyal', 'Telesales - Abdullah Altamimi'],
    'Alaa - JM1': ['Alaa - JM1'],
    'Hussam El Kalache - JM1': ['Hussam El Kalache - JM1'],
    'Sherif - TL Jeddah': ['Sherif - TL Jeddah'],
    'Sherif - TL Makkah': ['Sherif - TL Makkah'],
    'Hussain - TL PK': ['Hussain - TL PK'],
    'Mohsin - TL PK': ['Mohsin - TL PK'],
}

# TL names that are leaders (excluded from soft KPI avg)
LEADERS = set(TEAM_TO_TL_NAME.values()) | set(MANAGER_ALIAS_TO_NAME.values())

# Team type classification
TELESALES_TEAMS = {
    'Telesales - Sulaiman Aljurbua', 'Telesales - Abdullah Altamimi',
    'Telesales-Abdelfattah Khaiyal', 'Telesales Manager',
    'Hussain - TL PK', 'Mohsin - TL PK'
}

# Manager Reporting -> Region
MANAGER_REGION = {
    'Alaa - JM1': 'Jeddah',
    'El-Kallas - M4': 'Riyadh',
    'Mohammed Abdelkader - Eastern': 'Dammam',
    'Reham AL Harbi - M2': 'Riyadh',
    'Mohamad Ghannoum - JM3': 'Jeddah',
    'Mohamed Abdullah - M3': 'Riyadh',
    'AbdulMajed - TL Riyadh': 'Riyadh',
    'Telesales - Sulaiman Aljurbua': 'Telesales',
    'Telesales - Abdullah Altamimi': 'Telesales',
    'Sherif - TL Jeddah': 'Jeddah',
    'Sherif - TL Makkah': 'Makkah',
    'Mohammed Subhi - TL Jeddah': 'Jeddah',
    'Hussain - TL PK': 'Telesales',
    'Mohsin - TL PK': 'Telesales',
    'Rola - TL Riyadh': 'Riyadh',
    'Saif- M5 - Riyadh': 'Riyadh',
    'Hussam El Kalache - JM1': 'Jeddah',
}

# Team-level region overrides: applied on top of MANAGER_REGION for teams whose
# region differs from their manager's region (e.g. Medina TL reports to Jeddah manager).
TEAM_REGION_OVERRIDE = {
    'Othman - TL Medina': 'Medina',
}

# ============================================================
# 2. PULL CONSULTANT-LEVEL DATA (Jan 2026 -> current month MTD)
# ============================================================

print(f"Pulling consultant-level data for Jan {START_YEAR} to {today.strftime('%b %Y')} MTD...")

# ---- Single query: month-end team for roster/targets/packages/renewals,
# ---- team-period split for calls/collections/meetings/verified meetings ----
query = f"""
WITH months AS (
    {build_months_cte()}
),
-- Team periods: only use insert/delete for boundaries (NaN = updates, not team changes)
team_periods AS (
    SELECT h.user_id, h.team_id, t.name as team_name,
        h.operation_timestamp as period_start,
        LEAD(h.operation_timestamp) OVER (PARTITION BY h.user_id ORDER BY h.operation_timestamp) as period_end,
        h.operation_type
    FROM jarvis_empg.jarvis_empg__crm_team_members__history h
    JOIN jarvis_empg.jarvis_empg__crm_teams t ON h.team_id = t.id
    WHERE h.operation_type IN ('insert', 'delete')
),
-- Active periods = insert records (period ends at next insert/delete)
active_periods AS (
    SELECT user_id, team_id, team_name, period_start, period_end
    FROM team_periods
    WHERE operation_type = 'insert'
),
-- Staff base info
staff_base AS (
    SELECT DISTINCT
        s.email as staff_email, s.staff_name_en,
        CASE WHEN s.is_active = 1 THEN 'Active' ELSE 'Inactive' END as status,
        s.date_leaving_nk as last_working_date, s.date_joining_nk as doj,
        s.jarvis_id, s.staff_sk, u.deactivated_at,
        s.designation
    FROM podl_bayutsa.dim_staff s
    LEFT JOIN jarvis_empg.jarvis_empg__crm_users u ON s.jarvis_id = u.id
    WHERE s.email IS NOT NULL AND s.email != ''
    AND s.staff_sk LIKE '%bayutsa%' AND s.email LIKE '%@bayut.sa'
),
-- For each staff+month, find team at month-end (latest record must be 'insert', not 'delete')
team_at_month_end AS (
    SELECT h.user_id, h.team_id, m.month_num, t.name as team_name_en, h.operation_type,
        ROW_NUMBER() OVER (PARTITION BY h.user_id, m.month_num ORDER BY h.operation_timestamp DESC) as rn
    FROM jarvis_empg.jarvis_empg__crm_team_members__history h
    JOIN jarvis_empg.jarvis_empg__crm_teams t ON h.team_id = t.id
    CROSS JOIN months m
    WHERE h.operation_timestamp < m.month_end
    AND h.operation_type IN ('insert', 'delete')
),
month_end_teams AS (
    SELECT user_id, team_id, month_num, team_name_en
    FROM team_at_month_end WHERE rn = 1 AND operation_type = 'insert'
),
-- For each staff+month, find team at BOM (6th of month) for targets
team_at_bom AS (
    SELECT h.user_id, h.team_id, m.month_num, t.name as bom_team_name, h.operation_type,
        ROW_NUMBER() OVER (PARTITION BY h.user_id, m.month_num ORDER BY h.operation_timestamp DESC) as rn
    FROM jarvis_empg.jarvis_empg__crm_team_members__history h
    JOIN jarvis_empg.jarvis_empg__crm_teams t ON h.team_id = t.id
    CROSS JOIN months m
    WHERE h.operation_timestamp < (m.month_start + INTERVAL '7 days')
    AND h.operation_type IN ('insert', 'delete')
),
bom_teams AS (
    SELECT user_id, team_id, month_num, bom_team_name
    FROM team_at_bom WHERE rn = 1 AND operation_type = 'insert'
),
-- CALLS: split by team at time of call
calls_by_team AS (
    SELECT s.jarvis_id, s.staff_sk, s.staff_email, s.staff_name_en,
        ap.team_name, m.month_num,
        COUNT(*) as calls_count,
        COUNT(DISTINCT c.account_sk) as unique_calls,
        SUM(CASE WHEN c.connected_duration >= 60 THEN 1 ELSE 0 END) as total_qualified_calls,
        COUNT(DISTINCT CASE WHEN c.connected_duration >= 60 THEN c.account_sk END) as unique_qualified_calls,
        SUM(CASE WHEN c.calltracking_status_sk LIKE '%541' THEN 1 ELSE 0 END) as rejected_calls,
        SUM(CASE WHEN c.calltracking_status_sk LIKE '%544' THEN 1 ELSE 0 END) as unanswered_calls,
        COUNT(*) - SUM(CASE WHEN c.connected_duration >= 60 THEN 1 ELSE 0 END) as non_qualified_calls,
        ROUND(SUM(c.connected_duration) / 60.0, 4) as total_talk_time
    FROM podl_bayutsa.fact_calltracking_staff_logs c
    JOIN staff_base s ON c.staff_sk = s.staff_sk
    JOIN active_periods ap ON s.jarvis_id = ap.user_id
        AND c.time_call_started_local >= ap.period_start
        AND (ap.period_end IS NULL OR c.time_call_started_local < ap.period_end)
    JOIN months m ON c.date_call_nk >= m.month_start AND c.date_call_nk < m.month_end
    WHERE c.call_type IN ('in', 'out') AND c.account_sk != 'unknown'
    GROUP BY s.jarvis_id, s.staff_sk, s.staff_email, s.staff_name_en, ap.team_name, m.month_num
),
-- COLLECTIONS: split by team at time of payment
collections_by_team AS (
    SELECT s.jarvis_id, ap.team_name, m.month_num,
        SUM(p.net_amount) as collections_achieved
    FROM jarvis_empg.jarvis_empg__crm_payments p
    JOIN staff_base s ON p.collected_by_id = s.jarvis_id
    JOIN active_periods ap ON s.jarvis_id = ap.user_id
        AND p.collected_at >= ap.period_start
        AND (ap.period_end IS NULL OR p.collected_at < ap.period_end)
    JOIN months m ON p.collected_at >= m.month_start AND p.collected_at < m.month_end
    WHERE (p.operation_type IS NULL OR p.operation_type != 'delete') AND p.deleted_at IS NULL
    GROUP BY s.jarvis_id, ap.team_name, m.month_num
),
-- MEETINGS: split by team at time of meeting
meetings_by_team AS (
    SELECT m2.assignee_id, ap.team_name, m.month_num,
        COUNT(*) as total_meetings
    FROM jarvis_empg.jarvis_empg__crm_meetings m2
    JOIN active_periods ap ON m2.assignee_id = ap.user_id
        AND m2.start_date >= ap.period_start
        AND (ap.period_end IS NULL OR m2.start_date < ap.period_end)
    JOIN months m ON m2.start_date >= m.month_start AND m2.start_date < m.month_end
    WHERE (m2.operation_type IS NULL OR m2.operation_type != 'delete')
    GROUP BY m2.assignee_id, ap.team_name, m.month_num
),
-- VERIFIED MEETINGS: split by team at time of achievement
verified_by_team AS (
    SELECT ts.user_id, ap.team_name, m.month_num,
        COUNT(*) as verified_meetings,
        COUNT(DISTINCT task.client_id) as unique_verified_meetings
    FROM jarvis_empg.jarvis_empg__crm_target_summaries ts
    JOIN jarvis_empg.jarvis_empg__crm_tasks task ON ts.achievable_id = task.id
        AND (task.operation_type IS NULL OR task.operation_type != 'delete')
    JOIN active_periods ap ON ts.user_id = ap.user_id
        AND ts.achieved_at >= ap.period_start
        AND (ap.period_end IS NULL OR ts.achieved_at < ap.period_end)
    JOIN months m ON ts.achieved_at >= m.month_start AND ts.achieved_at < m.month_end
    WHERE (ts.operation_type IS NULL OR ts.operation_type != 'delete')
    AND ts.target_type_id = 115
    GROUP BY ts.user_id, ap.team_name, m.month_num
),
-- Monthly metrics use month-end team (targets, roster, packages, renewals)
roster AS (
    SELECT r.staff_sk, m.month_num,
        COUNT(CASE WHEN r.roster_status_l1_nk = 'on' THEN 1 END) as days_worked
    FROM podl_bayutsa.fact_staff_roster r
    JOIN months m ON r.date_nk >= m.month_start
                 AND r.date_nk < LEAST(m.month_end, CURRENT_DATE + INTERVAL '1 day')
    GROUP BY r.staff_sk, m.month_num
),
-- TARGETS: collection target from crm_targets, net gain target from crm_targets,
-- but net gain ACHIEVED from crm_clients__history (Active clients EOM - BOM)
-- Net gain achieved computed separately via Python post-processing
targets AS (
    SELECT t.user_id, m.month_num,
        MAX(CASE WHEN t.target_type_id = 109 THEN t.assigned END) as collection_target,
        0 as client_net_gain_achieved,
        MAX(CASE WHEN t.target_type_id = 122 THEN t.assigned END) as client_net_gain_target
    FROM jarvis_empg.jarvis_empg__crm_targets t
    JOIN months m ON t.due_date >= m.month_start AND t.due_date < m.month_end
    WHERE (t.operation_type IS NULL OR t.operation_type != 'delete')
    AND t.due_date >= '{_DATA_START}' AND t.due_date < '{_DATA_END}'
    AND t.target_type_id IN (109, 122)
    GROUP BY t.user_id, m.month_num
),
packages AS (
    SELECT c.assignee_staff_sk as staff_sk, m.month_num,
        COUNT(*) as packages_sold,
        ROUND(SUM(c.discount_value) / NULLIF(SUM(c.net_contract_value), 0), 4) as discounted_pct
    FROM podl_bayutsa.dim_contracts c
    JOIN months m ON c.date_sign_nk >= m.month_start AND c.date_sign_nk < m.month_end
    WHERE c.contract_category_sk NOT LIKE '%82' AND c.contract_category_sk NOT LIKE '%89'
    GROUP BY c.assignee_staff_sk, m.month_num
),
-- Pending renewals: Jarvis CRM logic (matches Jarvis pipeline view).
-- Takes the latest trackable contract per active Field/Tele Sales client (CDC dedup).
-- Buckets by end_date month. Excludes clients with a follow-up contract
-- (has_future: another contract starting >= this contract's end_date;
--  has_overlap: another contract that straddles end_date).
-- Attributed to current assignee_id on the client record.
jrv_latest_client AS (
    SELECT id AS cl_id, sales_channel_id, assignee_id, is_active,
           ROW_NUMBER() OVER (PARTITION BY id ORDER BY inserted_date DESC) AS rn
    FROM jarvis_empg.jarvis_empg__crm_clients
    WHERE tenant_id = 8
),
jrv_trackable AS (
    SELECT c.client_id, c.id AS contract_id,
           c.start_date::date AS start_date,
           c.end_date::date   AS end_date
    FROM jarvis_empg.jarvis_empg__crm_contracts c
    WHERE c.operation_type IS NULL AND c.is_trackable = 1 AND c.tenant_id = 8
      AND c.is_draft = FALSE AND c.deleted_at IS NULL
      AND c.status_id NOT IN (399, 401)
),
jrv_latest_contract AS (
    SELECT cl.cl_id AS client_id, cl.assignee_id,
           at.contract_id, at.end_date,
           ROW_NUMBER() OVER (PARTITION BY cl.cl_id ORDER BY at.end_date DESC) AS rn
    FROM jrv_latest_client cl
    JOIN jrv_trackable at ON at.client_id = cl.cl_id
    WHERE cl.rn = 1 AND cl.sales_channel_id IN (20, 21) AND cl.is_active = 1
),
jrv_coverage AS (
    SELECT l.client_id, l.assignee_id, l.end_date,
           MAX(CASE WHEN t2.start_date >= l.end_date THEN 1 ELSE 0 END) AS has_future,
           MAX(CASE WHEN t2.start_date <= l.end_date
                     AND t2.end_date   >  l.end_date THEN 1 ELSE 0 END) AS has_overlap
    FROM jrv_latest_contract l
    LEFT JOIN jrv_trackable t2
           ON t2.client_id = l.client_id AND t2.contract_id != l.contract_id
    WHERE l.rn = 1
    GROUP BY l.client_id, l.assignee_id, l.end_date
),
pending_ren AS (
    SELECT s.staff_sk, m.month_num,
           COUNT(DISTINCT cov.client_id) AS pending_renewal_clients
    FROM jrv_coverage cov
    JOIN months m ON cov.end_date >= m.month_start AND cov.end_date < m.month_end
    JOIN podl_bayutsa.dim_staff s ON cov.assignee_id = s.jarvis_id
    WHERE cov.has_future = 0 AND cov.has_overlap = 0
    GROUP BY s.staff_sk, m.month_num
),
renewed_ren AS (
    SELECT c.assignee_staff_sk as staff_sk, m.month_num,
        COUNT(DISTINCT c.account_sk) as renewed_clients
    FROM podl_bayutsa.dim_contracts c
    JOIN months m ON c.date_sign_nk >= m.month_start AND c.date_sign_nk < m.month_end
    WHERE c.contract_category_sk LIKE '%43'
    GROUP BY c.assignee_staff_sk, m.month_num
),
-- Get all distinct team+month combinations per user from event-level data
all_user_team_months AS (
    SELECT jarvis_id, staff_sk, team_name, month_num FROM calls_by_team
    UNION SELECT jarvis_id, NULL, team_name, month_num FROM collections_by_team
    UNION SELECT assignee_id, NULL, team_name, month_num FROM meetings_by_team
    UNION SELECT user_id, NULL, team_name, month_num FROM verified_by_team
),
-- Also include month-end team for users with no events but have targets/roster
all_user_months AS (
    SELECT user_id as jarvis_id, team_name_en as team_name, month_num FROM month_end_teams
    UNION
    SELECT jarvis_id, team_name, month_num FROM all_user_team_months
)
SELECT
    sb.staff_email, sb.staff_name_en, sb.jarvis_id, sb.status,
    aum.team_name as team_name_en,
    sb.last_working_date, m.month_num as month, m.yr as year, sb.doj,
    sb.deactivated_at, m.month_end, sb.designation,
    -- Monthly metrics only on month-end team row
    CASE WHEN aum.team_name = met.team_name_en THEN COALESCE(r.days_worked, 0) ELSE 0 END as days_worked,
    COALESCE(cbt.collections_achieved, 0) as collections_achieved,
    CASE WHEN aum.team_name = met.team_name_en THEN COALESCE(tg.collection_target, 0) ELSE 0 END as collection_target,
    CASE WHEN aum.team_name = met.team_name_en THEN COALESCE(tg.client_net_gain_achieved, 0) ELSE 0 END as client_net_gain_achieved,
    CASE WHEN aum.team_name = met.team_name_en THEN COALESCE(tg.client_net_gain_target, 0) ELSE 0 END as client_net_gain_target,
    COALESCE(ct.calls_count, 0) as calls_count,
    COALESCE(ct.unique_calls, 0) as unique_calls,
    COALESCE(ct.total_qualified_calls, 0) as total_qualified_calls,
    COALESCE(ct.unique_qualified_calls, 0) as unique_qualified_calls,
    COALESCE(ct.non_qualified_calls, 0) as non_qualified_calls,
    COALESCE(ct.rejected_calls, 0) as rejected_calls,
    COALESCE(ct.unanswered_calls, 0) as unanswered_calls,
    COALESCE(ct.total_talk_time, 0) as total_talk_time,
    COALESCE(mbt.total_meetings, 0) as total_meetings,
    COALESCE(vbt.verified_meetings, 0) as verified_meetings,
    COALESCE(vbt.unique_verified_meetings, 0) as unique_verified_meetings,
    COALESCE(mbt.total_meetings, 0) - COALESCE(vbt.verified_meetings, 0) as failed_meetings,
    CASE WHEN aum.team_name = met.team_name_en THEN COALESCE(pk.packages_sold, 0) ELSE 0 END as packages_sold,
    CASE WHEN aum.team_name = met.team_name_en THEN pk.discounted_pct ELSE NULL END as discounted_pct,
    CASE WHEN aum.team_name = met.team_name_en THEN COALESCE(rr.renewed_clients, 0) ELSE 0 END as renewed_clients,
    CASE WHEN aum.team_name = met.team_name_en THEN COALESCE(pr.pending_renewal_clients, 0) ELSE 0 END as pending_renewal_clients
FROM all_user_months aum
JOIN staff_base sb ON aum.jarvis_id = sb.jarvis_id
JOIN months m ON aum.month_num = m.month_num
JOIN month_end_teams met ON sb.jarvis_id = met.user_id AND aum.month_num = met.month_num
LEFT JOIN bom_teams bom ON sb.jarvis_id = bom.user_id AND aum.month_num = bom.month_num
-- Event-level metrics matched by team
LEFT JOIN calls_by_team ct ON sb.staff_sk = ct.staff_sk AND m.month_num = ct.month_num AND aum.team_name = ct.team_name
LEFT JOIN collections_by_team cbt ON sb.jarvis_id = cbt.jarvis_id AND m.month_num = cbt.month_num AND aum.team_name = cbt.team_name
LEFT JOIN meetings_by_team mbt ON sb.jarvis_id = mbt.assignee_id AND m.month_num = mbt.month_num AND aum.team_name = mbt.team_name
LEFT JOIN verified_by_team vbt ON sb.jarvis_id = vbt.user_id AND m.month_num = vbt.month_num AND aum.team_name = vbt.team_name
-- Monthly metrics (only on month-end team row)
LEFT JOIN roster r ON sb.staff_sk = r.staff_sk AND m.month_num = r.month_num
LEFT JOIN targets tg ON sb.jarvis_id = tg.user_id AND m.month_num = tg.month_num
LEFT JOIN packages pk ON sb.staff_sk = pk.staff_sk AND m.month_num = pk.month_num
LEFT JOIN pending_ren pr ON sb.staff_sk = pr.staff_sk AND m.month_num = pr.month_num
LEFT JOIN renewed_ren rr ON sb.staff_sk = rr.staff_sk AND m.month_num = rr.month_num
WHERE COALESCE(ct.calls_count,0) + COALESCE(mbt.total_meetings,0) + COALESCE(cbt.collections_achieved,0) > 0
    OR (aum.team_name = met.team_name_en AND (COALESCE(r.days_worked,0) + COALESCE(tg.collection_target,0)
        + COALESCE(pr.pending_renewal_clients,0) + COALESCE(rr.renewed_clients,0)) > 0)
ORDER BY m.month_num, sb.staff_email, aum.team_name
"""

df = run_query(query)
print(f"Consultant data: {len(df)} rows")
print(f"Month breakdown: {df.groupby('month').size().to_dict()}")

# ============================================================
# 2.45 PRO-RATE TARGETS BY WORKING DAYS PER TEAM
# ============================================================
# Working week: Sun-Thu (weekday 6,0,1,2,3). Fri(4) and Sat(5) are off.
# For consultants with multiple team rows in a month, split the monthly target
# proportionally by working days spent in each team.

from datetime import date, timedelta
from calendar import monthrange

# ============================================================
# 2.45 COMPUTE NET GAIN FROM crm_clients__history (Active EOM - Active BOM)
# ============================================================
print("\nComputing net gain from client status history...")

ng_query = """
WITH all_consultants AS (
    SELECT DISTINCT jarvis_id FROM podl_bayutsa.dim_staff
    WHERE email LIKE '%%@bayut.sa' AND staff_sk LIKE '%%bayutsa%%'
),
months AS (
    SELECT 1 as mn, '2026-01-01'::timestamp as bom, '2026-02-01'::timestamp as eom
    UNION ALL SELECT 2, '2026-02-01', '2026-03-01'
    UNION ALL SELECT 3, '2026-03-01', '2026-04-01'
    UNION ALL SELECT 4, '2026-04-01', '2026-05-01'
),
-- Active clients at BOM per assignee
bom_active AS (
    SELECT m.mn, h.assignee_id,
        COUNT(DISTINCT h.id) as active_bom
    FROM (
        SELECT h2.id, h2.assignee_id, h2.status_id,
            ROW_NUMBER() OVER (PARTITION BY h2.id ORDER BY h2.operation_timestamp DESC) as rn
        FROM jarvis_empg.jarvis_empg__crm_clients__history h2
        CROSS JOIN months m2
        WHERE h2.operation_timestamp < m2.bom
        AND h2.assignee_id IN (SELECT jarvis_id FROM all_consultants)
    ) h
    CROSS JOIN months m
    WHERE h.rn = 1 AND h.status_id = 375
    GROUP BY m.mn, h.assignee_id
),
-- Active clients at EOM per assignee
eom_active AS (
    SELECT m.mn, h.assignee_id,
        COUNT(DISTINCT h.id) as active_eom
    FROM (
        SELECT h2.id, h2.assignee_id, h2.status_id,
            ROW_NUMBER() OVER (PARTITION BY h2.id ORDER BY h2.operation_timestamp DESC) as rn
        FROM jarvis_empg.jarvis_empg__crm_clients__history h2
        CROSS JOIN months m2
        WHERE h2.operation_timestamp < m2.eom
        AND h2.assignee_id IN (SELECT jarvis_id FROM all_consultants)
    ) h
    CROSS JOIN months m
    WHERE h.rn = 1 AND h.status_id = 375
    GROUP BY m.mn, h.assignee_id
)
SELECT s.email, m.mn as month_num,
    COALESCE(eom.active_eom, 0) - COALESCE(bom.active_bom, 0) as net_gain
FROM all_consultants ac
JOIN podl_bayutsa.dim_staff s ON ac.jarvis_id = s.jarvis_id
CROSS JOIN months m
LEFT JOIN bom_active bom ON ac.jarvis_id = bom.assignee_id AND m.mn = bom.mn
LEFT JOIN eom_active eom ON ac.jarvis_id = eom.assignee_id AND m.mn = eom.mn
WHERE COALESCE(eom.active_eom, 0) - COALESCE(bom.active_bom, 0) != 0
"""

# This query is too complex for Redshift with CROSS JOIN on history.
# Use a simpler per-month approach instead.

ng_results = {}
# Correct NG logic: gain = client status went non-Active->Active (attributed to EOM assignee)
#                   loss = client status went Active->non-Active (attributed to BOM assignee)
# Transfers (Active->Active, different assignee) do NOT affect NG.
for month_num, bom_date, eom_date in MONTHS:
    ng_df = run_query(f"""
    WITH
    -- Clients touched by any bayut.sa consultant during this month (to limit scan scope)
    active_client_ids AS (
        SELECT DISTINCT h.id as client_id
        FROM jarvis_empg.jarvis_empg__crm_clients__history h
        WHERE h.operation_timestamp >= '{bom_date}' AND h.operation_timestamp < '{eom_date}'
          AND h.tenant_id = 8
          AND h.assignee_id IN (
              SELECT jarvis_id FROM podl_bayutsa.dim_staff WHERE email LIKE '%%@bayut.sa'
          )
    ),
    -- True BOM state: latest record before month start (no assignee filter)
    bom_snapshot AS (
        SELECT h.id as client_id, h.assignee_id, h.status_id,
               ROW_NUMBER() OVER (PARTITION BY h.id ORDER BY h.operation_timestamp DESC) as rn
        FROM jarvis_empg.jarvis_empg__crm_clients__history h
        JOIN active_client_ids ac ON h.id = ac.client_id
        WHERE h.operation_timestamp < '{bom_date}' AND h.tenant_id = 8
    ),
    -- True EOM state: latest record before month end (no assignee filter)
    eom_snapshot AS (
        SELECT h.id as client_id, h.assignee_id, h.status_id,
               ROW_NUMBER() OVER (PARTITION BY h.id ORDER BY h.operation_timestamp DESC) as rn
        FROM jarvis_empg.jarvis_empg__crm_clients__history h
        JOIN active_client_ids ac ON h.id = ac.client_id
        WHERE h.operation_timestamp < '{eom_date}' AND h.tenant_id = 8
    ),
    -- Gains: not Active at BOM, Active at EOM -> attributed to EOM assignee
    gains AS (
        SELECT eom.assignee_id, COUNT(DISTINCT eom.client_id) as gained
        FROM eom_snapshot eom
        LEFT JOIN bom_snapshot bom ON eom.client_id = bom.client_id AND bom.rn = 1
        WHERE eom.rn = 1 AND eom.status_id = 375
          AND (bom.status_id IS NULL OR bom.status_id != 375)
        GROUP BY eom.assignee_id
    ),
    -- Losses: Active at BOM, Lost (380) at EOM -> attributed to EOM assignee
    -- (whoever held the client when it churned, not who had it at BOM).
    -- Suspended (377) excluded — Jarvis does not treat Active->Suspended as a loss.
    losses AS (
        SELECT eom.assignee_id, COUNT(DISTINCT eom.client_id) as lost
        FROM eom_snapshot eom
        JOIN bom_snapshot bom ON eom.client_id = bom.client_id AND bom.rn = 1
        WHERE eom.rn = 1 AND eom.status_id = 380
          AND bom.status_id = 375
        GROUP BY eom.assignee_id
    )
    SELECT s.email,
           COALESCE(g.gained, 0) - COALESCE(l.lost, 0) as net_gain
    FROM podl_bayutsa.dim_staff s
    LEFT JOIN gains g ON s.jarvis_id = g.assignee_id
    LEFT JOIN losses l ON s.jarvis_id = l.assignee_id
    WHERE s.email LIKE '%%@bayut.sa'
      AND (COALESCE(g.gained, 0) - COALESCE(l.lost, 0)) != 0
    """)
    for _, r in ng_df.iterrows():
        ng_results[(r['email'], month_num)] = r['net_gain']
    print(f"  Month {month_num}: {len(ng_df)} consultants with net gain != 0")

# Apply NG to primary row only (row with highest collection per email+month).
# People who changed teams mid-month appear in multiple rows — applying NG to all
# causes double-counting. Use fully vectorized pandas operations.
unmatched_ng = {}  # (email, month_num) -> net_gain, for consultants not in main df

# Map ng_results -> Series indexed by (email, month) for vectorized merge
ng_series = pd.Series(
    {(email, int(mo)): val for (email, mo), val in ng_results.items()},
    name='ng_val'
)

# Create a lookup key column in df (use int month to match ng_series key type)
df['_ng_key'] = list(zip(df['staff_email'], df['month'].astype(int)))

# Identify rows that have an NG result
has_ng_mask = df['_ng_key'].isin(ng_series.index)

# Among those rows, find the primary index (row with max collection) per (email, month)
ng_candidates = df[has_ng_mask].copy()
primary_idx_series = ng_candidates.groupby(['staff_email', 'month'])['collections_achieved'].idxmax()
primary_indices = set(primary_idx_series.values)

# Apply NG to primary rows, zero out all other rows that have an NG key (non-primary duplicates)
df['client_net_gain_achieved'] = 0  # reset all first
for idx in primary_indices:
    key = df.at[idx, '_ng_key']
    df.at[idx, 'client_net_gain_achieved'] = ng_series[key]

df.drop(columns=['_ng_key'], inplace=True)

applied = len(primary_indices)
print(f"  NG applied to {applied} primary rows ({applied} unique email+month pairs)")

# Find ng_results keys not matched to any row (inactive/departed staff still holding clients)
df_keys = set(zip(df['staff_email'], df['month']))
for (email, month_num), ng_val in ng_results.items():
    if (email, month_num) not in df_keys:
        unmatched_ng[(email, month_num)] = ng_val

if unmatched_ng:
    print(f"  Unmatched NG entries (inactive/departed staff): {len(unmatched_ng)}")
    # Find their last known row in df (from any earlier month) to inherit team info
    extra_rows = []
    # Build a lookup of last known team from Redshift for consultants with no CSV history
    no_history_emails = [e for (e, _) in unmatched_ng if df[df['staff_email']==e].empty]
    no_history_emails = list(set(no_history_emails))
    redshift_team_lookup = {}
    if no_history_emails:
        email_list = "','".join(no_history_emails)
        team_lkp = run_query(f"""
            SELECT s.email, t.name as team_name,
                   tm.operation_timestamp,
                   ROW_NUMBER() OVER (PARTITION BY s.email ORDER BY tm.operation_timestamp DESC) as rn
            FROM podl_bayutsa.dim_staff s
            JOIN jarvis_empg.jarvis_empg__crm_team_members__history tm ON s.jarvis_id = tm.user_id
            JOIN jarvis_empg.jarvis_empg__crm_teams t ON tm.team_id = t.id
            WHERE s.email IN ('{email_list}')
              AND tm.operation_type = 'insert'
        """)
        for _, r in team_lkp.iterrows():
            if r['rn'] == 1:
                redshift_team_lookup[r['email']] = r['team_name']

    for (email, month_num), ng_val in unmatched_ng.items():
        last_row = df[df['staff_email'] == email].sort_values('month', ascending=False).head(1)
        if len(last_row) == 0:
            # No CSV history — try Redshift team lookup
            team_name = redshift_team_lookup.get(email)
            mgr = TEAM_TO_MANAGER.get(team_name)
            if not team_name or not mgr:
                print(f"    Skipping {email} (no team history found)")
                continue
            # Build a minimal row using any existing row from same team as template
            template = df[df['team_name_en'] == team_name].sort_values('month', ascending=False).head(1)
            if len(template) == 0:
                print(f"    Skipping {email} (no template row for team {team_name})")
                continue
            last_row = template
        new_row = last_row.iloc[0].copy()
        new_row['staff_email'] = email  # ensure we use the unmatched consultant's email, not the template's
        new_row['month'] = month_num
        new_row['client_net_gain_achieved'] = ng_val
        # Zero out live metrics for departed staff (only cols that exist now)
        zero_cols = ['collections_achieved','collection_target','calls_count','unique_calls',
                     'total_qualified_calls','unique_qualified_calls','non_qualified_calls',
                     'rejected_calls','unanswered_calls','total_talk_time','total_meetings',
                     'verified_meetings','unique_verified_meetings','failed_meetings',
                     'packages_sold','discounted_pct','renewed_clients','pending_renewal_clients',
                     'client_net_gain_target']
        for col in zero_cols:
            if col in new_row.index:
                new_row[col] = 0
        extra_rows.append(new_row)
        print(f"    {email}: NG={ng_val} -> attributed to team '{new_row['team_name_en']}'")
    if extra_rows:
        df = pd.concat([df, pd.DataFrame(extra_rows)], ignore_index=True)

print(f"  Applied {applied} net gain values ({len(unmatched_ng)} attributed from departed staff)")

# ── Manual NG adjustments ────────────────────────────────────────────────────
# Amjad Almutiry Apr-2026 +1: client REF 61445 reactivated by Amjad (payment
# collector) but EOM assignee is a different consultant — Jarvis credits Amjad.
amjad_mask = (df['staff_email'] == 'amjad.almutiry@bayut.sa') & (df['month'] == 4)
if amjad_mask.any():
    primary_amjad = df.loc[amjad_mask, 'collections_achieved'].idxmax()
    df.at[primary_amjad, 'client_net_gain_achieved'] += 1
    print(f"  Manual adj: amjad.almutiry@bayut.sa Apr NG -> {df.at[primary_amjad, 'client_net_gain_achieved']}")
# ─────────────────────────────────────────────────────────────────────────────

print("\nPro-rating targets by working days per team...")

MONTH_RANGES = {
    mn: (date.fromisoformat(bom), date.fromisoformat(bom) + relativedelta(months=1))
    for mn, bom, _ in MONTHS
}

def working_days(start, end):
    count = 0
    d = start
    while d < end:
        if d.weekday() not in (4, 5):
            count += 1
        d += timedelta(days=1)
    return count

# Pull team periods for pro-rating
team_periods_df = run_query("""
SELECT h.user_id, t.name as team_name,
    h.operation_timestamp as period_start,
    LEAD(h.operation_timestamp) OVER (PARTITION BY h.user_id ORDER BY h.operation_timestamp) as period_end
FROM jarvis_empg.jarvis_empg__crm_team_members__history h
JOIN jarvis_empg.jarvis_empg__crm_teams t ON h.team_id = t.id
WHERE h.operation_type = 'insert'
""")
team_periods_df['period_start'] = pd.to_datetime(team_periods_df['period_start'])
team_periods_df['period_end'] = pd.to_datetime(team_periods_df['period_end'])

# Find consultants with multiple team rows in same month (team changers)
multi_team = df.groupby(['staff_email', 'month']).size().reset_index(name='team_count')
changers = multi_team[multi_team['team_count'] > 1]

target_cols = ['collection_target']  # Only collection_target is pro-rated; net gain stays on month-end team
prorated_count = 0

for _, chg in changers.iterrows():
    email = chg['staff_email']
    month = chg['month']
    rows = df[(df['staff_email'] == email) & (df['month'] == month)]

    # Find the row that has the target (month-end team)
    target_row = rows[rows['collection_target'] > 0]
    if len(target_row) == 0:
        continue

    monthly_target = target_row.iloc[0]['collection_target']
    if monthly_target == 0:
        continue

    # Get this user's team periods
    jarvis_id = target_row.iloc[0].get('jarvis_id', None)
    if pd.isna(jarvis_id):
        # Look up from dim_staff
        jarvis_id_series = rows['staff_email'].map(
            lambda e: team_periods_df[team_periods_df['user_id'].notna()]['user_id'].iloc[0] if len(team_periods_df) > 0 else None
        )
        continue

    m_start, m_end = MONTH_RANGES.get(month, (None, None))
    if not m_start:
        continue

    total_wd = working_days(m_start, m_end)
    if total_wd == 0:
        continue

    # Calculate working days per team for this consultant in this month
    user_periods = team_periods_df[team_periods_df['user_id'] == jarvis_id].copy()
    team_wd = {}
    for _, tp in user_periods.iterrows():
        p_start = max(tp['period_start'].date() if pd.notna(tp['period_start']) else m_start, m_start)
        p_end = min(tp['period_end'].date() if pd.notna(tp['period_end']) else m_end, m_end)
        if p_start >= m_end or p_end <= m_start:
            continue
        wd = working_days(p_start, p_end)
        tn = tp['team_name']
        team_wd[tn] = team_wd.get(tn, 0) + wd

    if not team_wd or sum(team_wd.values()) == 0:
        continue

    # Pro-rate collection target across teams by working days
    # Net gain stays fully with month-end team (not pro-rated)
    total_team_wd = sum(team_wd.values())
    for team_name, wd in team_wd.items():
        ratio = wd / total_team_wd
        mask = (df['staff_email'] == email) & (df['month'] == month) & (df['team_name_en'] == team_name)
        if mask.sum() > 0:
            df.loc[mask, 'collection_target'] = round(monthly_target * ratio, 2)

    # Zero out target on rows where team doesn't appear in team_wd
    for _, row in rows.iterrows():
        if row['team_name_en'] not in team_wd:
            mask = (df['staff_email'] == email) & (df['month'] == month) & (df['team_name_en'] == row['team_name_en'])
            df.loc[mask, target_cols] = 0

    prorated_count += 1

print(f"  Pro-rated targets for {prorated_count} consultant-month combinations")

# ============================================================
# 2.5 MERGE COVERAGE DATA FROM UPLOADED CSVs (Jan/Feb/Mar)
# ============================================================

print("\nMerging coverage data from uploaded CSVs...")
coverage_files = {
    1: 'C:/Users/hamza.rizwan/Downloads/Coverage Data - Jan_Feb_March - Jan 2026.csv',
    2: 'C:/Users/hamza.rizwan/Downloads/Coverage Data - Jan_Feb_March - Feb 2026.csv',
    3: 'C:/Users/hamza.rizwan/Downloads/Coverage Data - Jan_Feb_March - Mar 2026.csv',
}

coverage_dfs = []
for month_num, fpath in coverage_files.items():
    cov = pd.read_csv(fpath)
    cov = cov[['staff_email', 'month', 'coverage_clients', 'current_assigned_clients']]
    coverage_dfs.append(cov)

coverage_all = pd.concat(coverage_dfs, ignore_index=True)
coverage_all['coverage_clients'] = pd.to_numeric(coverage_all['coverage_clients'], errors='coerce').fillna(0).astype(int)
coverage_all['current_assigned_clients'] = pd.to_numeric(coverage_all['current_assigned_clients'], errors='coerce').fillna(0).astype(int)

# For April (month 4): use live snapshot from crm_clients as current proxy
# This will be replaced with a proper month-end snapshot at end of April
apr_coverage = run_query("""
SELECT u.email as staff_email,
    4 as month,
    COUNT(DISTINCT CASE WHEN cds.calls_30_days > 0 OR cds.meetings_30_days > 0 THEN cds.client_id END) as coverage_clients,
    COUNT(DISTINCT cds.client_id) as current_assigned_clients
FROM jarvis_empg.jarvis_empg__crm_client_detail_summaries cds
JOIN jarvis_empg.jarvis_empg__crm_clients cl ON cds.client_id = cl.id
    AND (cl.operation_type IS NULL OR cl.operation_type != 'delete') AND cl.is_active = 1
JOIN jarvis_empg.jarvis_empg__crm_users u ON cl.assignee_id = u.id
WHERE (cds.operation_type IS NULL OR cds.operation_type != 'delete')
GROUP BY u.email
""")
coverage_all = pd.concat([coverage_all, apr_coverage], ignore_index=True)

# Merge into main dataframe
df = df.merge(coverage_all[['staff_email', 'month', 'coverage_clients', 'current_assigned_clients']],
              on=['staff_email', 'month'], how='left')
df['coverage_clients'] = df['coverage_clients'].fillna(0).astype(int)
df['current_assigned_clients'] = df['current_assigned_clients'].fillna(0).astype(int)

print("\nRenewal data: pending from dim_contracts (Signed+Completed expiring), renewed from dim_contracts category 43")

print(f"\nCoverage merged. Sample check:")
for m in [1, 2, 3, 4]:
    mdf = df[df['month'] == m]
    has_cov = (mdf['coverage_clients'] > 0).sum()
    print(f"  Month {m}: {has_cov} consultants with coverage > 0")

# ============================================================
# 3. ENRICH WITH TEAM MAPPINGS
# ============================================================

df['team_name_en'] = df['team_name_en'].str.strip()
df['manager_reporting'] = df['team_name_en'].map(TEAM_TO_MANAGER)
df['tl_name'] = df['team_name_en'].map(TEAM_TO_TL_NAME)
df['manager_name'] = df['manager_reporting'].map(MANAGER_ALIAS_TO_NAME)
df['is_telesales'] = df['team_name_en'].isin(TELESALES_TEAMS)
df['is_leader'] = df['staff_name_en'].isin(LEADERS)
df['region'] = df['manager_reporting'].map(MANAGER_REGION)
# Apply team-level overrides for teams whose region differs from their manager's region
df['region'] = df['team_name_en'].map(TEAM_REGION_OVERRIDE).fillna(df['region'])

# Point-in-time active status: active at end of month if deactivated_at is NULL or > month_end
df['deactivated_at'] = pd.to_datetime(df['deactivated_at'], errors='coerce')
df['month_end'] = pd.to_datetime(df['month_end'], errors='coerce')
df['active_eom'] = df['deactivated_at'].isna() | (df['deactivated_at'] >= df['month_end'])

# Computed per-day metrics
df['uqc_per_day'] = np.where(df['days_worked'] > 0, df['unique_qualified_calls'] / df['days_worked'], 0)
df['dtt_per_day'] = np.where(df['days_worked'] > 0, df['total_talk_time'] / df['days_worked'], 0)
df['vm_per_day'] = np.where(df['days_worked'] > 0, df['unique_verified_meetings'] / df['days_worked'], 0)

# Save enriched consultant data
df.to_csv('C:/Users/hamza.rizwan/sales_consultants_jan_to_apr_2026.csv', index=False)
print(f"Saved enriched consultant data to sales_consultants_jan_to_apr_2026.csv")

# ============================================================
# 3.5 DAILY COLLECTIONS (for trend chart)
# ============================================================
print("\nPulling daily collections for trend chart...")
_ts_team_names = "','".join(TELESALES_TEAMS)
eom_daily = (today + relativedelta(days=1)).strftime('%Y-%m-%d')
daily_coll_df = run_query(f"""
WITH telesales_team_ids AS (
    SELECT id FROM jarvis_empg.jarvis_empg__crm_teams
    WHERE name IN ('{_ts_team_names}')
),
team_periods AS (
    SELECT h.user_id, h.team_id,
        h.operation_timestamp as period_start,
        LEAD(h.operation_timestamp) OVER (PARTITION BY h.user_id ORDER BY h.operation_timestamp) as period_end,
        h.operation_type
    FROM jarvis_empg.jarvis_empg__crm_team_members__history h
    WHERE h.operation_type IN ('insert','delete')
),
active_periods AS (
    SELECT user_id, team_id, period_start, period_end
    FROM team_periods WHERE operation_type = 'insert'
)
SELECT
    DATE_TRUNC('day', p.collected_at)::date as collection_date,
    CASE WHEN ap.team_id IN (SELECT id FROM telesales_team_ids) THEN 'ts' ELSE 'field' END as team_type,
    SUM(p.net_amount) as daily_amount
FROM jarvis_empg.jarvis_empg__crm_payments p
JOIN podl_bayutsa.dim_staff s ON p.collected_by_id = s.jarvis_id
JOIN active_periods ap ON s.jarvis_id = ap.user_id
    AND p.collected_at >= ap.period_start
    AND (ap.period_end IS NULL OR p.collected_at < ap.period_end)
WHERE s.email LIKE '%%@bayut.sa'
  AND (p.operation_type IS NULL OR p.operation_type != 'delete') AND p.deleted_at IS NULL
  AND p.collected_at >= '{_DATA_START}' AND p.collected_at < '{eom_daily}'
GROUP BY collection_date, team_type
ORDER BY collection_date
""")

# Structure: { "YYYY-MM-DD": { "ts": x, "field": y } }
daily_coll = {}
for _, row in daily_coll_df.iterrows():
    d = str(row['collection_date'])
    if d not in daily_coll:
        daily_coll[d] = {'ts': 0, 'field': 0}
    daily_coll[d][row['team_type']] = round(float(row['daily_amount']), 2)

import json
with open('C:/Users/hamza.rizwan/daily_collections_2026.json', 'w') as f:
    json.dump(daily_coll, f, separators=(',', ':'))
print(f"  Daily collections saved: {len(daily_coll)} days")

# ============================================================
# 3.6 PACKAGE MIX (for stacked bar / doughnut chart)
# ============================================================
print("\nPulling package mix by month...")
pkg_mix_df = run_query(f"""
WITH months AS (
    {build_months_cte()}
),
our_staff AS (
    SELECT staff_sk, email
    FROM podl_bayutsa.dim_staff
    WHERE staff_sk LIKE '%bayutsa%' AND email LIKE '%@bayut.sa'
)
SELECT
    m.month_num,
    s.email,
    COALESCE(p.package_name_en, 'Unknown') as package_name,
    COUNT(*) as cnt
FROM podl_bayutsa.dim_contracts c
JOIN months m ON c.date_sign_nk >= m.month_start AND c.date_sign_nk < m.month_end
JOIN our_staff s ON c.assignee_staff_sk = s.staff_sk
LEFT JOIN podl_bayutsa.dim_packages p ON c.package_sk = p.package_sk
WHERE c.contract_category_sk NOT LIKE '%82'
  AND c.contract_category_sk NOT LIKE '%89'
GROUP BY m.month_num, s.email, p.package_name_en
ORDER BY m.month_num, cnt DESC
""")

# Build email → is_telesales lookup from consultant df
email_is_ts = df.drop_duplicates('staff_email').set_index('staff_email')['is_telesales'].to_dict()

# Core packages to show individually; anything else → Other
CORE_PACKAGES = ['Starter','Bronze','Starter Pro','Silver',
                 'Platinum Plus','Platinum','Gold','Unknown']

pkg_mix = {'all': {}, 'ts': {}, 'field': {}}
for _, row in pkg_mix_df.iterrows():
    mn   = str(int(row['month_num']))
    name = row['package_name'] if row['package_name'] in CORE_PACKAGES else 'Other Packages'
    cnt  = int(row['cnt'])
    is_ts = email_is_ts.get(row['email'], False)
    buckets = ['all', 'ts' if is_ts else 'field']
    for bucket in buckets:
        if mn not in pkg_mix[bucket]:
            pkg_mix[bucket][mn] = {}
        pkg_mix[bucket][mn][name] = pkg_mix[bucket][mn].get(name, 0) + cnt

with open('C:/Users/hamza.rizwan/package_mix_2026.json', 'w') as f:
    json.dump(pkg_mix, f, separators=(',', ':'))
print(f"  Package mix saved: {len(pkg_mix['all'])} months (all/ts/field slices)")

# ============================================================
# 4. AGGREGATION FUNCTION
# ============================================================

def build_aggregated_view(df, group_col, group_label):
    """Aggregate consultant data by group_col (team_name_en or manager_reporting) and month."""
    results = []

    for (group, month), g in df.groupby([group_col, 'month']):
        if pd.isna(group):
            continue

        # Determine team type
        is_ts = g['is_telesales'].any()

        # All members in pool (for hard KPIs)
        # For manager view: include everyone under Manager Reporting except the manager
        # For TL view: include everyone (TL's hard KPIs count, soft KPIs excluded via LEADERS)
        mgr_name = MANAGER_ALIAS_TO_NAME.get(group, '')
        if group_label == 'Manager':
            pool = g[g['staff_name_en'] != mgr_name]
        else:
            pool = g  # include TL — their hard KPIs count, LEADERS set handles soft KPI exclusion

        # Team members only (exclude leaders) for productivity, soft KPIs
        members = pool[~pool['staff_name_en'].isin(LEADERS)]

        # Active team (EOM) = staff who were active at end of that month
        active_team = len(pool[pool['active_eom'] == True])

        # BOM and Productivity = team members only (exclude leaders)
        bom = len(members[members['collection_target'] > 0])

        # Hard KPIs — cash/target use full pool
        cash_collection = pool['collections_achieved'].sum()
        target = pool['collection_target'].sum()
        tva = cash_collection / target if target > 0 else None
        productive_users = len(members[members['collections_achieved'] >= 4000])
        productivity = (productive_users / bom * 100) if bom > 0 else None
        packages_sold = pool['packages_sold'].sum()
        # Avg discount: average of discounted_pct for consultants with packages > 0
        pkg_holders = pool[pool['packages_sold'] > 0]
        avg_discount = pkg_holders['discounted_pct'].mean() if len(pkg_holders) > 0 else None
        net_gain = pool['client_net_gain_achieved'].sum()
        # Coverage uses full group (including manager/TL) since coverage is a team-wide metric
        coverage = g['coverage_clients'].sum()
        assigned = g['current_assigned_clients'].sum()
        coverage_pct = (coverage / assigned * 100) if assigned > 0 else None
        renewed = pool['renewed_clients'].sum()
        pending_renewals = pool['pending_renewal_clients'].sum()
        renewal_rate = (renewed / (renewed + pending_renewals) * 100) if (renewed + pending_renewals) > 0 else None
        cash_per_employee = (cash_collection / bom) if bom > 0 else None

        # TL Collection (for manager view: sum of collections by TLs themselves)
        tl_collection = 0
        if group_label == 'Manager':
            tls_in_pool = g[g['staff_name_en'].isin(LEADERS) & (g['staff_name_en'] != mgr_name)]
            tl_collection = tls_in_pool['collections_achieved'].sum()
        tl_collection_pct = (tl_collection / cash_collection * 100) if cash_collection > 0 else 0

        # Soft KPIs (zeros excluded per metric independently)
        uqc_pool = members[members['unique_qualified_calls'] > 0]
        dtt_pool = members[members['total_talk_time'] > 0]
        vm_pool = members[members['unique_verified_meetings'] > 0] if not is_ts else pd.DataFrame()

        avg_uqc = uqc_pool['uqc_per_day'].mean() if len(uqc_pool) > 0 else 0
        avg_dtt = dtt_pool['dtt_per_day'].mean() if len(dtt_pool) > 0 else 0
        avg_vm = vm_pool['vm_per_day'].mean() if len(vm_pool) > 0 else None

        # Attrition = count of inactive staff
        attrition = len(g[(g['status'] == 'Inactive') & (g['days_worked'] > 0)])

        results.append({
            f'{group_label}': group,
            f'{group_label} Name': MANAGER_ALIAS_TO_NAME.get(group, TEAM_TO_TL_NAME.get(group, '')),
            'Month': int(month),
            'Type': 'Telesales' if is_ts else 'Field',
            'Region': MANAGER_REGION.get(group, MANAGER_REGION.get(TEAM_TO_MANAGER.get(group, ''), '')),
            'Cash Collection': round(cash_collection, 2),
            'Team Collection': round(cash_collection, 2),
            'TL Collection': round(tl_collection, 2),
            'TL Collection %': round(tl_collection_pct, 1),
            'Target': round(target, 2),
            'TvA': round(tva * 100, 1) if tva else None,
            'Total Packages Sold': int(packages_sold),
            'Active Team (EOM)': active_team,
            'Team with Target (BOM)': bom,
            'Cash Collection per Employee': round(cash_per_employee, 1) if cash_per_employee else None,
            'Avg Discount %': round(avg_discount * 100, 0) if avg_discount else None,
            'Absolute Coverage': int(coverage),
            'Total Tagged Clients': int(assigned),
            'Coverage %': round(coverage_pct, 0) if coverage_pct else None,
            'Net Gain (Clients)': int(net_gain),
            'Renewed Clients': int(renewed),
            'Pending Renewals': int(pending_renewals),
            'Renewal Rate': f"{int(round(renewal_rate))}%" if renewal_rate is not None else None,
            'Productive Users': productive_users,
            'Productivity': f"{int(round(productivity))}%" if productivity else None,
            'Attrition': attrition,
            'Avg. UQC per Employee': round(avg_uqc, 1),
            'Avg. DTT per Employee': round(avg_dtt, 1),
            'Avg. VM per Employee': round(avg_vm, 1) if avg_vm is not None else 'N/A',
        })

    return pd.DataFrame(results)


# ============================================================
# 5. BUILD MANAGER VIEW
# ============================================================

print("\nBuilding Manager view...")
manager_df = build_aggregated_view(df, 'manager_reporting', 'Manager')
print(f"Manager view: {len(manager_df)} rows")
print(f"Managers: {manager_df['Manager'].nunique()}")
print(f"Months: {sorted(manager_df['Month'].unique())}")

# Pivot to match CSV format (metrics as rows, months as columns)
manager_df.to_csv('C:/Users/hamza.rizwan/manager_metrics_jan_to_apr_2026.csv', index=False)
print("Saved to manager_metrics_jan_to_apr_2026.csv")

# ============================================================
# 6. BUILD TEAM LEAD VIEW
# ============================================================

print("\nBuilding Team Lead view...")
tl_df = build_aggregated_view(df, 'team_name_en', 'Team Lead')
print(f"Team Lead view: {len(tl_df)} rows")
print(f"Teams: {tl_df['Team Lead'].nunique()}")
print(f"Months: {sorted(tl_df['Month'].unique())}")

tl_df.to_csv('C:/Users/hamza.rizwan/tl_metrics_jan_to_apr_2026.csv', index=False)
print("Saved to tl_metrics_jan_to_apr_2026.csv")

# ============================================================
# 7. VALIDATE AGAINST PROVIDED MANAGER CSV (March)
# ============================================================

print("\n=== VALIDATION: Manager View (March) ===")
mar_mgr = manager_df[manager_df['Month'] == 3]
for _, row in mar_mgr.iterrows():
    mgr = row['Manager']
    if mgr in ['El-Kallas - M4', 'Mohammed Abdelkader - Eastern', 'Reham AL Harbi - M2',
               'Mohamad Ghannoum - JM3', 'Mohamed Abdullah - M3', 'AbdulMajed - TL Riyadh']:
        print(f"\n{mgr} ({row['Manager Name']}):")
        print(f"  Cash Collection: {row['Cash Collection']/1000:.1f}K")
        print(f"  Target: {row['Target']/1000:.1f}K")
        print(f"  TvA: {row['TvA']}%")
        print(f"  Packages Sold: {row['Total Packages Sold']}")
        print(f"  Active Team: {row['Active Team (EOM)']}")
        print(f"  BOM: {row['Team with Target (BOM)']}")
        print(f"  Avg Discount: {row['Avg Discount %']}%")
        print(f"  Net Gain: {row['Net Gain (Clients)']}")
        print(f"  Avg UQC: {row['Avg. UQC per Employee']}")
        print(f"  Avg DTT: {row['Avg. DTT per Employee']}")
        print(f"  Avg VM: {row['Avg. VM per Employee']}")

print("\n=== PROVIDED CSV VALUES (March) ===")
print("El-Kallas - M4: Cash=79.8K, Target=90K, TvA=88.7%, Pkg=12, Active=13, BOM=12, Disc=43%, NetGain=2, UQC=1.4, DTT=6.1, VM=1.3")
print("Mohammed Abdelkader: Cash=198.4K, Target=106K, TvA=187.1%, Pkg=23, Active=21, BOM=20, Disc=34%, NetGain=11, UQC=1.5, DTT=5.7, VM=2.9")
print("Reham AL Harbi: Cash=93.7K, Target=106K, TvA=88.4%, Pkg=26, Active=16, BOM=14, Disc=39%, NetGain=11, UQC=2.2, DTT=12.3, VM=1.2")
print("Mohamad Ghannoum: Cash=43K, Target=147.5K, TvA=29.1%, Pkg=13, Active=22, BOM=20, Disc=42%, NetGain=3, UQC=1.8, DTT=7.5, VM=1.9")
print("Mohamed Abdullah: Cash=137.2K, Target=85K, TvA=161.4%, Pkg=9, Active=13, BOM=11, Disc=27%, NetGain=7, UQC=2.5, DTT=9.0, VM=0.9")
print("AbdulMajed: Cash=40.3K, Target=88K, TvA=45.8%, Pkg=10, Active=12, BOM=11, Disc=42%, NetGain=3, UQC=0.9, DTT=3.9, VM=1.2")

# ============================================================
# 8. PACKAGE DISCOUNT % BY CLIENT TYPE (New vs Renewal)
# ============================================================
print("\nPulling package discount % by client type (new vs renewal)...")
disc_ct_query = f"""
WITH months AS (
    {build_months_cte()}
),
our_staff AS (
    SELECT staff_sk, email
    FROM podl_bayutsa.dim_staff
    WHERE staff_sk LIKE '%%bayutsa%%' AND email LIKE '%%@bayut.sa'
)
SELECT
    m.month_num,
    s.email,
    COALESCE(p.package_name_en, 'Unknown') as package_name,
    CASE
        WHEN c.contract_category_sk LIKE '%%42' THEN 'new'
        WHEN c.contract_category_sk LIKE '%%43' THEN 'renewal'
    END as client_type,
    SUM(c.discount_value)      as total_discount,
    SUM(c.net_contract_value)  as total_contract_value
FROM podl_bayutsa.dim_contracts c
JOIN months m ON c.date_sign_nk >= m.month_start AND c.date_sign_nk < m.month_end
JOIN our_staff s ON c.assignee_staff_sk = s.staff_sk
LEFT JOIN podl_bayutsa.dim_packages p ON c.package_sk = p.package_sk
WHERE (c.contract_category_sk LIKE '%%42' OR c.contract_category_sk LIKE '%%43')
GROUP BY m.month_num, s.email, p.package_name_en, client_type
ORDER BY m.month_num, s.email
"""
disc_ct_df = run_query(disc_ct_query)
print(f"  Discount rows fetched: {len(disc_ct_df)}")

# Build email → team-type / region lookups from consultant df
_email_is_ts  = df.drop_duplicates('staff_email').set_index('staff_email')['is_telesales'].to_dict()
_email_region = df.drop_duplicates('staff_email').set_index('staff_email')['region'].to_dict()

_CORE_PKG = ['Starter','Bronze','Starter Pro','Silver','Platinum Plus','Platinum','Gold','Unknown']

# Accumulate sums: bucket -> client_type -> month -> package -> [sum_disc, sum_val]
_disc_acc = {}

for _, _row in disc_ct_df.iterrows():
    _mn = int(_row['month_num'])
    if _mn < 1:
        continue   # Oct-Dec 2025 not shown on discount chart
    _mn_str = str(_mn)
    _ctype  = _row['client_type']
    if not _ctype:
        continue
    _pkg      = _row['package_name'] if _row['package_name'] in _CORE_PKG else 'Other Packages'
    _disc_val = float(_row['total_discount'])     if pd.notna(_row['total_discount'])     else 0.0
    _cont_val = float(_row['total_contract_value']) if pd.notna(_row['total_contract_value']) else 0.0
    if _cont_val <= 0 or _disc_val != _disc_val:   # skip zero-value or NaN discount
        continue
    _email   = _row['email']
    _is_ts   = _email_is_ts.get(_email, False)
    _region  = _email_region.get(_email, None)

    _buckets = ['all', 'ts' if _is_ts else 'field']
    if _region and str(_region) != 'nan':
        _buckets.append(_region)

    for _bucket in _buckets:
        if _bucket not in _disc_acc:
            _disc_acc[_bucket] = {}
        for _ct in [_ctype, 'all']:   # update both the specific type and 'all'
            if _ct not in _disc_acc[_bucket]:
                _disc_acc[_bucket][_ct] = {}
            if _mn_str not in _disc_acc[_bucket][_ct]:
                _disc_acc[_bucket][_ct][_mn_str] = {}
            if _pkg not in _disc_acc[_bucket][_ct][_mn_str]:
                _disc_acc[_bucket][_ct][_mn_str][_pkg] = [0.0, 0.0]
            _disc_acc[_bucket][_ct][_mn_str][_pkg][0] += _disc_val
            _disc_acc[_bucket][_ct][_mn_str][_pkg][1] += _cont_val

# Convert accumulated sums to avg discount %
_pkg_disc_out = {}
for _bucket, _ctypes in _disc_acc.items():
    _pkg_disc_out[_bucket] = {}
    for _ct, _months in _ctypes.items():
        _pkg_disc_out[_bucket][_ct] = {}
        for _mn_str, _pkgs in _months.items():
            _pkg_disc_out[_bucket][_ct][_mn_str] = {}
            for _pkg, (_d, _v) in _pkgs.items():
                _pct = _d / _v * 100 if _v > 0 else None
                if _pct is not None and _pct == _pct:  # skip None and NaN
                    _pkg_disc_out[_bucket][_ct][_mn_str][_pkg] = round(_pct, 1)

with open('C:/Users/hamza.rizwan/pkg_discount_by_filter.json', 'w') as f:
    json.dump(_pkg_disc_out, f, separators=(',', ':'))
print(f"  Package discount by filter saved: {len(_pkg_disc_out)} buckets, client types: all/new/renewal")

# ============================================================
# DAILY METRICS PER CONSULTANT (for day-level date filter)
# ============================================================
print("\nPulling daily metrics per consultant (Jan 2026 – today)...")
_dm_start = '2026-01-01'
_dm_end   = (date.today() + relativedelta(days=1)).strftime('%Y-%m-%d')

_daily_cash_df = run_query(f"""
SELECT DATE_TRUNC('day', p.collected_at)::date AS dt,
       s.email,
       SUM(p.net_amount) AS cash
FROM   jarvis_empg.jarvis_empg__crm_payments p
JOIN   podl_bayutsa.dim_staff s ON p.collected_by_id = s.jarvis_id
WHERE  s.email LIKE '%%@bayut.sa'
  AND  (p.operation_type IS NULL OR p.operation_type != 'delete')
  AND  p.deleted_at IS NULL
  AND  p.collected_at >= '{_dm_start}' AND p.collected_at < '{_dm_end}'
GROUP BY dt, s.email
""")

_daily_pkg_df = run_query(f"""
SELECT DATE_TRUNC('day', c.date_sign_nk)::date AS dt,
       s.email,
       COUNT(*) AS pkg
FROM   podl_bayutsa.dim_contracts c
JOIN   podl_bayutsa.dim_staff s ON c.assignee_staff_sk = s.staff_sk
WHERE  s.email LIKE '%%@bayut.sa'
  AND  c.contract_category_sk NOT LIKE '%%82'
  AND  c.contract_category_sk NOT LIKE '%%89'
  AND  c.date_sign_nk >= '{_dm_start}' AND c.date_sign_nk < '{_dm_end}'
GROUP BY dt, s.email
""")

_daily_calls_df = run_query(f"""
SELECT DATE_TRUNC('day', c.time_call_started_local)::date AS dt,
       s.email,
       COUNT(DISTINCT CASE WHEN c.connected_duration >= 60 THEN c.account_sk END) AS uqc,
       ROUND(SUM(c.connected_duration) / 60.0, 2) AS dtt
FROM   podl_bayutsa.fact_calltracking_staff_logs c
JOIN   podl_bayutsa.dim_staff s ON c.staff_sk = s.staff_sk
WHERE  s.email LIKE '%%@bayut.sa'
  AND  c.call_type IN ('in', 'out') AND c.account_sk != 'unknown'
  AND  c.date_call_nk >= '{_dm_start}' AND c.date_call_nk < '{_dm_end}'
GROUP BY dt, s.email
""")

_daily_vm_df = run_query(f"""
SELECT DATE_TRUNC('day', ts.achieved_at)::date AS dt,
       s.email,
       COUNT(DISTINCT task.client_id) AS vm
FROM   jarvis_empg.jarvis_empg__crm_target_summaries ts
JOIN   jarvis_empg.jarvis_empg__crm_tasks task ON ts.achievable_id = task.id
JOIN   podl_bayutsa.dim_staff s ON ts.user_id = s.jarvis_id
WHERE  s.email LIKE '%%@bayut.sa'
  AND  ts.target_type_id = 115
  AND  (ts.operation_type IS NULL OR ts.operation_type != 'delete')
  AND  ts.achieved_at >= '{_dm_start}' AND ts.achieved_at < '{_dm_end}'
GROUP BY dt, s.email
""")

for _df_ in [_daily_cash_df, _daily_pkg_df, _daily_calls_df, _daily_vm_df]:
    _df_['dt'] = _df_['dt'].astype(str)

_dm_merged = (_daily_cash_df
    .merge(_daily_pkg_df,   on=['dt','email'], how='outer')
    .merge(_daily_calls_df, on=['dt','email'], how='outer')
    .merge(_daily_vm_df,    on=['dt','email'], how='outer')
    .fillna(0))
_dm_merged['cash'] = _dm_merged['cash'].round(2)
_dm_merged['dtt']  = _dm_merged['dtt'].round(2)
for _c in ['pkg','uqc','vm']:
    _dm_merged[_c] = _dm_merged[_c].astype(int)

daily_metrics = {}
for _, _r in _dm_merged.iterrows():
    _em = str(_r['email'])
    if _em not in daily_metrics:
        daily_metrics[_em] = []
    daily_metrics[_em].append([_r['dt'], round(float(_r['cash']),2), int(_r['pkg']), int(_r['uqc']), round(float(_r['dtt']),2), int(_r['vm'])])
for _em in daily_metrics:
    daily_metrics[_em].sort(key=lambda x: x[0])

with open('C:/Users/hamza.rizwan/daily_metrics_2026.json', 'w') as f:
    json.dump(daily_metrics, f, separators=(',', ':'))
print(f"  Daily metrics saved: {len(daily_metrics)} consultants, {len(_dm_merged)} day-rows")

# ============================================================
# ACTIVE LISTINGS SNAPSHOT (for Overview tile)
# ============================================================
print("\nPulling active listings snapshot...")
_al_df = run_query("""
SELECT l.user_email_address AS email,
       COUNT(*) AS active_listings,
       COUNT(DISTINCT l.account_sk) AS active_agencies
FROM   podl_bayutsa.fact_listings l
WHERE  l.listing_status_sk = 'active'
  AND  l.user_email_address LIKE '%@bayut.sa'
GROUP BY l.user_email_address
""")
_al_total_df = run_query("""
SELECT COUNT(*) AS total_active
FROM   podl_bayutsa.fact_listings
WHERE  listing_status_sk = 'active'
""")
_total_active_listings = int(_al_total_df['total_active'].iloc[0])

# Zero posters: consultants who have active assigned clients but zero active listings
# Use current consultant pool from latest month in df
_latest_mn_staff = df[df['month'] == df['month'].max()]['staff_email'].dropna().unique()
_al_by_email = _al_df.set_index('email')
_zero_posters = {}
_cons_active_listings = {}
_cons_active_agencies = {}
for _em in _al_by_email.index:
    _cons_active_listings[_em] = int(_al_by_email.loc[_em, 'active_listings'])
    _cons_active_agencies[_em] = int(_al_by_email.loc[_em, 'active_agencies'])

# Zero posters: consultants in latest DATA with zero listings
for _em in _latest_mn_staff:
    if _em not in _al_by_email.index or _al_by_email.loc[_em, 'active_listings'] == 0:
        # Count their assigned clients as "zero poster" weight
        _rows = df[(df['staff_email'] == _em) & (df['month'] == df['month'].max())]
        _assigned = int(_rows['current_assigned_clients'].sum()) if len(_rows) > 0 else 0
        if _assigned > 0:
            _zero_posters[_em] = _assigned

active_listings_snapshot = {
    'total': _total_active_listings,
    'by_consultant': _cons_active_listings,
    'agencies_by_consultant': _cons_active_agencies,
    'zero_posters': _zero_posters
}
with open('C:/Users/hamza.rizwan/active_listings_snapshot.json', 'w') as f:
    json.dump(active_listings_snapshot, f, separators=(',', ':'))
print(f"  Active listings snapshot saved: total={_total_active_listings}, consultants={len(_cons_active_listings)}")

# ============================================================
# CONSULTANT AVG MEETING DURATION (Jan 2026 – today)
# ============================================================
print("\nPulling consultant avg meeting duration...")
_mtg_dur_df = run_query(f"""
WITH field_consultants AS (
    SELECT DISTINCT s.email, s.jarvis_id
    FROM   podl_bayutsa.dim_staff s
    JOIN   podl_bayutsa.dim_teams t ON s.team_sk = t.team_sk
    WHERE  s.email LIKE '%%@bayut.sa'
      AND  t.team_name_en NOT LIKE '%%Telesales%%'
      AND  s.jarvis_id != t.team_lead_staff_sk
),
mtg_dur AS (
    SELECT m.assignee_id,
           SUM(DATEDIFF('minute', ci.checked_in_at, ci.completed_at)) AS total_minutes,
           COUNT(*) AS mtg_count
    FROM   jarvis_empg.jarvis_empg__crm_meetings m
    JOIN   jarvis_empg.jarvis_empg__crm_check_ins ci ON ci.meeting_id = m.id
    WHERE  m.start_date >= '{_dm_start}' AND m.start_date < '{_dm_end}'
      AND  ci.completed_at IS NOT NULL
      AND  (m.operation_type IS NULL OR m.operation_type != 'delete')
      AND  (ci.operation_type IS NULL OR ci.operation_type != 'delete')
    GROUP BY m.assignee_id
)
SELECT fc.email,
       ROUND(md.total_minutes::float / md.mtg_count, 1) AS avg_duration_min
FROM   mtg_dur md
JOIN   field_consultants fc ON md.assignee_id = fc.jarvis_id
WHERE  md.mtg_count >= 5
""")
consultant_avg_mtg_duration = dict(zip(_mtg_dur_df['email'], _mtg_dur_df['avg_duration_min'].round(1)))
with open('C:/Users/hamza.rizwan/consultant_avg_mtg_duration.json', 'w') as f:
    json.dump(consultant_avg_mtg_duration, f, separators=(',', ':'))
print(f"  Avg meeting duration saved: {len(consultant_avg_mtg_duration)} consultants")
