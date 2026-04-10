import { useState, useEffect } from 'react'

const START_DATE = new Date('2026-04-14')
const START_WEIGHT = 94
const HEIGHT_CM = 180.5

function getCurrentWeek() {
  const now = new Date()
  const diffDays = Math.floor((now - START_DATE) / (1000 * 60 * 60 * 24))
  if (diffDays < 0) return 1
  return Math.floor(diffDays / 7) + 1
}

function calcBMI(weightKg) {
  return (weightKg / Math.pow(HEIGHT_CM / 100, 2)).toFixed(1)
}

const inputStyle = {
  background: 'var(--surface)',
  border: '1px solid var(--border)',
  color: 'var(--text)',
  fontFamily: "'DM Mono', monospace",
  fontSize: 13,
  padding: '10px 14px',
  width: '100%',
  outline: 'none',
}

const labelStyle = {
  fontFamily: "'DM Mono', monospace",
  fontSize: 10,
  letterSpacing: 2,
  color: 'var(--muted)',
  textTransform: 'uppercase',
  marginBottom: 6,
  display: 'block',
}

export default function WeeklyLog({ token }) {
  const [weight, setWeight] = useState('')
  const [waist, setWaist] = useState('')
  const [chest, setChest] = useState('')
  const [hips, setHips] = useState('')
  const [bodyFat, setBodyFat] = useState('')
  const [notes, setNotes] = useState('')
  const [weekNum, setWeekNum] = useState(getCurrentWeek())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(null)
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(true)

  useEffect(() => {
    fetch('/api/log/weekly', { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(data => { setHistory(data); setLoadingHistory(false) })
      .catch(() => setLoadingHistory(false))
  }, [token])

  const weightNum = parseFloat(weight)
  const prevWeight = history.length > 0 ? history[history.length - 1].weight_kg : START_WEIGHT
  const bmi = weight ? calcBMI(weightNum) : null
  const changeFromStart = weight ? (weightNum - START_WEIGHT).toFixed(1) : null
  const changeFromLast = weight ? (weightNum - prevWeight).toFixed(1) : null

  async function handleSubmit(e) {
    e.preventDefault()
    if (!weight || !waist) { setError('Weight and waist are required.'); return }
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/log/weekly', {
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
      if (!res.ok) throw new Error('Save failed')
      const data = await res.json()
      setSaved(data)
      setHistory(prev => [...prev, data])
      // Reset form
      setWeight(''); setWaist(''); setChest(''); setHips(''); setBodyFat(''); setNotes('')
    } catch {
      setError('Save failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-pad">
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1, marginBottom: 8 }}>WEEKLY CHECK-IN</div>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 32 }}>
        Body measurements · Week {weekNum}
      </div>

      <div className="two-col">
        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Week Number</label>
            <input type="number" value={weekNum} onChange={e => setWeekNum(parseInt(e.target.value))} min={1} max={32} style={inputStyle} />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Weight (kg) *</label>
            <input type="number" step="0.1" value={weight} onChange={e => setWeight(e.target.value)} placeholder="e.g. 91.5" style={inputStyle} required />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Waist (inches) *</label>
            <input type="number" step="0.5" value={waist} onChange={e => setWaist(e.target.value)} placeholder="e.g. 37.0" style={inputStyle} required />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Chest (inches)</label>
            <input type="number" step="0.5" value={chest} onChange={e => setChest(e.target.value)} placeholder="optional" style={inputStyle} />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Hips (inches)</label>
            <input type="number" step="0.5" value={hips} onChange={e => setHips(e.target.value)} placeholder="optional" style={inputStyle} />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Body Fat %</label>
            <input type="number" step="0.1" value={bodyFat} onChange={e => setBodyFat(e.target.value)} placeholder="optional" style={inputStyle} />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={labelStyle}>Notes</label>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="How's the week been?" rows={3}
              style={{ ...inputStyle, resize: 'vertical', fontFamily: "'DM Sans', sans-serif" }} />
          </div>

          {error && <div style={{ color: 'var(--accent2)', fontFamily: "'DM Mono', monospace", fontSize: 12, marginBottom: 12 }}>{error}</div>}

          <button type="submit" disabled={loading} style={{
            background: 'var(--accent)',
            border: 'none',
            color: '#000',
            fontFamily: "'DM Mono', monospace",
            fontSize: 12,
            letterSpacing: 3,
            textTransform: 'uppercase',
            padding: '12px 28px',
            fontWeight: 'bold',
            opacity: loading ? 0.7 : 1,
          }}>
            {loading ? 'SAVING...' : 'SAVE LOG'}
          </button>

          {saved && (
            <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(232,255,71,0.05)', border: '1px solid rgba(232,255,71,0.15)', fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--accent)' }}>
              ✓ Week {saved.week_number} logged
            </div>
          )}
        </form>

        {/* Live derived metrics */}
        <div>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 16 }}>Auto-computed</div>

          {[
            ['BMI', bmi ? `${bmi}` : '—', `(5'11" / 180.5cm)`],
            ['Change from Start', changeFromStart ? `${changeFromStart > 0 ? '+' : ''}${changeFromStart} kg` : '—', `from ${START_WEIGHT} kg`],
            ['Change from Last Week', changeFromLast ? `${changeFromLast > 0 ? '+' : ''}${changeFromLast} kg` : '—', `prev: ${prevWeight} kg`],
          ].map(([label, val, sub]) => (
            <div key={label} style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '16px 20px', marginBottom: 12 }}>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 4 }}>{label}</div>
              <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 32, color: val !== '—' && parseFloat(val) < 0 ? 'var(--accent)' : val !== '—' && parseFloat(val) > 0 && label.includes('Change') ? 'var(--accent2)' : 'var(--text)' }}>{val}</div>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: 'var(--muted)', marginTop: 2 }}>{sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* History */}
      {history.length > 0 && (
        <div style={{ marginTop: 48 }}>
          <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 24, letterSpacing: 1, marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid var(--border)' }}>
            LOG HISTORY
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>
              <thead>
                <tr>
                  {['Wk', 'Date', 'Weight', 'Waist', 'BMI', 'Δ Start', 'Δ Prev'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', color: 'var(--muted)', fontWeight: 400, textAlign: 'left', letterSpacing: 1 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[...history].reverse().map((row, i) => (
                  <tr key={row.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '8px 12px', color: 'var(--accent)' }}>W{row.week_number}</td>
                    <td style={{ padding: '8px 12px', color: 'var(--muted)' }}>{row.log_date}</td>
                    <td style={{ padding: '8px 12px', color: 'var(--text)' }}>{row.weight_kg} kg</td>
                    <td style={{ padding: '8px 12px', color: 'var(--text)' }}>{row.waist_inches}"</td>
                    <td style={{ padding: '8px 12px', color: 'var(--muted)' }}>{row.bmi}</td>
                    <td style={{ padding: '8px 12px', color: row.weight_change_from_start < 0 ? 'var(--accent)' : 'var(--accent2)' }}>
                      {row.weight_change_from_start > 0 ? '+' : ''}{row.weight_change_from_start} kg
                    </td>
                    <td style={{ padding: '8px 12px', color: row.weight_change_from_last_week < 0 ? 'var(--accent)' : 'var(--accent2)' }}>
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
