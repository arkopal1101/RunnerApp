# RunnerApp Deployment Guide

This document covers deploying the RunnerApp to production:
- **Frontend**: Railway
- **Backend**: Hugging Face Spaces

---

## Architecture Overview

```
┌─────────────────┐          ┌──────────────────┐
│   Railway       │          │   HF Spaces      │
│  (Frontend)     │          │  (Backend/API)   │
│  React + Vite   │◄────────►│  FastAPI         │
│  Port: 80/443   │  HTTPS   │  Port: 7860      │
└─────────────────┘          └──────────────────┘
                                      ▲
                                      │
                                   SQLite DB
                                  (persistent)
```

---

## Part 1: Frontend Deployment (Railway)

### Prerequisites
- Railway account: https://railway.app
- GitHub repo with RunnerApp code
- Node.js 18+ (Railway auto-detected)

### Step 1: Create Railway Project

1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your RunnerApp repository
4. Railway auto-detects Node.js and runs:
   ```
   npm install
   npm run build
   ```

### Step 2: Configure Frontend Build

Railway will auto-detect the Vite build. Verify in Railway dashboard:

- **Build Command**: `npm install && npm run build`
- **Start Command**: (Not needed—Railway serves static files)
- **Root Directory**: `frontend` (if not auto-detected, set this)

### Step 3: Environment Variables (Optional)

Frontend needs the backend API URL. In Railway dashboard, add:

```env
VITE_API_URL=https://<backend-domain>/api
```

Update `frontend/src/utils/api.js` or similar to use:

```javascript
const API_BASE = import.meta.env.VITE_API_URL || '/api';
```

*If frontend proxies via `/api`, this may not be needed in production.*

### Step 4: Deploy

1. Railway auto-deploys on GitHub push to main branch
2. Once built, Railway generates a public URL (e.g., `runnerapp.railway.app`)
3. Verify frontend loads and can reach backend API

### Step 5: Custom Domain (Optional)

1. In Railway dashboard → **Settings** → **Domains**
2. Add custom domain (e.g., `runner.example.com`)
3. Update DNS CNAME records as instructed

---

## Part 2: Backend Deployment (Hugging Face Spaces)

### Prerequisites
- HF Account: https://huggingface.co
- HF CLI installed: `pip install huggingface-hub`
- Git LFS (for large files): `git lfs install`

### Step 1: Create HF Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Configure:
   - **Name**: `runner-api`
   - **License**: MIT
   - **Space SDK**: Docker
   - **Private/Public**: Private (recommended for auth endpoints)

### Step 2: Set Up Docker Container

Create `Dockerfile` in project root (if not present):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for pytesseract)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY backend/ ./backend
COPY . .

# Expose port
EXPOSE 7860

# Start server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

### Step 3: Create `app.py` for HF Spaces (Optional)

HF Spaces can run a custom entry point. Create `app.py` at repo root:

```python
#!/usr/bin/env python3
"""HF Spaces entry point."""
import os
import subprocess
import sys

# Set port to 7860 (HF Spaces default)
os.environ.setdefault("PORT", "7860")

# Run Uvicorn
subprocess.run([
    sys.executable, "-m", "uvicorn",
    "backend.main:app",
    "--host", "0.0.0.0",
    "--port", "7860"
])
```

### Step 4: Configure Environment Variables

In HF Spaces **Settings** → **Repository Secrets**, add:

```env
APP_PASSWORD=<your-secure-password>
DATA_DIR=/tmp/data
FRONTEND_URL=https://<railway-frontend-url>
```

**Important**:
- `APP_PASSWORD`: User password for "arko" account (required)
- `DATA_DIR`: Use `/tmp/data` (HF Spaces ephemeral storage) or connect persistent storage
- `FRONTEND_URL`: Frontend domain for CORS (if not using wildcard)

### Step 5: Handle Persistent Data (Critical)

**HF Spaces has ephemeral storage** — `/tmp` is cleared on restart. For persistent SQLite:

