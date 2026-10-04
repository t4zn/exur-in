import os
import time
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Response
from typing import Optional

router = APIRouter()

BBOX_PARAM = "75.5,27.5,78.5,30.5"

_cache_data: Optional[dict] = None
_cache_timestamp: float = 0.0
CACHE_TTL_SECONDS = 300.0

@router.get("/firms")
async def get_firms(response: Response):
    global _cache_data, _cache_timestamp

    now = time.time()
    if _cache_data and (now - _cache_timestamp) < CACHE_TTL_SECONDS:
        cached_resp = dict(_cache_data)
        cached_resp["cacheHit"] = True
        response.headers["Cache-Control"] = "public, s-maxage=300, stale-while-revalidate=120"
        return cached_resp

    firms_key = os.environ.get("NASA_FIRMS_KEY")
    if not firms_key:
        raise HTTPException(
            status_code=500,
            detail="NASA_FIRMS_KEY is not configured in .env.local. Get a free key at https://firms.modaps.eosdis.nasa.gov/api/map_key/"
        )

    try:
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{firms_key}/VIIRS_SNPP_NRT/{BBOX_PARAM}/1"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url)

        if not res.is_success:
            raise Exception(f"FIRMS API error ({res.status_code}): {res.text}")

        csv_text = res.text.strip()
        lines = csv_text.split("\n")
        if len(lines) < 1:
            raise Exception("FIRMS returned empty response")

        headers = [h.strip().lower() for h in lines[0].split(",")]
        def get_col(name: str):
            try:
                return headers.index(name)
            except ValueError:
                return -1

        lat_idx = get_col("latitude")
        lng_idx = get_col("longitude")
        bright_idx = get_col("bright_ti4")
        scan_idx = get_col("scan")
        track_idx = get_col("track")
        date_idx = get_col("acq_date")
        time_idx = get_col("acq_time")
        sat_idx = get_col("satellite")
        conf_idx = get_col("confidence")
        frp_idx = get_col("frp")
        dn_idx = get_col("daynight")

        fires = []
        for line in lines[1:]:
            cols = [c.strip() for c in line.split(",")]
            if len(cols) < 5 or lat_idx == -1 or lng_idx == -1:
                continue

            try:
                lat = float(cols[lat_idx])
                lng = float(cols[lng_idx])
            except ValueError:
                continue

            fires.append({
                "lat": lat,
                "lng": lng,
                "brightness": float(cols[bright_idx]) if bright_idx >= 0 and cols[bright_idx] else 0.0,
                "scan": float(cols[scan_idx]) if scan_idx >= 0 and cols[scan_idx] else 0.0,
                "track": float(cols[track_idx]) if track_idx >= 0 and cols[track_idx] else 0.0,
                "acqDate": cols[date_idx] if date_idx >= 0 and date_idx < len(cols) else "",
                "acqTime": cols[time_idx] if time_idx >= 0 and time_idx < len(cols) else "",
                "satellite": cols[sat_idx] if sat_idx >= 0 and sat_idx < len(cols) else "VIIRS",
                "confidence": cols[conf_idx] if conf_idx >= 0 and conf_idx < len(cols) else "nominal",
                "frp": float(cols[frp_idx]) if frp_idx >= 0 and cols[frp_idx] else 0.0,
                "daynight": cols[dn_idx] if dn_idx >= 0 and dn_idx < len(cols) else "",
            })

        result = {
            "fires": fires,
            "corridorFireCount": len(fires),
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "source": "NASA FIRMS VIIRS S-NPP NRT",
        }

        _cache_data = result
        _cache_timestamp = now

        response.headers["Cache-Control"] = "public, s-maxage=300, stale-while-revalidate=120"
        return result
    except Exception as e:
        print(f"[FIRMS API Error]: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch FIRMS data: {e}")
