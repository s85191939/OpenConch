"use client";

import { Conversation } from "@/lib/types";
import { Plus, MessageSquare, Trash2, Brain, PanelLeftClose, Search } from "lucide-react";

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

  const formatDate = (timestamp: number) => {
    const d = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 86400000) return "Today";
    if (diff < 172800000) return "Yesterday";
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  return (
    <div className="w-[272px] bg-[var(--surface-0)] flex flex-col h-full border-r border-[var(--border-subtle)] sidebar-responsive">
      {/* ── Top: Brand + New Chat ── */}
      <div className="px-4 pt-5 pb-3">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[var(--accent-soft)] flex items-center justify-center">
              <span className="text-xs">🐚</span>
            </div>
            <span className="text-[13px] font-semibold tracking-[-0.01em] text-[var(--text-primary)]">
              OpenConch
            </span>
          </div>
          <button
            onClick={onToggle}
            className="p-1.5 rounded-lg hover:bg-[var(--surface-2)] transition-colors duration-150"
            aria-label="Close sidebar"
          >
            <PanelLeftClose size={14} className="text-[var(--text-tertiary)]" />
          </button>
        </div>

        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 h-10 rounded-[10px] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border-default)] hover:border-[var(--border-strong)] transition-all duration-200 text-[13px] font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] group"
        >
          <Plus size={14} className="text-[var(--text-tertiary)] group-hover:text-[var(--accent)] transition-colors" />
          New conversation
        </button>
      </div>

      {/* ── Conversation List ── */}
      <div className="flex-1 overflow-y-auto px-2.5 pb-2">
        {conversations.length > 0 && (
          <div className="px-2.5 pt-3 pb-2">
            <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--text-faint)]">
              Recents
            </span>
          </div>
        )}

        {conversations.length === 0 && (
          <div className="flex flex-col items-center justify-center pt-20 px-6 text-center">
            <MessageSquare size={18} className="text-[var(--text-faint)] mb-3" />
            <p className="text-[12px] text-[var(--text-faint)] leading-relaxed">
              Your conversations will appear here
            </p>
          </div>
        )}

        <div className="space-y-0.5">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => onSelect(conv.id)}
              className={`group relative flex items-center gap-2.5 px-3 py-2.5 rounded-[10px] cursor-pointer transition-all duration-150 ${
                conv.id === activeId
                  ? "bg-[var(--surface-2)]"
                  : "hover:bg-[var(--surface-1)]"
              }`}
            >
              <div className="flex-1 min-w-0">
                <p
                  className={`text-[13px] truncate leading-tight ${
                    conv.id === activeId
                      ? "text-[var(--text-primary)] font-medium"
                      : "text-[var(--text-secondary)]"
                  }`}
                >
                  {conv.title}
                </p>
                <p className="text-[10px] text-[var(--text-faint)] mt-0.5">
                  {formatDate(conv.updatedAt)}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-[var(--surface-3)] transition-all duration-150"
                aria-label="Delete conversation"
              >
                <Trash2 size={11} className="text-[var(--text-faint)]" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ── Bottom: Memory ── */}
      <div className="px-3 py-3 border-t border-[var(--border-subtle)]">
        <button
          onClick={onToggleMemory}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-[10px] hover:bg-[var(--surface-1)] transition-all duration-150 group"
        >
          <Brain size={15} className="text-[var(--accent)] opacity-80 group-hover:opacity-100 transition-opacity" />
          <span className="text-[13px] text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">
            Memory
          </span>
          {memoryCount > 0 && (
            <span className="ml-auto text-[10px] font-medium bg-[var(--accent-soft)] text-[var(--accent)] px-2 py-0.5 rounded-full tabular-nums">
              {memoryCount}
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
