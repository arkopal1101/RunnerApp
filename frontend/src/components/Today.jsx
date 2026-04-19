import { useState, useEffect } from 'react'
import { PHASE_NAMES, PHASE_COLORS, DAY_TYPE_COLORS, getCTALabel, getCTATab, restDayMessage } from '../utils/planData'
import { apiUrl } from '../utils/api'
import WeeklyRings from './WeeklyRings'
import WeekOverWeek from './WeekOverWeek'

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

function StatusBadge({ status }) {
  const isGood = status === 'on_track'
  return (
    <span style={{
      display: 'inline-block',
      padding: '3px 10px',
      fontFamily: "'DM Mono', monospace",
      fontSize: 10,
      letterSpacing: 2,
      textTransform: 'uppercase',
      border: `1px solid ${isGood ? 'var(--accent)' : 'var(--accent2)'}`,
      color: isGood ? 'var(--accent)' : 'var(--accent2)',
      background: isGood ? 'rgba(232,255,71,0.05)' : 'rgba(255,107,53,0.05)',
    }}>
      {isGood ? 'On Track' : 'Needs Attention'}
    </span>
  )
}

function PhaseGateReq({ req }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '8px 0',
      borderBottom: '1px solid var(--border)',
    }}>
      <span style={{
        width: 18,
        height: 18,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: `1px solid ${req.met ? 'var(--accent)' : 'var(--border)'}`,
        background: req.met ? 'var(--accent)' : 'transparent',
        color: req.met ? '#000' : 'var(--muted)',
        fontSize: 11,
        flexShrink: 0,
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
  )
}

