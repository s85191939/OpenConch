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
      <div className="fixed inset-0 bg-black/20 z-40 cursor-pointer" onClick={onClose} />

      <div className="fixed right-0 top-0 h-full w-[420px] max-w-full bg-white z-50 flex flex-col shadow-2xl border-l border-gray-200">
        <div className="h-[56px] flex items-center justify-between px-6 border-b border-gray-100 shrink-0">
          <div className="flex items-center gap-3">
            <Brain size={18} className="text-[#7c3aed]" />
            <span className="text-[15px] font-semibold text-gray-900">Memory</span>
            <span className="text-[13px] text-gray-400">{memories.length}</span>
          </div>
          <button onClick={onClose} className="w-[34px] h-[34px] flex items-center justify-center rounded-lg hover:bg-gray-100 cursor-pointer transition-colors">
            <X size={18} className="text-gray-400" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {memories.length === 0 && (
            <div className="text-center pt-24">
              <p className="text-[14px] text-gray-400">No memories yet</p>
              <p className="text-[13px] text-gray-300 mt-1">Chat and I&apos;ll remember what matters.</p>
            </div>
          )}
          {memories.map((m) => (
            <div key={m.id} className="group relative bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors border border-gray-100">
              <p className="text-[14px] text-gray-700 leading-[1.65] pr-8">{m.content}</p>
              <div className="flex items-center gap-2 mt-2.5">
                <span className="text-[11px] text-gray-400">{timeAgo(m.createdAt)}</span>
                <span className="text-gray-300">&middot;</span>
                <span className={`text-[11px] font-medium ${m.salience >= 0.7 ? "text-[#7c3aed]" : "text-gray-400"}`}>
                  {m.salience >= 0.7 ? "Important" : m.salience >= 0.4 ? "Noted" : "Minor"}
                </span>
              </div>
              <button
                onClick={() => onDelete(m.id)}
                className="absolute top-3 right-3 w-[30px] h-[30px] flex items-center justify-center rounded-lg opacity-0 group-hover:opacity-100 hover:bg-gray-200 transition-all cursor-pointer"
              >
                <Trash2 size={14} className="text-gray-400" />
              </button>
            </div>
          ))}
        </div>

        <div className="px-6 py-4 border-t border-gray-100 shrink-0">
          <p className="text-[11px] text-gray-400 text-center">Memories are extracted automatically and stored in your browser.</p>
        </div>
      </div>
    </>
  );
}
