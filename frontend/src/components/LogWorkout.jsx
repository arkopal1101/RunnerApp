// Log a strength / workout session. Uploads a screenshot (no OCR parsing in
// v1 — just stored as-is) + optional notes. Marks the day as completed.
import { useState, useRef, useCallback } from 'react'
import { apiUrl } from '../utils/api'
import { getCurrentWeek, getTodayInfo } from '../utils/planData'

export default function LogWorkout({ token, onDone }) {
  const { week, dayOfWeek } = getTodayInfo()
  const [image, setImage] = useState(null)
  const [preview, setPreview] = useState(null)
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const fileRef = useRef(null)
  const [targetWeek, setTargetWeek] = useState(week)
  const [targetDow, setTargetDow] = useState(dayOfWeek)

  const handleFile = useCallback(file => {
    if (!file || !file.type.startsWith('image/')) {
      setError('Please select an image file (PNG or JPG).')
      return
    }
    setError('')
    setImage(file)
    setPreview(URL.createObjectURL(file))
  }, [])

  async function handleSave() {
    if (!image) {
      setError('Upload a workout screenshot first.')
      return
    }
    setSaving(true)
    setError('')
    try {
      const fd = new FormData()
      fd.append('image', image)
      fd.append('notes', notes || '')
      fd.append('week_number', String(targetWeek))
      fd.append('day_of_week', String(targetDow))
      const res = await fetch(apiUrl('/api/day-log/workout'), {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      })
      if (!res.ok) throw new Error('Save failed')
      setSaved(true)
      onDone?.()
    } catch {
      setError('Save failed. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (saved) {
    return (
      <div className="page-pad">
        <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1, marginBottom: 4 }}>Workout Logged</div>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 24 }}>
          Week {targetWeek} · day {targetDow} marked complete
        </div>
        <button onClick={() => { setImage(null); setPreview(null); setNotes(''); setSaved(false) }}
          style={{ background: 'var(--accent)', border: 'none', color: '#000', fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, textTransform: 'uppercase', padding: '10px 20px', cursor: 'pointer', fontWeight: 'bold' }}>
          Log Another
        </button>
      </div>
    )
  }

  return (
    <div className="page-pad">
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1, marginBottom: 4 }}>Log Workout</div>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 24 }}>
        Strength session — upload a screenshot
      </div>

      <div
        onDragOver={e => e.preventDefault()}
        onDrop={e => { e.preventDefault(); handleFile(e.dataTransfer.files[0]) }}
        onClick={() => fileRef.current?.click()}
        style={{
          border: `2px dashed ${image ? 'var(--accent)' : 'var(--border)'}`,
          background: 'var(--surface)',
          padding: '40px 24px',
          textAlign: 'center',
          cursor: 'pointer',
          marginBottom: 16,
        }}
      >
        <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }}
          onChange={e => handleFile(e.target.files[0])} />
        {preview ? (
          <img src={preview} alt="workout preview" style={{ maxHeight: 300, maxWidth: '100%', objectFit: 'contain' }} />
        ) : (
          <>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, color: 'var(--muted)', marginBottom: 8 }}>
              Drop screenshot or click
            </div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)' }}>
              PNG or JPG — whatever you took during / after the session
            </div>
          </>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
        <div>
          <label style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', display: 'block', marginBottom: 5 }}>
            Week
          </label>
          <input type="number" min="1" max="32" value={targetWeek}
            onChange={e => setTargetWeek(parseInt(e.target.value || '1'))}
            style={{ width: '100%', background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--text)', fontFamily: "'DM Mono', monospace", fontSize: 13, padding: '9px 12px', outline: 'none', boxSizing: 'border-box' }} />
        </div>
        <div>
          <label style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', display: 'block', marginBottom: 5 }}>
            Day (0=Mon, 6=Sun)
          </label>
          <input type="number" min="0" max="6" value={targetDow}
            onChange={e => setTargetDow(parseInt(e.target.value || '0'))}
            style={{ width: '100%', background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--text)', fontFamily: "'DM Mono', monospace", fontSize: 13, padding: '9px 12px', outline: 'none', boxSizing: 'border-box' }} />
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <label style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', display: 'block', marginBottom: 5 }}>
          Notes (optional)
        </label>
        <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={3}
          placeholder="How did it go? PRs, niggles, energy, etc."
          style={{ width: '100%', background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--text)', fontFamily: "'DM Sans', sans-serif", fontSize: 13, padding: '10px 12px', outline: 'none', boxSizing: 'border-box', resize: 'vertical' }} />
      </div>

      {error && (
        <div style={{ color: 'var(--accent2)', fontFamily: "'DM Mono', monospace", fontSize: 12, marginBottom: 12, padding: '8px 12px', background: 'rgba(255,107,53,0.05)', border: '1px solid rgba(255,107,53,0.15)' }}>
          {error}
        </div>
      )}

      <button onClick={handleSave} disabled={saving}
        style={{ background: 'var(--accent)', border: 'none', color: '#000', fontFamily: "'DM Mono', monospace", fontSize: 12, letterSpacing: 3, textTransform: 'uppercase', padding: '12px 28px', fontWeight: 'bold', cursor: saving ? 'not-allowed' : 'pointer', opacity: saving ? 0.7 : 1 }}>
        {saving ? 'Saving…' : 'Save Workout'}
      </button>
    </div>
  )
}
