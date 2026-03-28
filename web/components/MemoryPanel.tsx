"use client";

import { MemoryEntry } from "@/lib/types";
import { X, Trash2, Brain } from "lucide-react";

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
    if (salience >= 0.7) return "bg-[#10a37f]";
    if (salience >= 0.4) return "bg-yellow-600";
    return "bg-[#666]";
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
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-96 bg-[#171717] border-l border-[#333] z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#333]">
          <div className="flex items-center gap-2">
            <Brain size={18} className="text-[#10a37f]" />
            <h2 className="font-semibold">Memories</h2>
            <span className="text-xs text-[#666]">({memories.length})</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-[#2a2a2a] transition-colors"
          >
            <X size={16} className="text-[#9a9a9a]" />
          </button>
        </div>

        {/* Memory list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {memories.length === 0 && (
            <div className="text-center text-[#666] text-sm mt-12">
              <Brain size={32} className="mx-auto mb-3 text-[#333]" />
              <p>No memories yet.</p>
              <p className="text-xs mt-1">
                Start chatting and I&apos;ll remember important things.
              </p>
            </div>
          )}

          {memories.map((memory) => (
            <div
              key={memory.id}
              className="group bg-[#212121] rounded-xl p-3 hover:bg-[#2a2a2a] transition-colors"
            >
              <div className="flex items-start gap-2">
                {/* Salience indicator */}
                <div
                  className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${getSalienceColor(memory.salience)}`}
                  title={`Salience: ${(memory.salience * 100).toFixed(0)}%`}
                />

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm leading-relaxed">{memory.content}</p>
                  <p className="text-[10px] text-[#666] mt-1">
                    {formatTime(memory.createdAt)} · {(memory.salience * 100).toFixed(0)}% salience
                  </p>
                </div>

                {/* Delete */}
                <button
                  onClick={() => onDelete(memory.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[#333] transition-all shrink-0"
                >
                  <Trash2 size={12} className="text-[#666]" />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-[#333]">
          <p className="text-[10px] text-[#666] text-center">
            Memories are extracted from conversations and stored locally.
            High salience = more important.
          </p>
        </div>
      </div>
    </>
  );
}
