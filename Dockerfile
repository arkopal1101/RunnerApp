# ── Stage 1: Build React frontend ──────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build
# Output goes to /app/static (configured in vite.config.js)

# ── Stage 2: Python backend ─────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy backend
COPY backend/ ./backend/

# Copy built frontend static files
COPY --from=frontend-builder /app/static ./static/

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    sqlalchemy \
    python-jose[cryptography] \
    bcrypt \
    python-multipart \
    requests

# Persistent storage: mount an HF Storage Bucket at /data (see README / Space settings).
# DATA_DIR is read by backend/database.py and checkin.py to locate runner.db and uploads.
ENV DATA_DIR=/data
RUN mkdir -p /data/uploads

# HuggingFace Spaces requires port 7860
EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
