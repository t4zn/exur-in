import os
import json
import httpx
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/radiometry")

# ─────────────────────────────────────────────────────────────────────────────
# 1. OpenAQ Proxy
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/openaq")
async def openaq_proxy(
    response: Response,
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius: Optional[str] = Query("50000"),
):
    longitude = lon if lon is not None else lng
    if lat is None or longitude is None:
        raise HTTPException(status_code=400, detail="Invalid coordinates provided")

    api_key = os.environ.get("OPENAQ_API_KEY", "")
    url = f"https://api.openaq.org/v3/locations?coordinates={lat},{longitude}&radius={radius}&limit=10"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url, headers=headers)

        if not res.is_success:
            print(f"[OpenAQ Proxy] OpenAQ returned {res.status_code}: {res.text}")
            return JSONResponse(
                content={"error": f"OpenAQ returned {res.status_code}", "results": []},
                status_code=res.status_code
            )

        data = res.json()
        response.headers["Cache-Control"] = "public, s-maxage=300, stale-while-revalidate=120"
        return data
    except Exception as e:
        print(f"[OpenAQ Proxy Exception]: {e}")
        raise HTTPException(status_code=502, detail=f"OpenAQ fetch failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Gemma 4 / Groq Vision Air Quality & Sky Haze Analyzer
# ─────────────────────────────────────────────────────────────────────────────
class VisionPayload(BaseModel):
    imageBase64: str
    mimeType: Optional[str] = "image/jpeg"
    opticalDepth: Optional[float] = 0.3
    aqi: Optional[float] = 100.0
    locationName: Optional[str] = "India"

@router.post("/vision")
async def vision_analyzer(payload: VisionPayload):
    image_base64 = payload.imageBase64
    mime_type = payload.mimeType or "image/jpeg"
    optical_depth = payload.opticalDepth or 0.3
    aqi = payload.aqi or 100.0
    location_name = payload.locationName or "India"

    if not image_base64:
        raise HTTPException(status_code=400, detail="Missing imageBase64 in request body.")

    groq_key = os.environ.get("GROQ_API_KEY")
    gemma_key = os.environ.get("GEMMA_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if not groq_key and not gemma_key:
        return {
            "success": False,
            "isConfigured": False,
            "fallbackReason": "Neither GROQ_API_KEY nor GEMMA_API_KEY is set in .env.local. Add one to enable live AI vision analysis.",
        }

    prompt_text = f"""You are an atmospheric scientist and expert in optical remote sensing and aerosol physics.
Analyze this outdoor sky/horizon photograph to assess air pollution, aerosol loading, and visibility.

Physical optical depth calculated from camera CMOS sensor: {float(optical_depth):.3f}
Baseline physical estimated AQI: {round(float(aqi))}
Location context: {location_name}

Task:
1. Distinguish natural water vapor clouds from particulate aerosol haze/smog/smoke.
2. Estimate horizontal visibility distance and visual landmark contrast.
3. Identify dominant atmospheric optical characteristics (e.g. photochemical smog, dust suspension, biomass burning smoke, or clean Rayleigh atmosphere).
4. Provide an independent visual AQI estimate on the 0-500 Indian/US standard scale.

Return ONLY valid JSON with no markdown backticks, matching this exact structure:
{{
  "hazeSeverity": "pristine" | "light" | "moderate" | "heavy" | "severe",
  "hazeDescription": "1-2 concise sentences summarizing the atmospheric conditions and particulate load",
  "estimatedAodTau": number between 0.05 and 3.0,
  "estimatedAqi": integer between 0 and 500,
  "aqiCategory": "Good" | "Moderate" | "Poor" | "Very Poor" | "Severe" | "Hazardous",
  "cloudCoveragePercent": number between 0 and 100,
  "cloudType": "Clear" | "Cirrus" | "Cumulus" | "Stratus" | "Overcast" | "Inversion Smog Layer",
  "aerosolVsCloudConfidence": number between 0.5 and 0.99,
  "skyTurbidityRating": "low" | "moderate" | "high" | "extreme",
  "visualClarity": "e.g. Horizon contrast indicates ~3.2 km visibility",
  "radiometricCorroboration": "brief explanation comparing visual haze with the physical optical depth {float(optical_depth):.3f}"
}}"""

    parsed: Optional[dict] = None

    # 1. Groq Vision
    if groq_key:
        try:
            groq_model = os.environ.get("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")
            groq_payload = {
                "model": groq_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{image_base64}"},
                            },
                        ],
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.15,
                "max_tokens": 800,
            }

            async with httpx.AsyncClient(timeout=14.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json=groq_payload
                )
                if res.is_success:
                    content = res.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    clean_json = content.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)
        except Exception as e:
            print(f"[Groq Vision Exception]: {e}")

    # 2. Gemma 4 / Gemini Vision
    if not parsed and gemma_key:
        try:
            is_oauth = gemma_key.startswith("ya29.")
            headers = {"Content-Type": "application/json"}
            if is_oauth:
                headers["Authorization"] = f"Bearer {gemma_key}"

            model_name = "gemini-2.5-flash"
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
                if is_oauth
                else f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemma_key}"
            )

            gemma_payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt_text},
                            {
                                "inlineData": {
                                    "mimeType": mime_type,
                                    "data": image_base64,
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.15,
                    "maxOutputTokens": 1200,
                }
            }

            async with httpx.AsyncClient(timeout=16.0) as client:
                res = await client.post(url, headers=headers, json=gemma_payload)
                if res.is_success:
                    data = res.json()
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    non_thought = [p for p in parts if not p.get("thought")]
                    chosen_parts = non_thought if non_thought else parts
                    text_part = "".join(p.get("text", "") for p in chosen_parts).strip()
                    if text_part:
                        clean_json = text_part.replace("```json", "").replace("```", "").strip()
                        parsed = json.loads(clean_json)
        except Exception as e:
            print(f"[Gemma Vision Exception]: {e}")

    if not parsed:
        return {
            "success": False,
            "isConfigured": True,
            "fallbackReason": "Vision AI model did not return valid analysis.",
        }

    return {
        "success": True,
        "isConfigured": True,
        "isSynthetic": False,
        "hazeSeverity": parsed.get("hazeSeverity", "moderate"),
        "hazeDescription": parsed.get("hazeDescription", "Atmospheric aerosol analysis completed."),
        "estimatedAodTau": float(parsed.get("estimatedAodTau", optical_depth)),
        "estimatedAqi": round(float(parsed.get("estimatedAqi", aqi))),
        "aqiCategory": parsed.get("aqiCategory", "Moderate"),
        "cloudCoveragePercent": round(float(parsed.get("cloudCoveragePercent", 0))),
        "cloudType": parsed.get("cloudType", "Clear"),
        "aerosolVsCloudConfidence": min(0.99, max(0.5, float(parsed.get("aerosolVsCloudConfidence", 0.85)))),
        "skyTurbidityRating": parsed.get("skyTurbidityRating", "moderate"),
        "visualClarity": parsed.get("visualClarity", "Visibility consistent with atmospheric baseline"),
        "radiometricCorroboration": parsed.get("radiometricCorroboration", "AI visual analysis corroborates physical sensor."),
    }
