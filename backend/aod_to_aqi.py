"""
ISRO INSAT-3DS AOD → Ground-Level PM2.5 → Indian National AQI Converter
"""

from typing import Optional, TypedDict

MOSDAC_AOD_LUT: list[tuple[int, int, int, float]] = [
    (0, 0, 80, 0.02),
    (0, 0, 130, 0.05),
    (26, 35, 126, 0.08),
    (21, 101, 192, 0.12),
    (30, 136, 229, 0.16),
    (66, 165, 245, 0.20),
    (77, 208, 225, 0.25),
    (0, 188, 212, 0.28),
    (0, 150, 136, 0.30),
    (76, 175, 80, 0.35),
    (102, 187, 106, 0.40),
    (139, 195, 74, 0.45),
    (192, 202, 51, 0.50),
    (255, 235, 59, 0.55),
    (255, 202, 40, 0.60),
    (255, 183, 77, 0.65),
    (255, 152, 0, 0.72),
    (255, 120, 0, 0.80),
    (255, 87, 34, 0.90),
    (244, 67, 54, 1.00),
    (229, 57, 53, 1.10),
    (211, 47, 47, 1.20),
    (198, 40, 40, 1.35),
    (156, 39, 176, 1.50),
    (106, 27, 154, 1.70),
    (74, 20, 140, 2.00),
    (49, 27, 146, 2.50),
]

def rgb_to_aod(r: int, g: int, b: int) -> Optional[float]:
    if r < 8 and g < 8 and b < 8:
        return None
    if r > 240 and g > 240 and b > 240:
        return None
    if abs(r - g) < 10 and abs(g - b) < 10 and 50 < r < 200:
        return None

    best_dist = float("inf")
    best_aod = 0.0

    for lr, lg, lb, aod in MOSDAC_AOD_LUT:
        dist = (r - lr) ** 2 + (g - lg) ** 2 + (b - lb) ** 2
        if dist < best_dist:
            best_dist = dist
            best_aod = aod

    if best_dist > 12000:
        return None

    return best_aod

AOD_BOUNDS = {
    "south": -10.01,
    "west": 45.05,
    "north": 51.65,
    "east": 100.06,
}

def lat_lng_to_pixel(lat: float, lng: float, img_width: int, img_height: int) -> Optional[dict[str, int]]:
    if lat < AOD_BOUNDS["south"] or lat > AOD_BOUNDS["north"]:
        return None
    if lng < AOD_BOUNDS["west"] or lng > AOD_BOUNDS["east"]:
        return None

    x = round(((lng - AOD_BOUNDS["west"]) / (AOD_BOUNDS["east"] - AOD_BOUNDS["west"])) * (img_width - 1))
    y = round(((AOD_BOUNDS["north"] - lat) / (AOD_BOUNDS["north"] - AOD_BOUNDS["south"])) * (img_height - 1))
    return {"x": x, "y": y}

ETA = 85000
GAMMA = 0.38

def hygroscopic_growth(relative_humidity: float) -> float:
    rh = max(10.0, min(95.0, relative_humidity))
    return (1.0 - rh / 100.0) ** (-GAMMA)

def aod_to_pm25(aod: float, pblh: float, rh: float) -> float:
    safe_pblh = max(200.0, min(2500.0, pblh if pblh else 600.0))
    f_rh = hygroscopic_growth(rh if rh else 50.0)
    pm25 = (aod * ETA) / (safe_pblh * f_rh)
    return max(5.0, round(pm25, 1))

CPCB_PM25_BREAKPOINTS = [
    (0, 30, 0, 50, "Good", "#009966"),
    (31, 60, 51, 100, "Satisfactory", "#58bc2b"),
    (61, 90, 101, 200, "Moderate", "#ffbf00"),
    (91, 120, 201, 300, "Poor", "#ff9800"),
    (121, 250, 301, 400, "Very Poor", "#e53935"),
    (251, 500, 401, 500, "Severe", "#880e4f"),
]

def pm25_to_aqi(pm25: float) -> dict:
    for c_low, c_high, i_low, i_high, category, color in CPCB_PM25_BREAKPOINTS:
        if pm25 <= c_high:
            aqi = round(((i_high - i_low) / (c_high - c_low)) * (pm25 - c_low) + i_low)
            return {"aqi": max(0, min(500, aqi)), "category": category, "color": color}
    return {"aqi": 500, "category": "Severe", "color": "#880e4f"}

def compute_aqi(aod: float, pblh: float, rh: float) -> dict:
    pm25 = aod_to_pm25(aod, pblh, rh)
    aqi_res = pm25_to_aqi(pm25)
    return {
        "aqi": aqi_res["aqi"],
        "category": aqi_res["category"],
        "color": aqi_res["color"],
        "pm25": pm25,
        "aod": aod,
    }
