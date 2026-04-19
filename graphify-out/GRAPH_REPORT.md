# Graph Report - .  (2026-04-19)

## Corpus Check
- Corpus is ~45,111 words - fits in a single context window. You may not need a graph.

## Summary
- 595 nodes · 930 edges · 43 communities detected
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 198 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Plan Adjustment System|Plan Adjustment System]]
- [[_COMMUNITY_Coach Metrics Computation|Coach Metrics Computation]]
- [[_COMMUNITY_Authentication & JWT|Authentication & JWT]]
- [[_COMMUNITY_Plan Data Tests|Plan Data Tests]]
- [[_COMMUNITY_Core Data Models|Core Data Models]]
- [[_COMMUNITY_Auth Tests|Auth Tests]]
- [[_COMMUNITY_Parser & Seed Tests|Parser & Seed Tests]]
- [[_COMMUNITY_Plan API Tests|Plan API Tests]]
- [[_COMMUNITY_Integration Tests|Integration Tests]]
- [[_COMMUNITY_Plan Data Building|Plan Data Building]]
- [[_COMMUNITY_Weekly Adjustment|Weekly Adjustment]]
- [[_COMMUNITY_Checkin Processing|Checkin Processing]]
- [[_COMMUNITY_Progress Tracking|Progress Tracking]]
- [[_COMMUNITY_Frontend Components|Frontend Components]]
- [[_COMMUNITY_Baseline Tracking|Baseline Tracking]]
- [[_COMMUNITY_Day Log Routing|Day Log Routing]]
- [[_COMMUNITY_Weekly Log Routing|Weekly Log Routing]]
- [[_COMMUNITY_Coach Notes|Coach Notes]]
- [[_COMMUNITY_Plan Routes|Plan Routes]]
- [[_COMMUNITY_Today Activity|Today Activity]]
- [[_COMMUNITY_CSS Styling|CSS Styling]]
- [[_COMMUNITY_Database Schema|Database Schema]]
- [[_COMMUNITY_Route Handlers|Route Handlers]]
- [[_COMMUNITY_Test Utilities|Test Utilities]]
- [[_COMMUNITY_Type Definitions|Type Definitions]]
- [[_COMMUNITY_API Clients|API Clients]]
- [[_COMMUNITY_Validation|Validation]]
- [[_COMMUNITY_Error Handling|Error Handling]]
- [[_COMMUNITY_Logging|Logging]]
- [[_COMMUNITY_Configuration|Configuration]]
- [[_COMMUNITY_Dependencies|Dependencies]]
- [[_COMMUNITY_Frontend Utils|Frontend Utils]]
- [[_COMMUNITY_Data Processing|Data Processing]]
- [[_COMMUNITY_Weekly Summary|Weekly Summary]]
- [[_COMMUNITY_Baseline Adjustment|Baseline Adjustment]]
- [[_COMMUNITY_Component Rendering|Component Rendering]]
- [[_COMMUNITY_React Hooks|React Hooks]]
- [[_COMMUNITY_State Management|State Management]]
- [[_COMMUNITY_API Responses|API Responses]]
- [[_COMMUNITY_Form Handling|Form Handling]]
- [[_COMMUNITY_Navigation|Navigation]]
- [[_COMMUNITY_Performance|Performance]]
- [[_COMMUNITY_Documentation|Documentation]]

## God Nodes (most connected - your core abstractions)
1. `User` - 73 edges
2. `DailyCheckin` - 61 edges
3. `DayLog` - 18 edges
4. `WeeklyLog` - 17 edges
5. `CoachNote` - 17 edges
6. `PlanAdjustment` - 14 edges
7. `FastAPI Backend Server` - 13 edges
8. `TestDailyCheckin` - 12 edges
9. `TestProgress` - 12 edges
10. `TestWeeklyLog` - 12 edges

