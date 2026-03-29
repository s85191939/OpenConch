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
    if (d < 3600000) return `${Math.floor(d / 60000)}m ago`;
    if (d < 86400000) return `${Math.floor(d / 3600000)}h ago`;
    return `${Math.floor(d / 86400000)}d ago`;
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/30 z-40 cursor-pointer" onClick={onClose} />

      <div className="fixed right-0 top-0 h-full w-[420px] max-w-full bg-white z-50 flex flex-col shadow-2xl border-l border-[#e5e5e5]">
        <div className="h-[56px] flex items-center justify-between px-5 border-b border-[#e5e5e5] shrink-0">
          <div className="flex items-center gap-2.5">
            <Brain size={18} className="text-[#7c3aed]" />
            <span className="text-[15px] font-semibold text-[#0d0d0d]">Memory</span>
            <span className="text-[12px] text-[#999]">{memories.length}</span>
          </div>
          <button onClick={onClose} className="w-[32px] h-[32px] flex items-center justify-center rounded-lg hover:bg-black/5 cursor-pointer">
            <X size={18} className="text-[#999]" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {memories.length === 0 && (
            <div className="text-center pt-24">
              <p className="text-[14px] text-[#999]">No memories yet</p>
              <p className="text-[12px] text-[#ccc] mt-1">Chat and I&apos;ll remember what matters.</p>
            </div>
          )}
          {memories.map((m) => (
            <div key={m.id} className="group relative bg-[#f9f9f9] rounded-xl p-4 hover:bg-[#f4f4f4] transition-colors border border-[#eee]">
              <p className="text-[14px] text-[#374151] leading-[1.65] pr-8">{m.content}</p>
              <div className="flex items-center gap-2 mt-2.5">
                <span className="text-[11px] text-[#999]">{timeAgo(m.createdAt)}</span>
                <span className="text-[#ddd]">&middot;</span>
                <span className={`text-[11px] font-medium ${m.salience >= 0.7 ? "text-[#7c3aed]" : "text-[#999]"}`}>
                  {m.salience >= 0.7 ? "Important" : m.salience >= 0.4 ? "Noted" : "Minor"}
                </span>
              </div>
              <button
                onClick={() => onDelete(m.id)}
                className="absolute top-3 right-3 w-[28px] h-[28px] flex items-center justify-center rounded-md opacity-0 group-hover:opacity-100 hover:bg-black/5 transition-all cursor-pointer"
              >
                <Trash2 size={13} className="text-[#999]" />
              </button>
            </div>
          ))}
        </div>

        <div className="px-5 py-4 border-t border-[#e5e5e5] shrink-0">
          <p className="text-[11px] text-[#999] text-center">Memories are extracted automatically and stored in your browser.</p>
        </div>
      </div>
    </>
  );
}
