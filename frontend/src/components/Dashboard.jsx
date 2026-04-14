import { useState, useEffect } from 'react'
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
  ResponsiveContainer,
} from 'recharts'

const PHASE_COLORS = { 1: '#47b8ff', 2: '#b847ff', 3: '#ff6b35', 4: '#e8ff47' }

/* ── Shared chart tooltip theme ── */
const chartTheme = {
  contentStyle: { background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 0, fontFamily: "'DM Mono', monospace", fontSize: 11 },
  labelStyle: { color: 'var(--text)' },
  itemStyle: { color: 'var(--muted)' },
}

function secondsToPace(s) {
  if (!s) return '--'
  return `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`
}

/* ── Summary metric card ── */
function MetricCard({ label, value, sub, color = 'var(--accent)' }) {
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '18px 22px' }}>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 6 }}>{label}</div>
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 34, color, lineHeight: 1, marginBottom: 3 }}>{value}</div>
      {sub && <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)' }}>{sub}</div>}
    </div>
  )
}

/* ── Chart container ── */
function ChartBox({ title, badge, children }) {
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: 24, marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 18 }}>
        <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 20, letterSpacing: 1 }}>{title}</div>
        {badge && <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, padding: '2px 8px', background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--muted)', textTransform: 'uppercase' }}>{badge}</span>}
      </div>
      {children}
    </div>
  )
}

/* ── Insight card ── */
function InsightCard({ title, status, message, children, color }) {
  const statusColors = {
    improving: 'var(--accent)',
    regressing: 'var(--accent2)',
    tracking: 'var(--accent3)',
    baseline: 'var(--muted)',
    no_data: 'var(--border)',
    steady: 'var(--accent)',
    high_jump: 'var(--accent2)',
    normal_increase: 'var(--accent)',
    low: 'var(--muted)',
    first_week: 'var(--accent3)',
  }
  const borderColor = color || statusColors[status] || 'var(--border)'
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderLeft: `3px solid ${borderColor}`,
      padding: '18px 20px',
    }}>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 6 }}>{title}</div>
      <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6, marginBottom: children ? 12 : 0 }}>{message}</div>
      {children}
    </div>
  )
}

/* ── Phase gate requirements ── */
function PhaseGateCard({ gate, phaseColor }) {
  if (!gate) return null
  const statusMap = {
    ready:              { label: 'Ready to progress', color: 'var(--accent)' },
    almost_ready:       { label: 'Almost ready',      color: 'var(--phase2)' },
    repeat_phase:       { label: 'Keep building',     color: 'var(--accent2)' },
    insufficient_data:  { label: 'Need more data',    color: 'var(--muted)' },
    taper:              { label: 'Race taper',        color: 'var(--phase4)' },
  }
  const { label, color } = statusMap[gate.status] || statusMap.insufficient_data

  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderTop: `3px solid ${color}`, padding: '20px 24px', marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
        <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 20, letterSpacing: 1 }}>
          Phase {gate.phase} Gate
        </div>
        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, padding: '3px 10px', border: `1px solid ${color}`, color, textTransform: 'uppercase' }}>
          {label}
        </span>
      </div>

      {gate.requirements?.length > 0 ? (
        gate.requirements.map((req, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: i < gate.requirements.length - 1 ? '1px solid var(--border)' : 'none' }}>
            <span style={{
              width: 18, height: 18, display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: `1px solid ${req.met ? 'var(--accent)' : 'var(--border)'}`,
              background: req.met ? 'var(--accent)' : 'transparent',
              color: req.met ? '#000' : 'var(--muted)', fontSize: 11, flexShrink: 0,
            }}>
              {req.met ? '✓' : '·'}
            </span>
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: req.met ? 'var(--text)' : 'var(--muted)', flex: 1 }}>
              {req.label}
            </span>
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: req.met ? 'var(--accent)' : 'var(--accent2)' }}>
              {req.current}
            </span>
          </div>
        ))
      ) : (
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)' }}>
          {gate.message || 'Log more runs to evaluate phase readiness.'}
        </div>
      )}
    </div>
  )
}

