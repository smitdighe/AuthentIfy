<div align="center">
<pre>
 █████╗  ██╗   ██╗ ████████╗ ██╗  ██╗ ███████╗ ███╗   ██╗ ████████╗ ██╗ ███████╗ ██╗   ██╗
██╔══██╗ ██║   ██║ ╚══██╔══╝ ██║  ██║ ██╔════╝ ████╗  ██║ ╚══██╔══╝ ██║ ██╔════╝ ╚██╗ ██╔╝
███████║ ██║   ██║    ██║    ███████║ █████╗   ██╔██╗ ██║    ██║    ██║ █████╗    ╚████╔╝ 
██╔══██║ ██║   ██║    ██║    ██╔══██║ ██╔══╝   ██║╚██╗██║    ██║    ██║ ██╔══╝     ╚██╔╝  
██║  ██║ ╚██████╔╝    ██║    ██║  ██║ ███████╗ ██║ ╚████║    ██║    ██║ ██║         ██║   
╚═╝  ╚═╝  ╚═════╝     ╚═╝    ╚═╝  ╚═╝ ╚══════╝ ╚═╝  ╚═══╝    ╚═╝    ╚═╝ ╚═╝         ╚═╝   
</pre>

### Verify before you trust.

</div>

<div align="center">

**AuthentIfy** is an AI-assisted forensic pipeline for detecting tampered PDFs — the kind of document fraud that slips past a human eye: a swapped date, a spliced-in page, a re-exported "official" certificate. Upload a PDF and it runs six independent analysis phases — PDF metadata forensics, Error Level Analysis, noise/blur profiling, OCR text extraction, document-template matching, and an Isolation-Forest anomaly model — then folds every signal into a single **0–100 authenticity score** and a **Genuine / Suspicious / Tampered** verdict, with a plain-English reason for each deduction. A Flask REST API drives the pipeline; a React SPA handles upload, animated results, JWT auth, and a per-user analysis history. Every phase is failure-isolated — one analyzer crashing degrades the score, it never takes down the request.

</div>

---

## 🔍 How It Works

**Analysis pipeline (`POST /analyze`):**

```
PDF upload  →  save_upload()  →  uploads/<uuid>_<name>.pdf   (size + extension validated)
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                                                                 ▼
Phase 1  Metadata forensics        PyMuPDF metadata + font_inspector + digital_signature
         · missing author/date · mod-date < creation-date · stripped fields
         · suspicious producer/creator tools · non-embedded / novelty fonts · invalid sigs
        ▼
Phase 2  Vision (ELA + noise)      render pages @200dpi → processed/<uuid>/page_NNN.png
         · Error Level Analysis (re-save-JPEG diff, 8×8 block ratio)
         · Laplacian blur · regional noise variance · cross-page outlier detection
        ▼
Phase 3  OCR                       pytesseract per page → text + mean confidence
         · low OCR confidence · sparse text · garbled-character ratio
        ▼
Phase 4  Template match            OCR text vs templates/*.json (aadhaar · pan · marksheet)
         · detect doc_type by required-keyword ratio · flag missing required keywords
         · flag metadata fields a real document of that type should carry
        ▼
Phase 5  ML anomaly                8-feature vector → IsolationForest.predict()
         · issue counts · text length · page count · OCR confidence · avg ELA ratio
        ▼
Phase 6  Score aggregation         100 − Σ(deductions);  verdict by threshold
                                        │
                                        ▼
      full report → reports/<uuid>.json   (+ DB row if the caller is authenticated)
      uploads/<uuid>_<name>.pdf deleted in a finally block, regardless of outcome
```

**Scoring is transparent, not a black box:**

```
start 100
  − 25 per metadata issue      − 20 per OCR issue        − 15 if ML flags anomaly
  − 15 per vision issue        − 25 per template issue
score = max(0, 100 − Σ)

verdict:   score ≥ 80 → Genuine     score ≥ 50 → Suspicious     else → Tampered
confidence = round(score × 0.6 + ml_confidence × 0.4, 1)
```

**Auth + history layer:**

```
register/login  →  Flask-JWT access (1h) + refresh (30d) tokens  →  stored in localStorage
authenticated /analyze  →  Report row linked to user, user.total_reports++
/report/history · /report/stats  →  dashboard (paginated history + verdict counts)
axios 401 interceptor  →  one silent /auth/refresh retry, then clear + redirect to /login
```

