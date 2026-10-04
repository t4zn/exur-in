import os
import json
import asyncio
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Literal

from python_backend.advisor_engine import generate_atmospheric_advice

router = APIRouter()

SYSTEM_PROMPT = """You are Exur, an expert atmospheric scientist, environmental epidemiologist, and citizen air quality advisor for India's National Capital Region (Delhi-NCR) and the Indo-Gangetic Corridor, powered by Google Gemma 4 open weights.
Your mission is to translate complex atmospheric physics, ISRO INSAT-3DS satellite AOD imagery, CPCB monitoring station data, and industrial emission registries into clear, compassionate, and highly actionable advice for ordinary citizens.

Grounding Context from Exur Atmospheric Engine:
- Indore (Vijay Nagar / Scheme 78): India's cleanest city (#1 Swachh Survekshan for 7+ years). Typical annual AQI 65-85 (PM2.5 ~38 µg/m³). High plateau ventilation, zero severe industrial smog traps in residential sectors.
- Delhi NCR Regional Baseline: Annual AQI ~235 (PM2.5 ~185 µg/m³), winter inversion peaks >450-700 µg/m³ when boundary layer compresses to 100-150m.
- Relocating an elderly parent with asthma from Indore to Delhi NCR is a high-risk medical decision requiring strict microclimate selection, air purifiers, and hospital proximity.
- Best Delhi NCR microclimates for asthma:
  1. Greater Noida Sector 150 & Pari Chowk Corridor (80% green cover, lowest density, >18km from industrial clusters, Jaypee/Yatharth hospital access).
  2. South Delhi Aravalli Ridge (Vasant Vihar, Chanakyapuri, Mehrauli - protected by dense forest canopy, near AIIMS/Max Saket).
  3. New Gurugram Golf Course Extension (Sectors 58-66 - elevated terrain near Aravalli foothills, near Medanta).
- High-danger zones to avoid for asthmatics: Anand Vihar/Ghazipur (diesel bus terminal + landfill smolder), Mundka/Bawana (plastic pyrolysis & smelting), Okhla/Wazirpur (industrial emissions).
- Core Medical Guidance: True HEPA H13/H14 purifiers with zero ozone; stay in Indore during winter (Oct 25-Jan 15) if possible; close proximity to tertiary pulmonology centers.

Style Guidelines:
- Format in elegant, structured Markdown matching Apple and ChatGPT aesthetics.
- Use clean headings (###), highlighted points, and concise tables where appropriate.
- Be empathetic, scientific, and realistic. Never sugarcoat hazardous air quality for vulnerable respiratory patients."""

def get_suggested_follow_ups(query: str) -> list[str]:
    q = query.lower()
    if any(k in q for k in ["asthma", "parent", "father", "shifting", "indore", "relocat"]):
        return [
            "Which specific air purifier model has true HEPA H13 with zero ozone?",
            "Compare Sector 150 Greater Noida vs Vasant Vihar for living costs & air quality",
            "What are the emergency pulmonary hospitals closest to Sector 150?",
            "Can my father stay in Indore during peak winter inversion months?",
        ]
    if any(k in q for k in ["sector", "noida", "gurgaon", "delhi"]):
        return [
            "Are there industrial brick kilns or factories upwind of Sector 150?",
            "Which areas in Delhi have the worst pollution to avoid at all costs?",
            "What is the average PM2.5 difference between South Delhi and Anand Vihar?",
            "What time of day is safest for outdoor walks in Delhi NCR?",
        ]
    if any(k in q for k in ["purifier", "hepa", "cadr", "filter"]):
        return [
            "How to calculate the exact CADR needed for a 250 sq ft bedroom?",
            "Why must ionizers and UV air purifiers be avoided for asthmatics?",
            "How often do HEPA filters need replacement in Delhi winter?",
        ]
    return [
        "I want to relocate my elderly parents to Delhi NCR. Where is it safest?",
        "Why are Mundka and Anand Vihar pollution hotspots?",
        "What specific air purifier should I buy for an elderly asthma patient?",
        "How does ISRO INSAT-3DS satellite detect twilight stubble fires?",
    ]

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatPayload(BaseModel):
    messages: list[ChatMessage]
    stream: Optional[bool] = False
    modelPreference: Optional[Literal["auto", "gemma", "groq"]] = "auto"

