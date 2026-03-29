"use client";

import { MemoryEntry } from "@/lib/types";
import { X, Trash2, Brain } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  memories: MemoryEntry[];
  onDelete: (id: string) => void;
}

export default function MemoryPanel({ isOpen, onClose, memories, onDelete }: Props) {
  if (!isOpen) return null;

  const timeAgo = (ts: number) => {
    const d = Date.now() - ts;
    if (d < 60000) return "now";
    if (d < 3600000) return `${Math.floor(d / 60000)}m`;
    if (d < 86400000) return `${Math.floor(d / 3600000)}h`;
    return `${Math.floor(d / 86400000)}d`;
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed right-0 top-0 h-full w-[380px] bg-[#171717] border-l border-[#2a2a2a] z-50 flex flex-col animate-in">
        {/* Header */}
        <div className="flex items-center justify-between h-14 px-5 border-b border-[#2a2a2a]">
          <div className="flex items-center gap-2.5">
            <Brain size={16} className="text-[#b4a0fb]" />
            <span className="text-sm font-medium">Memory</span>
            <span className="text-xs text-[#666]">{memories.length}</span>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-[#2a2a2a]">
            <X size={16} className="text-[#666]" />
          </button>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {memories.length === 0 && (
            <div className="text-center pt-20">
              <p className="text-sm text-[#555]">No memories yet</p>
              <p className="text-xs text-[#444] mt-1">Chat and I&apos;ll remember the important stuff.</p>
            </div>
          )}
          {memories.map((m) => (
            <div key={m.id} className="group bg-[#212121] rounded-xl p-4 hover:bg-[#252525] transition-colors">
              <p className="text-sm text-[#ccc] leading-relaxed pr-6">{m.content}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-[10px] text-[#555]">{timeAgo(m.createdAt)}</span>
                <span className="text-[10px] text-[#555]">&middot;</span>
                <span className={`text-[10px] ${m.salience >= 0.7 ? "text-[#b4a0fb]" : "text-[#555]"}`}>
                  {m.salience >= 0.7 ? "High" : m.salience >= 0.4 ? "Mid" : "Low"}
                </span>
              </div>
              <button
                onClick={() => onDelete(m.id)}
                className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[#333] transition-all"
              >
                <Trash2 size={12} className="text-[#555]" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
