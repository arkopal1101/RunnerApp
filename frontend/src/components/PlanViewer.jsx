import { useState, useEffect } from 'react'
import { apiUrl } from '../utils/api'

/* ─── CSS-in-JS helpers ─── */
const css = {
  hero: {
    position: 'relative',
    padding: '60px 40px 40px',
    borderBottom: '1px solid var(--border)',
    overflow: 'hidden',
  },
  heroBefore: {
    content: "''",
    position: 'absolute',
    top: -100,
    right: -100,
    width: 500,
    height: 500,
    background: 'radial-gradient(circle, rgba(232,255,71,0.06) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  heroLabel: {
    fontFamily: "'DM Mono', monospace",
    fontSize: 11,
    letterSpacing: 3,
    color: 'var(--accent)',
    textTransform: 'uppercase',
    marginBottom: 16,
  },
  heroH1: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: 'clamp(48px, 8vw, 96px)',
    lineHeight: 0.9,
    letterSpacing: 2,
    marginBottom: 24,
  },
  statsRow: { display: 'flex', gap: 32, flexWrap: 'wrap', marginTop: 32 },
  stat: { display: 'flex', flexDirection: 'column', gap: 4 },
  statLabel: {
    fontFamily: "'DM Mono', monospace",
    fontSize: 10,
    letterSpacing: 2,
    color: 'var(--muted)',
    textTransform: 'uppercase',
  },
  statValue: { fontFamily: "'Bebas Neue', sans-serif", fontSize: 32, color: 'var(--text)' },
  statValueTarget: { fontFamily: "'Bebas Neue', sans-serif", fontSize: 32, color: 'var(--accent)' },
  arrow: { fontSize: 24, color: 'var(--accent2)', alignSelf: 'center', marginTop: 16 },
  nav: {
    display: 'flex',
    gap: 0,
    padding: '0 40px',
    borderBottom: '1px solid var(--border)',
    overflowX: 'auto',
    scrollbarWidth: 'none',
  },
  content: { padding: 40, width: '100%' },
  sectionHeader: {
    display: 'flex',
    alignItems: 'baseline',
    gap: 16,
    marginBottom: 24,
    marginTop: 40,
    paddingBottom: 12,
    borderBottom: '1px solid var(--border)',
  },
  sectionH2: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: 28,
    letterSpacing: 1,
  },
  badge: {
    fontFamily: "'DM Mono', monospace",
    fontSize: 10,
    letterSpacing: 2,
    padding: '3px 8px',
    background: 'var(--surface2)',
    border: '1px solid var(--border)',
    color: 'var(--muted)',
    textTransform: 'uppercase',
  },
  callout: {
    background: 'rgba(232,255,71,0.05)',
    border: '1px solid rgba(232,255,71,0.15)',
    padding: '16px 20px',
    marginBottom: 24,
    fontSize: 13,
    color: 'var(--muted)',
  },
  twoCol: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 },
  infoBlock: (accentColor = 'var(--accent)') => ({
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderLeft: `3px solid ${accentColor}`,
    padding: '20px 24px',
    marginBottom: 16,
  }),
  infoH3: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: 20,
    letterSpacing: 1,
    marginBottom: 12,
  },
  infoUl: { listStyle: 'none' },
  infoLi: {
    fontSize: 14,
    color: 'var(--muted)',
    padding: '5px 0',
    paddingLeft: 16,
    position: 'relative',
  },
}

const PHASE_COLORS = { 1: 'var(--phase1)', 2: 'var(--phase2)', 3: 'var(--phase3)', 4: 'var(--phase4)' }


/* ─── Sub-components ─── */
function NavBtn({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: 'none',
        border: 'none',
        color: active ? 'var(--accent)' : 'var(--muted)',
        fontFamily: "'DM Mono', monospace",
        fontSize: 11,
        letterSpacing: 2,
        textTransform: 'uppercase',
        padding: '16px 20px',
        borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
        whiteSpace: 'nowrap',
        transition: 'all 0.2s',
      }}
    >
      {label}
    </button>
  )
}

