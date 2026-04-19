import re
import base64
import os
import sys
from typing import Optional

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

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
    "- avg_hr is the arithmetic mean of per-km HR, rounded to one decimal"
)


def parse_workout_screenshot(image_path: str, openai_api_key: Optional[str] = None) -> dict:
    """
    Parse workout screenshot from Apple Health.
    Step 1: pytesseract OCR + regex (3 strategies, handles multi-column Apple Health layout)
    Step 2: OpenAI vision fallback if OCR yields < 2 splits.
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

    # Step 1: pytesseract OCR
    if TESSERACT_AVAILABLE:
        try:
            img = Image.open(image_path)
            raw_text = pytesseract.image_to_string(img)
            result["raw_text"] = raw_text
            splits = _extract_splits_regex(raw_text)
            if len(splits) >= 2:
                _log(f"OCR succeeded with {len(splits)} splits")
                result["splits"] = splits
                result["confidence"] = "ocr"
                _compute_aggregates(result)
                return result
            _log(f"OCR returned {len(splits)} splits (<2) — falling through to LLM")
        except Exception as e:
            _log(f"OCR failed: {type(e).__name__}: {e}")
    else:
        _log("Tesseract not installed — skipping OCR stage")

    # Step 2: OpenAI vision fallback (default: gpt-5-mini).
    # GPT-5 models burn tokens on internal reasoning before output; we use
    # reasoning_effort=minimal + a generous max_completion_tokens so the
    # visible JSON response actually fits.
    if not openai_api_key:
        _log("No OPENAI_API_KEY set — LLM fallback skipped, marking parse as failed")
        return result
    if not REQUESTS_AVAILABLE:
        _log("requests package not installed — LLM fallback unavailable")
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
        _log(f"LLM fallback error: {type(e).__name__}: {e}")
        return result


def _extract_splits_regex(text: str) -> list:
    """Extract splits from OCR text — tries three strategies."""
    splits = []

    # Strategy 1: all data on one line
    # e.g. "1  09:49  9'49''/km  144BPM  159W"
    pattern = r'(\d+)\s+(\d{1,2}:\d{2})\s+(\d{1,2}[\':]?\d{2}[\'\"]*(?:/km|\'\'\/km)?)\s+(\d{3})\s*[Bb][Pp][Mm]\s+(\d+)\s*[Ww]'
    for m in re.findall(pattern, text):
        splits.append({
            "km": int(m[0]),
            "time": m[1],
            "pace_per_km": m[2].replace("''", '"').replace("'", ":").rstrip("/km").rstrip(":").rstrip('"'),
            "hr_bpm": int(m[3]),
            "power_watts": int(m[4])
        })
    if splits:
        return splits

    # Strategy 2: mm:ss/km on one line
    pattern2 = r'(\d+)\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})/km\s+(\d{3})\s*bpm\s+(\d+)\s*[Ww]'
    for m in re.findall(pattern2, text, re.IGNORECASE):
        splits.append({
            "km": int(m[0]),
            "time": m[1],
            "pace_per_km": m[2],
            "hr_bpm": int(m[3]),
            "power_watts": int(m[4])
        })
    if splits:
        return splits

    # Strategy 3: Apple Health multi-column layout
    # OCR reads each column as a separate block, not row-by-row:
    #   "1 08:38\n2 10:08\n..." then "8'38\"/km\n10'08\"/km\n..." then "142BPM\n..." then "174w\n..."
    splits_times = re.findall(r'^(\d+)\s+(\d{1,2}:\d{2})\s*$', text, re.MULTILINE)
    paces = re.findall(r"(\d{1,2}[':]\d{2})['\"\s./]*/km", text, re.IGNORECASE)
    hrs = re.findall(r'(\d{3})\s*[Bb][Pp][Mm]', text)
    powers = re.findall(r'(\d{1,4})\s*[Ww](?:[^a-zA-Z]|$)', text)
    n = min(len(splits_times), len(paces), len(hrs), len(powers))
    for i in range(n):
        km, time = splits_times[i]
        splits.append({
            "km": int(km),
            "time": time,
            "pace_per_km": paces[i].replace("'", ":").rstrip(":"),
            "hr_bpm": int(hrs[i]),
            "power_watts": int(powers[i])
        })

    return splits


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
