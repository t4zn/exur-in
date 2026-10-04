import type { ChatSession } from "@/types/advisor";

export const ADVISOR_STORAGE_KEY = "exur_advisor_sessions_v3";
const LEGACY_KEYS = ["exur_advisor_sessions_v2", "tropos_advisor_sessions_v2"];

function normalizeSession(value: unknown): ChatSession | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Partial<ChatSession>;
  if (typeof candidate.id !== "string" || !Array.isArray(candidate.messages)) return null;

  const messages = candidate.messages.filter(
    (message): message is ChatSession["messages"][number] =>
      Boolean(message) &&
      typeof message === "object" &&
      ((message as { role?: string }).role === "user" || (message as { role?: string }).role === "assistant") &&
      typeof (message as { content?: unknown }).content === "string"
  );
  const now = Date.now();
  return {
    id: candidate.id,
    title: typeof candidate.title === "string" && candidate.title.trim() ? candidate.title : "New Conversation",
    createdAt: typeof candidate.createdAt === "number" ? candidate.createdAt : now,
    lastActivityAt: typeof candidate.lastActivityAt === "number" ? candidate.lastActivityAt : now,
    messages,
    pinned: candidate.pinned === true,
    archived: candidate.archived === true,
  };
}

export function loadAdvisorSessions(): ChatSession[] {
  if (typeof window === "undefined") return [];
  for (const key of [ADVISOR_STORAGE_KEY, ...LEGACY_KEYS]) {
    try {
      const stored = window.localStorage.getItem(key);
      if (!stored) continue;
      const parsed: unknown = JSON.parse(stored);
      if (!Array.isArray(parsed)) continue;
      const sessions = parsed.map(normalizeSession).filter((session): session is ChatSession => session !== null);
      if (sessions.length > 0) return sessions;
    } catch {
      // Try the next versioned storage key.
    }
  }
  return [];
}

export function saveAdvisorSessions(sessions: ChatSession[]): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ADVISOR_STORAGE_KEY, JSON.stringify(sessions));
}
