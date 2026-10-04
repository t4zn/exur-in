# Exur Atmospheric Data Engine

CORRIDOR_STATIONS = [
  {
    "id": "DEL-AV-01",
    "name": "Anand Vihar Transit Terminal",
    "type": "CPCB_MACRO",
    "state": "Delhi NCT",
    "coordinates": {
      "lat": 28.6469,
      "lng": 77.316,
      "elevationMeters": 214
    },
    "aqi": 412,
    "pm25": 286,
    "pm10": 430,
    "windSpeedKmh": 4.8,
    "windDirection": "NW",
    "windBearingDeg": 315,
    "boundaryLayerHeightM": 180,
    "status": "Severe"
  },
  {
    "id": "DEL-MM-02",
    "name": "Mandir Marg Central",
    "type": "CPCB_MACRO",
    "state": "Delhi NCT",
    "coordinates": {
      "lat": 28.6341,
      "lng": 77.199,
      "elevationMeters": 220
    },
    "aqi": 228,
    "pm25": 142,
    "pm10": 215,
    "windSpeedKmh": 5.2,
    "windDirection": "WNW",
    "windBearingDeg": 292,
    "boundaryLayerHeightM": 220,
    "status": "Poor"
  },
  {
    "id": "HAR-GGN-01",
    "name": "Gurugram CyberCity Node",
    "type": "CPCB_MACRO",
    "state": "Haryana",
    "coordinates": {
      "lat": 28.495,
      "lng": 77.0895,
      "elevationMeters": 228
    },
    "aqi": 285,
    "pm25": 174,
    "pm10": 290,
    "windSpeedKmh": 6.1,
    "windDirection": "NW",
    "windBearingDeg": 310,
    "boundaryLayerHeightM": 210,
    "status": "Poor"
  },
  {
    "id": "UP-NOI-01",
    "name": "Noida Sector 62 Corridor",
    "type": "CPCB_MACRO",
    "state": "Uttar Pradesh",
    "coordinates": {
      "lat": 28.6255,
      "lng": 77.3695,
      "elevationMeters": 208
    },
    "aqi": 368,
    "pm25": 224,
    "pm10": 380,
    "windSpeedKmh": 4.2,
    "windDirection": "NW",
    "windBearingDeg": 320,
    "boundaryLayerHeightM": 175,
    "status": "Very Poor"
  },
  {
    "id": "HOT-MUNDKA-09",
    "name": "Mundka Plastic Pyrolysis Zone",
    "type": "HYPERLOCAL_HOTSPOT",
    "state": "Delhi NCT",
    "coordinates": {
      "lat": 28.6835,
      "lng": 77.0315,
      "elevationMeters": 216
    },
    "aqi": 684,
    "pm25": 492,
    "pm10": 710,
    "windSpeedKmh": 3.5,
    "windDirection": "WNW",
    "windBearingDeg": 295,
    "boundaryLayerHeightM": 140,
    "status": "Hazardous",
    "anomalyType": "Illegal Night Smelting / Plastic Pyrolysis",
    "attributedSource": {
      "clusterName": "Mundka Industrial Sector 4 Foundry Ring",
      "clusterType": "Industrial Slag/Pyrolysis",
      "distanceKm": 2.4,
      "confidencePercent": 91,
      "upwindHeading": "WNW",
      "upwindBearingDeg": 295,
      "coordinates": {
        "lat": 28.6942,
        "lng": 77.0095,
        "elevationMeters": 218
      }
    }
  },
  {
    "id": "HOT-JHAJ-03",
    "name": "Jhajjar-Badli Brick Kiln Belt",
    "type": "HYPERLOCAL_HOTSPOT",
    "state": "Haryana",
    "coordinates": {
      "lat": 28.584,
      "lng": 76.852,
      "elevationMeters": 222
    },
    "aqi": 540,
    "pm25": 385,
    "pm10": 590,
    "windSpeedKmh": 5,
    "windDirection": "NW",
    "windBearingDeg": 315,
    "boundaryLayerHeightM": 160,
    "status": "Hazardous",
    "anomalyType": "FCBK (Fixed Chimney Bull's Trench) Unregulated Emission",
    "attributedSource": {
      "clusterName": "Badli Kiln Ring #14-22",
      "clusterType": "Brick Kiln Ring",
      "distanceKm": 6.8,
      "confidencePercent": 86,
      "upwindHeading": "NW",
      "upwindBearingDeg": 315,
      "coordinates": {
        "lat": 28.628,
        "lng": 76.804,
        "elevationMeters": 224
      }
    }
  },
  {
    "id": "HOT-GHAZ-07",
    "name": "Ghazipur Landfill Smolder Core",
    "type": "HYPERLOCAL_HOTSPOT",
    "state": "Delhi NCT",
    "coordinates": {
      "lat": 28.628,
      "lng": 77.3295,
      "elevationMeters": 275
    },
    "aqi": 720,
    "pm25": 530,
    "pm10": 840,
    "windSpeedKmh": 3.8,
    "windDirection": "NNW",
    "windBearingDeg": 335,
    "boundaryLayerHeightM": 130,
    "status": "Hazardous",
    "anomalyType": "Sub-surface Methane Flaring & Rubber Smolder",
    "attributedSource": {
      "clusterName": "East Delhi Municipal Dump Vent #2",
      "clusterType": "Landfill Smolder",
      "distanceKm": 0.9,
      "confidencePercent": 96,
      "upwindHeading": "NNW",
      "upwindBearingDeg": 335,
      "coordinates": {
        "lat": 28.6355,
        "lng": 77.326,
        "elevationMeters": 275
      }
    }
  },
  {
    "id": "HOT-PANIPAT-11",
    "name": "Panipat Agro-Industrial Belt",
    "type": "HYPERLOCAL_HOTSPOT",
    "state": "Haryana",
    "coordinates": {
      "lat": 29.3909,
      "lng": 76.9635,
      "elevationMeters": 219
    },
    "aqi": 615,
    "pm25": 440,
    "pm10": 640,
    "windSpeedKmh": 5.5,
    "windDirection": "NW",
    "windBearingDeg": 312,
    "boundaryLayerHeightM": 155,
    "status": "Hazardous",
    "anomalyType": "Post-Harvest Biomass Residue Burn",
    "attributedSource": {
      "clusterName": "Israna Agricultural Zone Fire Front",
      "clusterType": "Agricultural Burn",
      "distanceKm": 8.2,
      "confidencePercent": 89,
      "upwindHeading": "NW",
      "upwindBearingDeg": 312,
      "coordinates": {
        "lat": 29.445,
        "lng": 76.898,
        "elevationMeters": 221
      }
    }
  }
]

