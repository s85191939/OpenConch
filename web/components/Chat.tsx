"use client";

import { Conversation } from "@/lib/types";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import { PanelLeft } from "lucide-react";

interface ChatProps {
  conversation: Conversation | null;
  isStreaming: boolean;
  onSendMessage: (content: string) => void;
  onNewChat: () => void;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

const SUGGESTIONS = [
  {
    text: "What do you remember about me?",
    label: "Recall",
    sub: "Search your memory",
  },
  {
    text: "Help me think through a problem",
    label: "Reason",
    sub: "Step-by-step thinking",
  },
  {
    text: "Tell me about your memory system",
    label: "Explore",
    sub: "How OpenConch works",
  },
  {
    text: "I want to learn something new today",
    label: "Learn",
    sub: "Discover and grow",
  },
];

export default function Chat({
  conversation,
  isStreaming,
  onSendMessage,
  onNewChat,
  sidebarOpen,
  onToggleSidebar,
}: ChatProps) {
  const handleSuggestion = (text: string) => {
    if (!conversation) onNewChat();
    setTimeout(() => onSendMessage(text), 60);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[var(--void)] min-w-0">
      {/* ── Top Bar ── */}
      <header className="h-[52px] flex items-center px-5 border-b border-[var(--border-subtle)] shrink-0">
        {!sidebarOpen && (
          <button
            onClick={onToggleSidebar}
            className="p-2 -ml-1 mr-2 rounded-lg hover:bg-[var(--surface-1)] transition-colors duration-150"
            aria-label="Open sidebar"
          >
            <PanelLeft size={16} className="text-[var(--text-tertiary)]" />
          </button>
        )}
        <div className="flex items-center gap-2">
          <span className="text-[13px] font-semibold gradient-text select-none" style={{ fontFamily: 'var(--font-display)' }}>
            OpenConch
          </span>
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400/80" />
        </div>
      </header>

      {/* ── Content ── */}
      {!conversation || conversation.messages.length === 0 ? (
        /* ── Empty State ── */
        <div className="flex-1 flex flex-col items-center justify-center px-6 pb-8">
          <div className="anim-fade-in max-w-md w-full text-center">
            {/* Hero icon */}
            <div
              className="w-[72px] h-[72px] rounded-[20px] mx-auto mb-8 flex items-center justify-center"
              style={{
                background: 'linear-gradient(145deg, var(--surface-2), var(--surface-1))',
                boxShadow: '0 0 0 1px var(--border-default), 0 8px 40px rgba(155, 138, 251, 0.08)',
              }}
            >
              <span className="text-[32px]" style={{ animation: 'float 4s ease-in-out infinite' }}>🐚</span>
            </div>

            <h1
              className="text-[28px] font-bold tracking-[-0.03em] mb-3 text-[var(--text-primary)]"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              {getGreeting()}
            </h1>
            <p className="text-[var(--text-tertiary)] text-[15px] leading-relaxed max-w-xs mx-auto">
              I remember your conversations. Ask anything&mdash;I&apos;ll pick up where we left off.
            </p>
          </div>

          {/* Suggestions */}
          <div
            className="grid grid-cols-2 gap-2.5 max-w-md w-full mt-10 anim-fade-in"
            style={{ animationDelay: '0.12s' }}
          >
            {SUGGESTIONS.map((s) => (
              <button
                key={s.text}
                onClick={() => handleSuggestion(s.text)}
                className="text-left px-4 py-3.5 rounded-xl border border-[var(--border-default)] hover:border-[var(--border-strong)] bg-[var(--surface-0)] hover:bg-[var(--surface-1)] transition-all duration-200 group"
              >
                <div className="text-[12px] font-semibold text-[var(--text-primary)] mb-0.5 group-hover:text-[var(--accent)] transition-colors" style={{ fontFamily: 'var(--font-display)' }}>
                  {s.label}
                </div>
                <div className="text-[12px] text-[var(--text-faint)] leading-snug">
                  {s.sub}
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <MessageList messages={conversation.messages} isStreaming={isStreaming} />
      )}

      {/* ── Input Area ── */}
      <div className="shrink-0 px-4 sm:px-6 pb-5 pt-2">
        <MessageInput onSend={onSendMessage} disabled={isStreaming} />
        <p className="text-[11px] text-[var(--text-faint)] text-center mt-3 select-none">
          OpenConch remembers across conversations &middot; Stored locally
        </p>
      </div>
    </div>
  );
}

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning.";
  if (h < 18) return "Good afternoon.";
  return "Good evening.";
}