/* ── Empty chart placeholder ── */
function EmptyChart({ message, cta }) {
  return (
    <div style={{ height: 80, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)' }}>{message}</div>
      {cta && <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--border)' }}>{cta}</div>}
    </div>
  )
}

/* ── Main dashboard ── */
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
      Loading dashboard...
    </div>
  )
  if (error) return (
    <div style={{ padding: 40, fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--accent2)' }}>{error}</div>
  )
  if (!data) return null

  const { summary, weight_chart, waist_chart, pace_chart, hr_chart, volume_chart, references, insights, phase_gate } = data
  const phase = summary.current_phase
  const phaseColor = PHASE_COLORS[phase]

  return (
    <div className="page-pad">
      {/* Header */}
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1, marginBottom: 6 }}>Progress Dashboard</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32, flexWrap: 'wrap' }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase' }}>
          Week {summary.current_week} of 32
        </div>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, padding: '3px 10px', border: `1px solid ${phaseColor}`, color: phaseColor, textTransform: 'uppercase' }}>
          Phase {phase} · {summary.phase_progress_pct}%
        </div>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10, marginBottom: 36 }}>
        <MetricCard
          label="Current Weight"
          value={summary.latest_weight ? `${summary.latest_weight} kg` : '—'}
          sub={`Target: ${summary.target_weight} kg`}
          color={summary.latest_weight && summary.latest_weight <= summary.target_weight ? 'var(--accent)' : 'var(--text)'}
        />
        <MetricCard label="Runs This Week" value={summary.runs_this_week} sub="logged this week" color="var(--accent3)" />
        <MetricCard
          label="Latest Z2 Pace"
          value={summary.latest_pace || '—'}
          sub={`Baseline: ${summary.baseline_pace}/km`}
          color={summary.latest_pace ? 'var(--accent)' : 'var(--muted)'}
        />
        <MetricCard label="Weeks to Phase Gate" value={summary.weeks_until_phase_gate} sub={`Phase ${phase} gate`} color={phaseColor} />
      </div>

      {/* ── Coaching Insights ── */}
      {insights && (
        <div style={{ marginBottom: 36 }}>
          <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 24, letterSpacing: 1, marginBottom: 16, paddingBottom: 10, borderBottom: '1px solid var(--border)' }}>
            Coaching Insights
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
            <InsightCard title="Aerobic Fitness" status={insights.aerobic_fitness?.status} message={insights.aerobic_fitness?.message || 'Upload a run to start tracking pace.'}>
              {insights.aerobic_fitness?.improvement_pct != null && insights.aerobic_fitness.improvement_pct > 0 && (
                <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 26, color: 'var(--accent)', lineHeight: 1 }}>
                  +{insights.aerobic_fitness.improvement_pct}%
                  <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)', marginLeft: 8 }}>pace improvement</span>
                </div>
              )}
            </InsightCard>

            <InsightCard title="Body Recomposition" status={insights.body_recomposition?.status} message={insights.body_recomposition?.message || 'Log a weekly check-in to start tracking.'}>
              {insights.body_recomposition?.weight_change_start != null && (
                <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 26, color: insights.body_recomposition.weight_change_start < 0 ? 'var(--accent)' : 'var(--text)', lineHeight: 1 }}>
                  {insights.body_recomposition.weight_change_start > 0 ? '+' : ''}{insights.body_recomposition.weight_change_start} kg
                  <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)', marginLeft: 8 }}>from start</span>
                </div>
              )}
            </InsightCard>

            <InsightCard title="Training Load" status={insights.training_load?.status} message={insights.training_load?.message || 'No run data yet.'}>
              {insights.training_load?.current_week_km != null && (
                <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 26, color: 'var(--accent3)', lineHeight: 1 }}>
                  {insights.training_load.current_week_km} km
                  <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)', marginLeft: 8 }}>this week</span>
                </div>
              )}
            </InsightCard>

            <InsightCard title="Consistency" status={insights.consistency?.adherence_pct >= 75 ? 'improving' : 'baseline'} message={insights.consistency?.message || 'No run data yet.'}>
              {insights.consistency?.adherence_pct != null && (
                <div>
                  <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 26, color: insights.consistency.adherence_pct >= 75 ? 'var(--accent)' : 'var(--accent2)', lineHeight: 1 }}>
                    {insights.consistency.adherence_pct}%
                    <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)', marginLeft: 8 }}>4-week adherence</span>
                  </div>
                  <div style={{ background: 'var(--surface2)', height: 4, borderRadius: 2, overflow: 'hidden', marginTop: 8 }}>
                    <div style={{ height: '100%', width: `${insights.consistency.adherence_pct}%`, background: insights.consistency.adherence_pct >= 75 ? 'var(--accent)' : 'var(--accent2)' }} />
                  </div>
                </div>
              )}
            </InsightCard>
          </div>

          {/* Next Best Action */}
          {insights.next_best_action && (
            <div style={{ marginTop: 12, padding: '14px 18px', background: 'rgba(232,255,71,0.04)', border: '1px solid rgba(232,255,71,0.12)' }}>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--accent)', textTransform: 'uppercase', marginBottom: 4 }}>Next Best Action</div>
              <div style={{ fontSize: 13, color: 'var(--muted)' }}>{insights.next_best_action.message}</div>
            </div>
          )}
        </div>
      )}

      {/* ── Phase Gate ── */}
      {phase_gate && <PhaseGateCard gate={phase_gate} phaseColor={phaseColor} />}

      {/* ── Charts ── */}
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 24, letterSpacing: 1, marginBottom: 16, paddingBottom: 10, borderBottom: '1px solid var(--border)', marginTop: 8 }}>
        Progress Charts
      </div>

      <ChartBox title="Weight Over Time" badge="kg">
        {weight_chart.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={weight_chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="week" tickFormatter={w => `W${w}`} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <YAxis domain={[76, 96]} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <Tooltip {...chartTheme} formatter={v => [`${v} kg`]} />
              <ReferenceLine y={references.start_weight} stroke="#555" strokeDasharray="4 4" label={{ value: 'Start 94kg', fill: '#555', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <ReferenceLine y={references.target_weight} stroke="#e8ff47" strokeDasharray="4 4" label={{ value: 'Target 80kg', fill: '#e8ff47', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <Line type="monotone" dataKey="weight" stroke="#e8ff47" strokeWidth={2} dot={{ fill: '#e8ff47', r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : <EmptyChart message="No weight data yet." cta="Log your first weekly check-in" />}
      </ChartBox>

      <ChartBox title="Waist Over Time" badge="inches">
        {waist_chart.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={waist_chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="week" tickFormatter={w => `W${w}`} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <YAxis domain={[30, 40]} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <Tooltip {...chartTheme} formatter={v => [`${v}"`]} />
              <ReferenceLine y={references.start_waist} stroke="#555" strokeDasharray="4 4" label={{ value: 'Start 38"', fill: '#555', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <ReferenceLine y={references.target_waist} stroke="#e8ff47" strokeDasharray="4 4" label={{ value: 'Target 32"', fill: '#e8ff47', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <Line type="monotone" dataKey="waist" stroke="#47b8ff" strokeWidth={2} dot={{ fill: '#47b8ff', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : <EmptyChart message="No waist data yet." cta="Log a weekly check-in" />}
      </ChartBox>

      <ChartBox title="Zone 2 Pace Over Time" badge="min/km — lower is better">
        {pace_chart.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={pace_chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="week" tickFormatter={w => `W${w}`} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <YAxis reversed domain={[380, 700]} tickFormatter={secondsToPace} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <Tooltip {...chartTheme} formatter={v => [secondsToPace(v), 'Pace']} />
              <ReferenceLine y={references.baseline_pace_seconds} stroke="#555" strokeDasharray="4 4" label={{ value: 'Baseline 10:30', fill: '#555', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <ReferenceLine y={references.phase1_gate_seconds} stroke="#47b8ff" strokeDasharray="4 4" label={{ value: 'P1 Gate 7:30', fill: '#47b8ff', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <ReferenceLine y={references.phase2_gate_seconds} stroke="#b847ff" strokeDasharray="4 4" label={{ value: 'P2 Gate 7:00', fill: '#b847ff', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <Line type="monotone" dataKey="pace_seconds" stroke="#ff6b35" strokeWidth={2} dot={{ fill: '#ff6b35', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : <EmptyChart message="No pace data yet." cta="Upload a daily run check-in" />}
      </ChartBox>

      <ChartBox title="Average Heart Rate Over Time" badge="bpm">
        {hr_chart.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={hr_chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="week" tickFormatter={w => `W${w}`} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <YAxis domain={[120, 175]} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <Tooltip {...chartTheme} formatter={v => [`${v} bpm`]} />
              <ReferenceLine y={145} stroke="#e8ff47" strokeDasharray="4 4" label={{ value: 'Z2 ceiling 145', fill: '#e8ff47', fontSize: 10, fontFamily: "'DM Mono', monospace" }} />
              <Line type="monotone" dataKey="avg_hr" stroke="#b847ff" strokeWidth={2} dot={{ fill: '#b847ff', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : <EmptyChart message="No heart rate data yet." />}
      </ChartBox>

      <ChartBox title="Weekly Run Volume" badge="km / week">
        {volume_chart.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={volume_chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="week" tickFormatter={w => `W${w}`} stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <YAxis stroke="#444" tick={{ fontFamily: "'DM Mono', monospace", fontSize: 10, fill: '#666' }} />
              <Tooltip {...chartTheme} formatter={v => [`${v} km`]} />
              <Bar dataKey="km" fill="#47b8ff" />
            </BarChart>
          </ResponsiveContainer>
        ) : <EmptyChart message="No volume data yet." cta="Log a run to see weekly totals" />}
      </ChartBox>

      {/* Phase progress */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderTop: `3px solid ${phaseColor}`, padding: 24 }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: phaseColor, textTransform: 'uppercase', marginBottom: 6 }}>Current Phase</div>
        <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 26, letterSpacing: 1, marginBottom: 10 }}>
          PHASE {phase} — {['', 'AEROBIC BASE', 'BUILD & RECOMP', 'RACE SPECIFIC', 'PEAK & RACE READY'][phase]}
        </div>
        <div style={{ background: 'var(--surface2)', height: 5, borderRadius: 3, overflow: 'hidden', marginBottom: 6 }}>
          <div style={{ height: '100%', width: `${summary.phase_progress_pct}%`, background: phaseColor, transition: 'width 0.5s' }} />
        </div>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)' }}>
          {summary.phase_progress_pct}% complete · {summary.weeks_until_phase_gate} weeks to gate
        </div>
      </div>
    </div>
  )
}
