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

export default function Chat({
  conversation, isStreaming, onSendMessage, onNewChat, sidebarOpen, onToggleSidebar,
}: ChatProps) {
  const isEmpty = !conversation || conversation.messages.length === 0;

  return (
    <main className="flex-1 flex flex-col h-full bg-[#212121] min-w-0">
      {/* Header */}
      <div className="h-11 flex items-center px-4 shrink-0">
        {!sidebarOpen && (
          <button onClick={onToggleSidebar} className="p-1.5 rounded-lg hover:bg-[#2a2a2a] mr-2">
            <PanelLeft size={18} className="text-[#999]" />
          </button>
        )}
        <span className="text-sm font-medium text-[#b4a0fb]">OpenConch</span>
      </div>

      {/* Content */}
      {isEmpty ? (
        <div className="flex-1 flex flex-col items-center justify-center pb-20">
          <div className="text-center mb-10">
            <div className="text-5xl mb-6">🐚</div>
            <h1 className="text-[28px] font-semibold text-white tracking-tight">
              What can I help with?
            </h1>
          </div>

          {/* Input in center for empty state */}
          <div className="w-full max-w-[720px] px-4">
            <MessageInput onSend={(text) => {
              if (!conversation) onNewChat();
              setTimeout(() => onSendMessage(text), 60);
            }} disabled={isStreaming} />
          </div>

          <div className="flex gap-2 mt-6 flex-wrap justify-center px-4">
            {["What do you remember about me?", "Help me brainstorm", "How does your memory work?"].map((t) => (
              <button
                key={t}
                onClick={() => {
                  if (!conversation) onNewChat();
                  setTimeout(() => onSendMessage(t), 60);
                }}
                className="px-4 py-2 rounded-full border border-[#383838] text-sm text-[#999] hover:bg-[#2a2a2a] hover:text-white transition-colors"
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <>
          <MessageList messages={conversation.messages} isStreaming={isStreaming} />
          <div className="shrink-0 w-full max-w-[720px] mx-auto px-4 pb-6 pt-2">
            <MessageInput onSend={onSendMessage} disabled={isStreaming} />
            <p className="text-[11px] text-[#555] text-center mt-2">
              OpenConch can make mistakes. Memories stored locally.
            </p>
          </div>
        </>
      )}
    </main>
  );
}