function DayTypeColor(type) {
  const map = {
    run: 'var(--phase3)',
    strength: 'var(--phase1)',
    rest: 'var(--muted)',
    cross: 'var(--phase2)',
    'long-run': 'var(--accent)',
    tempo: 'var(--accent2)',
  }
  return map[type] || 'var(--text)'
}

function DayCard({ day, completion }) {
  const label = day.type_label || day.typeLabel || ''
  const isCompleted = !!completion
  const borderLeftColor = isCompleted ? 'var(--accent)' : day.adjusted ? 'var(--accent3)' : null
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderLeft: borderLeftColor ? `3px solid ${borderLeftColor}` : '1px solid var(--border)',
      padding: 20,
      opacity: isCompleted ? 0.95 : 1,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, gap: 6, flexWrap: 'wrap' }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 3, color: 'var(--muted)', textTransform: 'uppercase' }}>
          {day.name}
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {isCompleted && (
            <span
              title={`Logged ${completion.kind} on ${completion.log_date}`}
              style={{
                fontFamily: "'DM Mono', monospace", fontSize: 9, letterSpacing: 1,
                padding: '2px 7px', background: 'var(--accent)', color: '#000',
                textTransform: 'uppercase', fontWeight: 600,
              }}
            >
              ✓ Done
            </span>
          )}
          {day.adjusted && (
            <span
              title={day.adjustment_rationale || 'Plan adjusted based on your recent progress'}
              style={{
                fontFamily: "'DM Mono', monospace", fontSize: 9, letterSpacing: 1,
                padding: '2px 7px', border: '1px solid var(--accent3)',
                color: 'var(--accent3)', textTransform: 'uppercase',
              }}
            >
              Adjusted
            </span>
          )}
        </div>
      </div>
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 20, letterSpacing: 1, color: DayTypeColor(day.type), marginBottom: 12 }}>
        {label}
      </div>
      <ul style={{ listStyle: 'none' }}>
        {day.details.map(([label, val], i) => (
          <li key={i} style={{
            fontSize: 13,
            color: 'var(--muted)',
            padding: '4px 0',
            borderBottom: i < day.details.length - 1 ? '1px solid var(--border)' : 'none',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 8,
          }}>
            {label}
            <span style={{ color: 'var(--text)', fontWeight: 500, textAlign: 'right', fontSize: 12 }}>{val}</span>
          </li>
        ))}
      </ul>
      {day.note && (
        <div style={{
          marginTop: 10,
          padding: '8px 10px',
          background: 'var(--surface2)',
          fontSize: 12,
          color: 'var(--muted)',
          fontStyle: 'italic',
          borderLeft: '2px solid var(--border)',
        }}>
          {day.note}
        </div>
      )}
      {day.adjusted && day.adjustment_rationale && (
        <div style={{
          marginTop: 8,
          padding: '8px 10px',
          background: 'rgba(71,184,255,0.05)',
          fontSize: 11,
          color: 'var(--accent3)',
          borderLeft: '2px solid var(--accent3)',
          lineHeight: 1.5,
        }}>
          <strong style={{ fontFamily: "'DM Mono', monospace", fontSize: 9, letterSpacing: 1, textTransform: 'uppercase' }}>Why adjusted: </strong>
          {day.adjustment_rationale}
        </div>
      )}
    </div>
  )
}

function InfoBlock({ title, items, accentColor = 'var(--accent)', style: extraStyle = {} }) {
  return (
    <div style={{ ...css.infoBlock(accentColor), ...extraStyle }}>
      <h3 style={css.infoH3}>{title}</h3>
      <ul style={css.infoUl}>
        {items.map((item, i) => (
          <li key={i} style={css.infoLi}>
            <span style={{ position: 'absolute', left: 0, color: 'var(--accent)' }}>→</span>
            <span dangerouslySetInnerHTML={{ __html: item }} />
          </li>
        ))}
      </ul>
    </div>
  )
}

