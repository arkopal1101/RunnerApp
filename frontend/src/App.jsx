import { useState, useEffect } from 'react'
import Login from './components/Login.jsx'
import Today from './components/Today.jsx'
import PlanViewer from './components/PlanViewer.jsx'
import LogRun from './components/LogRun.jsx'
import LogWorkout from './components/LogWorkout.jsx'
import WeeklyLog from './components/WeeklyLog.jsx'
import Dashboard from './components/Dashboard.jsx'

const NAV_ITEMS = [
  { id: 'today',     label: 'Today',            short: 'Today' },
  { id: 'plan',      label: 'Plan',             short: 'Plan' },
  { id: 'checkin',   label: 'Log Run',          short: 'Run' },
  { id: 'workout',   label: 'Log Workout',      short: 'Lift' },
  { id: 'weekly',    label: 'Weekly Check-In',  short: 'Weekly' },
  { id: 'dashboard', label: 'Dashboard',        short: 'Stats' },
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
              <span className="nav-tab-label-full">{item.label}</span>
              <span className="nav-tab-label-short">{item.short}</span>
            </button>
          ))}
        </div>
        <button className="nav-logout" onClick={() => setToken(null)}>
          Logout
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'today' && <Today token={token} onNavigate={setActiveTab} />}
        {activeTab === 'plan' && <PlanViewer token={token} />}
        {activeTab === 'checkin' && <LogRun token={token} />}
        {activeTab === 'workout' && <LogWorkout token={token} />}
        {activeTab === 'weekly' && <WeeklyLog token={token} />}
        {activeTab === 'dashboard' && <Dashboard token={token} />}
      </div>
    </div>
  )
}
