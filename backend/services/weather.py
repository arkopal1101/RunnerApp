"""
Open-Meteo wrapper — geocodes a place name and fetches historical hourly
weather for the workout's start hour. No API key, free, generous rate limits.

Both functions are best-effort: they return None on any failure so callers
can degrade gracefully (the coach just operates without weather context).

Geocoding results are cached process-locally for 7 days because city
coordinates effectively never change.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime
from typing import Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False


def _log(msg: str):
    print(f"[weather] {msg}", file=sys.stderr, flush=True)


# In-memory geocode cache: name -> (lat, lon, resolved_name, expires_at)
_GEOCODE_CACHE: dict[str, tuple[float, float, str, float]] = {}
_GEOCODE_TTL_SECONDS = 7 * 24 * 3600


def geocode(name: str) -> Optional[tuple[float, float, str]]:
    """
    Resolve a place name to (lat, lon, resolved_name). Returns None if the
    lookup fails or no result is found.

    resolved_name is the full Open-Meteo display string (e.g.
    "Gurugram, Haryana, India") so the user can tell which match was picked.
    """
    if not name or not REQUESTS_AVAILABLE:
        return None

    key = name.strip().lower()
    now = time.time()
    cached = _GEOCODE_CACHE.get(key)
    if cached and cached[3] > now:
        return (cached[0], cached[1], cached[2])

    try:
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": name.strip(), "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        if not resp.ok:
            _log(f"geocode HTTP {resp.status_code} for {name!r}")
            return None
        data = resp.json()
        results = data.get("results") or []
        if not results:
            _log(f"geocode: no results for {name!r}")
            return None
        r = results[0]
        lat, lon = r.get("latitude"), r.get("longitude")
        parts = [r.get("name"), r.get("admin1"), r.get("country")]
        resolved = ", ".join(p for p in parts if p)
        if lat is None or lon is None:
            return None
        _GEOCODE_CACHE[key] = (float(lat), float(lon), resolved, now + _GEOCODE_TTL_SECONDS)
        return (float(lat), float(lon), resolved)
    except Exception as e:
        _log(f"geocode error for {name!r}: {type(e).__name__}: {e}")
        return None


def fetch_historical_weather(lat: float, lon: float, started_at: str) -> Optional[dict]:
    """
    Fetch hourly weather for the date+hour of `started_at` (ISO datetime).
    Returns a dict with the fields below, or None on failure.

    Picks the hourly bucket whose hour matches the workout's local start
    hour. Open-Meteo's `timezone=auto` makes the returned series local to
    the requested coordinates so the hour index lines up with the
    `started_at` we received from the screenshot.

    Returns:
      {
        "temperature_c": float,
        "apparent_temperature_c": float,
        "humidity_pct": int,
        "wind_speed_kmh": float,
        "precipitation_mm": float,
        "weather_code": int,
      }
    """
    if not REQUESTS_AVAILABLE or lat is None or lon is None or not started_at:
        return None

    try:
        dt = datetime.fromisoformat(started_at)
    except ValueError:
        _log(f"bad started_at {started_at!r}")
        return None

    date_str = dt.date().isoformat()
    hour = dt.hour

    try:
        resp = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": date_str,
                "end_date": date_str,
                "hourly": ",".join([
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "wind_speed_10m",
                    "weather_code",
                ]),
                "timezone": "auto",
            },
            timeout=15,
        )
        if not resp.ok:
            _log(f"archive HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        data = resp.json()
        hourly = data.get("hourly") or {}
        times = hourly.get("time") or []
        if not times:
            _log("archive: empty hourly series")
            return None

        # Find the index whose hour matches the workout start.
        idx = None
        for i, t in enumerate(times):
            try:
                if datetime.fromisoformat(t).hour == hour:
                    idx = i
                    break
            except ValueError:
                continue
        if idx is None:
            idx = 0  # fall back to the first hour available

        def _get(key: str):
            arr = hourly.get(key) or []
            return arr[idx] if 0 <= idx < len(arr) else None

        temp = _get("temperature_2m")
        humidity = _get("relative_humidity_2m")
        apparent = _get("apparent_temperature")
        precip = _get("precipitation")
        wind = _get("wind_speed_10m")
        code = _get("weather_code")

        return {
            "temperature_c": float(temp) if temp is not None else None,
            "apparent_temperature_c": float(apparent) if apparent is not None else None,
            "humidity_pct": int(humidity) if humidity is not None else None,
            "wind_speed_kmh": float(wind) if wind is not None else None,
            "precipitation_mm": float(precip) if precip is not None else None,
            "weather_code": int(code) if code is not None else None,
        }
    except Exception as e:
        _log(f"archive error: {type(e).__name__}: {e}")
        return None


def fetch_forecast_weather(lat: float, lon: float, target_dt: datetime) -> Optional[dict]:
    """
    Fetch hourly forecast for the date+hour of `target_dt`. Returns same
    shape as fetch_historical_weather. Used by the pre-run coach to
    heat-adjust today's target before the run actually happens.

    Open-Meteo forecast covers up to ~16 days ahead; for today + tomorrow
    requests it's effectively a current-conditions / short-range forecast.
    """
    if not REQUESTS_AVAILABLE or lat is None or lon is None or target_dt is None:
        return None

    date_str = target_dt.date().isoformat()
    hour = target_dt.hour

    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": date_str,
                "end_date": date_str,
                "hourly": ",".join([
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "wind_speed_10m",
                    "weather_code",
                ]),
                "timezone": "auto",
            },
            timeout=15,
        )
        if not resp.ok:
            _log(f"forecast HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        data = resp.json()
        hourly = data.get("hourly") or {}
        times = hourly.get("time") or []
        if not times:
            return None
        idx = None
        for i, t in enumerate(times):
            try:
                if datetime.fromisoformat(t).hour == hour:
                    idx = i
                    break
            except ValueError:
                continue
        if idx is None:
            idx = 0

        def _get(key: str):
            arr = hourly.get(key) or []
            return arr[idx] if 0 <= idx < len(arr) else None

        temp = _get("temperature_2m")
        humidity = _get("relative_humidity_2m")
        apparent = _get("apparent_temperature")
        precip = _get("precipitation")
        wind = _get("wind_speed_10m")
        code = _get("weather_code")

        return {
            "temperature_c": float(temp) if temp is not None else None,
            "apparent_temperature_c": float(apparent) if apparent is not None else None,
            "humidity_pct": int(humidity) if humidity is not None else None,
            "wind_speed_kmh": float(wind) if wind is not None else None,
            "precipitation_mm": float(precip) if precip is not None else None,
            "weather_code": int(code) if code is not None else None,
        }
    except Exception as e:
        _log(f"forecast error: {type(e).__name__}: {e}")
        return None


# WMO weather code → short label. Used by the coach prompts and the UI.
# https://open-meteo.com/en/docs#weathervariables
_WMO_CODES = {
    0: "clear",
    1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog",
    51: "drizzle", 53: "drizzle", 55: "drizzle",
    56: "freezing drizzle", 57: "freezing drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    66: "freezing rain", 67: "freezing rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    77: "snow grains",
    80: "rain showers", 81: "rain showers", 82: "heavy rain showers",
    85: "snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with hail",
}


def weather_label(code: Optional[int]) -> Optional[str]:
    if code is None:
        return None
    return _WMO_CODES.get(int(code), f"code {code}")