/* ─── TABS ─── */
function OverviewTab() {
  return (
    <div>
      <div style={css.callout}>
        <strong style={{ color: 'var(--accent)' }}>Baseline logged (April 10):</strong>{' '}
        <span>Your first Zone 2 run clocked 10:49–9:49/km across 3.7km with HR drifting 144→152 bpm as pace slowed — classic <em>cardiac drift</em> from an underdeveloped aerobic base. This is the exact problem Phase 1 fixes. Your Zone 2 pace is normal for your starting point. The plan is now calibrated to your actual numbers.</span>
      </div>

      {/* Phase cards */}
      <div style={{ ...css.sectionHeader, marginTop: 0 }}>
        <h2 style={css.sectionH2}>The 4 Phases</h2>
        <span style={css.badge}>April → December</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, marginBottom: 48 }}>
        {[
          { phase: 1, tag: 'Weeks 1–8 · April–May', title: 'AEROBIC BASE & FAT ADAPTATION', rows: [['Duration', '8 weeks'], ['Target Weight', '~88 kg'], ['Weekly Run Volume', '20 → 35 km'], ['Strength', '3x/week full body']], unlock: '🔓 Unlock Phase 2 when: Zone 2 pace drops below 7:30/km at HR <145 bpm' },
          { phase: 2, tag: 'Weeks 9–16 · June–July', title: 'BUILD & BODY RECOMP', rows: [['Duration', '8 weeks'], ['Target Weight', '~84 kg'], ['Weekly Run Volume', '35 → 50 km'], ['Strength', '3x/week split']], unlock: '🔓 Unlock Phase 3 when: Long run reaches 14km, Zone 2 pace sub 7:00/km' },
          { phase: 3, tag: 'Weeks 17–24 · Aug–Sep', title: 'RACE SPECIFIC BUILD', rows: [['Duration', '8 weeks'], ['Target Weight', '~81 kg'], ['Weekly Run Volume', '50 → 60 km'], ['Strength', '2x/week maintenance']], unlock: '🔓 Unlock Phase 4 when: Completed a 18km long run, feeling strong' },
          { phase: 4, tag: 'Weeks 25–32 · Oct–Dec', title: 'PEAK & RACE READY', rows: [['Duration', '8 weeks'], ['Target Weight', '<80 kg'], ['Weekly Run Volume', '55–60 km (taper)'], ['Strength', '1x/week light']], unlock: '🏁 Race day: Half Marathon — sub 2:30 target pace' },
        ].map(({ phase, tag, title, rows, unlock }) => (
          <div key={phase} style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderTop: `3px solid ${PHASE_COLORS[phase]}`,
            padding: 24,
            position: 'relative',
            transition: 'transform 0.2s',
            cursor: 'default',
          }}>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 64, lineHeight: 1, opacity: 0.08, position: 'absolute', top: 8, right: 16 }}>{phase}</div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', color: PHASE_COLORS[phase], marginBottom: 8 }}>{tag}</div>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 26, letterSpacing: 1, marginBottom: 12 }}>{title}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
              {rows.map(([label, val]) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--muted)' }}>
                  {label} <strong style={{ color: 'var(--text)' }}>{val}</strong>
                </div>
              ))}
            </div>
            <div style={{ fontSize: 12, padding: '8px 12px', background: 'var(--surface2)', borderLeft: `2px solid ${PHASE_COLORS[phase]}`, color: 'var(--muted)', fontStyle: 'italic' }}>
              {unlock}
            </div>
          </div>
        ))}
      </div>

      {/* Running zones */}
      <div style={css.sectionHeader}>
        <h2 style={css.sectionH2}>Running Zones Explained</h2>
        <span style={css.badge}>Your Blueprint</span>
      </div>
      <div style={css.twoCol}>
        <InfoBlock title="Zone 2 — The Foundation" accentColor="var(--accent)" items={[
          'HR: <strong>130–145 bpm</strong> — stay under 145, walk if it spikes',
          'Effort: <strong>Conversational</strong> — full sentences easily',
          'Your baseline: <strong>~10:30/km at 144–152 bpm</strong> (logged April 10)',
          'Phase 1 Gate target: <strong>under 7:30/km at ≤145 bpm</strong>',
          'Phase 2 Gate target: <strong>under 7:00/km at ≤145 bpm</strong>',
          'Key fix: <strong>Start first 500m extra slow</strong> — let HR settle under 140 before finding pace. Your drift shows you\'re starting too hot.',
          '80% of all runs in Phase 1 are Zone 2 only',
        ]} />
        <InfoBlock title="Zone 4 — The Race Zone" accentColor="var(--accent2)" items={[
          'HR: <strong>165–180 bpm</strong>',
          'Effort: <strong>Can say 3–4 words max</strong>',
          'Use: <strong>Tempo runs & intervals only</strong>',
          'Max 20% of weekly volume in Phase 1–2',
          'This is where you race at pace',
          'Only introduced from Week 9 onwards',
        ]} />
      </div>

      {/* Baseline */}
      <div style={css.sectionHeader}>
        <h2 style={css.sectionH2}>Your Actual Baseline</h2>
        <span style={css.badge}>April 10 · First Run Logged</span>
      </div>
      <InfoBlock title="Split Analysis — What Your Data Says" accentColor="var(--accent)" items={[
        'KM 1: <strong>9:49/km @ 144 bpm</strong> — started too fast, HR already at ceiling',
        'KM 2: <strong>10:10/km @ 148 bpm</strong> — pace dropped, HR still climbing',
        'KM 3: <strong>10:39/km @ 152 bpm</strong> — HR above Zone 2 ceiling despite slowing down',
        'KM 4: <strong>10:59/km @ 146 bpm</strong> — HR came back down as pace slowed further',
        'Pattern: <strong>Cardiac drift</strong> — heart works harder to maintain same effort as run continues. Aerobic engine is not yet efficient.',
        'Fix: <strong>First 500m must feel embarrassingly slow.</strong> Let HR settle to ~135 before finding your cruise pace. This alone will stop the drift.',
        'HR ceiling for all Phase 1 runs: <strong>145 bpm strict</strong>. Walk the moment it hits 148+.',
      ]} />
      <div style={css.twoCol}>
        <InfoBlock title="Realistic Phase 1 Pace Progression" accentColor="var(--accent2)" items={[
          'Week 1–2: <strong>10:30–11:00/km</strong> is fine and expected',
          'Week 3–4: <strong>10:00–10:30/km</strong> target',
          'Week 5–6: <strong>9:30–10:00/km</strong> at same HR',
          'Week 7–8: <strong>8:30–9:30/km</strong> — noticeable improvement',
          'Phase Gate: <strong>sub 7:30/km at HR ≤145</strong>',
        ]} />
        <InfoBlock title="Week 1 Run Distances (Recalibrated)" accentColor="var(--accent3)" items={[
          'Tue: <strong>3km</strong> — short, controlled, HR under 140',
          'Thu: <strong>4km</strong> — slightly longer, same HR discipline',
          'Sat: <strong>3km</strong> — shakeout, legs fresh for Sunday',
          'Sun: <strong>6km long run</strong> — walk-run fine, just cover distance',
          'Total Week 1: <strong>~16km</strong> including strength days',
        ]} />
      </div>

      {/* Strength */}
      <div style={css.sectionHeader}>
        <h2 style={css.sectionH2}>Strength Training Philosophy</h2>
        <span style={css.badge}>Muscle definition + injury prevention</span>
      </div>
      <div style={css.twoCol}>
        <InfoBlock title="Phase 1–2 Focus (Full Body)" accentColor="var(--accent3)" items={[
          '<strong>Squats & Deadlifts</strong> — posterior chain for running power',
          '<strong>Push-ups / Chest Press</strong> — upper body baseline',
          '<strong>Rows & Pull-ups</strong> — back strength, posture',
          '<strong>Lunges & Step-ups</strong> — running specific legs',
          '<strong>Core work</strong> — planks, dead bugs, Russian twists daily',
          '3 sets × 10–12 reps, progressive overload each week',
        ]} />
        <InfoBlock title="Phase 3–4 Focus (Maintenance)" accentColor="var(--phase2)" items={[
          'Running takes priority — volume of strength drops',
          'Bodyweight + light weights to retain muscle',
          '<strong>Heavy on single-leg work</strong> — glute bridges, step-ups',
          '<strong>Injury prevention</strong> — calf raises, hip flexor work',
          'Friday is always run/tempo — never strength on Friday',
          'Saturday is always active recovery — never training',
          '<strong>Never strength train the day before a long run</strong> — Saturday is sacred rest',
        ]} />
      </div>
    </div>
  )
}

