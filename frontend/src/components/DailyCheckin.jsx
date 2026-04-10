import { useState, useRef, useCallback } from 'react'

export default function DailyCheckin({ token }) {
  const [dragging, setDragging] = useState(false)
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [notes, setNotes] = useState('')
  const [editedSplits, setEditedSplits] = useState([])
  const [saved, setSaved] = useState(false)
  const fileInputRef = useRef(null)

  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith('image/')) return
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
    setResult(null)
    setSaved(false)
    setError('')
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }, [handleFile])

  async function handleUpload() {
    if (!imageFile) return
    setLoading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('image', imageFile)
      formData.append('notes', notes)
      const res = await fetch('/api/checkin/daily', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })
      if (!res.ok) throw new Error('Upload failed')
      const data = await res.json()
      setResult(data)
      setEditedSplits(data.splits || [])
      setSaved(true)
    } catch (e) {
      setError('Upload failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  function updateSplit(idx, field, value) {
    setEditedSplits(prev => prev.map((s, i) => i === idx ? { ...s, [field]: value } : s))
  }

  const inputStyle = {
    background: 'var(--surface2)',
    border: '1px solid var(--border)',
    color: 'var(--text)',
    fontFamily: "'DM Mono', monospace",
    fontSize: 12,
    padding: '4px 8px',
    width: '100%',
    outline: 'none',
  }

  return (
    <div className="page-pad">
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1, marginBottom: 8 }}>DAILY CHECK-IN</div>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 32 }}>
        Upload your Apple Health workout screenshot
      </div>

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragging ? 'var(--accent)' : 'var(--border)'}`,
          background: dragging ? 'rgba(232,255,71,0.03)' : 'var(--surface)',
          padding: 40,
          textAlign: 'center',
          cursor: 'pointer',
          marginBottom: 24,
          transition: 'all 0.2s',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={e => handleFile(e.target.files[0])}
        />
        {imagePreview ? (
          <img src={imagePreview} alt="preview" style={{ maxHeight: 300, maxWidth: '100%', objectFit: 'contain' }} />
        ) : (
          <>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 24, color: 'var(--muted)', marginBottom: 8 }}>
              DROP SCREENSHOT HERE
            </div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--muted)', letterSpacing: 2 }}>
              or click to browse · PNG / JPG
            </div>
          </>
        )}
      </div>

      {/* Notes */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 6 }}>Notes (optional)</div>
        <input
          type="text"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="How did the run feel?"
          style={{ ...inputStyle, width: '100%', padding: '10px 14px' }}
        />
      </div>

      {/* Upload button */}
      {imageFile && !saved && (
        <button
          onClick={handleUpload}
          disabled={loading}
          style={{
            background: 'var(--accent)',
            border: 'none',
            color: '#000',
            fontFamily: "'DM Mono', monospace",
            fontSize: 12,
            letterSpacing: 3,
            textTransform: 'uppercase',
            padding: '12px 28px',
            fontWeight: 'bold',
            marginBottom: 24,
            opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? 'PARSING...' : 'UPLOAD & PARSE'}
        </button>
      )}

      {error && (
        <div style={{ color: 'var(--accent2)', fontFamily: "'DM Mono', monospace", fontSize: 12, marginBottom: 16 }}>{error}</div>
      )}

      {/* Results */}
      {result && (
        <div>
          {/* Confidence badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, letterSpacing: 1 }}>PARSED RESULTS</div>
            <div style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 10,
              letterSpacing: 2,
              padding: '3px 8px',
              background: 'var(--surface2)',
              border: `1px solid ${result.confidence === 'ocr' ? 'var(--accent3)' : result.confidence === 'llm' ? 'var(--phase2)' : 'var(--accent2)'}`,
              color: result.confidence === 'ocr' ? 'var(--accent3)' : result.confidence === 'llm' ? 'var(--phase2)' : 'var(--accent2)',
              textTransform: 'uppercase',
            }}>
              {result.confidence === 'ocr' ? 'OCR parsed' : result.confidence === 'llm' ? 'Gemini parsed' : 'Manual required'}
            </div>
          </div>

          {/* Summary metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 24 }}>
            {[
              ['Week', result.week_number ? `W${result.week_number}` : '—'],
              ['Distance', result.total_distance_km ? `${result.total_distance_km} km` : '—'],
              ['Avg Pace', result.avg_pace_per_km || '—'],
              ['Avg HR', result.avg_hr_bpm ? `${result.avg_hr_bpm} bpm` : '—'],
              ['Max HR', result.max_hr_bpm ? `${result.max_hr_bpm} bpm` : '—'],
            ].map(([label, val]) => (
              <div key={label} style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '14px 16px' }}>
                <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 4 }}>{label}</div>
                <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 24, color: 'var(--accent)' }}>{val}</div>
              </div>
            ))}
          </div>

          {/* Splits table (editable) */}
          {editedSplits.length > 0 && (
            <div>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 12 }}>
                Split Data — click to edit
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: "'DM Mono', monospace", fontSize: 12 }}>
                  <thead>
                    <tr>
                      {['KM', 'Time', 'Pace /km', 'HR bpm', 'Power W'].map(h => (
                        <th key={h} style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', color: 'var(--muted)', fontWeight: 400, textAlign: 'left', letterSpacing: 1 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {editedSplits.map((s, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '6px 12px', color: 'var(--muted)' }}>{s.km}</td>
                        {['time', 'pace_per_km', 'hr_bpm', 'power_watts'].map(field => (
                          <td key={field} style={{ padding: '4px 8px' }}>
                            <input
                              value={s[field] ?? ''}
                              onChange={e => updateSplit(i, field, e.target.value)}
                              style={inputStyle}
                            />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div style={{ marginTop: 16, padding: '12px 16px', background: 'rgba(232,255,71,0.05)', border: '1px solid rgba(232,255,71,0.15)', fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--accent)' }}>
            ✓ Saved to database — Week {result.week_number}
          </div>
        </div>
      )}
    </div>
  )
}
