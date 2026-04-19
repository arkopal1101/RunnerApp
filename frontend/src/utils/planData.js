// Shared training plan helpers used by Today, PlanViewer, and Dashboard

export const START_DATE = new Date('2026-04-14')
export const START_WEIGHT = 94
export const TARGET_WEIGHT = 80
export const START_WAIST = 38
export const TARGET_WAIST = 32
export const HEIGHT_CM = 180.5
export const BASELINE_PACE = '10:30'
export const PHASE1_GATE_PACE = '7:30'
export const PHASE2_GATE_PACE = '7:00'

export const PHASE_NAMES = {
  1: 'Aerobic Base',
  2: 'Build & Recomp',
  3: 'Race Specific',
  4: 'Peak & Race Ready',
}

export const PHASE_COLORS = {
  1: 'var(--phase1)',
  2: 'var(--phase2)',
  3: 'var(--phase3)',
  4: 'var(--phase4)',
}

// Day types for the standard weekly structure
// 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
const STANDARD_DAY_TYPES = {
  0: { type: 'strength', label: 'Full Body Strength' },
  1: { type: 'run', label: 'Easy Zone 2 Run' },
  2: { type: 'rest', label: 'Full Rest Day' },
  3: { type: 'strength', label: 'Full Body Strength' },
  4: { type: 'run', label: 'Easy Zone 2 Run' },
  5: { type: 'rest', label: 'Active Recovery' },
  6: { type: 'long-run', label: 'Long Run' },
}

const DELOAD_DAY_TYPES = {
  0: { type: 'rest', label: 'Full Rest - Deload' },
  1: { type: 'run', label: 'Easy Run - Deload' },
  2: { type: 'strength', label: 'Light Strength - Deload' },
  3: { type: 'rest', label: 'Full Rest Day' },
  4: { type: 'run', label: 'Easy Run - Deload' },
  5: { type: 'rest', label: 'Active Recovery' },
  6: { type: 'long-run', label: 'Long Run (Easy Repeat)' },
}

const PHASE2_DAY_TYPES = {
  0: { type: 'strength', label: 'Strength' },
  1: { type: 'run', label: 'Easy Zone 2 Run' },
  2: { type: 'rest', label: 'Full Rest Day' },
  3: { type: 'strength', label: 'Strength' },
  4: { type: 'tempo', label: 'Tempo / Intervals' },
  5: { type: 'rest', label: 'Active Recovery' },
  6: { type: 'long-run', label: 'Long Run' },
}

const DELOAD_WEEKS = new Set([5, 12, 21, 29, 30, 31])
const RACE_WEEK = 32

const RACE_DAY_TYPES = {
  0: { type: 'run', label: 'Easy 3km' },
  1: { type: 'rest', label: 'Full Rest' },
  2: { type: 'run', label: 'Easy 3km' },
  3: { type: 'rest', label: 'Full Rest' },
  4: { type: 'rest', label: 'Rest + Carb Load' },
  5: { type: 'run', label: 'Shakeout 2km' },
  6: { type: 'long-run', label: 'RACE DAY' },
}

export function getPhase(week) {
  if (week <= 8) return 1
  if (week <= 16) return 2
  if (week <= 24) return 3
  return 4
}

export function getCurrentWeek() {
  const diffDays = Math.floor((new Date() - START_DATE) / (1000 * 60 * 60 * 24))
  if (diffDays < 0) return 1
  return Math.min(Math.floor(diffDays / 7) + 1, 32)
}

export function getDayInfo(week, dayOfWeek) {
  if (week === RACE_WEEK) return RACE_DAY_TYPES[dayOfWeek] || { type: 'rest', label: 'Rest' }
  if (DELOAD_WEEKS.has(week)) return DELOAD_DAY_TYPES[dayOfWeek] || { type: 'rest', label: 'Rest' }
  if (week >= 9) return PHASE2_DAY_TYPES[dayOfWeek] || { type: 'rest', label: 'Rest' }
  return STANDARD_DAY_TYPES[dayOfWeek] || { type: 'rest', label: 'Rest' }
}

export function getTodayInfo() {
  const week = getCurrentWeek()
  const dayOfWeek = new Date().getDay() // 0=Sun, 1=Mon...
  // Convert JS day (Sun=0) to our format (Mon=0)
  const dayIdx = (dayOfWeek + 6) % 7
  return { week, phase: getPhase(week), dayOfWeek: dayIdx, ...getDayInfo(week, dayIdx) }
}

export function getCTALabel(dayType, nextAction) {
  if (nextAction === 'weekly_checkin') return 'Complete Weekly Check-In'
  switch (dayType) {
    case 'run':
    case 'long-run':
    case 'tempo':
    case 'intervals':
      return "Log Today's Run"
    case 'strength':
      return 'Log Workout'
    case 'rest':
      return 'Rested Today'
    default:
      return 'Log Today'
  }
}

export function getCTATab(dayType, nextAction) {
  if (nextAction === 'weekly_checkin') return 'weekly'
  if (dayType === 'strength') return 'workout'
  if (dayType === 'rest') return 'today'  // handled inline on Today page
  return 'checkin'
}

// Rotating lighthearted messages for rest/recovery days. Pick one based on
// week number so the same day shows the same message on refresh.
export const REST_DAY_MESSAGES = [
  "Today's job: do absolutely nothing. Expert-level difficulty.",
  "Sofa. Snacks. Smugness. That's the workout.",
  "The best athletes schedule rest. You are now, officially, one of them.",
  "Your muscles are holding a team meeting. Don't interrupt.",
  "Active recovery: walking to the fridge counts if it's uphill.",
  "Nap hard. Hydrate harder. Gains happen in your sleep.",
  "Congrats — today's medal is for restraint.",
  "Rest is a skill. You're practicing. Don't skip practice.",
  "Your legs called. They said please, for the love of god, no.",
  "Foam roll, stretch, sleep. Boring. Effective. Do it.",
]

export function restDayMessage(week, dayOfWeek) {
  const idx = ((week - 1) * 7 + dayOfWeek) % REST_DAY_MESSAGES.length
  return REST_DAY_MESSAGES[idx]
}

export const DAY_TYPE_COLORS = {
  run: 'var(--phase3)',
  'long-run': 'var(--accent)',
  tempo: 'var(--accent2)',
  strength: 'var(--phase1)',
  rest: 'var(--muted)',
}

export function paceToSeconds(paceStr) {
  if (!paceStr) return 0
  try {
    const [m, s] = paceStr.split(':').map(Number)
    return m * 60 + s
  } catch {
    return 0
  }
}

export function secondsToPace(seconds) {
  if (!seconds) return '--'
  return `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`
}