function WeeklyTab({ token }) {
  const [selectedWeek, setSelectedWeek] = useState(1)
  const [weeks, setWeeks] = useState(null)
  const [completion, setCompletion] = useState({})  // { weekNumber: { dow: dayLog } }
  const [error, setError] = useState('')

  useEffect(() => {
    const auth = { headers: { Authorization: `Bearer ${token}` } }
    fetch(apiUrl('/api/plan/all'), auth)
      .then(r => r.ok ? r.json() : Promise.reject(new Error('fetch failed')))
      .then(d => setWeeks(d.weeks))
      .catch(() => setError('Could not load training plan.'))
    // Completion map is optional — render the plan even if this fails
    fetch(apiUrl('/api/day-log/all'), auth)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.by_week) setCompletion(d.by_week) })
      .catch(() => {})
  }, [token])

  function renderWeekContent(w) {
    if (!weeks) {
      return (
        <div style={{ padding: 20, fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)' }}>
          {error || 'Loading plan…'}
        </div>
      )
    }
    const week = weeks.find(x => x.week === w)
    if (!week) return null
    const phaseColor = PHASE_COLORS[week.phase]
    return (
      <div style={{ animation: 'fadeIn 0.2s ease' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20, flexWrap: 'wrap' }}>
          <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1 }}>WEEK {week.week}</div>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, padding: '4px 12px', border: `1px solid ${phaseColor}`, textTransform: 'uppercase', color: phaseColor }}>
            Phase {week.phase} · {week.phase_name}
          </div>
          {week.is_deload && (
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, padding: '3px 10px', border: '1px solid var(--accent2)', color: 'var(--accent2)', textTransform: 'uppercase' }}>
              Deload
            </div>
          )}
          {week.is_race_week && (
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, padding: '3px 10px', border: '1px solid var(--accent)', color: 'var(--accent)', textTransform: 'uppercase' }}>
              🏁 Race Week
            </div>
          )}
        </div>
        {week.focus && <div style={{ fontSize: 14, color: 'var(--muted)', marginBottom: 20 }}>{week.focus}</div>}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
          {week.days.map((day, i) => (
            <DayCard
              key={i}
              day={day}
              completion={completion[String(week.week)]?.[String(i)]}
            />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div style={css.callout}>
        <strong style={{ color: 'var(--accent)' }}>Weekly structure (all phases):</strong> Mon — Strength | Tue — Run | <strong>Wed — REST</strong> | Thu — Strength | Fri — Run/Tempo | <strong>Sat — Active Recovery</strong> | Sun — Long Run. Two rest/recovery days every single week. This is not optional — it's where adaptation happens.
      </div>

      <div style={{ ...css.sectionHeader, marginTop: 0 }}>
        <h2 style={css.sectionH2}>Select a Week</h2>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 32 }}>
        {Array.from({ length: 32 }, (_, i) => i + 1).map(w => {
          const phase = w <= 8 ? 1 : w <= 16 ? 2 : w <= 24 ? 3 : 4
          const phaseColor = PHASE_COLORS[phase]
          const isActive = w === selectedWeek
          return (
            <button
              key={w}
              onClick={() => setSelectedWeek(w)}
              style={{
                background: isActive ? 'var(--accent)' : 'var(--surface)',
                border: `1px solid ${isActive ? 'var(--accent)' : 'var(--border)'}`,
                borderTop: `2px solid ${isActive ? 'var(--accent)' : phaseColor}`,
                color: isActive ? '#000' : 'var(--muted)',
                fontFamily: "'DM Mono', monospace",
                fontSize: 11,
                letterSpacing: 1,
                padding: '8px 14px',
                transition: 'all 0.15s',
                fontWeight: isActive ? 'bold' : 'normal',
              }}
            >
              W{w}
            </button>
          )
        })}
      </div>

      {renderWeekContent(selectedWeek)}
    </div>
  )
}

