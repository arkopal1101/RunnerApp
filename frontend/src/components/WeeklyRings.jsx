// Three concentric SVG progress rings — Apple Watch style.
// Each ring maps one of the three goals: Volume, Sessions, Z2 Adherence.

const RING_COLORS = {
  volume: 'var(--accent)',     // yellow
  sessions: 'var(--accent3)',  // blue
  z2_adherence: 'var(--phase2)', // purple
}

function Ring({ cx, cy, r, stroke, color, pct, trackColor = 'rgba(255,255,255,0.06)' }) {
  const C = 2 * Math.PI * r
  const dashOffset = C * (1 - Math.min(100, Math.max(0, pct)) / 100)
  return (
    <>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={trackColor} strokeWidth={stroke} />
      <circle
        cx={cx} cy={cy} r={r} fill="none"
        stroke={color} strokeWidth={stroke}
        strokeDasharray={C}
        strokeDashoffset={dashOffset}
        strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}
        style={{ transition: 'stroke-dashoffset 0.6s ease' }}
      />
    </>
  )
}

function Legend({ label, value, color, subtext }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase' }}>
          {label}
        </div>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--text)' }}>
          {value}
        </div>
        {subtext && (
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: 'var(--muted)' }}>
            {subtext}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * rings: { volume, sessions, z2_adherence } — each { label, pct, display, ... }
 */
export default function WeeklyRings({ rings, week }) {
  if (!rings) return null
  const size = 180
  const cx = size / 2
  const cy = size / 2
  const stroke = 10
  // Nested radii: outer, middle, inner
  const r0 = size / 2 - stroke
  const r1 = r0 - stroke - 4
  const r2 = r1 - stroke - 4

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap' }}>
      <svg width={size} height={size} style={{ flexShrink: 0 }}>
        <Ring cx={cx} cy={cy} r={r0} stroke={stroke} color={RING_COLORS.volume} pct={rings.volume?.pct || 0} />
        <Ring cx={cx} cy={cy} r={r1} stroke={stroke} color={RING_COLORS.sessions} pct={rings.sessions?.pct || 0} />
        <Ring cx={cx} cy={cy} r={r2} stroke={stroke} color={RING_COLORS.z2_adherence} pct={rings.z2_adherence?.pct || 0} />
        <text x={cx} y={cy - 4} textAnchor="middle"
              style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 28, fill: 'var(--text)', letterSpacing: 1 }}>
          W{week}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle"
              style={{ fontFamily: "'DM Mono', monospace", fontSize: 9, fill: 'var(--muted)', letterSpacing: 2, textTransform: 'uppercase' }}>
          Goals
        </text>
      </svg>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <Legend label={rings.volume?.label || 'Volume'}
                value={rings.volume?.display || '—'}
                subtext={`${rings.volume?.pct ?? 0}%`}
                color={RING_COLORS.volume} />
        <Legend label={rings.sessions?.label || 'Sessions'}
                value={rings.sessions?.display || '—'}
                subtext={`${rings.sessions?.pct ?? 0}%`}
                color={RING_COLORS.sessions} />
        <Legend label={rings.z2_adherence?.label || 'Z2 Adherence'}
                value={rings.z2_adherence?.display || '—'}
                subtext={`HR cap ${rings.z2_adherence?.hr_cap ?? '—'} · ${rings.z2_adherence?.compliant_runs ?? 0}/${rings.z2_adherence?.total_runs_with_hr ?? 0} runs`}
                color={RING_COLORS.z2_adherence} />
      </div>
    </div>
  )
}