`/analyze` uses **optional** auth — anonymous callers still get a full analysis and a shareable `reports/<uuid>.json`; only logged-in callers get it persisted to their history.

---

## ✨ Features

**Backend**

<table>
  <tr>
    <td align="center" width="220">
      <h3>🧬</h3>
      <b>Six-Phase Forensic Pipeline</b><br/>
      <sub>Metadata, ELA, noise, OCR, template, and ML analysis — each isolated in its own <code>try</code> so one failure degrades gracefully instead of 500-ing the request</sub><br/>
    </td>
    <td align="center" width="220">
      <h3>📊</h3>
      <b>Explainable Scoring</b><br/>
      <sub>Every point lost maps to a human-readable reason; the response carries the full <code>breakdown</code> of per-phase deductions, not just a number</sub><br/>
    </td>
    <td align="center" width="220">
      <h3>🔑</h3>
      <b>JWT Auth + Optional Uploads</b><br/>
      <sub>Bcrypt passwords, access/refresh tokens, per-user history — yet <code>/analyze</code> works anonymously and only persists when a token is present</sub><br/>
    </td>
  </tr>
</table>

**Frontend**

<table>
  <tr>
    <td align="center" width="220">
      <h3>📤</h3>
      <b>Drag-Drop Analyze Flow</b><br/>
      <sub>PDF drop zone with a staged upload strip and an animated phase-by-phase "pipeline running" view via Framer Motion</sub><br/>
    </td>
    <td align="center" width="220">
      <h3>🗂️</h3>
      <b>Dashboard & History</b><br/>
      <sub>Paginated report history, verdict-count stat cards, per-report delete, and a shareable public report page addressed by UUID</sub><br/>
    </td>
    <td align="center" width="220">
      <h3>🛡️</h3>
      <b>Resilient API Layer</b><br/>
      <sub>Axios instance with token injection, a single-shot refresh-on-401 interceptor, and protected routes gated on auth state</sub><br/>
    </td>
  </tr>
</table>

---

## 🛠️ Tech Stack

**Backend**

| Layer | Technology | Purpose |
|:------|:-----------|:--------|
| 🌐 API | Flask 3 (app factory + blueprints) | `auth` · `analyze` · `report` · `health` routes |
| 📄 PDF | PyMuPDF (`fitz`) | Metadata, page rendering @200dpi, font/signature inspection |
| 👁️ Vision | OpenCV + Pillow + NumPy | Error Level Analysis, Laplacian blur, regional noise variance |
| 🔤 OCR | pytesseract (Tesseract) | Per-page text + confidence extraction |
| 🤖 ML | scikit-learn `IsolationForest` + joblib | 8-feature anomaly detection, model persisted to `.pkl` |
| 🗄️ Data | Flask-SQLAlchemy + SQLite | `users` and `reports` tables |
| 🔐 Auth | Flask-JWT-Extended + Flask-Bcrypt | Access/refresh tokens, password hashing |
| ⚙️ Config | python-dotenv | `.env` loading + fail-fast on missing secrets |
| 🚀 Serving | Gunicorn (`wsgi:app`) | Production WSGI server (Render) |

**Frontend**

| Layer | Technology | Purpose |
|:------|:-----------|:--------|
| ⚛️ Framework | React 19 + Vite | SPA and dev server / bundler |
| 🧭 Routing | React Router 7 | Landing · Analyze · Report · Login · Register · Dashboard |
| 🎬 Animation | Framer Motion | Upload flow, pipeline steps, score/verdict reveals |
| 🎨 Styling | Tailwind CSS (+ heavy inline styles) | Dark theme, `verdict` color tokens |
| 🌐 HTTP | Axios | Interceptor-based token handling + refresh |
| 🎯 Icons | lucide-react | UI iconography |

---

## 📁 Project Structure

