"use client";

import { Conversation } from "@/lib/types";
import { Plus, MessageSquare, Trash2, Brain, PanelLeftClose } from "lucide-react";

interface SidebarProps {
  conversations: Conversation[];
  activeId?: string;
  isOpen: boolean;
  memoryCount: number;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onToggle: () => void;
  onToggleMemory: () => void;
}

export default function Sidebar({
  conversations,
  activeId,
  isOpen,
  memoryCount,
  onNewChat,
  onSelect,
  onDelete,
  onToggle,
  onToggleMemory,
}: SidebarProps) {
  if (!isOpen) return null;

  return (
    <div className="w-[280px] bg-[#0c0c0e] flex flex-col h-full border-r border-white/[0.06] relative z-10">
      {/* Header */}
      <div className="p-4 flex items-center gap-2">
        <button
          onClick={onNewChat}
          className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] hover:border-white/[0.1] transition-all duration-200 text-sm font-medium flex-1 group"
        >
          <Plus size={15} className="text-[#a78bfa] group-hover:rotate-90 transition-transform duration-300" />
          <span className="text-[#a1a1aa]">New chat</span>
        </button>
        <button
          onClick={onToggle}
          className="p-2.5 rounded-xl hover:bg-white/[0.06] transition-colors duration-200"
        >
          <PanelLeftClose size={15} className="text-[#52525b]" />
        </button>
      </div>

      {/* Section label */}
      {conversations.length > 0 && (
        <div className="px-5 py-2">
          <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-[#3f3f46]">
            Recent
          </span>
        </div>
      )}

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-3">
        {conversations.length === 0 && (
          <div className="text-center mt-16 px-6">
            <div className="w-10 h-10 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mx-auto mb-3">
              <MessageSquare size={16} className="text-[#3f3f46]" />
            </div>
            <p className="text-[#3f3f46] text-xs leading-relaxed">
              No conversations yet.
              <br />
              Start one above.
            </p>
          </div>
        )}
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`group flex items-center gap-2.5 px-3.5 py-3 rounded-xl cursor-pointer mb-1 transition-all duration-200 ${
              conv.id === activeId
                ? "bg-white/[0.08] border border-white/[0.08]"
                : "hover:bg-white/[0.04] border border-transparent"
            }`}
            onClick={() => onSelect(conv.id)}
          >
            <span
              className={`text-sm truncate flex-1 ${
                conv.id === activeId ? "text-[#fafafa]" : "text-[#a1a1aa]"
              }`}
            >
              {conv.title}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(conv.id);
              }}
              className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-white/[0.08] transition-all duration-200"
            >
              <Trash2 size={12} className="text-[#52525b]" />
            </button>
          </div>
        ))}
      </div>

      {/* Memory button */}
      <div className="p-4 border-t border-white/[0.06]">
        <button
          onClick={onToggleMemory}
          className="flex items-center gap-3 w-full px-4 py-3 rounded-xl hover:bg-white/[0.04] border border-transparent hover:border-white/[0.06] transition-all duration-200 text-sm group"
        >
          <div className="w-7 h-7 rounded-lg bg-[#a78bfa]/10 flex items-center justify-center group-hover:bg-[#a78bfa]/15 transition-colors">
            <Brain size={14} className="text-[#a78bfa]" />
          </div>
          <span className="text-[#a1a1aa]">Memories</span>
          {memoryCount > 0 && (
            <span className="ml-auto text-[10px] font-semibold bg-[#a78bfa]/15 text-[#a78bfa] px-2 py-0.5 rounded-full">
              {memoryCount}
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
