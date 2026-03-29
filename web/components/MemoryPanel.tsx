"use client";

import { MemoryEntry } from "@/lib/types";
import { X, Trash2, Brain, Sparkles } from "lucide-react";

interface MemoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
  memories: MemoryEntry[];
  onDelete: (id: string) => void;
}

export default function MemoryPanel({
  isOpen,
  onClose,
  memories,
  onDelete,
}: MemoryPanelProps) {
  if (!isOpen) return null;

  const getSalienceBar = (salience: number) => {
    const pct = Math.round(salience * 100);
    if (salience >= 0.7) return { color: 'var(--accent)', label: 'High', bg: 'var(--accent-soft)' };
    if (salience >= 0.4) return { color: '#f59e0b', label: 'Mid', bg: 'rgba(245,158,11,0.1)' };
    return { color: 'var(--text-faint)', label: 'Low', bg: 'var(--surface-2)' };
  };

  const formatTime = (timestamp: number) => {
    const diff = Date.now() - timestamp;
    const min = Math.floor(diff / 60000);
    const hr = Math.floor(diff / 3600000);
    const day = Math.floor(diff / 86400000);
    if (min < 1) return "Just now";
    if (min < 60) return `${min}m ago`;
    if (hr < 24) return `${hr}h ago`;
    if (day < 7) return `${day}d ago`;
    return new Date(timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-[2px] z-40"
        onClick={onClose}
        style={{ animation: 'fadeIn 0.2s ease-out' }}
      />

      {/* Panel */}
      <div
        className="fixed right-0 top-0 h-full w-full sm:w-[420px] bg-[var(--surface-0)] border-l border-[var(--border-subtle)] z-50 flex flex-col anim-slide-right"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 h-[60px] border-b border-[var(--border-subtle)] shrink-0">
          <div className="flex items-center gap-3">
            <Brain size={16} className="text-[var(--accent)]" />
            <h2 className="text-[14px] font-semibold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)' }}>
              Memory
            </h2>
            <span className="text-[11px] tabular-nums text-[var(--text-faint)] bg-[var(--surface-2)] px-2 py-0.5 rounded-md">
              {memories.length}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-2 -mr-1 rounded-lg hover:bg-[var(--surface-2)] transition-colors duration-150"
            aria-label="Close"
          >
            <X size={15} className="text-[var(--text-tertiary)]" />
          </button>
        </div>

        {/* Memory List */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {memories.length === 0 && (
            <div className="flex flex-col items-center justify-center pt-24 text-center px-8">
              <div className="w-12 h-12 rounded-2xl bg-[var(--surface-1)] border border-[var(--border-default)] flex items-center justify-center mb-4">
                <Sparkles size={18} className="text-[var(--text-faint)]" />
              </div>
              <p className="text-[13px] font-medium text-[var(--text-tertiary)] mb-1">No memories yet</p>
              <p className="text-[12px] text-[var(--text-faint)] leading-relaxed max-w-[200px]">
                As you chat, important details will be stored here automatically.
              </p>
            </div>
          )}

          <div className="space-y-2">
            {memories.map((memory, idx) => {
              const salience = getSalienceBar(memory.salience);
              return (
                <div
                  key={memory.id}
                  className="group relative bg-[var(--surface-1)] border border-[var(--border-subtle)] hover:border-[var(--border-default)] rounded-xl p-4 transition-all duration-200 anim-fade-in"
                  style={{ animationDelay: `${idx * 0.04}s` }}
                >
                  <p className="text-[13px] leading-[1.65] text-[var(--text-secondary)] pr-6">
                    {memory.content}
                  </p>

                  {/* Meta row */}
                  <div className="flex items-center gap-3 mt-3">
                    <span className="text-[10px] text-[var(--text-faint)]">
                      {formatTime(memory.createdAt)}
                    </span>
                    <div
                      className="flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-medium"
                      style={{ background: salience.bg, color: salience.color }}
                    >
                      <div className="w-1 h-1 rounded-full" style={{ background: salience.color }} />
                      {salience.label}
                    </div>
                  </div>

                  {/* Delete */}
                  <button
                    onClick={() => onDelete(memory.id)}
                    className="absolute top-3 right-3 p-1.5 rounded-md opacity-0 group-hover:opacity-100 hover:bg-[var(--surface-3)] transition-all duration-150"
                    aria-label="Delete memory"
                  >
                    <Trash2 size={11} className="text-[var(--text-faint)]" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[var(--border-subtle)] shrink-0">
          <p className="text-[11px] text-[var(--text-faint)] leading-relaxed text-center">
            Memories are extracted from conversations and stored locally in your browser.
          </p>
        </div>
      </div>
    </>
  );
}
