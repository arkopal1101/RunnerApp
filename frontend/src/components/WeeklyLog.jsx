import { useState, useEffect } from 'react'
import { START_DATE, START_WEIGHT, TARGET_WEIGHT, START_WAIST, TARGET_WAIST, HEIGHT_CM } from '../utils/planData'
import { apiUrl } from '../utils/api'

function getCurrentWeek() {
  const diffDays = Math.floor((new Date() - START_DATE) / (1000 * 60 * 60 * 24))
  if (diffDays < 0) return 1
  return Math.floor(diffDays / 7) + 1
}

function calcBMI(kg) {
  return (kg / Math.pow(HEIGHT_CM / 100, 2)).toFixed(1)
}

function trendMsg(weightChange) {
  if (weightChange < -0.8) return { text: 'Dropping fast — make sure you\'re fuelling enough for training.', color: 'var(--accent3)' }
  if (weightChange < -0.1) return { text: 'Healthy rate of change. Keep it consistent.', color: 'var(--accent)' }
  if (weightChange < 0.2)  return { text: 'Holding steady — normal during high training weeks.', color: 'var(--muted)' }
  return { text: 'Weight ticked up. Check sleep, stress, and nutrition.', color: 'var(--accent2)' }
}

const INPUT = {
  background: 'var(--surface)',
  border: '1px solid var(--border)',
  color: 'var(--text)',
  fontFamily: "'DM Mono', monospace",
  fontSize: 13,
  padding: '9px 14px',
  width: '100%',
  outline: 'none',
  boxSizing: 'border-box',
}

const LABEL = {
  fontFamily: "'DM Mono', monospace",
  fontSize: 10,
  letterSpacing: 2,
  color: 'var(--muted)',
  textTransform: 'uppercase',
  marginBottom: 5,
  display: 'block',
}

