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

function splitSpeech(text: string): string[] {
  const sentences = text.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [text];
  const chunks: string[] = [];
  let current = "";
  for (const sentence of sentences) {
    const next = `${current} ${sentence}`.trim();
    if (next.length > 700 && current) {
      chunks.push(current);
      current = sentence.trim();
    } else {
      current = next;
    }
  }
  if (current) chunks.push(current);
  return chunks;
}

export function useElevenLabsVoice(): UseElevenLabsVoiceReturn {
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const requestControllerRef = useRef<AbortController | null>(null);
  const activeMessageIdRef = useRef<string | null>(null);

  const stop = useCallback(() => {
    requestControllerRef.current?.abort();
    requestControllerRef.current = null;
    audioRef.current?.pause();
    audioRef.current = null;
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
    setIsLoading(false);
    setSpeakingMessageId(null);
    activeMessageIdRef.current = null;
  }, []);

  const speak = useCallback(async (messageId: string, text: string) => {
    if (activeMessageIdRef.current === messageId) {
      stop();
      return;
    }

    stop();
    const chunks = splitSpeech(stripMarkdown(text));
    if (!chunks.length) return;

    setError(null);
    setIsLoading(true);
    activeMessageIdRef.current = messageId;
    const requestController = new AbortController();
    requestControllerRef.current = requestController;

    try {
      setIsLoading(false);
      setSpeakingMessageId(messageId);
      for (const chunk of chunks) {
        if (requestController.signal.aborted) return;
        const response = await fetch("/api/voice", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: chunk }),
          signal: requestController.signal,
        });
        if (!response.ok) {
          const body = await response.json().catch(() => null);
          throw new Error(body?.error || `Voice request failed (${response.status})`);
        }
        const url = URL.createObjectURL(await response.blob());
        objectUrlRef.current = url;
        const audio = new Audio(url);
        audioRef.current = audio;
        await new Promise<void>((resolve, reject) => {
          audio.onended = () => resolve();
          audio.onerror = () => reject(new Error("Voice playback failed."));
          void audio.play().catch(reject);
        });
        URL.revokeObjectURL(url);
        objectUrlRef.current = null;
      }
      stop();
    } catch (caught) {
      if (requestController.signal.aborted) return;
      stop();
      setError(caught instanceof Error ? caught.message : "Voice playback failed.");
      throw caught;
    }
  }, [stop]);

  useEffect(() => stop, [stop]);

  return { speakingMessageId, isLoading, error, speak, stop };
}
