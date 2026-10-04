"use client";

import React, { useState, useRef, useEffect } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import ChatMarkdown from "@/components/ChatMarkdown";
import { useElevenLabsVoice } from "@/hooks/useElevenLabsVoice";
import type { ChatMessage } from "@/types/advisor";

type Message = ChatMessage;

const FLOATING_CHAT_STORAGE_KEY = "exur_floating_advisor_messages_v1";

export default function FloatingAdvisor() {
  const pathname = usePathname();
  // Don't show the floating widget if the user is already on the dedicated /advisor page
  const isAdvisorPage = pathname === "/advisor";

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const { speakingMessageId, speak, error: voiceError } = useElevenLabsVoice();

  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(FLOATING_CHAT_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as Message[];
        if (Array.isArray(parsed)) setMessages(parsed);
      }
    } catch (error) {
      console.warn("Failed to restore floating advisor history", error);
    }
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      try {
        window.localStorage.setItem(FLOATING_CHAT_STORAGE_KEY, JSON.stringify(messages.slice(-80)));
      } catch (error) {
        console.warn("Failed to save floating advisor history", error);
      }
    }
  }, [messages]);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, isLoading, streamingMessageId]);

  if (isAdvisorPage) return null;

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || isLoading) return;

    setInputQuery("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    const userMsg: Message = {
      id: "u-" + Date.now(),
      role: "user",
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const newMsgs = [...messages, userMsg];
    const assistantId = "a-" + Date.now();
    const placeholderAssistant: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      provider: "Connecting...",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages([...newMsgs, placeholderAssistant]);
    setIsLoading(true);
    setStreamingMessageId(assistantId);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: newMsgs.map((m) => ({ role: m.role, content: m.content })),
          stream: true,
        }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error("API failed");

      if (res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let accumulated = "";
        let finalProvider = "Exur Intelligence Engine";
        let finalFollowUps: string[] = [];

        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("data: ")) {
              try {
                const data = JSON.parse(trimmed.slice(6));
                if (data.token) {
                  accumulated += data.token;
                  setMessages((prev) =>
                    prev.map((m) => (m.id === assistantId ? { ...m, content: accumulated } : m))
                  );
                }
                if (data.done) {
                  if (data.provider) finalProvider = data.provider;
                  if (data.suggestedFollowUps) finalFollowUps = data.suggestedFollowUps;
                }
              } catch {
                // ignore
              }
            }
          }
        }

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: accumulated || "No response received.",
                  provider: finalProvider,
                  suggestedFollowUps: finalFollowUps,
                }
              : m
          )
        );
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
      } else {
        console.error(err);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: "⚠️ Atmospheric intelligence temporarily unavailable. Please try again.",
                }
              : m
          )
        );
      }
    } finally {
      setIsLoading(false);
      setStreamingMessageId(null);
      abortControllerRef.current = null;
    }
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setStreamingMessageId(null);
  };

  const handleSpeak = async (id: string, text: string) => {
    try {
      await speak(id, text);
    } catch {
      if (!("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(
        text.replace(/[#>*_`~]/g, "").replace(/\|/g, " ").replace(/\s+/g, " ").trim()
      );
      utterance.rate = 1.05;
      window.speechSynthesis.speak(utterance);
    }
  };

  const samplePrompt =
    "I am moving my asthmatic father from Indore (Scheme 78) to Delhi NCR. Best place to live?";

  return (
    <>
      {/* ─── Floating Trigger Button (Bottom-Right Apple Capsule) ───────────── */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            zIndex: 999,
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "10px 18px",
            borderRadius: "9999px",
            backgroundColor: "#ffffff",
            color: "#1f2937",
            border: "1px solid #dbe2ea",
            boxShadow:
              "0 10px 30px rgba(15, 23, 42, 0.16)",
            cursor: "pointer",
            fontSize: "13px",
            fontWeight: 600,
            transition: "all 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "scale(1.04)";
            e.currentTarget.style.borderColor = "rgba(41, 151, 255, 0.6)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "scale(1)";
            e.currentTarget.style.borderColor = "#dbe2ea";
          }}
        >
          {/* Apple Intelligence Aura Glyph */}
          <div
            style={{
              width: "18px",
              height: "18px",
              borderRadius: "50%",
              background:
                "conic-gradient(from 180deg, #00f2fe, #4facfe, #0071e3, #f093fb, #00f2fe)",
              boxShadow: "0 0 10px rgba(41, 151, 255, 0.5)",
            }}
          />
          <span>✦ Exur</span>
        </button>
      )}

      {/* ─── Apple Popover Floating Glass Window (ChatGPT Experience) ─────────── */}
      {isOpen && (
        <div
          style={{
            position: "fixed",
            bottom: "20px",
            right: "20px",
            width: "440px",
            maxWidth: "calc(100vw - 32px)",
            height: "620px",
            maxHeight: "calc(100vh - 40px)",
            backgroundColor: "#ffffff",
            border: "1px solid #dbe2ea",
            borderRadius: "24px",
            boxShadow:
              "0 22px 60px rgba(15, 23, 42, 0.18)",
            zIndex: 1000,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            animation: "fadeIn 0.25s ease-out",
          }}
        >
          {/* Drawer Header */}
          <div
            style={{
              padding: "14px 18px",
              borderBottom: "1px solid #e5e7eb",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              backgroundColor: "#f8fafc",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "9px" }}>
              <div
                style={{
                  width: "16px",
                  height: "16px",
                  borderRadius: "50%",
                  background:
                    "conic-gradient(from 180deg, #00f2fe, #4facfe, #0071e3, #f093fb, #00f2fe)",
                }}
              />
              <span style={{ fontSize: "14px", fontWeight: 650, color: "#1f2937" }}>
                Exur
              </span>
              <span
                style={{
                  fontSize: "10px",
                  backgroundColor: "rgba(41, 151, 255, 0.15)",
                  color: "#2997ff",
                  padding: "2px 7px",
                  borderRadius: "999px",
                  fontWeight: 600,
                }}
              >
                LPU Live
              </span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              {/* Fullscreen Advisor Link */}
              <Link
                href="/advisor"
                title="Open Fullscreen ChatGPT Mode"
                style={{
                  color: "#475569",
                  textDecoration: "none",
                  fontSize: "12px",
                  padding: "4px 8px",
                  borderRadius: "6px",
                  backgroundColor: "#eef2f7",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                <span>↗ Fullscreen</span>
              </Link>

              {/* Close Button */}
              <button
                onClick={() => setIsOpen(false)}
                title="Close"
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#64748b",
                  cursor: "pointer",
                  padding: "4px",
                  fontSize: "14px",
                }}
              >
                ✕
              </button>
            </div>
          </div>

          {/* Messages Stream */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
          >
            {messages.length === 0 && (
              <div style={{ textAlign: "center", padding: "28px 12px" }}>
                <div
                  style={{
                    width: "44px",
                    height: "44px",
                    borderRadius: "50%",
                    background:
                      "conic-gradient(from 180deg, #00f2fe, #4facfe, #0071e3, #f093fb, #00f2fe)",
                    boxShadow: "0 0 20px rgba(41, 151, 255, 0.4)",
                    margin: "0 auto 16px auto",
                  }}
                />
                <div
                  style={{
                    fontSize: "15px",
                    fontWeight: 650,
                    color: "#1f2937",
                    marginBottom: "6px",
                  }}
                >
                  Atmospheric Intelligence
                </div>
                <p
                  style={{
                    fontSize: "13px",
                    color: "#64748b",
                    lineHeight: 1.45,
                    marginBottom: "20px",
                  }}
                >
                  Ask about family relocation, asthma protection, or neighborhood air pollution.
                </p>

                <button
                  onClick={() => handleSendMessage(samplePrompt)}
                  style={{
                    width: "100%",
                    backgroundColor: "rgba(41, 151, 255, 0.08)",
                    border: "1px solid rgba(41, 151, 255, 0.25)",
                    borderRadius: "14px",
                    padding: "12px 14px",
                    textAlign: "left",
                    color: "#334155",
                    fontSize: "12px",
                    cursor: "pointer",
                    lineHeight: 1.4,
                  }}
                >
                  <div style={{ fontWeight: 600, color: "#2997ff", marginBottom: "4px" }}>
                    Try Popular Query:
                  </div>
                  "{samplePrompt}" &rarr;
                </button>
              </div>
            )}

            {messages.map((m) => {
              const isUser = m.role === "user";
              const isStreamingThis = m.id === streamingMessageId;

              return (
                <div
                  key={m.id}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: isUser ? "flex-end" : "flex-start",
                    width: "100%",
                  }}
                >
                  {isUser ? (
                    <div
                      style={{
                        maxWidth: "85%",
                        backgroundColor: "#e8f0fe",
                        border: "1px solid #c7d7f5",
                        borderRadius: "18px 18px 4px 18px",
                        padding: "10px 14px",
                        fontSize: "14px",
                        color: "#1f2937",
                        lineHeight: 1.45,
                        wordBreak: "break-word",
                      }}
                    >
                      {m.content}
                    </div>
                  ) : (
                    <div style={{ width: "100%" }}>
                      <div
                        style={{
                          fontSize: "11px",
                          color: "#64748b",
                          marginBottom: "4px",
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                        }}
                      >
                        <span style={{ color: "#2997ff", fontWeight: 600 }}>Exur</span>
                        <span>&bull;</span>
                        <span>{m.timestamp}</span>
                      </div>

                      <ChatMarkdown content={m.content} isStreaming={isStreamingThis} />
                      {!isStreamingThis && m.content && (
                        <div style={{ display: "flex", gap: "6px", marginTop: "8px" }}>
                          <button
                            type="button"
                            onClick={() => handleSpeak(m.id, m.content)}
                            aria-label={speakingMessageId === m.id ? "Stop voice" : "Read response aloud"}
                            style={{
                              border: "1px solid rgba(255,255,255,0.12)",
                              borderRadius: "8px",
                              padding: "4px 8px",
                              color: speakingMessageId === m.id ? "#1d4ed8" : "#64748b",
                              background: "#f1f5f9",
                              cursor: "pointer",
                              fontSize: "11px",
                            }}
                          >
                            {speakingMessageId === m.id ? "Stop voice" : "Read aloud"}
                          </button>
                        </div>
                      )}

                      {/* Follow-up chips */}
                      {!isStreamingThis &&
                        m.suggestedFollowUps &&
                        m.suggestedFollowUps.length > 0 && (
                          <div
                            style={{
                              display: "flex",
                              flexWrap: "wrap",
                              gap: "6px",
                              marginTop: "10px",
                            }}
                          >
                            {voiceError && (
                              <div role="status" style={{ color: "rgba(255,190,190,0.9)", fontSize: "11px", marginBottom: "8px" }}>
                                ElevenLabs unavailable; browser voice fallback is available.
                              </div>
                            )}
                            {m.suggestedFollowUps.slice(0, 2).map((fu, fIdx) => (
                              <button
                                key={fIdx}
                                onClick={() => handleSendMessage(fu)}
                                style={{
                                  backgroundColor: "rgba(41, 151, 255, 0.08)",
                                  border: "1px solid rgba(41, 151, 255, 0.2)",
                                  borderRadius: "12px",
                                  padding: "4px 10px",
                                  fontSize: "11px",
                                  color: "#334155",
                                  cursor: "pointer",
                                  textAlign: "left",
                                }}
                              >
                                {fu} &rarr;
                              </button>
                            ))}
                          </div>
                        )}
                    </div>
                  )}
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Capsule Dock */}
          <div
            style={{
              padding: "12px 14px 14px",
              borderTop: "1px solid #e5e7eb",
              backgroundColor: "#f8fafc",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "flex-end",
                gap: "8px",
                backgroundColor: "#ffffff",
                border: "1px solid #dbe2ea",
                borderRadius: "20px",
                padding: "6px 8px 6px 14px",
              }}
            >
              <textarea
                ref={textareaRef}
                rows={1}
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Ask Exur..."
                style={{
                  flex: 1,
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: "#1f2937",
                  fontSize: "14px",
                  lineHeight: 1.4,
                  maxHeight: "120px",
                  resize: "none",
                  padding: "5px 0",
                  fontFamily: "inherit",
                }}
              />

              {isLoading ? (
                <button
                  onClick={handleStopGeneration}
                  title="Stop"
                  style={{
                    width: "30px",
                    height: "30px",
                    borderRadius: "50%",
                    backgroundColor: "#ffffff",
                    border: "none",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: "pointer",
                  }}
                >
                  <div
                    style={{
                      width: "10px",
                      height: "10px",
                      backgroundColor: "#1f2937",
                      borderRadius: "2px",
                    }}
                  />
                </button>
              ) : (
                <button
                  onClick={() => handleSendMessage()}
                  disabled={!inputQuery.trim()}
                  title="Send"
                  style={{
                    width: "30px",
                    height: "30px",
                    borderRadius: "50%",
                    backgroundColor: inputQuery.trim() ? "#2563eb" : "#dbe2ea",
                    border: "none",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: inputQuery.trim() ? "pointer" : "default",
                    color: "#ffffff",
                    fontSize: "14px",
                    fontWeight: 700,
                  }}
                >
                  &uarr;
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
