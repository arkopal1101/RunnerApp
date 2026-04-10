Build a full-stack fitness tracking web app called "Runner". 

## Tech Stack

- Frontend: React + Vite (single page app, static build)
- Backend: FastAPI (Python 3.11)
- Database: SQLite via SQLAlchemy
- Auth: JWT tokens, single user
- Image parsing: regex-first, Gemini Flash API as optional fallback
- Deploy target: HuggingFace Spaces (Docker), free tier

## Project structure

/
├── frontend/          # React + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── PlanViewer.jsx       # Port the existing fitness-plan.html EXACTLY
│   │   │   ├── DailyCheckin.jsx     # Screenshot upload + parsed results
│   │   │   ├── WeeklyLog.jsx        # Body params form
│   │   │   ├── Dashboard.jsx        # Progress charts
│   │   │   └── Login.jsx            # Single user login
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   └── vite.config.js
├── backend/           # FastAPI
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── checkin.py
│   │   ├── weekly.py
│   │   └── progress.py
│   ├── parser.py      # Image parsing logic
│   └── database.py
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md

---

## FEATURE 1: Existing Plan Viewer (PlanViewer.jsx)

Faithfully port the entire fitness-plan.html into React. This file has:

- A hero section with stats
- 4 nav tabs: Overview, Week by Week, Nutrition, Milestones
- Week selector (W1–W32) with full day-by-day detail for Phase 1 (weeks 1–8), daily detail for Phase 2 week 9, and summary blueprints for weeks 10–32
- Color-coded phase system (Phase 1 = blue, 2 = purple, 3 = orange, 4 = yellow)
- All existing CSS variables, fonts (Bebas Neue, DM Sans, DM Mono), and visual design must be preserved exactly
- Clicking week buttons shows that week's content with animation

The full HTML source will be provided as a file called fitness-plan.html. Replicate every single detail.

---

## FEATURE 2: Daily Check-In (screenshot upload)

Route: POST /api/checkin/daily

User uploads a screenshot from Apple Health workout summary (a PNG/JPG showing splits data with km, pace, heart rate, and power columns).

Parser logic (parser.py) — try in order:

1. OCR-free regex parsing: use pytesseract to extract text from the image, then regex to extract:
  - Each km split: split number, time, pace (mm:ss/km), heart rate (bpm), power (watts)
  - Total distance, total time if visible
  - Date/time if visible in status bar
2. If pytesseract fails or confidence is low (fewer than 2 splits extracted), fall back to Gemini Flash API (google-generativeai):
  - Send image as base64
  - Prompt: "Extract workout split data from this Apple Health screenshot. Return JSON only: { date, splits: [{km, time, pace_per_km, hr_bpm, power_watts}], total_distance_km, avg_pace, avg_hr }"
  - Parse JSON response
3. Store raw image file in /data/uploads/ with UUID filename
4. Store parsed JSON in SQLite checkins table

Frontend (DailyCheckin.jsx):

- Drag-and-drop or click-to-upload image area (styled to match existing dark theme)
- Show image preview after upload
- Show parsed results in a split table (matching the existing split analysis style from the plan)
- Allow user to manually edit any parsed field before saving
- Show confirmation with the parsed metrics

---

## FEATURE 3: Weekly Check-In (WeeklyLog.jsx)

Route: POST /api/log/weekly

Form fields:

- Weight (kg) — required
- Waist (inches) — required
- Chest (inches) — optional
- Hips (inches) — optional  
- Body fat % — optional (manual entry)
- Notes — free text, optional
- Week number (auto-detected from current date relative to April 10, 2025 start date, but editable)

