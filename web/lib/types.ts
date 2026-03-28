export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

export interface MemoryEntry {
  id: string;
  content: string;
  salience: number;
  createdAt: number;
  accessCount: number;
  source: "extracted" | "manual";
}

export interface MemorySearchResult extends MemoryEntry {
  score: number;
}
