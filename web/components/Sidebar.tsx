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
    <nav className="w-[260px] h-full flex flex-col bg-[#171024] shrink-0">
      {/* Top row */}
      <div className="h-[56px] flex items-center justify-between px-5 shrink-0">
        <button onClick={onGoHome} className="p-2 rounded-lg hover:bg-white/10 cursor-pointer transition-colors">
          <span className="text-[20px] select-none">🐚</span>
        </button>
        <div className="flex items-center gap-0.5">
          <button onClick={onToggle} className="w-[36px] h-[36px] flex items-center justify-center rounded-lg hover:bg-white/10 cursor-pointer transition-colors">
            <PanelLeftClose size={18} className="text-white/50" />
          </button>
          <button onClick={onNewChat} className="w-[36px] h-[36px] flex items-center justify-center rounded-lg hover:bg-white/10 cursor-pointer transition-colors">
            <SquarePen size={18} className="text-white/50" />
          </button>
        </div>
      </div>

      {/* Conversations */}
      <div className="flex-1 overflow-y-auto px-3 pt-2">
        {conversations.length > 0 && (
          <p className="text-[11px] font-semibold text-white/30 pl-5 pt-3 pb-2 uppercase tracking-wider select-none">Today</p>
        )}
        <div className="space-y-0.5">
          {conversations.map((c) => (
            <button
              key={c.id}
              onClick={() => onSelect(c.id)}
              className={`group w-full flex items-center h-[44px] pl-5 pr-3 rounded-lg text-[14px] text-left cursor-pointer select-none transition-colors ${
                c.id === activeId
                  ? "bg-white/[0.12] text-white font-medium"
                  : "text-white/65 hover:bg-white/[0.06]"
              }`}
            >
              <span className="truncate flex-1">{c.title}</span>
              <span
                role="button"
                onClick={(e) => { e.stopPropagation(); onDelete(c.id); }}
                className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md hover:bg-white/10 transition-all cursor-pointer"
              >
                <Trash2 size={14} className="text-white/40" />
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Bottom */}
      <div className="px-3 py-3 border-t border-white/[0.08]">
        <button
          onClick={onToggleMemory}
          className="w-full flex items-center gap-3 h-[44px] pl-5 pr-3 rounded-lg text-[14px] text-white/65 hover:bg-white/[0.06] cursor-pointer select-none transition-colors"
        >
          <Brain size={18} className="text-[#a78bfa]" />
          Memory
          {memoryCount > 0 && (
            <span className="ml-auto text-[11px] font-semibold bg-[#a78bfa]/20 text-[#a78bfa] min-w-[22px] h-[22px] flex items-center justify-center rounded-full px-1.5">
              {memoryCount}
            </span>
          )}
        </button>
      </div>
    </nav>
  );
}