## Surprising Connections (you probably didn't know these)
- `React App Root Component` --semantically_similar_to--> `FastAPI JWT Authentication`  [INFERRED] [semantically similar]
  frontend/src/App.jsx → backend/main.py
- `Create or update the 'arko' user on every startup.      Priority:       1. AP` --uses--> `User`  [INFERRED]
  backend\main.py → backend\models.py
- `Merge any PlanAdjustment rows for this user/week into the week's days.     Adju` --uses--> `User`  [INFERRED]
  backend\routes\plan.py → backend\models.py
- `Return today's planned activity with full detail (adjustments merged).` --uses--> `User`  [INFERRED]
  backend\routes\plan.py → backend\models.py
- `Shared fixtures for all tests. Uses an in-memory SQLite DB (StaticPool) so every` --uses--> `User`  [INFERRED]
  tests\conftest.py → backend\models.py

## Hyperedges (group relationships)
- **User Authentication and Data Flow** — login_component, fastapi_dependency_jwt, user_model, seed_user_function [INFERRED 0.75]
- **Run Logging and Tracking Pipeline** — log_run_component, daily_checkin_model, fastapi_router_checkin, coach_note_model [INFERRED 0.75]
- **Progress Tracking and Dashboard System** — dashboard_component, weekly_log_model, daily_checkin_model, fastapi_router_progress [INFERRED 0.70]

## Communities

### Community 0 - "Plan Adjustment System"
Cohesion: 0.06
Nodes (57): Dynamic plan adjuster.  Trigger: after a user saves a weekly log, we re-evalua, Filter LLM output through guardrails, build PlanAdjustment rows, and     replac, Main entry: compute a new batch of adjustments for `user`. Called after     eac, Look up a per-day adjustment. Returns {day: ..., rationale: ...} when an     ad, Return weeks to consider adjusting. Skip race week (untouchable)., Token, Base, Baseline calibration — compute a personal Z2 baseline pace from Week 1 runs and (+49 more)

### Community 1 - "Coach Metrics Computation"
Cohesion: 0.06
Nodes (29): compute_post_run_metrics(), compute_pre_run_metrics(), _format_post_prompt(), _format_pre_prompt(), get_or_create_post_run_note(), get_or_create_pre_run_note(), _llm_generate(), pace_to_seconds() (+21 more)

### Community 2 - "Authentication & JWT"
Cohesion: 0.08
Nodes (27): create_access_token(), login(), verify_password(), calibrate_baseline(), _current_baseline(), get_baseline(), post_run_note(), pre_run_note() (+19 more)

### Community 3 - "Plan Data Tests"
Cohesion: 0.05
Nodes (13): Unit tests for backend/plan_data.py — the single source of truth for the 32-wee, Phase 1 days are ported verbatim from PlanViewer.jsx — sanity-check a few., Week 16 should have the pace test + 18km long run., Week 32 race week: Mon easy, Tue rest, Wed easy, Thu rest, Fri rest, Sat shakeou, Run/long-run/tempo/intervals days should have a distance or duration target;, Every week must build, have 7 days, and every day must have the expected shape., TestAccessors, TestPhase1Content (+5 more)

### Community 4 - "Core Data Models"
Cohesion: 0.09
Nodes (32): React App Root Component, Baseline Pace Calibration, Coach Note Model, Daily Checkin Model, Dashboard Component, Day Log Model, FastAPI JWT Authentication, Auth Router (+24 more)

### Community 5 - "Auth Tests"
Cohesion: 0.07
Nodes (8): Tests for auth: password hashing, JWT creation, login endpoint. These directly g, Token from login must work on a protected route., Windows .env files embed \\r — must not cause Invalid salt., Garbage hash (e.g. env var interpolated away) raises ValueError., The hash must contain $2b$12$ — verifies no $ stripping happens., TestJWT, TestLoginEndpoint, TestVerifyPassword

