# QA Dashboard — Python / Streamlit

A Python port of the QA Dashboard. Reads all 15 Google Sheets, no Google credentials required.

## Why this version

- **No API key, no Cloud project, no service account** — sidesteps the permission walls in Google Cloud Console.
- Reads each spreadsheet as a downloaded `.xlsx` (local mode) **or** via its public export URL (live mode).
- Loads all sources in parallel, caches for 15 min, renders 13 interactive tabs.

## 1. Install (one time)

```powershell
py -3 -m pip install -r requirements.txt
```

## 2. Get the data — pick ONE mode

### ⭐ Mode LIVE — via Apps Script (recommended: no downloads, no credentials, always current)

Your sheets are **private**, so Python can't read them directly. Instead, your Apps Script reads them (it runs as *you*) and publishes the data as JSON; the dashboard fetches that one URL.

1. Open your Apps Script project (the one with `Code.gs` + `index`).
2. Make sure `Code.gs` is the **latest** version from this folder (it now has the `?api=1` JSON endpoint and all 14 data sources). Paste it in if needed.
3. **Deploy ▸ Manage deployments ▸ Edit (✎) ▸ New version**. Set:
   - **Execute as:** Me
   - **Who has access:** **Anyone**  ← important; "Anyone within Groupon" will *not* work
   - **Deploy** → copy the **Web app URL** (ends in `/exec`).
4. Test it: open `<that-url>?api=1` in your browser — you should see raw JSON. If you see a Google login page, the access isn't set to **Anyone** (redo step 3).
5. Tell the dashboard the URL — either:
   - Open `qa_helpers.py`, find `APPS_SCRIPT_URL = os.environ.get("QA_APPS_SCRIPT_URL", "")`, and put your URL inside the quotes: `"...", "https://script.google.com/.../exec"`, **or**
   - Set an env var before running: `setx QA_APPS_SCRIPT_URL "https://script.google.com/.../exec"` (then open a new terminal).

That's it — the dashboard now loads live from the sheets. **↻ Refresh** re-pulls.

> If your org blocks **Anyone** access for web apps, use Mode A below, or just use the Apps Script HTML dashboard directly (open the `/exec` URL in your browser — it's already a live dashboard).

### Mode A — Local files (offline fallback, no Apps Script)

For each sheet, open it in Google Sheets → **File → Download → Microsoft Excel (.xlsx)** → save into a `data\` folder next to `app.py` with these exact names:

| Sheet | Save as |
|---|---|
| WoW Calibration | `data\calibration.xlsx` |
| Disputes | `data\disputes.xlsx` |
| FL Audit | `data\fl_audit.xlsx` |
| Audit Tracker (Super Audit) | `data\super_audit.xlsx` |
| CR — Process Audits | `data\cr_audit.xlsx` |
| Escalation Rejected | `data\esc_rejected.xlsx` |
| Cost to Serve | `data\cost_to_serve.xlsx` |
| CR — Agent Audits | `data\agent_audits.xlsx` |
| GO Recovery | `data\go_recovery.xlsx` |
| Resolution Form Audits | `data\res_form.xlsx` |
| Potential System Gamers | `data\sys_gamers.xlsx` |
| MO Regular Audits | `data\mo_regular.xlsx` |
| MO Deal Alerts | `data\mo_deal.xlsx` |
| CO April | `data\co_april.xlsx` |
| CO May | `data\co_may.xlsx` |

To refresh later, just re-download the changed files and click **↻ Refresh** in the app. (Local mode is only used when `APPS_SCRIPT_URL` is blank.)

## 3. Run

```powershell
py -3 -m streamlit run app.py
```

It opens at `http://localhost:8501` in your browser. The first load fetches/reads all sheets (a few seconds); subsequent loads are instant from cache. **↻ Refresh** in the sidebar clears the cache and reloads.

## Files

| File | Purpose |
|---|---|
| `app.py` | Main app — data loaders, 13 tab renderers, navigation |
| `qa_helpers.py` | Config (sheet IDs), workbook reader, parsing + chart/KPI/table helpers |
| `requirements.txt` | Python dependencies |

## Sharing with the team

- **Easiest:** each person runs it locally (`streamlit run app.py`) with their own `data\` folder.
- **Hosted:** push to a private GitHub repo and deploy free on [Streamlit Community Cloud](https://streamlit.io/cloud) — only works in live mode, so all sheets must be link-shared.
