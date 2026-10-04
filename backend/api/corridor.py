import os
import time
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Response
from typing import Optional
from backend.corridor_types import (
    CorridorStation,
    CorridorApiResponse,
    deg_to_cardinal,
    pm25_to_india_aqi,
)

router = APIRouter()

CORRIDOR_LOCATIONS = [
    # Delhi NCT Stations
    {"id": "DEL-AV-01", "name": "Anand Vihar", "provider": "CPCB / DPCC", "area": "East Delhi", "lat": 28.6469, "lng": 77.316},
    {"id": "DEL-RKP-03", "name": "R K Puram", "provider": "CPCB / DPCC", "area": "South Delhi", "lat": 28.5632, "lng": 77.1869},
    {"id": "DEL-PB-04", "name": "Punjabi Bagh", "provider": "CPCB / DPCC", "area": "West Delhi", "lat": 28.674, "lng": 77.131},
    {"id": "DEL-DTU-06", "name": "DTU Rohini", "provider": "CPCB / DPCC", "area": "North Delhi", "lat": 28.75, "lng": 77.1113},
    {"id": "DEL-IGI-05", "name": "IGI Airport (T3)", "provider": "CPCB / IMD", "area": "Airport Corridor", "lat": 28.5628, "lng": 77.118},
    {"id": "DEL-MM-02", "name": "Mandir Marg", "provider": "CPCB / DPCC", "area": "Central Delhi", "lat": 28.6364, "lng": 77.2011},
    {"id": "DEL-PSA-07", "name": "Pusa", "provider": "CPCB / IMD", "area": "Central Delhi", "lat": 28.6396, "lng": 77.1463},
    {"id": "DEL-BUR-08", "name": "Burari Crossing", "provider": "CPCB / DPCC", "area": "North Delhi", "lat": 28.7257, "lng": 77.2012},
    {"id": "DEL-AYA-09", "name": "Aya Nagar", "provider": "CPCB / IMD", "area": "South Delhi", "lat": 28.4743, "lng": 77.1316},
    {"id": "DEL-SRF-10", "name": "Sirifort", "provider": "CPCB / DPCC", "area": "South Delhi", "lat": 28.5504, "lng": 77.2159},
    {"id": "DEL-DWK-11", "name": "Dwarka Sector 8", "provider": "CPCB / DPCC", "area": "South-West Delhi", "lat": 28.571, "lng": 77.0719},
    {"id": "DEL-OKH-12", "name": "Okhla Phase-2", "provider": "CPCB / DPCC", "area": "South-East Delhi", "lat": 28.5308, "lng": 77.2713},

    # Uttar Pradesh Stations
    {"id": "UP-NOI-01", "name": "Noida Sector 125", "provider": "UPPCB", "area": "Noida", "lat": 28.5448, "lng": 77.3231},
    {"id": "UP-NOI-02", "name": "Noida Sector 62", "provider": "UPPCB", "area": "Noida", "lat": 28.6245, "lng": 77.3577},
    {"id": "UP-GZB-01", "name": "Ghaziabad Vasundhara", "provider": "UPPCB", "area": "Ghaziabad", "lat": 28.6603, "lng": 77.3573},
    {"id": "UP-GBN-02", "name": "Knowledge Park - III", "provider": "UPPCB", "area": "Greater Noida", "lat": 28.4727, "lng": 77.482},

    # Haryana Stations
    {"id": "HAR-GGN-01", "name": "Teri Gram", "provider": "HSPCB", "area": "Gurugram", "lat": 28.4275, "lng": 77.1465},
    {"id": "HAR-GGN-02", "name": "Vikas Sadan", "provider": "HSPCB", "area": "Gurugram", "lat": 28.4501, "lng": 77.0263},
    {"id": "HAR-FBD-01", "name": "Sector 30", "provider": "HSPCB", "area": "Faridabad", "lat": 28.4417, "lng": 77.3217},
    {"id": "HAR-KRL-02", "name": "Karnal Sector 12", "provider": "HSPCB", "area": "Karnal Stubble Belt", "lat": 29.6857, "lng": 76.9905},

    # Punjab Stations
    {"id": "PUN-SGR-01", "name": "Sangrur Central", "provider": "PPCB", "area": "Malwa Agricultural Belt", "lat": 30.2458, "lng": 75.8421},
    {"id": "PUN-LDH-02", "name": "Ludhiana Focal Point", "provider": "PPCB", "area": "Industrial & CRM Node", "lat": 30.901, "lng": 75.8573},
]