function NutritionTab() {
  return (
    <div>
      <div style={css.callout}>
        <strong style={{ color: 'var(--accent)' }}>The rule:</strong>{' '}
        You cannot outrun a bad diet — but you also can't fuel your training on nothing. This is a <strong>performance-first deficit</strong>. You eat enough to train hard, recover well, and lose fat consistently. No crash dieting.
      </div>

      <div style={{ ...css.sectionHeader, marginTop: 0 }}>
        <h2 style={css.sectionH2}>Daily Macros — Phase 1 & 2</h2>
        <span style={css.badge}>Approx 2000–2200 kcal</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        {[['180', 'GRAMS / DAY', 'Protein'], ['200', 'GRAMS / DAY', 'Carbohydrates'], ['65', 'GRAMS / DAY', 'Healthy Fats'], ['~500', 'KCAL DEFICIT', 'From Maintenance']].map(([val, unit, label]) => (
          <div key={label} style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: 20, textAlign: 'center' }}>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 48, lineHeight: 1, color: 'var(--accent)' }}>{val}</div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: 'var(--muted)', letterSpacing: 2 }}>{unit}</div>
            <div style={{ fontSize: 14, color: 'var(--text)', marginTop: 4 }}>{label}</div>
          </div>
        ))}
      </div>

      <div style={css.sectionHeader}>
        <h2 style={css.sectionH2}>Eating Strategy</h2>
      </div>
      <div style={css.twoCol}>
        <InfoBlock title="Pre-Run Nutrition" accentColor="var(--accent)" items={[
          '<strong>Easy runs (&lt;45 min):</strong> Fasted or light snack — banana, black coffee',
          '<strong>Long runs (60+ min):</strong> Light meal 90 min before — oats, banana, peanut butter',
          '<strong>During long runs (&gt;90 min):</strong> 30–60g carbs/hour — dates, gels, raisins',
          'Always hydrate 500ml 1hr before',
        ]} />
        <InfoBlock title="Post-Run Recovery Window" accentColor="var(--accent2)" items={[
          'Eat within <strong>45 minutes</strong> post-run',
          'Protein + Carbs combo — 3:1 carb-to-protein ratio',
          'Options: Eggs + rice, paneer + roti, whey + banana shake',
          'Avoid high-fat in this window — slows absorption',
        ]} />
      </div>

      <InfoBlock title="Indian Meal Planning — What Works" accentColor="var(--accent3)" items={[
        '<strong>Breakfast:</strong> 4 eggs (2 whole + 2 whites) + 2 whole wheat rotis + black coffee',
        '<strong>Lunch:</strong> 200g paneer/chicken + 1 cup dal + 1 cup sabji + 2 rotis or 1 cup rice',
        '<strong>Pre-workout snack:</strong> Greek yogurt + banana OR handful of mixed nuts + dates',
        '<strong>Post-workout:</strong> Whey shake (30g protein) + 1 banana OR egg whites + quick carb',
        '<strong>Dinner:</strong> Large salad + 200g lean protein (chicken/fish/paneer) + vegetables',
        '<strong>Avoid:</strong> Maida, fried snacks, packaged food, excessive chai with sugar, alcohol on training days',
        '<strong>Cheat meal:</strong> 1x per week — not a cheat day. Controlled indulgence, not a binge.',
      ]} />

      <div style={css.sectionHeader}>
        <h2 style={css.sectionH2}>Supplements Worth Taking</h2>
      </div>
      <InfoBlock title="The Short List (Evidence-Based Only)" accentColor="var(--accent)" items={[
        '<strong>Whey Protein:</strong> Only if you can\'t hit 180g protein from food. Not magic, just convenient.',
        '<strong>Creatine Monohydrate:</strong> 5g/day, every day. Retains muscle during fat loss. Cheap and proven.',
        '<strong>Vitamin D3 + K2:</strong> Most Indians are deficient. Supports muscle function and immunity.',
        '<strong>Magnesium Glycinate:</strong> 300mg at night. Aids sleep quality and muscle recovery.',
        '<strong>Electrolytes:</strong> On long run days — coconut water, ORS, or electrolyte tabs. Not during short runs.',
        '<strong>Skip:</strong> Fat burners, BCAAs (redundant with sufficient protein), expensive pre-workouts.',
      ]} />
    </div>
  )
}