export default function WeeklyLog({ token }) {
  const [weight, setWeight]     = useState('')
  const [waist, setWaist]       = useState('')
  const [chest, setChest]       = useState('')
  const [hips, setHips]         = useState('')
  const [bodyFat, setBodyFat]   = useState('')
  const [notes, setNotes]       = useState('')
  const [weekNum, setWeekNum]   = useState(getCurrentWeek())
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')
  const [saved, setSaved]       = useState(null)
  const [history, setHistory]   = useState([])
  const [loadingHistory, setLoadingHistory] = useState(true)
  // For update flow when week already exists
  const [existingLog, setExistingLog] = useState(null)
  const [isUpdating, setIsUpdating] = useState(false)

  useEffect(() => {
    fetch(apiUrl('/api/log/weekly'), { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(data => {
        setHistory(data)
        setLoadingHistory(false)
        // Check if current week already logged
        const existing = data.find(l => l.week_number === getCurrentWeek())
        if (existing) {
          setExistingLog(existing)
          // Prefill form with existing values
          setWeight(String(existing.weight_kg))
          setWaist(String(existing.waist_inches))
          setChest(existing.chest_inches ? String(existing.chest_inches) : '')
          setHips(existing.hips_inches ? String(existing.hips_inches) : '')
          setBodyFat(existing.body_fat_pct ? String(existing.body_fat_pct) : '')
          setNotes(existing.notes || '')
          setIsUpdating(true)
        }
      })
      .catch(() => setLoadingHistory(false))
  }, [token])

  // Last logged values for comparison
  const lastLog = history.length > 0 ? history[history.length - 1] : null
  const prevWeight = lastLog && !isUpdating ? lastLog.weight_kg : (isUpdating && history.length > 1 ? history[history.length - 2]?.weight_kg : START_WEIGHT)
  const weightNum = parseFloat(weight)
  const bmi = weight ? calcBMI(weightNum) : null
  const changeFromStart = weight ? +(weightNum - START_WEIGHT).toFixed(1) : null
  const changeFromLast  = weight && prevWeight != null ? +(weightNum - prevWeight).toFixed(1) : null
  const waistNum = parseFloat(waist)
  const waistChangeFromStart = waist ? +(waistNum - START_WAIST).toFixed(1) : null
  const weightProgress = weight ? Math.min(100, Math.round((START_WEIGHT - weightNum) / (START_WEIGHT - TARGET_WEIGHT) * 100)) : null
  const trend = changeFromLast !== null ? trendMsg(changeFromLast) : null

  async function handleSubmit(e) {
    e.preventDefault()
    if (!weight || !waist) { setError('Weight and waist are required.'); return }
    setLoading(true)
    setError('')
    try {
      let res, data
      if (isUpdating && existingLog) {
        // PUT update
        res = await fetch(apiUrl(`/api/log/weekly/${existingLog.id}`), {
          method: 'PUT',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            weight_kg: parseFloat(weight),
            waist_inches: parseFloat(waist),
            chest_inches: chest ? parseFloat(chest) : null,
            hips_inches: hips ? parseFloat(hips) : null,
            body_fat_pct: bodyFat ? parseFloat(bodyFat) : null,
            notes,
          }),
        })
      } else {
        // POST new
        res = await fetch(apiUrl('/api/log/weekly'), {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            weight_kg: parseFloat(weight),
            waist_inches: parseFloat(waist),
            chest_inches: chest ? parseFloat(chest) : null,
            hips_inches: hips ? parseFloat(hips) : null,
            body_fat_pct: bodyFat ? parseFloat(bodyFat) : null,
            week_number: weekNum,
            notes,
          }),
        })
        // Handle duplicate week response
        if (res.status === 409) {
          const conflict = await res.json()
          setError(`Week ${weekNum} already has a log. Switching to update mode.`)
          const id = conflict.detail?.existing_id
          if (id) {
            setExistingLog({ id, week_number: weekNum })
            setIsUpdating(true)
          }
          setLoading(false)
          return
        }
      }
      if (!res.ok) throw new Error('Save failed')
      data = await res.json()
      setSaved(data)
      setHistory(prev => {
        const updated = prev.filter(l => l.id !== data.id)
        return [...updated, data].sort((a, b) => a.week_number - b.week_number)
      })
      setExistingLog(data)
    } catch {
      setError('Save failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-pad">
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1, marginBottom: 4 }}>Weekly Check-In</div>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8 }}>
        Body measurements · Week {weekNum}
      </div>

      {/* Update notice */}
      {isUpdating && (
        <div style={{ marginBottom: 20, padding: '10px 14px', background: 'rgba(71,184,255,0.05)', border: '1px solid rgba(71,184,255,0.2)', fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--accent3)' }}>
          Week {weekNum} already logged — editing existing entry.
        </div>
      )}

      {/* Last log reference */}
      {lastLog && !isUpdating && (
        <div style={{ marginBottom: 24, padding: '12px 16px', background: 'var(--surface)', border: '1px solid var(--border)' }}>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8 }}>Last logged (Week {lastLog.week_number})</div>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 13, color: 'var(--text)' }}>{lastLog.weight_kg} kg</span>
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 13, color: 'var(--text)' }}>{lastLog.waist_inches}" waist</span>
            {lastLog.body_fat_pct && <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 13, color: 'var(--muted)' }}>{lastLog.body_fat_pct}% BF</span>}
          </div>
        </div>
      )}

      <div className="two-col">
        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 14 }}>
            <label style={LABEL}>Week Number</label>
            <input type="number" value={weekNum} onChange={e => setWeekNum(parseInt(e.target.value))} min={1} max={32} style={INPUT} disabled={isUpdating} />
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={LABEL}>Weight (kg) *</label>
            <input type="number" step="0.1" value={weight} onChange={e => setWeight(e.target.value)} placeholder="e.g. 91.5" style={INPUT} required />
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={LABEL}>Waist (inches) *</label>
            <input type="number" step="0.5" value={waist} onChange={e => setWaist(e.target.value)} placeholder="e.g. 37.0" style={INPUT} required />
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={LABEL}>Chest (inches)</label>
            <input type="number" step="0.5" value={chest} onChange={e => setChest(e.target.value)} placeholder="optional" style={INPUT} />
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={LABEL}>Hips (inches)</label>
            <input type="number" step="0.5" value={hips} onChange={e => setHips(e.target.value)} placeholder="optional" style={INPUT} />
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={LABEL}>Body Fat %</label>
            <input type="number" step="0.1" value={bodyFat} onChange={e => setBodyFat(e.target.value)} placeholder="optional" style={INPUT} />
          </div>
          <div style={{ marginBottom: 20 }}>
            <label style={LABEL}>Notes</label>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="How's the week been?" rows={3}
              style={{ ...INPUT, resize: 'vertical', fontFamily: "'DM Sans', sans-serif" }} />
          </div>

          {error && (
            <div style={{ color: 'var(--accent2)', fontFamily: "'DM Mono', monospace", fontSize: 12, marginBottom: 12, padding: '8px 12px', background: 'rgba(255,107,53,0.05)', border: '1px solid rgba(255,107,53,0.15)' }}>
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} style={{
            background: 'var(--accent)', border: 'none', color: '#000',
            fontFamily: "'DM Mono', monospace", fontSize: 12, letterSpacing: 3,
            textTransform: 'uppercase', padding: '12px 28px', fontWeight: 'bold',
            opacity: loading ? 0.7 : 1, cursor: loading ? 'not-allowed' : 'pointer',
          }}>
            {loading ? 'Saving...' : isUpdating ? 'Update Check-In' : 'Save Check-In'}
          </button>

          {saved && (
            <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(232,255,71,0.05)', border: '1px solid rgba(232,255,71,0.15)', fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--accent)' }}>
              Week {saved.week_number} check-in saved.
            </div>
          )}
        </form>

        {/* Live derived metrics */}
        <div>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 14 }}>Live preview</div>

          {/* BMI */}
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '14px 18px', marginBottom: 10 }}>
            <div style={LABEL}>BMI</div>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 30, color: 'var(--text)' }}>{bmi || '—'}</div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: 'var(--muted)', marginTop: 2 }}>5'11" / 180.5 cm</div>
          </div>

          {/* Weight change */}
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '14px 18px', marginBottom: 10 }}>
            <div style={LABEL}>Change from start</div>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 30, color: changeFromStart !== null && changeFromStart < 0 ? 'var(--accent)' : changeFromStart !== null && changeFromStart > 0 ? 'var(--accent2)' : 'var(--text)' }}>
              {changeFromStart !== null ? `${changeFromStart > 0 ? '+' : ''}${changeFromStart} kg` : '—'}
            </div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: 'var(--muted)', marginTop: 2 }}>from {START_WEIGHT} kg start</div>
          </div>

          {/* Week-over-week */}
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '14px 18px', marginBottom: 10 }}>
            <div style={LABEL}>This week</div>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 30, color: changeFromLast !== null && changeFromLast < 0 ? 'var(--accent)' : changeFromLast !== null && changeFromLast > 0.2 ? 'var(--accent2)' : 'var(--text)' }}>
              {changeFromLast !== null ? `${changeFromLast > 0 ? '+' : ''}${changeFromLast} kg` : '—'}
            </div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: 'var(--muted)', marginTop: 2 }}>vs prev: {prevWeight ?? START_WEIGHT} kg</div>
            {trend && (
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: trend.color, marginTop: 6, lineHeight: 1.5 }}>
                {trend.text}
              </div>
            )}
          </div>

          {/* Waist change */}
          {waist && (
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '14px 18px', marginBottom: 10 }}>
              <div style={LABEL}>Waist from start</div>
              <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 30, color: waistChangeFromStart < 0 ? 'var(--accent)' : waistChangeFromStart > 0 ? 'var(--accent2)' : 'var(--text)' }}>
                {`${waistChangeFromStart > 0 ? '+' : ''}${waistChangeFromStart}"`}
              </div>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: 'var(--muted)', marginTop: 2 }}>target: {TARGET_WAIST}"</div>
            </div>
          )}

          {/* Progress toward goal */}
          {weightProgress !== null && (
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '14px 18px', marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={LABEL}>Goal progress</span>
                <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--accent)' }}>{Math.max(0, weightProgress)}%</span>
              </div>
              <div style={{ background: 'var(--surface2)', height: 5, borderRadius: 3, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${Math.max(0, Math.min(100, weightProgress))}%`, background: 'var(--accent)', transition: 'width 0.4s' }} />
              </div>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: 'var(--muted)', marginTop: 4 }}>{TARGET_WEIGHT} kg target</div>
            </div>
          )}
        </div>
      </div>

      {/* History */}
      {!loadingHistory && history.length === 0 && (
        <div style={{ marginTop: 40, paddingTop: 24, borderTop: '1px solid var(--border)', fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)' }}>
          No weekly check-ins yet. Log your first to start tracking body recomposition.
        </div>
      )}

      {history.length > 0 && (
        <div style={{ marginTop: 48 }}>
          <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, letterSpacing: 1, marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid var(--border)' }}>
            Log History
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>
              <thead>
                <tr>
                  {['Wk', 'Date', 'Weight', 'Waist', 'BMI', 'vs Start', 'vs Prev'].map(h => (
                    <th key={h} style={{ padding: '7px 10px', borderBottom: '1px solid var(--border)', color: 'var(--muted)', fontWeight: 400, textAlign: 'left', letterSpacing: 1, fontSize: 10 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[...history].reverse().map(row => (
                  <tr key={row.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '8px 10px', color: 'var(--accent)' }}>W{row.week_number}</td>
                    <td style={{ padding: '8px 10px', color: 'var(--muted)' }}>{row.log_date}</td>
                    <td style={{ padding: '8px 10px', color: 'var(--text)' }}>{row.weight_kg} kg</td>
                    <td style={{ padding: '8px 10px', color: 'var(--text)' }}>{row.waist_inches}"</td>
                    <td style={{ padding: '8px 10px', color: 'var(--muted)' }}>{row.bmi}</td>
                    <td style={{ padding: '8px 10px', color: row.weight_change_from_start < 0 ? 'var(--accent)' : 'var(--accent2)' }}>
                      {row.weight_change_from_start > 0 ? '+' : ''}{row.weight_change_from_start} kg
                    </td>
                    <td style={{ padding: '8px 10px', color: row.weight_change_from_last_week < 0 ? 'var(--accent)' : row.weight_change_from_last_week > 0.2 ? 'var(--accent2)' : 'var(--muted)' }}>
                      {row.weight_change_from_last_week > 0 ? '+' : ''}{row.weight_change_from_last_week} kg
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