```bash
AuthentIfy/
├── backend/
│   ├── app.py                    # Flask factory · numpy-aware JSON provider · blueprint wiring
│   ├── config.py                 # env-driven config + fail-fast on missing SECRET_KEY / JWT_SECRET_KEY
│   ├── database.py               # SQLAlchemy + Bcrypt init, create_all()
│   ├── wsgi.py                   # Gunicorn entry (create_app())
│   ├── Procfile                  # web: gunicorn ... wsgi:app
│   ├── requirements.txt
│   ├── routes/
│   │   ├── auth.py               # register · login · refresh · logout · me
│   │   ├── analyze.py            # /analyze — orchestrates the 6-phase pipeline
│   │   ├── report.py             # public report · history · stats · delete
│   │   └── health.py
│   ├── services/                 # pipeline orchestrators (one per phase)
│   │   ├── metadata_analyzer.py  # · ela_analyzer.py · ocr_extractor.py
│   │   ├── template_matcher.py   # · anomaly_detector.py · score_aggregator.py
│   ├── forensics/                # low-level primitives
│   │   ├── ela.py · noise_analysis.py · font_inspector.py · digital_signature.py
│   ├── utils/                    # file_handler · pdf_utils · image_utils
│   ├── db_models/                # user.py · report.py
│   ├── middleware/               # auth_middleware.py (jwt_required_with_user, optional_jwt_user)
│   ├── models/                   # isolation_forest.pkl + training/train_model.py
│   ├── templates/                # aadhaar · pan · marksheet template JSON
│   ├── uploads/ processed/ reports/ database/   # runtime artifacts (gitignored)
│   ├── .env.example
│   └── .venv/
├── frontend/
│   ├── src/
│   │   ├── main.jsx · App.jsx                    # router + AuthProvider shell
│   │   ├── pages/                # Landing · Login · Register · Analyze · Report · Dashboard
│   │   ├── context/AuthContext.jsx · hooks/useAuth.js
│   │   ├── services/api.js       # axios instance · token helpers · refresh interceptor · endpoints
│   │   ├── components/
│   │   │   ├── Navbar · Footer · ProtectedRoute
│   │   │   ├── upload/           # UploadZone · FilePreview
│   │   │   ├── results/          # VerdictCard · ScoreGauge · ScoreRing · ConfidenceBadge · ReasonsList
│   │   │   └── dashboard/        # HistoryTable · ReportRow · StatsCard
│   │   └── utils/helpers.js
│   ├── vite.config.js            # dev server :3000, proxy /api → :5000
│   ├── tailwind.config.js
│   └── .env.example
├── render.yaml                   # Render web service + 1GB disk
└── .env.production.example
```

Backend dependency direction: **`forensics / utils → services → routes`**. `routes/analyze.py` calls each service, catches per-phase, and hands the merged results to `score_aggregator`.

---

## 🧠 The Analysis Rules That Matter

Where a naive "is this PDF fake?" check goes shallow, AuthentIfy layers independent signals — no single one is trusted alone:

1. **Metadata logic, not just presence.** A modification date *earlier* than the creation date is a logical impossibility → tamper flag. Fully stripped metadata (no author/producer/creator/date) is itself the signal.
2. **ELA on re-compressed pages.** Each page is re-saved as JPEG-90 and diffed against itself; regions edited at a different compression level light up. Scored per 8×8 block, flagged above a 15% suspicious-block ratio or an extreme max-error spike.
3. **Noise consistency across the page and across pages.** Regional Laplacian/noise variance catches spliced composites; a page whose noise profile is a statistical outlier (z > 2) among its siblings suggests it came from a different source document.
4. **Fonts betray edits.** Novelty fonts (Comic Sans, Impact, Wingdings…), non-embedded fonts, or a sudden jump in distinct fonts between pages all flag.
5. **Template expectations.** Detected document type (Aadhaar/PAN/marksheet) pulls a JSON spec of required keywords and expected metadata fields; anything an authentic document of that type should contain but doesn't becomes a reason.
6. **ML as a tiebreaker, weighted 40%.** The Isolation Forest sees the *shape* of all the above (issue counts, text length, OCR confidence, average ELA ratio) and contributes to the blended confidence — but the deterministic score leads.

Every analyzer returns a neutral, non-crashing default on failure, so a corrupt or encrypted PDF yields a low-confidence verdict rather than an exception.

---

## ⚙️ Getting Started

### Prerequisites

- **Python 3.11** (Render pins 3.11.7)
- **Node.js 18+**
- **Tesseract OCR** — required for Phases 3 & 4; without it, OCR silently returns empty text and template matching no-ops (the rest of the pipeline still runs)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Windows (Git Bash);  use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