function MilestonesTab() {
  const milestones = [
    { date: 'End of Week 2 — Late April', title: 'First Check-In', desc: 'Consistent 5x/week running. No pace targets — just no-drift runs. Cardiac drift (your baseline pattern) should be visibly reduced: HR should stay flatter across km 2–3 even if pace is similar. Weight: ~92–93 kg. Zone 2 pace should feel less miserable than Day 1.' },
    { date: 'End of Week 4 — Early May', title: 'First Long Run: 10 km', desc: 'Complete a 10km run at full Zone 2 — walk-run is fine. Zone 2 pace target: under 10:00/km (you started at 10:30 — this is a real, achievable improvement). HR should be staying flatter across the run with less drift than your baseline. Weight: ~91 kg.' },
    { date: 'End of Week 8 — Late May', title: 'Phase 1 Gate: Aerobic Base Established', desc: '✅ Zone 2 pace under 7:30/km at HR ≤145\n✅ Long run: 14km completed\n✅ Weight: ~88 kg\n✅ Running 5x per week consistently\nIf all boxes are checked, you move to Phase 2.' },
    { date: 'End of Week 12 — Late June', title: 'First Tempo Run: 5km @ Race Pace', desc: 'You\'ve introduced tempo intervals. Run 5km at a pace that\'s uncomfortable but sustainable. This becomes your gauge for half marathon target pace. Weight: ~85–86 kg. Zone 2 should feel truly easy now.' },
    { date: 'End of Week 16 — Late July', title: 'Phase 2 Gate: First Long Run 18km', desc: '✅ Long run: 18km completed\n✅ Zone 2 pace: under 7:00/km\n✅ Weight: ~83–84 kg\n✅ Tempo runs feeling controlled\nYou now know you can finish the race. Phase 3 is about doing it faster.' },
    { date: 'End of Week 20 — Late August', title: 'Peak Training Week', desc: 'Highest volume week — ~60km total. Long run: 20km. This is the hardest week of the plan. After this you begin tapering the long runs while keeping intensity. Weight: ~81 kg. Visible muscle definition should be evident.' },
    { date: 'End of Week 24 — Late September', title: 'Phase 3 Gate: Race Simulation', desc: '✅ Completed a simulated half marathon effort (run 19–20km at target pace)\n✅ Weight: ~80 kg\n✅ Consistent 5–6 runs per week for 8+ weeks\n✅ No major injuries\nPhase 4 is just refinement. You\'re essentially ready.' },
    { date: 'Weeks 25–28 — October', title: 'Race Specific Sharpening', desc: 'Volume drops, intensity sharpens. 10km race (if possible) as a tune-up. Fine-tune race day nutrition strategy. Dial in your target pace — aim for sub 2:30 finish (roughly 7:06/km). Weight: at or below 80 kg.' },
    { date: 'Weeks 29–32 — November-December', title: 'Taper & Race Day', desc: 'Volume drops 40% in the final 3 weeks. You will feel sluggish and doubt everything — this is normal. Trust the taper. Race week: easy runs only, sleep 8+ hours, carb load 2 days out, race day nutrition locked in.' },
    { date: 'December 2025', title: '🏁 HALF MARATHON — RACE DAY', desc: 'Target: Sub 2:30:00 (aggressive but achievable given the training)\nWeight: Under 80 kg\nWaist: ~32–33"\nVisible muscle definition ✅\nA completely different body and engine than where you started.' },
  ]

  return (
    <div>
      <div style={css.callout}>
        <strong style={{ color: 'var(--accent)' }}>Use these as checkpoints.</strong>{' '}
        If you're not hitting a milestone, don't advance phases — extend the current one. Progress is more important than schedule. Missing a milestone by a week is fine. Missing it by three weeks means something needs adjusting.
      </div>

      <div style={{ ...css.sectionHeader, marginTop: 0 }}>
        <h2 style={css.sectionH2}>Progress Milestones</h2>
      </div>

      <div style={{ position: 'relative', paddingLeft: 32 }}>
        <div style={{ position: 'absolute', left: 8, top: 0, bottom: 0, width: 1, background: 'var(--border)' }} />
        {milestones.map((m, i) => (
          <div key={i} style={{ position: 'relative', marginBottom: 28 }}>
            <div style={{
              position: 'absolute',
              left: -28,
              top: 6,
              width: 10,
              height: 10,
              borderRadius: '50%',
              border: '2px solid var(--accent)',
              background: 'var(--bg)',
            }} />
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 2, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 4 }}>{m.date}</div>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, letterSpacing: 1, marginBottom: 6 }}>{m.title}</div>
            <div style={{ fontSize: 13, color: 'var(--muted)', whiteSpace: 'pre-line' }}>{m.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ─── Main Component ─── */
export default function PlanViewer({ token }) {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <div>
      {/* Hero */}
      <div style={css.hero} className="plan-hero">
        <div style={{ position: 'absolute', top: -100, right: -100, width: 500, height: 500, background: 'radial-gradient(circle, rgba(232,255,71,0.06) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={css.heroLabel}>/ Personal Transformation Plan / April 2025 → December 2025 · Baseline Logged</div>
        <h1 style={css.heroH1}>
          HALF<br />MARATHON<br /><span style={{ color: 'var(--accent)' }}>MODE</span>
        </h1>
        <div style={css.statsRow}>
          <div style={css.stat}><div style={css.statLabel}>Start Weight</div><div style={css.statValue}>94 kg</div></div>
          <div style={css.arrow}>→</div>
          <div style={css.stat}><div style={css.statLabel}>Target Weight</div><div style={css.statValueTarget}>&lt;80 kg</div></div>
          <div style={css.stat}><div style={css.statLabel}>Start Waist</div><div style={css.statValue}>38"</div></div>
          <div style={css.arrow}>→</div>
          <div style={css.stat}><div style={css.statLabel}>Target Waist</div><div style={css.statValueTarget}>~32"</div></div>
          <div style={css.stat}><div style={css.statLabel}>Z2 Pace Now</div><div style={css.statValue}>10:30/km</div></div>
          <div style={css.arrow}>→</div>
          <div style={css.stat}><div style={css.statLabel}>Z2 Pace Target</div><div style={css.statValueTarget}>&lt;7:00/km</div></div>
          <div style={css.stat}><div style={css.statLabel}>Goal Event</div><div style={css.statValueTarget}>21.1 KM</div></div>
        </div>
      </div>

      {/* Inner nav */}
      <div style={css.nav} className="plan-nav">
        {[['overview', 'Overview'], ['weekly', 'Week by Week'], ['nutrition', 'Nutrition'], ['milestones', 'Milestones']].map(([id, label]) => (
          <NavBtn key={id} label={label} active={activeTab === id} onClick={() => setActiveTab(id)} />
        ))}
      </div>

      {/* Content */}
      <div style={css.content} className="plan-content">
        <style>{`@keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }`}</style>
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'weekly' && <WeeklyTab token={token} />}
        {activeTab === 'nutrition' && <NutritionTab />}
        {activeTab === 'milestones' && <MilestonesTab />}
      </div>
    </div>
  )
}
