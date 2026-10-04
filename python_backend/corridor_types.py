from typing import Literal, TypedDict, Optional

CorridorStatus = Literal["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
CorridorSource = Literal["open-meteo", "google", "openaq", "openweather", "fallback"]

class CorridorStation(TypedDict, total=False):
    id: str
    name: str
    lat: float
    lng: float
    aqi: int
    pm25: float
    pm10: float
    windSpeed: float
    windDeg: int
    windDir: str
    boundaryLayerHeight: int
    temperature: float
    humidity: int
    status: CorridorStatus
    source: CorridorSource
    provider: Optional[str]
    area: Optional[str]
    observationTime: Optional[str]
    updatedAt: str

class WindSummary(TypedDict):
    speed: float
    deg: int
    dir: str

class MetaSummary(TypedDict):
    sources: list[str]
    fetchedAt: str
    cacheHit: bool

class CorridorApiResponse(TypedDict):
    stations: list[CorridorStation]
    wind: WindSummary
    meta: MetaSummary

def deg_to_cardinal(deg: float) -> str:
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(deg / 22.5) % 16
    return dirs[idx]

def pm25_to_india_aqi(pm25: float) -> tuple[int, CorridorStatus]:
    """
    Compute India National AQI from PM2.5 concentration based on CPCB breakpoint table.
    """
    breakpoints: list[tuple[float, float, int, int, CorridorStatus]] = [
        (0, 30, 0, 50, "Good"),
        (30, 60, 51, 100, "Satisfactory"),
        (60, 90, 101, 200, "Moderate"),
        (90, 120, 201, 300, "Poor"),
        (120, 250, 301, 400, "Very Poor"),
        (250, 500, 401, 500, "Severe"),
    ]

    for c_low, c_high, i_low, i_high, status in breakpoints:
        if pm25 <= c_high:
            aqi = round(((i_high - i_low) / (c_high - c_low)) * (pm25 - c_low) + i_low)
            return aqi, status

    return min(999, round(pm25 * 1.5)), "Severe"
