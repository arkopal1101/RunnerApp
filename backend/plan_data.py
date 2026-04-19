"""
Single source of truth for the 32-week half-marathon training plan.

Phase 1 (weeks 1-8) and Week 9 are fully authored day-by-day (preserving the
original content from PlanViewer.jsx / fitness-plan.html). Weeks 10-32 are
built from compact per-week parameters that expand into the same 7-day shape.

Each day returned has the shape:
    {
        "name": "Monday",
        "type": "strength" | "run" | "long-run" | "tempo" | "intervals" | "rest",
        "type_label": "Full Body Strength",
        "details": [["Distance", "3 km"], ...],
        "note": "optional string or null",
        "targets": {
            "distance_km": float | None,
            "target_pace": "mm:ss" | "range string" | None,
            "target_hr": "bpm range" | None,
            "duration_min": int | None,
        },
    }

Access functions:
    get_week(week)       -> dict with metadata + days[7]
    get_day(week, dow)   -> single day dict (dow = 0=Mon..6=Sun)
    get_all_weeks()      -> list[dict] for all 32 weeks
"""
from __future__ import annotations

from typing import Optional

PHASE_NAMES = {
    1: "Aerobic Base",
    2: "Build & Recomp",
    3: "Race Specific",
    4: "Peak & Race Ready",
}

DELOAD_WEEKS = {5, 12, 21, 29, 30, 31}
RACE_WEEK = 32

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_phase(week: int) -> int:
    if week <= 8:
        return 1
    if week <= 16:
        return 2
    if week <= 24:
        return 3
    return 4


# --------------------------------------------------------------------------
# Phase 1 focus titles (one per week)
# --------------------------------------------------------------------------
PHASE1_FOCUS = [
    "Foundation — Run Easy, Feel Awkward, That's Fine",
    "Consistency Over Intensity",
    "Zone 2 Lock-In — Every Run Easy",
    "First Long Run Week — 10km Zone 2",
    "Strength Foundation Deepening",
    "Volume Bump — Running Gets Easier",
    "12km Long Run — Progress is Real",
    "Phase 1 Peak — 14km Long Run",
]