Auto-computed fields (show on form, don't ask user):

- BMI (from weight + 5'11" / 180.5cm height, hardcoded)
- Weight change from last week
- Total weight change from start (94kg)

Store in weekly_logs table in SQLite.

---

## FEATURE 4: Progress Dashboard (Dashboard.jsx)

Route: GET /api/progress

Charts (use Recharts library):

1. Weight over time — line chart, show 94kg start line, 80kg target line, actual weekly weights
2. Waist over time — line chart, show 38" start, 32" target
3. Zone 2 pace over time — line chart, plot avg pace per km from each daily check-in, show 10:30 baseline, 7:30 Phase 1 gate, 7:00 Phase 2 gate as reference lines
4. Average HR over time — line chart from check-in data
5. Weekly run volume — bar chart showing total km per week from check-ins
6. Phase progress — show which phase user is in, % progress to phase gate

Dashboard summary cards (top row):

- Current weight vs target
- Runs logged this week
- Latest Z2 pace vs baseline
- Weeks until Phase Gate (calculated)

All charts dark themed matching existing CSS variables. Color scheme matches phase colors.

---

## FEATURE 5: Authentication

Single user system:

- Username: "arko" (hardcoded)
- Password: stored as bcrypt hash in .env file as PASSWORD_HASH
- JWT secret in .env as JWT_SECRET
- Token expiry: 7 days
- All /api/* routes require valid JWT except /api/auth/login
- Frontend stores JWT in localStorage, sends as Bearer token
- Login page matches existing dark theme exactly
- Auto-redirect to dashboard if token valid on app load

Backend auth route: POST /api/auth/login → returns { access_token, token_type }

---

## DATABASE SCHEMA (SQLite)

Table: users

- id, username, password_hash, created_at

Table: daily_checkins

- id, user_id, checkin_date, image_path, raw_text_extracted
- total_distance_km, total_time_seconds, avg_pace_per_km
- avg_hr_bpm, max_hr_bpm, avg_power_watts
- splits_json (JSON string of array)
- week_number (computed from date vs April 10 2025)
- notes, created_at

Table: weekly_logs

- id, user_id, log_date, week_number
- weight_kg, waist_inches, chest_inches, hips_inches
- body_fat_pct, notes, created_at

---

## IMAGE PARSING (parser.py)

Dependencies: pytesseract, Pillow, google-generativeai

```python
def parse_workout_screenshot(image_path: str, gemini_api_key: str = None) -> dict:
    # Step 1: Try pytesseract
    # Step 2: Regex extract splits table
    # Step 3: If < 2 splits found and gemini_api_key set, use Gemini Flash
    # Return: { splits, avg_pace, avg_hr, total_distance, confidence: "ocr"|"llm"|"failed" }
```

The Apple Health screenshot format has columns: split number | Time | Pace | Heart Rate | Power
Example row: "1  09:49  9'49''/km  144BPM  159W"
Regex pattern to target: r'(\d+)\s+(\d+:\d+)\s+(\d+?\d+?/km)\s+(\d+)\s*[Bb][Pp][Mm]\s+(\d+)[Ww]'

---

## DOCKERFILE

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y tesseract-ocr nodejs npm
WORKDIR /app
COPY backend/ ./backend/
COPY frontend/ ./frontend/
RUN pip install fastapi uvicorn sqlalchemy python-jose bcrypt python-multipart pytesseract Pillow google-generativeai
RUN cd frontend && npm install && npm run build
# Serve frontend static files from FastAPI
COPY --from=build /app/frontend/dist /app/static
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

FastAPI should serve the React build from /static at the root route, and all /api/* routes for the backend. Port 7860 is required for HuggingFace Spaces.

---

## .env.example

PASSWORD_HASH=<bcrypt hash of your password>
JWT_SECRET=<random 32 char string>
GEMINI_API_KEY=<optional, leave blank to disable LLM fallback>
DATA_DIR=/data

On HuggingFace Spaces, set these as Repository Secrets (not in the repo).
SQLite db and uploads go to /data/ which persists on HF Spaces paid tier, or use HF Dataset repo as backup storage on free tier.

---

## STYLING REQUIREMENTS
The frontend must use these exact CSS variables and fonts from the original plan:
- Font imports: Bebas Neue, DM Sans (300/400/500/600), DM Mono (400/500) from Google Fonts
- Background: #0a0a0a, Surface: #111111, Surface2: #1a1a1a
- Accent: #e8ff47, Accent2: #ff6b35, Accent3: #47b8ff
- Phase colors: Phase1 #47b8ff, Phase2 #b847ff, Phase3 #ff6b35, Phase4 #e8ff47
- All new components must match this aesthetic exactly

---

## DEPLOYMENT NOTES FOR HUGGINGFACE SPACES
- Space type: Docker
- Port: 7860 (HF requirement)
- README.md must include: title, emoji, colorFrom, colorTo, sdk: docker, app_port: 7860
- Data persistence: free tier has ephemeral storage; add note in README to use HF Dataset repo for SQLite backup
- Environment variables set via HF Space Secrets UI, not committed to repo

Provide a generate_password_hash.py script so Arko can generate his bcrypt hash locally and paste it into HF Secrets.
