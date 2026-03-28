/**
 * localStorage-based memory and conversation store.
 * Simple MVP — no database needed.
 */

import { Conversation, MemoryEntry, Message } from "./types";

const CONVERSATIONS_KEY = "openconch_conversations";
const MEMORIES_KEY = "openconch_memories";

// ── Conversations ──

export function getConversations(): Conversation[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(CONVERSATIONS_KEY);
  return raw ? JSON.parse(raw) : [];
}

export function saveConversations(conversations: Conversation[]) {
  if (typeof window === "undefined") return;
  localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations));
}

export function getConversation(id: string): Conversation | undefined {
  return getConversations().find((c) => c.id === id);
}

export function saveConversation(conversation: Conversation) {
  const all = getConversations();
  const idx = all.findIndex((c) => c.id === conversation.id);
  if (idx >= 0) {
    all[idx] = conversation;
  } else {
    all.unshift(conversation);
  }
  saveConversations(all);
}

export function deleteConversation(id: string) {
  const all = getConversations().filter((c) => c.id !== id);
  saveConversations(all);
}

// ── Memories ──

export function getMemories(): MemoryEntry[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(MEMORIES_KEY);
  return raw ? JSON.parse(raw) : [];
}

export function saveMemories(memories: MemoryEntry[]) {
  if (typeof window === "undefined") return;
  localStorage.setItem(MEMORIES_KEY, JSON.stringify(memories));
}

export function addMemory(memory: MemoryEntry) {
  const all = getMemories();
  all.unshift(memory);
  saveMemories(all);
}

export function deleteMemory(id: string) {
  const all = getMemories().filter((m) => m.id !== id);
  saveMemories(all);
}

export function searchMemories(query: string, topK: number = 5): MemoryEntry[] {
  const all = getMemories();
  if (!query.trim() || all.length === 0) return all.slice(0, topK);

  const queryWords = new Set(query.toLowerCase().split(/\s+/));

  const scored = all.map((mem) => {
    const memWords = mem.content.toLowerCase().split(/\s+/);
    let matchCount = 0;
    for (const w of memWords) {
      if (queryWords.has(w)) matchCount++;
    }
    const relevance = matchCount / Math.max(queryWords.size, 1);
    return { ...mem, score: relevance * 0.6 + mem.salience * 0.4 };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, topK);
}
