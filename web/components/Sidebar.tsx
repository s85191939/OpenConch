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
  conversations, activeId, isOpen, memoryCount,
  onNewChat, onSelect, onDelete, onToggle, onToggleMemory,
}: SidebarProps) {
  if (!isOpen) return null;

  return (
    <nav className="w-[260px] h-full flex flex-col bg-[#171717] shrink-0">
      {/* Top */}
      <div className="p-2">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-3 px-3 h-10 rounded-lg text-sm text-[#b4b4b4] hover:bg-[#212121] transition-colors"
        >
          <Plus size={16} />
          New chat
        </button>
      </div>

      {/* Conversations */}
      <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
        {conversations.length > 0 && (
          <div className="px-3 pt-4 pb-1">
            <span className="text-xs font-medium text-[#666]">Today</span>
          </div>
        )}
        {conversations.map((c) => (
          <div
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer text-sm transition-colors ${
              c.id === activeId
                ? "bg-[#212121] text-white"
                : "text-[#b4b4b4] hover:bg-[#1e1e1e]"
            }`}
          >
            <span className="truncate flex-1">{c.title}</span>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(c.id); }}
              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[#333] transition-all"
            >
              <Trash2 size={14} className="text-[#666]" />
            </button>
          </div>
        ))}
      </div>

      {/* Bottom */}
      <div className="p-2 border-t border-[#2a2a2a]">
        <button
          onClick={onToggleMemory}
          className="w-full flex items-center gap-3 px-3 h-10 rounded-lg text-sm text-[#b4b4b4] hover:bg-[#212121] transition-colors"
        >
          <Brain size={16} className="text-[#b4a0fb]" />
          Memory
          {memoryCount > 0 && (
            <span className="ml-auto text-xs bg-[#2a2a2a] text-[#b4a0fb] px-1.5 py-0.5 rounded-full font-medium">
              {memoryCount}
            </span>
          )}
        </button>
      </div>
    </nav>
  );
}
