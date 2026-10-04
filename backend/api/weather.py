import os
import time
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Response
from typing import Optional

router = APIRouter()

_cache_data: Optional[dict] = None
_cache_timestamp: float = 0.0
CACHE_TTL_SECONDS = 300.0

def deg_to_cardinal(deg: float) -> str:
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[round(deg / 22.5) % 16]

@router.get("/weather")
async def get_weather(response: Response):
    global _cache_data, _cache_timestamp

    now = time.time()
    if _cache_data and (now - _cache_timestamp) < CACHE_TTL_SECONDS:
        cached_resp = dict(_cache_data)
        cached_resp["cacheHit"] = True
        response.headers["Cache-Control"] = "public, s-maxage=300, stale-while-revalidate=120"
        return cached_resp

    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENWEATHER_API_KEY not configured")

    try:
        lat = 28.6139
        lng = 77.2090
        wx_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={api_key}&units=metric"

        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(wx_url)

        if not res.is_success:
            raise Exception(f"OpenWeather API error ({res.status_code}): {res.text}")

        data = res.json()
        temp = round(float(data.get("main", {}).get("temp", 25.0)), 1)
        wind_speed_mps = float(data.get("wind", {}).get("speed", 2.5))
        wind_speed_kmh = round(wind_speed_mps * 3.6, 1)
        wind_deg = round(float(data.get("wind", {}).get("deg", 0)))

        blh = round(450 + (temp - 25 * 20 if temp > 25 else 0) + wind_speed_kmh * 8)

        result = {
            "temperature": temp,
            "humidity": round(float(data.get("main", {}).get("humidity", 60))),
            "pressure": round(float(data.get("main", {}).get("pressure", 1013))),
            "windSpeed": wind_speed_kmh,
            "windDeg": wind_deg,
            "windDir": deg_to_cardinal(wind_deg),
            "visibility": data.get("visibility", 10000),
            "cloudCover": data.get("clouds", {}).get("all", 0),
            "description": (data.get("weather", [{}])[0].get("description") or "clear sky"),
            "feelsLike": round(float(data.get("main", {}).get("feels_like", temp)), 1),
            "boundaryLayerEstimate": blh,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "source": "OpenWeather",
        }

        _cache_data = result
        _cache_timestamp = now

        response.headers["Cache-Control"] = "public, s-maxage=300, stale-while-revalidate=120"
        return result
    except Exception as e:
        print(f"[Weather API Error]: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch weather data: {e}")