function MetricTile({ label, value, sub, color = 'var(--accent)' }) {
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '14px 16px' }}>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 4 }}>{label}</div>
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 26, color, lineHeight: 1.1 }}>{value}</div>
      {sub && <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: 'var(--muted)', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

export default function Today({ token, onNavigate }) {
  const [data, setData] = useState(null)
  const [coachNote, setCoachNote] = useState(null)
  const [weeklySummary, setWeeklySummary] = useState(null)
  const [todayCompletion, setTodayCompletion] = useState(null)
  const [restSaving, setRestSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchWeekCompletion = (week, auth) =>
    fetch(apiUrl(`/api/day-log/week/${week}`), auth)
      .then(r => r.ok ? r.json() : null)
      .catch(() => null)

  useEffect(() => {
    const auth = { headers: { Authorization: `Bearer ${token}` } }
    // Fire in parallel — Today data is required, others are optional.
    const p1 = fetch(apiUrl('/api/today'), auth).then(r => r.json())
    const p2 = fetch(apiUrl('/api/coach/pre-run'), auth)
      .then(r => r.ok ? r.json() : null)
      .catch(() => null)
    const p3 = fetch(apiUrl('/api/progress/weekly-summary'), auth)
      .then(r => r.ok ? r.json() : null)
      .catch(() => null)
    Promise.all([p1, p2, p3])
      .then(([todayData, note, summary]) => {
        setData(todayData); setCoachNote(note); setWeeklySummary(summary); setLoading(false)
        // Check if today is already logged
        if (todayData?.current_week != null && todayData?.day_of_week != null) {
          fetchWeekCompletion(todayData.current_week, auth).then(wk => {
            if (wk?.by_day_of_week) {
              setTodayCompletion(wk.by_day_of_week[String(todayData.day_of_week)] || null)
            }
          })
        }
      })
      .catch(() => { setError('Could not load today data.'); setLoading(false) })
  }, [token])

  async function markRested(week, dow) {
    if (restSaving || todayCompletion) return
    setRestSaving(true)
    try {
      const res = await fetch(apiUrl('/api/day-log'), {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ kind: 'rest', week_number: week, day_of_week: dow }),
      })
      if (res.ok) setTodayCompletion(await res.json())
    } finally {
      setRestSaving(false)
    }
  }

  if (loading) return (
    <div style={{ padding: 40, fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)' }}>
      Loading your day...
    </div>
  )

  if (error) return (
    <div style={{ padding: 40 }}>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--accent2)', marginBottom: 12 }}>{error}</div>
      <button onClick={() => { setLoading(true); setError('') }} style={{ background: 'var(--accent)', border: 'none', color: '#000', padding: '8px 16px', fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2 }}>Retry</button>
    </div>
  )

  if (!data) return null

  const { current_week, current_phase, phase_name, day_of_week, day_type, next_action,
    plan_complete, phase_progress_pct, weeks_until_phase_gate,
    latest_checkin, latest_weekly_log, phase_gate, status, coaching_note, today_date,
    week_focus, activity } = data

  const phaseColor = PHASE_COLORS[current_phase]
  const dayColor = DAY_TYPE_COLORS[day_type] || 'var(--muted)'
  const dayName = DAY_NAMES[day_of_week] || 'Today'

  // Format today's date nicely
  const dateStr = today_date ? new Date(today_date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }) : dayName

  const ctaLabel = getCTALabel(day_type, next_action)
  const ctaTab = getCTATab(day_type, next_action)

  const gateStatusMap = {
    ready: { label: 'Ready to progress', color: 'var(--accent)' },
    almost_ready: { label: 'Almost ready', color: 'var(--phase2)' },
    repeat_phase: { label: 'Keep building', color: 'var(--accent2)' },
    insufficient_data: { label: 'Need more data', color: 'var(--muted)' },
    taper: { label: 'Race taper mode', color: 'var(--phase4)' },
  }
  const gateInfo = gateStatusMap[phase_gate?.status] || gateStatusMap.insufficient_data

  return (
    <div className="page-pad">
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 3, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 6 }}>
          {dateStr}
        </div>
        <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 'clamp(32px, 6vw, 52px)', lineHeight: 1, letterSpacing: 1, marginBottom: 12 }}>
          {plan_complete ? 'Plan Complete' : `Week ${current_week} of 32`}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, padding: '3px 10px', border: `1px solid ${phaseColor}`, color: phaseColor, textTransform: 'uppercase' }}>
            Phase {current_phase} · {phase_name}
          </span>
          <StatusBadge status={status} />
        </div>
      </div>

      {plan_complete ? (
        <div style={{ background: 'var(--surface)', border: `1px solid var(--accent)`, borderTop: `3px solid var(--accent)`, padding: 24, marginBottom: 32 }}>
          <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 28, marginBottom: 8 }}>32-Week Plan Complete</div>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
            You've completed the full training plan. Review your progress in the Dashboard.
          </div>
        </div>
      ) : (
        <>
          {/* Today's workout — full activity spec from plan (with any adjustments merged) */}
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderLeft: `3px solid ${dayColor}`,
            padding: '20px 24px',
            marginBottom: 24,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
              <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase' }}>
                {dayName}'s Training
              </span>
              {activity?.adjusted && (
                <span
                  title={activity.adjustment_rationale}
                  style={{
                    fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 1,
                    padding: '2px 8px', border: '1px solid var(--accent3)',
                    color: 'var(--accent3)', textTransform: 'uppercase',
                  }}
                >
                  Adjusted
                </span>
              )}
            </div>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 28, color: dayColor, letterSpacing: 1, marginBottom: 8 }}>
              {activity?.type_label || getDayLabel(day_type, current_week)}
            </div>
            {week_focus && (
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)', marginBottom: 16, fontStyle: 'italic' }}>
                {week_focus}
              </div>
            )}

            {/* Activity detail rows */}
            {activity?.details?.length > 0 && (
              <ul style={{ listStyle: 'none', marginBottom: 16, borderTop: '1px solid var(--border)' }}>
                {activity.details.map(([label, val], i) => (
                  <li key={i} style={{
                    fontSize: 13,
                    color: 'var(--muted)',
                    padding: '8px 0',
                    borderBottom: '1px solid var(--border)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 12,
                  }}>
                    <span>{label}</span>
                    <span style={{ color: 'var(--text)', fontWeight: 500, textAlign: 'right', fontSize: 12 }}>{val}</span>
                  </li>
                ))}
              </ul>
            )}

            {/* Day-specific note */}
            {activity?.note && (
              <div style={{
                marginBottom: 10,
                padding: '10px 14px',
                background: 'var(--surface2)',
                fontSize: 12,
                color: 'var(--muted)',
                fontStyle: 'italic',
                borderLeft: '2px solid var(--border)',
              }}>
                {activity.note}
              </div>
            )}

            {/* Adjustment rationale */}
            {activity?.adjusted && activity.adjustment_rationale && (
              <div style={{
                marginBottom: 16,
                padding: '10px 14px',
                background: 'rgba(71,184,255,0.05)',
                fontSize: 12,
                color: 'var(--accent3)',
                borderLeft: '2px solid var(--accent3)',
                lineHeight: 1.5,
              }}>
                <strong style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 1, textTransform: 'uppercase' }}>Why adjusted: </strong>
                {activity.adjustment_rationale}
              </div>
            )}

            {/* Rest-day funny message + inline Rested Today button */}
            {day_type === 'rest' && !todayCompletion && (
              <div style={{
                padding: '12px 14px',
                marginBottom: 14,
                background: 'rgba(232,255,71,0.04)',
                border: '1px solid var(--border)',
                fontFamily: "'DM Sans', sans-serif",
                fontSize: 14,
                color: 'var(--text)',
                lineHeight: 1.5,
              }}>
                {restDayMessage(current_week, day_of_week)}
              </div>
            )}

            {/* Primary CTA — context-aware */}
            {todayCompletion ? (
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 10,
                padding: '10px 20px',
                background: 'var(--accent)', color: '#000',
                fontFamily: "'DM Mono', monospace", fontSize: 12,
                letterSpacing: 3, textTransform: 'uppercase', fontWeight: 'bold',
              }}>
                ✓ Logged Today
                <span style={{ fontSize: 10, opacity: 0.75, letterSpacing: 1 }}>
                  {todayCompletion.kind}
                </span>
              </div>
            ) : day_type === 'rest' ? (
              <button
                onClick={() => markRested(current_week, day_of_week)}
                disabled={restSaving}
                style={{
                  background: 'var(--accent)', border: 'none', color: '#000',
                  fontFamily: "'DM Mono', monospace", fontSize: 12, letterSpacing: 3,
                  textTransform: 'uppercase', padding: '12px 24px', fontWeight: 'bold',
                  cursor: restSaving ? 'not-allowed' : 'pointer', opacity: restSaving ? 0.7 : 1,
                }}
              >
                {restSaving ? 'Saving…' : 'Rested Today'}
              </button>
            ) : (
              <button
                onClick={() => onNavigate(ctaTab)}
                style={{
                  background: 'var(--accent)', border: 'none', color: '#000',
                  fontFamily: "'DM Mono', monospace", fontSize: 12, letterSpacing: 3,
                  textTransform: 'uppercase', padding: '12px 24px', fontWeight: 'bold', cursor: 'pointer',
                }}
              >
                {ctaLabel}
              </button>
            )}
          </div>

          {/* Phase progress bar */}
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '16px 20px', marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: phaseColor, textTransform: 'uppercase' }}>
                Phase {current_phase} Progress
              </span>
              <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)' }}>
                {weeks_until_phase_gate} weeks to gate
              </span>
            </div>
            <div style={{ background: 'var(--surface2)', height: 5, borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${phase_progress_pct}%`, background: phaseColor, transition: 'width 0.5s' }} />
            </div>
          </div>
        </>
      )}

      {/* Latest data grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 32 }}>
        {latest_checkin ? (
          <>
            <MetricTile label="Last Run" value={latest_checkin.total_distance_km ? `${latest_checkin.total_distance_km} km` : '--'} sub={latest_checkin.checkin_date} />
            <MetricTile label="Last Pace" value={latest_checkin.avg_pace_per_km || '--'} sub="avg pace" color="var(--accent3)" />
            <MetricTile label="Last HR" value={latest_checkin.avg_hr_bpm ? `${latest_checkin.avg_hr_bpm}` : '--'} sub="avg bpm" color="var(--phase2)" />
          </>
        ) : (
          <div style={{ gridColumn: '1 / -1', background: 'var(--surface)', border: '1px solid var(--border)', padding: '20px 24px' }}>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)', marginBottom: 10 }}>
              No runs logged yet. Log your first run to start tracking pace, heart rate, and weekly volume.
            </div>
            <button onClick={() => onNavigate('checkin')} style={{ background: 'none', border: '1px solid var(--accent)', color: 'var(--accent)', fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, padding: '7px 14px', cursor: 'pointer', textTransform: 'uppercase' }}>
              Log Run
            </button>
          </div>
        )}
        {latest_weekly_log ? (
          <MetricTile label="Weight" value={`${latest_weekly_log.weight_kg} kg`} sub={`W${latest_weekly_log.week_number}`} color="var(--text)" />
        ) : (
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '14px 16px' }}>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 4 }}>Weight</div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>No check-in yet</div>
            <button onClick={() => onNavigate('weekly')} style={{ background: 'none', border: '1px solid var(--border)', color: 'var(--muted)', fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 1, padding: '4px 8px', cursor: 'pointer', textTransform: 'uppercase' }}>
              Log now
            </button>
          </div>
        )}
      </div>

      {/* Weekly progress rings */}
      {weeklySummary?.rings && (
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          padding: '20px 24px',
          marginBottom: 24,
        }}>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 14 }}>
            This Week's Goals
          </div>
          <WeeklyRings rings={weeklySummary.rings} week={weeklySummary.week} />
        </div>
      )}

      {/* Week-over-week */}
      {weeklySummary?.week_over_week && (
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          padding: '20px 24px',
          marginBottom: 24,
        }}>
          <WeekOverWeek wow={weeklySummary.week_over_week} week={weeklySummary.week} />
        </div>
      )}

      {/* Phase Gate */}
      {phase_gate && phase_gate.requirements?.length > 0 && (
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderTop: `3px solid ${gateInfo.color}`,
          padding: '20px 24px',
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 20, letterSpacing: 1 }}>
              Phase {current_phase} Gate
            </div>
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, padding: '3px 10px', border: `1px solid ${gateInfo.color}`, color: gateInfo.color, textTransform: 'uppercase' }}>
              {gateInfo.label}
            </span>
          </div>
          {phase_gate.requirements.map((req, i) => (
            <PhaseGateReq key={i} req={req} />
          ))}
          {phase_gate.message && (
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)', marginTop: 12, fontStyle: 'italic' }}>
              {phase_gate.message}
            </div>
          )}
        </div>
      )}

      {/* Coach note — LLM-generated pre-run target + guidance (falls back to rules) */}
      {(coachNote?.text || coaching_note) && (
        <div style={{
          background: 'rgba(232,255,71,0.04)',
          border: '1px solid rgba(232,255,71,0.12)',
          padding: '16px 20px',
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--accent)', textTransform: 'uppercase' }}>Coach Note</span>
            {coachNote?.model && coachNote.model !== 'rules' && (
              <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 9, letterSpacing: 1, color: 'var(--muted)', textTransform: 'uppercase' }}>
                {coachNote.model}
              </span>
            )}
          </div>
          <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6 }}>
            {coachNote?.text || coaching_note}
          </div>
        </div>
      )}

      {/* Quick nav */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 24 }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 12 }}>Quick Actions</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {[
            { label: 'Log Run', tab: 'checkin' },
            { label: 'Weekly Check-In', tab: 'weekly' },
            { label: 'View Plan', tab: 'plan' },
            { label: 'Dashboard', tab: 'dashboard' },
          ].map(({ label, tab }) => (
            <button
              key={tab}
              onClick={() => onNavigate(tab)}
              style={{
                background: 'none',
                border: '1px solid var(--border)',
                color: 'var(--muted)',
                fontFamily: "'DM Mono', monospace",
                fontSize: 11,
                letterSpacing: 1,
                padding: '8px 16px',
                cursor: 'pointer',
                textTransform: 'uppercase',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => { e.target.style.borderColor = 'var(--accent)'; e.target.style.color = 'var(--accent)' }}
              onMouseLeave={e => { e.target.style.borderColor = 'var(--border)'; e.target.style.color = 'var(--muted)' }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function getDayLabel(dayType, week) {
  if (week === 32 && dayType === 'long-run') return 'RACE DAY'
  switch (dayType) {
    case 'run': return 'Easy Zone 2 Run'
    case 'long-run': return `Long Run - Week ${week}`
    case 'tempo': return 'Tempo / Intervals'
    case 'strength': return 'Full Body Strength'
    case 'rest': return 'Rest & Recovery'
    default: return 'Training Day'
  }
}
