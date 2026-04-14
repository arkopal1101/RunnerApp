import { useState, useEffect } from 'react'
import Login from './components/Login.jsx'
import Today from './components/Today.jsx'
import PlanViewer from './components/PlanViewer.jsx'
import LogRun from './components/LogRun.jsx'
import WeeklyLog from './components/WeeklyLog.jsx'
import Dashboard from './components/Dashboard.jsx'

const NAV_ITEMS = [
  { id: 'today', label: 'Today' },
  { id: 'plan', label: 'Plan' },
  { id: 'checkin', label: 'Log Run' },
  { id: 'weekly', label: 'Weekly Check-In' },
  { id: 'dashboard', label: 'Dashboard' },
]

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('runner_token'))
  const [activeTab, setActiveTab] = useState('today')

  useEffect(() => {
    if (token) localStorage.setItem('runner_token', token)
    else localStorage.removeItem('runner_token')
  }, [token])

  if (!token) {
    return <Login onLogin={setToken} />
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      <div className="app-nav">
        <div className="nav-tabs">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`nav-tab${activeTab === item.id ? ' nav-tab--active' : ''}`}
            >
              {item.label}
            </button>
          ))}
        </div>
        <button className="nav-logout" onClick={() => setToken(null)}>
          Logout
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'today' && <Today token={token} onNavigate={setActiveTab} />}
        {activeTab === 'plan' && <PlanViewer />}
        {activeTab === 'checkin' && <LogRun token={token} />}
        {activeTab === 'weekly' && <WeeklyLog token={token} />}
        {activeTab === 'dashboard' && <Dashboard token={token} />}
      </div>
    </div>
  )
}
