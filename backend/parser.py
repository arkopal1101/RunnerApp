import re
import base64
import os
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

_PROMPT = (
    'Extract workout split data from this Apple Health / fitness app screenshot. '
    'Return JSON only, no markdown, no explanation: '
    '{ "splits": [{"km": 1, "time": "08:38", "pace_per_km": "8:38", "hr_bpm": 142, "power_watts": 174}], '
    '"total_distance_km": 4.5, "avg_pace": "10:06", "avg_hr": 146 }'
)


def parse_workout_screenshot(image_path: str, openai_api_key: Optional[str] = None) -> dict:
    """
    Parse workout screenshot from Apple Health.
    Step 1: pytesseract OCR + regex (3 strategies, handles multi-column Apple Health layout)
    Step 2: OpenAI gpt-4o-mini vision fallback if OCR yields < 2 splits
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
                result["splits"] = splits
                result["confidence"] = "ocr"
                _compute_aggregates(result)
                return result
        except Exception:
            pass

    # Step 2: OpenAI gpt-4o-mini vision
    if openai_api_key and REQUESTS_AVAILABLE:
        try:
            import json
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            image_data = base64.b64encode(image_bytes).decode("utf-8")
            ext = os.path.splitext(image_path)[1].lower()
            mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

            resp = _requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
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
                    "max_tokens": 600,
                },
                timeout=30,
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()
            if text.startswith("```"):
                text = re.sub(r"```(?:json)?\n?", "", text).strip("`").strip()
            parsed = json.loads(text)
            result["splits"] = parsed.get("splits", [])
            result["avg_pace"] = parsed.get("avg_pace")
            result["avg_hr"] = parsed.get("avg_hr")
            result["total_distance_km"] = parsed.get("total_distance_km")
            result["confidence"] = "llm"
            _compute_aggregates(result)
            return result
        except Exception:
            pass

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