#### Option A: Mount HF Datasets (Recommended)

1. Create a private HF Dataset: `https://huggingface.co/datasets/new`
2. In Space settings, mount dataset:
   - **Settings** → **Persistent Storage**
   - Mount path: `/data`
3. Update `backend/database.py`:
   ```python
   DATA_DIR = os.getenv("DATA_DIR", "/data")
   ```

#### Option B: Use PostgreSQL (HF Datasets Alternative)

If SQLite persistence is critical, migrate to PostgreSQL:
1. Provision Postgres (Railway, Neon, etc.)
2. Update `DATABASE_URL`:
   ```python
   DATABASE_URL = os.getenv(
       "DATABASE_URL",
       "postgresql://user:pass@host/db"
   )
   ```

### Step 6: Deploy to HF Spaces

**Option A: Direct Push (Recommended)**

```bash
cd /path/to/RunnerApp

# Set HF repo (one-time)
git remote add huggingface https://huggingface.co/spaces/<your-user>/<space-name>

# Push to deploy
git push huggingface main
```

**Option B: Upload via Web UI**

1. HF Spaces → **Files** tab
2. Upload `Dockerfile`, `app.py`, `backend/`, `requirements.txt`
3. Space auto-builds and deploys

### Step 7: Verify Backend

Once deployed:
1. Check **Space logs** for Uvicorn startup messages
2. Visit `https://<huggingface-user>-<space-name>.hf.space/api/docs` (FastAPI Swagger UI)
3. Test `/api/auth/login` endpoint

---

## Part 3: Environment Configuration

### Backend Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_PASSWORD` | `runner123` | User password (required in prod) |
| `PASSWORD_HASH` | None | Pre-hashed bcrypt password (alt to APP_PASSWORD) |
| `DATA_DIR` | `./data` | SQLite database directory |
| `FRONTEND_URL` | `*` (all origins) | CORS origin (restrict in prod) |
| `DATABASE_URL` | SQLite | Override with PostgreSQL (optional) |

### Frontend Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_URL` | `/api` | Backend API base URL |

### Example `.env` for Development

```env
# Backend
APP_PASSWORD=SecurePassword123!
DATA_DIR=./data

# Frontend (if using VITE_API_URL)
VITE_API_URL=http://localhost:7860/api
```

### Example HF Spaces Secrets

```env
APP_PASSWORD=SecurePassword123!
DATA_DIR=/data
FRONTEND_URL=https://runner.railway.app
```

---

## Part 4: Database Management

### Local SQLite (Development)

```bash
# View schema
sqlite3 data/runner.db ".schema"

# Backup
cp data/runner.db data/runner.backup.db

# Reset (careful!)
rm data/runner.db
```

### On HF Spaces (Persistent Storage)

```bash
# SSH into Space (if enabled)
sqlite3 /data/runner.db ".schema"
```

### Migration: SQLite → PostgreSQL

If migrating from SQLite to Postgres:

1. Install `psycopg2`: `pip install psycopg2-binary`
2. Update `backend/database.py`:
   ```python
   DATABASE_URL = os.getenv(
       "DATABASE_URL",
       "postgresql://user:pass@host/db"
   )
   engine = create_engine(DATABASE_URL)
   ```
3. SQLAlchemy auto-creates tables on first run

---

## Part 5: CORS & API Security

### Development (Current)

```python
# backend/main.py
allow_origins=["*"]
```

### Production (Recommended)

