"""
QA Dashboard — shared helpers, config, and Google-Sheets reader.
Imported by app.py via `from qa_helpers import *`.

No Google credentials are required. Each spreadsheet is read either:
  • LOCAL  — from a downloaded .xlsx file in ./data/  (File > Download > Microsoft Excel)
  • LIVE   — from the public xlsx-export URL (only works if the sheet is link-shared)

read_workbook() prefers the local file when present, else falls back to the live URL.
"""
import io
import os
import json as _json
import math
import pathlib
import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ──────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────
DATA_DIR = pathlib.Path(__file__).parent / "data"

# ── LIVE MODE ──────────────────────────────────────────────────────────
# The dashboard pulls all data live from the sheets via the Apps Script
# web app — no downloads, no Google credentials. The URL is resolved from
# (1) Streamlit secrets (for cloud hosting), (2) the QA_APPS_SCRIPT_URL env
# var, then (3) the hardcoded fallback below — so it "just works" anywhere.
_FALLBACK_URL = "https://script.google.com/macros/s/AKfycbw-ix6BN0KctO8e-BvOBRAaRbEl7LeCL5ogZXggl1REErs6qgogsqjtkEZESOYsVdcg/exec"


def _resolve_apps_script_url():
    try:  # Streamlit Community Cloud / local secrets.toml
        if "QA_APPS_SCRIPT_URL" in st.secrets:
            return st.secrets["QA_APPS_SCRIPT_URL"]
    except Exception:
        pass
    return os.environ.get("QA_APPS_SCRIPT_URL", _FALLBACK_URL)


APPS_SCRIPT_URL = _resolve_apps_script_url()

# Apps Script getAllData() key  ->  dashboard data key
LIVE_KEY_MAP = {
    "calibration": "calibration",
    "disputes":    "disputes",
    "flAudit":     "flAudit",
    "superAudit":  "superAudit",
    "cr":          "contactResolution",
    "esc":         "escalations",
    "cts":         "costToServe",
    "cara":        "agentAudits",
    "gor":         "goRecovery",
    "rfa":         "resFormAudit",
    "psg":         "sysGamers",
    "moReg":       "moRegular",
    "moDeal":      "moDealAlert",
    "coa":         "coAudits",
    "scorecard":   "scorecard",
    "workRequests": "workRequests",
    "qaMetrics":   "qaMetrics",
    "docErrors":   "docErrors",
}


# Heavy server-side aggregations need a longer read timeout than the default.
_SLOW_SRC = {"qaMetrics": 340, "superAudit": 200}


def _fetch_one(url, js_key):
    sep = "&" if "?" in url else "?"
    resp = requests.get(url + sep + "api=1&src=" + js_key, timeout=_SLOW_SRC.get(js_key, 150))
    resp.raise_for_status()
    text = resp.text
    if text.lstrip()[:1] == "<":
        raise RuntimeError(
            "login page, not JSON — set 'Who has access = Anyone' and deploy a New version"
        )
    return _json.loads(text)


def fetch_source(key, url=None):
    """Fetch ONE source live from the Apps Script endpoint → (DataFrame, error)."""
    url = (url or APPS_SCRIPT_URL).strip()
    if not url:
        return pd.DataFrame(), "APPS_SCRIPT_URL is not set."
    if key not in LIVE_KEY_MAP:
        return pd.DataFrame(), f"unknown source '{key}'"
    try:
        recs = _fetch_one(url, LIVE_KEY_MAP[key])
        return pd.DataFrame(recs or []), None
    except Exception as e:
        return pd.DataFrame(), str(e)


def fetch_live(url=None):
    """Pull every source live from the Apps Script endpoint, one request per
    spreadsheet, all in parallel. Returns (data_dict, errors_dict)."""
    from concurrent.futures import ThreadPoolExecutor

    url = (url or APPS_SCRIPT_URL).strip()
    if not url:
        raise RuntimeError("APPS_SCRIPT_URL is not set.")

    data, errors = {}, {}
    with ThreadPoolExecutor(max_workers=len(LIVE_KEY_MAP)) as ex:
        futs = {ex.submit(_fetch_one, url, js): app
                for app, js in LIVE_KEY_MAP.items()}
        for fut, app_key in futs.items():
            try:
                records = fut.result()
                data[app_key] = pd.DataFrame(records or [])
            except Exception as e:
                data[app_key] = pd.DataFrame()
                errors[app_key] = str(e)
    return data, errors

