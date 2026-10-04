import time
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Response

router = APIRouter()

_cache: dict[str, tuple[dict, float]] = {}
CACHE_TTL_SECONDS = 120.0

@router.get("/wind-history")
async def get_wind_history(
    response: Response,
    lat: float = Query(28.6139),
    lng: float = Query(77.2090),
    hours: int = Query(6),
):
    hours_req = min(12, max(1, hours))
    cache_key = f"{lat:.2f},{lng:.2f},{hours_req}"

    now_ts = time.time()
    if cache_key in _cache:
        data, ts = _cache[cache_key]
        if (now_ts - ts) < CACHE_TTL_SECONDS:
            cached_data = dict(data)
            cached_data["cacheHit"] = True
            response.headers["Cache-Control"] = "public, s-maxage=120, stale-while-revalidate=60"
            return cached_data

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lng}"
            f"&hourly=wind_speed_10m,wind_direction_10m,boundary_layer_height"
            f"&wind_speed_unit=kmh"
            f"&timezone=auto"
            f"&past_hours={hours_req}"
            f"&forecast_hours=0"
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url)

        if not res.is_success:
            raise Exception(f"Open-Meteo returned status {res.status_code}")

        data = res.json()
        hourly = data.get("hourly", {})
        time_list = hourly.get("time", [])

        if not isinstance(time_list, list):
            raise Exception("Invalid Open-Meteo response structure")

        entries = []
        now_dt = datetime.now(timezone.utc)

        for i, time_str in enumerate(time_list):
            wind_speed = float((hourly.get("wind_speed_10m") or [])[i] if i < len(hourly.get("wind_speed_10m", [])) else 0.0)
            wind_dir = float((hourly.get("wind_direction_10m") or [])[i] if i < len(hourly.get("wind_direction_10m", [])) else 0.0)
            blh = float((hourly.get("boundary_layer_height") or [])[i] if i < len(hourly.get("boundary_layer_height", [])) else 500.0)

            # Estimate hoursAgo
            try:
                entry_dt = datetime.fromisoformat(time_str)
                # convert to naive or comparable
                hours_ago = max(0.0, (now_dt.timestamp() - entry_dt.timestamp()) / 3600.0)
            except Exception:
                hours_ago = float(len(time_list) - 1 - i)

            entries.append({
                "time": time_str,
                "hoursAgo": round(hours_ago, 1),
                "windSpeedKmh": round(wind_speed, 1),
                "windDeg": round(wind_dir),
                "boundaryLayerHeight": round(blh),
            })

        # Sort newest first
        entries.sort(key=lambda e: e["hoursAgo"])

        result = {
            "entries": entries,
            "lat": lat,
            "lng": lng,
            "hoursRequested": hours_req,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "source": "Open-Meteo ERA5/GFS",
        }

        _cache[cache_key] = (result, now_ts)
        response.headers["Cache-Control"] = "public, s-maxage=120, stale-while-revalidate=60"
        return result
    except Exception as e:
        print(f"[Wind History API Error]: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch wind history: {e}")