Update `backend/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://runner.railway.app",
        "https://runner.example.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Or use env var:

```python
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
allow_origins=[FRONTEND_URL] if FRONTEND_URL != "*" else ["*"]
```

---

## Part 6: Verification Checklist

### Frontend (Railway)

- [ ] Build succeeds (`npm run build` creates `static/`)
- [ ] Frontend loads on public URL
- [ ] Can reach backend API (check network tab)
- [ ] Login works
- [ ] Dashboard loads and fetches data

### Backend (HF Spaces)

- [ ] Container builds (`docker build` succeeds)
- [ ] Uvicorn starts on port 7860
- [ ] `/api/docs` (Swagger UI) accessible
- [ ] `/api/auth/login` accepts correct credentials
- [ ] `/api/today` returns data (requires auth)
- [ ] Database persists across restarts

### Integration

- [ ] Frontend → Backend API calls work
- [ ] Auth flow (login → token → protected routes) works
- [ ] CORS headers correct (no `Access-Control-Allow-Origin` errors)
- [ ] WebSocket/polling for real-time updates work (if applicable)

---

## Part 7: Monitoring & Troubleshooting

### Railway Frontend

**Logs**: Dashboard → **Logs** tab
- Check for build errors
- Monitor 404 errors for missing assets

**Common Issues**:
- `npm: command not found` — Railway didn't detect Node.js; add `.railwayrc` in frontend/
- Static assets 404 — Vite built to wrong dir; check `vite.config.js` `outDir`

### HF Spaces Backend

**Logs**: Space → **Logs** tab (tail Uvicorn startup)

**Common Issues**:
- `ModuleNotFoundError: No module named 'backend'` — Incorrect working dir; ensure `Dockerfile` `WORKDIR /app` and `COPY backend/`
- `Bind: Address already in use` — HF Spaces restart needed
- Data loss — Ephemeral storage cleared; mount persistent dataset (Section Part 2, Step 5)
- Auth failures — `APP_PASSWORD` not set in secrets

### Debug Endpoints

Add to `backend/main.py` for development:

```python
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/api/debug/env")
def debug_env():
    return {
        "data_dir": os.getenv("DATA_DIR"),
        "frontend_url": os.getenv("FRONTEND_URL"),
    }
```

---

## Part 8: Deployment Workflow

### Automatic (Recommended)

1. **Frontend**: Push to `main` → Railway auto-deploys
2. **Backend**: Push to `main` → HF Spaces auto-pulls and rebuilds

### Manual

**Frontend (Railway)**:
```bash
git push origin main
# Railway auto-triggers build/deploy
```

**Backend (HF Spaces)**:
```bash
git push huggingface main
# Or manually upload files via web UI
```

---

## Part 9: Rollback & Hotfixes

### Railway

1. Dashboard → **Deployments**
2. Find previous successful deployment
3. Click **"Rollback"**

### HF Spaces

1. Space → **Files** tab
2. View commit history
3. Click **"Revert to"** for a previous version

---

## Part 10: Scaling & Performance

### Frontend Caching

In Railway **Settings** → **Build Configuration**:
```bash
VITE_OPTIMIZE_DEPS=true
```

### Backend Optimization

1. **Connection Pooling**: SQLAlchemy uses pool by default
2. **Uvicorn Workers**: `--workers 4` (HF Spaces may be single-worker)
3. **Async Routes**: Ensure routes are `async def`

---

## Support & Debugging

### Local Testing Before Deploy

```bash
# Frontend
cd frontend && npm run build && npm run preview

# Backend
cd backend && pip install -r requirements.txt
export APP_PASSWORD=test123
uvicorn main:app --host 0.0.0.0 --port 7860
```

### Check Deployed API

```bash
# Test login
curl -X POST https://<hf-space>/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"arko","password":"<APP_PASSWORD>"}'

# Test protected endpoint
curl https://<hf-space>/api/today \
  -H "Authorization: Bearer <token>"
```

---

## Quick Reference

| Component | Platform | Port | Entry Point |
|-----------|----------|------|------------|
| Frontend | Railway | 80/443 | `dist/index.html` (Vite) |
| Backend | HF Spaces | 7860 | `uvicorn backend.main:app` |
| Database | Local/Mounted | N/A | `./data/runner.db` or `/data/runner.db` |

---

**Last Updated**: 2026-04-19
**Version**: 1.0