MUNICIPAL_ACTIONS = [
  {
    "grapStage": "GRAP I (Poor)",
    "triggerThresholdPm25": 60,
    "actionTitle": "Mechanized Sweeping & Water Sprinkling",
    "targetAgencies": [
      "MCD Sanitation",
      "PWD Highway Wing"
    ],
    "dispatchedResources": "12 Vacuum Sweepers + 8 Water Tankers",
    "expectedDeltaPm25Percent": -12
  },
  {
    "grapStage": "GRAP II (Very Poor)",
    "triggerThresholdPm25": 120,
    "actionTitle": "Diesel Generator Ban & Dust Suppression",
    "targetAgencies": [
      "Delhi State Electricity Board",
      "Haryana Discom"
    ],
    "dispatchedResources": "Grid Priority Routing + Anti-Smog Mists at Major Bus Stands",
    "expectedDeltaPm25Percent": -18
  },
  {
    "grapStage": "GRAP III (Severe)",
    "triggerThresholdPm25": 250,
    "actionTitle": "Construction Halt & Interstate Freight Diversion",
    "targetAgencies": [
      "Traffic Police Delhi",
      "NHAI Control Room",
      "Pollution Control Boards"
    ],
    "dispatchedResources": "Western Peripheral Expressway Diversion + 24 Fly Squad Inspections",
    "expectedDeltaPm25Percent": -28
  },
  {
    "grapStage": "GRAP IV (Hazardous)",
    "triggerThresholdPm25": 400,
    "actionTitle": "Emergency Industrial Shutdown & School Virtual Shift",
    "targetAgencies": [
      "Directorate of Education",
      "State Industries Department",
      "Disaster Mgmt"
    ],
    "dispatchedResources": "Immediate Smelter Power Cuts + 16 Heavy Anti-Smog Cannons Deployed",
    "expectedDeltaPm25Percent": -39
  }
]

RADIOMETRY_PRESETS = [
  {
    "id": "clean-sky",
    "title": "Clear Sky Calibration (Lutyens Delhi)",
    "environment": "Open Troposphere / High Solar Radiance",
    "iso": 50,
    "aperture": 1.8,
    "shutterSpeedText": "1/4000s",
    "shutterSpeedSeconds": 0.00025,
    "calculatedEv": 14.67,
    "calculatedAod": 0.18,
    "pmEquivalentUgM3": 24,
    "pmCategory": "Good",
    "trustScore": 0.95,
    "antiSpoofChecks": {
      "solarElevationMatch": True,
      "sensorAgreement": True,
      "spatialConsensus": True
    }
  },
  {
    "id": "twilight-haze",
    "title": "Twilight Stubble Smoke (Karnal Belt)",
    "environment": "Dusk Biomass Haze / Forward Light Scattering",
    "iso": 400,
    "aperture": 2,
    "shutterSpeedText": "1/60s",
    "shutterSpeedSeconds": 0.016666666666666666,
    "calculatedEv": 7.97,
    "calculatedAod": 1.54,
    "pmEquivalentUgM3": 385,
    "pmCategory": "Severe",
    "trustScore": 0.91,
    "antiSpoofChecks": {
      "solarElevationMatch": True,
      "sensorAgreement": True,
      "spatialConsensus": True
    }
  },
  {
    "id": "industrial-smog",
    "title": "Dense Industrial Plume (Mundka)",
    "environment": "Opaque Pyrolysis Plume / Low Optical Depth",
    "iso": 800,
    "aperture": 2.2,
    "shutterSpeedText": "1/45s",
    "shutterSpeedSeconds": 0.022222222222222223,
    "calculatedEv": 6.78,
    "calculatedAod": 2.15,
    "pmEquivalentUgM3": 512,
    "pmCategory": "Hazardous",
    "trustScore": 0.89,
    "antiSpoofChecks": {
      "solarElevationMatch": True,
      "sensorAgreement": True,
      "spatialConsensus": True
    }
  }
]

