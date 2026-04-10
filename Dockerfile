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

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

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
    pytesseract \
    Pillow \
    google-generativeai

# Create data directory
RUN mkdir -p /data/uploads

# HuggingFace Spaces requires port 7860
EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
