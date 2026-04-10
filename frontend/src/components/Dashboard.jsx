import { useState, useEffect } from 'react'
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
  ResponsiveContainer, Legend,
} from 'recharts'

const PHASE_COLORS = { 1: '#47b8ff', 2: '#b847ff', 3: '#ff6b35', 4: '#e8ff47' }

function SummaryCard({ label, value, sub, color = 'var(--accent)' }) {
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '20px 24px' }}>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8 }}>{label}</div>
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, color, lineHeight: 1, marginBottom: 4 }}>{value}</div>
      {sub && <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)' }}>{sub}</div>}
    </div>
  )
}

function ChartContainer({ title, badge, children }) {
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '24px', marginBottom: 24 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 20 }}>
        <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, letterSpacing: 1 }}>{title}</div>
        {badge && (
          <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, padding: '2px 8px', background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--muted)', textTransform: 'uppercase' }}>
            {badge}
          </span>
        )}
      </div>
      {children}
    </div>
  )
}

const chartTheme = {
  style: { background: 'transparent' },
  contentStyle: { background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 0, fontFamily: "'DM Mono', monospace", fontSize: 11 },
  labelStyle: { color: 'var(--text)' },
  itemStyle: { color: 'var(--muted)' },
}

function secondsToPace(seconds) {
  if (!seconds) return '—'
  return `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`
}

