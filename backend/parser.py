import re
import base64
import os
import sys
from typing import Optional

try:
    import requests as _requests
    REQUESTS_AVAILABLE = True
except ImportError:
    _requests = None
    REQUESTS_AVAILABLE = False


def _log(msg: str):
    """Emit parser progress to stderr so uvicorn shows it without breaking the response."""
    print(f"[parser] {msg}", file=sys.stderr, flush=True)

_PROMPT = (
    "This image is a screenshot of a running workout from Apple Health (or a similar fitness app), "
    "showing a Splits table with per-kilometer rows. Each row has: kilometer index, elapsed time, "
    "pace (like 9'35\"/km or 9:35/km), heart rate in BPM, and power in watts.\n\n"
    "Extract EVERY visible row into a JSON object. Even if some values are partially cut off or hard "
    "to read, still include the row and use your best estimate. Do not return an empty splits array "
    "unless the image truly contains no split data.\n\n"
    "Return a single JSON object matching this exact schema (no markdown, no commentary):\n"
    '{\n'
    '  "splits": [\n'
    '    {"km": 1, "time": "09:35", "pace_per_km": "9:35", "hr_bpm": 142, "power_watts": 155},\n'
    '    {"km": 2, "time": "10:57", "pace_per_km": "10:57", "hr_bpm": 144, "power_watts": 120}\n'
    '  ],\n'
    '  "total_distance_km": 4.0,\n'
    '  "avg_pace": "10:38",\n'
    '  "avg_hr": 144\n'
    "}\n\n"
    "Rules:\n"
    "- time and pace_per_km are strings in mm:ss format (no apostrophes or quotes)\n"
    "- hr_bpm and power_watts are integers\n"
    "- total_distance_km equals the number of full km rows (integer or float)\n"
    "- avg_pace is the arithmetic mean of the per-km paces, in mm:ss\n"
    "- avg_hr is the arithmetic mean of per-km HR, rounded to one decimal\n"
    "- KM indices must be sequential 1..N — do not skip rows"
)


def parse_workout_screenshot(image_path: str, openai_api_key: Optional[str] = None) -> dict:
    """
    Parse workout screenshot from Apple Health using OpenAI vision.

    OCR was previously attempted as a first stage but proved unreliable on Apple
    Health's multi-column dark-theme layout (each column read as a separate
    block, single-character glitches desynced rows). LLM-only is simpler and
    more accurate; cost is negligible for one screenshot per logged run.

    Model is controlled by OPENAI_MODEL env var (default: gpt-5-mini).
    Returns: { splits, avg_pace, avg_hr, total_distance_km, max_hr, avg_power, confidence }
    """
    result = {
        "splits": [],
        "avg_pace": None,
        "avg_hr": None,
        "max_hr": None,
        "avg_power": None,
        "total_distance_km": None,
        "total_time_seconds": None,
        "confidence": "failed",
        "raw_text": ""
    }

    if not openai_api_key:
        _log("No OPENAI_API_KEY set — parser cannot run, returning failed result")
        return result
    if not REQUESTS_AVAILABLE:
        _log("requests package not installed — parser unavailable")
        return result

    try:
        import json
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image_data = base64.b64encode(image_bytes).decode("utf-8")
        ext = os.path.splitext(image_path)[1].lower()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

        model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        _log(f"Calling {model} vision API…")
        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{image_data}"},
                    },
                    {"type": "text", "text": _PROMPT},
                ],
            }],
            # GPT-5 family: reasoning_effort=minimal keeps the response fast
            # and prevents reasoning tokens from eating all the budget.
            "reasoning_effort": "minimal",
            "max_completion_tokens": 2000,
            "response_format": {"type": "json_object"},
        }
        resp = _requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        if not resp.ok:
            _log(f"OpenAI returned HTTP {resp.status_code}: {resp.text[:300]}")
            resp.raise_for_status()
        body = resp.json()
        text = body["choices"][0]["message"]["content"].strip()
        if not text:
            finish = body["choices"][0].get("finish_reason")
            _log(f"OpenAI returned empty content (finish_reason={finish}) — full response: {str(body)[:500]}")
            return result
        if text.startswith("```"):
            text = re.sub(r"```(?:json)?\n?", "", text).strip("`").strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            _log(f"Could not parse JSON from model output: {e}. Raw text: {text[:300]}")
            return result
        splits = parsed.get("splits") or []
        if not splits:
            _log(f"Model returned zero splits. Full JSON: {json.dumps(parsed)[:500]}")
            return result
        result["splits"] = splits
        result["avg_pace"] = parsed.get("avg_pace")
        result["avg_hr"] = parsed.get("avg_hr")
        result["total_distance_km"] = parsed.get("total_distance_km")
        result["confidence"] = "llm"
        _log(f"LLM parse succeeded with {len(splits)} splits")
        _compute_aggregates(result)
        return result
    except Exception as e:
        _log(f"LLM parse error: {type(e).__name__}: {e}")
        return result


