"use client";

import { Conversation } from "@/lib/types";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import { PanelLeft, Sparkles } from "lucide-react";

interface ChatProps {
  conversation: Conversation | null;
  isStreaming: boolean;
  onSendMessage: (content: string) => void;
  onNewChat: () => void;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

const SUGGESTIONS = [
  { text: "What can you remember about me?", icon: "🧠" },
  { text: "Tell me about your memory system", icon: "🐚" },
  { text: "Help me brainstorm an idea", icon: "💡" },
  { text: "I want to learn something new", icon: "📚" },
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
    setTimeout(() => onSendMessage(text), 50);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#09090b] relative z-10">
      {/* Top bar */}
      <div className="h-14 flex items-center px-5 border-b border-white/[0.04]">
        {!sidebarOpen && (
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-xl hover:bg-white/[0.06] transition-colors duration-200 mr-3"
          >
            <PanelLeft size={16} className="text-[#52525b]" />
          </button>
        )}
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold gradient-text">OpenConch</span>
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
        </div>
      </div>

      {/* Messages or empty state */}
      {!conversation || conversation.messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-6">
          {/* Hero */}
          <div className="animate-fade-in-up">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#a78bfa]/20 to-[#6366f1]/20 border border-[#a78bfa]/10 flex items-center justify-center mx-auto mb-6 glow-accent">
              <span className="text-3xl">🐚</span>
            </div>
            <h1 className="text-3xl font-bold text-center mb-3 tracking-tight">
              Good{getTimeOfDay()}.
            </h1>
            <p className="text-[#71717a] text-center max-w-sm leading-relaxed text-[15px]">
              I remember our conversations. Ask me anything and I&apos;ll pick up where we left off.
            </p>
          </div>

          {/* Suggestions */}
          <div className="grid grid-cols-2 gap-3 max-w-lg w-full mt-10 animate-fade-in-up" style={{ animationDelay: "0.15s" }}>
            {SUGGESTIONS.map((s) => (
              <button
                key={s.text}
                onClick={() => handleSuggestion(s.text)}
                className="text-left text-sm p-4 rounded-2xl border border-white/[0.06] hover:border-white/[0.12] bg-white/[0.02] hover:bg-white/[0.04] transition-all duration-300 group"
              >
                <span className="text-lg mb-2 block">{s.icon}</span>
                <span className="text-[#a1a1aa] group-hover:text-[#d4d4d8] transition-colors text-[13px] leading-relaxed">
                  {s.text}
                </span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <MessageList
          messages={conversation.messages}
          isStreaming={isStreaming}
        />
      )}

      {/* Input */}
      <div className="px-4 pb-6 pt-2">
        <MessageInput onSend={onSendMessage} disabled={isStreaming} />
        <p className="text-[10px] text-[#3f3f46] text-center mt-3 tracking-wide">
          OpenConch remembers across conversations. Memories are stored locally in your browser.
        </p>
      </div>
    </div>
  );
}

function getTimeOfDay(): string {
  const hour = new Date().getHours();
  if (hour < 12) return " morning";
  if (hour < 17) return " afternoon";
  return " evening";
}
