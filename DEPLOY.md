# Deploy the QA Dashboard for free (shareable with your team)

The dashboard reads data live from your **public Apps Script endpoint**, so a
cloud host needs **no Google credentials** — it fetches data the same way your
laptop does. Recommended host: **Streamlit Community Cloud** (free, always-on,
gives a `https://<name>.streamlit.app` URL).

---

## Option 1 — Streamlit Community Cloud  ⭐ recommended

### A. Put the code on GitHub (one time)
1. Create a free account at **github.com** if you don't have one.
2. Create a **new repository** (Private is fine — Streamlit Cloud can read private repos).
3. Upload these 3 files (drag-and-drop in GitHub's web UI works):
   - `app.py`
   - `qa_helpers.py`
   - `requirements.txt`

   (You do **not** need `data/`, `Code.gs`, `index.html`, or the `test_*`/`_*` files.)

### B. Deploy
1. Go to **share.streamlit.io** → sign in with GitHub.
2. **Create app** → **Deploy a public app from GitHub**.
3. Pick your **repository**, **branch** (`main`), and **Main file path** = `app.py`.
4. (Optional) **Advanced settings** → Python version **3.12**.
5. Click **Deploy**. First build takes ~2 min; then it opens at your `.streamlit.app` URL.

### C. Share with your team
- Copy the app URL and send it. Done.
- To **restrict who can open it**: app menu (⋮) → **Settings** → **Sharing** →
  set it to **specific viewers** and add your teammates' Google emails. They'll
  sign in with Google to view.

### D. (Optional) Keep the endpoint URL out of the repo
Instead of the hardcoded URL in `qa_helpers.py`, use a secret:
- App **Settings** → **Secrets** → paste:
  ```toml
  QA_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw-…/exec"
  ```
- The app prefers this secret automatically.

---

## Option 2 — Hugging Face Spaces (also free)
1. Create account at **huggingface.co** → **New Space** → SDK: **Streamlit**.
2. Upload `app.py`, `qa_helpers.py`, `requirements.txt`.
3. It builds and serves at `https://huggingface.co/spaces/<you>/<space>`.
4. Space visibility can be Public or Private.

---

## Option 3 — Internal only (no hosting account)
Run on your machine and share on the office network:
```cmd
py -3 -m streamlit run app.py --server.address 0.0.0.0
```
Teammates on the same network open `http://<your-PC-IP>:8501`.
(Only works while your machine is on — fine for quick demos, not for 24/7.)

---

## 🔒 Recommended hardening (internal data on a public endpoint)

Your Apps Script endpoint is currently open to **Anyone** with the URL. To lock
it to just the dashboard, add a shared secret token:

**In `Code.gs` `doGet(e)`**, at the top of the `api === '1'` block:
```javascript
if (e.parameter.token !== 'PICK_A_LONG_RANDOM_STRING') {
  return ContentService.createTextOutput('forbidden').setMimeType(ContentService.MimeType.TEXT);
}
```
Redeploy a **New version**. Then in `qa_helpers.py` (or Streamlit Secrets) append
`?token=PICK_A_LONG_RANDOM_STRING` is handled by adding it to the URL — tell me
and I'll wire the token into `fetch_live()` so only your app can pull the data.
