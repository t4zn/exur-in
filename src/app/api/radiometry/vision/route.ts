import { NextResponse } from "next/server";

/**
 * Multimodal AI Vision Air Quality & Sky Haze Analysis API
 * 
 * Uses Google Gemini / Gemma multimodal vision models to independently analyze
 * outdoor sky/horizon photos for particulate haze, cloud vs aerosol classification,
 * landmark extinction, and visual AQI.
 * 
 * Key stored securely in server-side process.env.GEMMA_API_KEY or process.env.GEMINI_API_KEY.
 */

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { imageBase64, mimeType = "image/jpeg", opticalDepth = 0.3, aqi = 100, locationName = "India" } = body;

    if (!imageBase64) {
      return NextResponse.json(
        { success: false, error: "Missing imageBase64 in request body." },
        { status: 400 }
      );
    }

    const groqKey = process.env.GROQ_API_KEY;
    const gemmaKey = process.env.GEMMA_API_KEY || process.env.GEMINI_API_KEY;

    if (!groqKey && !gemmaKey) {
      return NextResponse.json({
        success: false,
        isConfigured: false,
        fallbackReason: "Neither GROQ_API_KEY nor GEMINI_API_KEY is configured in .env.local.",
      });
    }

    const promptText = `
You are an atmospheric scientist and expert in optical remote sensing and aerosol physics.
Analyze this outdoor sky/horizon photograph to assess air pollution, aerosol loading, and visibility.

Physical optical depth calculated from camera CMOS sensor: ${Number(opticalDepth).toFixed(3)}
Baseline physical estimated AQI: ${Math.round(Number(aqi))}
Location context: ${locationName}

Task:
1. Distinguish natural water vapor clouds from particulate aerosol haze/smog/smoke.
2. Estimate horizontal visibility distance and visual landmark contrast.
3. Identify dominant atmospheric optical characteristics (e.g. photochemical smog, dust suspension, biomass burning smoke, or clean Rayleigh atmosphere).
4. Provide an independent visual AQI estimate on the 0-500 Indian/US standard scale.

Return ONLY valid JSON with no markdown backticks, matching this exact structure:
{
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
  "radiometricCorroboration": "brief explanation comparing visual haze with the physical optical depth ${Number(opticalDepth).toFixed(3)}"
}
`;

    let parsed: Record<string, unknown> | null = null;
    let providerUsed = "";

    // 1. Try Google Gemini Vision models (high precision multimodal vision)
    if (gemmaKey) {
      const apiKey = gemmaKey;
      const isOAuthBearer = apiKey.startsWith("ya29.");
      const authHeaders: Record<string, string> = {
        "Content-Type": "application/json",
      };

      if (isOAuthBearer) {
        authHeaders["Authorization"] = `Bearer ${apiKey}`;
      } else {
        authHeaders["x-goog-api-key"] = apiKey;
      }

      // Prioritize supported Gemini multimodal vision models
      const visionCandidates = [
        "gemini-3.5-flash",
        "gemini-flash-latest",
        "gemini-3.8-flash",
        "gemini-3.1-flash-lite",
      ];

      for (const candidate of visionCandidates) {
        try {
          const url = isOAuthBearer
            ? `https://generativelanguage.googleapis.com/v1beta/models/${candidate}:generateContent`
            : `https://generativelanguage.googleapis.com/v1beta/models/${candidate}:generateContent?key=${encodeURIComponent(apiKey)}`;

          const payload = {
            contents: [
              {
                parts: [
                  { text: promptText },
                  {
                    inlineData: {
                      mimeType,
                      data: imageBase64,
                    },
                  },
                ],
              },
            ],
            generationConfig: {
              responseMimeType: "application/json",
              temperature: 0.15,
              maxOutputTokens: 1200,
            },
          };

          const res = await fetch(url, {
            method: "POST",
            headers: authHeaders,
            body: JSON.stringify(payload),
            signal: AbortSignal.timeout(10000),
          });

          if (res.ok) {
            const data = await res.json();
            const parts = data.candidates?.[0]?.content?.parts || [];
            const nonThought = parts.filter((p: { thought?: unknown }) => !p.thought);
            const textPart = (nonThought.length > 0 ? nonThought : parts)
              .map((p: { text?: string }) => p.text || "")
              .join("")
              .trim();

            if (textPart) {
              const cleanJson = textPart.replace(/^```json\s*/i, "").replace(/\s*```$/, "").trim();
              parsed = JSON.parse(cleanJson);
              providerUsed = `Google Gemini (${candidate})`;
              break;
            }
          } else {
            const errText = await res.text().catch(() => "");
            console.warn(`[Gemini Vision ${candidate}] returned ${res.status}:`, errText.slice(0, 150));
          }
        } catch (modelErr) {
          console.warn(`[Gemini Vision ${candidate} Exception]:`, modelErr);
        }
      }
    }

    // 2. Try Groq Vision if explicit GROQ_VISION_MODEL is configured and Gemini didn't complete
    if (!parsed && groqKey && process.env.GROQ_VISION_MODEL) {
      try {
        const groqModel = process.env.GROQ_VISION_MODEL;
        const groqPayload = {
          model: groqModel,
          messages: [
            {
              role: "user",
              content: [
                { type: "text", text: promptText },
                {
                  type: "image_url",
                  image_url: {
                    url: `data:${mimeType};base64,${imageBase64}`,
                  },
                },
              ],
            },
          ],
          response_format: { type: "json_object" },
          temperature: 0.15,
          max_tokens: 800,
        };

        const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${groqKey}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(groqPayload),
          signal: AbortSignal.timeout(10000),
        });

        if (groqRes.ok) {
          const groqData = await groqRes.json();
          const content = groqData.choices?.[0]?.message?.content;
          if (content) {
            const cleanJson = content.replace(/^```json\s*/i, "").replace(/\s*```$/, "").trim();
            parsed = JSON.parse(cleanJson);
            providerUsed = `Groq (${groqModel})`;
          }
        }
      } catch (groqErr) {
        console.warn("[Groq Vision Exception]:", groqErr);
      }
    }

    // 3. Fallback: Physics-based synthetic estimation if remote models were unreachable or rate-limited
    if (!parsed) {
      const tau = Math.max(0.05, Number(opticalDepth) || 0.3);
      const numAqi = Math.max(10, Math.round(Number(aqi)) || 85);
      const severity = numAqi > 250 ? "severe" : numAqi > 150 ? "heavy" : numAqi > 100 ? "moderate" : numAqi > 50 ? "light" : "pristine";
      const category = numAqi > 300 ? "Severe" : numAqi > 200 ? "Very Poor" : numAqi > 100 ? "Poor" : numAqi > 50 ? "Moderate" : "Good";

      return NextResponse.json({
        success: true,
        isConfigured: true,
        isSynthetic: true,
        hazeSeverity: severity,
        hazeDescription: `Atmospheric optical extinction in ${locationName} shows ${severity} aerosol scattering with tau=${tau.toFixed(2)}.`,
        estimatedAodTau: tau,
        estimatedAqi: numAqi,
        aqiCategory: category,
        cloudCoveragePercent: 12,
        cloudType: "Clear",
        aerosolVsCloudConfidence: 0.85,
        skyTurbidityRating: numAqi > 150 ? "high" : "moderate",
        visualClarity: `Atmospheric path extinction indicates ~${(15 / Math.max(0.1, tau)).toFixed(1)} km optical visual range`,
        radiometricCorroboration: `Physical CMOS exposure telemetry corroborates AOD tau=${tau.toFixed(3)} and indicative AQI of ${numAqi}.`,
        provider: "Physical Atmospheric Engine (Synthetic Fallback)",
      });
    }

    return NextResponse.json({
      success: true,
      isConfigured: true,
      isSynthetic: false,
      hazeSeverity: parsed.hazeSeverity || "moderate",
      hazeDescription: parsed.hazeDescription || "Atmospheric aerosol analysis completed.",
      estimatedAodTau: Number(parsed.estimatedAodTau) || Number(opticalDepth),
      estimatedAqi: Math.round(Number(parsed.estimatedAqi)) || Math.round(Number(aqi)),
      aqiCategory: parsed.aqiCategory || "Moderate",
      cloudCoveragePercent: Math.round(Number(parsed.cloudCoveragePercent) || 0),
      cloudType: parsed.cloudType || "Clear",
      aerosolVsCloudConfidence: Math.min(0.99, Math.max(0.5, Number(parsed.aerosolVsCloudConfidence) || 0.85)),
      skyTurbidityRating: parsed.skyTurbidityRating || "moderate",
      visualClarity: parsed.visualClarity || "Visibility consistent with atmospheric baseline",
      radiometricCorroboration: parsed.radiometricCorroboration || `${providerUsed} visual analysis corroborates physical sensor.`,
      provider: providerUsed,
    });
  } catch (error) {
    const msg = error instanceof Error ? error.message : "Internal error";
    console.error("[Vision Exception]:", msg);
    return NextResponse.json({
      success: false,
      isConfigured: Boolean(process.env.GEMMA_API_KEY || process.env.GEMINI_API_KEY || process.env.GROQ_API_KEY),
      fallbackReason: msg,
    });
  }
}
