// Week-over-week comparison table — shows current vs prior week for
// volume, avg pace, avg HR, session count.
// Color semantics:
//   volume up / sessions up → good (accent yellow)
//   pace down (faster) → good; pace up → regression
//   HR down at similar paces → good

function deltaStyle(delta, kind) {
  if (delta === null || delta === undefined) return { color: 'var(--muted)' }
  if (kind === 'higher_is_better') {
    if (delta > 0) return { color: 'var(--accent)' }
    if (delta < 0) return { color: 'var(--accent2)' }
  } else if (kind === 'lower_is_better') {
    if (delta < 0) return { color: 'var(--accent)' }
    if (delta > 0) return { color: 'var(--accent2)' }
  }
  return { color: 'var(--muted)' }
}

function signed(n, unit = '', digits = 1) {
  if (n === null || n === undefined) return '—'
  const s = n > 0 ? '+' : ''
  return `${s}${typeof n === 'number' ? n.toFixed(digits).replace(/\.0$/, '') : n}${unit}`
}

function Row({ label, current, prev, delta, deltaDisplay, kind }) {
  const s = deltaStyle(delta, kind)
  return (
    <tr style={{ borderBottom: '1px solid var(--border)' }}>
      <td style={{ padding: '10px 12px', fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)', letterSpacing: 1, textTransform: 'uppercase' }}>
        {label}
      </td>
      <td style={{ padding: '10px 12px', fontFamily: "'DM Mono', monospace", fontSize: 13, color: 'var(--text)' }}>
        {current ?? '—'}
      </td>
      <td style={{ padding: '10px 12px', fontFamily: "'DM Mono', monospace", fontSize: 13, color: 'var(--muted)' }}>
        {prev ?? '—'}
      </td>
      <td style={{ padding: '10px 12px', fontFamily: "'DM Mono', monospace", fontSize: 13, fontWeight: 600, ...s }}>
        {deltaDisplay}
      </td>
    </tr>
  )
}

export default function WeekOverWeek({ wow, week }) {
  if (!wow) return null
  const noPrior = wow.prev_week === null || wow.prev_week === undefined

  return (
    <div>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 10 }}>
        {noPrior
          ? `Week ${week} · no prior week to compare`
          : `Week ${week} vs Week ${wow.prev_week}`}
      </div>
      {noPrior ? (
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)', padding: '12px 16px', background: 'var(--surface)', border: '1px solid var(--border)' }}>
          Week-over-week comparisons start from Week 2.
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Metric', 'This week', 'Last week', 'Δ'].map(h => (
                  <th key={h} style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', fontWeight: 400, textAlign: 'left', textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <Row label="Volume"
                   current={`${wow.volume_km.current ?? 0} km`}
                   prev={wow.volume_km.prev !== null ? `${wow.volume_km.prev} km` : null}
                   delta={wow.volume_km.delta}
                   deltaDisplay={signed(wow.volume_km.delta, ' km')}
                   kind="higher_is_better" />
              <Row label="Sessions"
                   current={wow.sessions.current}
                   prev={wow.sessions.prev}
                   delta={wow.sessions.delta}
                   deltaDisplay={signed(wow.sessions.delta, '', 0)}
                   kind="higher_is_better" />
              <Row label="Avg pace"
                   current={wow.avg_pace.current}
                   prev={wow.avg_pace.prev}
                   delta={wow.avg_pace.delta_sec}
                   deltaDisplay={wow.avg_pace.delta_sec !== null ? `${wow.avg_pace.delta_sec > 0 ? '+' : ''}${wow.avg_pace.delta_sec}s/km` : '—'}
                   kind="lower_is_better" />
              <Row label="Avg HR"
                   current={wow.avg_hr.current ? `${wow.avg_hr.current} bpm` : null}
                   prev={wow.avg_hr.prev ? `${wow.avg_hr.prev} bpm` : null}
                   delta={wow.avg_hr.delta_bpm}
                   deltaDisplay={signed(wow.avg_hr.delta_bpm, ' bpm')}
                   kind="lower_is_better" />
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
