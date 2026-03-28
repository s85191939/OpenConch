"use client";

import { Conversation } from "@/lib/types";
import { Plus, MessageSquare, Trash2, Brain, PanelLeftClose, PanelLeft } from "lucide-react";

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
    <div className="w-64 bg-[#171717] flex flex-col h-full border-r border-[#333]">
      {/* Header */}
      <div className="p-3 flex items-center justify-between">
        <button
          onClick={onNewChat}
          className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-[#2a2a2a] transition-colors text-sm flex-1"
        >
          <Plus size={16} />
          New chat
        </button>
        <button
          onClick={onToggle}
          className="p-2 rounded-lg hover:bg-[#2a2a2a] transition-colors"
        >
          <PanelLeftClose size={16} className="text-[#9a9a9a]" />
        </button>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-2">
        {conversations.length === 0 && (
          <p className="text-[#666] text-xs text-center mt-8 px-4">
            No conversations yet. Start a new chat!
          </p>
        )}
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer mb-0.5 transition-colors ${
              conv.id === activeId
                ? "bg-[#2a2a2a]"
                : "hover:bg-[#212121]"
            }`}
            onClick={() => onSelect(conv.id)}
          >
            <MessageSquare size={14} className="text-[#9a9a9a] shrink-0" />
            <span className="text-sm truncate flex-1">{conv.title}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(conv.id);
              }}
              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[#333] transition-all"
            >
              <Trash2 size={12} className="text-[#666]" />
            </button>
          </div>
        ))}
      </div>

      {/* Memory button */}
      <div className="p-3 border-t border-[#333]">
        <button
          onClick={onToggleMemory}
          className="flex items-center gap-2 w-full px-3 py-2.5 rounded-lg hover:bg-[#2a2a2a] transition-colors text-sm"
        >
          <Brain size={16} className="text-[#10a37f]" />
          <span>Memories</span>
          {memoryCount > 0 && (
            <span className="ml-auto bg-[#10a37f] text-[#0d0d0d] text-xs font-medium px-1.5 py-0.5 rounded-full">
              {memoryCount}
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
