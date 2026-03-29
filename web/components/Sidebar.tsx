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
      <div style={{ height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingLeft: 20, paddingRight: 12 }}>
        <button onClick={onGoHome} style={{ padding: 8, borderRadius: 8, cursor: 'pointer', background: 'none', border: 'none' }}>
          <span style={{ fontSize: 20 }}>🐚</span>
        </button>
        <div style={{ display: 'flex', gap: 2 }}>
          <button onClick={onToggle} style={{ width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 8, cursor: 'pointer', background: 'none', border: 'none' }}>
            <PanelLeftClose size={18} color="rgba(255,255,255,0.5)" />
          </button>
          <button onClick={onNewChat} style={{ width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 8, cursor: 'pointer', background: 'none', border: 'none' }}>
            <SquarePen size={18} color="rgba(255,255,255,0.5)" />
          </button>
        </div>
      </div>

      {/* Conversations */}
      <div style={{ flex: 1, overflowY: 'auto', paddingTop: 8 }}>
        {conversations.length > 0 && (
          <p style={{ fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.3)', paddingLeft: 24, paddingTop: 12, paddingBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em', userSelect: 'none' }}>
            Today
          </p>
        )}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, paddingLeft: 8, paddingRight: 8 }}>
          {conversations.map((c) => (
            <button
              key={c.id}
              onClick={() => onSelect(c.id)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                height: 44,
                paddingLeft: 16,
                paddingRight: 12,
                borderRadius: 8,
                fontSize: 14,
                textAlign: 'left' as const,
                cursor: 'pointer',
                border: 'none',
                background: c.id === activeId ? 'rgba(255,255,255,0.12)' : 'transparent',
                color: c.id === activeId ? '#fff' : 'rgba(255,255,255,0.65)',
                fontWeight: c.id === activeId ? 500 : 400,
                transition: 'background 0.15s',
              }}
              onMouseEnter={(e) => { if (c.id !== activeId) e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; }}
              onMouseLeave={(e) => { if (c.id !== activeId) e.currentTarget.style.background = 'transparent'; }}
            >
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Bottom */}
      <div style={{ padding: '12px 8px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
        <button
          onClick={onToggleMemory}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            height: 44,
            paddingLeft: 16,
            paddingRight: 12,
            borderRadius: 8,
            fontSize: 14,
            color: 'rgba(255,255,255,0.65)',
            cursor: 'pointer',
            border: 'none',
            background: 'transparent',
            transition: 'background 0.15s',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
        >
          <Brain size={18} color="#a78bfa" />
          Memory
          {memoryCount > 0 && (
            <span style={{
              marginLeft: 'auto',
              fontSize: 11,
              fontWeight: 600,
              background: 'rgba(167,139,250,0.2)',
              color: '#a78bfa',
              minWidth: 22,
              height: 22,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 999,
              paddingLeft: 6,
              paddingRight: 6,
            }}>
              {memoryCount}
            </span>
          )}
        </button>
      </div>
    </nav>
  );
}