SHEET_IDS = {
    "calibration": "1pokBJxLU4YNwOBE9GZf27B0tPLWFWKvIjPelE5zAzVQ",
    "disputes":    "1mAxkGh8jRb7U9YFF7TxFocJCIp5Nxxm-io9xp9lfjRE",
    "flAudit":     "1euPoVW8yvxw0rfTP4rAyNxDFsSLCsrR69M9xfiEmGEg",
    "superAudit":  "1KDDnuKZiDpGrXhLT9nKfW8___Ls3Kyl_LULfLFKiI_Q",
    "cr":          "12g8_DcjqZPriOaWFyDvbNIrH7BE7WdYZBK_PHedw-DY",
    "esc":         "1YKt08Rg9OQAE7wNqzgqSXMTaB2xrrYsM8d5u1v2Fm9w",
    "cts":         "1SWOBVEsg1F_D1zaC5W77rvA_PTZxLin1pFlyszKbCks",
    "cara":        "15pKXj_8VMdgzpzUVhMgeyYeITmf6pYWX1ixMEjXOjz4",
    "gor":         "1XfHuL2aIwP2dmNT8u_H2WkxCavhU9kIB3GNg_gnxrjE",
    "rfa":         "1wnoMjfKGDdZmuDdtFAI5ASX1IYfhDDFy7YCmXEKG7cQ",
    "psg":         "1UMXPO3uGoPv9OyF6o_pXeDAJp3TAJVbzTKvqWunyDKA",
    "moReg":       "1wibfqvrArR8y2DXgwFQX6zfgC3DuYHPT7VcOFmhnfEw",
    "moDeal":      "1dwomBe5-nkcrCOnAXOW5t53TdaVuFG9i3MgVnHA7aQ8",
    "coApr":       "1UBm-VNFCucIrv5sJ0sIWgnabKjDSGF-0DKCY_jxA388",
    "coMay":       "1qm1nQ5c5vQl9zqVTel4m8RCoMDKHJ31GX2DDsAw3j3Q",
}

# Filename used for the LOCAL fallback in ./data/
FILES = {
    "calibration": "calibration.xlsx",
    "disputes":    "disputes.xlsx",
    "flAudit":     "fl_audit.xlsx",
    "superAudit":  "super_audit.xlsx",
    "cr":          "cr_audit.xlsx",
    "esc":         "esc_rejected.xlsx",
    "cts":         "cost_to_serve.xlsx",
    "cara":        "agent_audits.xlsx",
    "gor":         "go_recovery.xlsx",
    "rfa":         "res_form.xlsx",
    "psg":         "sys_gamers.xlsx",
    "moReg":       "mo_regular.xlsx",
    "moDeal":      "mo_deal.xlsx",
    "coApr":       "co_april.xlsx",
    "coMay":       "co_may.xlsx",
}

PCOL = {"CS": "#4285F4", "MO": "#34A853", "CO": "#FBBC04"}
_KPI_COLORS = {"blue": "#1a73e8", "green": "#2e9e2e", "orange": "#e37400",
               "red": "#e0483b", "purple": "#7b1fa2"}

# Chart theme — mutated by set_chart_theme() each run so Plotly figures match
# the active light / dark mode (canvas can't read CSS variables).
CHART_THEME = {"font": "#3c4043", "grid": "#e8eaed", "line": "#ffffff"}


def set_chart_theme(dark: bool):
    if dark:
        CHART_THEME.update(font="#c7d0e0", grid="rgba(255,255,255,0.10)", line="#0f1729")
    else:
        CHART_THEME.update(font="#3c4043", grid="#e8eaed", line="#ffffff")

# ──────────────────────────────────────────────────────────────────────
# WORKBOOK READER  (no credentials)
# ──────────────────────────────────────────────────────────────────────
def read_workbook(key):
    """Return {worksheet_name: rows(list[list])} for one spreadsheet.
    Cells are raw values (str/number/None). Loaders apply S()/dstr()/to_pct()."""
    local = DATA_DIR / FILES[key]
    if local.exists():
        xls = pd.read_excel(local, sheet_name=None, header=None, dtype=object)
    else:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_IDS[key]}/export?format=xlsx"
        resp = requests.get(url, timeout=90)
        resp.raise_for_status()
        if b"<html" in resp.content[:512].lower():
            raise RuntimeError(
                f"'{key}' is not publicly readable. Either share it as "
                f"'Anyone with the link can view', or download it to data/{FILES[key]}."
            )
        xls = pd.read_excel(io.BytesIO(resp.content), sheet_name=None, header=None, dtype=object)
    out = {}
    for name, df in xls.items():
        df = df.where(pd.notna(df), None)
        out[name] = df.values.tolist()
    return out

# ──────────────────────────────────────────────────────────────────────
# PARSING HELPERS  (used by loaders — mirror Code.gs / dashboard.html)
# ──────────────────────────────────────────────────────────────────────
def S(x):
    """Clean string. NaN/None -> ''. Integer-valued floats -> '123' not '123.0'."""
    if x is None:
        return ""
    if isinstance(x, float):
        if math.isnan(x):
            return ""
        if x.is_integer():
            return str(int(x))
        return str(x)
    return str(x).strip()


def dstr(x):
    """Normalise a date cell to its date part (drops time / 'T' suffix)."""
    s = S(x)
    if not s:
        return ""
    return s.split("T")[0].split(" ")[0]


