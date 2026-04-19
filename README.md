---
title: Runner
emoji: 🏃
colorFrom: yellow
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Runner — Arko's Half Marathon Tracker

A private full-stack fitness tracking web app for the 32-week half marathon transformation plan.

## Features

- **Plan Viewer** — Complete 32-week training plan with all phases, nutrition, and milestones
- **Daily Check-In** — Upload Apple Health workout screenshots; splits are parsed automatically
- **Weekly Log** — Track weight, waist, body measurements with auto-computed BMI and deltas
- **Dashboard** — Progress charts (weight, waist, Z2 pace, HR, weekly volume)

## Stack

- **Frontend**: React + Vite (SPA, served as static files)
- **Backend**: FastAPI (Python 3.11)
- **Database**: SQLite via SQLAlchemy
- **Auth**: JWT tokens, single user (`arko`)
- **Image parsing**: pytesseract (OCR) → Gemini Flash fallback

## Local Development

### Prerequisites
- Node.js 20+
- Python 3.11+
- Tesseract OCR installed (`brew install tesseract` / `apt install tesseract-ocr`)

### Setup

```bash
# 1. Generate your password hash
python generate_password_hash.py

# 2. Create .env from example
cp .env.example .env
# Edit .env — fill in PASSWORD_HASH and JWT_SECRET

# 3. Install backend deps
pip install fastapi uvicorn sqlalchemy python-jose passlib python-multipart pytesseract Pillow google-generativeai

# 4. Build frontend
cd frontend && npm install && npm run build && cd ..

# 5. Run
uvicorn backend.main:app --host 0.0.0.0 --port 7860
```

Open `http://localhost:7860` — login as `arko` with your password.

### Frontend dev server (with hot reload)
```bash
cd frontend
npm run dev   # proxies /api/* to localhost:7860
```

## Docker

```bash
cp .env.example .env   # fill in values
docker-compose up --build
```

## Deploy — two options

### Option A: Monolithic (backend + frontend on HuggingFace Spaces)

1. Create a new Space: **Docker** type, port **7860**
2. Push this repo to the Space's git remote (uses the root-level `Dockerfile`)
3. In **Settings → Repository Secrets**, add:
   - `APP_PASSWORD` — your login password (or `PASSWORD_HASH` for a pre-hashed value)
   - `JWT_SECRET` — any 32+ character random string
   - `OPENAI_API_KEY` — for GPT-5 vision screenshot parsing
   - `OPENAI_MODEL` — (optional) overrides the default `gpt-5-mini`
4. The Space builds and deploys automatically. Open the Space URL to use the app.

### Option B: Decoupled (frontend on Railway, backend on HuggingFace Spaces)

Better mobile experience — the HF Spaces frame is removed, and you get Railway's custom domain.

**Backend (HuggingFace Spaces):**

Same as Option A steps 1-4, **but** the frontend won't be used from here — your phone will hit Railway. You can still visit the Space URL directly for backend API docs at `/api/docs`.

Additionally, tighten CORS if you want (currently it's `*`): edit [backend/main.py](backend/main.py) and set `allow_origins=["https://<your-railway-app>.up.railway.app"]`.

**Frontend (Railway):**

1. Create a new Railway project pointing at this repo.
2. In the service settings, set **Root Directory** to `frontend/`. Railway will auto-detect [frontend/Dockerfile](frontend/Dockerfile).
3. In **Variables**, add:
   - `VITE_API_BASE_URL` = `https://<your-space>.hf.space` (your HF Space URL, no trailing slash)

   Also mark it as a **Build-time variable** (or add `VITE_API_BASE_URL` as a build arg in Railway's advanced settings) — Vite needs this at build time, not runtime.
4. Deploy. Railway serves the built SPA via nginx (with SPA-route fallback + $PORT binding).

Open your Railway URL on your phone — all `/api/*` calls will hit the HF Space.

### Data Persistence Note
HuggingFace Spaces **free tier** has ephemeral storage — SQLite and uploaded images will reset on restart. Options:
- **Paid tier**: Persistent disk (recommended)
- **Free tier backup**: Periodically sync `/data/runner.db` to a HF Dataset repo using the HF API

### Data Persistence Note
HuggingFace Spaces **free tier** has ephemeral storage — SQLite and uploaded images will reset on restart. Options:
- **Paid tier**: Persistent disk (recommended)
- **Free tier backup**: Periodically sync `/data/runner.db` to a HF Dataset repo using the HF API

## Environment Variables

### Backend (HuggingFace Spaces)

| Variable | Required | Description |
|---|---|---|
| `APP_PASSWORD` | One of these | Plain-text login password (simplest) |
| `PASSWORD_HASH` | One of these | Pre-computed bcrypt hash of login password |
| `JWT_SECRET` | Yes | Secret key for JWT signing (32+ chars) |
| `OPENAI_API_KEY` | No | Enables GPT-5 vision screenshot parsing fallback |
| `OPENAI_MODEL` | No | Defaults to `gpt-5-mini`; override e.g. to `gpt-5-nano` to save cost |
| `DATA_DIR` | No | Data directory path (default: `./data`) |

### Frontend (Railway, decoupled deploy only)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | Yes (build-time) | Absolute URL of the HF Spaces backend, e.g. `https://arko-runner.hf.space`. Must be set as a **Build-time** variable in Railway. |

## Default Credentials (local dev only)
If `PASSWORD_HASH` is not set, a default hash for password `runner123` is used. **Change this before deploying.**
