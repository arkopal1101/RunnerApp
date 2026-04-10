import { useState, useEffect } from 'react'
import Login from './components/Login.jsx'
import PlanViewer from './components/PlanViewer.jsx'
import DailyCheckin from './components/DailyCheckin.jsx'
import WeeklyLog from './components/WeeklyLog.jsx'
import Dashboard from './components/Dashboard.jsx'

const NAV_ITEMS = [
  { id: 'plan', label: 'THE PLAN' },
  { id: 'checkin', label: 'DAILY CHECK-IN' },
  { id: 'weekly', label: 'WEEKLY LOG' },
  { id: 'dashboard', label: 'DASHBOARD' },
]

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('runner_token'))
  const [activeTab, setActiveTab] = useState('plan')

  useEffect(() => {
    if (token) localStorage.setItem('runner_token', token)
    else localStorage.removeItem('runner_token')
  }, [token])

  if (!token) {
    return <Login onLogin={setToken} />
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* App nav */}
      <div className="app-nav">
        <div className="nav-tabs">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                background: 'none',
                border: 'none',
                color: activeTab === item.id ? 'var(--accent)' : 'var(--muted)',
                fontFamily: "'DM Mono', monospace",
                fontSize: 11,
                letterSpacing: 2,
                textTransform: 'uppercase',
                padding: '16px 20px',
                borderBottom: activeTab === item.id ? '2px solid var(--accent)' : '2px solid transparent',
                whiteSpace: 'nowrap',
                transition: 'all 0.2s',
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
        <button
          onClick={() => setToken(null)}
          style={{
            background: 'none',
            border: '1px solid var(--border)',
            color: 'var(--muted)',
            fontFamily: "'DM Mono', monospace",
            fontSize: 10,
            letterSpacing: 2,
            padding: '6px 12px',
            textTransform: 'uppercase',
          }}
        >
          LOGOUT
        </button>
      </div>

      {/* Tab content */}
      {activeTab === 'plan' && <PlanViewer />}
      {activeTab === 'checkin' && <DailyCheckin token={token} />}
      {activeTab === 'weekly' && <WeeklyLog token={token} />}
      {activeTab === 'dashboard' && <Dashboard token={token} />}
    </div>
  )
}
