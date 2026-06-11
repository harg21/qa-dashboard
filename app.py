"""
QA Dashboard — Streamlit app (auto-assembled).
Run with:  streamlit run app.py
"""
import os
import re
import math as _math
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from qa_helpers import *

st.set_page_config(page_title="QA Dashboard", layout="wide")


def _to_float(x):
    """Lenient float parse used by some loaders — '' / bad -> 0.0."""
    if x is None or x == "":
        return 0.0
    if isinstance(x, (int, float)):
        return 0.0 if (isinstance(x, float) and _math.isnan(x)) else float(x)
    try:
        return float(str(x).replace("%", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


def _to_int(x):
    """Lenient int parse used by some loaders — '' / bad -> 0."""
    if x is None or x == "":
        return 0
    try:
        return int(float(str(x).strip()))
    except (ValueError, TypeError):
        return 0



# ───────────────────── palette / category constants ─────────────────────
SCOL = {'Accepted':'#137333','Non QA Error':'#1a73e8','Rejected':'#c5221f','Outside Window':'#e37400'}
SBGCOL = {'Accepted':'#e6f4ea','Non QA Error':'#e8f0fe','Rejected':'#fce8e6','Outside Window':'#fef3e2'}
STATUSES = ['Accepted','Non QA Error','Rejected','Outside Window']
OUTCOMES = ['Bucks Accepted','Agreed to use the voucher','OFP post retention attempt','No Response from customer','Others']
OCOL = ['#137333','#34A853','#e37400','#4285F4','#9aa0a6']
AUD_COLS = {'Arif':'#4285F4','Farzana':'#EA4335','Nanaiah':'#34A853','Sunil':'#FBBC04'}
ERRCOL = {'Agent Error':'#c5221f','Non-Agent Error':'#4285F4','Tools Error':'#e37400','Customer Error':'#34A853'}
ERR_CATS = ['Agent Error','Non-Agent Error','Tools Error','Customer Error']
CR_CATS = ['Merchant not honoring','Voucher redeemed by mistake','Booking and availability issue','Delivered product issue']
CR_CAT_SHORT = ['Merchant','Voucher','Booking','Delivered']
CR_CAT_COL = ['#4285F4','#34A853','#FBBC04','#EA4335']
ESC_ERR_COL = {'CS - Agent Error':'#c5221f','MO - Agent Error':'#e37400','Non-Agent Error':'#4285F4','Tool Limitations':'#9c27b0'}
ESC_ERR_CATS = ['CS - Agent Error','MO - Agent Error','Non-Agent Error','Tool Limitations']
ESC_ERR_LABELS = ['CS Agent Error','MO Agent Error','Non-Agent Error','Tool Limitations']
ESC_SB_COL = {'Correct':'#137333','Incorrect':'#c5221f','MO Invalid Rejection':'#e37400','N/A':'#9aa0a6','No Reason Selected':'#5f6368'}
ESC_SB_CATS = ['Correct','Incorrect','MO Invalid Rejection','N/A','No Reason Selected']
CTS_ERR_COL = {'Agent Error':'#c5221f','Non-Agent Error':'#4285F4','Process Error':'#9c27b0','Tool Issue':'#e37400'}
CTS_ERR_CATS = ['Agent Error','Non-Agent Error','Process Error','Tool Issue']
CTS_TYPE_COL = {'survey_leave':'#4285F4','not_responsive':'#34A853','long_engagement':'#FBBC04','mgr_escalation':'#EA4335'}
CTS_TYPE_LABEL = {'survey_leave':'Survey/Leave','not_responsive':'Not Responsive','long_engagement':'Long Engagement','mgr_escalation':'Mgr Escalation'}
CARA_ERR_COL = {'Agent Error':'#c5221f','Non-Agent Error':'#4285F4','Customer Error':'#34A853','Tools Error':'#e37400'}
CARA_ERR_CATS = ['Agent Error','Non-Agent Error','Customer Error','Tools Error']
CARA_RES_COL = {'No Error':'#137333','Customer Not Responsive':'#4285F4','Issue Not Resolved':'#c5221f','Incorrect Leave/Resolve':'#e37400','Error':'#9c27b0'}
GOR_ERR_COL = {'Agent Error':'#c5221f','Non-Agent Error':'#4285F4','Tools Error':'#e37400'}
GOR_ERR_CATS = ['Agent Error','Non-Agent Error','Tools Error']
GOR_CSAT_VALS = ['5','3','1','Yes','No','N/A']
GOR_CSAT_COL = {'5':'#137333','3':'#e37400','1':'#c5221f','Yes':'#34A853','No':'#ea4335','N/A':'#9aa0a6'}
RFA_SCORE_LABELS = ['0%','25%','50%','75%','100%']
RFA_SCORE_VALUES = [0,25,50,75,100]
RFA_SCORE_COL = ['#c5221f','#e37400','#ea8600','#fbbc04','#137333']
RFA_OUTCOMES = ['Advised customer to wait','Agreed to use the voucher','Bucks Accepted','Escalated to other departments','Expiration Extension Denial','No Response from customer','OFP post retention attempt','Others','Refund Denied','Refund Status provided']
RFA_OUTCOME_COL = ['#4285F4','#34A853','#34A853','#EA4335','#9aa0a6','#e37400','#FBBC04','#9aa0a6','#c5221f','#1a73e8']
PSG_TYPE_LABEL = {'cnr_audit':'CNR Audit','cnr_scores':'CNR Score','survey_avoid':'Survey Avoid','leave_misuse':'Leave Misuse','long_eng':'Long Engagement','mgr_esc':'Mgr Escalation'}
PSG_TYPE_COL = {'cnr_audit':'#4285F4','cnr_scores':'#34A853','survey_avoid':'#FBBC04','leave_misuse':'#EA4335','long_eng':'#9c27b0','mgr_esc':'#e37400'}
PSG_ERR_COL = {'Agent Error':'#c5221f','Non-Agent Error':'#4285F4','Process Error':'#9c27b0','Tool Issue':'#e37400'}
MOR_CH_COL = {'Email':'#4285F4','Chat':'#34A853','Voice':'#FBBC04'}
MOD_SUB_COL = {'Consistent Refund Offender':'#c5221f','Redemption Offender':'#e37400','UK CMA Deal Investigation':'#4285F4'}
COA_PROC_COL = {'Writing':'#4285F4','Vetting':'#34A853','Deal Edits':'#FBBC04'}
COA_LOC_COL = {'India':'#1a73e8','Albania':'#EA4335'}


# ═══════════════════ DATA LOADERS ═══════════════════

def load_calibration(tabs) -> pd.DataFrame:
    rows = tabs.get('WoW_calibration score') or []
    out = []
    for r in rows[1:]:
        def g(i):
            return r[i] if i < len(r) else ''
        proc = S(g(2)).upper()
        if proc not in ('CS', 'MO', 'CO'):
            continue
        rev = S(g(3))
        if not rev:
            continue
        try:
            wk = int(float(S(g(1))))
        except (ValueError, TypeError):
            continue
        if not wk:
            continue
        out.append({
            'date': dstr(g(0)), 'week': wk, 'process': proc, 'reviewerName': rev,
            'reviewerEmail': S(g(4)), 'caseId': S(g(5)),
            'resExec': to_pct(g(6)), 'busLogic': to_pct(g(7)), 'custRights': to_pct(g(8)),
            'variance': to_pct(g(9)), 'overallScore': to_pct(g(10)),
            'observations': S(g(11)), 'hostAssessment': S(g(12)),
        })
    return pd.DataFrame(out)

def load_disputes(tabs) -> pd.DataFrame:
    rows = tabs.get('Disputes') or []
    hdr_idx = 0
    for i in range(min(len(rows), 30)):
        c0 = rows[i][0] if len(rows[i]) > 0 else ''
        if 'date' in S(c0).lower():
            hdr_idx = i
            break
    out = []
    for i in range(hdr_idx + 1, len(rows)):
        r = rows[i]
        def g(j):
            return r[j] if j < len(r) else ''
        if not S(g(0)) and not S(g(4)):
            continue
        proc = S(g(1)).upper()
        if proc not in ('CS', 'MO', 'CO'):
            continue
        status = norm_dispute(S(g(13)))
        if not status:
            continue
        d0, d14 = dstr(g(0)), dstr(g(14))
        days = None
        if d0 and d14:
            t1 = pd.to_datetime(d0, errors='coerce')
            t2 = pd.to_datetime(d14, errors='coerce')
            if pd.notna(t1) and pd.notna(t2):
                days = max(0, int(round((t2 - t1).total_seconds() / 86400)))
        try:
            wknum = int(float(S(g(16))))
        except (ValueError, TypeError):
            wknum = 0
        try:
            yr = int(float(S(g(18))))
        except (ValueError, TypeError):
            yr = 0
        try:
            ascore = to_pct(g(7))
        except (ValueError, TypeError):
            ascore = 0
        out.append({
            'disputeDate': d0, 'process': proc, 'disputeType': S(g(2)),
            'evaluationDate': dstr(g(3)), 'caseId': S(g(4)),
            'agent': S(g(5)), 'reviewer': S(g(6)),
            'agentScore': ascore, 'attributes': S(g(10)),
            'status': status, 'resolvedDate': d14, 'weekNumber': wknum,
            'month': S(g(17)), 'year': yr,
            'daysToResolve': days, 'has2ndLevel': bool(S(g(19))),
        })
    return pd.DataFrame(out)

def load_fl(tabs) -> pd.DataFrame:
    import re
    out = []
    for name, rows in tabs.items():
        m = re.match(r'^Week\s*(\d+)$', name, re.IGNORECASE)
        if not m:
            continue
        wk = int(m.group(1))
        if len(rows) < 2:
            continue
        hi = 0
        for i in range(min(len(rows), 5)):
            c0 = rows[i][0] if len(rows[i]) > 0 else ''
            c5 = rows[i][5] if len(rows[i]) > 5 else ''
            if S(c0).lower() == 'week' or 'agent' in S(c5).lower():
                hi = i
                break
        for i in range(hi + 1, len(rows)):
            r = rows[i]
            def g(j):
                return r[j] if j < len(r) else ''
            ag = S(g(5))
            if not ag:
                continue
            st = S(g(11)).lower()
            if st and st != 'completed':
                continue
            out.append({
                'week': wk, 'assignedDate': dstr(g(1)), 'transactionDate': dstr(g(2)),
                'engagement': S(g(3)), 'caseId': S(g(4)), 'agentName': ag,
                'agentEmail': S(g(6)), 'process': S(g(8)).upper() or 'FL',
                'teamLeader': S(g(9)), 'auditor': S(g(10)),
                'probe': yna(g(12)), 'investigate': yna(g(13)), 'alternatives': yna(g(14)),
                'finalOutcome': S(g(15)), 'followProcess': yna(g(16)),
                'comments': S(g(17)),
            })
    return pd.DataFrame(out)

def _find_sa_cols(row):
    c = {'agent': -1, 'caseId': -1, 'transDate': -1, 'agentEmail': -1, 'tlName': -1,
         'process': -1, 'category': -1, 'location': -1, 'role': -1, 'auditor': -1,
         'assignedDate': -1, 'status': -1}
    has_agent = False
    has_auditor = False
    for i in range(len(row)):
        h = S(row[i]).lower()
        if h == 'agent name':
            c['agent'] = i; has_agent = True
        elif 'case number' in h:
            c['caseId'] = i
        elif 'transaction date' in h:
            c['transDate'] = i
        elif 'agent email' in h:
            c['agentEmail'] = i
        elif 'tl name' in h or 'reviewer (tl)' in h:
            c['tlName'] = i
        elif h == 'process':
            c['process'] = i
        elif h == 'category':
            c['category'] = i
        elif h == 'location':
            c['location'] = i
        elif h == 'role':
            c['role'] = i
        elif h == 'auditor':
            c['auditor'] = i; has_auditor = True
        elif h == 'assigned date' or h == 'assigned':
            c['assignedDate'] = i
        elif h == 'status':
            c['status'] = i
    return c if (has_agent and has_auditor) else None

def load_super_audit(tabs) -> pd.DataFrame:
    rows_out = []
    for name, rows in tabs.items():
        if len(rows) < 2:
            continue
        hi = -1
        cols = None
        for i in range(min(len(rows), 5)):
            d = _find_sa_cols(rows[i])
            if d:
                hi = i; cols = d; break
        if hi < 0:
            continue
        for i in range(hi + 1, len(rows)):
            r = rows[i]
            ag = S(r[cols['agent']]) if cols['agent'] >= 0 else ''
            if not ag:
                continue
            aud = S(r[cols['auditor']]) if cols['auditor'] >= 0 else ''
            if not aud:
                continue
            proc = S(r[cols['process']]) if cols['process'] >= 0 else ''
            if not proc:
                proc = 'FL'
            rows_out.append({
                'batch': name,
                'caseId': S(r[cols['caseId']]) if cols['caseId'] >= 0 else '',
                'transDate': dstr(r[cols['transDate']]) if cols['transDate'] >= 0 else '',
                'agentName': ag,
                'agentEmail': S(r[cols['agentEmail']]) if cols['agentEmail'] >= 0 else '',
                'tlName': S(r[cols['tlName']]) if cols['tlName'] >= 0 else '',
                'process': proc,
                'category': S(r[cols['category']]) if cols['category'] >= 0 else '',
                'location': S(r[cols['location']]).upper() if cols['location'] >= 0 else '',
                'role': S(r[cols['role']]) if cols['role'] >= 0 else '',
                'auditor': aud,
                'assignedDate': dstr(r[cols['assignedDate']]) if cols['assignedDate'] >= 0 else '',
                'status': S(r[cols['status']]) if cols['status'] >= 0 else '',
            })
    return pd.DataFrame(rows_out)

def _find_cr_cols(row):
    if len(row) < 11:
        return None
    h0 = S(row[0]).lower().replace('\n', ' ').replace('\r', ' ').strip()
    h10 = S(row[10]).lower().replace('\n', ' ').replace('\r', ' ').strip()
    if h0 != 'engagement' or h10 != 'auditor':
        return None
    return {'engagement': 0, 'date': 2, 'agent': 3, 'teamLeader': 4, 'manager': 5,
            'reason': 6, 'outcome': 7, 'auditor': 10, 'assignedDate': 11,
            'appropriateCategory': 14, 'appropriateResolve': 15, 'errorCategory': 16,
            'errorSubCategory': 17, 'comments': 18, 'resolveError': 19,
            'disputeStatus': 22, 'overallStatus': 25, 'tlActions': 26}

def _norm_cr_resolve_error(s):
    l = S(s).lower()
    if not l or l == 'no error':
        return 'No Error'
    if 'not responsive' in l:
        return 'Customer Not Responsive'
    if 'not resolved' in l or 'ended incorrectly' in l:
        return 'Issue Not Resolved'
    return 'Other'

def load_cr(tabs) -> pd.DataFrame:
    rows_out = []
    for name, rows in tabs.items():
        if len(rows) < 2:
            continue
        hi = -1
        cd = None
        for i in range(min(len(rows), 5)):
            d = _find_cr_cols(rows[i])
            if d:
                hi = i; cd = d; break
        if hi < 0:
            continue
        for i in range(hi + 1, len(rows)):
            r = rows[i]
            eng = S(r[cd['engagement']])
            if not eng or len(eng) != 36 or len(eng.split('-')) != 5:
                continue
            aud = S(r[cd['auditor']])
            if not aud:
                continue
            rr = S(r[cd['reason']])
            rp = rr.split('::')
            rows_out.append({
                'batch': name,
                'engagementId': eng,
                'date': dstr(r[cd['date']]),
                'agent': S(r[cd['agent']]),
                'teamLeader': S(r[cd['teamLeader']]),
                'manager': S(r[cd['manager']]),
                'contactCategory': rp[0].strip(),
                'categoryGroup': rp[1].strip() if len(rp) > 1 else '',
                'outcome': S(r[cd['outcome']]),
                'auditor': aud,
                'assignedDate': dstr(r[cd['assignedDate']]),
                'appropriateCategory': S(r[cd['appropriateCategory']]),
                'appropriateResolve': S(r[cd['appropriateResolve']]),
                'errorCategory': S(r[cd['errorCategory']]),
                'errorSubCategory': S(r[cd['errorSubCategory']]),
                'comments': S(r[cd['comments']]),
                'resolveButtonError': _norm_cr_resolve_error(S(r[cd['resolveError']])),
                'disputeStatus': norm_cr_dispute(S(r[cd['disputeStatus']])),
                'overallStatus': S(r[cd['overallStatus']]),
            })
    return pd.DataFrame(rows_out)

def _is_esc_header(row):
    if len(row) < 15:
        return False
    return S(row[0]).lower() == 'case number' and S(row[14]).lower() == 'auditor'

def _norm_esc_send_back(s):
    if not s:
        return ''
    l = s.lower()
    if l == 'correct sendback reason':
        return 'Correct'
    if 'invalid rejection' in l:
        return 'MO Invalid Rejection'
    if 'n/a' in l:
        return 'N/A'
    if 'no sendback' in l:
        return 'No Reason Selected'
    if 'incorrect' in l:
        return 'Incorrect'
    return s

def load_esc(tabs) -> pd.DataFrame:
    rows_out = []
    for name, rows in tabs.items():
        if len(rows) < 2:
            continue
        hi = -1
        for i in range(min(len(rows), 5)):
            if _is_esc_header(rows[i]):
                hi = i; break
        if hi < 0:
            continue
        for i in range(hi + 1, len(rows)):
            r = rows[i]
            cn = S(r[0])
            if not cn:
                continue
            try:
                int(cn)
            except (ValueError, TypeError):
                continue
            comp_st = S(r[16]).lower()
            if comp_st and comp_st != 'completed':
                continue
            aud = S(r[14])
            if not aud:
                continue
            cc = S(r[11]).split('::')
            ac = S(r[17]).split('::')
            rows_out.append({
                'batch': name,
                'caseNumber': cn,
                'createdDate': dstr(r[1]),
                'escType': S(r[2]),
                'csAgent': S(r[3]),
                'csTl': S(r[4]),
                'moAgent': S(r[7]),
                'moTl': S(r[8]),
                'contactCategory': cc[0].strip(),
                'contactGroup': cc[1].strip() if len(cc) > 1 else '',
                'origin': S(r[12]),
                'rejectionReason': S(r[13]),
                'auditor': aud,
                'assignedDate': dstr(r[15]),
                'appropriateCategory': ac[0].strip(),
                'errorCategory': S(r[18]),
                'errorSubCategory': S(r[19]),
                'errorDetail': S(r[20]),
                'sendBackAssessment': _norm_esc_send_back(S(r[21])),
                'sendBackContext': S(r[22]),
            })
    return pd.DataFrame(rows_out)

def _find_cts_cols(row):
    n = len(row)
    if n < 8:
        return None
    def h(i):
        v = row[i] if i < n else ''
        return S(v).lower().replace('\n', ' ').replace('\r', ' ').strip()
    h0 = h(0)
    h2 = h(2) if n > 2 else ''
    h4 = h(4) if n > 4 else ''
    h7 = h(7) if n > 7 else ''
    h8 = h(8) if n > 8 else ''
    h9 = h(9) if n > 9 else ''
    h11 = h(11) if n > 11 else ''
    default = {'reason': -1, 'outcome': -1, 'resolution': -1, 'approveLeave': -1,
               'stuckInLimbo': -1, 'tl': -1, 'location': -1, 'engTimeMins': -1,
               'operEff': -1, 'avoidedResolve': -1, 'smeInv': -1, 'escReason': -1,
               'actioned': -1, 'daysAction': -1}
    def mk(extra):
        d = dict(default)
        d.update(extra)
        return d
    if h0 == 'engagement':
        if h7 == 'severity':
            return mk({'type': 'cnr_scores', 'eng': 0, 'date': 2, 'agent': 3,
                       'reason': 4, 'outcome': 5, 'resolution': 6, 'severity': 7,
                       'autoSat': 8, 'expressed': 9, 'empathy': 10, 'clarity': 11,
                       'completeness': 12, 'language': 13})
        if h11 == 'auditor' and h2 == 'team':
            return mk({'type': 'long_engagement', 'eng': 0, 'date': 1, 'agent': 3,
                       'tl': 2, 'location': 9, 'auditor': 11, 'assignedDate': 12,
                       'engTimeMins': 5, 'operEff': 14, 'avoidedResolve': 16, 'smeInv': 20})
        if h9 == 'auditor' and h4 == 'team lead':
            return mk({'type': 'survey_leave', 'eng': 0, 'date': 2, 'agent': 3, 'tl': 4,
                       'reason': 5, 'outcome': 6, 'resolution': -1, 'auditor': 9,
                       'assignedDate': 10, 'errCat': 13, 'errSub': 14, 'approveLeave': 16})
        if h8 == 'auditor' and n >= 15:
            return mk({'type': 'not_responsive', 'eng': 0, 'date': 2, 'agent': 3,
                       'reason': 4, 'outcome': 5, 'resolution': 6, 'auditor': 8,
                       'assignedDate': 9, 'errCat': 11, 'errSub': 12,
                       'approveLeave': 14, 'stuckInLimbo': 15})
        if h8 == 'auditor' and n >= 13:
            return mk({'type': 'survey_leave', 'eng': 0, 'date': 2, 'agent': 3,
                       'reason': 4, 'outcome': 5, 'resolution': 6, 'auditor': 8,
                       'errCat': 10, 'errSub': 11, 'approveLeave': 13})
    if h0 == 'agent name' and h7 == 'auditor':
        return mk({'type': 'mgr_escalation', 'eng': -1, 'date': 4, 'agent': 0,
                   'tl': 1, 'location': 2, 'auditor': 7, 'assignedDate': 8,
                   'escReason': 10, 'actioned': 14, 'daysAction': 15,
                   'errCat': 16, 'errSub': 17})
    return None

def load_cts(tabs):
    out = []
    for name, rows in tabs.items():
        if len(rows) < 2:
            continue
        hi, cd = -1, None
        for i in range(min(len(rows), 5)):
            d = _find_cts_cols(rows[i])
            if d:
                hi, cd = i, d
                break
        if hi < 0:
            continue
        eng_i = cd.get('eng', -1)
        for i in range(hi + 1, len(rows)):
            r = rows[i]
            def cell(idx):
                return r[idx] if 0 <= idx < len(r) else ''
            if eng_i >= 0:
                pk = S(cell(eng_i))
                if not pk or len(pk) != 36 or len(pk.split('-')) != 5:
                    continue
            else:
                pk = S(cell(0))
                if not pk or len(pk) < 2:
                    continue
            aud_i = cd.get('auditor', -1)
            aud = S(cell(aud_i)) if aud_i >= 0 else ''
            if not aud:
                continue
            errc_i = cd.get('errCat', -1)
            errs_i = cd.get('errSub', -1)
            err_cat = S(cell(errc_i)) if errc_i >= 0 else ''
            err_sub = S(cell(errs_i)) if errs_i >= 0 else ''
            if cd['type'] == 'long_engagement':
                op_i = cd.get('operEff', -1)
                av_i = cd.get('avoidedResolve', -1)
                sm_i = cd.get('smeInv', -1)
                op = S(cell(op_i)) if op_i >= 0 else ''
                av = S(cell(av_i)) if av_i >= 0 else ''
                sm = S(cell(sm_i)) if sm_i >= 0 else ''
                if av == 'Tool Issue':
                    err_cat, err_sub = 'Tool Issue', av
                elif op and op != 'N/A':
                    err_cat, err_sub = 'Agent Error', op
                elif av and av != 'N/A':
                    err_cat, err_sub = 'Agent Error', av
                elif sm and sm != 'N/A':
                    err_cat, err_sub = 'Process Error', sm
            if err_cat == 'Non Agent Error':
                err_cat = 'Non-Agent Error'
            q_score = None
            if cd['type'] == 'cnr_scores':
                dim_keys = ['severity', 'autoSat', 'expressed', 'empathy',
                            'clarity', 'completeness', 'language']
                sv = []
                for k in dim_keys:
                    c = cd.get(k, -1)
                    if c is not None and c >= 0:
                        try:
                            val = float(S(cell(c)))
                        except (ValueError, TypeError):
                            continue
                        if not pd.isna(val):
                            sv.append(val)
                q_score = (sum(sv) / len(sv)) if sv else None
            reason_i = cd.get('reason', -1)
            rr = S(cell(reason_i)) if reason_i >= 0 else ''
            rp = rr.split('::')
            date_i = cd.get('date', -1)
            agent_i = cd.get('agent', -1)
            tl_i = cd.get('tl', -1)
            loc_i = cd.get('location', -1)
            asg_i = cd.get('assignedDate', -1)
            out_i = cd.get('outcome', -1)
            res_i = cd.get('resolution', -1)
            al_i = cd.get('approveLeave', -1)
            sl_i = cd.get('stuckInLimbo', -1)
            etm_i = cd.get('engTimeMins', -1)
            esc_i = cd.get('escReason', -1)
            try:
                eng_time = float(S(cell(etm_i)) or '0') if etm_i >= 0 else 0
            except (ValueError, TypeError):
                eng_time = 0
            if pd.isna(eng_time):
                eng_time = 0
            out.append({
                'batch': name, 'auditType': cd['type'], 'engagementId': pk,
                'date': dstr(cell(date_i)) if date_i >= 0 else '',
                'agent': S(cell(agent_i)) if agent_i >= 0 else '',
                'teamLeader': S(cell(tl_i)) if tl_i >= 0 else '',
                'location': S(cell(loc_i)).upper() if loc_i >= 0 else '',
                'auditor': aud,
                'assignedDate': dstr(cell(asg_i)) if asg_i >= 0 else '',
                'errorCategory': err_cat, 'errorSubCategory': err_sub,
                'reason': rp[0].strip(),
                'outcome': S(cell(out_i)) if out_i >= 0 else '',
                'resolution': S(cell(res_i)) if res_i >= 0 else '',
                'approveLeave': S(cell(al_i)) if al_i >= 0 else '',
                'stuckInLimbo': S(cell(sl_i)) if sl_i >= 0 else '',
                'engTimeMins': eng_time,
                'escReason': S(cell(esc_i)) if esc_i >= 0 else '',
                'qualityScore': q_score})
    return pd.DataFrame(out)

def _is_cara_header(row):
    return len(row) >= 11 and \
        S(row[0]).lower().strip() == 'engagement' and \
        S(row[10]).lower().strip() == 'auditor'

def _norm_cara_resolve_error(s):
    if not s or s == 'No Error':
        return 'No Error'
    l = s.lower()
    if 'not responsive' in l:
        return 'Customer Not Responsive'
    if 'not resolved' in l or 'ended incorrectly' in l:
        return 'Issue Not Resolved'
    if l.startswith('leave -') or l.startswith('resolve -'):
        return 'Incorrect Leave/Resolve'
    return 'Error'

def load_cara(tabs):
    out = []
    for name, rows in tabs.items():
        if len(rows) < 2:
            continue
        hi, v2 = -1, False
        for i in range(min(len(rows), 5)):
            if _is_cara_header(rows[i]):
                hi = i
                v2 = len(rows[i]) >= 28
                break
        if hi < 0:
            continue
        errC = 17 if v2 else 16
        errS = 18 if v2 else 17
        resE = 20 if v2 else 19
        appC = 15 if v2 else 14
        appR = -1 if v2 else 15
        intN = 16 if v2 else -1
        disC = 23 if v2 else 22
        ovC = 26 if v2 else 25
        for i in range(hi + 1, len(rows)):
            r = rows[i]
            def cell(idx):
                return r[idx] if 0 <= idx < len(r) else ''
            eng = S(cell(0))
            if not eng or len(eng) != 36 or len(eng.split('-')) != 5:
                continue
            aud = S(cell(10))
            if not aud:
                continue
            rr = S(cell(6)).split('::')
            out.append({
                'batch': name, 'engagementId': eng, 'date': dstr(cell(2)),
                'agent': S(cell(3)), 'teamLeader': S(cell(4)),
                'manager': S(cell(5)),
                'contactCategory': rr[0].strip(),
                'categoryGroup': rr[1].strip() if len(rr) > 1 else '',
                'outcome': S(cell(7)), 'crRating': S(cell(8)),
                'auditor': aud, 'assignedDate': dstr(cell(11)),
                'appropriateCategory': S(cell(appC)),
                'appropriateResolve': S(cell(appR)) if appR >= 0 else '',
                'internalNote': S(cell(intN)) if intN >= 0 else '',
                'errorCategory': S(cell(errC)),
                'errorSubCategory': S(cell(errS)),
                'resolveError': _norm_cara_resolve_error(S(cell(resE))),
                'disputeStatus': norm_cr_dispute(S(cell(disC))),
                'overallStatus': S(cell(ovC))})
    return pd.DataFrame(out)

def _is_gor_header(row):
    h0 = S(row[0] if len(row) > 0 else '').lower().replace('#', ' ').replace('\n', ' ').replace('\r', ' ').strip()
    return ('case' in h0
            and S(row[2] if len(row) > 2 else '').lower() == 'auditor'
            and S(row[6] if len(row) > 6 else '').lower() == 'agent name')

def load_gor(tabs) -> pd.DataFrame:
    rows_out = []
    for name, rows in tabs.items():
        if len(rows) < 2:
            continue
        hi = -1
        for i in range(min(len(rows), 5)):
            if _is_gor_header(rows[i]):
                hi = i
                break
        if hi < 0:
            continue
        for i in range(hi + 1, len(rows)):
            r = rows[i]
            cn = S(r[0] if len(r) > 0 else '')
            if not cn:
                continue
            st_val = S(r[4] if len(r) > 4 else '')
            if not st_val:
                continue
            aud = S(r[2] if len(r) > 2 else '')
            if not aud:
                continue
            ag = S(r[6] if len(r) > 6 else '').replace('​', '')
            cc = S(r[8] if len(r) > 8 else '').split('::')
            rows_out.append({
                'batch': name,
                'caseId': cn,
                'dateOfCreation': dstr(r[1] if len(r) > 1 else ''),
                'auditor': aud,
                'assignedDate': dstr(r[3] if len(r) > 3 else ''),
                'completionStatus': st_val,
                'exclusionReason': S(r[5] if len(r) > 5 else ''),
                'agentName': ag,
                'dealPermalink': S(r[7] if len(r) > 7 else ''),
                'contactCategory': cc[0].strip(),
                'contactGroup': cc[1].strip() if len(cc) > 1 else '',
                'errorCategory': S(r[9] if len(r) > 9 else ''),
                'errorSubCategory': S(r[10] if len(r) > 10 else ''),
                'errorDetail': S(r[11] if len(r) > 11 else ''),
                'csatRating': S(r[12] if len(r) > 12 else ''),
                'recommendations': S(r[13] if len(r) > 13 else ''),
            })
    return pd.DataFrame(rows_out)

def load_rfa(tabs) -> pd.DataFrame:
    rows_out = []
    for name, rows in tabs.items():
        if len(rows) < 2:
            continue
        hi = -1
        for i in range(min(len(rows), 5)):
            h0 = S(rows[i][0] if len(rows[i]) > 0 else '').lower()
            h3 = S(rows[i][3] if len(rows[i]) > 3 else '').lower()
            if h0 == 'timestamp' and h3 == 'agent name':
                hi = i
                break
        if hi < 0:
            continue
        for i in range(hi + 1, len(rows)):
            r = rows[i]
            if not S(r[0] if len(r) > 0 else ''):
                continue
            try:
                sc = float(S(r[22] if len(r) > 22 else '0').replace('%', ''))
            except (ValueError, TypeError):
                sc = 0.0
            try:
                t_yes = int(float(S(r[20] if len(r) > 20 else '0')))
            except (ValueError, TypeError):
                t_yes = 0
            try:
                t_no = int(float(S(r[21] if len(r) > 21 else '0')))
            except (ValueError, TypeError):
                t_no = 0
            rows_out.append({
                'timestamp': S(r[0] if len(r) > 0 else ''),
                'auditorEmail': S(r[1] if len(r) > 1 else ''),
                'caseLink': S(r[2] if len(r) > 2 else ''),
                'agentName': S(r[3] if len(r) > 3 else ''),
                'agentEmail': S(r[4] if len(r) > 4 else ''),
                'manager': S(r[5] if len(r) > 5 else ''),
                'transactionDate': dstr(r[6] if len(r) > 6 else ''),
                'probe': yna(r[7] if len(r) > 7 else ''),
                'investigate': yna(r[9] if len(r) > 9 else ''),
                'alternatives': yna(r[11] if len(r) > 11 else ''),
                'processPolicy': yna(r[13] if len(r) > 13 else ''),
                'redAlert': yna(r[15] if len(r) > 15 else ''),
                'finalOutcome': S(r[17] if len(r) > 17 else ''),
                'totalYes': t_yes,
                'totalNo': t_no,
                'agentScore': sc,
                'disputeStatus': norm_cr_dispute(S(r[23] if len(r) > 23 else '')),
                'week': S(r[27] if len(r) > 27 else ''),
            })
    return pd.DataFrame(rows_out)

def _find_psg_cols(row):
    n = len(row)
    if n < 8:
        return None

    def h(i):
        return S(row[i]).lower().replace('\n', ' ').replace('\r', ' ').strip()

    h0 = h(0)
    h4 = h(4) if n > 4 else ''
    h7 = h(7) if n > 7 else ''
    h8 = h(8) if n > 8 else ''
    h9 = h(9) if n > 9 else ''
    h12 = h(12) if n > 12 else ''
    default = {'reason': -1, 'outcome': -1, 'resolution': -1, 'approveLeave': -1,
               'stuckInLimbo': -1, 'tl': -1, 'location': -1, 'engTimeMins': -1,
               'operEff': -1, 'avoidedResolve': -1, 'smeInv': -1, 'escReason': -1,
               'severity': -1, 'autoSat': -1, 'expressed': -1, 'empathy': -1,
               'clarity': -1, 'completeness': -1, 'language': -1,
               'eng': -1, 'date': -1, 'agent': -1, 'auditor': -1, 'assignedDate': -1,
               'errCat': -1, 'errSub': -1, 'agentErrFirst': -1, 'disputed': -1}

    def mk(extra):
        d = dict(default)
        d.update(extra)
        return d

    if h0 == 'engagement':
        if h7 == 'severity':
            return mk({'type': 'cnr_scores', 'eng': 0, 'date': 2, 'agent': 3, 'reason': 4,
                       'outcome': 5, 'resolution': 6, 'severity': 7, 'autoSat': 8,
                       'expressed': 9, 'empathy': 10, 'clarity': 11, 'completeness': 12,
                       'language': 13})
        if 'seconds' in h4:
            return mk({'type': 'long_eng', 'eng': 0, 'date': 1, 'agent': 3, 'tl': 2,
                       'location': 9, 'auditor': 11, 'assignedDate': 12, 'engTimeMins': 5,
                       'operEff': 14, 'avoidedResolve': 16, 'smeInv': 20})
        if h4 == 'team leader':
            return mk({'type': 'cnr_audit', 'eng': 0, 'date': 2, 'agent': 3, 'tl': 4,
                       'auditor': 9, 'assignedDate': 10, 'reason': 5, 'outcome': 6,
                       'resolution': 7, 'errCat': 12, 'errSub': 13, 'approveLeave': 15,
                       'agentErrFirst': 17, 'disputed': 19})
        if h4 == 'team lead' and h12 == 'terminated by':
            return mk({'type': 'survey_avoid', 'eng': 0, 'date': 2, 'agent': 3, 'tl': 4,
                       'auditor': 9, 'assignedDate': 10, 'reason': 5, 'outcome': 6,
                       'errCat': 13, 'errSub': 14, 'approveLeave': 16})
        if h8 == 'auditor' and h9 == 'terminated by':
            return mk({'type': 'leave_misuse', 'eng': 0, 'date': 2, 'agent': 3, 'auditor': 8,
                       'reason': 4, 'outcome': 5, 'resolution': 6, 'errCat': 10, 'errSub': 11,
                       'approveLeave': 13})
    if h0 == 'agent name' and h7 == 'auditor':
        return mk({'type': 'mgr_esc', 'eng': -1, 'date': 4, 'agent': 0, 'tl': 1,
                   'location': 2, 'auditor': 7, 'assignedDate': 8, 'escReason': 10,
                   'errCat': 16, 'errSub': 17})
    return None

def load_psg(tabs):
    out = []
    for name, rows in tabs.items():
        if len(rows) < 2:
            continue
        hi = -1
        cd = None
        for i in range(min(len(rows), 5)):
            d = _find_psg_cols(rows[i])
            if d:
                hi = i
                cd = d
                break
        if hi < 0:
            continue
        for i in range(hi + 1, len(rows)):
            r = rows[i]
            if cd['eng'] >= 0:
                pk = S(r[0]) if len(r) > 0 else ''
                if not pk or len(pk) != 36 or len(pk.split('-')) != 5:
                    continue
            else:
                pk = S(r[0]) if len(r) > 0 else ''
                if not pk or len(pk) < 2:
                    continue
            ag = S(r[cd['agent']]) if cd['agent'] >= 0 and len(r) > cd['agent'] else ''
            if not ag:
                continue
            err_cat = S(r[cd['errCat']]) if cd['errCat'] >= 0 and len(r) > cd['errCat'] else ''
            err_sub = S(r[cd['errSub']]) if cd['errSub'] >= 0 and len(r) > cd['errSub'] else ''
            if cd['type'] == 'long_eng':
                op = S(r[cd['operEff']]) if cd['operEff'] >= 0 and len(r) > cd['operEff'] else ''
                av = S(r[cd['avoidedResolve']]) if cd['avoidedResolve'] >= 0 and len(r) > cd['avoidedResolve'] else ''
                sm = S(r[cd['smeInv']]) if cd['smeInv'] >= 0 and len(r) > cd['smeInv'] else ''
                if av == 'Tool Issue':
                    err_cat = 'Tool Issue'
                    err_sub = av
                elif op and op != 'N/A':
                    err_cat = 'Agent Error'
                    err_sub = op
                elif av and av != 'N/A':
                    err_cat = 'Agent Error'
                    err_sub = av
                elif sm and sm != 'N/A':
                    err_cat = 'Process Error'
                    err_sub = sm
            qs = None
            if cd['type'] == 'cnr_scores':
                dims = [cd['severity'], cd['autoSat'], cd['expressed'], cd['empathy'],
                        cd['clarity'], cd['completeness'], cd['language']]
                sv = []
                for c in dims:
                    if c and c >= 0 and len(r) > c:
                        try:
                            v = float(S(r[c]))
                            sv.append(v)
                        except (ValueError, TypeError):
                            pass
                qs = (sum(sv) / len(sv)) if sv else None
            rr = S(r[cd['reason']]) if cd['reason'] >= 0 and len(r) > cd['reason'] else ''
            rp = rr.split('::')
            out.append({
                'batch': name, 'auditType': cd['type'], 'engagementId': pk,
                'date': dstr(r[cd['date']]) if cd['date'] >= 0 and len(r) > cd['date'] else '',
                'agent': ag,
                'teamLeader': S(r[cd['tl']]) if cd['tl'] >= 0 and len(r) > cd['tl'] else '',
                'location': (S(r[cd['location']]).upper() if cd['location'] >= 0 and len(r) > cd['location'] else ''),
                'auditor': S(r[cd['auditor']]) if cd['auditor'] >= 0 and len(r) > cd['auditor'] else '',
                'assignedDate': dstr(r[cd['assignedDate']]) if cd['assignedDate'] >= 0 and len(r) > cd['assignedDate'] else '',
                'reason': rp[0].strip(),
                'outcome': S(r[cd['outcome']]) if cd['outcome'] >= 0 and len(r) > cd['outcome'] else '',
                'errorCategory': err_cat, 'errorSubCategory': err_sub,
                'agentError': S(r[cd['agentErrFirst']]) if cd['agentErrFirst'] >= 0 and len(r) > cd['agentErrFirst'] else '',
                'disputed': S(r[cd['disputed']]) if cd['disputed'] >= 0 and len(r) > cd['disputed'] else '',
                'approveLeave': S(r[cd['approveLeave']]) if cd['approveLeave'] >= 0 and len(r) > cd['approveLeave'] else '',
                'engTimeMins': (_to_float(r[cd['engTimeMins']]) if cd['engTimeMins'] >= 0 and len(r) > cd['engTimeMins'] else 0),
                'escReason': S(r[cd['escReason']]) if cd['escReason'] >= 0 and len(r) > cd['escReason'] else '',
                'qualityScore': qs,
            })
    return pd.DataFrame(out)

def load_mo_reg(tabs):
    def _is_mo_reg_hdr(row):
        return (len(row) >= 11 and
                S(row[0]).lower() == 'week' and
                S(row[4]).lower() == 'agent name' and
                S(row[10]).lower() == 'auditor')

    out = []
    for name, rows in tabs.items():
        if len(rows) < 2:
            continue
        hi = -1
        hl = 0
        for i in range(min(len(rows), 5)):
            if _is_mo_reg_hdr(rows[i]):
                hi = i
                hl = len(rows[i])
                break
        if hi < 0:
            continue
        zt_c = 22 if hl >= 20 else 14
        neg_c = 23 if hl >= 20 else 15
        for i in range(hi + 1, len(rows)):
            r = rows[i]
            eng = S(r[2]) if len(r) > 2 else ''
            if not eng or len(eng) != 36 or len(eng.split('-')) != 5:
                continue
            aud = S(r[10]) if len(r) > 10 else ''
            if not aud:
                continue
            out.append({
                'batch': name,
                'week': S(r[0]) if len(r) > 0 else '',
                'assignedDate': dstr(r[1]) if len(r) > 1 else '',
                'engagementId': eng,
                'caseId': S(r[3]) if len(r) > 3 else '',
                'agentName': S(r[4]) if len(r) > 4 else '',
                'agentEmail': S(r[5]) if len(r) > 5 else '',
                'channelType': S(r[6]) if len(r) > 6 else '',
                'transDate': dstr(r[8]) if len(r) > 8 else '',
                'teamLeader': S(r[9]) if len(r) > 9 else '',
                'auditor': aud,
                'completedOn': dstr(r[12]) if len(r) > 12 else '',
                'ztUsage': S(r[zt_c]) if len(r) > zt_c else '',
                'negImpact': S(r[neg_c]) if len(r) > neg_c else '',
            })
    return pd.DataFrame(out)

def load_mo_deal(tabs):
    def _is_moda_hdr(row):
        return (len(row) >= 4 and
                S(row[0]).lower() == 'status' and
                S(row[1]).lower() == 'issue category' and
                S(row[3]).lower() == 'case number')

    out = []
    for name, rows in tabs.items():
        if len(rows) < 2:
            continue
        hi = -1
        hl = 0
        for i in range(min(len(rows), 5)):
            if _is_moda_hdr(rows[i]):
                hi = i
                hl = len(rows[i])
                break
        if hi < 0:
            continue
        for i in range(hi + 1, len(rows)):
            r = rows[i]
            cn = S(r[3]) if len(r) > 3 else ''
            try:
                int(cn)
                cn_ok = True
            except (ValueError, TypeError):
                cn_ok = False
            if not cn or not cn_ok:
                continue
            aud = S(r[36]) if len(r) > 36 else ''
            if not aud:
                continue
            out.append({
                'batch': name,
                'status': S(r[0]) if len(r) > 0 else '',
                'issueSubcategory': S(r[2]) if len(r) > 2 else '',
                'caseNumber': cn,
                'dateOpened': dstr(r[4]) if len(r) > 4 else '',
                'caseOwner': S(r[8]) if len(r) > 8 else '',
                'accountName': S(r[9]) if len(r) > 9 else '',
                'alertRefundRate': _to_float(r[17]) if len(r) > 17 else 0,
                'alertOrders': _to_int(r[18]) if len(r) > 18 else 0,
                'alertRefunds': _to_int(r[19]) if len(r) > 19 else 0,
                'alertRefundedGR': _to_float(r[21]) if len(r) > 21 else 0,
                'featureCountry': S(r[32]) if len(r) > 32 else '',
                'dealUUID': S(r[33]) if len(r) > 33 else '',
                'auditor': aud,
                'dateAssigned': dstr(r[37]) if len(r) > 37 else '',
                'ztUsed': S(r[39]) if len(r) > 39 else '',
                'resIncomplete': S(r[40]) if len(r) > 40 else '',
                'caseHistoryChecked': S(r[41]) if len(r) > 41 else '',
                'refundReason': S(r[42]) if len(r) > 42 else '',
                'agentError': (S(r[44]) if hl > 44 and len(r) > 44 else ''),
            })
    return pd.DataFrame(out)

def _find_co_cols_h(row):
    c = {'set': -1, 'week': -1, 'agentName': -1, 'oppId': -1, 'process': -1,
         'tl': -1, 'date': -1, 'auditBy': -1, 'status': -1, 'completedOn': -1,
         'location': -1}
    has_ag = has_op = has_p = has_au = False
    for i in range(len(row)):
        h = S(row[i]).lower()
        if h == 'set':
            c['set'] = i
        elif h == 'week':
            c['week'] = i
        elif h == 'agent name':
            c['agentName'] = i
            has_ag = True
        elif h == 'opportunity id':
            c['oppId'] = i
            has_op = True
        elif h == 'process':
            c['process'] = i
            has_p = True
        elif h == 'team leader':
            c['tl'] = i
        elif h == 'audit by':
            c['auditBy'] = i
            has_au = True
        elif h == 'date':
            c['date'] = i
        elif h == 'status':
            c['status'] = i
        elif h in ('audited on', 'date of completion', 'to be completed on'):
            c['completedOn'] = i
        elif h == 'location':
            c['location'] = i
    return c if (has_ag and has_op and has_p and has_au) else None

def load_co(tabs):
    # Single combined dict of tabs; each worksheet name is prefixed with its
    # month source (e.g. 'April::<sheet>' / 'May::<sheet>'). The JS loaded two
    # spreadsheets (coApr -> 'April', coMay -> 'May') and concatenated them.
    out = []
    for name, rows in tabs.items():
        if '::' in name:
            month, sheet = name.split('::', 1)
        else:
            month, sheet = '', name
        cols = None
        for r in rows:
            d = _find_co_cols_h(r)
            if d:
                cols = d
                continue
            if not cols:
                continue
            ag = S(r[cols['agentName']]) if cols['agentName'] >= 0 and len(r) > cols['agentName'] else ''
            if not ag:
                continue
            op = S(r[cols['oppId']]) if cols['oppId'] >= 0 and len(r) > cols['oppId'] else ''
            if not op:
                continue
            loc = S(r[cols['location']]) if cols['location'] >= 0 and len(r) > cols['location'] else 'India'
            if cols['set'] >= 0 and len(r) > cols['set']:
                set_val = S(r[cols['set']])
            elif cols['week'] >= 0 and len(r) > cols['week']:
                set_val = S(r[cols['week']])
            else:
                set_val = ''
            out.append({
                'month': month, 'batch': sheet,
                'set': set_val,
                'agentName': ag, 'opportunityId': op,
                'process': S(r[cols['process']]) if cols['process'] >= 0 and len(r) > cols['process'] else '',
                'teamLeader': S(r[cols['tl']]) if cols['tl'] >= 0 and len(r) > cols['tl'] else '',
                'location': loc or 'India',
                'date': dstr(r[cols['date']]) if cols['date'] >= 0 and len(r) > cols['date'] else '',
                'auditor': S(r[cols['auditBy']]) if cols['auditBy'] >= 0 and len(r) > cols['auditBy'] else '',
                'status': S(r[cols['status']]) if cols['status'] >= 0 and len(r) > cols['status'] else '',
                'completedOn': dstr(r[cols['completedOn']]) if cols['completedOn'] >= 0 and len(r) > cols['completedOn'] else '',
            })
    return pd.DataFrame(out)


# ───────────────────── data orchestration (cached) ─────────────────────
def _co_tabs():
    out = {}
    for wbkey, month in (("coApr", "April"), ("coMay", "May")):
        for name, rows in read_workbook(wbkey).items():
            out[month + "::" + name] = rows
    return out


def _safe(fn, *a):
    try:
        return fn(*a), None
    except Exception as e:
        return pd.DataFrame(), str(e)


def _load_one(fn, wbkey):
    return fn(read_workbook(wbkey))


@st.cache_data(ttl=900, show_spinner="Loading data from Google Sheets…")
def load_all():
    data, errors = {}, {}
    # ── LIVE MODE: pull everything from the Apps Script JSON endpoint ──
    if APPS_SCRIPT_URL:
        try:
            return fetch_live()
        except Exception as e:
            return {}, {"Live fetch": str(e)}
    # ── LOCAL MODE: read downloaded .xlsx files / public export URLs ──
    plan = [
        ("calibration", load_calibration, "calibration"),
        ("disputes", load_disputes, "disputes"),
        ("flAudit", load_fl, "flAudit"),
        ("superAudit", load_super_audit, "superAudit"),
        ("cr", load_cr, "cr"),
        ("esc", load_esc, "esc"),
        ("cts", load_cts, "cts"),
        ("cara", load_cara, "cara"),
        ("gor", load_gor, "gor"),
        ("rfa", load_rfa, "rfa"),
        ("psg", load_psg, "psg"),
        ("moReg", load_mo_reg, "moReg"),
        ("moDeal", load_mo_deal, "moDeal"),
    ]
    for outkey, fn, wbkey in plan:
        df, err = _safe(_load_one, fn, wbkey)
        data[outkey] = df
        if err:
            errors[outkey] = err
    df, err = _safe(lambda: load_co(_co_tabs()))
    data["coa"] = df
    if err:
        errors["coa"] = err
    return data, errors


# ═══════════════════ TAB RENDERERS ═══════════════════

def render_calibration(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view')
        return

    # ---- Filters ----
    reviewers = sorted([r for r in df['reviewerName'].dropna().unique() if str(r).strip() != ''])
    weeks_all = sorted([int(w) for w in df['week'].dropna().unique()])
    wmin, wmax = (weeks_all[0], weeks_all[-1]) if weeks_all else (0, 0)

    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    with c1:
        proc = st.radio('Process', ['ALL', 'CS', 'MO', 'CO'], horizontal=True, key='calibration_process')
    with c2:
        reviewer = st.selectbox('Reviewer', ['ALL'] + reviewers, key='calibration_reviewer')
    with c3:
        week_from = st.selectbox('From Week', weeks_all, index=0, key='calibration_week_from') if weeks_all else wmin
    with c4:
        to_opts = [w for w in weeks_all if w >= week_from] or [week_from]
        week_to = st.selectbox('To Week', to_opts, index=len(to_opts) - 1, key='calibration_week_to') if weeks_all else wmax

    # ---- Apply filters ----
    fdf = df.copy()
    if proc != 'ALL':
        fdf = fdf[fdf['process'] == proc]
    if reviewer != 'ALL':
        fdf = fdf[fdf['reviewerName'] == reviewer]
    fdf = fdf[(fdf['week'] >= week_from) & (fdf['week'] <= week_to)]

    if fdf.empty:
        st.info('No data for this view')
        return

    # ---- KPIs ----
    n_entries = len(fdf)
    n_cases = fdf['caseId'].nunique()
    avg_score = fdf['overallScore'].mean()
    avg_var = fdf['variance'].mean()
    alignment = (fdf['variance'] == 0).mean() * 100 if n_entries else 0.0
    var_color = 'green' if avg_var <= 10 else ('orange' if avg_var <= 20 else 'red')

    kpi_row([
        dict(label='Total Entries', value=str(n_entries), hint=f'{n_cases} unique cases', color='blue'),
        dict(label='Avg Overall Score', value=f'{avg_score:.1f}%', hint='Higher is better', color='green'),
        dict(label='Avg Variance', value=f'{avg_var:.1f}%', hint='Lower is better', color=var_color),
        dict(label='Alignment Rate', value=f'{alignment:.1f}%', hint='Cases with 0% variance', color='green'),
    ])

    # ---- Weekly trend charts (line, per-process series) ----
    weeks = sorted([int(w) for w in fdf['week'].dropna().unique()])
    labels = [f'Wk{w}' for w in weeks]
    procs = [proc] if proc != 'ALL' else sorted(fdf['process'].dropna().unique())
    proc_colors = {p: PCOL.get(p, '#666') for p in procs}

    def mk_series(key):
        series = {}
        for p in procs:
            pd_p = fdf[fdf['process'] == p]
            vals = []
            for w in weeks:
                wd = pd_p[pd_p['week'] == w]
                vals.append(wd[key].mean() if len(wd) else None)
            series[p] = vals
        return series

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown('**Weekly Avg Overall Score**')
        st.plotly_chart(
            line_chart(labels, mk_series('overallScore'), colors=proc_colors, ymax=100, yfmt='%'),
            width="stretch",
        )
    with cc2:
        st.markdown('**Weekly Avg Variance**')
        st.plotly_chart(
            line_chart(labels, mk_series('variance'), colors=proc_colors, yfmt='%'),
            width="stretch",
        )

    # ---- Section Score Averages by Reviewer (grouped bars + overall line) ----
    rev_list = sorted(fdf['reviewerName'].dropna().unique())

    def rd(key):
        return [fdf[fdf['reviewerName'] == r][key].mean() for r in rev_list]

    st.markdown('**Section Score Averages by Reviewer**')
    sec_series = {
        'Res. Execution': rd('resExec'),
        'Bus. Logic': rd('busLogic'),
        'Cust. Rights': rd('custRights'),
        'Overall Score': rd('overallScore'),
    }
    sec_colors = {
        'Res. Execution': '#4285F4',
        'Bus. Logic': '#34A853',
        'Cust. Rights': '#EA4335',
        'Overall Score': '#FBBC04',
    }
    st.plotly_chart(
        stacked_bar(rev_list, sec_series, colors=sec_colors),
        width="stretch",
    )

    # ---- Reviewer Breakdown table ----
    st.markdown('**Reviewer Breakdown**')
    rows = []
    for r in rev_list:
        rdat = fdf[fdf['reviewerName'] == r]
        cnt = len(rdat)
        rows.append({
            'Reviewer': r,
            'Process': ', '.join(sorted(rdat['process'].dropna().unique())),
            'Entries': cnt,
            'Avg Score': rdat['overallScore'].mean(),
            'Avg Variance': rdat['variance'].mean(),
            'Alignment %': (rdat['variance'] == 0).mean() * 100 if cnt else 0.0,
            'Res. Exec': rdat['resExec'].mean(),
            'Bus. Logic': rdat['busLogic'].mean(),
            'Cust. Rights': rdat['custRights'].mean(),
        })
    tdf = pd.DataFrame(rows).sort_values('Avg Score', ascending=False).reset_index(drop=True)
    show_table(
        tdf,
        pct_cols=('Avg Variance', 'Alignment %', 'Res. Exec', 'Bus. Logic', 'Cust. Rights'),
        bar_cols=('Avg Score',),
        int_cols=('Entries',),
    )

def render_disputes(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view'); return

    SCOL = {'Accepted': '#137333', 'Non QA Error': '#1a73e8', 'Rejected': '#c5221f', 'Outside Window': '#e37400'}
    STATUSES = ['Accepted', 'Non QA Error', 'Rejected', 'Outside Window']

    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    with c1:
        status = st.radio('Status', ['ALL'] + STATUSES, horizontal=True, key='disputes_status')
    with c2:
        process = st.radio('Process', ['ALL', 'CS', 'MO', 'CO'], horizontal=True, key='disputes_process')
    with c3:
        reviewers = sorted([r for r in df['reviewer'].dropna().unique() if str(r).strip()])
        reviewer = st.selectbox('Reviewer', ['ALL'] + reviewers, key='disputes_reviewer')
    with c4:
        dtype = st.selectbox('Dispute Type', ['ALL', 'Additional Audit', 'Super Audit'], key='disputes_type')

    fdf = df.copy()
    if status != 'ALL':
        fdf = fdf[fdf['status'] == status]
    if process != 'ALL':
        fdf = fdf[fdf['process'] == process]
    if reviewer != 'ALL':
        fdf = fdf[fdf['reviewer'] == reviewer]
    if dtype != 'ALL':
        fdf = fdf[fdf['disputeType'] == dtype]

    # KPIs
    total = len(fdf)
    accepted = len(fdf[fdf['status'].isin(['Accepted', 'Non QA Error'])])
    rejected = len(fdf[fdf['status'].isin(['Rejected', 'Outside Window'])])
    with_days = fdf[fdf['daysToResolve'].notna()]
    avg_days = with_days['daysToResolve'].astype(float).mean() if len(with_days) else 0
    uniq = fdf['caseId'].nunique()

    kpi_row([
        dict(label='Total Disputes', value=str(total), hint=f'{uniq} unique cases', color='blue'),
        dict(label='Acceptance Rate', value=(f'{accepted/total*100:.1f}%' if total else '–'), hint='Accepted + Non QA Error', color='green'),
        dict(label='Rejection Rate', value=(f'{rejected/total*100:.1f}%' if total else '–'), hint='Rejected + Outside Window', color='red'),
        dict(label='Avg Days to Resolve', value=(f'{avg_days:.1f}d' if avg_days else '–'), hint='Dispute → resolved date', color='blue'),
    ])

    # Charts row: donut + reviewer stacked bar
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown('**Disputes by Status**')
        counts = [int((fdf['status'] == s).sum()) for s in STATUSES]
        st.plotly_chart(donut(STATUSES, counts, [SCOL[s] for s in STATUSES]), width="stretch")
    with ch2:
        st.markdown('**Disputes by Reviewer**')
        revs = sorted([r for r in fdf['reviewer'].dropna().unique() if str(r).strip()])
        rev_series = {s: [int(len(fdf[(fdf['reviewer'] == r) & (fdf['status'] == s)])) for r in revs] for s in STATUSES}
        st.plotly_chart(stacked_bar(revs, rev_series, {s: SCOL[s] for s in STATUSES}), width="stretch")

    # Trend by week (full width stacked bar)
    st.markdown('**Disputes Trend by Week**')
    weeks = sorted([int(w) for w in fdf['weekNumber'].dropna().unique()])
    wk_labels = [f'Wk {w}' for w in weeks]
    wk_series = {s: [int(len(fdf[(fdf['weekNumber'] == w) & (fdf['status'] == s)])) for w in weeks] for s in STATUSES}
    st.plotly_chart(stacked_bar(wk_labels, wk_series, {s: SCOL[s] for s in STATUSES}), width="stretch")

    # Table
    st.markdown('**Dispute Log**')
    tbl = pd.DataFrame({
        'Date': fdf['disputeDate'],
        'Process': fdf['process'],
        'Type': fdf['disputeType'],
        'Case': fdf['caseId'],
        'Agent': fdf['agent'],
        'Reviewer': fdf['reviewer'],
        'Score': fdf['agentScore'],
        'Attributes': fdf['attributes'],
        'Status': fdf['status'],
        'Days': fdf['daysToResolve'],
    })
    show_table(tbl, pct_cols=('Score',))

def render_flaudit(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view')
        return

    weeks_all = sorted([int(w) for w in df['week'].dropna().unique()])
    wmin, wmax = (weeks_all[0], weeks_all[-1]) if weeks_all else (0, 0)
    auditors = ['ALL'] + sorted([a for a in df['auditor'].dropna().unique() if str(a).strip()])
    tls = ['ALL'] + sorted([t for t in df['teamLeader'].dropna().unique() if str(t).strip()])
    OUTCOMES = ['Bucks Accepted', 'Agreed to use the voucher', 'OFP post retention attempt',
                'No Response from customer', 'Others']
    OCOL = ['#137333', '#34A853', '#e37400', '#4285F4', '#9aa0a6']

    c1, c2, c3, c4, c5 = st.columns([1, 1, 1.4, 1.4, 1.4])
    with c1:
        week_from = st.selectbox('From Week', weeks_all, index=0,
                                 key='flaudit_week_from') if weeks_all else wmin
    with c2:
        to_opts = [w for w in weeks_all if w >= week_from] or weeks_all
        week_to = st.selectbox('To Week', to_opts, index=len(to_opts) - 1,
                               key='flaudit_week_to') if weeks_all else wmax
    with c3:
        sel_auditor = st.selectbox('Auditor', auditors, index=0, key='flaudit_auditor')
    with c4:
        sel_tl = st.selectbox('Team Leader', tls, index=0, key='flaudit_teamleader')
    with c5:
        sel_outcome = st.selectbox('Outcome', ['ALL'] + OUTCOMES, index=0, key='flaudit_outcome')

    fdf = df[(df['week'] >= week_from) & (df['week'] <= week_to)].copy()
    if sel_auditor != 'ALL':
        fdf = fdf[fdf['auditor'] == sel_auditor]
    if sel_tl != 'ALL':
        fdf = fdf[fdf['teamLeader'] == sel_tl]
    if sel_outcome != 'ALL':
        fdf = fdf[fdf['finalOutcome'] == sel_outcome]

    # ---- KPIs ----
    total = len(fdf)
    n_agents = fdf['agentName'].nunique()
    pass_rate = pct_yes(fdf, 'followProcess')
    retained = len(fdf[fdf['finalOutcome'].isin(['Bucks Accepted', 'Agreed to use the voucher'])])
    ret_rate = (retained / total * 100) if total else 0.0
    fweeks = sorted([int(w) for w in fdf['week'].dropna().unique()])
    n_weeks = len(fweeks)
    weeks_hint = ('Wk ' + str(fweeks[0]) + ' – Wk ' + str(fweeks[-1])) if fweeks else ''
    pass_color = 'green' if pass_rate >= 80 else ('orange' if pass_rate >= 60 else 'red')

    kpi_row([
        dict(label='Total Cases', value=str(total), hint=str(n_agents) + ' unique agents', color='blue'),
        dict(label='Process Pass Rate', value=pass_rate.__format__('.1f') + '%',
             hint='Follow process = Yes', color=pass_color),
        dict(label='Retention Rate', value=ret_rate.__format__('.1f') + '%',
             hint='Bucks Accepted + Voucher used', color='green'),
        dict(label='Weeks Covered', value=str(n_weeks), hint=weeks_hint, color='blue'),
    ])

    # ---- Charts row 1 ----
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown('**Quality Criteria Pass Rates**')
        crit_keys = ['probe', 'investigate', 'alternatives', 'followProcess']
        crit_labels = ['Probe', 'Investigate', 'Alternatives', 'Process']
        yes_d = [int((fdf[k] == 'Yes').sum()) for k in crit_keys]
        no_d = [int((fdf[k] == 'No').sum()) for k in crit_keys]
        na_d = [int((fdf[k] == 'N/A').sum()) for k in crit_keys]
        fig_crit = stacked_bar(
            crit_labels,
            {'Yes': yes_d, 'No': no_d, 'N/A': na_d},
            colors={'Yes': '#34A853', 'No': '#EA4335', 'N/A': '#9aa0a6'},
            horizontal=True,
        )
        st.plotly_chart(fig_crit, width="stretch")
    with cc2:
        st.markdown('**Customer Outcome Distribution**')
        ocounts = [int((fdf['finalOutcome'] == o).sum()) for o in OUTCOMES]
        olabels = ['Bucks Accepted', 'Voucher Used', 'OFP post-retention', 'No Response', 'Others']
        fig_out = donut(olabels, ocounts, colors=OCOL)
        st.plotly_chart(fig_out, width="stretch")

    # ---- Weekly trend (full week axis from df, filtered values) ----
    st.markdown('**Weekly Process Pass Rate Trend**')
    trend_vals = []
    for w in weeks_all:
        wd = fdf[fdf['week'] == w]
        trend_vals.append(pct_yes(wd, 'followProcess') if len(wd) else None)
    fig_week = line_chart(
        ['Wk ' + str(w) for w in weeks_all],
        {'Process Pass Rate': trend_vals},
        colors={'Process Pass Rate': '#1a73e8'},
        ymax=100, yfmt='%',
    )
    st.plotly_chart(fig_week, width="stretch")

    # ---- Auditor Breakdown table ----
    st.markdown('**Auditor Breakdown**')
    auds = [a for a in fdf['auditor'].dropna().unique() if str(a).strip()]
    rows = []
    for a in auds:
        ad = fdf[fdf['auditor'] == a]
        n = len(ad)
        ret = len(ad[ad['finalOutcome'].isin(['Bucks Accepted', 'Agreed to use the voucher'])])
        rows.append({
            'Auditor': a,
            'Cases': n,
            'Pass Rate': round(pct_yes(ad, 'followProcess'), 1),
            'Probe': round(pct_yes(ad, 'probe'), 1),
            'Investigate': round(pct_yes(ad, 'investigate'), 1),
            'Alternatives': round(pct_yes(ad, 'alternatives'), 1),
            'Retention': round((ret / n * 100) if n else 0.0, 1),
            'Unique Agents': ad['agentName'].nunique(),
        })
    tdf = pd.DataFrame(rows, columns=['Auditor', 'Cases', 'Pass Rate', 'Probe', 'Investigate',
                                      'Alternatives', 'Retention', 'Unique Agents'])
    show_table(
        tdf,
        bar_cols=('Pass Rate', 'Probe', 'Investigate', 'Alternatives', 'Retention'),
        int_cols=('Cases', 'Unique Agents'),
    )

def render_sa(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view')
        return

    AUD_COLS = {'Arif': '#4285F4', 'Farzana': '#EA4335', 'Nanaiah': '#34A853', 'Sunil': '#FBBC04'}
    aud_palette = ['#4285F4', '#EA4335', '#34A853', '#FBBC04', '#9c27b0', '#00bcd4']
    cat_cols = ['#4285F4', '#34A853', '#FBBC04', '#EA4335', '#9aa0a6']
    proc_cols = ['#7b1fa2', '#4285F4', '#34A853', '#FBBC04', '#EA4335']

    # ── Filters ──
    batches_all = sorted([b for b in df['batch'].dropna().unique().tolist() if str(b) != ''])
    auditors_all = sorted([a for a in df['auditor'].dropna().unique().tolist() if str(a) != ''])
    procs_all = sorted([p for p in df['process'].dropna().unique().tolist() if str(p) != ''])
    cats_all = sorted([c for c in df['category'].dropna().unique().tolist() if str(c) != ''])

    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.2, 1])
    with c1:
        f_batch = st.selectbox('Batch', ['ALL'] + batches_all, key='sa_batch')
    with c2:
        f_auditor = st.selectbox('Auditor', ['ALL'] + auditors_all, key='sa_auditor')
    with c3:
        f_process = st.selectbox('Process', ['ALL'] + procs_all, key='sa_process')
    with c4:
        f_location = st.radio('Location', ['ALL', 'BLR', 'CHN'], horizontal=True, key='sa_location')
    with c5:
        f_category = st.selectbox('Category', ['ALL'] + cats_all, key='sa_category')

    fdf = df.copy()
    if f_batch != 'ALL':
        fdf = fdf[fdf['batch'] == f_batch]
    if f_auditor != 'ALL':
        fdf = fdf[fdf['auditor'] == f_auditor]
    if f_process != 'ALL':
        fdf = fdf[fdf['process'] == f_process]
    if f_location != 'ALL':
        fdf = fdf[fdf['location'] == f_location]
    if f_category != 'ALL':
        fdf = fdf[fdf['category'] == f_category]

    if fdf.empty:
        st.info('No data for this view')
        return

    # ── KPIs ──
    n_total = len(fdf)
    comp = int((fdf['status'].astype(str).str.lower() == 'completed').sum())
    comp_rate = comp / n_total * 100 if n_total else 0.0
    n_batches = fdf['batch'].nunique()
    n_tls = fdf[fdf['tlName'].astype(str) != '']['tlName'].nunique()
    n_agents = fdf[fdf['agentName'].astype(str) != '']['agentName'].nunique()
    comp_color = 'green' if comp_rate >= 95 else ('orange' if comp_rate >= 80 else 'red')

    kpi_row([
        dict(label='Total Cases', value=str(n_total),
             hint=str(n_batches) + (' batch' if n_batches == 1 else ' batches'), color='blue'),
        dict(label='Completion Rate', value='{:.1f}%'.format(comp_rate),
             hint=str(comp) + ' of ' + str(n_total) + ' completed', color=comp_color),
        dict(label='TLs Covered', value=str(n_tls), hint='unique team leaders', color='blue'),
        dict(label='Agents Covered', value=str(n_agents), hint='unique agents audited', color='blue'),
    ])

    auditors = sorted([a for a in fdf['auditor'].dropna().unique().tolist() if str(a) != ''])
    batches = sorted([b for b in fdf['batch'].dropna().unique().tolist() if str(b) != ''])

    # ── Cases per Batch by Auditor (stacked bar: batches × auditor) ──
    st.markdown('**Cases per Batch by Auditor**')
    series = {}
    aud_color_map = {}
    for i, a in enumerate(auditors):
        ad = fdf[fdf['auditor'] == a]
        series[a] = [int(((ad['batch'] == b)).sum()) for b in batches]
        aud_color_map[a] = AUD_COLS.get(a, aud_palette[i % len(aud_palette)])
    fig_work = stacked_bar(batches, series, colors=aud_color_map)
    st.plotly_chart(fig_work, width="stretch")

    # ── Row 2: Completion by Auditor + Category + Process ──
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown('**Completion by Auditor**')
        comp_data = []
        for a in auditors:
            ad = fdf[fdf['auditor'] == a]
            comp_data.append(
                (ad['status'].astype(str).str.lower() == 'completed').sum() / len(ad) * 100 if len(ad) else 0.0)
        comp_bar_colors = [AUD_COLS.get(a, aud_palette[i % len(aud_palette)]) for i, a in enumerate(auditors)]
        fig_comp = vbar(auditors, comp_data, colors=comp_bar_colors, yfmt='%')
        st.plotly_chart(fig_comp, width="stretch")
    with r2:
        st.markdown('**Category Distribution**')
        cats = [c for c in fdf['category'].dropna().unique().tolist() if str(c) != '']
        cat_counts = [int((fdf['category'] == c).sum()) for c in cats]
        cat_color_list = [cat_cols[i % len(cat_cols)] for i in range(len(cats))]
        fig_cat = donut(cats, cat_counts, colors=cat_color_list)
        st.plotly_chart(fig_cat, width="stretch")
    with r3:
        st.markdown('**Process Distribution**')
        procs = [p for p in fdf['process'].dropna().unique().tolist() if str(p) != '']
        proc_counts = [int((fdf['process'] == p).sum()) for p in procs]
        proc_color_list = [proc_cols[i % len(proc_cols)] for i in range(len(procs))]
        fig_proc = donut(procs, proc_counts, colors=proc_color_list)
        st.plotly_chart(fig_proc, width="stretch")

    # ── Auditor Summary table ──
    st.markdown('**Auditor Summary**')
    summary_rows = []
    for a in auditors:
        ad = fdf[fdf['auditor'] == a]
        c = int((ad['status'].astype(str).str.lower() == 'completed').sum())
        summary_rows.append({
            'Auditor': a,
            'Total': len(ad),
            'Completed': c,
            'Completion %': c / len(ad) * 100 if len(ad) else 0.0,
            'BLR': int((ad['location'] == 'BLR').sum()),
            'CHN': int((ad['location'] == 'CHN').sum()),
            'TLs': ad[ad['tlName'].astype(str) != '']['tlName'].nunique(),
            'Agents': ad[ad['agentName'].astype(str) != '']['agentName'].nunique(),
            'Batches': ad['batch'].nunique(),
        })
    summary_df = pd.DataFrame(summary_rows,
                              columns=['Auditor', 'Total', 'Completed', 'Completion %',
                                       'BLR', 'CHN', 'TLs', 'Agents', 'Batches'])
    show_table(summary_df, pct_cols=('Completion %',), bar_cols=('Completion %',),
               int_cols=('Total', 'Completed', 'BLR', 'CHN', 'TLs', 'Agents', 'Batches'))

    # ── Batch Detail table (batch × auditor) ──
    st.markdown('**Batch Detail**')
    batch_rows = []
    seen = set()
    for _, x in fdf.iterrows():
        key = (x['batch'], x['auditor'])
        if key in seen:
            continue
        seen.add(key)
        bd = fdf[(fdf['batch'] == x['batch']) & (fdf['auditor'] == x['auditor'])]
        c = int((bd['status'].astype(str).str.lower() == 'completed').sum())
        batch_rows.append({
            'Batch': x['batch'],
            'Auditor': x['auditor'],
            'Total': len(bd),
            'Completed': c,
            'Completion %': c / len(bd) * 100 if len(bd) else 0.0,
            'Top Process': top_val(bd['process']),
            'Top Category': top_val(bd['category']),
            'BLR': int((bd['location'] == 'BLR').sum()),
            'CHN': int((bd['location'] == 'CHN').sum()),
        })
    batch_df = pd.DataFrame(batch_rows,
                            columns=['Batch', 'Auditor', 'Total', 'Completed', 'Completion %',
                                     'Top Process', 'Top Category', 'BLR', 'CHN'])
    show_table(batch_df, pct_cols=('Completion %',), bar_cols=('Completion %',),
               int_cols=('Total', 'Completed', 'BLR', 'CHN'))

def render_cr(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view')
        return

    ERR_CATS = ['Agent Error', 'Non-Agent Error', 'Tools Error', 'Customer Error']
    ERRCOL = {'Agent Error': '#c5221f', 'Non-Agent Error': '#4285F4', 'Tools Error': '#e37400', 'Customer Error': '#34A853'}
    CR_CATS = ['Merchant not honoring', 'Voucher redeemed by mistake', 'Booking and availability issue', 'Delivered product issue']
    CR_CAT_SHORT = ['Merchant', 'Voucher', 'Booking', 'Delivered']
    CR_CAT_COL = ['#4285F4', '#34A853', '#FBBC04', '#EA4335']

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        cat = st.radio('Contact Category', ['ALL'] + CR_CATS, horizontal=True, key='cr_category')
    with c2:
        auditors_all = sorted([a for a in df['auditor'].dropna().unique() if str(a).strip()])
        auditor = st.selectbox('Auditor', ['ALL'] + auditors_all, key='cr_auditor')
    with c3:
        err_cat = st.selectbox('Error Category', ['ALL'] + ERR_CATS, key='cr_errorCat')
    with c4:
        tls_all = sorted([t for t in df['teamLeader'].dropna().unique() if str(t).strip()])
        team_leader = st.selectbox('Team Leader', ['ALL'] + tls_all, key='cr_teamLeader')

    fdf = df
    if cat != 'ALL':
        fdf = fdf[fdf['contactCategory'] == cat]
    if auditor != 'ALL':
        fdf = fdf[fdf['auditor'] == auditor]
    if err_cat != 'ALL':
        fdf = fdf[fdf['errorCategory'] == err_cat]
    if team_leader != 'ALL':
        fdf = fdf[fdf['teamLeader'] == team_leader]

    n = len(fdf)
    agents = fdf['agent'][fdf['agent'].astype(str).str.strip() != ''].nunique() if n else 0
    agents = len([a for a in fdf['agent'].dropna().unique() if str(a).strip()])
    agent_err = int((fdf['errorCategory'] == 'Agent Error').sum())
    resolve_err = int((fdf['resolveButtonError'] != 'No Error').sum())
    disputed = int((fdf['disputeStatus'] != '').sum())

    kpi_row([
        dict(label='Total Cases', value=str(n), hint=f'{agents} unique agents', color='blue'),
        dict(label='Agent Error Rate', value=(f'{agent_err / n * 100:.1f}%' if n else '–'), hint='Cases with Agent Error', color='red'),
        dict(label='Resolve Button Errors', value=(f'{resolve_err / n * 100:.1f}%' if n else '–'), hint='Incorrectly hit Resolve', color='orange'),
        dict(label='Dispute Rate', value=(f'{disputed / n * 100:.1f}%' if n else '–'), hint=f'{disputed} cases disputed', color='purple'),
    ])

    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown('**Error Category Distribution**')
        err_counts = [int((fdf['errorCategory'] == e).sum()) for e in ERR_CATS]
        st.plotly_chart(donut(ERR_CATS, err_counts, [ERRCOL[e] for e in ERR_CATS]), width="stretch")
    with g2:
        st.markdown('**Cases by Auditor**')
        auditors = sorted([a for a in fdf['auditor'].dropna().unique() if str(a).strip()])
        series = {}
        for e in ERR_CATS:
            series[e] = [int(((fdf['auditor'] == a) & (fdf['errorCategory'] == e)).sum()) for a in auditors]
        st.plotly_chart(stacked_bar(auditors, series, {e: ERRCOL[e] for e in ERR_CATS}), width="stretch")
    with g3:
        st.markdown('**Contact Category Mix**')
        cat_counts = [int((fdf['contactCategory'] == c).sum()) for c in CR_CATS]
        st.plotly_chart(donut(CR_CAT_SHORT, cat_counts, CR_CAT_COL), width="stretch")

    st.markdown('**Error Sub-Category Breakdown (Top 15)**')
    sub = fdf['errorSubCategory'][fdf['errorSubCategory'].astype(str).str.strip() != '']
    sub_counts = sub.value_counts().head(15)
    if len(sub_counts):
        st.plotly_chart(hbar(list(sub_counts.index), list(sub_counts.values), '#1a73e8'), width="stretch")

    st.markdown('**Team Leader Breakdown**')
    tls = [t for t in fdf['teamLeader'].dropna().unique() if str(t).strip()]
    rows = []
    for tl in tls:
        td = fdf[fdf['teamLeader'] == tl]
        tn = len(td)
        ae = int((td['errorCategory'] == 'Agent Error').sum())
        ne = int((td['errorCategory'] == 'Non-Agent Error').sum())
        te = int((td['errorCategory'] == 'Tools Error').sum())
        re_ = int((td['resolveButtonError'] != 'No Error').sum())
        rows.append({
            'Team Leader': tl,
            'Cases': tn,
            'Agent Error %': (ae / tn * 100) if tn else 0,
            'Non-Agent %': (ne / tn * 100) if tn else 0,
            'Tools Error %': (te / tn * 100) if tn else 0,
            'Resolve Error %': (re_ / tn * 100) if tn else 0,
            'Agents': len([a for a in td['agent'].dropna().unique() if str(a).strip()]),
        })
    tbl = pd.DataFrame(rows)
    if not tbl.empty:
        tbl = tbl.sort_values('Cases', ascending=False)
    show_table(
        tbl,
        bar_cols=('Agent Error %', 'Non-Agent %', 'Tools Error %', 'Resolve Error %'),
        int_cols=('Cases', 'Agents'),
    )

def render_esc(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view'); return

    ESC_ERR_CATS = ['CS - Agent Error', 'MO - Agent Error', 'Non-Agent Error', 'Tool Limitations']
    ESC_ERR_LABELS = ['CS Agent Error', 'MO Agent Error', 'Non-Agent Error', 'Tool Limitations']
    ESC_ERR_COL = {'CS - Agent Error': '#c5221f', 'MO - Agent Error': '#e37400',
                   'Non-Agent Error': '#4285F4', 'Tool Limitations': '#9c27b0'}
    ESC_SB_CATS = ['Correct', 'Incorrect', 'MO Invalid Rejection', 'N/A', 'No Reason Selected']
    ESC_SB_COL = {'Correct': '#137333', 'Incorrect': '#c5221f', 'MO Invalid Rejection': '#e37400',
                  'N/A': '#9aa0a6', 'No Reason Selected': '#5f6368'}

    # ── Filters ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        batches = sorted([b for b in df['batch'].dropna().unique() if str(b).strip()])
        f_batch = st.selectbox('Batch', ['ALL'] + batches, key='esc_batch')
    with c2:
        auds = sorted([a for a in df['auditor'].dropna().unique() if str(a).strip()])
        f_aud = st.selectbox('Auditor', ['ALL'] + auds, key='esc_auditor')
    with c3:
        f_err = st.selectbox('Error Category', ['ALL'] + ESC_ERR_CATS, key='esc_errcat')
    with c4:
        tls = sorted([t for t in df['csTl'].dropna().unique() if str(t).strip()])
        f_tl = st.selectbox('CS Team Leader', ['ALL'] + tls, key='esc_cstl')

    fdf = df.copy()
    if f_batch != 'ALL':
        fdf = fdf[fdf['batch'] == f_batch]
    if f_aud != 'ALL':
        fdf = fdf[fdf['auditor'] == f_aud]
    if f_err != 'ALL':
        fdf = fdf[fdf['errorCategory'] == f_err]
    if f_tl != 'ALL':
        fdf = fdf[fdf['csTl'] == f_tl]

    n = len(fdf)

    # ── KPIs ──
    n_batches = fdf['batch'][fdf['batch'].astype(str).str.strip() != ''].nunique()
    cs_err = int((fdf['errorCategory'] == 'CS - Agent Error').sum())
    mo_err = int((fdf['errorCategory'] == 'MO - Agent Error').sum())
    inval_sb = int((fdf['sendBackAssessment'] == 'MO Invalid Rejection').sum())
    kpi_row([
        dict(label='Total Cases', value=str(n),
             hint=str(n_batches) + ' batch' + ('es' if n_batches != 1 else ''), color='blue'),
        dict(label='CS Agent Error Rate', value=(f'{cs_err/n*100:.1f}%' if n else '–'),
             hint='Incorrect CS escalations', color='red'),
        dict(label='MO Agent Error Rate', value=(f'{mo_err/n*100:.1f}%' if n else '–'),
             hint='Invalid MO rejections', color='orange'),
        dict(label='MO Invalid Send-Back', value=(f'{inval_sb/n*100:.1f}%' if n else '–'),
             hint='MO rejected incorrectly', color='purple'),
    ])

    # ── Charts row 3 ──
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown('**Error Category Distribution**')
        err_counts = [int((fdf['errorCategory'] == e).sum()) for e in ESC_ERR_CATS]
        err_colors = [ESC_ERR_COL.get(e, '#9aa0a6') for e in ESC_ERR_CATS]
        st.plotly_chart(donut(ESC_ERR_LABELS, err_counts, colors=err_colors),
                        width="stretch")
    with g2:
        st.markdown('**Send-Back Assessment**')
        sb_counts = [int((fdf['sendBackAssessment'] == s).sum()) for s in ESC_SB_CATS]
        sb_colors = [ESC_SB_COL.get(s, '#9aa0a6') for s in ESC_SB_CATS]
        st.plotly_chart(vbar(ESC_SB_CATS, sb_counts, colors=sb_colors),
                        width="stretch")
    with g3:
        st.markdown('**Rejection Reason**')
        rej = fdf['rejectionReason'][fdf['rejectionReason'].astype(str).str.strip() != '']
        rej_counts = rej.value_counts().head(8)
        st.plotly_chart(hbar(list(rej_counts.index), list(rej_counts.values), color='#1a73e8'),
                        width="stretch")

    # ── Error sub-category breakdown (Top 15) ──
    st.markdown('**Error Sub-Category Breakdown (Top 15)**')
    sub = fdf['errorSubCategory'][fdf['errorSubCategory'].astype(str).str.strip() != '']
    sub_counts = sub.value_counts().head(15)

    def _sub_col(lbl):
        s = str(lbl)
        if s.startswith('CS -'):
            return ESC_ERR_COL['CS - Agent Error']
        if s.startswith('MO -'):
            return ESC_ERR_COL['MO - Agent Error']
        if s.startswith('Tool'):
            return ESC_ERR_COL['Tool Limitations']
        return ESC_ERR_COL['Non-Agent Error']

    sub_labels = list(sub_counts.index)
    sub_colors = [_sub_col(l) for l in sub_labels]
    st.plotly_chart(hbar(sub_labels, list(sub_counts.values), color=sub_colors),
                    width="stretch")

    # ── CS Team Leader Breakdown table ──
    st.markdown('**CS Team Leader Breakdown**')
    tl_list = [t for t in fdf['csTl'].dropna().unique() if str(t).strip()]
    rows = []
    for tl in tl_list:
        td = fdf[fdf['csTl'] == tl]
        m = len(td)
        cs = int((td['errorCategory'] == 'CS - Agent Error').sum())
        mo = int((td['errorCategory'] == 'MO - Agent Error').sum())
        na = int((td['errorCategory'] == 'Non-Agent Error').sum())
        iv = int((td['sendBackAssessment'] == 'MO Invalid Rejection').sum())
        agents = td['csAgent'][td['csAgent'].astype(str).str.strip() != ''].nunique()
        rows.append({
            'Team Leader': tl,
            'Cases': m,
            'CS Error %': (cs / m * 100) if m else 0.0,
            'MO Error %': (mo / m * 100) if m else 0.0,
            'Non-Agent %': (na / m * 100) if m else 0.0,
            'Invalid Send-Back %': (iv / m * 100) if m else 0.0,
            'CS Agents': agents,
        })
    tbl = pd.DataFrame(rows, columns=['Team Leader', 'Cases', 'CS Error %', 'MO Error %',
                                      'Non-Agent %', 'Invalid Send-Back %', 'CS Agents'])
    if not tbl.empty:
        tbl = tbl.sort_values('Cases', ascending=False)
    show_table(tbl,
               bar_cols=('CS Error %', 'MO Error %', 'Non-Agent %', 'Invalid Send-Back %'),
               int_cols=('Cases', 'CS Agents'))

def render_cts(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view')
        return

    CTS_ERR_CATS = ['Agent Error', 'Non-Agent Error', 'Process Error', 'Tool Issue']
    CTS_ERR_COL = {'Agent Error': '#c5221f', 'Non-Agent Error': '#4285F4',
                   'Process Error': '#9c27b0', 'Tool Issue': '#e37400'}
    CTS_TYPE_LABEL = {'survey_leave': 'Survey/Leave', 'not_responsive': 'Not Responsive',
                      'long_engagement': 'Long Engagement', 'mgr_escalation': 'Mgr Escalation'}

    # ---- Filters ----
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        type_opts = ['ALL', 'survey_leave', 'not_responsive', 'long_engagement', 'mgr_escalation']
        f_type = st.radio('Audit Type', type_opts,
                          format_func=lambda t: 'All' if t == 'ALL' else CTS_TYPE_LABEL.get(t, t),
                          horizontal=True, key='cts_audit_type')
    with c2:
        auditors_all = ['ALL'] + sorted([a for a in df['auditor'].dropna().unique() if str(a).strip()])
        f_auditor = st.selectbox('Auditor', auditors_all,
                                 format_func=lambda a: 'All Auditors' if a == 'ALL' else a,
                                 key='cts_auditor')
    with c3:
        errcat_opts = ['ALL', 'Agent Error', 'Non-Agent Error', 'Process Error', 'Tool Issue']
        f_errcat = st.selectbox('Error Category', errcat_opts,
                                format_func=lambda e: 'All Errors' if e == 'ALL' else e,
                                key='cts_errcat')
    with c4:
        tls_all = ['ALL'] + sorted([t for t in df['teamLeader'].dropna().unique() if str(t).strip()])
        f_tl = st.selectbox('Team Leader', tls_all,
                            format_func=lambda t: 'All TLs' if t == 'ALL' else t,
                            key='cts_tl')

    # ---- Apply filters ----
    fdf = df
    if f_type != 'ALL':
        fdf = fdf[fdf['auditType'] == f_type]
    if f_auditor != 'ALL':
        fdf = fdf[fdf['auditor'] == f_auditor]
    if f_errcat != 'ALL':
        fdf = fdf[fdf['errorCategory'] == f_errcat]
    if f_tl != 'ALL':
        fdf = fdf[fdf['teamLeader'] == f_tl]

    n = len(fdf)

    # ---- KPIs ----
    agents = fdf['agent'].dropna()
    agents = agents[agents.astype(str).str.strip() != '']
    n_agents = agents.nunique()
    auds = fdf['auditor'].dropna()
    auds = auds[auds.astype(str).str.strip() != '']
    n_auditors = auds.nunique()
    batches = fdf['batch'].dropna()
    batches = batches[batches.astype(str).str.strip() != '']
    n_batches = batches.nunique()
    agent_err = int((fdf['errorCategory'] == 'Agent Error').sum())
    other_err = int(fdf['errorCategory'].isin(['Non-Agent Error', 'Process Error']).sum())

    kpi_row([
        dict(label='Total Cases', value=str(n),
             hint=str(n_batches) + ' batch' + ('es' if n_batches != 1 else ''), color='blue'),
        dict(label='Agent Error Rate',
             value=(('%.1f' % (agent_err / n * 100)) + '%') if n else '-',
             hint='Cases with Agent Error', color='red'),
        dict(label='Non-Agent / Process',
             value=(('%.1f' % (other_err / n * 100)) + '%') if n else '-',
             hint='Non-Agent + Process errors', color='orange'),
        dict(label='Agents Audited', value=str(n_agents),
             hint=str(n_auditors) + ' auditor' + ('s' if n_auditors != 1 else ''), color='blue'),
    ])

    # ---- Charts row: donut + stacked-by-type + stacked-by-auditor ----
    g1, g2, g3 = st.columns(3)

    with g1:
        st.markdown('**Error Category Distribution**')
        err_counts = [int((fdf['errorCategory'] == e).sum()) for e in CTS_ERR_CATS]
        st.plotly_chart(
            donut(CTS_ERR_CATS, err_counts,
                  colors=[CTS_ERR_COL.get(e, '#9aa0a6') for e in CTS_ERR_CATS]),
            width="stretch")

    with g2:
        st.markdown('**Cases by Audit Type**')
        types = ['survey_leave', 'not_responsive', 'long_engagement', 'mgr_escalation']
        type_labels = [CTS_TYPE_LABEL[t] for t in types]
        series_type = {}
        for e in CTS_ERR_CATS:
            series_type[e] = [int(((fdf['auditType'] == t) & (fdf['errorCategory'] == e)).sum())
                              for t in types]
        st.plotly_chart(
            stacked_bar(type_labels, series_type,
                        colors={e: CTS_ERR_COL.get(e, '#9aa0a6') for e in CTS_ERR_CATS}),
            width="stretch")

    with g3:
        st.markdown('**Cases by Auditor**')
        aud_list = sorted([a for a in fdf['auditor'].dropna().unique() if str(a).strip()])
        series_aud = {}
        for e in CTS_ERR_CATS:
            series_aud[e] = [int(((fdf['auditor'] == a) & (fdf['errorCategory'] == e)).sum())
                             for a in aud_list]
        st.plotly_chart(
            stacked_bar(aud_list, series_aud,
                        colors={e: CTS_ERR_COL.get(e, '#9aa0a6') for e in CTS_ERR_CATS}),
            width="stretch")

    # ---- Error Sub-Category Breakdown (Top 15) ----
    st.markdown('**Error Sub-Category Breakdown (Top 15)**')
    sub_rows = fdf[fdf['errorSubCategory'].notna() & (fdf['errorSubCategory'].astype(str).str.strip() != '')]
    sub_counts = sub_rows['errorSubCategory'].value_counts()
    sub_top = sub_counts.head(15)
    # majority/first-seen errorCategory per sub-category (first occurrence, mirroring JS)
    sub_col_map = {}
    for _, r in sub_rows.iterrows():
        k = r['errorSubCategory']
        if k not in sub_col_map:
            sub_col_map[k] = r['errorCategory']
    sub_labels = list(sub_top.index)
    sub_vals = [int(v) for v in sub_top.values]
    if sub_labels:
        st.plotly_chart(
            hbar(sub_labels, sub_vals,
                 color=[CTS_ERR_COL.get(sub_col_map.get(l), '#1a73e8') for l in sub_labels]),
            width="stretch")
    else:
        st.info('No sub-category data')

    # ---- Team Leader / Agent Breakdown table ----
    st.markdown('**Team Leader / Agent Breakdown**')
    table_rows = []
    for ag in [a for a in fdf['agent'].dropna().unique() if str(a).strip()]:
        ad = fdf[fdf['agent'] == ag]
        cnt = len(ad)
        ae = int((ad['errorCategory'] == 'Agent Error').sum())
        ne = int((ad['errorCategory'] == 'Non-Agent Error').sum())
        atypes = []
        for t in ad['auditType']:
            lbl = CTS_TYPE_LABEL.get(t, t)
            if lbl not in atypes:
                atypes.append(lbl)
        table_rows.append({
            'Agent': ag,
            'Team Leader': top_val(ad['teamLeader']),
            'Audit Type': ', '.join([str(x) for x in atypes if str(x).strip()]),
            'Cases': cnt,
            'Agent Error %': (ae / cnt * 100) if cnt else 0.0,
            'Non-Agent %': (ne / cnt * 100) if cnt else 0.0,
            'Auditor': top_val(ad['auditor']),
        })
    tbl = pd.DataFrame(table_rows,
                       columns=['Agent', 'Team Leader', 'Audit Type', 'Cases',
                                'Agent Error %', 'Non-Agent %', 'Auditor'])
    if not tbl.empty:
        tbl = tbl.sort_values('Cases', ascending=False)
    show_table(tbl, pct_cols=('Agent Error %', 'Non-Agent %'),
               bar_cols=('Agent Error %', 'Non-Agent %'), int_cols=('Cases',))

def render_cara(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view')
        return

    CARA_ERR_CATS = ['Agent Error', 'Non-Agent Error', 'Customer Error', 'Tools Error']
    CARA_ERR_COL = {'Agent Error': '#c5221f', 'Non-Agent Error': '#4285F4',
                    'Customer Error': '#34A853', 'Tools Error': '#e37400'}

    # ── Filters ──
    batches = ['ALL'] + sorted([b for b in df['assignedDate'].dropna().unique() if S(b)])
    auditors = ['ALL'] + sorted([a for a in df['auditor'].dropna().unique() if S(a)])
    tls = ['ALL'] + sorted([t for t in df['teamLeader'].dropna().unique() if S(t)])
    err_opts = ['ALL'] + CARA_ERR_CATS

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        f_batch = st.selectbox('Batch', batches, key='cara_batch')
    with c2:
        f_auditor = st.selectbox('Auditor', auditors, key='cara_auditor')
    with c3:
        f_err = st.selectbox('Error Category', err_opts, key='cara_errcat')
    with c4:
        f_tl = st.selectbox('Team Leader', tls, key='cara_tl')

    fdf = df.copy()
    if f_batch != 'ALL':
        fdf = fdf[fdf['assignedDate'] == f_batch]
    if f_auditor != 'ALL':
        fdf = fdf[fdf['auditor'] == f_auditor]
    if f_err != 'ALL':
        fdf = fdf[fdf['errorCategory'] == f_err]
    if f_tl != 'ALL':
        fdf = fdf[fdf['teamLeader'] == f_tl]

    if fdf.empty:
        st.info('No data for this view')
        return

    n = len(fdf)

    # ── KPIs ──
    agents = fdf['agent'].apply(lambda x: S(x)).replace('', pd.NA).dropna().nunique()
    agent_err = int((fdf['errorCategory'] == 'Agent Error').sum())
    res_err = int((fdf['resolveError'] != 'No Error').sum())
    note_rows = fdf[fdf['internalNote'].apply(lambda x: S(x)) != '']
    note_ok = int((note_rows['internalNote'] == 'Internal Notes Added').sum())

    kpi_row([
        dict(label='Total Cases', value=str(n),
             hint=str(agents) + ' unique agents', color='blue'),
        dict(label='Agent Error Rate',
             value=(f'{agent_err / n * 100:.1f}%' if n else '–'),
             hint='Cases with Agent Error', color='red'),
        dict(label='Resolve Error Rate',
             value=(f'{res_err / n * 100:.1f}%' if n else '–'),
             hint='Incorrect Resolve / Leave', color='orange'),
        dict(label='Internal Note Compliance',
             value=(f'{note_ok / len(note_rows) * 100:.1f}%' if len(note_rows) else '–'),
             hint='Notes added correctly (Mar batch)', color='green'),
    ])

    # ── Charts row 1 ──
    r1c1, r1c2, r1c3 = st.columns(3)

    with r1c1:
        st.markdown('**Error Category Distribution**')
        err_counts = [int((fdf['errorCategory'] == e).sum()) for e in CARA_ERR_CATS]
        donut_fig = donut(CARA_ERR_CATS, err_counts,
                          colors=[CARA_ERR_COL.get(e, '#9aa0a6') for e in CARA_ERR_CATS])
        st.plotly_chart(donut_fig, width="stretch")

    with r1c2:
        st.markdown('**Monthly Trend by Error Category**')
        month_cats = sorted([b for b in fdf['assignedDate'].dropna().unique() if S(b)])
        month_series = {}
        for e in CARA_ERR_CATS:
            month_series[e] = [int(((fdf['assignedDate'] == b) & (fdf['errorCategory'] == e)).sum())
                               for b in month_cats]
        month_fig = stacked_bar(month_cats, month_series,
                                colors={e: CARA_ERR_COL.get(e, '#9aa0a6') for e in CARA_ERR_CATS})
        st.plotly_chart(month_fig, width="stretch")

    with r1c3:
        st.markdown('**Cases by Auditor**')
        aud_cats = sorted([a for a in fdf['auditor'].dropna().unique() if S(a)])
        aud_series = {}
        for e in CARA_ERR_CATS:
            aud_series[e] = [int(((fdf['auditor'] == a) & (fdf['errorCategory'] == e)).sum())
                             for a in aud_cats]
        aud_fig = stacked_bar(aud_cats, aud_series,
                              colors={e: CARA_ERR_COL.get(e, '#9aa0a6') for e in CARA_ERR_CATS})
        st.plotly_chart(aud_fig, width="stretch")

    # ── Error Sub-Category Breakdown (Top 15) ──
    st.markdown('**Error Sub-Category Breakdown (Top 15)**')
    sub_map = {}
    sub_cat_map = {}
    for _, x in fdf.iterrows():
        sc = S(x['errorSubCategory'])
        if sc:
            sub_map[sc] = sub_map.get(sc, 0) + 1
            if sc not in sub_cat_map:
                sub_cat_map[sc] = x['errorCategory']
    sub_entries = sorted(sub_map.items(), key=lambda kv: kv[1], reverse=True)[:15]
    if sub_entries:
        sub_labels = [k for k, _ in sub_entries]
        sub_vals = [c for _, c in sub_entries]
        # hbar takes a single color; render manually to keep per-bar parent-category colors
        sub_colors = [CARA_ERR_COL.get(sub_cat_map.get(k), '#1a73e8') for k in sub_labels]
        # sorted desc by value; hbar expects this. Use go.Figure for per-bar colors.
        sub_fig = go.Figure(go.Bar(
            x=list(reversed(sub_vals)),
            y=list(reversed(sub_labels)),
            orientation='h',
            marker=dict(color=list(reversed(sub_colors))),
        ))
        sub_fig.update_layout(margin=dict(l=10, r=10, t=10, b=10),
                              showlegend=False, height=380)
        st.plotly_chart(sub_fig, width="stretch")

    # ── Team Leader Breakdown table ──
    st.markdown('**Team Leader Breakdown**')
    tl_list = [t for t in fdf['teamLeader'].dropna().unique() if S(t)]
    rows = []
    for tl in tl_list:
        td = fdf[fdf['teamLeader'] == tl]
        tn = len(td)
        ae = int((td['errorCategory'] == 'Agent Error').sum())
        ne = int((td['errorCategory'] == 'Non-Agent Error').sum())
        te = int((td['errorCategory'] == 'Tools Error').sum())
        re_ = int((td['resolveError'] != 'No Error').sum())
        ag = td['agent'].apply(lambda x: S(x)).replace('', pd.NA).dropna().nunique()
        rows.append({
            'Team Leader': tl,
            'Cases': tn,
            'Agent Error %': (ae / tn * 100 if tn else 0),
            'Non-Agent %': (ne / tn * 100 if tn else 0),
            'Tools Error %': (te / tn * 100 if tn else 0),
            'Resolve Error %': (re_ / tn * 100 if tn else 0),
            'Agents': ag,
        })
    tbl = pd.DataFrame(rows, columns=['Team Leader', 'Cases', 'Agent Error %',
                                      'Non-Agent %', 'Tools Error %',
                                      'Resolve Error %', 'Agents'])
    if not tbl.empty:
        tbl = tbl.sort_values('Cases', ascending=False)
    show_table(
        tbl,
        bar_cols=('Agent Error %', 'Non-Agent %', 'Tools Error %', 'Resolve Error %'),
        int_cols=('Cases', 'Agents'),
    )

def render_gor(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view')
        return

    GOR_ERR_COL = {'Agent Error': '#c5221f', 'Non-Agent Error': '#4285F4', 'Tools Error': '#e37400'}
    GOR_ERR_CATS = ['Agent Error', 'Non-Agent Error', 'Tools Error']
    GOR_CSAT_VALS = ['5', '3', '1', 'Yes', 'No', 'N/A']
    GOR_CSAT_COL = {'5': '#137333', '3': '#e37400', '1': '#c5221f', 'Yes': '#34A853', 'No': '#ea4335', 'N/A': '#9aa0a6'}

    # ── Filters ──
    batches_all = sorted([b for b in df['assignedDate'].dropna().unique() if str(b).strip()])
    auditors_all = sorted([a for a in df['auditor'].dropna().unique() if str(a).strip()])
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        f_batch = st.selectbox('Batch', ['ALL'] + batches_all, key='gor_batch')
    with c2:
        f_auditor = st.selectbox('Auditor', ['ALL'] + auditors_all, key='gor_auditor')
    with c3:
        f_errcat = st.selectbox('Error Category', ['ALL', 'Agent Error', 'Non-Agent Error', 'Tools Error'], key='gor_errcat')

    fdf = df.copy()
    if f_batch != 'ALL':
        fdf = fdf[fdf['assignedDate'] == f_batch]
    if f_auditor != 'ALL':
        fdf = fdf[fdf['auditor'] == f_auditor]
    if f_errcat != 'ALL':
        fdf = fdf[fdf['errorCategory'] == f_errcat]

    comp = fdf[fdf['completionStatus'] == 'Completed']

    # ── KPIs ──
    total = len(fdf)
    completed = int((fdf['completionStatus'] == 'Completed').sum())
    excluded = int((fdf['completionStatus'] == 'Excluded').sum())
    agent_err = int((comp['errorCategory'] == 'Agent Error').sum())

    def _csat_num(series):
        nums = []
        for v in series:
            try:
                nums.append(int(v))
            except (ValueError, TypeError):
                pass
        return nums

    csat_nums = _csat_num(comp['csatRating'])
    avg_csat = (sum(csat_nums) / len(csat_nums)) if csat_nums else None

    kpi_row([
        dict(label='Total Cases', value=str(total),
             hint='%d completed, %d excluded' % (completed, excluded), color='blue'),
        dict(label='Exclusion Rate', value=('%.1f%%' % (excluded / total * 100)) if total else '–',
             hint='Cases excluded from audit', color='orange'),
        dict(label='Agent Error Rate', value=('%.1f%%' % (agent_err / len(comp) * 100)) if len(comp) else '–',
             hint='Of completed audits', color='red'),
        dict(label='Avg CSAT Score', value=('%.1f' % avg_csat) if avg_csat is not None else '–',
             hint='Numeric scores (1 / 3 / 5) only', color='green'),
    ])

    # ── Charts row 1 ──
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        st.markdown('**Error Category Distribution**')
        err_counts = [int((comp['errorCategory'] == e).sum()) for e in GOR_ERR_CATS]
        fig = donut(GOR_ERR_CATS, err_counts,
                    colors=[GOR_ERR_COL.get(e, '#9aa0a6') for e in GOR_ERR_CATS])
        st.plotly_chart(fig, width="stretch")
    with r1c2:
        st.markdown('**CSAT Score Distribution**')
        csat_counts = [int((comp['csatRating'] == v).sum()) for v in GOR_CSAT_VALS]
        fig = vbar(GOR_CSAT_VALS, csat_counts,
                   colors=[GOR_CSAT_COL.get(v, '#9aa0a6') for v in GOR_CSAT_VALS])
        st.plotly_chart(fig, width="stretch")
    with r1c3:
        st.markdown('**Batch Comparison**')
        batches = sorted([b for b in fdf['assignedDate'].dropna().unique() if str(b).strip()])
        series = {}
        for e in GOR_ERR_CATS:
            series[e] = [int(((comp['assignedDate'] == b) & (comp['errorCategory'] == e)).sum()) for b in batches]
        fig = stacked_bar(batches, series, colors={e: GOR_ERR_COL.get(e, '#9aa0a6') for e in GOR_ERR_CATS})
        st.plotly_chart(fig, width="stretch")

    # ── Error sub-category horizontal bar (top 12) ──
    st.markdown('**Error Sub-Category Breakdown (Top 12)**')
    sub_map = {}
    sub_cat_map = {}
    for _, x in comp.iterrows():
        sc = x['errorSubCategory']
        if sc and str(sc).strip():
            sub_map[sc] = sub_map.get(sc, 0) + 1
            if sc not in sub_cat_map:
                sub_cat_map[sc] = x['errorCategory']
    sub_entries = sorted(sub_map.items(), key=lambda kv: kv[1], reverse=True)[:12]
    if sub_entries:
        sub_labels = [k for k, _ in sub_entries]
        sub_vals = [c for _, c in sub_entries]
        fig = hbar(sub_labels, sub_vals)
        st.plotly_chart(fig, width="stretch")
    else:
        st.info('No sub-category data')

    # ── Agent Breakdown table ──
    st.markdown('**Agent Breakdown**')
    agents = [a for a in comp['agentName'].dropna().unique() if str(a).strip()]
    rows = []
    for ag in agents:
        ad = comp[comp['agentName'] == ag]
        n = len(ad)
        ae = int((ad['errorCategory'] == 'Agent Error').sum())
        ne = int((ad['errorCategory'] == 'Non-Agent Error').sum())
        csat_n = _csat_num(ad['csatRating'])
        avg = (sum(csat_n) / len(csat_n)) if csat_n else None
        rows.append({
            'Agent': ag,
            'Cases': n,
            'Agent Error %': (ae / n * 100) if n else 0.0,
            'Non-Agent %': (ne / n * 100) if n else 0.0,
            'Avg CSAT': round(avg, 1) if avg is not None else None,
            'Auditor': top_val(ad['auditor']),
        })
    tdf = pd.DataFrame(rows, columns=['Agent', 'Cases', 'Agent Error %', 'Non-Agent %', 'Avg CSAT', 'Auditor'])
    if not tdf.empty:
        tdf = tdf.sort_values('Cases', ascending=False).reset_index(drop=True)
    show_table(tdf, bar_cols=('Agent Error %', 'Non-Agent %'), int_cols=('Cases',))

def render_rfa(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view')
        return

    RFA_SCORE_LABELS = ['0%', '25%', '50%', '75%', '100%']
    RFA_SCORE_VALUES = [0, 25, 50, 75, 100]
    RFA_SCORE_COL = ['#c5221f', '#e37400', '#ea8600', '#fbbc04', '#137333']
    RFA_OUTCOMES = ['Advised customer to wait', 'Agreed to use the voucher', 'Bucks Accepted',
                    'Escalated to other departments', 'Expiration Extension Denial', 'No Response from customer',
                    'OFP post retention attempt', 'Others', 'Refund Denied', 'Refund Status provided']
    RFA_OUTCOME_COL = ['#4285F4', '#34A853', '#34A853', '#EA4335', '#9aa0a6',
                       '#e37400', '#FBBC04', '#9aa0a6', '#c5221f', '#1a73e8']

    # ── Filters ──
    weeks = sorted([w for w in df['week'].dropna().unique() if str(w) != ''], key=lambda v: int(v))
    auditors = sorted([a for a in df['auditorEmail'].dropna().unique() if str(a).strip() != ''])
    managers = sorted([m for m in df['manager'].dropna().unique() if str(m).strip() != ''])

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        f_week = st.selectbox('Week', ['ALL'] + weeks, key='rfa_week')
    with c2:
        f_auditor = st.selectbox('Auditor', ['ALL'] + auditors, key='rfa_auditor')
    with c3:
        f_manager = st.selectbox('Reporting Manager', ['ALL'] + managers, key='rfa_manager')

    fdf = df
    if f_week != 'ALL':
        fdf = fdf[fdf['week'] == f_week]
    if f_auditor != 'ALL':
        fdf = fdf[fdf['auditorEmail'] == f_auditor]
    if f_manager != 'ALL':
        fdf = fdf[fdf['manager'] == f_manager]

    if fdf.empty:
        st.info('No data for this view')
        return

    # ── KPIs ──
    n = len(fdf)
    agents = fdf['agentName'][fdf['agentName'].astype(bool)].nunique()
    avg_score = fdf['agentScore'].mean() if n else 0
    full = (fdf['agentScore'] >= 100).sum()
    fail = (fdf['agentScore'] < 75).sum()
    avg_color = 'green' if avg_score >= 80 else 'orange' if avg_score >= 60 else 'red'

    kpi_row([
        dict(label='Total Audited', value=str(n), hint=f'{agents} unique agents', color='blue'),
        dict(label='Avg Agent Score', value=f'{avg_score:.1f}%', hint='Mean across all criteria', color=avg_color),
        dict(label='Full Pass Rate', value=(f'{full / n * 100:.1f}%' if n else '–'), hint='Score = 100%', color='green'),
        dict(label='Fail Rate', value=(f'{fail / n * 100:.1f}%' if n else '–'), hint='Score below 75%', color='red'),
    ])

    # ── Charts row 1 ──
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown('**Quality Criteria Pass Rates**')
        keys = ['probe', 'investigate', 'alternatives', 'processPolicy', 'redAlert']
        crit_labels = ['Probe', 'Investigate', 'Alternatives', 'Process/Policy', 'Red Alert']
        yes_d = [int((fdf[k] == 'Yes').sum()) for k in keys]
        no_d = [int((fdf[k] == 'No').sum()) for k in keys]
        fig = stacked_bar(crit_labels, {'Yes': yes_d, 'No': no_d},
                          colors={'Yes': '#34A853', 'No': '#EA4335'}, horizontal=True)
        st.plotly_chart(fig, width="stretch")
    with r1c2:
        st.markdown('**Agent Score Distribution**')
        rounded = fdf['agentScore'].round()
        score_counts = [int((rounded == v).sum()) for v in RFA_SCORE_VALUES]
        fig = vbar(RFA_SCORE_LABELS, score_counts, colors=RFA_SCORE_COL)
        st.plotly_chart(fig, width="stretch")

    # ── Charts row 2 ──
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown('**Final Outcome Distribution**')
        out_counts = [int((fdf['finalOutcome'] == o).sum()) for o in RFA_OUTCOMES]
        fig = donut(RFA_OUTCOMES, out_counts, colors=RFA_OUTCOME_COL)
        st.plotly_chart(fig, width="stretch")
    with r2c2:
        st.markdown('**Cases by Reporting Manager**')
        mgrs = sorted([m for m in fdf['manager'].dropna().unique() if str(m).strip() != ''])
        rounded_m = fdf['agentScore'].round()
        s_full = [int(((fdf['manager'] == m) & (fdf['agentScore'] >= 100)).sum()) for m in mgrs]
        s_75 = [int(((fdf['manager'] == m) & (rounded_m == 75)).sum()) for m in mgrs]
        s_low = [int(((fdf['manager'] == m) & (fdf['agentScore'] <= 50)).sum()) for m in mgrs]
        fig = stacked_bar(mgrs, {'100%': s_full, '75%': s_75, '≤50%': s_low},
                          colors={'100%': '#137333', '75%': '#fbbc04', '≤50%': '#c5221f'})
        st.plotly_chart(fig, width="stretch")

    # ── Agent table ──
    st.markdown('**Agent Breakdown**')
    table_agents = [a for a in fdf['agentName'].unique() if str(a) != '' and a is not None]
    rows = []
    for ag in table_agents:
        ad = fdf[fdf['agentName'] == ag]
        rows.append({
            'Agent': ag,
            'Manager': top_val(ad['manager']),
            'Cases': len(ad),
            'Avg Score': ad['agentScore'].mean(),
            'Probe %': pct_yes(ad, 'probe'),
            'Investigate %': pct_yes(ad, 'investigate'),
            'Alternatives %': pct_yes(ad, 'alternatives'),
            'Process %': pct_yes(ad, 'processPolicy'),
            'Red Alert %': pct_yes(ad, 'redAlert'),
        })
    tdf = pd.DataFrame(rows)
    if not tdf.empty:
        tdf = tdf.sort_values('Avg Score', ascending=False)
    show_table(
        tdf,
        pct_cols=('Avg Score',),
        bar_cols=('Probe %', 'Investigate %', 'Alternatives %', 'Process %', 'Red Alert %'),
        int_cols=('Cases',),
    )

def render_psg(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view'); return

    PSG_TYPE_LABEL = {'cnr_audit': 'CNR Audit', 'cnr_scores': 'CNR Score',
                      'survey_avoid': 'Survey Avoid', 'leave_misuse': 'Leave Misuse',
                      'long_eng': 'Long Engagement', 'mgr_esc': 'Mgr Escalation'}
    PSG_TYPE_COL = {'cnr_audit': '#4285F4', 'cnr_scores': '#34A853', 'survey_avoid': '#FBBC04',
                    'leave_misuse': '#EA4335', 'long_eng': '#9c27b0', 'mgr_esc': '#e37400'}
    PSG_ERR_COL = {'Agent Error': '#c5221f', 'Non-Agent Error': '#4285F4',
                   'Process Error': '#9c27b0', 'Tool Issue': '#e37400'}

    # ── Filters ──
    type_opts = ['ALL', 'cnr_audit', 'cnr_scores', 'survey_avoid', 'leave_misuse', 'long_eng', 'mgr_esc']
    type_btn_labels = {'ALL': 'All', 'cnr_audit': 'CNR', 'cnr_scores': 'CNR Score',
                       'survey_avoid': 'Survey', 'leave_misuse': 'Leave',
                       'long_eng': 'Long Eng', 'mgr_esc': 'Mgr Esc'}
    agents_all = sorted([a for a in df['agent'].dropna().unique() if str(a).strip()])
    auditors_all = sorted([a for a in df['auditor'].dropna().unique() if str(a).strip()])

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        f_type = st.radio('Audit Type', type_opts, index=0, horizontal=True,
                          format_func=lambda t: type_btn_labels[t], key='psg_type')
    with c2:
        f_agent = st.selectbox('Agent', ['ALL'] + agents_all, index=0, key='psg_agent')
    with c3:
        f_auditor = st.selectbox('Auditor', ['ALL'] + auditors_all, index=0, key='psg_auditor')

    fdf = df.copy()
    if f_type != 'ALL':
        fdf = fdf[fdf['auditType'] == f_type]
    if f_agent != 'ALL':
        fdf = fdf[fdf['agent'] == f_agent]
    if f_auditor != 'ALL':
        fdf = fdf[fdf['auditor'] == f_auditor]

    if fdf.empty:
        st.info('No data for this view'); return

    # ── KPIs ──
    agents = [a for a in fdf['agent'].dropna().unique() if str(a).strip()]
    types_n = fdf['auditType'].nunique()
    agent_type_map = {}
    for _, x in fdf.iterrows():
        ag = x['agent']
        if ag and str(ag).strip():
            agent_type_map.setdefault(ag, set()).add(x['auditType'])
    multi_type = sum(1 for a in agent_type_map if len(agent_type_map[a]) > 1)
    agent_err = int((fdf['errorCategory'] == 'Agent Error').sum())
    score_rows = fdf[fdf['qualityScore'].notna()]
    avg_score = score_rows['qualityScore'].mean() if len(score_rows) else None

    kpi_row([
        {'label': 'Total Cases Flagged', 'value': str(len(fdf)),
         'hint': str(types_n) + ' audit type' + ('s' if types_n != 1 else ''), 'color': 'red'},
        {'label': 'Unique Agents Flagged', 'value': str(len(agents)),
         'hint': str(multi_type) + ' in 2+ types', 'color': 'orange'},
        {'label': 'Agent Error Rate',
         'value': (f'{agent_err / len(fdf) * 100:.1f}%' if len(fdf) else '–'),
         'hint': 'Cases with Agent Error', 'color': 'red'},
        {'label': 'Avg CNR Quality Score',
         'value': (f'{avg_score:.2f}/ 5' if avg_score is not None else '–'),
         'hint': '1–5 scale (CNR Score block)', 'color': 'green'},
    ])

    # ── Charts ──
    ch_types = ['cnr_audit', 'cnr_scores', 'survey_avoid', 'leave_misuse', 'long_eng', 'mgr_esc']
    type_labels = [PSG_TYPE_LABEL[t] for t in ch_types]
    type_counts = [int((fdf['auditType'] == t).sum()) for t in ch_types]
    type_colors = [PSG_TYPE_COL[t] for t in ch_types]

    agent_counts = fdf[fdf['agent'].astype(str).str.strip() != '']['agent'].value_counts()
    agent_entries = agent_counts.head(12)
    agent_labels = list(agent_entries.index)
    agent_vals = [int(v) for v in agent_entries.values]

    err_cats = ['Agent Error', 'Non-Agent Error', 'Process Error', 'Tool Issue']
    err_counts = [int((fdf['errorCategory'] == e).sum()) for e in err_cats]
    err_colors = [PSG_ERR_COL.get(e, '#9aa0a6') for e in err_cats]

    sub_counts = fdf[fdf['errorSubCategory'].astype(str).str.strip() != '']['errorSubCategory'].value_counts()
    sub_entries = sub_counts.head(12)
    sub_labels = list(sub_entries.index)
    sub_vals = [int(v) for v in sub_entries.values]
    sub_cat_map = {}
    for _, x in fdf.iterrows():
        sc = x['errorSubCategory']
        if sc and str(sc).strip() and sc not in sub_cat_map:
            sub_cat_map[sc] = x['errorCategory']

    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown('**Cases by Audit Type**')
        st.plotly_chart(vbar(type_labels, type_counts, colors=type_colors), width="stretch")
    with r2:
        st.markdown('**Top Flagged Agents**')
        st.plotly_chart(hbar(agent_labels, agent_vals, color='#EA4335'), width="stretch")
    with r3:
        st.markdown('**Error Category Distribution**')
        st.plotly_chart(donut(err_cats, err_counts, colors=err_colors), width="stretch")

    st.markdown('**Error Sub-Category Breakdown (Top 12)**')
    sub_colors = [PSG_ERR_COL.get(sub_cat_map.get(l), '#EA4335') for l in sub_labels]
    # hbar is single-color; render via stacked_bar to keep per-bar parent-category colors
    if sub_labels:
        rev_labels = sub_labels[::-1]
        rev_vals = sub_vals[::-1]
        rev_colors = sub_colors[::-1]
        fig_sub = go.Figure()
        fig_sub.add_trace(go.Bar(y=rev_labels, x=rev_vals, orientation='h',
                                 marker_color=rev_colors, showlegend=False))
        fig_sub.update_layout(margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_title=None, yaxis_title=None, height=320)
        st.plotly_chart(fig_sub, width="stretch")

    # ── Table: Agent Cross-Type Summary ──
    table_agents = [a for a in fdf['agent'].dropna().unique() if str(a).strip()]
    rows = []
    for ag in table_agents:
        ad = fdf[fdf['agent'] == ag]
        ae = int((ad['errorCategory'] == 'Agent Error').sum())
        srows = ad[ad['qualityScore'].notna()]
        avg = round(float(srows['qualityScore'].mean()), 2) if len(srows) else None
        rows.append({
            'Agent': ag,
            'Total': len(ad),
            'CNR': int((ad['auditType'] == 'cnr_audit').sum()),
            'Survey': int((ad['auditType'] == 'survey_avoid').sum()),
            'Leave': int((ad['auditType'] == 'leave_misuse').sum()),
            'Long Eng': int((ad['auditType'] == 'long_eng').sum()),
            'Mgr Esc': int((ad['auditType'] == 'mgr_esc').sum()),
            'CNR Score': avg,
            'Error %': round(ae / len(ad) * 100, 1) if len(ad) else 0.0,
        })
    tdf = pd.DataFrame(rows, columns=['Agent', 'Total', 'CNR', 'Survey', 'Leave',
                                      'Long Eng', 'Mgr Esc', 'CNR Score', 'Error %'])
    if not tdf.empty:
        tdf = tdf.sort_values('Total', ascending=False).reset_index(drop=True)
    st.markdown('**Agent Cross-Type Summary**')
    show_table(tdf, pct_cols=('Error %',),
               int_cols=('Total', 'CNR', 'Survey', 'Leave', 'Long Eng', 'Mgr Esc'))

def render_moa(df_reg, df_deal) -> None:
    view = st.radio('View', ['Regular Audits', 'Deal Alerts'], horizontal=True, key='moa_view')

    MOR_CH_COL = {'Email': '#4285F4', 'Chat': '#34A853', 'Voice': '#FBBC04'}
    MOD_SUB_COL = {'Consistent Refund Offender': '#c5221f', 'Redemption Offender': '#e37400', 'UK CMA Deal Investigation': '#4285F4'}

    if view == 'Regular Audits':
        df = df_reg
        if df is None or df.empty:
            st.info('No data for this view')
            return

        # ── Filters ──
        auditors_all = ['ALL'] + sorted([a for a in df['auditor'].dropna().unique() if str(a).strip()])
        tls_all = ['ALL'] + sorted([t for t in df['teamLeader'].dropna().unique() if str(t).strip()])
        c1, c2, c3 = st.columns(3)
        with c1:
            f_aud = st.selectbox('Auditor', auditors_all, key='moa_reg_auditor')
        with c2:
            f_ch = st.selectbox('Channel', ['ALL', 'Email', 'Chat', 'Voice'], key='moa_reg_channel')
        with c3:
            f_tl = st.selectbox('Team Leader', tls_all, key='moa_reg_tl')

        fdf = df.copy()
        if f_aud != 'ALL':
            fdf = fdf[fdf['auditor'] == f_aud]
        if f_ch != 'ALL':
            fdf = fdf[fdf['channelType'] == f_ch]
        if f_tl != 'ALL':
            fdf = fdf[fdf['teamLeader'] == f_tl]

        # ── KPIs ──
        n = len(fdf)
        agents = fdf['agentName'].dropna().loc[fdf['agentName'].astype(str).str.strip() != ''].nunique()
        auds = fdf['auditor'].dropna().loc[fdf['auditor'].astype(str).str.strip() != ''].nunique()
        weeks = ', '.join(str(w) for w in sorted(set(x for x in fdf['week'].tolist() if x not in (None, '', 0))))
        zt_yes = int((fdf['ztUsage'] == 'Yes').sum())
        neg_flag = int(fdf['negImpact'].apply(lambda v: bool(v) and str(v) != '' and str(v) != '0').sum())
        zt_rate = (zt_yes / n * 100) if n else 0.0
        kpi_row([
            dict(label='Total Cases', value=str(n), hint=('Week ' + weeks) if weeks else 'Week –', color='blue'),
            dict(label='Unique Agents', value=str(agents), hint=str(auds) + ' auditors', color='blue'),
            dict(label='ZT Usage Rate', value=(f'{zt_rate:.1f}%' if n else '–'), hint='ZT tool used', color='green'),
            dict(label='Negative Impact', value=str(neg_flag) + ' cases', hint='Cases with negative impact flagged', color='orange'),
        ])

        auds_all = sorted([a for a in fdf['auditor'].dropna().unique() if str(a).strip()])

        # ── Charts row ──
        ch1, ch2, ch3 = st.columns(3)
        with ch1:
            st.markdown('**Cases by Auditor**')
            vals = [int((fdf['auditor'] == a).sum()) for a in auds_all]
            st.plotly_chart(vbar(auds_all, vals, colors=['#1a73e8'] * len(auds_all)), width="stretch")
        with ch2:
            st.markdown('**Channel Distribution**')
            chs = ['Email', 'Chat', 'Voice']
            ch_vals = [int((fdf['channelType'] == c).sum()) for c in chs]
            st.plotly_chart(donut(chs, ch_vals, colors=[MOR_CH_COL[c] for c in chs]), width="stretch")
        with ch3:
            st.markdown('**ZT Usage by Auditor**')
            series = {
                'ZT Yes': [int(((fdf['auditor'] == a) & (fdf['ztUsage'] == 'Yes')).sum()) for a in auds_all],
                'ZT No': [int(((fdf['auditor'] == a) & (fdf['ztUsage'] == 'No')).sum()) for a in auds_all],
            }
            st.plotly_chart(stacked_bar(auds_all, series, colors={'ZT Yes': '#34A853', 'ZT No': '#EA4335'}), width="stretch")

        # ── TL horizontal bar ──
        st.markdown('**Cases by Team Leader**')
        tls = sorted([t for t in fdf['teamLeader'].dropna().unique() if str(t).strip()])
        tl_pairs = sorted([(t, int((fdf['teamLeader'] == t).sum())) for t in tls], key=lambda p: p[1], reverse=True)
        st.plotly_chart(hbar([p[0] for p in tl_pairs], [p[1] for p in tl_pairs], color='#4285F4'), width="stretch")

        # ── Auditor Summary table ──
        st.markdown('**Auditor Summary**')
        rows = []
        for a in auds_all:
            ad = fdf[fdf['auditor'] == a]
            tot = len(ad)
            zt = int((ad['ztUsage'] == 'Yes').sum())
            neg = int(ad['negImpact'].apply(lambda v: bool(v) and str(v) != '' and str(v) != '0').sum())
            ag = ad['agentName'].dropna().loc[ad['agentName'].astype(str).str.strip() != ''].nunique()
            rows.append({
                'Auditor': a,
                'Total': tot,
                'Email': int((ad['channelType'] == 'Email').sum()),
                'Chat': int((ad['channelType'] == 'Chat').sum()),
                'Voice': int((ad['channelType'] == 'Voice').sum()),
                'ZT %': (zt / tot * 100) if tot else 0.0,
                'Neg Impact %': (neg / tot * 100) if tot else 0.0,
                'Agents': ag,
            })
        tbl = pd.DataFrame(rows, columns=['Auditor', 'Total', 'Email', 'Chat', 'Voice', 'ZT %', 'Neg Impact %', 'Agents'])
        if not tbl.empty:
            tbl = tbl.sort_values('Total', ascending=False)
        show_table(tbl, pct_cols=('ZT %', 'Neg Impact %'), bar_cols=('ZT %', 'Neg Impact %'),
                   int_cols=('Total', 'Email', 'Chat', 'Voice', 'Agents'))

    else:
        df = df_deal
        if df is None or df.empty:
            st.info('No data for this view')
            return

        # ── Filters ──
        auditors_all = ['ALL'] + sorted([a for a in df['auditor'].dropna().unique() if str(a).strip()])
        ctrs_all = ['ALL'] + sorted([c for c in df['featureCountry'].dropna().unique() if str(c).strip()])
        c1, c2, c3 = st.columns(3)
        with c1:
            f_aud = st.selectbox('Auditor', auditors_all, key='moa_deal_auditor')
        with c2:
            f_sub = st.selectbox('Type', ['ALL', 'Consistent Refund Offender', 'Redemption Offender', 'UK CMA Deal Investigation'], key='moa_deal_subcategory')
        with c3:
            f_ctr = st.selectbox('Country', ctrs_all, key='moa_deal_country')

        fdf = df.copy()
        if f_aud != 'ALL':
            fdf = fdf[fdf['auditor'] == f_aud]
        if f_sub != 'ALL':
            fdf = fdf[fdf['issueSubcategory'] == f_sub]
        if f_ctr != 'ALL':
            fdf = fdf[fdf['featureCountry'] == f_ctr]

        # ── KPIs ──
        n = len(fdf)
        batches = fdf['batch'].dropna().loc[fdf['batch'].astype(str).str.strip() != ''].nunique()
        rates_only = fdf[fdf['alertRefundRate'] > 0]
        avg_rate = float(rates_only['alertRefundRate'].mean()) if len(rates_only) else 0.0
        res_inc = int((fdf['resIncomplete'] == 'Yes').sum())
        err_flag = int(fdf['agentError'].apply(lambda v: bool(v) and str(v) != '').sum())
        comm_rate = (res_inc / n * 100) if n else 0.0
        err_rate = (err_flag / n * 100) if n else 0.0
        kpi_row([
            dict(label='Total Audited', value=str(n), hint=str(batches) + (' batch' if batches == 1 else ' batches'), color='blue'),
            dict(label='Avg Refund Rate', value=f'{avg_rate:.1f}%', hint='Alert refund rate mean', color='red'),
            dict(label='Comments Incomplete', value=(f'{comm_rate:.1f}%' if n else '–'), hint='Resolution / case comments missing', color='orange'),
            dict(label='Agent Errors', value=(f'{err_rate:.1f}%' if n else '–'), hint='Cases with agent error noted', color='red'),
        ])

        # ── Charts row ──
        ch1, ch2, ch3 = st.columns(3)
        with ch1:
            st.markdown('**Issue Subcategory**')
            subs = ['Consistent Refund Offender', 'Redemption Offender', 'UK CMA Deal Investigation']
            sub_vals = [int((fdf['issueSubcategory'] == s).sum()) for s in subs]
            st.plotly_chart(donut(subs, sub_vals, colors=[MOD_SUB_COL[s] for s in subs]), width="stretch")
        with ch2:
            st.markdown('**Refund Rate Distribution**')
            buckets = ['<30%', '30-50%', '>=50%']
            bk_counts = [
                int(((fdf['alertRefundRate'] > 0) & (fdf['alertRefundRate'] < 30)).sum()),
                int(((fdf['alertRefundRate'] >= 30) & (fdf['alertRefundRate'] < 50)).sum()),
                int((fdf['alertRefundRate'] >= 50).sum()),
            ]
            st.plotly_chart(vbar(buckets, bk_counts, colors=['#137333', '#e37400', '#c5221f']), width="stretch")
        with ch3:
            st.markdown('**Country Distribution**')
            ctrs = sorted([c for c in fdf['featureCountry'].dropna().unique() if str(c).strip()])
            ctr_vals = [int((fdf['featureCountry'] == c).sum()) for c in ctrs]
            st.plotly_chart(vbar(ctrs, ctr_vals, colors=['#4285F4'] * len(ctrs)), width="stretch")

        # ── Deal Alert Case Log table ──
        st.markdown('**Deal Alert Case Log**')
        log = fdf.copy()
        if not log.empty:
            log = log.sort_values('alertRefundRate', ascending=False)
        tbl = pd.DataFrame({
            'Case #': log['caseNumber'],
            'Account': log['accountName'],
            'Type': log['issueSubcategory'],
            'Refund Rate': log['alertRefundRate'],
            'Orders': log['alertOrders'],
            'Country': log['featureCountry'],
            'Auditor': log['auditor'],
            'ZT': log['ztUsed'],
            'Comments': log['resIncomplete'],
            'Agent Error': log['agentError'],
        })
        show_table(tbl, pct_cols=('Refund Rate',), int_cols=('Orders',))

def render_coa(df) -> None:
    if df is None or df.empty:
        st.info('No data for this view')
        return

    COA_PROC_COL = {'Writing': '#4285F4', 'Vetting': '#34A853', 'Deal Edits': '#FBBC04'}
    procs = ['Writing', 'Vetting', 'Deal Edits']

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        month = st.radio('Month', ['ALL', 'April', 'May'], horizontal=True, key='coa_month')
    with c2:
        location = st.radio('Region', ['ALL', 'India', 'Albania'], horizontal=True, key='coa_region')
    with c3:
        aud_opts = ['ALL'] + sorted([a for a in df['auditor'].dropna().unique() if str(a).strip()])
        auditor = st.selectbox('Auditor', aud_opts, key='coa_auditor')
    with c4:
        process = st.selectbox('Process', ['ALL', 'Writing', 'Vetting', 'Deal Edits'], key='coa_process')

    fdf = df.copy()
    if month != 'ALL':
        fdf = fdf[fdf['month'] == month]
    if location != 'ALL':
        fdf = fdf[fdf['location'] == location]
    if auditor != 'ALL':
        fdf = fdf[fdf['auditor'] == auditor]
    if process != 'ALL':
        fdf = fdf[fdf['process'] == process]

    total = len(fdf)
    agents = fdf['agentName'].replace('', pd.NA).dropna().nunique()
    auditors = fdf['auditor'].replace('', pd.NA).dropna().nunique()
    regions = fdf['location'].replace('', pd.NA).dropna().nunique()
    months = fdf['month'].replace('', pd.NA).dropna().nunique()
    comp = int((fdf['status'] == 'Completed').sum())
    comp_rate = comp / total * 100 if total else 0.0
    comp_color = 'green' if comp_rate >= 90 else 'orange' if comp_rate >= 70 else 'red'

    kpi_row([
        dict(label='Total Assigned', value=str(total),
             hint=str(months) + ' month' + ('' if months == 1 else 's'), color='blue'),
        dict(label='Completion Rate', value='{:.1f}%'.format(comp_rate),
             hint='{} of {} completed'.format(comp, total), color=comp_color),
        dict(label='Agents Covered', value=str(agents),
             hint=str(regions) + ' region' + ('' if regions == 1 else 's'), color='blue'),
        dict(label='Auditors Active', value=str(auditors), hint='Unique auditors', color='blue'),
    ])

    ch1, ch2, ch3 = st.columns(3)
    with ch1:
        st.markdown('**Process Distribution**')
        pvals = [int((fdf['process'] == p).sum()) for p in procs]
        fig = donut(procs, pvals, colors=[COA_PROC_COL[p] for p in procs])
        st.plotly_chart(fig, width="stretch")
    with ch2:
        st.markdown('**Completion by Month**')
        months2 = ['April', 'May']
        completed = [int(((fdf['month'] == m) & (fdf['status'] == 'Completed')).sum()) for m in months2]
        pending = [int(((fdf['month'] == m) & (fdf['status'] != 'Completed')).sum()) for m in months2]
        fig = stacked_bar(months2, {'Completed': completed, 'Pending': pending},
                          colors={'Completed': '#137333', 'Pending': '#e8eaed'})
        st.plotly_chart(fig, width="stretch")
    with ch3:
        st.markdown('**Cases by Auditor**')
        auds = sorted([a for a in fdf['auditor'].dropna().unique() if str(a).strip()])
        series = {p: [int(((fdf['auditor'] == a) & (fdf['process'] == p)).sum()) for a in auds] for p in procs}
        fig = stacked_bar(auds, series, colors={p: COA_PROC_COL[p] for p in procs})
        st.plotly_chart(fig, width="stretch")

    st.markdown('**Top Agents by Audit Volume**')
    avol = fdf[fdf['agentName'].astype(str).str.strip() != '']['agentName'].value_counts().head(15)
    fig = hbar(list(avol.index), [int(v) for v in avol.values], color='#4285F4')
    st.plotly_chart(fig, width="stretch")

    st.markdown('**Agent Breakdown**')
    agent_set = [a for a in fdf['agentName'].dropna().unique() if str(a).strip()]
    rows = []
    for ag in agent_set:
        ad = fdf[fdf['agentName'] == ag]
        c = int((ad['status'] == 'Completed').sum())
        rows.append({
            'Agent': ag,
            'Region': top_val(ad['location']),
            'Total': len(ad),
            'Writing': int((ad['process'] == 'Writing').sum()),
            'Vetting': int((ad['process'] == 'Vetting').sum()),
            'Deal Edits': int((ad['process'] == 'Deal Edits').sum()),
            'Completed': c,
            '%': c / len(ad) * 100 if len(ad) else 0,
        })
    tdf = pd.DataFrame(rows, columns=['Agent', 'Region', 'Total', 'Writing', 'Vetting',
                                      'Deal Edits', 'Completed', '%'])
    if not tdf.empty:
        tdf = tdf.sort_values('Total', ascending=False)
    show_table(tdf, bar_cols=('%',),
               int_cols=('Total', 'Writing', 'Vetting', 'Deal Edits', 'Completed'))


# ───────────────────── QA Scorecard (#3 KPI summary) ─────────────────────
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SC_NUM_COLS = ["auditTargetPct", "calibrationPct", "disputeAcceptPct", "docErrorPct",
               "regAssigned", "regCompleted", "superAssigned", "superCompleted",
               "adhocAssigned", "adhocCompleted", "totalAssigned", "totalCompleted",
               "casesCalibrated", "disputesRaised", "validDisputes", "processImprov",
               "week", "year"]
SC_KPIS = [("auditTargetPct", "Audit Target", 100, "target 100%"),
           ("calibrationPct", "Calibration Accuracy", 90, "target 85–90%"),
           ("disputeAcceptPct", "Dispute Acceptance", 99, "target 95–99%"),
           ("docErrorPct", "Documentation", 98, "target 98%")]


def _sc_pct(v):
    return "–" if v is None or (isinstance(v, float) and pd.isna(v)) else f"{v:.1f}%"


def _sc_color(v, target):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "blue"
    if v >= target:
        return "green"
    if v >= target - 10:
        return "orange"
    return "red"


def _sc_mkey(m):
    return MONTH_ORDER.index(m) if m in MONTH_ORDER else 99


def _sc_avg(frame, col):
    if col not in frame.columns:
        return None
    v = pd.to_numeric(frame[col], errors="coerce").dropna()
    return float(v.mean()) if len(v) else None


def render_scorecard(df):
    st.caption("Per-QA performance KPIs — weekly & monthly, with current-vs-previous comparison.")
    if df is None or df.empty:
        st.info("No scorecard data yet. Add the scorecard source to Apps Script "
                "(getScorecardData) and deploy a New version, then ↻ Refresh.")
        return
    df = df.copy()
    for c in SC_NUM_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[df["qaName"].notna() & (df["qaName"].astype(str).str.strip() != "")]
    months_present = [m for m in MONTH_ORDER if m in set(df["month"].dropna())]

    fc = st.columns(3)
    with fc[0]:
        msel = st.selectbox("Month", ["All"] + months_present, key="sc_month")
    with fc[1]:
        qsel = st.selectbox("QA", ["All"] + sorted(df["qaName"].dropna().unique()), key="sc_qa")
    with fc[2]:
        weeks = sorted({int(w) for w in df["week"].dropna()})
        wsel = st.selectbox("Week", ["All"] + [str(w) for w in weeks], key="sc_week")

    d = df.copy()
    if msel != "All":
        d = d[d["month"] == msel]
    if qsel != "All":
        d = d[d["qaName"] == qsel]
    if wsel != "All":
        d = d[d["week"] == int(wsel)]
    if d.empty:
        st.info("No rows for this selection.")
        return

    # KPI cards (averages over the current selection)
    kpi_row([{"label": lbl, "value": _sc_pct(_sc_avg(d, col)), "hint": hint,
              "color": _sc_color(_sc_avg(d, col), tgt)} for col, lbl, tgt, hint in SC_KPIS])

    # Weekly trend (respects Month + QA, spans all weeks) + volume by QA
    dt = df.copy()
    if msel != "All":
        dt = dt[dt["month"] == msel]
    if qsel != "All":
        dt = dt[dt["qaName"] == qsel]
    wk_order = sorted({int(w) for w in dt["week"].dropna()})
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**Weekly KPI trend**")
        if wk_order:
            series = {lbl: [_sc_avg(dt[dt["week"] == w], col) for w in wk_order]
                      for col, lbl, _, _ in SC_KPIS}
            st.plotly_chart(line_chart(["Wk " + str(w) for w in wk_order], series, ymax=115),
                            width="stretch")
        else:
            st.info("No weekly data.")
    with c2:
        st.markdown("**Audit volume by QA**")
        vol = d.groupby("qaName").agg(Assigned=("totalAssigned", "sum"),
                                      Completed=("totalCompleted", "sum")).reset_index()
        st.plotly_chart(stacked_bar(list(vol["qaName"]),
                        {"Assigned": list(vol["Assigned"]), "Completed": list(vol["Completed"])},
                        horizontal=True), width="stretch")

    # Current vs previous month (the #3 core)
    st.markdown("### Current vs previous month")
    cmp_src = df if qsel == "All" else df[df["qaName"] == qsel]
    present = sorted(set(cmp_src["month"].dropna()), key=_sc_mkey)
    cur_m = msel if msel != "All" else (present[-1] if present else None)
    prev_m = None
    if cur_m in present:
        i = present.index(cur_m)
        prev_m = present[i - 1] if i > 0 else None
    if cur_m:
        st.caption(f"Current: **{cur_m}**" + (f"   ·   previous: **{prev_m}**" if prev_m
                   else "   ·   (no earlier month)"))
        rows = []
        for qa in sorted(cmp_src["qaName"].dropna().unique()):
            qd = cmp_src[cmp_src["qaName"] == qa]
            row = {"QA": qa}
            for col, lbl, _, _ in SC_KPIS:
                cur = _sc_avg(qd[qd["month"] == cur_m], col)
                row[lbl] = round(cur, 1) if cur is not None else None
                if prev_m:
                    prv = _sc_avg(qd[qd["month"] == prev_m], col)
                    row[lbl + " Δ"] = (round(cur - prv, 1)
                                       if (cur is not None and prv is not None) else None)
            rows.append(row)
        cmp_df = pd.DataFrame(rows)
        st.dataframe(cmp_df, width="stretch", hide_index=True)
        st.download_button("⬇ Download comparison (CSV)", cmp_df.to_csv(index=False).encode(),
                           file_name="qa_scorecard_comparison.csv", mime="text/csv", key="sc_dl")

    # Per-QA detail for the current selection
    st.markdown("### Per-QA detail (current selection)")
    rows = []
    for qa in sorted(d["qaName"].dropna().unique()):
        g = d[d["qaName"] == qa]
        row = {"QA": qa,
               "Samples": int(pd.to_numeric(g["totalCompleted"], errors="coerce").fillna(0).sum())}
        for col, lbl, _, _ in SC_KPIS:
            a = _sc_avg(g, col)
            row[lbl] = round(a, 1) if a is not None else None
        rows.append(row)
    detail = pd.DataFrame(rows)
    show_table(detail, pct_cols=tuple(lbl for _, lbl, _, _ in SC_KPIS), int_cols=("Samples",))


# ───────────────────── Work Requests (#2 ideations) ─────────────────────
WR_MONTHS = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
             7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
WR_STATUS = ["Open", "WIP", "Closed"]
WR_STATUS_COL = {"Open": "#1a73e8", "WIP": "#e37400", "Closed": "#137333"}


def render_workrequests(df):
    st.caption("Process-improvement ideations / work requests raised by each QA (target: 4 per QA per month).")
    if df is None or df.empty:
        st.info("No work-request data yet. Add getWorkRequestsData to Apps Script, "
                "deploy a New version, then ↻ Refresh.")
        return
    df = df.copy()
    df["week"] = pd.to_numeric(df["week"], errors="coerce")
    df["month"] = pd.to_numeric(df["month"], errors="coerce")
    df["monthName"] = df["month"].map(WR_MONTHS).fillna(df["month"].astype("string"))

    fc = st.columns(3)
    with fc[0]:
        qsel = st.selectbox("Raised by", ["All"] + sorted(df["raisedBy"].dropna().unique()), key="wr_qa")
    with fc[1]:
        ssel = st.selectbox("Status", ["All"] + WR_STATUS, key="wr_status")
    with fc[2]:
        mopts = [WR_MONTHS[m] for m in sorted(df["month"].dropna().unique()) if m in WR_MONTHS]
        msel = st.selectbox("Month", ["All"] + mopts, key="wr_month")

    d = df.copy()
    if qsel != "All":
        d = d[d["raisedBy"] == qsel]
    if ssel != "All":
        d = d[d["status"] == ssel]
    if msel != "All":
        d = d[d["monthName"] == msel]
    if d.empty:
        st.info("No ideas for this selection.")
        return

    total = len(d)
    closed = int((d["status"] == "Closed").sum())
    kpi_row([
        {"label": "Total Ideas", "value": str(total), "hint": f"{d['raisedBy'].nunique()} QAs", "color": "blue"},
        {"label": "Open", "value": str(int((d["status"] == "Open").sum())), "hint": "awaiting action", "color": "blue"},
        {"label": "In Progress", "value": str(int((d["status"] == "WIP").sum())), "hint": "WIP", "color": "orange"},
        {"label": "Closed", "value": str(closed),
         "hint": f"{(closed / total * 100 if total else 0):.0f}% done", "color": "green"},
    ])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Ideas by QA**")
        by = d.groupby("raisedBy").size().sort_values(ascending=False)
        st.plotly_chart(hbar(list(by.index), list(by.values), "#1a73e8"), width="stretch")
    with c2:
        st.markdown("**Status**")
        counts = [int((d["status"] == s).sum()) for s in WR_STATUS]
        st.plotly_chart(donut(WR_STATUS, counts, [WR_STATUS_COL[s] for s in WR_STATUS]), width="stretch")
    with c3:
        st.markdown("**Ideas by month**")
        months = [WR_MONTHS[m] for m in sorted(df["month"].dropna().unique()) if m in WR_MONTHS]
        st.plotly_chart(vbar(months, [int((d["monthName"] == m).sum()) for m in months]), width="stretch")

    st.markdown("### Ideas per QA per month  ·  target 4/month")
    pv = d.pivot_table(index="raisedBy", columns="monthName", values="suggestion",
                       aggfunc="count", fill_value=0)
    ordered = [WR_MONTHS[m] for m in sorted(df["month"].dropna().unique())
               if WR_MONTHS.get(m) in pv.columns]
    if ordered:
        pv = pv[ordered]
    pv["Total"] = pv.sum(axis=1)
    st.dataframe(pv.reset_index().rename(columns={"raisedBy": "QA"}), width="stretch", hide_index=True)

    st.markdown("### Ideation log")
    log = d[["date", "week", "monthName", "raisedBy", "suggestion", "status"]].rename(
        columns={"date": "Date", "week": "Week", "monthName": "Month",
                 "raisedBy": "Raised by", "suggestion": "Suggestion", "status": "Status"})
    st.dataframe(log, width="stretch", hide_index=True)
    st.download_button("⬇ Download work requests (CSV)", log.to_csv(index=False).encode(),
                       file_name="work_requests.csv", mime="text/csv", key="wr_dl")


# ───────────────────── navigation / main ─────────────────────
TABS = [
    ("QA Scorecard",    "scorecard",   render_scorecard),
    ("Work Requests",   "workRequests", render_workrequests),
    ("WoW Calibration", "calibration", render_calibration),
    ("Disputes",        "disputes",    render_disputes),
    ("FL Audit",        "flAudit",     render_flaudit),
    ("Audit Tracker",   "superAudit",  render_sa),
    ("CR Audit",        "cr",          render_cr),
    ("Esc Rejected",    "esc",         render_esc),
    ("Cost to Serve",   "cts",         render_cts),
    ("Agent Audits",    "cara",        render_cara),
    ("GO Recovery",     "gor",         render_gor),
    ("Res. Form",       "rfa",         render_rfa),
    ("Sys. Gamers",     "psg",         render_psg),
    ("MO Audits",       "moa",         None),
    ("CO Audits",       "coa",         render_coa),
]


# ───────────────────── global Month/Week filter (#1) ─────────────────────
_PERIOD_DATE = {
    "calibration": "date", "disputes": "disputeDate", "flAudit": "assignedDate",
    "superAudit": "assignedDate", "cr": "date", "esc": "createdDate", "cts": "date",
    "cara": "date", "gor": "dateOfCreation", "rfa": "transactionDate", "psg": "date",
    "moReg": "assignedDate", "moDeal": "dateOpened", "coa": "date",
}
_PERIOD_WEEK = {"calibration": "week", "flAudit": "week", "moReg": "week",
                "scorecard": "week", "disputes": "weekNumber", "workRequests": "week"}
_PERIOD_MONTH = {"disputes": "month", "scorecard": "month", "coa": "month",
                 "workRequests": "month"}
_FULL_MONTH = {"january": "Jan", "february": "Feb", "march": "Mar", "april": "Apr",
               "may": "May", "june": "Jun", "july": "Jul", "august": "Aug",
               "september": "Sep", "october": "Oct", "november": "Nov", "december": "Dec"}


def _to_month3(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() in ("nan", "none", "nat"):
        return None
    low = s.lower()
    if low in _FULL_MONTH:
        return _FULL_MONTH[low]
    if low[:3].capitalize() in MONTH_ORDER:
        return low[:3].capitalize()
    try:
        n = int(float(s))
        if 1 <= n <= 12:
            return MONTH_ORDER[n - 1]
    except (ValueError, TypeError):
        pass
    return None


def enrich_periods(key, df):
    """Add normalized _month (3-letter) and _week (number) for the global filter."""
    if df is None or df.empty or "_month" in df.columns:
        return df
    df = df.copy()
    mcol = _PERIOD_MONTH.get(key)
    if mcol and mcol in df.columns:
        df["_month"] = df[mcol].map(_to_month3)
    elif _PERIOD_DATE.get(key) in df.columns:
        df["_month"] = pd.to_datetime(df[_PERIOD_DATE[key]], errors="coerce").dt.strftime("%b")
    else:
        df["_month"] = None
    wcol = _PERIOD_WEEK.get(key)
    if wcol and wcol in df.columns:
        df["_week"] = pd.to_numeric(df[wcol], errors="coerce")
    elif _PERIOD_DATE.get(key) in df.columns:
        df["_week"] = pd.to_datetime(df[_PERIOD_DATE[key]], errors="coerce").dt.isocalendar().week
    else:
        df["_week"] = pd.NA
    return df


def apply_global(df):
    """Filter by the sidebar global Month/Week, then drop the helper columns."""
    if df is None or df.empty:
        return df
    gm = st.session_state.get("g_month", [])
    gw = st.session_state.get("g_week", [])
    out = df
    if gm and "_month" in out.columns:
        out = out[out["_month"].isin(gm)]
    if gw and "_week" in out.columns:
        out = out[pd.to_numeric(out["_week"], errors="coerce").isin(gw)]
    return out.drop(columns=[c for c in out.columns if c.startswith("_")], errors="ignore")


def _clean(df):
    if df is None:
        return pd.DataFrame()
    return df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")


@st.cache_data(ttl=900, show_spinner="Loading…")
def load_source(key):
    """Fetch + enrich ONE source (cached 15 min). Lazy: only the active tab loads."""
    if APPS_SCRIPT_URL:
        df, err = fetch_source(key)
    else:
        data, errs = load_all()
        df, err = data.get(key, pd.DataFrame()), errs.get(key)
    return enrich_periods(key, df), err


def main():
    st.sidebar.markdown("## 📊 QA Dashboard")
    choice = st.sidebar.radio("Section", [t[0] for t in TABS], key="__nav")
    cur_key = next((k for (lbl, k, _) in TABS if lbl == choice), None)
    errors = {}

    def get(k):
        df, err = load_source(k)
        if err:
            errors[k] = err
        return df

    # Global filter options come from the (fast) Scorecard, which spans the whole timeline
    sc, _ = load_source("scorecard")
    months = [m for m in MONTH_ORDER if "_month" in sc.columns and m in set(sc["_month"].dropna())]
    weeks = (sorted({int(w) for w in pd.to_numeric(sc["_week"], errors="coerce").dropna()})
             if "_week" in sc.columns and not sc.empty else [])
    st.sidebar.markdown("### Filters")
    st.sidebar.multiselect("Month", months, key="g_month")
    st.sidebar.multiselect("Week", weeks, key="g_week")

    if st.sidebar.button("↻ Refresh data", key="__refresh"):
        load_source.clear()
        st.rerun()

    # Load only the active tab's source(s)
    if cur_key == "moa":
        d_reg, d_deal = get("moReg"), get("moDeal")
        cur_raw = apply_global(d_reg)
    else:
        d_cur = get(cur_key)
        cur_raw = apply_global(d_cur)

    # ── exports (#4) ──
    st.sidebar.markdown("### Export")
    if cur_raw is not None and not cur_raw.empty:
        st.sidebar.download_button("⬇ This tab (CSV)", _clean(cur_raw).to_csv(index=False).encode(),
                                   file_name=f"{cur_key}.csv", mime="text/csv", key="__dl_cur")
    with st.sidebar.expander("⬇ Export ALL (Excel)"):
        st.caption("Pulls every source — first time can take ~1–2 min.")
        if st.button("Build full export", key="__dl_all_btn"):
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as xl:
                wrote = False
                for _lbl, k, _fn in TABS:
                    for kk in (("moReg", "moDeal") if k == "moa" else (k,)):
                        cd = _clean(apply_global(get(kk)))
                        if cd is not None and not cd.empty:
                            cd.to_excel(xl, sheet_name=str(kk)[:31], index=False)
                            wrote = True
                if not wrote:
                    pd.DataFrame({"info": ["no data"]}).to_excel(xl, sheet_name="info", index=False)
            st.download_button("Download Excel", buf.getvalue(),
                               file_name="qa_dashboard_export.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="__dl_all")

    if errors:
        with st.sidebar.expander("⚠ %d source(s) unavailable" % len(errors)):
            for k, v in errors.items():
                st.caption("**%s** — %s" % (k, v))

    # Render the active tab
    st.markdown("## " + choice)
    if cur_key == "moa":
        render_moa(apply_global(d_reg), apply_global(d_deal))
    else:
        fn = next(f for (lbl, k, f) in TABS if k == cur_key)
        fn(apply_global(d_cur))


if os.environ.get("QA_NO_MAIN") != "1":
    main()