export default function Dashboard({ token }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/progress', { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => { setError('Failed to load progress data.'); setLoading(false) })
  }, [token])

  if (loading) return (
    <div style={{ padding: 40, fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)' }}>
      LOADING DASHBOARD...
    </div>
  )

  if (error) return (
    <div style={{ padding: 40, fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--accent2)' }}>{error}</div>
  )

  if (!data) return null

  const { summary, weight_chart, waist_chart, pace_chart, hr_chart, volume_chart, references } = data
  const phase = summary.current_phase
  const phaseColor = PHASE_COLORS[phase]

  return (
    <div className="page-pad">
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1, marginBottom: 8 }}>PROGRESS DASHBOARD</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32 }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase' }}>
          Week {summary.current_week} of 32
        </div>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, padding: '3px 10px', border: `1px solid ${phaseColor}`, color: phaseColor, textTransform: 'uppercase' }}>
          Phase {phase} · {summary.phase_progress_pct}%
        </div>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 40 }}>
        <SummaryCard
          label="Current Weight"
          value={summary.latest_weight ? `${summary.latest_weight} kg` : '—'}
          sub={`Target: ${summary.target_weight} kg`}
          color={summary.latest_weight && summary.latest_weight > summary.target_weight ? 'var(--text)' : 'var(--accent)'}
        />
        <SummaryCard
          label="Runs This Week"
          value={summary.runs_this_week}
          sub="logged check-ins"
          color="var(--accent3)"
        />
        <SummaryCard
          label="Latest Z2 Pace"
          value={summary.latest_pace || '—'}
          sub={`Baseline: ${summary.baseline_pace}/km`}
          color={summary.latest_pace ? 'var(--accent)' : 'var(--muted)'}
        />
        <SummaryCard
          label="Weeks to Phase Gate"
          value={summary.weeks_until_phase_gate}
          sub={`Phase ${phase} gate`}
          color={phaseColor}
        />
      </div>

      {/* Weight chart */}
      <ChartContainer title="Weight Over Time" badge="kg">
        {weight_chart.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={weight_chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="week" tickFormatter={w => `W${w}`} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <YAxis domain={[76, 96]} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <Tooltip {...chartTheme} formatter={(v) => [`${v} kg`]} />
              <ReferenceLine y={references.start_weight} stroke="#666" strokeDasharray="4 4" label={{ value: 'Start 94kg', fill: '#666', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <ReferenceLine y={references.target_weight} stroke="#e8ff47" strokeDasharray="4 4" label={{ value: 'Target 80kg', fill: '#e8ff47', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <Line type="monotone" dataKey="weight" stroke="#e8ff47" strokeWidth={2} dot={{ fill: '#e8ff47', r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>
            No weight data yet — log your first weekly check-in
          </div>
        )}
      </ChartContainer>

      {/* Waist chart */}
      <ChartContainer title="Waist Over Time" badge="inches">
        {waist_chart.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={waist_chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="week" tickFormatter={w => `W${w}`} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <YAxis domain={[30, 40]} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <Tooltip {...chartTheme} formatter={(v) => [`${v}"`]} />
              <ReferenceLine y={references.start_waist} stroke="#666" strokeDasharray="4 4" label={{ value: 'Start 38"', fill: '#666', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <ReferenceLine y={references.target_waist} stroke="#e8ff47" strokeDasharray="4 4" label={{ value: 'Target 32"', fill: '#e8ff47', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <Line type="monotone" dataKey="waist" stroke="#47b8ff" strokeWidth={2} dot={{ fill: '#47b8ff', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>
            No waist data yet
          </div>
        )}
      </ChartContainer>

      {/* Zone 2 Pace chart */}
      <ChartContainer title="Zone 2 Pace Over Time" badge="min/km — lower is better">
        {pace_chart.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={pace_chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="week" tickFormatter={w => `W${w}`} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <YAxis reversed domain={[380, 700]} tickFormatter={secondsToPace} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <Tooltip {...chartTheme} formatter={(v) => [secondsToPace(v), 'Pace']} />
              <ReferenceLine y={references.baseline_pace_seconds} stroke="#666" strokeDasharray="4 4" label={{ value: 'Baseline 10:30', fill: '#666', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <ReferenceLine y={references.phase1_gate_seconds} stroke="#47b8ff" strokeDasharray="4 4" label={{ value: 'P1 Gate 7:30', fill: '#47b8ff', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <ReferenceLine y={references.phase2_gate_seconds} stroke="#b847ff" strokeDasharray="4 4" label={{ value: 'P2 Gate 7:00', fill: '#b847ff', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <Line type="monotone" dataKey="pace_seconds" stroke="#ff6b35" strokeWidth={2} dot={{ fill: '#ff6b35', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>
            No pace data yet — upload a daily check-in
          </div>
        )}
      </ChartContainer>

      {/* HR chart */}
      <ChartContainer title="Average Heart Rate Over Time" badge="bpm">
        {hr_chart.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={hr_chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="week" tickFormatter={w => `W${w}`} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <YAxis domain={[120, 175]} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <Tooltip {...chartTheme} formatter={(v) => [`${v} bpm`]} />
              <ReferenceLine y={145} stroke="#e8ff47" strokeDasharray="4 4" label={{ value: 'Z2 ceiling 145', fill: '#e8ff47', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <Line type="monotone" dataKey="avg_hr" stroke="#b847ff" strokeWidth={2} dot={{ fill: '#b847ff', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>
            No HR data yet
          </div>
        )}
      </ChartContainer>

      {/* Weekly volume bar chart */}
      <ChartContainer title="Weekly Run Volume" badge="km / week">
        {volume_chart.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={volume_chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="week" tickFormatter={w => `W${w}`} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <YAxis stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <Tooltip {...chartTheme} formatter={(v) => [`${v} km`]} />
              <Bar dataKey="km" fill="#47b8ff" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>
            No volume data yet
          </div>
        )}
      </ChartContainer>

      {/* Phase progress */}
      <div style={{ background: 'var(--surface)', border: `1px solid var(--border)`, borderTop: `3px solid ${phaseColor}`, padding: '24px' }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: phaseColor, textTransform: 'uppercase', marginBottom: 8 }}>
          Current Phase
        </div>
        <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 28, letterSpacing: 1, marginBottom: 12 }}>
          PHASE {phase} — {['', 'AEROBIC BASE', 'BUILD & RECOMP', 'RACE SPECIFIC', 'PEAK & RACE READY'][phase]}
        </div>
        <div style={{ background: 'var(--surface2)', height: 6, borderRadius: 3, overflow: 'hidden', marginBottom: 8 }}>
          <div style={{ height: '100%', width: `${summary.phase_progress_pct}%`, background: phaseColor, borderRadius: 3, transition: 'width 0.5s' }} />
        </div>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)' }}>
          {summary.phase_progress_pct}% complete · {summary.weeks_until_phase_gate} weeks to gate
        </div>
      </div>
    </div>
  )
}