def to_pct(x):
    """0.20 -> 20.0 ; '85%' -> 85.0 ; 85 -> 85.0 ; '' -> 0."""
    if x is None or x == "":
        return 0.0
    if isinstance(x, (int, float)):
        if isinstance(x, float) and math.isnan(x):
            return 0.0
        if 0 <= x <= 1:
            return round(x * 10000) / 100
        return round(x * 100) / 100
    try:
        n = float(str(x).replace("%", "").strip())
    except ValueError:
        return 0.0
    return round(n * 100) / 100


def yna(x):
    s = S(x).lower()
    if s == "yes":
        return "Yes"
    if s == "no":
        return "No"
    return "N/A"


def norm_dispute(x):
    l = S(x).lower()
    if not l:
        return None
    if "outside" in l:
        return "Outside Window"
    if "non qa" in l:
        return "Non QA Error"
    if "accepted" in l:
        return "Accepted"
    if "rejected" in l:
        return "Rejected"
    return None


def norm_cr_dispute(x):
    l = S(x).lower()
    if not l:
        return ""
    if "accepted" in l:
        return "Accepted"
    if "rejected" in l:
        return "Rejected"
    if "outside" in l:
        return "Outside Window"
    return S(x)


def is_uuid(s):
    return len(s) == 36 and s.count("-") == 4

# ──────────────────────────────────────────────────────────────────────
# STAT HELPERS  (used by render_ functions)
# ──────────────────────────────────────────────────────────────────────
def pct_yes(df, col):
    sub = df[df[col].isin(["Yes", "No"])]
    if len(sub) == 0:
        return 0.0
    return (sub[col] == "Yes").sum() / len(sub) * 100


def top_val(values):
    vc = pd.Series(list(values)).value_counts()
    return vc.index[0] if len(vc) else ""

# ──────────────────────────────────────────────────────────────────────
# UI HELPERS
# ──────────────────────────────────────────────────────────────────────
def kpi_row(items):
    """items: list of dict(label, value, hint='', color='blue'). Card styling
    comes from the .qa-kpi CSS injected per-theme in app.py."""
    cols = st.columns(len(items))
    for c, it in zip(cols, items):
        color = _KPI_COLORS.get(it.get("color", "blue"), "#1a73e8")
        with c:
            st.markdown(
                f"""<div class="qa-kpi">
                  <div class="qa-kpi-label">{it['label']}</div>
                  <div class="qa-kpi-value" style="color:{color}">{it['value']}</div>
                  <div class="qa-kpi-hint">{it.get('hint','')}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def _style(fig, height=250, legend=True):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        font=dict(size=11, color=CHART_THEME["font"]),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=legend,
        legend=dict(font=dict(size=10)),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=CHART_THEME["grid"])
    return fig


def donut(labels, values, colors=None):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors, line=dict(color=CHART_THEME["line"], width=2)),
        textinfo="value",
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    return _style(fig, 250)


def vbar(labels, values, colors=None, yfmt=None):
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors or "#1a73e8"))
    fig = _style(fig, 250, legend=False)
    if yfmt == "%":
        fig.update_yaxes(ticksuffix="%")
    return fig


def hbar(labels, values, color="#1a73e8"):
    # plotly draws bottom-to-top; reverse so the largest sits on top
    fig = go.Figure(go.Bar(x=list(values)[::-1], y=list(labels)[::-1],
                           orientation="h", marker_color=color))
    return _style(fig, max(260, 22 * len(labels)), legend=False)


def stacked_bar(categories, series, colors=None, horizontal=False):
    fig = go.Figure()
    for name, vals in series.items():
        col = (colors or {}).get(name)
        if horizontal:
            fig.add_bar(y=categories, x=vals, name=name, orientation="h", marker_color=col)
        else:
            fig.add_bar(x=categories, y=vals, name=name, marker_color=col)
    fig.update_layout(barmode="stack")
    return _style(fig, 260)


def line_chart(x, series, colors=None, ymax=None, yfmt="%"):
    fig = go.Figure()
    for name, vals in series.items():
        col = (colors or {}).get(name)
        fig.add_scatter(x=x, y=vals, mode="lines+markers", name=name,
                        line=dict(color=col, width=2), connectgaps=True)
    fig = _style(fig, 250)
    if ymax is not None:
        fig.update_yaxes(range=[0, ymax])
    if yfmt == "%":
        fig.update_yaxes(ticksuffix="%")
    return fig


def show_table(df, pct_cols=(), bar_cols=(), int_cols=()):
    cfg = {}
    for c in bar_cols:
        if c in df.columns:
            cfg[c] = st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%.1f%%")
    for c in pct_cols:
        if c in df.columns:
            cfg[c] = st.column_config.NumberColumn(c, format="%.1f%%")
    for c in int_cols:
        if c in df.columns:
            cfg[c] = st.column_config.NumberColumn(c, format="%d")
    st.dataframe(df, column_config=cfg, width="stretch", hide_index=True)
