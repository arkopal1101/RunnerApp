import { useState, useRef, useCallback, useEffect } from 'react'
import { apiUrl } from '../utils/api'

const INPUT = {
  background: 'var(--surface2)',
  border: '1px solid var(--border)',
  color: 'var(--text)',
  fontFamily: "'DM Mono', monospace",
  fontSize: 13,
  padding: '9px 12px',
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

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={LABEL}>{label}</label>
      {children}
    </div>
  )
}

function ConfidenceBadge({ confidence }) {
  const map = {
    ocr:    { label: 'High confidence',             color: 'var(--accent3)' },
    llm:    { label: 'AI parsed — review values',   color: 'var(--phase2)' },
    failed: { label: 'Manual correction needed',    color: 'var(--accent2)' },
    manual: { label: 'Manual entry',                color: 'var(--muted)' },
  }
  const { label, color } = map[confidence] || map.failed
  return (
    <span style={{
      fontFamily: "'DM Mono', monospace",
      fontSize: 10,
      letterSpacing: 2,
      padding: '3px 9px',
      border: `1px solid ${color}`,
      color,
      textTransform: 'uppercase',
    }}>
      {label}
    </span>
  )
}

/* ── History row ── */
function HistoryRow({ entry }) {
  return (
    <tr style={{ borderBottom: '1px solid var(--border)' }}>
      <td style={{ padding: '8px 10px', color: 'var(--accent)', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>W{entry.week_number}</td>
      <td style={{ padding: '8px 10px', color: 'var(--muted)', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>{entry.checkin_date}</td>
      <td style={{ padding: '8px 10px', color: 'var(--text)', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>{entry.total_distance_km ? `${entry.total_distance_km} km` : '—'}</td>
      <td style={{ padding: '8px 10px', color: 'var(--text)', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>{entry.avg_pace_per_km || '—'}</td>
      <td style={{ padding: '8px 10px', color: 'var(--muted)', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>{entry.avg_hr_bpm ? `${entry.avg_hr_bpm}` : '—'}</td>
    </tr>
  )
}

/* ── Step 1: Upload or Manual choice ── */
function StepUpload({ onParsed, onManual }) {
  const [dragging, setDragging] = useState(false)
  const [parsing, setParsing] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef(null)

  const processFile = useCallback(async (file) => {
    if (!file || !file.type.startsWith('image/')) {
      setError('Please select an image file (PNG or JPG).')
      return
    }
    setParsing(true)
    setError('')
    try {
      const form = new FormData()
      form.append('image', file)
      const res = await fetch(apiUrl('/api/checkin/parse'), {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('runner_token')}` },
        body: form,
      })
      if (!res.ok) throw new Error('Parse failed')
      const data = await res.json()
      onParsed(data, URL.createObjectURL(file))
    } catch {
      setError('Could not parse the screenshot. You can enter the data manually.')
    } finally {
      setParsing(false)
    }
  }, [onParsed])

  return (
    <div>
      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => { e.preventDefault(); setDragging(false); processFile(e.dataTransfer.files[0]) }}
        onClick={() => fileRef.current?.click()}
        style={{
          border: `2px dashed ${dragging ? 'var(--accent)' : 'var(--border)'}`,
          background: dragging ? 'rgba(232,255,71,0.03)' : 'var(--surface)',
          padding: '40px 24px',
          textAlign: 'center',
          cursor: 'pointer',
          marginBottom: 16,
          transition: 'all 0.2s',
        }}
      >
        <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }}
          onChange={e => processFile(e.target.files[0])} />
        {parsing ? (
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 13, color: 'var(--muted)' }}>
            Parsing screenshot...
          </div>
        ) : (
          <>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, color: 'var(--muted)', marginBottom: 6 }}>
              Drop Apple Health Screenshot Here
            </div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)', letterSpacing: 1 }}>
              or click to browse · PNG / JPG
            </div>
          </>
        )}
      </div>

      {error && (
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--accent2)', marginBottom: 12, padding: '10px 14px', background: 'rgba(255,107,53,0.05)', border: '1px solid rgba(255,107,53,0.15)' }}>
          {error}
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)', letterSpacing: 1 }}>or</span>
        <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
      </div>

      <button
        onClick={onManual}
        style={{
          width: '100%',
          marginTop: 12,
          background: 'none',
          border: '1px solid var(--border)',
          color: 'var(--muted)',
          fontFamily: "'DM Mono', monospace",
          fontSize: 12,
          letterSpacing: 2,
          textTransform: 'uppercase',
          padding: '12px',
          cursor: 'pointer',
          transition: 'all 0.15s',
        }}
        onMouseEnter={e => { e.target.style.borderColor = 'var(--accent)'; e.target.style.color = 'var(--accent)' }}
        onMouseLeave={e => { e.target.style.borderColor = 'var(--border)'; e.target.style.color = 'var(--muted)' }}
      >
        Enter Run Manually
      </button>
    </div>
  )
}

/* ── Step 2: Review & edit parsed/manual data ── */
function StepReview({ parsed, imagePreview, isManual, onConfirm, onBack }) {
  const today = new Date().toISOString().split('T')[0]

  const [form, setForm] = useState({
    checkin_date: today,
    total_distance_km: parsed?.total_distance_km ?? '',
    avg_pace_per_km: parsed?.avg_pace_per_km ?? '',
    avg_hr_bpm: parsed?.avg_hr_bpm ?? '',
    max_hr_bpm: parsed?.max_hr_bpm ?? '',
    avg_power_watts: parsed?.avg_power_watts ?? '',
    notes: '',
  })
  const [splits, setSplits] = useState(parsed?.splits || [])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  function set(key, val) {
    setForm(f => ({ ...f, [key]: val }))
  }

  function updateSplit(idx, field, val) {
    setSplits(prev => prev.map((s, i) => i === idx ? { ...s, [field]: val } : s))
  }

  async function handleConfirm() {
    if (!form.total_distance_km && !form.avg_pace_per_km) {
      setError('Enter at least a distance or pace to save.')
      return
    }
    setSaving(true)
    setError('')
    try {
      const overrideData = {
        checkin_date: form.checkin_date,
        total_distance_km: form.total_distance_km ? parseFloat(form.total_distance_km) : null,
        avg_pace_per_km: form.avg_pace_per_km || null,
        avg_hr_bpm: form.avg_hr_bpm ? parseInt(form.avg_hr_bpm) : null,
        max_hr_bpm: form.max_hr_bpm ? parseInt(form.max_hr_bpm) : null,
        avg_power_watts: form.avg_power_watts ? parseInt(form.avg_power_watts) : null,
        splits,
        notes: form.notes || null,
        ...(parsed?.tmp_image_path ? { tmp_image_path: parsed.tmp_image_path } : {}),
      }

      const fd = new FormData()
      fd.append('checkin_date', form.checkin_date)
      fd.append('notes', form.notes || '')
      fd.append('override_json', JSON.stringify(overrideData))

      const res = await fetch(apiUrl('/api/checkin/daily'), {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('runner_token')}` },
        body: fd,
      })
      if (!res.ok) throw new Error('Save failed')
      const saved = await res.json()
      onConfirm(saved)
    } catch {
      setError('Save failed. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, letterSpacing: 1 }}>
          {isManual ? 'Enter Run Details' : 'Review Parsed Data'}
        </div>
        {!isManual && parsed?.confidence && <ConfidenceBadge confidence={parsed.confidence} />}
      </div>

      {imagePreview && (
        <img src={imagePreview} alt="screenshot" style={{ maxHeight: 180, maxWidth: '100%', objectFit: 'contain', marginBottom: 16, border: '1px solid var(--border)' }} />
      )}

      {/* Core fields */}
      <div className="two-col" style={{ marginBottom: 0 }}>
        <Field label="Date">
          <input type="date" value={form.checkin_date} onChange={e => set('checkin_date', e.target.value)} style={INPUT} />
        </Field>
        <Field label="Distance (km)">
          <input type="number" step="0.01" value={form.total_distance_km} onChange={e => set('total_distance_km', e.target.value)} placeholder="e.g. 7.2" style={INPUT} />
        </Field>
        <Field label="Avg Pace (mm:ss /km)">
          <input type="text" value={form.avg_pace_per_km} onChange={e => set('avg_pace_per_km', e.target.value)} placeholder="e.g. 8:45" style={INPUT} />
        </Field>
        <Field label="Avg HR (bpm)">
          <input type="number" value={form.avg_hr_bpm} onChange={e => set('avg_hr_bpm', e.target.value)} placeholder="e.g. 138" style={INPUT} />
        </Field>
        <Field label="Max HR (bpm)">
          <input type="number" value={form.max_hr_bpm} onChange={e => set('max_hr_bpm', e.target.value)} placeholder="e.g. 152" style={INPUT} />
        </Field>
        <Field label="Avg Power (W)">
          <input type="number" value={form.avg_power_watts} onChange={e => set('avg_power_watts', e.target.value)} placeholder="e.g. 185" style={INPUT} />
        </Field>
      </div>

      <Field label="Notes">
        <textarea value={form.notes} onChange={e => set('notes', e.target.value)}
          placeholder="How did the run feel?" rows={2}
          style={{ ...INPUT, fontFamily: "'DM Sans', sans-serif", resize: 'vertical' }} />
      </Field>

      {/* Splits */}
      {splits.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 10 }}>
            Splits — click to edit
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>
              <thead>
                <tr>
                  {['KM', 'Time', 'Pace /km', 'HR bpm', 'Power W'].map(h => (
                    <th key={h} style={{ padding: '6px 10px', borderBottom: '1px solid var(--border)', color: 'var(--muted)', fontWeight: 400, textAlign: 'left', letterSpacing: 1, fontSize: 10 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {splits.map((s, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '4px 10px', color: 'var(--muted)' }}>{s.km}</td>
                    {['time', 'pace_per_km', 'hr_bpm', 'power_watts'].map(f => (
                      <td key={f} style={{ padding: '3px 6px' }}>
                        <input value={s[f] ?? ''} onChange={e => updateSplit(i, f, e.target.value)}
                          style={{ ...INPUT, padding: '4px 6px', fontSize: 12 }} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {error && (
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--accent2)', marginBottom: 12, padding: '10px 14px', background: 'rgba(255,107,53,0.05)', border: '1px solid rgba(255,107,53,0.15)' }}>
          {error}
        </div>
      )}

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 8 }}>
        <button onClick={handleConfirm} disabled={saving} style={{
          background: 'var(--accent)', border: 'none', color: '#000',
          fontFamily: "'DM Mono', monospace", fontSize: 12, letterSpacing: 3,
          textTransform: 'uppercase', padding: '12px 28px', fontWeight: 'bold',
          cursor: saving ? 'not-allowed' : 'pointer', opacity: saving ? 0.7 : 1,
        }}>
          {saving ? 'Saving...' : 'Confirm & Save'}
        </button>
        <button onClick={onBack} style={{
          background: 'none', border: '1px solid var(--border)', color: 'var(--muted)',
          fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2,
          textTransform: 'uppercase', padding: '12px 20px', cursor: 'pointer',
        }}>
          Back
        </button>
      </div>
    </div>
  )
}

/* ── Step 3: Success ── */
function StepSuccess({ saved, onAnother }) {
  const [coachNote, setCoachNote] = useState(null)
  const [loadingNote, setLoadingNote] = useState(true)

  useEffect(() => {
    if (!saved?.id) return
    setLoadingNote(true)
    fetch(apiUrl(`/api/coach/post-run/${saved.id}`), {
      headers: { Authorization: `Bearer ${localStorage.getItem('runner_token')}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(d => { setCoachNote(d); setLoadingNote(false) })
      .catch(() => setLoadingNote(false))
  }, [saved?.id])

  const metrics = coachNote?.metrics || {}
  const paceVerdictColor = {
    ahead_of_target: 'var(--accent)',
    on_target: 'var(--accent3)',
    slightly_behind: 'var(--phase2)',
    behind: 'var(--accent2)',
    unknown: 'var(--muted)',
  }[metrics.pace_verdict] || 'var(--muted)'

  return (
    <div>
      <div style={{ padding: '20px 24px', background: 'rgba(232,255,71,0.05)', border: '1px solid rgba(232,255,71,0.15)', marginBottom: 24 }}>
        <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, color: 'var(--accent)', marginBottom: 6 }}>
          Run Saved
        </div>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)' }}>
          Week {saved.week_number} · {saved.checkin_date}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10, marginBottom: 24 }}>
        {[
          ['Distance', saved.total_distance_km ? `${saved.total_distance_km} km` : '—'],
          ['Avg Pace', saved.avg_pace_per_km || '—'],
          ['Avg HR', saved.avg_hr_bpm ? `${saved.avg_hr_bpm} bpm` : '—'],
          ['Max HR', saved.max_hr_bpm ? `${saved.max_hr_bpm} bpm` : '—'],
        ].map(([label, val]) => (
          <div key={label} style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '12px 14px' }}>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 3 }}>{label}</div>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, color: 'var(--accent)' }}>{val}</div>
          </div>
        ))}
      </div>

      {/* Post-run coach summary */}
      {(coachNote || loadingNote) && (
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderLeft: `3px solid ${paceVerdictColor}`,
          padding: '16px 20px',
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: paceVerdictColor, textTransform: 'uppercase' }}>
              Coach Summary
            </span>
            {coachNote?.model && coachNote.model !== 'rules' && (
              <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 9, color: 'var(--muted)' }}>{coachNote.model}</span>
            )}
          </div>
          {loadingNote ? (
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)' }}>
              Analyzing workout…
            </div>
          ) : coachNote ? (
            <>
              {/* Offset quick-read row */}
              {(metrics.pace_offset_sec !== null && metrics.pace_offset_sec !== undefined) && (
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 10, fontFamily: "'DM Mono', monospace", fontSize: 11 }}>
                  <span>
                    <span style={{ color: 'var(--muted)' }}>Pace offset: </span>
                    <span style={{ color: paceVerdictColor, fontWeight: 600 }}>
                      {metrics.pace_offset_sec > 0 ? '+' : ''}{metrics.pace_offset_sec}s/km
                    </span>
                  </span>
                  {metrics.target_pace && (
                    <span>
                      <span style={{ color: 'var(--muted)' }}>Target: </span>
                      <span style={{ color: 'var(--text)' }}>{metrics.target_pace}</span>
                    </span>
                  )}
                  {metrics.distance_offset !== null && metrics.distance_offset !== undefined && (
                    <span>
                      <span style={{ color: 'var(--muted)' }}>Distance: </span>
                      <span style={{ color: 'var(--text)' }}>
                        {metrics.distance_offset > 0 ? '+' : ''}{metrics.distance_offset} km
                      </span>
                    </span>
                  )}
                </div>
              )}
              <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.6 }}>{coachNote.text}</div>
            </>
          ) : null}
        </div>
      )}

      <button onClick={onAnother} style={{
        background: 'none', border: '1px solid var(--border)', color: 'var(--muted)',
        fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2,
        textTransform: 'uppercase', padding: '10px 20px', cursor: 'pointer',
      }}>
        Log Another Run
      </button>
    </div>
  )
}

/* ── Main component ── */
export default function LogRun({ token }) {
  // step: 'upload' | 'review' | 'success'
  const [step, setStep] = useState('upload')
  const [parsed, setParsed] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [isManual, setIsManual] = useState(false)
  const [saved, setSaved] = useState(null)
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(true)

  useEffect(() => {
    fetch(apiUrl('/api/checkin/daily'), { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => { setHistory(d); setLoadingHistory(false) })
      .catch(() => setLoadingHistory(false))
  }, [token])

  function handleParsed(data, preview) {
    setParsed(data)
    setImagePreview(preview)
    setIsManual(false)
    setStep('review')
  }

  function handleManual() {
    setParsed(null)
    setImagePreview(null)
    setIsManual(true)
    setStep('review')
  }

  function handleConfirmed(savedEntry) {
    setSaved(savedEntry)
    setHistory(prev => [savedEntry, ...prev])
    setStep('success')
  }

  function handleAnother() {
    setParsed(null)
    setImagePreview(null)
    setIsManual(false)
    setSaved(null)
    setStep('upload')
  }

  return (
    <div className="page-pad">
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1, marginBottom: 4 }}>Log Run</div>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 32 }}>
        {step === 'upload' && 'Upload screenshot or enter manually'}
        {step === 'review' && 'Review and confirm before saving'}
        {step === 'success' && 'Run saved successfully'}
      </div>

      {/* Step indicator */}
      {step !== 'success' && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 28 }}>
          {[['1', 'Upload'], ['2', 'Review'], ['3', 'Saved']].map(([num, label], i) => {
            const stepIdx = step === 'upload' ? 0 : step === 'review' ? 1 : 2
            const active = stepIdx === i
            const done = stepIdx > i
            return (
              <div key={num} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{
                  width: 22, height: 22,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: done ? 'var(--accent)' : active ? 'var(--surface2)' : 'transparent',
                  border: `1px solid ${done || active ? 'var(--accent)' : 'var(--border)'}`,
                  color: done ? '#000' : active ? 'var(--accent)' : 'var(--muted)',
                  fontFamily: "'DM Mono', monospace", fontSize: 11,
                }}>
                  {done ? '✓' : num}
                </span>
                <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: active ? 'var(--text)' : 'var(--muted)', letterSpacing: 1 }}>{label}</span>
                {i < 2 && <span style={{ color: 'var(--border)', marginLeft: 4 }}>—</span>}
              </div>
            )
          })}
        </div>
      )}

      {/* Step content */}
      {step === 'upload' && <StepUpload onParsed={handleParsed} onManual={handleManual} />}
      {step === 'review' && (
        <StepReview
          parsed={parsed}
          imagePreview={imagePreview}
          isManual={isManual}
          onConfirm={handleConfirmed}
          onBack={() => setStep('upload')}
        />
      )}
      {step === 'success' && <StepSuccess saved={saved} onAnother={handleAnother} />}

      {/* Run history */}
      {history.length > 0 && (
        <div style={{ marginTop: 48, paddingTop: 32, borderTop: '1px solid var(--border)' }}>
          <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, letterSpacing: 1, marginBottom: 16 }}>
            Run History
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Wk', 'Date', 'Distance', 'Pace', 'HR'].map(h => (
                    <th key={h} style={{ padding: '7px 10px', borderBottom: '1px solid var(--border)', color: 'var(--muted)', fontWeight: 400, textAlign: 'left', fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 1, textTransform: 'uppercase' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.map(e => <HistoryRow key={e.id} entry={e} />)}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loadingHistory && history.length === 0 && step !== 'success' && (
        <div style={{ marginTop: 48, paddingTop: 32, borderTop: '1px solid var(--border)', fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)' }}>
          No runs logged yet. Log your first run to start tracking progress.
        </div>
      )}
    </div>
  )
}
