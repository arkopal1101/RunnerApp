import { useState } from 'react'

export default function Login({ onLogin }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const form = new URLSearchParams()
      form.append('username', 'arko')
      form.append('password', password)
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString(),
      })
      if (!res.ok) {
        setError('Incorrect password.')
        return
      }
      const data = await res.json()
      onLogin(data.access_token)
    } catch {
      setError('Connection error.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div style={{ width: '100%', maxWidth: 400, padding: '0 24px' }}>
        {/* Hero label */}
        <div style={{
          fontFamily: "'DM Mono', monospace",
          fontSize: 11,
          letterSpacing: 3,
          color: 'var(--accent)',
          textTransform: 'uppercase',
          marginBottom: 16,
        }}>
          / Runner App / Private
        </div>

        <h1 style={{
          fontFamily: "'Bebas Neue', sans-serif",
          fontSize: 72,
          lineHeight: 0.9,
          letterSpacing: 2,
          marginBottom: 40,
        }}>
          HALF<br />MARATHON<br /><span style={{ color: 'var(--accent)' }}>MODE</span>
        </h1>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <div style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 10,
              letterSpacing: 2,
              color: 'var(--muted)',
              textTransform: 'uppercase',
              marginBottom: 8,
            }}>
              Password
            </div>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoFocus
              style={{
                width: '100%',
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                color: 'var(--text)',
                fontFamily: "'DM Mono', monospace",
                fontSize: 14,
                padding: '12px 16px',
                outline: 'none',
              }}
              placeholder="Enter password"
            />
          </div>

          {error && (
            <div style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 12,
              color: 'var(--accent2)',
              marginBottom: 16,
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              background: 'var(--accent)',
              border: 'none',
              color: '#000',
              fontFamily: "'DM Mono', monospace",
              fontSize: 12,
              letterSpacing: 3,
              textTransform: 'uppercase',
              padding: '14px',
              fontWeight: 'bold',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'ENTERING...' : 'ENTER'}
          </button>
        </form>
      </div>
    </div>
  )
}