SATELLITE_TIME_SERIES = [
  {
    "time": "13:30 (1:30 PM)",
    "hourFloat": 13.5,
    "nasaFirmsFires": 0,
    "nasaSatellitesOverhead": "MODIS (Aqua/Terra) Polar Orbit Passage",
    "insatAodIndex": 0.28,
    "detectedPlumeIntensity": "Baseline",
    "inversionCeilingM": 850,
    "notes": "NASA polar satellite overpass window. Low thermal anomaly signature under direct noon sun."
  },
  {
    "time": "15:00 (3:00 PM)",
    "hourFloat": 15,
    "nasaFirmsFires": 0,
    "nasaSatellitesOverhead": "None (Polar Satellites over Central Asia)",
    "insatAodIndex": 0.35,
    "detectedPlumeIntensity": "Incipient",
    "inversionCeilingM": 620,
    "notes": "NASA blind spot begins. Ambient surface temperature cools; boundary layer starts descent."
  },
  {
    "time": "16:45 (4:45 PM)",
    "hourFloat": 16.75,
    "nasaFirmsFires": 0,
    "nasaSatellitesOverhead": "None (Overpass Blind Spot)",
    "insatAodIndex": 0.68,
    "detectedPlumeIntensity": "Active",
    "inversionCeilingM": 380,
    "notes": "Agricultural burning initiated across Karnal-Panipat corridor post daytime work shifts."
  },
  {
    "time": "17:45 (5:45 PM)",
    "hourFloat": 17.75,
    "nasaFirmsFires": 0,
    "nasaSatellitesOverhead": "None (Blind Spot Active for next 9 hours)",
    "insatAodIndex": 1.52,
    "detectedPlumeIntensity": "Critical Flare",
    "inversionCeilingM": 190,
    "notes": "TWILIGHT EVASION PEAK: 420-acre burn cluster captured live by ISRO INSAT-3DR 15-minute scan."
  },
  {
    "time": "19:30 (7:30 PM)",
    "hourFloat": 19.5,
    "nasaFirmsFires": 0,
    "nasaSatellitesOverhead": "None (Overpass Blind Spot)",
    "insatAodIndex": 1.88,
    "detectedPlumeIntensity": "Ground Trapped",
    "inversionCeilingM": 130,
    "notes": "Surface radiation inversion lid collapses to 130m, trapping toxic particulate near ground level."
  }
]



import math

def calculate_exposure_value(f_number: float, exposure_time_seconds: float, iso: float) -> float:
    aperture_term = math.log2((f_number * f_number) / exposure_time_seconds)
    iso_term = math.log2(iso / 100)
    return round(aperture_term - iso_term, 2)

def estimate_aod_from_exposure(ev: float, reference_clear_sky_ev: float = 15.0) -> float:
    ev_deficit = max(0.0, reference_clear_sky_ev - ev)
    aod = round(ev_deficit * 0.26, 2)
    return min(3.5, aod)

def compute_reverse_trajectory(
    receptor_lat: float,
    receptor_lng: float,
    wind_speed_kmh: float,
    wind_bearing_deg: float,
    hours_back: float = 2.0
) -> dict:
    distance_km = wind_speed_kmh * hours_back
    bearing_rad = (wind_bearing_deg * math.pi) / 180.0
    delta_lat = (distance_km * math.cos(bearing_rad)) / 111.0
    delta_lng = (distance_km * math.sin(bearing_rad)) / (111.0 * math.cos((receptor_lat * math.pi) / 180.0))
    return {
        "sourceLat": round(receptor_lat + delta_lat, 4),
        "sourceLng": round(receptor_lng + delta_lng, 4),
        "distanceKm": round(distance_km, 1),
    }

def get_naqi_category(pm25: float) -> dict:
    if pm25 <= 30:
        return {"status": "Good", "colorHex": "#34c759", "badgeBg": "#eefbee"}
    if pm25 <= 60:
        return {"status": "Moderate", "colorHex": "#30b0c7", "badgeBg": "#e8f8fb"}
    if pm25 <= 90:
        return {"status": "Poor", "colorHex": "#ff9500", "badgeBg": "#fff8ed"}
    if pm25 <= 120:
        return {"status": "Very Poor", "colorHex": "#ff3b30", "badgeBg": "#ffefee"}
    if pm25 <= 250:
        return {"status": "Severe", "colorHex": "#af52de", "badgeBg": "#f8effd"}
    return {"status": "Hazardous", "colorHex": "#8e0000", "badgeBg": "#ffe5e5"}

calculateExposureValue = calculate_exposure_value
computeReverseTrajectory = compute_reverse_trajectory
estimateAodFromExposure = estimate_aod_from_exposure
getNaqiCategory = get_naqi_category
