"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface UseElevenLabsVoiceReturn {
  speakingMessageId: string | null;
  isLoading: boolean;
  error: string | null;
  speak: (messageId: string, text: string) => Promise<void>;
  stop: () => void;
}

function stripMarkdown(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/[#>*_`~]/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\|/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function useElevenLabsVoice(): UseElevenLabsVoiceReturn {
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  const stop = useCallback(() => {
    audioRef.current?.pause();
    audioRef.current = null;
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
    setIsLoading(false);
    setSpeakingMessageId(null);
  }, []);

  const speak = useCallback(async (messageId: string, text: string) => {
    if (speakingMessageId === messageId) {
      stop();
      return;
    }

    stop();
    const cleanText = stripMarkdown(text);
    if (!cleanText) return;

    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch("/api/voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: cleanText }),
        signal: AbortSignal.timeout(30000),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.error || `Voice request failed (${response.status})`);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      objectUrlRef.current = url;
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = stop;
      audio.onerror = () => {
        setError("Voice playback failed. Check the ElevenLabs configuration.");
        stop();
      };
      setIsLoading(false);
      setSpeakingMessageId(messageId);
      await audio.play();
    } catch (caught) {
      stop();
      setError(caught instanceof Error ? caught.message : "Voice playback failed.");
      throw caught;
    }
  }, [speakingMessageId, stop]);

  useEffect(() => stop, [stop]);

  return { speakingMessageId, isLoading, error, speak, stop };
}