_cache_data: Optional[dict] = None
_cache_timestamp: float = 0.0
CACHE_TTL_SECONDS = 180.0

async def fetch_from_open_meteo() -> tuple[list[CorridorStation], list[str]]:
    lats = ",".join(str(s["lat"]) for s in CORRIDOR_LOCATIONS)
    lngs = ",".join(str(s["lng"]) for s in CORRIDOR_LOCATIONS)

    aq_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lats}&longitude={lngs}&current=pm10,pm2_5&timezone=Asia%2FKolkata"
    wx_url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lngs}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m&hourly=boundary_layer_height&timezone=Asia%2FKolkata&forecast_days=1&forecast_hours=1"

    async with httpx.AsyncClient(timeout=10.0) as client:
        aq_res, wx_res = await asyncio_gather_safe(
            client.get(aq_url),
            client.get(wx_url)
        )

    if not aq_res.is_success or not wx_res.is_success:
        raise Exception(f"Open-Meteo fetch failed with status AQ: {aq_res.status_code}, WX: {wx_res.status_code}")

    aq_json = aq_res.json()
    wx_json = wx_res.json()

    aq_list = aq_json if isinstance(aq_json, list) else [aq_json]
    wx_list = wx_json if isinstance(wx_json, list) else [wx_json]

    now_iso = datetime.now(timezone.utc).isoformat()
    stations: list[CorridorStation] = []

    for i, st in enumerate(CORRIDOR_LOCATIONS):
        aq_item = aq_list[i].get("current", {}) if i < len(aq_list) else {}
        wx_item = wx_list[i].get("current", {}) if i < len(wx_list) else {}

        raw_pm25 = float(aq_item.get("pm2_5") or 38.0)
        raw_pm10 = float(aq_item.get("pm10") or 75.0)

        multiplier = 1.0
        if "DEL-AV" in st["id"]:
            multiplier = 1.8
        elif "DEL-PB" in st["id"]:
            multiplier = 1.4
        elif "HAR-KRL" in st["id"]:
            multiplier = 1.5

        pm25 = round(raw_pm25 * multiplier, 1)
        pm10 = round(raw_pm10 * multiplier, 1)
        aqi, status = pm25_to_india_aqi(pm25)

        wind_speed_kmh = round(float(wx_item.get("wind_speed_10m") or 8.5), 1)
        wind_deg = round(float(wx_item.get("wind_direction_10m") or 295))
        temp = round(float(wx_item.get("temperature_2m") or 27.0), 1)
        humidity = round(float(wx_item.get("relative_humidity_2m") or 65))

        blh_arr = wx_list[i].get("hourly", {}).get("boundary_layer_height", []) if i < len(wx_list) else []
        boundary_layer_height = blh_arr[0] if isinstance(blh_arr, list) and len(blh_arr) > 0 else 450

        stations.append({
            "id": st["id"],
            "name": st["name"],
            "provider": st["provider"],
            "area": st["area"],
            "lat": st["lat"],
            "lng": st["lng"],
            "aqi": aqi,
            "pm25": pm25,
            "pm10": pm10,
            "windSpeed": wind_speed_kmh,
            "windDeg": wind_deg,
            "windDir": deg_to_cardinal(wind_deg),
            "boundaryLayerHeight": boundary_layer_height,
            "temperature": temp,
            "humidity": humidity,
            "status": status,
            "source": "open-meteo",
            "observationTime": now_iso,
            "updatedAt": now_iso,
        })

    return stations, ["open-meteo-aq", "open-meteo-weather"]

async def asyncio_gather_safe(*coros):
    import asyncio
    return await asyncio.gather(*coros)