# --------------------------------------------------------------------------
# Phase 1 — Weeks 1-8, fully authored (ported verbatim from PlanViewer.jsx)
# --------------------------------------------------------------------------
_PHASE1_DAYS: list[list[dict]] = [
    # Week 1
    [
        {"name": "Monday", "type": "strength", "type_label": "Full Body Strength",
         "details": [["Squats", "3×10"], ["Push-ups", "3×12"], ["Dumbbell Row", "3×10 each"], ["Lunges", "3×12 each"], ["Plank", "3×45s"], ["Core circuit", "10 min"]],
         "note": None,
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
        {"name": "Tuesday", "type": "run", "type_label": "Easy Zone 2 Run",
         "details": [["Distance", "3 km"], ["Target HR", "130–140 bpm — stricter than you think"], ["First 500m", "Embarrassingly slow — let HR settle"], ["Effort", "Full sentences comfortable"]],
         "note": "Your baseline showed HR at 144 in km 1. Start slower than feels right. HR under 140 for the first 500m, then find your cruise.",
         "targets": {"distance_km": 3.0, "target_pace": "10:30-11:00", "target_hr": "130-140", "duration_min": None}},
        {"name": "Wednesday", "type": "rest", "type_label": "Full Rest Day",
         "details": [["Do nothing", "Seriously. Rest."], ["Optional", "20 min gentle walk only"], ["Focus", "Sleep 7–8 hrs, eat well"], ["Why", "Adaptation happens during rest, not training"]],
         "note": "Rest days are not wasted days. Your aerobic base is being built right now while you sleep.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": None}},
        {"name": "Thursday", "type": "strength", "type_label": "Full Body Strength",
         "details": [["Deadlifts", "3×10"], ["Chest Press", "3×12"], ["Pull-ups / Assisted", "3×8"], ["Glute Bridge", "3×15"], ["Russian Twists", "3×20"], ["Dead Bug", "3×10"]],
         "note": None,
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
        {"name": "Friday", "type": "run", "type_label": "Easy Zone 2 Run",
         "details": [["Distance", "4 km"], ["Target HR", "Under 145 strict"], ["Walk trigger", "HR hits 148 → walk until 138, then resume"], ["Focus", "Nasal breathing only"]],
         "note": "Nasal breathing is your HR governor. If you can't breathe through your nose, you're going too fast. Use it religiously in Phase 1.",
         "targets": {"distance_km": 4.0, "target_pace": "10:30-11:00", "target_hr": "<145", "duration_min": None}},
        {"name": "Saturday", "type": "rest", "type_label": "Active Recovery",
         "details": [["Foam roll", "15–20 min — calves, quads, hamstrings"], ["Stretch", "Full body 20 min"], ["Walk", "30 min easy if you feel like it"], ["Sleep", "8+ hrs — long run tomorrow"]],
         "note": "This is not a run day. Foam roll and stretch. Your Sunday long run will be noticeably better for this rest.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 45}},
        {"name": "Sunday", "type": "long-run", "type_label": "Long Run — Zone 2",
         "details": [["Distance", "6 km"], ["Strategy", "Walk-run is not just allowed — it's encouraged"], ["HR cap", "150 bpm absolute max"], ["Pace", "Your baseline is 10:30–11:00/km. That's your starting point."], ["Fuelling", "Water every 20 min"]],
         "note": "6km because your baseline showed cardiac drift at 3.7km. Finishing 6km slow beats quitting 8km.",
         "targets": {"distance_km": 6.0, "target_pace": "10:30-11:00", "target_hr": "<150", "duration_min": None}},
    ],
    # Week 2
    [
        {"name": "Monday", "type": "strength", "type_label": "Full Body Strength",
         "details": [["Squats", "3×12"], ["Push-ups", "3×15"], ["Dumbbell Row", "3×12 each"], ["Reverse Lunges", "3×12 each"], ["Plank", "3×50s"], ["Core circuit", "12 min"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
        {"name": "Tuesday", "type": "run", "type_label": "Easy Zone 2 Run",
         "details": [["Distance", "4 km"], ["Target HR", "130–145 bpm"], ["Cadence", "Aim for ~160–170 spm"], ["Drift check", "Is HR stable across km 2–3? Flatter than Week 1?"]],
         "note": "Compare km splits to your baseline. If HR is drifting less at the same pace, the aerobic base is adapting. That's the win.",
         "targets": {"distance_km": 4.0, "target_pace": "10:30-11:00", "target_hr": "130-145", "duration_min": None}},
        {"name": "Wednesday", "type": "rest", "type_label": "Full Rest Day",
         "details": [["Rest", "No training"], ["Optional", "20 min walk + 15 min stretch"], ["Eat", "Hit your protein target — recovery needs fuel"], ["Sleep", "Prioritize 7–8 hours"]],
         "note": "Two rest days per week is the rule in Phase 1. You're not losing fitness. You're building it.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": None}},
        {"name": "Thursday", "type": "strength", "type_label": "Full Body Strength",
         "details": [["Romanian Deadlift", "3×10"], ["Incline Push-up", "3×12"], ["Pull-ups / Lat Pulldown", "3×10"], ["Single Leg Glute Bridge", "3×12 each"], ["Ab Wheel / Hollow Body", "3×10"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
        {"name": "Friday", "type": "run", "type_label": "Easy Zone 2 Run",
         "details": [["Distance", "5 km"], ["Pace", "Comfortable — HR guided"], ["Focus", "Relax shoulders, arms at 90°"], ["Post", "5 min walking cool-down + stretch"]],
         "note": None, "targets": {"distance_km": 5.0, "target_pace": "10:30-11:00", "target_hr": "130-145", "duration_min": None}},
        {"name": "Saturday", "type": "rest", "type_label": "Active Recovery",
         "details": [["Foam roll", "Calves, IT band, quads — 20 min"], ["Stretch", "Hip flexors, hamstrings, glutes"], ["Walk", "30 min easy optional"], ["Prep", "Eat a banana + good carb dinner for Sunday"]],
         "note": "Long run tomorrow. Eat well tonight. Sleep early. Lay out your kit.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 45}},
        {"name": "Sunday", "type": "long-run", "type_label": "Long Run — 7km Zone 2",
         "details": [["Distance", "7 km"], ["HR cap", "150 bpm"], ["Nutrition", "Banana 45 min before"], ["Hydration", "Water every 20 min"], ["Recovery", "10 min walk + stretch after"]],
         "note": "+1km from last week. This is the progression. Same effort, more distance.",
         "targets": {"distance_km": 7.0, "target_pace": "10:30-11:00", "target_hr": "<150", "duration_min": None}},
    ],
    # Week 3
    [
        {"name": "Monday", "type": "strength", "type_label": "Full Body Strength",
         "details": [["Squats", "4×10"], ["Push-ups", "3×15 or add weight"], ["Bent Row", "3×12"], ["Walking Lunges", "3×12 each"], ["Plank", "3×60s"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
        {"name": "Tuesday", "type": "run", "type_label": "Easy Zone 2 Run",
         "details": [["Distance", "5 km"], ["Focus", "Control breathing, relax shoulders"], ["HR", "Stay under 145"], ["Check", "Should feel easier than Week 1 at same pace"]],
         "note": None, "targets": {"distance_km": 5.0, "target_pace": "10:00-10:30", "target_hr": "<145", "duration_min": None}},
        {"name": "Wednesday", "type": "rest", "type_label": "Full Rest Day",
         "details": [["Rest", "No running, no lifting"], ["Mobility", "20 min hip flexor + calf work if you want"], ["Sleep", "Your legs are adapting right now"]],
         "note": "3 weeks in. Rest is still non-negotiable. The urge to do extra is normal. Resist it in Phase 1.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": None}},
        {"name": "Thursday", "type": "strength", "type_label": "Strength + Mobility Focus",
         "details": [["Deadlifts", "4×8 (add weight from last week)"], ["Pull-ups", "3×max"], ["Hip Flexor Stretch", "3×60s each"], ["Foam Roll", "15 min"], ["Core", "3 heavy sets"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
        {"name": "Friday", "type": "run", "type_label": "Easy Zone 2 Run",
         "details": [["Distance", "5 km"], ["Approach", "First 1km extra slow — warm up properly"], ["Last 0.5km", "Pick up slightly only if HR stays under 145"]],
         "note": None, "targets": {"distance_km": 5.0, "target_pace": "10:00-10:30", "target_hr": "<145", "duration_min": None}},
        {"name": "Saturday", "type": "rest", "type_label": "Active Recovery",
         "details": [["Walk", "30–40 min easy"], ["Stretch", "Full body 20 min"], ["Sleep", "8+ hrs"], ["Eat", "Carb-rich dinner — rice, roti, oats"]],
         "note": "Active recovery Saturday is a permanent fixture. Don't turn this into a training day.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 45}},
        {"name": "Sunday", "type": "long-run", "type_label": "Long Run — 8km Zone 2",
         "details": [["Distance", "8 km"], ["Zone", "Zone 2 the whole way"], ["Fuel", "Water + banana mid-run"], ["Post", "Protein + carb meal within 45 min"]],
         "note": "+1km again. Steady progression. It doesn't matter how slow — you ran 8km.",
         "targets": {"distance_km": 8.0, "target_pace": "10:00-10:30", "target_hr": "<150", "duration_min": None}},
    ],
    # Week 4
    [
        {"name": "Monday", "type": "strength", "type_label": "Full Body Strength",
         "details": [["Back Squat", "4×8 (progressive load)"], ["Push-up Variations", "4×12"], ["Pull-ups", "3×8"], ["Lunges", "3×12"], ["Plank Circuit", "4×45s"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
        {"name": "Tuesday", "type": "run", "type_label": "Easy Zone 2 Run",
         "details": [["Distance", "5 km"], ["HR", "130–145 bpm"], ["Add", "4×100m strides at very end only"]],
         "note": None, "targets": {"distance_km": 5.0, "target_pace": "10:00-10:30", "target_hr": "130-145", "duration_min": None}},
        {"name": "Wednesday", "type": "rest", "type_label": "Full Rest Day",
         "details": [["Rest", "Complete rest"], ["Optional", "20 min gentle walk"], ["Eat", "Hit protein — your muscles are repairing"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": None}},
        {"name": "Thursday", "type": "strength", "type_label": "Strength Focus",
         "details": [["Deadlift", "4×6 (heavy)"], ["DB Row", "4×10"], ["Face Pulls + Band Work", "3×15"], ["Calf Raises", "4×20"], ["Core Strength", "20 min"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
        {"name": "Friday", "type": "run", "type_label": "Easy Zone 2 Run",
         "details": [["Distance", "6 km"], ["Zone 2 strict", "HR under 145"], ["Post", "Stretching 10 min"]],
         "note": None, "targets": {"distance_km": 6.0, "target_pace": "10:00-10:30", "target_hr": "<145", "duration_min": None}},
        {"name": "Saturday", "type": "rest", "type_label": "Active Recovery",
         "details": [["Foam roll", "20 min — focus on calves & quads"], ["Stretch", "Hip flexors, hamstrings"], ["Walk", "Optional 30 min"], ["Carb load", "Rice/roti dinner — long run tomorrow"]],
         "note": "Longest run so far tomorrow. Rest properly today.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 45}},
        {"name": "Sunday", "type": "long-run", "type_label": "Long Run — 10km Zone 2",
         "details": [["Distance", "10 km — first double digits!"], ["Zone", "Zone 2 entire run — walk if HR spikes"], ["Fuel", "Carry water + 2 dates every 30 min"], ["Recovery", "Big protein meal + rest afternoon"]],
         "note": "🏆 First 10km. This is a milestone. It doesn't matter how long it takes.",
         "targets": {"distance_km": 10.0, "target_pace": "10:00-10:30", "target_hr": "<150", "duration_min": None}},
    ],
    # Week 5 — DELOAD
    [
        {"name": "Monday", "type": "rest", "type_label": "Full Rest — Deload Week",
         "details": [["Deload", "Every 4 weeks, back off. This is Week 5."], ["Purpose", "Let the body consolidate gains from Weeks 1–4"], ["Do", "Eat well, sleep lots, foam roll"]],
         "note": "Deload weeks are not optional. This is where your body catches up to the work you've been doing.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": None}},
        {"name": "Tuesday", "type": "run", "type_label": "Easy Zone 2 Run — Deload",
         "details": [["Distance", "4 km"], ["Easy effort", "HR under 140 — even easier than usual"], ["Focus", "Form only — posture, arm swing, cadence"]],
         "note": None, "targets": {"distance_km": 4.0, "target_pace": "9:30-10:00", "target_hr": "<140", "duration_min": None}},
        {"name": "Wednesday", "type": "strength", "type_label": "Full Body (Light Deload)",
         "details": [["Squats", "3×10 at 60% weight"], ["Push-ups", "3×10"], ["Rows", "3×10"], ["Core", "15 min"], ["Mobility", "20 min"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 45}},
        {"name": "Thursday", "type": "rest", "type_label": "Full Rest Day",
         "details": [["Rest", "Complete rest"], ["Sleep", "Prioritise 8+ hours"], ["Walk", "30 min gentle if restless"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": None}},
        {"name": "Friday", "type": "run", "type_label": "Easy Zone 2 Run — Deload",
         "details": [["Distance", "4 km"], ["Very easy", "HR under 135 if possible"], ["Enjoy", "Listen to a podcast, no watch-checking"]],
         "note": None, "targets": {"distance_km": 4.0, "target_pace": "9:30-10:00", "target_hr": "<135", "duration_min": None}},
        {"name": "Saturday", "type": "rest", "type_label": "Active Recovery",
         "details": [["Foam roll", "Full body 20 min"], ["Stretch", "20 min"], ["Sleep", "8+ hrs — long run tomorrow"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 45}},
        {"name": "Sunday", "type": "long-run", "type_label": "Long Run — 10km (Easy Repeat)",
         "details": [["Distance", "10 km — same as last week"], ["Note", "Deload — don't chase pace. This should feel easier."], ["Fuel", "Water + dates/banana"], ["Enjoy", "This is supposed to feel easy. That's the point."]],
         "note": None, "targets": {"distance_km": 10.0, "target_pace": "10:00-10:30", "target_hr": "<145", "duration_min": None}},
    ],
    # Week 6
    [
        {"name": "Monday", "type": "strength", "type_label": "Full Body Strength — Reload",
         "details": [["Back Squats", "4×8 (add 2.5–5kg vs Week 4)"], ["Weighted Push-ups", "4×12"], ["Pull-ups", "4×8"], ["Lunges", "4×12 each"], ["Heavy Core", "20 min"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
        {"name": "Tuesday", "type": "run", "type_label": "Easy Zone 2 Run",
         "details": [["Distance", "6 km"], ["HR", "145 max"], ["Key check", "Compare pace to Week 1. It should be noticeably faster at same HR."]],
         "note": None, "targets": {"distance_km": 6.0, "target_pace": "9:30-10:00", "target_hr": "<145", "duration_min": None}},
        {"name": "Wednesday", "type": "rest", "type_label": "Full Rest Day",
         "details": [["Rest", "No training"], ["Mobility", "15 min optional"], ["Eat", "Protein + carbs — reload week"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": None}},
        {"name": "Thursday", "type": "strength", "type_label": "Deadlift Focus + Upper",
         "details": [["Deadlift", "4×6 (PR attempt from Week 4)"], ["Rows", "4×10"], ["Shoulder Press", "3×10"], ["Core", "20 min heavy"], ["Foam Roll", "15 min"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
        {"name": "Friday", "type": "run", "type_label": "Easy Zone 2 Run",
         "details": [["Distance", "6 km"], ["Zone 2 enforced", "Walk if HR spikes above 147"], ["Post", "Stretching + calf raises"]],
         "note": None, "targets": {"distance_km": 6.0, "target_pace": "9:30-10:00", "target_hr": "<147", "duration_min": None}},
        {"name": "Saturday", "type": "rest", "type_label": "Active Recovery",
         "details": [["Foam roll", "Calves, IT band, quads"], ["Stretch", "Full body"], ["Walk", "Optional 30 min"], ["Sleep", "8+ hrs"]],
         "note": "Biggest long run so far tomorrow — 12km. Rest today.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 45}},
        {"name": "Sunday", "type": "long-run", "type_label": "Long Run — 12km",
         "details": [["Distance", "12 km"], ["This is getting real", "Longest run of the plan so far"], ["Fuel", "Every 30 min: water + 2 dates"], ["Post-run", "1hr rest, big meal, early sleep"]],
         "note": "Start thinking about long run shoes if you haven't already — proper cushioning matters now.",
         "targets": {"distance_km": 12.0, "target_pace": "9:30-10:00", "target_hr": "<150", "duration_min": None}},
    ],
    # Week 7
    [
        {"name": "Monday", "type": "strength", "type_label": "Full Body Strength Heavy",
         "details": [["Squats", "5×5 (heavy)"], ["Bench Press / Push-up", "4×10"], ["Pull-ups", "4×max"], ["Romanian Deadlift", "4×8"], ["Core", "25 min"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 65}},
        {"name": "Tuesday", "type": "run", "type_label": "Easy Zone 2 Run",
         "details": [["Distance", "7 km"], ["Pace check", "What is your avg pace at HR 140–145?"], ["Goal", "Should be under 9:00/km now — big improvement from 10:30"]],
         "note": None, "targets": {"distance_km": 7.0, "target_pace": "8:30-9:30", "target_hr": "140-145", "duration_min": None}},
        {"name": "Wednesday", "type": "rest", "type_label": "Full Rest Day",
         "details": [["Rest", "Complete rest"], ["Optional", "Gentle walk 20 min"], ["Sleep", "8 hrs"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": None}},
        {"name": "Thursday", "type": "strength", "type_label": "Upper Body + Core Heavy",
         "details": [["Deadlift", "4×5 heavy"], ["Row variants", "4×10"], ["Overhead Press", "3×10"], ["Abs heavy", "25 min"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 65}},
        {"name": "Friday", "type": "run", "type_label": "Zone 2 Run + Strides",
         "details": [["Distance", "7 km"], ["Structure", "6km easy + 4×100m strides"], ["Strides", "Controlled pick-up — not a sprint. Fast but relaxed."]],
         "note": None, "targets": {"distance_km": 7.0, "target_pace": "8:30-9:30", "target_hr": "<145", "duration_min": None}},
        {"name": "Saturday", "type": "rest", "type_label": "Active Recovery",
         "details": [["Foam roll", "45 min — full lower body focus"], ["Stretch", "Hip flexors + hamstrings"], ["Sleep", "8+ hours — 13km tomorrow"], ["Carb load", "Good carb dinner tonight"]],
         "note": "13km tomorrow. Sleep well, eat well today. This is the last big effort before Phase Gate week.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
        {"name": "Sunday", "type": "long-run", "type_label": "Long Run — 13km",
         "details": [["Distance", "13 km — nearly a Phase Gate distance"], ["Goal", "Note your pace at comfortable HR"], ["Fuel", "Carry nutrition — fuel every 30 min"], ["Post", "Record avg pace + HR — compare to Week 1 baseline"]],
         "note": None, "targets": {"distance_km": 13.0, "target_pace": "8:30-9:30", "target_hr": "<150", "duration_min": None}},
    ],
    # Week 8 — PHASE 1 GATE
    [
        {"name": "Monday", "type": "strength", "type_label": "Full Body Strength — Final Heavy",
         "details": [["Squats", "5×5"], ["Deadlift", "4×5"], ["Pull-ups", "4×max"], ["Core", "30 min"], ["Note", "Last heavy session before Phase Gate"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 65}},
        {"name": "Tuesday", "type": "run", "type_label": "Zone 2 Pace Test — 5km",
         "details": [["Distance", "5 km"], ["This is a test", "Run at HR 140–145 and record your avg pace"], ["Baseline to beat", "10:30/km (April 10 logged run)"], ["Record", "Time, avg HR, avg pace — this is your Phase 1 report card"]],
         "note": "⚡ Zone 2 pace test. You started at ~10:30/km. If you're now under 8:30/km at the same HR, that's a massive aerobic adaptation in 8 weeks.",
         "targets": {"distance_km": 5.0, "target_pace": "<8:30", "target_hr": "140-145", "duration_min": None}},
        {"name": "Wednesday", "type": "rest", "type_label": "Full Rest Day",
         "details": [["Rest", "Complete rest"], ["Eat", "High carb day — rice, roti, banana, oats"], ["Sleep", "8+ hours"], ["Prep", "Mentally prepare for Sunday Phase Gate"]],
         "note": "Two big days ahead — rest today completely.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": None}},
        {"name": "Thursday", "type": "strength", "type_label": "Light Strength — Prep Week",
         "details": [["Squats", "3×8 (moderate weight only)"], ["Push/Pull", "3×10 light"], ["Core", "20 min"], ["No heavy lifts", "Legs need to be fresh for Sunday"]],
         "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 45}},
        {"name": "Friday", "type": "rest", "type_label": "Full Rest — Pre-Gate",
         "details": [["Rest", "No training at all"], ["Eat", "High carb dinner — carb load for 14km Sunday"], ["Sleep", "8+ hours"], ["Hydrate", "2–3L water throughout the day"]],
         "note": "Carb load day. Eat rice, roti, banana, oats. No skimping. You need fuel for 14km.",
         "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": None}},
        {"name": "Saturday", "type": "run", "type_label": "Short Shakeout — 3km Only",
         "details": [["Distance", "3 km very easy"], ["Purpose", "Loosen legs — not a workout"], ["HR", "Under 130"], ["Duration", "~30 min max"]],
         "note": None, "targets": {"distance_km": 3.0, "target_pace": "9:00-10:00", "target_hr": "<130", "duration_min": 30}},
        {"name": "Sunday", "type": "long-run", "type_label": "🔓 PHASE GATE — 14km Long Run",
         "details": [["Distance", "14 km — Zone 2 the whole way"], ["Target HR", "Under 150 the entire run"], ["Fuel", "Water every 20 min + 3 date/banana portions"], ["Record", "Avg pace, avg HR, total time"], ["Gate check", "Sub 7:30/km at ≤145 bpm = Phase 2 unlocked"]],
         "note": "🔓 PHASE 1 GATE: Complete 14km Zone 2 AND Zone 2 pace under 7:30/km → you move to Phase 2. If not yet, one more week. No rush.",
         "targets": {"distance_km": 14.0, "target_pace": "<7:30", "target_hr": "<145", "duration_min": None}},
    ],
]


# --------------------------------------------------------------------------
# Week 9 — Phase 2 opener, fully authored
# --------------------------------------------------------------------------
_WEEK9_DAYS: list[dict] = [
    {"name": "Monday", "type": "strength", "type_label": "Upper Body Push",
     "details": [["Bench Press / DB Press", "4×10"], ["Shoulder Press", "3×10"], ["Tricep Dips", "3×12"], ["Push-up Finisher", "2×max"], ["Core", "20 min"]],
     "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 55}},
    {"name": "Tuesday", "type": "run", "type_label": "Easy Zone 2 Run",
     "details": [["Distance", "8 km"], ["Phase 2 begins", "Slightly longer easy runs"], ["HR", "Under 145"]],
     "note": None, "targets": {"distance_km": 8.0, "target_pace": "<8:00", "target_hr": "<145", "duration_min": None}},
    {"name": "Wednesday", "type": "rest", "type_label": "Full Rest Day",
     "details": [["Rest", "Complete rest"], ["Optional", "20 min walk + foam roll"], ["Eat", "Hit protein target"]],
     "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": None}},
    {"name": "Thursday", "type": "strength", "type_label": "Lower Body + Core",
     "details": [["Deadlift", "4×6"], ["Romanian DL", "3×8"], ["Hamstring Curl", "3×12"], ["Glute Bridge", "4×15"], ["Core", "20 min"]],
     "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 60}},
    {"name": "Friday", "type": "tempo", "type_label": "First Tempo Run",
     "details": [["Structure", "2km warm-up + 3km tempo + 1km cool-down"], ["Tempo pace", "Uncomfortable but controlled (Zone 4 edge)"], ["HR", "160–175 bpm during tempo"]],
     "note": "⚡ First tempo run of the plan. Your body will hate this. That's fine. Only 3km tempo — don't push beyond that today.",
     "targets": {"distance_km": 6.0, "target_pace": "tempo ~6:30", "target_hr": "160-175", "duration_min": None}},
    {"name": "Saturday", "type": "rest", "type_label": "Active Recovery",
     "details": [["Foam roll", "Full body — you need it after tempo"], ["Stretch", "Focus on calves, hip flexors"], ["Sleep", "8+ hrs for long run"]],
     "note": None, "targets": {"distance_km": None, "target_pace": None, "target_hr": None, "duration_min": 45}},
    {"name": "Sunday", "type": "long-run", "type_label": "Long Run — 15km",
     "details": [["Distance", "15 km — Zone 2"], ["Nutrition", "Fuel every 30 min"], ["Target", "Sub 8:00/km avg"]],
     "note": "You're in Phase 2. Runs get longer, tempo introduced. The rest days still matter — don't skip them.",
     "targets": {"distance_km": 15.0, "target_pace": "<8:00", "target_hr": "<150", "duration_min": None}},
]


# --------------------------------------------------------------------------
# Weeks 10-32 — parameterized (expanded by _build_week_from_params)
# --------------------------------------------------------------------------
# Templates for day-of-week construction. Keys are Mon(0)..Sun(6).
# Each per-week entry supplies these parameters:
#   template: "standard" | "deload" | "race-week-31" | "race-week"
#   phase: 2 | 3 | 4
#   focus: string shown at the top of the week card
#   weight_target: optional int
#   tue_km / tue_label / tue_note (easy run)
#   fri_km / fri_type / fri_label / fri_structure / fri_note
#   sun_km / sun_label / sun_note / sun_pace_target
#   mon_label, thu_label (strength day labels — optional overrides)

_PHASE2_4_PARAMS: dict[int, dict] = {
    10: {
        "phase": 2, "template": "standard", "focus": "Tempo becomes standard — volume builds", "weight_target": 87,
        "mon_label": "Strength — Upper Pull", "thu_label": "Strength — Legs",
        "tue_km": 8.0, "tue_pace": "<8:00",
        "fri_type": "tempo", "fri_km": 4.0, "fri_structure": "1km WU + 2km tempo + 1km CD", "fri_pace": "tempo ~6:30",
        "sun_km": 16.0, "sun_pace": "<7:45", "sun_note": "Compare to Week 9 long run — pace at same effort should be similar or better.",
    },
    11: {
        "phase": 2, "template": "standard", "focus": "Tempo sharpening — push the pace slightly", "weight_target": 86,
        "tue_km": 8.0, "tue_pace": "<7:50",
        "fri_type": "tempo", "fri_km": 4.0, "fri_structure": "1km WU + 2km tempo (faster than W10) + 1km CD", "fri_pace": "tempo ~6:20",
        "sun_km": 16.0, "sun_pace": "<7:40",
    },
    12: {
        "phase": 2, "template": "deload", "focus": "DELOAD — consolidate Weeks 9-11 gains", "weight_target": 86,
        "tue_km": 5.0, "tue_pace": "<8:30",
        "fri_km": 5.0, "fri_pace": "<8:30",
        "sun_km": 14.0, "sun_pace": "<8:00", "sun_note": "Deload long run — easy effort, no pace chasing.",
    },
    13: {
        "phase": 2, "template": "standard", "focus": "Volume bump — 17km long run", "weight_target": 85,
        "tue_km": 9.0, "tue_pace": "<7:45",
        "fri_type": "tempo", "fri_km": 5.0, "fri_structure": "1km WU + 3km tempo + 1km CD", "fri_pace": "tempo ~6:20",
        "sun_km": 17.0, "sun_pace": "<7:30",
    },
    14: {
        "phase": 2, "template": "standard", "focus": "Intervals introduced — VO2 max work", "weight_target": 85,
        "tue_km": 9.0, "tue_pace": "<7:40",
        "fri_type": "intervals", "fri_km": 7.0, "fri_structure": "2km WU + 6×800m @ ~6:00/km (400m jog) + 1km CD", "fri_pace": "intervals ~6:00",
        "fri_note": "First intervals session. Rep pace faster than tempo. Recover fully between reps.",
        "sun_km": 17.0, "sun_pace": "<7:30",
    },
    15: {
        "phase": 2, "template": "standard", "focus": "Peak Phase 2 volume — 18km long run", "weight_target": 84,
        "tue_km": 10.0, "tue_pace": "<7:30",
        "fri_type": "tempo", "fri_km": 6.0, "fri_structure": "1km WU + 4km tempo + 1km CD", "fri_pace": "tempo ~6:10",
        "sun_km": 18.0, "sun_pace": "<7:20",
    },
    16: {
        "phase": 2, "template": "standard", "focus": "⚡ PHASE 2 GATE — pace test + 18km long run", "weight_target": 84,
        "mon_label": "Light Strength — Prep", "thu_label": "Light Strength — Prep",
        "tue_km": 5.0, "tue_label": "Zone 2 Pace Test — 5km",
        "tue_pace": "<7:00", "tue_note": "⚡ Pace test. Hold HR 140-145 and record avg pace. Sub 7:00/km unlocks Phase 3.",
        "fri_type": "tempo", "fri_km": 5.0, "fri_structure": "1km WU + 3km tempo + 1km CD", "fri_pace": "tempo ~6:00",
        "sun_km": 18.0, "sun_pace": "<7:15",
        "sun_note": "🔓 PHASE 2 GATE: 18km completed + Zone 2 pace sub 7:00/km → Phase 3 unlocked.",
    },
    17: {
        "phase": 3, "template": "standard", "focus": "Peak volume begins — 19km long run", "weight_target": 83,
        "mon_label": "Strength 2× — Lower", "thu_label": "Strength 2× — Upper",
        "tue_km": 10.0, "tue_pace": "<7:15",
        "fri_type": "tempo", "fri_km": 7.0, "fri_structure": "2km WU + 4km tempo + 1km CD", "fri_pace": "tempo ~5:55",
        "sun_km": 19.0, "sun_pace": "<7:10",
    },
    18: {
        "phase": 3, "template": "standard", "focus": "Race pace sharpening — 800m intervals", "weight_target": 82,
        "mon_label": "Strength 2× — Lower", "thu_label": "Strength 2× — Upper",
        "tue_km": 10.0, "tue_pace": "<7:15",
        "fri_type": "intervals", "fri_km": 9.0, "fri_structure": "2km WU + 8×800m @ ~5:50/km (400m jog) + 1km CD", "fri_pace": "intervals ~5:50",
        "sun_km": 19.0, "sun_pace": "<7:10",
    },
    19: {
        "phase": 3, "template": "standard", "focus": "🏆 First 20km long run!", "weight_target": 82,
        "tue_km": 10.0, "tue_pace": "<7:10",
        "fri_type": "tempo", "fri_km": 7.0, "fri_structure": "2km WU + 4km tempo + 1km CD", "fri_pace": "tempo ~5:55",
        "sun_km": 20.0, "sun_pace": "<7:10",
        "sun_note": "🏆 First 20km. Fuel every 25 min. Don't race it — execute it.",
    },
    20: {
        "phase": 3, "template": "standard", "focus": "⚡ PEAK WEEK — highest volume (~55-60km)", "weight_target": 81,
        "tue_km": 10.0, "tue_pace": "<7:10",
        "fri_type": "tempo", "fri_km": 8.0, "fri_structure": "2km WU + 5km tempo + 1km CD", "fri_pace": "tempo ~5:50",
        "sun_km": 20.0, "sun_pace": "<7:05",
        "sun_note": "Peak volume week. After this, long runs start tapering while intensity stays high.",
    },
    21: {
        "phase": 3, "template": "deload", "focus": "DELOAD — absorb peak volume", "weight_target": 81,
        "tue_km": 8.0, "tue_pace": "<7:30",
        "fri_km": 8.0, "fri_pace": "<7:30",
        "sun_km": 16.0, "sun_pace": "<7:45",
        "sun_note": "Deload after peak. Easy effort. You've earned it.",
    },
    22: {
        "phase": 3, "template": "standard", "focus": "Short intervals — leg speed", "weight_target": 80,
        "tue_km": 10.0, "tue_pace": "<7:05",
        "fri_type": "intervals", "fri_km": 8.0, "fri_structure": "2km WU + 10×400m @ ~5:30/km (200m jog) + 1km CD", "fri_pace": "intervals ~5:30",
        "sun_km": 19.0, "sun_pace": "<7:05",
    },
    23: {
        "phase": 3, "template": "standard", "focus": "Race simulation — tempo at target pace", "weight_target": 80,
        "tue_km": 10.0, "tue_pace": "<7:05",
        "fri_type": "tempo", "fri_km": 8.0, "fri_structure": "2km WU + 5km @ race pace (7:06/km) + 1km CD", "fri_pace": "race ~7:06",
        "fri_note": "Tempo at your target race pace (7:06/km = sub 2:30 finish). Lock it in.",
        "sun_km": 20.0, "sun_pace": "<7:05",
    },
    24: {
        "phase": 3, "template": "standard", "focus": "⚡ PHASE 3 GATE — race simulation", "weight_target": 80,
        "mon_label": "Light Strength — Maintenance", "thu_label": "Rest / Easy",
        "tue_km": 8.0, "tue_pace": "<7:15",
        "fri_type": "easy", "fri_km": 6.0, "fri_pace": "<7:30",
        "sun_km": 20.0, "sun_label": "Long Run — Race Simulation 20km", "sun_pace": "~7:06 (race pace)",
        "sun_note": "🔓 PHASE 3 GATE: 20km at/near target race pace. If this feels controlled, Phase 4 is refinement only.",
    },
    25: {
        "phase": 4, "template": "standard", "focus": "Phase 4 begins — race-specific refinement", "weight_target": 80,
        "mon_label": "Light Strength 1× — Maintenance",
        "thu_label": "Easy Run (added)", "thu_override_type": "run", "thu_km": 8.0, "thu_pace": "<7:15",
        "tue_km": 8.0, "tue_pace": "<7:15",
        "fri_type": "tempo", "fri_km": 6.0, "fri_structure": "1km WU + 4km tempo + 1km CD", "fri_pace": "tempo ~6:00",
        "sun_km": 18.0, "sun_pace": "<7:10",
    },
    26: {
        "phase": 4, "template": "standard", "focus": "10km tune-up race option / easy long run", "weight_target": 80,
        "mon_label": "Light Strength 1×",
        "thu_override_type": "run", "thu_label": "Easy Run", "thu_km": 6.0, "thu_pace": "<7:30",
        "tue_km": 8.0, "tue_pace": "<7:15",
        "fri_type": "tempo", "fri_km": 10.0, "fri_label": "10km Tune-Up (race or time trial)", "fri_structure": "If race available, run it. Otherwise 2km WU + 6km @ race pace + 2km CD.", "fri_pace": "race ~7:00",
        "fri_note": "Optional 10km tune-up race. Trusted pace check before race week.",
        "sun_km": 16.0, "sun_pace": "<7:20", "sun_label": "Easy Long Run — 16km",
    },
    27: {
        "phase": 4, "template": "standard", "focus": "Nail race nutrition — full rehearsal", "weight_target": 80,
        "mon_label": "Light Strength 1×",
        "thu_override_type": "run", "thu_label": "Easy Run", "thu_km": 8.0, "thu_pace": "<7:15",
        "tue_km": 8.0, "tue_pace": "<7:15",
        "fri_type": "tempo", "fri_km": 6.0, "fri_structure": "1km WU + 4km tempo + 1km CD", "fri_pace": "tempo ~6:00",
        "sun_km": 18.0, "sun_pace": "<7:10",
        "sun_note": "Rehearse race nutrition today. Gels, dates, water — exactly what you'll use on race day.",
    },
    28: {
        "phase": 4, "template": "standard", "focus": "1km race pace intervals — final sharpening", "weight_target": 80,
        "mon_label": "Light Strength 1×",
        "thu_override_type": "intervals", "thu_label": "Race Pace Intervals", "thu_km": 9.0,
        "thu_structure": "2km WU + 6×1km @ race pace (7:06/km) + 1km CD", "thu_pace": "race ~7:06",
        "tue_km": 8.0, "tue_pace": "<7:15",
        "fri_type": "rest", "fri_label": "Full Rest",
        "sun_km": 16.0, "sun_pace": "<7:15",
        "sun_note": "Last big-ish long run before taper begins.",
    },
    29: {
        "phase": 4, "template": "deload", "focus": "TAPER begins — volume -25%", "weight_target": 79,
        "tue_km": 7.0, "tue_pace": "<7:15",
        "fri_km": 5.0, "fri_type": "tempo", "fri_structure": "1km WU + 3km tempo + 1km CD", "fri_pace": "tempo ~6:00",
        "sun_km": 14.0, "sun_pace": "<7:15",
        "sun_note": "Taper weeks will feel slow. Trust the process.",
    },
    30: {
        "phase": 4, "template": "deload", "focus": "TAPER — volume -40%", "weight_target": 79,
        "tue_km": 6.0, "tue_pace": "<7:15",
        "fri_km": 4.0, "fri_type": "tempo", "fri_structure": "1km WU + 2km tempo + 1km CD", "fri_pace": "tempo ~6:00",
        "sun_km": 12.0, "sun_pace": "<7:15",
    },
    31: {
        "phase": 4, "template": "race-week-31", "focus": "TAPER — final week before race", "weight_target": 79,
    },
    32: {
        "phase": 4, "template": "race-week", "focus": "🏁 RACE WEEK — YOU'VE MADE IT", "weight_target": 79,
    },
}


# --------------------------------------------------------------------------
# Builders
# --------------------------------------------------------------------------
def _d(name, dtype, label, details, note=None, distance=None, pace=None, hr=None, duration=None):
    return {
        "name": name, "type": dtype, "type_label": label,
        "details": details, "note": note,
        "targets": {"distance_km": distance, "target_pace": pace, "target_hr": hr, "duration_min": duration},
    }


def _build_standard_week(week: int, p: dict) -> list[dict]:
    phase = p["phase"]
    mon_label = p.get("mon_label", "Strength — Push/Pull/Legs" if phase == 2 else "Light Strength" if phase == 4 else "Strength 2×")
    thu_label = p.get("thu_label", "Strength — Push/Pull/Legs" if phase == 2 else "Light Strength" if phase == 4 else "Strength 2×")
    tue_km = p["tue_km"]
    tue_pace = p["tue_pace"]
    tue_label = p.get("tue_label", f"Easy Zone 2 Run — {tue_km:g}km")
    tue_note = p.get("tue_note")
    fri_type = p["fri_type"]
    fri_km = p.get("fri_km")
    fri_pace = p.get("fri_pace")
    fri_structure = p.get("fri_structure")
    fri_note = p.get("fri_note")
    if p.get("fri_label"):
        fri_label = p["fri_label"]
    elif fri_type == "tempo":
        fri_label = f"Tempo Run — {fri_km:g}km"
    elif fri_type == "intervals":
        fri_label = f"Intervals — {fri_km:g}km"
    elif fri_type == "easy":
        fri_label = f"Easy Run — {fri_km:g}km"
    elif fri_type == "rest":
        fri_label = "Full Rest"
    else:
        fri_label = "Run"
    sun_km = p["sun_km"]
    sun_pace = p["sun_pace"]
    sun_label = p.get("sun_label", f"Long Run — {sun_km:g}km")
    sun_note = p.get("sun_note")

    # Monday — Strength (or overridden)
    mon = _d("Monday", "strength", mon_label,
             [["Lower body", "Squat/Deadlift variants"], ["Upper body", "Push/Pull work"], ["Core", "15-20 min"], ["Volume", "45-60 min total"]],
             duration=50 if phase == 4 else 60)

    # Tuesday — Easy run
    tue_details = [["Distance", f"{tue_km:g} km"], ["Target HR", "130-145 bpm"], ["Target pace", tue_pace]]
    if p.get("tue_extra"):
        tue_details.append(p["tue_extra"])
    tue = _d("Tuesday", "run", tue_label, tue_details, note=tue_note,
             distance=tue_km, pace=tue_pace, hr="130-145")

    # Wednesday — Rest
    wed = _d("Wednesday", "rest", "Full Rest Day",
             [["Rest", "No training"], ["Sleep", "8+ hrs"], ["Eat", "Hit protein + carbs"]],
             note=None)

    # Thursday — Strength, or run/intervals if overridden
    thu_type_override = p.get("thu_override_type")
    if thu_type_override == "run":
        thu_km = p["thu_km"]
        thu_pace = p["thu_pace"]
        thu = _d("Thursday", "run", p.get("thu_label", f"Easy Run — {thu_km:g}km"),
                 [["Distance", f"{thu_km:g} km"], ["Pace", thu_pace], ["HR", "<145"]],
                 distance=thu_km, pace=thu_pace, hr="<145")
    elif thu_type_override == "intervals":
        thu = _d("Thursday", "intervals", p.get("thu_label", "Intervals"),
                 [["Distance", f"{p['thu_km']:g} km"], ["Structure", p["thu_structure"]], ["Pace", p["thu_pace"]]],
                 distance=p["thu_km"], pace=p["thu_pace"], hr="race pace")
    else:
        thu = _d("Thursday", "strength", thu_label,
                 [["Focus", "Heavy compound lifts"], ["Core", "20 min"], ["Volume", "45-60 min total"]],
                 duration=50 if phase == 4 else 60)

    # Friday — Tempo / Intervals / Easy / Rest
    if fri_type == "rest":
        fri = _d("Friday", "rest", fri_label,
                 [["Rest", "No training"], ["Hydrate", "Water + electrolytes"]],
                 note=fri_note)
    else:
        # Map builder-level type into the normalized day type
        day_type = {"tempo": "tempo", "intervals": "intervals", "easy": "run"}.get(fri_type, "run")
        fri_details = [["Distance", f"{fri_km:g} km"]]
        if fri_structure:
            fri_details.append(["Structure", fri_structure])
        if fri_type == "tempo":
            fri_details.append(["HR", "160-175 bpm during tempo"])
        elif fri_type == "intervals":
            fri_details.append(["HR", "170-180 during reps"])
        else:
            fri_details.append(["HR", "<145"])
        fri_details.append(["Pace target", fri_pace])
        fri = _d("Friday", day_type, fri_label, fri_details, note=fri_note,
                 distance=fri_km, pace=fri_pace,
                 hr="160-175" if fri_type == "tempo" else "170-180" if fri_type == "intervals" else "<145")

    # Saturday — Active Recovery
    sat = _d("Saturday", "rest", "Active Recovery",
             [["Foam roll", "20 min"], ["Stretch", "15-20 min"], ["Walk", "Optional 30 min"], ["Prep", "Eat well, sleep early — long run tomorrow"]],
             note="Long run tomorrow — rest today.", duration=45)

    # Sunday — Long Run
    sun = _d("Sunday", "long-run", sun_label,
             [["Distance", f"{sun_km:g} km"], ["Target pace", sun_pace], ["HR cap", "<150 bpm"], ["Fuel", "Water + dates/gels every 25-30 min"]],
             note=sun_note, distance=sun_km, pace=sun_pace, hr="<150")

    return [mon, tue, wed, thu, fri, sat, sun]


def _build_deload_week(week: int, p: dict) -> list[dict]:
    tue_km = p["tue_km"]
    tue_pace = p["tue_pace"]
    fri_km = p["fri_km"]
    fri_pace = p["fri_pace"]
    fri_type = p.get("fri_type", "run")
    fri_structure = p.get("fri_structure")
    sun_km = p["sun_km"]
    sun_pace = p["sun_pace"]
    sun_note = p.get("sun_note", "Deload long run — easy effort, no pace chasing.")

    mon = _d("Monday", "rest", "Full Rest — Deload",
             [["Deload week", "Consolidate prior block's gains"], ["Sleep", "8+ hrs"], ["Mobility", "Optional 20 min"]],
             note="Deload is not optional.")

    tue = _d("Tuesday", "run", f"Easy Run — Deload {tue_km:g}km",
             [["Distance", f"{tue_km:g} km"], ["Effort", "Very easy"], ["HR", "<140"], ["Pace", tue_pace]],
             distance=tue_km, pace=tue_pace, hr="<140")

    wed = _d("Wednesday", "strength", "Light Strength — Deload",
             [["Compound lifts", "3×8 at 60% weight"], ["Volume", "40 min max"], ["Focus", "Form over load"]],
             duration=40)

    thu = _d("Thursday", "rest", "Full Rest Day",
             [["Rest", "Complete rest"], ["Sleep", "8+ hrs"]],
             note=None)

    if fri_type == "tempo":
        fri = _d("Friday", "tempo", f"Light Tempo — {fri_km:g}km",
                 [["Distance", f"{fri_km:g} km"], ["Structure", fri_structure or "Short tempo"], ["HR", "150-165 (capped for deload)"], ["Pace", fri_pace]],
                 distance=fri_km, pace=fri_pace, hr="150-165")
    else:
        fri = _d("Friday", "run", f"Easy Run — Deload {fri_km:g}km",
                 [["Distance", f"{fri_km:g} km"], ["Effort", "Very easy"], ["HR", "<140"], ["Pace", fri_pace]],
                 distance=fri_km, pace=fri_pace, hr="<140")

    sat = _d("Saturday", "rest", "Active Recovery",
             [["Foam roll", "20 min"], ["Stretch", "15 min"], ["Sleep", "8+ hrs"]],
             duration=45)

    sun = _d("Sunday", "long-run", f"Long Run — Deload {sun_km:g}km",
             [["Distance", f"{sun_km:g} km"], ["Pace", sun_pace], ["Effort", "Easy — do not race this"], ["HR cap", "<145"]],
             note=sun_note, distance=sun_km, pace=sun_pace, hr="<145")

    return [mon, tue, wed, thu, fri, sat, sun]


def _build_race_week_31() -> list[dict]:
    """Week 31 taper — volume way down, leg freshness priority."""
    return [
        _d("Monday", "run", "Easy 5km", [["Distance", "5 km"], ["Effort", "Very easy, legs loose"], ["HR", "<140"]], distance=5.0, pace="<7:15", hr="<140"),
        _d("Tuesday", "rest", "Full Rest Day", [["Rest", "Complete rest"], ["Sleep", "8+ hrs"]]),
        _d("Wednesday", "run", "Easy 5km", [["Distance", "5 km"], ["Effort", "Very easy"], ["HR", "<140"]], distance=5.0, pace="<7:15", hr="<140"),
        _d("Thursday", "rest", "Full Rest Day", [["Rest", "Complete rest"]]),
        _d("Friday", "run", "Shakeout 3km", [["Distance", "3 km"], ["Effort", "Loosen legs, nothing more"], ["HR", "<135"]], distance=3.0, pace="<7:30", hr="<135"),
        _d("Saturday", "rest", "Rest — Carb Load Begins", [["Carbs", "Rice, roti, pasta, oats"], ["Sleep", "8+ hrs"], ["Hydrate", "Extra water"]],
           note="Carb load for Sunday's final long run."),
        _d("Sunday", "long-run", "Easy Long Run — 10km", [["Distance", "10 km"], ["Pace", "Very easy"], ["Note", "Last meaningful long run before race"]],
           note="Last 10km before race week. Easy effort only.", distance=10.0, pace="<7:20", hr="<145"),
    ]


def _build_race_week_32() -> list[dict]:
    """Week 32 — Race Week. Sunday is RACE DAY (half marathon)."""
    return [
        _d("Monday", "run", "Easy 3km", [["Distance", "3 km"], ["Effort", "Loosen legs"], ["HR", "<135"]], distance=3.0, pace="<7:30", hr="<135"),
        _d("Tuesday", "rest", "Full Rest Day", [["Rest", "Complete rest"], ["Sleep", "8+ hrs"]]),
        _d("Wednesday", "run", "Easy 3km", [["Distance", "3 km"], ["Effort", "Very easy shakeout"], ["HR", "<135"]], distance=3.0, pace="<7:30", hr="<135"),
        _d("Thursday", "rest", "Full Rest Day", [["Rest", "Complete rest"], ["Mental prep", "Visualize race day"]]),
        _d("Friday", "rest", "Rest + Carb Load", [["Carbs", "Rice, pasta, oats, banana"], ["Hydrate", "3L water"], ["Sleep", "8+ hrs early"]],
           note="No training. Eat, sleep, prepare kit."),
        _d("Saturday", "run", "Shakeout 2km", [["Distance", "2 km"], ["Effort", "Just loosen legs — 15-20 min total"], ["Prep", "Lay out race kit, eat early dinner"]],
           distance=2.0, pace="<7:30", hr="<130"),
        _d("Sunday", "long-run", "🏁 RACE DAY — HALF MARATHON",
           [["Distance", "21.1 km"], ["Target pace", "~7:06/km = sub 2:30 finish"], ["Target HR", "Controlled — don't red-line early"], ["Fuel", "Gels/dates every 5km + water each aid station"], ["Strategy", "First 5km: settle. 5-15km: lock pace. 15-21km: all of it."]],
           note="🏁 Race day. You've trained 32 weeks for this. Execute, don't race someone else's race.",
           distance=21.1, pace="~7:06", hr="race effort"),
    ]


def _build_week_from_params(week: int, params: dict) -> list[dict]:
    tpl = params["template"]
    if tpl == "standard":
        return _build_standard_week(week, params)
    if tpl == "deload":
        return _build_deload_week(week, params)
    if tpl == "race-week-31":
        return _build_race_week_31()
    if tpl == "race-week":
        return _build_race_week_32()
    raise ValueError(f"Unknown template {tpl} for week {week}")


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def get_week_focus(week: int) -> str:
    if 1 <= week <= 8:
        return PHASE1_FOCUS[week - 1]
    if week == 9:
        return "Phase 2 opens — tempo runs introduced, runs get longer"
    if week in _PHASE2_4_PARAMS:
        return _PHASE2_4_PARAMS[week].get("focus", "")
    return ""


def get_days_for_week(week: int) -> list[dict]:
    if 1 <= week <= 8:
        return _PHASE1_DAYS[week - 1]
    if week == 9:
        return _WEEK9_DAYS
    if week in _PHASE2_4_PARAMS:
        return _build_week_from_params(week, _PHASE2_4_PARAMS[week])
    return []


def get_week(week: int) -> dict:
    """Return full week spec: metadata + 7 days."""
    week = max(1, min(32, int(week)))
    phase = get_phase(week)
    days = get_days_for_week(week)
    return {
        "week": week,
        "phase": phase,
        "phase_name": PHASE_NAMES[phase],
        "focus": get_week_focus(week),
        "is_deload": week in DELOAD_WEEKS,
        "is_race_week": week == RACE_WEEK,
        "days": days,
    }


def get_day(week: int, day_of_week: int) -> Optional[dict]:
    """Return one day's activity. day_of_week: 0=Mon..6=Sun."""
    days = get_days_for_week(week)
    if 0 <= day_of_week < len(days):
        return days[day_of_week]
    return None


def get_all_weeks() -> list[dict]:
    return [get_week(w) for w in range(1, 33)]
