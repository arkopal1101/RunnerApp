# Frontend-only Dockerfile for Railway (decoupled deploy).
#
# The monolithic HuggingFace Spaces deploy keeps using the root-level
# Dockerfile which bundles frontend + backend. This one builds *only* the
# frontend (Vite + React) and serves it via nginx with SPA fallback.
#
# Required Railway env var:
#   VITE_API_BASE_URL=https://<your-space>.hf.space
# (Set this in Railway's Variables tab before deploying.)
#
# Railway injects $PORT at runtime; nginx.conf.template is rendered at
# container start so the listener binds to whatever port Railway gives us.

# ── Stage 1: Build the Vite bundle ────────────────────────────────────────────
FROM node:20-slim AS builder

WORKDIR /src/frontend
COPY package.json package-lock.json* ./
RUN npm install

COPY . ./

# Vite reads VITE_* build-time env vars. Passing it via ARG lets Railway
# inject it via their Variables UI (they become env vars at build time).
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# vite.config.js writes to ../static (so /src/static inside the builder).
RUN npm run build

# ── Stage 2: nginx serving the built SPA ─────────────────────────────────────
FROM nginx:1.27-alpine

# nginx.conf.template uses $PORT so Railway's dynamic port works.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Copy the built SPA — vite put it one level up from /src/frontend.
COPY --from=builder /src/static /usr/share/nginx/html

# Railway sets $PORT; default to 8080 for local Docker runs.
ENV PORT=8080
# Restrict envsubst so it only expands $PORT in the template and leaves
# nginx's own variables ($uri, $host, ...) alone.
ENV NGINX_ENVSUBST_FILTER=^PORT$
EXPOSE 8080

# The nginx:alpine image's entrypoint auto-envsubst's templates/*.template
# into /etc/nginx/conf.d/*.conf at startup, then execs nginx.
CMD ["nginx", "-g", "daemon off;"]