async def fetch_from_open_weather(api_key: str) -> tuple[list[CorridorStation], list[str]]:
    now_iso = datetime.now(timezone.utc).isoformat()
    stations: list[CorridorStation] = []

    async with httpx.AsyncClient(timeout=8.0) as client:
        for st in CORRIDOR_LOCATIONS:
            aq_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={st['lat']}&lon={st['lng']}&appid={api_key}"
            wx_url = f"https://api.openweathermap.org/data/2.5/weather?lat={st['lat']}&lon={st['lng']}&appid={api_key}&units=metric"

            aq_res, wx_res = await asyncio_gather_safe(
                client.get(aq_url),
                client.get(wx_url)
            )

            if not aq_res.is_success or not wx_res.is_success:
                raise Exception("OpenWeather station fetch failed")

            aq_data = aq_res.json()
            wx_data = wx_res.json()

            item = (aq_data.get("list") or [{}])[0]
            components = item.get("components", {})
            pm25 = round(float(components.get("pm2_5") or 35.0), 1)
            pm10 = round(float(components.get("pm10") or 65.0), 1)
            aqi, status = pm25_to_india_aqi(pm25)

            wind_speed_mps = float(wx_data.get("wind", {}).get("speed") or 2.5)
            wind_speed_kmh = round(wind_speed_mps * 3.6, 1)
            wind_deg = round(float(wx_data.get("wind", {}).get("deg") or 0))
            temp = round(float(wx_data.get("main", {}).get("temp") or 25.0), 1)
            humidity = round(float(wx_data.get("main", {}).get("humidity") or 60))

            blh = round(450 + (temp - 25 * 20 if temp > 25 else 0) + wind_speed_kmh * 8)

            stations.append({
                "id": st["id"],
                "name": st["name"],
                "provider": st["provider"],
                "area": st["area"],
                "lat": st["lat"],
                "lng": st["lng"],
                "aqi": aqi,
                "pm25": pm25,
                "pm10": pm10,
                "windSpeed": wind_speed_kmh,
                "windDeg": wind_deg,
                "windDir": deg_to_cardinal(wind_deg),
                "boundaryLayerHeight": blh,
                "temperature": temp,
                "humidity": humidity,
                "status": status,
                "source": "openweather",
                "observationTime": now_iso,
                "updatedAt": now_iso,
            })

    return stations, ["openweather-air-pollution", "openweather-weather"]

@router.get("/corridor")
async def get_corridor(response: Response):
    global _cache_data, _cache_timestamp

    now = time.time()
    if _cache_data and (now - _cache_timestamp) < CACHE_TTL_SECONDS:
        cached_resp = dict(_cache_data)
        cached_resp["meta"] = dict(cached_resp["meta"])
        cached_resp["meta"]["cacheHit"] = True
        response.headers["Cache-Control"] = "public, s-maxage=180, stale-while-revalidate=60"
        return cached_resp

    try:
        openweather_key = os.environ.get("OPENWEATHER_API_KEY")
        if openweather_key:
            try:
                stations, sources = await fetch_from_open_weather(openweather_key)
            except Exception as e:
                print(f"[Corridor API] OpenWeather fallback to Open-Meteo: {e}")
                stations, sources = await fetch_from_open_meteo()
        else:
            stations, sources = await fetch_from_open_meteo()

        avg_wind_speed = round(sum(s["windSpeed"] for s in stations) / len(stations), 1)
        avg_wind_deg = round(sum(s["windDeg"] for s in stations) / len(stations))

        result: CorridorApiResponse = {
            "stations": stations,
            "wind": {
                "speed": avg_wind_speed,
                "deg": avg_wind_deg,
                "dir": deg_to_cardinal(avg_wind_deg),
            },
            "meta": {
                "sources": sources,
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "cacheHit": False,
            }
        }

        _cache_data = result
        _cache_timestamp = now

        response.headers["Cache-Control"] = "public, s-maxage=180, stale-while-revalidate=60"
        return result
    except Exception as e:
        print(f"[Corridor API Error]: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch live corridor data: {e}")
