import { useState } from 'react'

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

/* ─── Data ─── */
const phase1Focus = [
  "Foundation — Run Easy, Feel Awkward, That's Fine",
  "Consistency Over Intensity",
  "Zone 2 Lock-In — Every Run Easy",
  "First Long Run Week — 10km Zone 2",
  "Strength Foundation Deepening",
  "Volume Bump — Running Gets Easier",
  "12km Long Run — Progress is Real",
  "Phase 1 Peak — 14km Long Run",
]

const phase1Days = [
  [
    { name: "Monday", type: "strength", typeLabel: "Full Body Strength", details: [["Squats", "3×10"], ["Push-ups", "3×12"], ["Dumbbell Row", "3×10 each"], ["Lunges", "3×12 each"], ["Plank", "3×45s"], ["Core circuit", "10 min"]] },
    { name: "Tuesday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "3 km"], ["Target HR", "130–140 bpm — stricter than you think"], ["First 500m", "Embarrassingly slow — let HR settle"], ["Effort", "Full sentences comfortable"]], note: "Your baseline showed HR at 144 in km 1. Start slower than feels right. HR under 140 for the first 500m, then find your cruise." },
    { name: "Wednesday", type: "rest", typeLabel: "Full Rest Day", details: [["Do nothing", "Seriously. Rest."], ["Optional", "20 min gentle walk only"], ["Focus", "Sleep 7–8 hrs, eat well"], ["Why", "Adaptation happens during rest, not training"]], note: "Rest days are not wasted days. Your aerobic base is being built right now while you sleep." },
    { name: "Thursday", type: "strength", typeLabel: "Full Body Strength", details: [["Deadlifts", "3×10"], ["Chest Press", "3×12"], ["Pull-ups / Assisted", "3×8"], ["Glute Bridge", "3×15"], ["Russian Twists", "3×20"], ["Dead Bug", "3×10"]] },
    { name: "Friday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "4 km"], ["Target HR", "Under 145 strict"], ["Walk trigger", "HR hits 148 → walk until 138, then resume"], ["Focus", "Nasal breathing only"]], note: "Nasal breathing is your HR governor. If you can't breathe through your nose, you're going too fast. Use it religiously in Phase 1." },
    { name: "Saturday", type: "rest", typeLabel: "Active Recovery", details: [["Foam roll", "15–20 min — calves, quads, hamstrings"], ["Stretch", "Full body 20 min"], ["Walk", "30 min easy if you feel like it"], ["Sleep", "8+ hrs — long run tomorrow"]], note: "This is not a run day. Foam roll and stretch. Your Sunday long run will be noticeably better for this rest." },
    { name: "Sunday", type: "long-run", typeLabel: "Long Run — Zone 2", details: [["Distance", "6 km"], ["Strategy", "Walk-run is not just allowed — it's encouraged"], ["HR cap", "150 bpm absolute max"], ["Pace", "Your baseline is 10:30–11:00/km. That's your starting point."], ["Fuelling", "Water every 20 min"]], note: "6km because your baseline showed cardiac drift at 3.7km. Finishing 6km slow beats quitting 8km." },
  ],
  [
    { name: "Monday", type: "strength", typeLabel: "Full Body Strength", details: [["Squats", "3×12"], ["Push-ups", "3×15"], ["Dumbbell Row", "3×12 each"], ["Reverse Lunges", "3×12 each"], ["Plank", "3×50s"], ["Core circuit", "12 min"]] },
    { name: "Tuesday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "4 km"], ["Target HR", "130–145 bpm"], ["Cadence", "Aim for ~160–170 spm"], ["Drift check", "Is HR stable across km 2–3? Flatter than Week 1?"]], note: "Compare km splits to your baseline. If HR is drifting less at the same pace, the aerobic base is adapting. That's the win." },
    { name: "Wednesday", type: "rest", typeLabel: "Full Rest Day", details: [["Rest", "No training"], ["Optional", "20 min walk + 15 min stretch"], ["Eat", "Hit your protein target — recovery needs fuel"], ["Sleep", "Prioritize 7–8 hours"]], note: "Two rest days per week is the rule in Phase 1. You're not losing fitness. You're building it." },
    { name: "Thursday", type: "strength", typeLabel: "Full Body Strength", details: [["Romanian Deadlift", "3×10"], ["Incline Push-up", "3×12"], ["Pull-ups / Lat Pulldown", "3×10"], ["Single Leg Glute Bridge", "3×12 each"], ["Ab Wheel / Hollow Body", "3×10"]] },
    { name: "Friday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "5 km"], ["Pace", "Comfortable — HR guided"], ["Focus", "Relax shoulders, arms at 90°"], ["Post", "5 min walking cool-down + stretch"]] },
    { name: "Saturday", type: "rest", typeLabel: "Active Recovery", details: [["Foam roll", "Calves, IT band, quads — 20 min"], ["Stretch", "Hip flexors, hamstrings, glutes"], ["Walk", "30 min easy optional"], ["Prep", "Eat a banana + good carb dinner for Sunday"]], note: "Long run tomorrow. Eat well tonight. Sleep early. Lay out your kit." },
    { name: "Sunday", type: "long-run", typeLabel: "Long Run — 7km Zone 2", details: [["Distance", "7 km"], ["HR cap", "150 bpm"], ["Nutrition", "Banana 45 min before"], ["Hydration", "Water every 20 min"], ["Recovery", "10 min walk + stretch after"]], note: "+1km from last week. This is the progression. Same effort, more distance." },
  ],
  [
    { name: "Monday", type: "strength", typeLabel: "Full Body Strength", details: [["Squats", "4×10"], ["Push-ups", "3×15 or add weight"], ["Bent Row", "3×12"], ["Walking Lunges", "3×12 each"], ["Plank", "3×60s"]] },
    { name: "Tuesday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "5 km"], ["Focus", "Control breathing, relax shoulders"], ["HR", "Stay under 145"], ["Check", "Should feel easier than Week 1 at same pace"]] },
    { name: "Wednesday", type: "rest", typeLabel: "Full Rest Day", details: [["Rest", "No running, no lifting"], ["Mobility", "20 min hip flexor + calf work if you want"], ["Sleep", "Your legs are adapting right now"]], note: "3 weeks in. Rest is still non-negotiable. The urge to do extra is normal. Resist it in Phase 1." },
    { name: "Thursday", type: "strength", typeLabel: "Strength + Mobility Focus", details: [["Deadlifts", "4×8 (add weight from last week)"], ["Pull-ups", "3×max"], ["Hip Flexor Stretch", "3×60s each"], ["Foam Roll", "15 min"], ["Core", "3 heavy sets"]] },
    { name: "Friday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "5 km"], ["Approach", "First 1km extra slow — warm up properly"], ["Last 0.5km", "Pick up slightly only if HR stays under 145"]] },
    { name: "Saturday", type: "rest", typeLabel: "Active Recovery", details: [["Walk", "30–40 min easy"], ["Stretch", "Full body 20 min"], ["Sleep", "8+ hrs"], ["Eat", "Carb-rich dinner — rice, roti, oats"]], note: "Active recovery Saturday is a permanent fixture. Don't turn this into a training day." },
    { name: "Sunday", type: "long-run", typeLabel: "Long Run — 8km Zone 2", details: [["Distance", "8 km"], ["Zone", "Zone 2 the whole way"], ["Fuel", "Water + banana mid-run"], ["Post", "Protein + carb meal within 45 min"]], note: "+1km again. Steady progression. It doesn't matter how slow — you ran 8km." },
  ],
  [
    { name: "Monday", type: "strength", typeLabel: "Full Body Strength", details: [["Back Squat", "4×8 (progressive load)"], ["Push-up Variations", "4×12"], ["Pull-ups", "3×8"], ["Lunges", "3×12"], ["Plank Circuit", "4×45s"]] },
    { name: "Tuesday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "5 km"], ["HR", "130–145 bpm"], ["Add", "4×100m strides at very end only"]] },
    { name: "Wednesday", type: "rest", typeLabel: "Full Rest Day", details: [["Rest", "Complete rest"], ["Optional", "20 min gentle walk"], ["Eat", "Hit protein — your muscles are repairing"]] },
    { name: "Thursday", type: "strength", typeLabel: "Strength Focus", details: [["Deadlift", "4×6 (heavy)"], ["DB Row", "4×10"], ["Face Pulls + Band Work", "3×15"], ["Calf Raises", "4×20"], ["Core Strength", "20 min"]] },
    { name: "Friday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "6 km"], ["Zone 2 strict", "HR under 145"], ["Post", "Stretching 10 min"]] },
    { name: "Saturday", type: "rest", typeLabel: "Active Recovery", details: [["Foam roll", "20 min — focus on calves & quads"], ["Stretch", "Hip flexors, hamstrings"], ["Walk", "Optional 30 min"], ["Carb load", "Rice/roti dinner — long run tomorrow"]], note: "Longest run so far tomorrow. Rest properly today." },
    { name: "Sunday", type: "long-run", typeLabel: "Long Run — 10km Zone 2", details: [["Distance", "10 km — first double digits!"], ["Zone", "Zone 2 entire run — walk if HR spikes"], ["Fuel", "Carry water + 2 dates every 30 min"], ["Recovery", "Big protein meal + rest afternoon"]], note: "🏆 First 10km. This is a milestone. It doesn't matter how long it takes." },
  ],
  [
    { name: "Monday", type: "rest", typeLabel: "Full Rest — Deload Week", details: [["Deload", "Every 4 weeks, back off. This is Week 5."], ["Purpose", "Let the body consolidate gains from Weeks 1–4"], ["Do", "Eat well, sleep lots, foam roll"]], note: "Deload weeks are not optional. This is where your body catches up to the work you've been doing." },
    { name: "Tuesday", type: "run", typeLabel: "Easy Zone 2 Run — Deload", details: [["Distance", "4 km"], ["Easy effort", "HR under 140 — even easier than usual"], ["Focus", "Form only — posture, arm swing, cadence"]] },
    { name: "Wednesday", type: "strength", typeLabel: "Full Body (Light Deload)", details: [["Squats", "3×10 at 60% weight"], ["Push-ups", "3×10"], ["Rows", "3×10"], ["Core", "15 min"], ["Mobility", "20 min"]] },
    { name: "Thursday", type: "rest", typeLabel: "Full Rest Day", details: [["Rest", "Complete rest"], ["Sleep", "Prioritise 8+ hours"], ["Walk", "30 min gentle if restless"]] },
    { name: "Friday", type: "run", typeLabel: "Easy Zone 2 Run — Deload", details: [["Distance", "4 km"], ["Very easy", "HR under 135 if possible"], ["Enjoy", "Listen to a podcast, no watch-checking"]] },
    { name: "Saturday", type: "rest", typeLabel: "Active Recovery", details: [["Foam roll", "Full body 20 min"], ["Stretch", "20 min"], ["Sleep", "8+ hrs — long run tomorrow"]] },
    { name: "Sunday", type: "long-run", typeLabel: "Long Run — 10km (Easy Repeat)", details: [["Distance", "10 km — same as last week"], ["Note", "Deload — don't chase pace. This should feel easier."], ["Fuel", "Water + dates/banana"], ["Enjoy", "This is supposed to feel easy. That's the point."]] },
  ],
  [
    { name: "Monday", type: "strength", typeLabel: "Full Body Strength — Reload", details: [["Back Squats", "4×8 (add 2.5–5kg vs Week 4)"], ["Weighted Push-ups", "4×12"], ["Pull-ups", "4×8"], ["Lunges", "4×12 each"], ["Heavy Core", "20 min"]] },
    { name: "Tuesday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "6 km"], ["HR", "145 max"], ["Key check", "Compare pace to Week 1. It should be noticeably faster at same HR."]] },
    { name: "Wednesday", type: "rest", typeLabel: "Full Rest Day", details: [["Rest", "No training"], ["Mobility", "15 min optional"], ["Eat", "Protein + carbs — reload week"]] },
    { name: "Thursday", type: "strength", typeLabel: "Deadlift Focus + Upper", details: [["Deadlift", "4×6 (PR attempt from Week 4)"], ["Rows", "4×10"], ["Shoulder Press", "3×10"], ["Core", "20 min heavy"], ["Foam Roll", "15 min"]] },
    { name: "Friday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "6 km"], ["Zone 2 enforced", "Walk if HR spikes above 147"], ["Post", "Stretching + calf raises"]] },
    { name: "Saturday", type: "rest", typeLabel: "Active Recovery", details: [["Foam roll", "Calves, IT band, quads"], ["Stretch", "Full body"], ["Walk", "Optional 30 min"], ["Sleep", "8+ hrs"]], note: "Biggest long run so far tomorrow — 12km. Rest today." },
    { name: "Sunday", type: "long-run", typeLabel: "Long Run — 12km", details: [["Distance", "12 km"], ["This is getting real", "Longest run of the plan so far"], ["Fuel", "Every 30 min: water + 2 dates"], ["Post-run", "1hr rest, big meal, early sleep"]], note: "Start thinking about long run shoes if you haven't already — proper cushioning matters now." },
  ],
  [
    { name: "Monday", type: "strength", typeLabel: "Full Body Strength Heavy", details: [["Squats", "5×5 (heavy)"], ["Bench Press / Push-up", "4×10"], ["Pull-ups", "4×max"], ["Romanian Deadlift", "4×8"], ["Core", "25 min"]] },
    { name: "Tuesday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "7 km"], ["Pace check", "What is your avg pace at HR 140–145?"], ["Goal", "Should be under 9:00/km now — big improvement from 10:30"]] },
    { name: "Wednesday", type: "rest", typeLabel: "Full Rest Day", details: [["Rest", "Complete rest"], ["Optional", "Gentle walk 20 min"], ["Sleep", "8 hrs"]] },
    { name: "Thursday", type: "strength", typeLabel: "Upper Body + Core Heavy", details: [["Deadlift", "4×5 heavy"], ["Row variants", "4×10"], ["Overhead Press", "3×10"], ["Abs heavy", "25 min"]] },
    { name: "Friday", type: "run", typeLabel: "Zone 2 Run + Strides", details: [["Distance", "7 km"], ["Structure", "6km easy + 4×100m strides"], ["Strides", "Controlled pick-up — not a sprint. Fast but relaxed."]] },
    { name: "Saturday", type: "rest", typeLabel: "Active Recovery", details: [["Foam roll", "45 min — full lower body focus"], ["Stretch", "Hip flexors + hamstrings"], ["Sleep", "8+ hours — 13km tomorrow"], ["Carb load", "Good carb dinner tonight"]], note: "13km tomorrow. Sleep well, eat well today. This is the last big effort before Phase Gate week." },
    { name: "Sunday", type: "long-run", typeLabel: "Long Run — 13km", details: [["Distance", "13 km — nearly a Phase Gate distance"], ["Goal", "Note your pace at comfortable HR"], ["Fuel", "Carry nutrition — fuel every 30 min"], ["Post", "Record avg pace + HR — compare to Week 1 baseline"]] },
  ],
  [
    { name: "Monday", type: "strength", typeLabel: "Full Body Strength — Final Heavy", details: [["Squats", "5×5"], ["Deadlift", "4×5"], ["Pull-ups", "4×max"], ["Core", "30 min"], ["Note", "Last heavy session before Phase Gate"]] },
    { name: "Tuesday", type: "run", typeLabel: "Zone 2 Pace Test — 5km", details: [["Distance", "5 km"], ["This is a test", "Run at HR 140–145 and record your avg pace"], ["Baseline to beat", "10:30/km (April 10 logged run)"], ["Record", "Time, avg HR, avg pace — this is your Phase 1 report card"]], note: "⚡ Zone 2 pace test. You started at ~10:30/km. If you're now under 8:30/km at the same HR, that's a massive aerobic adaptation in 8 weeks." },
    { name: "Wednesday", type: "rest", typeLabel: "Full Rest Day", details: [["Rest", "Complete rest"], ["Eat", "High carb day — rice, roti, banana, oats"], ["Sleep", "8+ hours"], ["Prep", "Mentally prepare for Sunday Phase Gate"]], note: "Two big days ahead — rest today completely." },
    { name: "Thursday", type: "strength", typeLabel: "Light Strength — Prep Week", details: [["Squats", "3×8 (moderate weight only)"], ["Push/Pull", "3×10 light"], ["Core", "20 min"], ["No heavy lifts", "Legs need to be fresh for Sunday"]] },
    { name: "Friday", type: "rest", typeLabel: "Full Rest — Pre-Gate", details: [["Rest", "No training at all"], ["Eat", "High carb dinner — carb load for 14km Sunday"], ["Sleep", "8+ hours"], ["Hydrate", "2–3L water throughout the day"]], note: "Carb load day. Eat rice, roti, banana, oats. No skimping. You need fuel for 14km." },
    { name: "Saturday", type: "run", typeLabel: "Short Shakeout — 3km Only", details: [["Distance", "3 km very easy"], ["Purpose", "Loosen legs — not a workout"], ["HR", "Under 130"], ["Duration", "~30 min max"]] },
    { name: "Sunday", type: "long-run", typeLabel: "🔓 PHASE GATE — 14km Long Run", details: [["Distance", "14 km — Zone 2 the whole way"], ["Target HR", "Under 150 the entire run"], ["Fuel", "Water every 20 min + 3 date/banana portions"], ["Record", "Avg pace, avg HR, total time"], ["Gate check", "Sub 7:30/km at ≤145 bpm = Phase 2 unlocked"]], note: "🔓 PHASE 1 GATE: Complete 14km Zone 2 AND Zone 2 pace under 7:30/km → you move to Phase 2. If not yet, one more week. No rush." },
  ],
]

const phase2Week9Days = [
  { name: "Monday", type: "strength", typeLabel: "Upper Body Push", details: [["Bench Press / DB Press", "4×10"], ["Shoulder Press", "3×10"], ["Tricep Dips", "3×12"], ["Push-up Finisher", "2×max"], ["Core", "20 min"]] },
  { name: "Tuesday", type: "run", typeLabel: "Easy Zone 2 Run", details: [["Distance", "8 km"], ["Phase 2 begins", "Slightly longer easy runs"], ["HR", "Under 145"]] },
  { name: "Wednesday", type: "rest", typeLabel: "Full Rest Day", details: [["Rest", "Complete rest"], ["Optional", "20 min walk + foam roll"], ["Eat", "Hit protein target"]] },
  { name: "Thursday", type: "strength", typeLabel: "Lower Body + Core", details: [["Deadlift", "4×6"], ["Romanian DL", "3×8"], ["Hamstring Curl", "3×12"], ["Glute Bridge", "4×15"], ["Core", "20 min"]] },
  { name: "Friday", type: "tempo", typeLabel: "First Tempo Run", details: [["Structure", "2km warm-up + 3km tempo + 1km cool-down"], ["Tempo pace", "Uncomfortable but controlled (Zone 4 edge)"], ["HR", "160–175 bpm during tempo"]], note: "⚡ First tempo run of the plan. Your body will hate this. That's fine. Only 3km tempo — don't push beyond that today." },
  { name: "Saturday", type: "rest", typeLabel: "Active Recovery", details: [["Foam roll", "Full body — you need it after tempo"], ["Stretch", "Focus on calves, hip flexors"], ["Sleep", "8+ hrs for long run"]] },
  { name: "Sunday", type: "long-run", typeLabel: "Long Run — 15km", details: [["Distance", "15 km — Zone 2"], ["Nutrition", "Fuel every 30 min"], ["Target", "Sub 8:00/km avg"]], note: "You're in Phase 2. Runs get longer, tempo introduced. The rest days still matter — don't skip them." },
]

const phase2Summaries = {
  10: "Structure: Mon/Thu Strength | Tue Easy 8km | Fri Tempo 4km | Wed+Sat REST | Sun Long Run 16km",
  11: "Structure: Mon/Thu Strength | Tue Easy 8km | Fri Tempo 4km faster | Wed+Sat REST | Sun Long Run 16km",
  12: "DELOAD — Mon REST | Tue Easy 5km | Wed Light Strength | Thu REST | Fri Easy 5km | Sat REST | Sun Long Run 14km (easy)",
  13: "Structure: Mon/Thu Strength | Tue Easy 9km | Fri Tempo 5km | Wed+Sat REST | Sun Long Run 17km",
  14: "Structure: Mon/Thu Strength | Tue Easy 9km | Fri Intervals 6×800m | Wed+Sat REST | Sun Long Run 17km",
  15: "Structure: Mon/Thu Strength | Tue Easy 10km | Fri Tempo 6km | Wed+Sat REST | Sun Long Run 18km",
  16: "⚡ PHASE GATE — Mon/Thu Light Strength | Tue Pace Test 5km | Fri Tempo 5km | Wed+Sat REST | Sun Long Run 18km — target sub 7:00/km Zone 2",
}

const phase34Summaries = {
  17: "Mon/Thu Strength (2×) | Tue Easy 10km | Fri Tempo 7km | Wed+Sat REST | Sun Long Run 19km | Focus: Peak volume begins",
  18: "Mon/Thu Strength (2×) | Tue Easy 10km | Fri Intervals 8×800m | Wed+Sat REST | Sun Long Run 19km | Focus: Race pace sharpening",
  19: "Mon/Thu Strength (2×) | Tue Easy 10km | Fri Tempo 7km | Wed+Sat REST | Sun Long Run 20km 🏆 First 20km!",
  20: "⚡ PEAK WEEK — Mon/Thu Strength | Tue Easy 10km | Fri Tempo 8km | Wed+Sat REST | Sun Long Run 20km | ~55–60km total",
  21: "DELOAD — Mon REST | Tue Easy 8km | Wed Light Strength | Thu REST | Fri Easy 8km | Sat REST | Sun Long Run 16km (easy)",
  22: "Mon/Thu Strength (2×) | Tue Easy 10km | Fri Intervals 10×400m | Wed+Sat REST | Sun Long Run 19km",
  23: "Mon/Thu Strength (2×) | Tue Easy 10km | Fri Tempo 8km at race pace | Wed+Sat REST | Sun Long Run 20km — Race simulation",
  24: "⚡ PHASE GATE — Mon Light Strength | Tue Easy 8km | Wed REST | Thu Easy 6km | Fri REST | Sat Shakeout 3km | Sun 19–20km race simulation at target pace",
  25: "Phase 4 begins. Mon Light Strength | Tue Easy 8km | Wed REST | Thu Easy 8km | Fri Tempo 6km | Sat REST | Sun Long Run 18km",
  26: "Mon Light Strength | Tue Easy 8km | Wed REST | Thu Easy 6km | Fri 10km tune-up race (if available) | Sat REST | Sun Easy 16km",
  27: "Mon Light Strength | Tue Easy 8km | Wed REST | Thu Easy 8km | Fri Tempo 6km | Sat REST | Sun Long Run 18km | Nail race nutrition",
  28: "Mon Light Strength | Tue Easy 8km | Wed REST | Thu Intervals 6×1km race pace | Fri REST | Sat Shakeout 3km | Sun Long Run 16km",
  29: "TAPER — Mon Light Strength | Tue Easy 7km | Wed REST | Thu Easy 7km | Fri Tempo 5km | Sat REST | Sun Long Run 14km | Vol -25%",
  30: "TAPER — Mon Light Strength | Tue Easy 6km | Wed REST | Thu Easy 6km | Fri Tempo 4km | Sat REST | Sun Long Run 12km | Vol -40%",
  31: "TAPER — Mon Easy 5km | Tue REST | Wed Easy 5km | Thu REST | Fri Easy 3km | Sat REST | Sun Easy 10km | Carb load Fri/Sat",
  32: "🏁 RACE WEEK — Mon Easy 3km | Tue REST | Wed Easy 3km | Thu REST | Fri REST + carb load | Sat Shakeout 2km | RACE DAY — YOU'VE MADE IT",
}

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

function DayCard({ day }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      padding: 20,
    }}>
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: 3, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8 }}>
        {day.name}
      </div>
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 20, letterSpacing: 1, color: DayTypeColor(day.type), marginBottom: 12 }}>
        {day.typeLabel}
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

function WeeklyTab() {
  const [selectedWeek, setSelectedWeek] = useState(1)

  function getPhase(w) {
    if (w <= 8) return 1
    if (w <= 16) return 2
    if (w <= 24) return 3
    return 4
  }

  function renderWeekContent(w) {
    const phase = getPhase(w)
    const phaseColor = PHASE_COLORS[phase]

    if (w <= 8) {
      const days = phase1Days[w - 1]
      const focus = phase1Focus[w - 1]
      return (
        <div style={{ animation: 'fadeIn 0.2s ease' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20, flexWrap: 'wrap' }}>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1 }}>WEEK {w}</div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, padding: '4px 12px', border: `1px solid ${phaseColor}`, textTransform: 'uppercase', color: phaseColor }}>Phase {phase}</div>
          </div>
          <div style={{ fontSize: 14, color: 'var(--muted)', marginBottom: 20 }}>{focus}</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
            {days.map((day, i) => <DayCard key={i} day={day} />)}
          </div>
        </div>
      )
    }

    if (w === 9) {
      return (
        <div style={{ animation: 'fadeIn 0.2s ease' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1 }}>WEEK 9</div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, padding: '4px 12px', border: `1px solid ${phaseColor}`, textTransform: 'uppercase', color: phaseColor }}>Phase 2 — Build</div>
          </div>
          <div style={{ fontSize: 14, color: 'var(--muted)', marginBottom: 20 }}>Tempo runs introduced. Runs get longer. Strength splits into push/pull/legs. Pace is improving.</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
            {phase2Week9Days.map((day, i) => <DayCard key={i} day={day} />)}
          </div>
        </div>
      )
    }

    if (w >= 10 && w <= 16) {
      const summary = phase2Summaries[w]
      const weightTarget = Math.round(88 - (w - 8) * 0.5)
      return (
        <div style={{ animation: 'fadeIn 0.2s ease' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1 }}>WEEK {w}</div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, padding: '4px 12px', border: `1px solid ${phaseColor}`, textTransform: 'uppercase', color: phaseColor }}>Phase 2</div>
          </div>
          <div style={{ ...css.infoBlock(phaseColor), marginTop: 0 }}>
            <h3 style={css.infoH3}>Weekly Blueprint</h3>
            <p style={{ fontSize: 14, color: 'var(--muted)', lineHeight: 1.7 }}>{summary}</p>
            <div style={{ marginTop: 16, fontSize: 13, color: 'var(--muted)' }}>
              <strong style={{ color: 'var(--text)' }}>Structure:</strong> Mon/Thu — Strength | Tue/Thu — Run | Sun — Long Run<br />
              <strong style={{ color: 'var(--text)' }}>Zone 2 rule:</strong> All easy runs HR 130–145. If it spikes above 150, walk.<br />
              <strong style={{ color: 'var(--text)' }}>Strength:</strong> Push/Pull/Legs split — no longer full body. Each session ~45–60 min.<br />
              <strong style={{ color: 'var(--text)' }}>Weight target:</strong> ~{weightTarget} kg by end of this week
            </div>
          </div>
        </div>
      )
    }

    // Phases 3–4
    const summary = phase34Summaries[w]
    return (
      <div style={{ animation: 'fadeIn 0.2s ease' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
          <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 36, letterSpacing: 1 }}>WEEK {w}</div>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, letterSpacing: 2, padding: '4px 12px', border: `1px solid ${phaseColor}`, textTransform: 'uppercase', color: phaseColor }}>Phase {phase}</div>
        </div>
        <div style={{ ...css.infoBlock(phaseColor), marginTop: 0 }}>
          <h3 style={css.infoH3}>Weekly Blueprint</h3>
          <p style={{ fontSize: 14, color: 'var(--muted)', lineHeight: 1.7 }}>{summary}</p>
          <div style={{ marginTop: 16, fontSize: 13, color: 'var(--muted)' }}>
            <strong style={{ color: 'var(--text)' }}>Structure:</strong> Phase 3: 2× strength, 5 runs | Phase 4: 1× strength, 5 runs<br />
            <strong style={{ color: 'var(--text)' }}>Zone 2 rule:</strong> All easy runs remain conversational HR guided<br />
            <strong style={{ color: 'var(--text)' }}>Strength:</strong> Maintenance only — single leg, core, injury prevention<br />
            <strong style={{ color: 'var(--text)' }}>Key:</strong> Never skip easy days. Recovery is where fitness is built.
          </div>
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

      {/* Week selector buttons */}
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
export default function PlanViewer() {
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
        {activeTab === 'weekly' && <WeeklyTab />}
        {activeTab === 'nutrition' && <NutritionTab />}
        {activeTab === 'milestones' && <MilestonesTab />}
      </div>
    </div>
  )
}
