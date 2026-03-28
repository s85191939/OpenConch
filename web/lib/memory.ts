/**
 * OpenConch Memory — TypeScript client-side implementation.
 * Manages memories with salience scoring and keyword search.
 */

import { MemoryEntry } from "./types";
import { scoreSalience } from "./scorer";
import { addMemory, getMemories, searchMemories, deleteMemory } from "./store";

export function createMemory(content: string): MemoryEntry {
  const existingContents = getMemories().map((m) => m.content);
  const salience = scoreSalience(content, existingContents);

  const memory: MemoryEntry = {
    id: crypto.randomUUID(),
    content,
    salience,
    createdAt: Date.now(),
    accessCount: 0,
    source: "extracted",
  };

  // Only store if salience is above threshold
  if (salience >= 0.15) {
    addMemory(memory);
  }

  return memory;
}

export function findRelevantMemories(query: string, topK: number = 5): MemoryEntry[] {
  return searchMemories(query, topK);
}

export function getAllMemories(): MemoryEntry[] {
  return getMemories();
}

export function removeMemory(id: string) {
  deleteMemory(id);
}

export function formatMemoriesForContext(memories: MemoryEntry[]): string {
  if (memories.length === 0) return "";

  const lines = memories.map((m) => `- ${m.content}`);
  return `Here are relevant things I remember about the user from previous conversations:\n${lines.join("\n")}`;
}
