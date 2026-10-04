import { NextRequest, NextResponse } from "next/server";

const MAX_TEXT_LENGTH = 8000;

export async function POST(request: NextRequest) {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  const voiceId = process.env.ELEVENLABS_VOICE_ID;
  const modelId = process.env.ELEVENLABS_MODEL_ID || "eleven_multilingual_v2";

  if (!apiKey || !voiceId) {
    return NextResponse.json(
      { error: "ElevenLabs voice is not configured. Add ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID." },
      { status: 503 }
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Request body must be valid JSON." }, { status: 400 });
  }

  const text = body && typeof body === "object" && "text" in body ? (body as { text?: unknown }).text : undefined;
  if (typeof text !== "string" || !text.trim()) {
    return NextResponse.json({ error: "A non-empty text value is required." }, { status: 400 });
  }
  if (text.length > MAX_TEXT_LENGTH) {
    return NextResponse.json({ error: `Text must be ${MAX_TEXT_LENGTH} characters or fewer.` }, { status: 413 });
  }

  try {
    const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${encodeURIComponent(voiceId)}`, {
      method: "POST",
      headers: {
        Accept: "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": apiKey,
      },
      body: JSON.stringify({
        text: text.trim(),
        model_id: modelId,
        voice_settings: { stability: 0.48, similarity_boost: 0.75, style: 0.15, use_speaker_boost: true },
      }),
      signal: AbortSignal.timeout(30000),
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      console.error("[Voice API] ElevenLabs request failed", response.status, detail.slice(0, 300));
      return NextResponse.json(
        { error: response.status === 429 ? "ElevenLabs rate limit reached. Please try again shortly." : "ElevenLabs could not generate audio." },
        { status: response.status === 429 ? 429 : 502 }
      );
    }

    return new Response(await response.arrayBuffer(), {
      status: 200,
      headers: { "Content-Type": "audio/mpeg", "Cache-Control": "private, no-store" },
    });
  } catch (error) {
    console.error("[Voice API] Upstream request failed", error);
    return NextResponse.json({ error: "Voice service is temporarily unavailable." }, { status: 502 });
  }
}
