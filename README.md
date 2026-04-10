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

## Deploy to HuggingFace Spaces

1. Create a new Space: **Docker** type, port **7860**
2. Push this repo to the Space's git remote
3. In **Settings → Repository Secrets**, add:
   - `PASSWORD_HASH` — from `generate_password_hash.py`
   - `JWT_SECRET` — any 32+ character random string
   - `GEMINI_API_KEY` — (optional) for LLM image parsing fallback
4. The Space will build and deploy automatically

### Data Persistence Note
HuggingFace Spaces **free tier** has ephemeral storage — SQLite and uploaded images will reset on restart. Options:
- **Paid tier**: Persistent disk (recommended)
- **Free tier backup**: Periodically sync `/data/runner.db` to a HF Dataset repo using the HF API

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PASSWORD_HASH` | Yes | bcrypt hash of your login password |
| `JWT_SECRET` | Yes | Secret key for JWT signing (32+ chars) |
| `GEMINI_API_KEY` | No | Enables Gemini Flash for screenshot parsing |
| `DATA_DIR` | No | Data directory path (default: `./data`) |

## Default Credentials (local dev only)
If `PASSWORD_HASH` is not set, a default hash for password `runner123` is used. **Change this before deploying.**