@router.post("/chat")
async def chat_endpoint(payload: ChatPayload):
    messages = payload.messages
    if not messages:
        raise HTTPException(status_code=400, detail="Messages array is required.")

    latest_message = messages[-1].content or ""
    gemma_key = os.environ.get("GEMMA_API_KEY") or os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")
    follow_ups = get_suggested_follow_ups(latest_message)
    model_pref = payload.modelPreference or "auto"

    if payload.stream:
        return StreamingResponse(
            stream_chat_response(messages, latest_message, gemma_key, groq_key, model_pref, follow_ups),
            media_type="text/event-stream"
        )

    # NON-STREAMING JSON MODE
    ai_response_text: Optional[str] = None
    provider_used = "Google Gemma 4 Atmospheric Intelligence Engine"

    # 1. Gemma 4
    if gemma_key and (model_pref == "gemma" or not ai_response_text):
        gemma_models = ["gemma-4-26b-a4b-it", "gemma-4-31b-it"]
        for model_name in gemma_models:
            if ai_response_text:
                break
            try:
                is_oauth = gemma_key.startswith("ya29.")
                headers = {"Content-Type": "application/json"}
                if is_oauth:
                    headers["Authorization"] = f"Bearer {gemma_key}"
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
                else:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemma_key}"

                gemma_contents = [
                    {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
                    for m in messages
                ]
                body = {
                    "contents": [
                        {"role": "user", "parts": [{"text": f"System Context: {SYSTEM_PROMPT}"}]},
                        *gemma_contents
                    ],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 2048,
                    }
                }

                async with httpx.AsyncClient(timeout=14.0) as client:
                    res = await client.post(url, headers=headers, json=body)
                    if res.is_success:
                        data = res.json()
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        non_thought = [p for p in parts if not p.get("thought")]
                        chosen_parts = non_thought if non_thought else parts
                        text = "".join(p.get("text", "") for p in chosen_parts).strip()
                        if text:
                            ai_response_text = text
                            provider_used = f"Google Gemma 4 ({model_name})"
            except Exception as e:
                print(f"[Chat API] Gemma 4 ({model_name}) attempt failed: {e}")

    # 2. Groq LPU
    if groq_key and not ai_response_text and model_pref != "gemma":
        try:
            groq_model = "qwen/qwen3.8-27b"
            groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
                {"role": m.role, "content": m.content} for m in messages
            ]
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={
                        "model": groq_model,
                        "messages": groq_messages,
                        "temperature": 0.3,
                        "max_tokens": 1600,
                    }
                )
                if res.is_success:
                    groq_data = res.json()
                    content = groq_data.get("choices", [{}])[0].get("message", {}).get("content")
                    if content:
                        ai_response_text = content
                        provider_used = f"Exur LPU ({groq_model})"
        except Exception as e:
            print(f"[Chat API] Groq attempt failed: {e}")

    # 3. Fallback
    if not ai_response_text:
        ai_response_text = generate_atmospheric_advice(latest_message)
        provider_used = "Google Gemma 4 Atmospheric Physics Baseline"

    return {
        "success": True,
        "response": ai_response_text,
        "provider": provider_used,
        "suggestedFollowUps": follow_ups,
    }

async def stream_chat_response(messages, latest_message, gemma_key, groq_key, model_pref, follow_ups):
    # 1. Gemma 4 streaming
    if gemma_key and (model_pref == "gemma" or not groq_key):
        try:
            model_name = "gemma-4-26b-a4b-it"
            is_oauth = gemma_key.startswith("ya29.")
            headers = {"Content-Type": "application/json"}
            if is_oauth:
                headers["Authorization"] = f"Bearer {gemma_key}"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent"
            else:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent?key={gemma_key}"

            gemma_contents = [
                {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
                for m in messages
            ]
            body = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"System Context: {SYSTEM_PROMPT}"}]},
                    *gemma_contents
                ],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048}
            }

            async with httpx.AsyncClient(timeout=20.0) as client:
                async with client.stream("POST", url, headers=headers, json=body) as stream_res:
                    if stream_res.is_success:
                        buffer = ""
                        async for chunk in stream_res.aiter_text():
                            buffer += chunk
                            lines = buffer.split("\n")
                            buffer = lines.pop()
                            for line in lines:
                                trimmed = line.strip().lstrip(",").lstrip("[").rstrip("]")
                                if not trimmed:
                                    continue
                                try:
                                    parsed = json.loads(trimmed)
                                    parts = parsed.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                                    for part in parts:
                                        if part.get("text") and not part.get("thought"):
                                            yield f"data: {json.dumps({'token': part['text']})}\n\n"
                                except Exception:
                                    pass

                        yield f"data: {json.dumps({'done': True, 'provider': f'Google Gemma 4 ({model_name})', 'suggestedFollowUps': follow_ups})}\n\n"
                        return
        except Exception as e:
            print(f"[Stream API] Gemma streaming failed: {e}")

    # 2. Groq streaming
    if groq_key and model_pref != "gemma":
        try:
            groq_model = "qwen/qwen3.8-27b"
            groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
                {"role": m.role, "content": m.content} for m in messages
            ]
            async with httpx.AsyncClient(timeout=15.0) as client:
                async with client.stream(
                    "POST",
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={
                        "model": groq_model,
                        "messages": groq_messages,
                        "temperature": 0.3,
                        "max_tokens": 1600,
                        "stream": True,
                    }
                ) as stream_res:
                    if stream_res.is_success:
                        buffer = ""
                        async for chunk in stream_res.aiter_text():
                            buffer += chunk
                            lines = buffer.split("\n")
                            buffer = lines.pop()
                            for line in lines:
                                trimmed = line.strip()
                                if not trimmed or trimmed == "data: [DONE]":
                                    continue
                                if trimmed.startswith("data: "):
                                    try:
                                        obj = json.loads(trimmed[6:])
                                        token = obj.get("choices", [{}])[0].get("delta", {}).get("content")
                                        if token:
                                            yield f"data: {json.dumps({'token': token})}\n\n"
                                    except Exception:
                                        pass

                        yield f"data: {json.dumps({'done': True, 'provider': f'Exur LPU ({groq_model})', 'suggestedFollowUps': follow_ups})}\n\n"
                        return
        except Exception as e:
            print(f"[Stream API] Groq streaming failed: {e}")

    # 3. Fallback streaming
    fallback_text = generate_atmospheric_advice(latest_message)
    # Split into words/tokens
    words = fallback_text.split(" ")
    for i, w in enumerate(words):
        token = w + (" " if i < len(words) - 1 else "")
        yield f"data: {json.dumps({'token': token})}\n\n"
        if i % 3 == 0:
            await asyncio.sleep(0.015)

    yield f"data: {json.dumps({'done': True, 'provider': 'Google Gemma 4 Atmospheric Physics Baseline', 'suggestedFollowUps': follow_ups})}\n\n"
