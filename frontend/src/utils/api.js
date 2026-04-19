// Central API client.
//
// In dev: VITE_API_BASE_URL is empty, so `/api/*` requests are relative and
// the Vite proxy forwards them to http://localhost:7860.
//
// In production split deploy (frontend on Railway, backend on HuggingFace
// Spaces), set VITE_API_BASE_URL to the Space URL, e.g.
//   VITE_API_BASE_URL=https://<your-space>.hf.space
// and all API calls will use that absolute origin.
//
// In monolithic HF Spaces deploy (backend serves the built frontend too),
// leave VITE_API_BASE_URL unset — same-origin requests just work.

const RAW_BASE = import.meta.env.VITE_API_BASE_URL || ''
// Strip trailing slash so we don't emit double slashes in joins.
const API_BASE = RAW_BASE.replace(/\/+$/, '')

export function apiUrl(path) {
  if (!path.startsWith('/')) path = '/' + path
  return `${API_BASE}${path}`
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Generic request wrapper. Returns the raw Response.
export function apiFetch(path, { token, headers, ...opts } = {}) {
  return fetch(apiUrl(path), {
    ...opts,
    headers: {
      ...(headers || {}),
      ...authHeaders(token),
    },
  })
}

// GET shortcut — returns parsed JSON or throws on non-OK.
export async function apiGet(path, { token } = {}) {
  const res = await apiFetch(path, { token })
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return res.json()
}

// POST with JSON body. Token optional.
export async function apiPost(path, body, { token } = {}) {
  const res = await apiFetch(path, {
    method: 'POST',
    token,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`)
  return res.json()
}

// PUT with JSON body.
export async function apiPut(path, body, { token } = {}) {
  const res = await apiFetch(path, {
    method: 'PUT',
    token,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`PUT ${path} failed: ${res.status}`)
  return res.json()
}
