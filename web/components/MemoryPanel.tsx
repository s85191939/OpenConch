"use client";

import { MemoryEntry } from "@/lib/types";
import { X, Trash2, Brain, Zap } from "lucide-react";

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

  const getSalienceColor = (salience: number) => {
    if (salience >= 0.7) return "bg-[#a78bfa]";
    if (salience >= 0.4) return "bg-amber-500";
    return "bg-[#52525b]";
  };

  const getSalienceLabel = (salience: number) => {
    if (salience >= 0.7) return "High";
    if (salience >= 0.4) return "Medium";
    return "Low";
  };

  const formatTime = (timestamp: number) => {
    const diff = Date.now() - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-[400px] bg-[#0c0c0e] border-l border-white/[0.06] z-50 flex flex-col animate-fade-in-up">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#a78bfa]/10 flex items-center justify-center">
              <Brain size={16} className="text-[#a78bfa]" />
            </div>
            <div>
              <h2 className="font-semibold text-[15px]">Memories</h2>
              <p className="text-[11px] text-[#52525b]">{memories.length} stored</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-white/[0.06] transition-colors duration-200"
          >
            <X size={16} className="text-[#52525b]" />
          </button>
        </div>

        {/* Memory list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
          {memories.length === 0 && (
            <div className="text-center mt-20">
              <div className="w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mx-auto mb-4">
                <Brain size={24} className="text-[#27272a]" />
              </div>
              <p className="text-[#52525b] text-sm font-medium">No memories yet</p>
              <p className="text-[#3f3f46] text-xs mt-1.5 max-w-[200px] mx-auto leading-relaxed">
                Start chatting and I&apos;ll remember the important things.
              </p>
            </div>
          )}

          {memories.map((memory, idx) => (
            <div
              key={memory.id}
              className="group bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] rounded-2xl p-4 transition-all duration-300 hover:bg-white/[0.03] animate-fade-in-up"
              style={{ animationDelay: `${idx * 0.03}s` }}
            >
              <div className="flex items-start gap-3">
                {/* Salience dot */}
                <div className="mt-1">
                  <div
                    className={`w-2 h-2 rounded-full ${getSalienceColor(memory.salience)}`}
                  />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] leading-relaxed text-[#d4d4d8]">
                    {memory.content}
                  </p>
                  <div className="flex items-center gap-2 mt-2.5">
                    <span className="text-[10px] text-[#52525b]">
                      {formatTime(memory.createdAt)}
                    </span>
                    <span className="text-[#27272a]">·</span>
                    <div className="flex items-center gap-1">
                      <Zap size={9} className={`${memory.salience >= 0.7 ? "text-[#a78bfa]" : "text-[#52525b]"}`} />
                      <span className={`text-[10px] ${memory.salience >= 0.7 ? "text-[#a78bfa]" : "text-[#52525b]"}`}>
                        {getSalienceLabel(memory.salience)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Delete */}
                <button
                  onClick={() => onDelete(memory.id)}
                  className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-white/[0.08] transition-all duration-200 shrink-0"
                >
                  <Trash2 size={12} className="text-[#52525b]" />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/[0.06]">
          <p className="text-[10px] text-[#3f3f46] text-center leading-relaxed">
            Memories are extracted from conversations and stored in your browser.
            <br />
            High salience memories are prioritized in context.
          </p>
        </div>
      </div>
    </>
  );
}