cp .env.example .env                 # then edit — SECRET_KEY and JWT_SECRET_KEY are REQUIRED (app refuses to boot without them)
python app.py                        # dev server → http://localhost:5000
```

The Isolation Forest is loaded from `models/isolation_forest.pkl`, or auto-trained on synthetic data on first run. To regenerate it explicitly:

```bash
python models/training/train_model.py
```

Sanity-check the API:

```bash
curl http://localhost:5000/health/          # → {"status":"ok","service":"AuthentIfy",...}
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env                 # VITE_API_URL=http://localhost:5000
npm run dev                          # → http://localhost:3000
```

> Both servers must run together. The Vite dev server proxies `/api/*` to `:5000`, but the app's axios client talks to `VITE_API_URL` directly — point it at the backend origin.

### 3. Production (Render)

`render.yaml` provisions a Python web service running `gunicorn ... backend.wsgi:app` with a 1 GB disk. Set the required env vars in the dashboard (see **Known Limitations** — `JWT_SECRET_KEY` is *not* auto-generated by the blueprint).

---

## 🌐 HTTP API Reference

Errors return `{ "error": "<message>" }` with the appropriate status. `/analyze` accepts an optional `Authorization: Bearer <token>`; everything under `/report` except the public GET requires one.

| Method & Route | Auth | Description |
|---|:---:|---|
| `GET /health/` | — | Liveness + version |
| `POST /auth/register` | — | Create account `{ email, password, full_name? }` → user + tokens |
| `POST /auth/login` | — | `{ email, password }` → user + access/refresh tokens |
| `POST /auth/refresh` | refresh | New access token from a refresh token |
| `POST /auth/logout` | ✓ | Stateless logout (client discards tokens) |
| `GET /auth/me` | ✓ | Current user profile |
| `POST /analyze` | optional | `multipart/form-data` PDF → full report; persisted to history if authenticated |
| `GET /report/<uuid>` | — | Public report JSON by ID (validated UUID format) |
| `GET /report/history?page=&limit=` | ✓ | Paginated history for the current user (limit clamped 1–50) |
| `GET /report/stats` | ✓ | Verdict counts + average score |
| `DELETE /report/history/<uuid>` | ✓ | Delete one of your own reports |

The frontend calls these through `frontend/src/services/api.js`, a thin axios wrapper with token injection and refresh handling.

---

## ⚠️ Known Limitations

- **SQLite + artifacts live on the local filesystem.** `config.py` writes the DB, uploads, page images, and JSON reports under `backend/`. Render's `render.yaml` mounts a persistent disk at `/var/data`, but the code doesn't point there — so **on a hosted redeploy/restart, users and history are lost**. Uploads are deleted post-analysis, but `processed/*.png` and `reports/*.json` accumulate unbounded on disk.
- **`JWT_SECRET_KEY` must be set by hand in production.** The fail-fast guard raises `RuntimeError` if `SECRET_KEY` or `JWT_SECRET_KEY` is unset — but `render.yaml` only `generateValue`s `SECRET_KEY`. Deploy will crash on boot until `JWT_SECRET_KEY` is added.
- **Single-origin CORS.** `CORS(app, origins=[Config.FRONTEND_URL])` treats the value as one origin. The comma-separated multi-origin example in `.env.production.example` will *not* parse as multiple origins.
- **The ML model is illustrative, not trained on real forgeries.** Training data is synthetic and entirely "genuine" (all issue counts zero), with a fixed `contamination=0.1`. The anomaly signal is a plausibility check layered on the deterministic score, not a learned forgery classifier.
- **Analysis is synchronous.** All six phases — multi-page rendering, ELA, and OCR — run inline within the request. A large PDF ties up a Gunicorn worker for the duration; there's no job queue or async processing.
- **`.env.production.example` over-promises.** It lists `DATABASE_URL` (Postgres) and second-based JWT expiry vars that `config.py` does not currently read — the DB is SQLite and token lifetimes are hardcoded (`1h` / `30d`).
- **External font CDNs.** `index.html` pulls Inter and Helvetica Now Display from third-party CDNs, so first paint depends on network reachability.

---

## 🔮 Future Improvements

- **Persist to the mounted disk / Postgres** — point `DATABASE_DIR` (and artifacts) at `/var/data`, or wire the already-documented `DATABASE_URL` for a real database and move reports/images to object storage
- **Async analysis** — offload the pipeline to Celery/RQ so uploads return a job id and long PDFs don't block workers
- **Train on real tampered documents** — replace the synthetic Isolation Forest with a model fit on genuine-vs-forged corpora; broaden the template library beyond Aadhaar/PAN/marksheet
- **Multi-origin CORS parsing** and standard hardening — rate limiting, upload scanning, artifact retention limits
- **Token-expiry + refresh polish** — surface access-token expiry to the UI instead of relying solely on the 401-retry path