_SUMMARY_PROMPT = (
    "This image is a screenshot of an Apple Fitness 'Workout Details' / Summary view "
    "for an outdoor run. Extract the visible fields into a single JSON object.\n\n"
    "Possible visible fields (omit any that aren't visible — do not invent values):\n"
    "- workout_date: the date shown at the top, ISO format YYYY-MM-DD. If only weekday "
    "+ month/day shown (e.g. 'Sun, Apr 26'), assume the current year.\n"
    "- workout_started_at, workout_ended_at: ISO datetimes built from workout_date and "
    "the time range shown (e.g. '06:42-08:02' → start 06:42, end 08:02). Use 24h time.\n"
    "- workout_time_seconds: 'Workout Time' in seconds (e.g. '1:18:20' → 4700).\n"
    "- total_elapsed_seconds: 'Elapsed Time' in seconds. Includes pauses; usually "
    "slightly larger than workout_time_seconds.\n"
    "- location_name: the city/place shown next to the workout name (e.g. 'Gurugram').\n"
    "- distance_km: 'Distance' in kilometers as a float.\n"
    "- active_calories, total_calories: integers (calories).\n"
    "- elevation_gain_m: 'Elevation Gain' in meters (integer or float).\n"
    "- avg_power_watts: 'Avg. Power' in watts.\n"
    "- avg_cadence_spm: 'Avg. Cadence' in steps per minute.\n"
    "- avg_pace: 'Avg. Pace' in mm:ss format (e.g. '11'12\"/km' → '11:12').\n"
    "- avg_hr_bpm: 'Avg. Heart Rate' in bpm.\n"
    "- perceived_effort: integer 1-10 from the 'Effort' badge if shown (e.g. '5 Moderate' → 5).\n\n"
    "Return JSON only (no markdown, no commentary). All keys are optional — omit, "
    "rather than guess, anything not clearly visible."
)


def parse_workout_summary_screenshot(image_path: str, openai_api_key: Optional[str] = None) -> dict:
    """
    Parse the Apple Fitness Workout Summary screen (the screen with totals,
    location, elevation, calories, cadence, effort). Returns a dict with any
    subset of the schema in _SUMMARY_PROMPT — all fields are optional.

    Returns {} on any failure so callers can merge it into the existing parsed
    payload without having to special-case errors.
    """
    if not openai_api_key:
        _log("No OPENAI_API_KEY — summary parser skipped")
        return {}
    if not REQUESTS_AVAILABLE:
        _log("requests not installed — summary parser unavailable")
        return {}

    try:
        import json
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image_data = base64.b64encode(image_bytes).decode("utf-8")
        ext = os.path.splitext(image_path)[1].lower()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

        model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        _log(f"Calling {model} for workout summary…")
        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_data}"}},
                    {"type": "text", "text": _SUMMARY_PROMPT},
                ],
            }],
            "reasoning_effort": "minimal",
            "max_completion_tokens": 800,
            "response_format": {"type": "json_object"},
        }
        resp = _requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {openai_api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        if not resp.ok:
            _log(f"Summary parse HTTP {resp.status_code}: {resp.text[:300]}")
            return {}
        body = resp.json()
        text = body["choices"][0]["message"]["content"].strip()
        if not text:
            _log("Summary parse: empty response")
            return {}
        if text.startswith("```"):
            text = re.sub(r"```(?:json)?\n?", "", text).strip("`").strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            _log(f"Summary parse JSON error: {e}. Raw: {text[:300]}")
            return {}
        # Drop any None / empty-string values so callers can merge cleanly.
        cleaned = {k: v for k, v in parsed.items() if v not in (None, "")}
        _log(f"Summary parse OK — fields: {sorted(cleaned.keys())}")
        return cleaned
    except Exception as e:
        _log(f"Summary parse error: {type(e).__name__}: {e}")
        return {}


def _pace_to_seconds(pace: str) -> Optional[int]:
    """Convert pace string 'mm:ss' to total seconds."""
    try:
        parts = pace.strip().split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        pass
    return None


def _seconds_to_pace(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def _compute_aggregates(result: dict):
    splits = result["splits"]
    if not splits:
        return
    hr_vals = [s["hr_bpm"] for s in splits if s.get("hr_bpm")]
    power_vals = [s["power_watts"] for s in splits if s.get("power_watts")]
    pace_vals = [_pace_to_seconds(s["pace_per_km"]) for s in splits if s.get("pace_per_km")]
    pace_vals = [p for p in pace_vals if p]

    if hr_vals:
        result["avg_hr"] = round(sum(hr_vals) / len(hr_vals), 1)
        result["max_hr"] = max(hr_vals)
    if power_vals:
        result["avg_power"] = round(sum(power_vals) / len(power_vals), 1)
    if pace_vals:
        avg_pace_sec = sum(pace_vals) // len(pace_vals)
        result["avg_pace"] = _seconds_to_pace(avg_pace_sec)
    result["total_distance_km"] = len(splits)
