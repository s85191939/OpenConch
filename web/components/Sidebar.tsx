"use client";

import { Conversation } from "@/lib/types";
import { SquarePen, Trash2, Brain, PanelLeftClose } from "lucide-react";

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
  onGoHome: () => void;
}

export default function Sidebar({
  conversations, activeId, isOpen, memoryCount,
  onNewChat, onSelect, onDelete, onToggle, onToggleMemory, onGoHome,
}: SidebarProps) {
  if (!isOpen) return null;

  return (
    <nav className="w-[260px] h-full flex flex-col bg-[#f9f9f9] shrink-0 border-r border-[#e5e5e5]">
      {/* Top row: logo + new chat + collapse */}
      <div className="h-[56px] flex items-center justify-between px-3 shrink-0">
        <button onClick={onGoHome} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-black/5 active:bg-black/8 transition-colors cursor-pointer">
          <span className="text-[18px] select-none">🐚</span>
        </button>
        <div className="flex items-center gap-1">
          <button onClick={onToggle} className="w-[34px] h-[34px] flex items-center justify-center rounded-lg hover:bg-black/5 transition-colors cursor-pointer">
            <PanelLeftClose size={18} className="text-[#999]" />
          </button>
          <button onClick={onNewChat} className="w-[34px] h-[34px] flex items-center justify-center rounded-lg hover:bg-black/5 transition-colors cursor-pointer">
            <SquarePen size={18} className="text-[#999]" />
          </button>
        </div>
      </div>

      {/* Nav items */}
      <div className="flex-1 overflow-y-auto px-2 pt-1">
        {conversations.length > 0 && (
          <p className="text-[11px] font-semibold text-[#999] px-3 pt-4 pb-2 select-none">
            Today
          </p>
        )}
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={`group w-full flex items-center h-[40px] px-3 rounded-lg text-[14px] text-left transition-colors cursor-pointer select-none mb-[1px] ${
              c.id === activeId
                ? "bg-black/8 text-[#0d0d0d] font-medium"
                : "text-[#374151] hover:bg-black/5"
            }`}
          >
            <span className="truncate flex-1">{c.title}</span>
            <span
              role="button"
              onClick={(e) => { e.stopPropagation(); onDelete(c.id); }}
              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-black/10 transition-all cursor-pointer"
            >
              <Trash2 size={14} className="text-[#999]" />
            </span>
          </button>
        ))}
      </div>

      {/* Bottom */}
      <div className="px-2 py-2 border-t border-[#e5e5e5]">
        <button
          onClick={onToggleMemory}
          className="w-full flex items-center gap-3 h-[40px] px-3 rounded-lg text-[14px] text-[#374151] hover:bg-black/5 transition-colors cursor-pointer select-none"
        >
          <Brain size={18} className="text-[#7c3aed]" />
          Memory
          {memoryCount > 0 && (
            <span className="ml-auto text-[11px] font-semibold bg-[#7c3aed]/10 text-[#7c3aed] min-w-[20px] h-[20px] flex items-center justify-center rounded-full px-1.5">
              {memoryCount}
            </span>
          )}
        </button>
      </div>
    </nav>
  );
}
