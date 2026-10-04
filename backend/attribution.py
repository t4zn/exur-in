"""
Inverse Ray-Tracing Atmospheric Source Attribution Engine
"""

import math
from typing import TypedDict, Optional
from backend.air_data import CORRIDOR_STATIONS
from backend.industrial_registry import INDUSTRIAL_CLUSTERS

class ParticlePoint(TypedDict):
    lat: float
    lng: float
    tHours: float

class CandidateScore(TypedDict):
    id: str
    name: str
    lat: float
    lng: float
    score: float
    distanceKm: float
    bearingDeg: int
    reasons: list[str]
    typeLabel: Optional[str]
    area: Optional[str]
    state: Optional[str]
    osmSource: Optional[str]

class AttributionResult(TypedDict):
    particlePaths: list[list[ParticlePoint]]
    envelope: list[dict[str, float]]
    ranked: list[CandidateScore]
    isKinematic: bool
    sourceCount: int

class HourlyWindVector(TypedDict, total=False):
    hoursAgo: float
    windSpeedKmh: float
    windDeg: int
    boundaryLayerHeight: Optional[int]

def deg2rad(d: float) -> float:
    return (d * math.pi) / 180.0

def rad2deg(r: float) -> float:
    return (r * 180.0) / math.pi

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    d_lat = deg2rad(lat2 - lat1)
    d_lon = deg2rad(lon2 - lon1)
    a = (math.sin(d_lat / 2.0) ** 2) + math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * (math.sin(d_lon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    y = math.sin(deg2rad(lon2 - lon1)) * math.cos(deg2rad(lat2))
    x = math.cos(deg2rad(lat1)) * math.sin(deg2rad(lat2)) - math.sin(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * math.cos(deg2rad(lon2 - lon1))
    return (rad2deg(math.atan2(y, x)) + 360.0) % 360.0

# Deterministic PRNG utilities matching JavaScript xmur3 + mulberry32
def _imul(a: int, b: int) -> int:
    return ((a & 0xFFFFFFFF) * (b & 0xFFFFFFFF)) & 0xFFFFFFFF

def _xmur3(string: str):
    h = 1779033703 ^ len(string)
    for ch in string:
        h = _imul(h ^ ord(ch), 3432918353)
        h = ((h << 13) | (h >> 19)) & 0xFFFFFFFF
    
    def next_seed():
        nonlocal h
        h = _imul(h ^ (h >> 16), 2246822507)
        h = _imul(h ^ (h >> 13), 3266489909)
        h = (h ^ (h >> 16)) & 0xFFFFFFFF
        return h
    return next_seed

def _mulberry32(a: int):
    def next_val():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = a
        t = _imul(t ^ (t >> 15), t | 1)
        t ^= (t + _imul(t ^ (t >> 7), t | 61)) & 0xFFFFFFFF
        return (((t ^ (t >> 14)) & 0xFFFFFFFF) >> 0) / 4294967296.0
    return next_val

def seeded_rng(seed_str: str):
    seed = _xmur3(seed_str)()
    return _mulberry32(seed)

def get_wind_at_time(
    hours_back: float,
    hourly_winds: list[dict],
    default_speed: float,
    default_deg: float
) -> tuple[float, float]:
    if not hourly_winds:
        return default_speed, default_deg
    closest = min(hourly_winds, key=lambda w: abs(w.get("hoursAgo", 0.0) - hours_back))
    return closest.get("windSpeedKmh", default_speed), closest.get("windDeg", default_deg)

def compute_kinematic_particles(
    receptor_lat: float,
    receptor_lng: float,
    hourly_winds: list[dict],
    fallback_speed_kmh: float,
    fallback_bearing_deg: float,
    hours_back: float = 3.0,
    n_particles: int = 36,
    step_minutes: int = 10
) -> list[list[ParticlePoint]]:
    particles: list[list[ParticlePoint]] = []
    steps = max(1, math.ceil((hours_back * 60.0) / step_minutes))
    dt_hours = step_minutes / 60.0

    base_deg = hourly_winds[0].get("windDeg", fallback_bearing_deg) if hourly_winds else fallback_bearing_deg
    rng = seeded_rng(f"{receptor_lat:.4f},{receptor_lng:.4f},{base_deg},{hours_back}")

    for p in range(n_particles):
        path: list[ParticlePoint] = []
        curr_lat = receptor_lat
        curr_lng = receptor_lng

        path.append({"lat": round(curr_lat, 6), "lng": round(curr_lng, 6), "tHours": 0.0})

        lateral_sign = 1 if (p % 2 == 0) else -1
        lateral_scale = (p // 2 + 1) * 0.15

        for s in range(1, steps + 1):
            t_hours = s * dt_hours
            w_speed, w_deg = get_wind_at_time(t_hours, hourly_winds, fallback_speed_kmh, fallback_bearing_deg)
            speed_kmh = max(1.0, w_speed)
            upwind_bearing = w_deg

            step_dist_km = speed_kmh * dt_hours
            jitter_km = (rng() - 0.5) * 0.08 * math.sqrt(t_hours)
            lateral_km = lateral_scale * math.sqrt(t_hours) * (rng() * 0.4 + 0.8) * lateral_sign * dt_hours

            bearing_rad = deg2rad(upwind_bearing)
            delta_lat = (step_dist_km * math.cos(bearing_rad)) / 111.0
            delta_lng = (step_dist_km * math.sin(bearing_rad)) / (111.0 * math.cos(deg2rad(curr_lat)))

            perp_rad = bearing_rad + math.pi / 2.0
            perp_lat = (lateral_km * math.cos(perp_rad)) / 111.0
            perp_lng = (lateral_km * math.sin(perp_rad)) / (111.0 * math.cos(deg2rad(curr_lat)))

            curr_lat += delta_lat + perp_lat + (jitter_km / 111.0)
            curr_lng += delta_lng + perp_lng + (jitter_km / (111.0 * math.cos(deg2rad(curr_lat))))

            path.append({
                "lat": round(curr_lat, 6),
                "lng": round(curr_lng, 6),
                "tHours": round(t_hours, 2),
            })

        particles.append(path)

    return particles

def build_envelope(particles: list[list[ParticlePoint]]) -> list[dict[str, float]]:
    ends = [p[-1] for p in particles if p]
    if not ends:
        return []
    cx = sum(e["lat"] for e in ends) / len(ends)
    cy = sum(e["lng"] for e in ends) / len(ends)

    sorted_ends = sorted(ends, key=lambda e: math.atan2(e["lat"] - cx, e["lng"] - cy))
    return [{"lat": e["lat"], "lng": e["lng"]} for e in sorted_ends]

def score_candidates(
    receptor_lat: float,
    receptor_lng: float,
    particles: list[list[ParticlePoint]],
    candidates: list[dict],
    pm25: float,
    boundary_layer_m: float,
    wind_bearing_deg: float
) -> list[CandidateScore]:
    endpoints = [p[-1] for p in particles if p]
    if not endpoints or not candidates:
        return []

    mean_lat = sum(e["lat"] for e in endpoints) / len(endpoints)
    mean_lng = sum(e["lng"] for e in endpoints) / len(endpoints)
    max_dist = max([haversine_km(receptor_lat, receptor_lng, e["lat"], e["lng"]) for e in endpoints] + [1.0])

    scores: list[CandidateScore] = []
    for cand in candidates:
        dist_to_mean = haversine_km(cand["lat"], cand["lng"], mean_lat, mean_lng)
        dist_to_receptor = haversine_km(cand["lat"], cand["lng"], receptor_lat, receptor_lng)
        bearing = bearing_deg(receptor_lat, receptor_lng, cand["lat"], cand["lng"])
        angular_diff = abs(((bearing - wind_bearing_deg + 540) % 360) - 180)
        alignment_score = max(0.0, 1.0 - angular_diff / 180.0)
        proximity_score = max(0.0, 1.0 - dist_to_mean / max(max_dist, 8.0))
        severity_score = min(1.0, pm25 / 400.0)
        blh_score = max(0.0, min(1.0, (600.0 - boundary_layer_m) / 600.0))

        w_align, w_prox, w_sev, w_blh = 0.45, 0.30, 0.15, 0.10
        score = max(0.0, min(1.0, w_align * alignment_score + w_prox * proximity_score + w_sev * severity_score + w_blh * blh_score))

        reasons: list[str] = []
        if alignment_score > 0.75:
            reasons.append("Direct upwind trajectory corridor alignment")
        elif alignment_score > 0.55:
            reasons.append("Moderate upwind trajectory alignment")

        if proximity_score > 0.7:
            reasons.append("Plume centroid directly intersects industrial zone")
        elif dist_to_receptor < 15.0:
            reasons.append(f"Close geographic proximity ({dist_to_receptor:.1f} km)")

        if severity_score > 0.6:
            reasons.append(f"Severe PM2.5 event at receptor ({pm25:.0f} µg/m³)")
        if blh_score > 0.5:
            reasons.append(f"Low boundary layer ({boundary_layer_m:.0f}m) promotes surface ground trapping")

        scores.append({
            "id": cand["id"],
            "name": cand["name"],
            "lat": cand["lat"],
            "lng": cand["lng"],
            "score": round(score, 3),
            "distanceKm": round(dist_to_receptor, 1),
            "bearingDeg": round(bearing),
            "reasons": reasons,
            "typeLabel": cand.get("typeLabel"),
            "area": cand.get("area"),
            "state": cand.get("state"),
            "osmSource": cand.get("osmSource"),
        })

    scores.sort(key=lambda s: s["score"], reverse=True)
    return scores

def compute_real_attribution(
    receptor_lat: float,
    receptor_lng: float,
    hourly_winds: list[dict],
    wind_speed_kmh: float,
    wind_bearing_deg: float,
    hours_back: float,
    pm25: float,
    boundary_layer_m: float
) -> AttributionResult:
    is_kinematic = bool(hourly_winds and len(hourly_winds) > 0)
    particles = compute_kinematic_particles(
        receptor_lat,
        receptor_lng,
        hourly_winds,
        wind_speed_kmh,
        wind_bearing_deg,
        hours_back,
        36,
        10
    )
    envelope = build_envelope(particles)

    lats = [pt["lat"] for p in particles for pt in p]
    lngs = [pt["lng"] for p in particles for pt in p]
    min_lat, max_lat = min(lats) - 0.15, max(lats) + 0.15
    min_lng, max_lng = min(lngs) - 0.15, max(lngs) + 0.15

    relevant = [c for c in INDUSTRIAL_CLUSTERS if min_lat <= c["lat"] <= max_lat and min_lng <= c["lng"] <= max_lng]
    candidate_pool = relevant if len(relevant) >= 3 else [
        c for c in INDUSTRIAL_CLUSTERS if haversine_km(receptor_lat, receptor_lng, c["lat"], c["lng"]) <= 50.0
    ]

    effective_bearing = hourly_winds[0].get("windDeg", wind_bearing_deg) if hourly_winds else wind_bearing_deg
    ranked = score_candidates(
        receptor_lat,
        receptor_lng,
        particles,
        candidate_pool,
        pm25,
        boundary_layer_m,
        effective_bearing
    )

    return {
        "particlePaths": particles,
        "envelope": envelope,
        "ranked": ranked,
        "isKinematic": is_kinematic,
        "sourceCount": len(candidate_pool),
    }
