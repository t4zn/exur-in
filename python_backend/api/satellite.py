import asyncio
import httpx
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Response

router = APIRouter()

MOSDAC_BASE = "https://mosdac.gov.in/look/3S_IMG/preview"
CHANNELS = ["IR1", "VIS", "SWIR", "WV"]
CHANNEL_LABELS = {
    "VIS": "Visible",
    "IR1": "Thermal Infrared",
    "SWIR": "Shortwave IR",
    "WV": "Water Vapor",
    "AOD": "Aerosol Optical Depth",
}
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

def format_mosdac_date(d: datetime) -> tuple[str, str, str]:
    day = f"{d.day:02d}"
    mon = MONTHS[d.month - 1]
    year = str(d.year)
    return year, f"{day}{mon}", f"{day}{mon}{year}"

def build_image_url(year: str, ddmon: str, ddmonyear: str, time_str: str, channel: str) -> str:
    product = "L2G_AOD" if channel == "AOD" else f"L1B_STD_{channel}"
    return f"{MOSDAC_BASE}/{year}/{ddmon}/3SIMG_{ddmonyear}_{time_str}_{product}_V01R00.jpg"

def utc_to_ist(hours: int, minutes: int) -> str:
    ist_min = minutes + 30
    ist_hour = hours + 5
    if ist_min >= 60:
        ist_min -= 60
        ist_hour += 1
    ist_hour = ist_hour % 24
    h = ist_hour - 12 if ist_hour > 12 else (12 if ist_hour == 0 else ist_hour)
    ampm = "PM" if ist_hour >= 12 else "AM"
    return f"{h}:{ist_min:02d} {ampm} IST"

async def check_aod_candidate(client: httpx.AsyncClient, year: str, ddmon: str, ddmonyear: str, time_str: str):
    url = build_image_url(year, ddmon, ddmonyear, time_str, "AOD")
    try:
        resp = await client.head(url)
        if resp.status_code == 200:
            h = int(time_str[:2])
            m = int(time_str[2:4])
            return {
                "utcTime": time_str,
                "istTime": utc_to_ist(h, m),
                "dateLabel": ddmonyear,
                "url": url,
            }
    except Exception:
        pass
    return None

async def find_available_aod() -> list[dict]:
    now = datetime.now(timezone.utc)
    aod_slots = []
    candidates = ["0500", "0530", "0600", "0630", "0700", "0730", "0800", "0830", "0900", "0930", "1000"]

    async with httpx.AsyncClient(timeout=4.0) as client:
        for day_offset in range(2):
            day = now - timedelta(days=day_offset)
            year, ddmon, ddmonyear = format_mosdac_date(day)

            tasks = [check_aod_candidate(client, year, ddmon, ddmonyear, t) for t in candidates]
            results = await asyncio.gather(*tasks)
            valid = [r for r in results if r]
            if valid:
                aod_slots.extend(valid)
                break

    aod_slots.sort(key=lambda s: s["utcTime"], reverse=True)
    return aod_slots

@router.get("/satellite")
async def get_satellite(response: Response):
    try:
        now = datetime.now(timezone.utc)
        scans = []
        seen_keys = set()

        for offset in range(4, 20):
            if len(scans) >= 8:
                break
            scan_time = now - timedelta(minutes=offset * 30)
            utc_hour = scan_time.hour
            utc_minute = (scan_time.minute // 30) * 30

            key = f"{scan_time.year}-{scan_time.month}-{scan_time.day}-{utc_hour}-{utc_minute}"
            if key in seen_keys:
                continue
            seen_keys.add(key)

            year, ddmon, ddmonyear = format_mosdac_date(scan_time)
            time_str = f"{utc_hour:02d}{utc_minute:02d}"

            channels = {
                ch: build_image_url(year, ddmon, ddmonyear, time_str, ch)
                for ch in CHANNELS
            }

            scans.append({
                "utcTime": time_str,
                "istTime": utc_to_ist(utc_hour, utc_minute),
                "dateLabel": ddmonyear,
                "channels": channels,
            })

        aod_scans = await find_available_aod()

        result = {
            "scans": scans,
            "aodScans": aod_scans,
            "channels": CHANNEL_LABELS,
            "satellite": "INSAT-3DS",
            "orbit": "Geostationary 82°E",
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

        response.headers["Cache-Control"] = "public, s-maxage=600, stale-while-revalidate=300"
        return result
    except Exception as e:
        print(f"[Satellite API Error]: {e}")
        return {"error": str(e), "source": "mosdac", "timestamp": datetime.now(timezone.utc).isoformat()}