### Community 6 - "Parser & Seed Tests"
Cohesion: 0.07
Nodes (8): Tests for parser.py — regex extraction and aggregate computation., Ensure seed_user handles env edge cases correctly., Simulate Windows .env CRLF ending., A bad hash should raise ValueError with a useful message, not crash silently., TestComputeAggregates, TestPaceConversions, TestRegexExtraction, TestSeedUser

### Community 7 - "Plan API Tests"
Cohesion: 0.09
Nodes (5): Integration tests for /api/plan/* endpoints.  Covers: - auth enforcement (401, TestPlanAll, TestPlanRouteAuth, TestPlanToday, TestPlanWeek

### Community 8 - "Integration Tests"
Cohesion: 0.13
Nodes (4): TestAutoCompleteOnRunSave, TestBaseline, TestDayLogCreate, TestWorkoutUpload

### Community 9 - "Plan Data Building"
Cohesion: 0.2
Nodes (17): _build_deload_week(), _build_race_week_31(), _build_race_week_32(), _build_standard_week(), _build_week_from_params(), _d(), get_all_weeks(), get_day() (+9 more)

### Community 10 - "Weekly Adjustment"
Cohesion: 0.18
Nodes (16): checkin_to_dict(), daily_checkin(), get_week_number(), list_checkins(), parse_checkin(), update_checkin(), _compute_aggregates(), _extract_splits_regex() (+8 more)

### Community 11 - "Checkin Processing"
Cohesion: 0.2
Nodes (16): _apply_and_store(), _build_user_prompt(), _clamp_distance(), _clamp_pace(), _delete_stale_adjustments(), get_adjusted_day(), _llm_generate_adjustments(), _recent_performance() (+8 more)

### Community 12 - "Progress Tracking"
Cohesion: 0.11
Nodes (6): Tests for the weekly log endpoint., BMI = weight / (1.805^2) = 91.5 / 3.258 ≈ 28.1, Start weight is 94kg; logging 91.5 should show -2.5, Second log delta should reflect change from first log., Week number is auto-computed and should be a positive int., TestWeeklyLog

### Community 13 - "Frontend Components"
Cohesion: 0.19
Nodes (16): _avg_hr(), _avg_pace(), _checkins_in_week(), compute_planned_week(), compute_rings(), compute_weekly_summary(), compute_wow(), _parse_hr_cap() (+8 more)

### Community 14 - "Baseline Tracking"
Cohesion: 0.18
Nodes (4): make_fake_image(), Tests for the daily check-in endpoint., Create a tiny white PNG in memory., TestDailyCheckin

### Community 15 - "Day Log Routing"
Cohesion: 0.13
Nodes (4): png_bytes(), Tests for the progress / dashboard endpoint., Baseline 10:30 = 630s, P1 gate 7:30 = 450s, P2 gate 7:00 = 420s., TestProgress

### Community 16 - "Weekly Log Routing"
Cohesion: 0.12
Nodes (5): Integration tests for the extended /api/today endpoint.  Feature B: /api/today, The pre-existing /api/today contract must still work., TestTodayActivity, TestTodayAuth, TestTodayBackwardsCompat

### Community 17 - "Coach Notes"
Cohesion: 0.22
Nodes (2): DayCard(), DayTypeColor()

### Community 18 - "Plan Routes"
Cohesion: 0.27
Nodes (4): getCurrentWeek(), getDayInfo(), getPhase(), getTodayInfo()

### Community 19 - "Today Activity"
Cohesion: 0.2
Nodes (9): auth_headers(), client(), db(), Shared fixtures for all tests. Uses an in-memory SQLite DB (StaticPool) so every, Drop and recreate all tables before every test for full isolation., A fresh SQLAlchemy session per test., TestClient wired to the in-memory DB.     Seeds the arko user with a known passw, Bearer token for the seeded arko user. (+1 more)

### Community 20 - "CSS Styling"
Cohesion: 0.54
Nodes (7): compute_insights(), compute_phase_gate(), get_current_week(), get_phase(), get_progress(), pace_to_seconds(), weekly_summary()

### Community 21 - "Database Schema"
Cohesion: 0.25
Nodes (0): 

### Community 22 - "Route Handlers"
Cohesion: 0.25
Nodes (0): 

### Community 23 - "Test Utilities"
Cohesion: 0.52
Nodes (6): apiFetch(), apiGet(), apiPost(), apiPut(), apiUrl(), authHeaders()

### Community 24 - "Type Definitions"
Cohesion: 0.4
Nodes (2): getDayLabel(), Today()

### Community 25 - "API Clients"
Cohesion: 0.6
Nodes (1): TestApplyAndStore

### Community 26 - "Validation"
Cohesion: 0.33
Nodes (1): TestWeeklySummaryEndpoint

### Community 27 - "Error Handling"
Cohesion: 0.7
Nodes (4): calcBMI(), getCurrentWeek(), trendMsg(), WeeklyLog()

### Community 28 - "Logging"
Cohesion: 0.6
Nodes (4): deltaStyle(), Row(), signed(), WeekOverWeek()

### Community 29 - "Configuration"
Cohesion: 0.6
Nodes (1): TestWeekOverWeek

### Community 30 - "Dependencies"
Cohesion: 0.83
Nodes (3): _find_images(), main(), _week1_date()

### Community 31 - "Frontend Utils"
Cohesion: 0.5
Nodes (0): 

### Community 32 - "Data Processing"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Weekly Summary"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Baseline Adjustment"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Component Rendering"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "React Hooks"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "State Management"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "API Responses"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Form Handling"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Navigation"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Performance"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Documentation"
Cohesion: 1.0
Nodes (1): Backend Dependencies

## Knowledge Gaps
- **60 isolated node(s):** `Add any declared columns that don't yet exist. Safe to call repeatedly.`, `LLM-generated coaching notes, cached so we don't regenerate on every     page v`, `Tracks per-day completion for any day type (run / strength / rest).     One row`, `Dynamic per-day plan overrides generated by the adjuster service after     each`, `Emit parser progress to stderr so uvicorn shows it without breaking the response` (+55 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Data Processing`** (2 nodes): `App()`, `App.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Weekly Summary`** (2 nodes): `DailyCheckin()`, `DailyCheckin.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Baseline Adjustment`** (2 nodes): `Login.jsx`, `Login()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Component Rendering`** (2 nodes): `LogWorkout.jsx`, `LogWorkout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `React Hooks`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `State Management`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API Responses`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Form Handling`** (1 nodes): `vite.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Navigation`** (1 nodes): `main.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Performance`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Documentation`** (1 nodes): `Backend Dependencies`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Plan Adjustment System` to `Coach Metrics Computation`, `Authentication & JWT`, `Integration Tests`, `Today Activity`, `API Clients`, `Validation`, `Configuration`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `DailyCheckin` connect `Plan Adjustment System` to `Coach Metrics Computation`, `Integration Tests`, `API Clients`, `Validation`, `Configuration`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `TestBaseline` connect `Integration Tests` to `Plan Adjustment System`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 71 inferred relationships involving `User` (e.g. with `Diagnostic: why does login fail?  Run it from the worktree root (where `backen` and `Coach service — generates pre-run target notes and post-run workout summaries.`) actually correct?**
  _`User` has 71 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `DailyCheckin` (e.g. with `Coach service — generates pre-run target notes and post-run workout summaries.` and `Convert 'mm:ss' to total seconds. Returns None on failure.`) actually correct?**
  _`DailyCheckin` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `DayLog` (e.g. with `DayLogCreate` and `Day-level completion tracking: one DayLog row per (user, week, day_of_week).`) actually correct?**
  _`DayLog` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `WeeklyLog` (e.g. with `Generate coaching insights from logged data.` and `Rings (volume/sessions/Z2 adherence) + week-over-week comparison.`) actually correct?**
  _`WeeklyLog` has 15 INFERRED edges - model-reasoned connections that need verification._