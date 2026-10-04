export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  provider?: string;
  suggestedFollowUps?: string[];
  timestamp: string;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  lastActivityAt: number;
  messages: ChatMessage[];
  pinned?: boolean;
  archived?: boolean;
}
