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
  conversation,
  isStreaming,
  onSendMessage,
  onNewChat,
  sidebarOpen,
  onToggleSidebar,
}: ChatProps) {
  return (
    <div className="flex-1 flex flex-col h-full bg-[#0d0d0d]">
      {/* Top bar */}
      <div className="h-12 flex items-center px-4 border-b border-[#333]/50">
        {!sidebarOpen && (
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-lg hover:bg-[#2a2a2a] transition-colors mr-2"
          >
            <PanelLeft size={16} className="text-[#9a9a9a]" />
          </button>
        )}
        <span className="text-sm font-medium text-[#10a37f]">OpenConch</span>
      </div>

      {/* Messages or empty state */}
      {!conversation || conversation.messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-4">
          <div className="text-4xl mb-4">🐚</div>
          <h1 className="text-2xl font-semibold mb-2">OpenConch</h1>
          <p className="text-[#9a9a9a] text-sm text-center max-w-md mb-8">
            AI that remembers. Your conversations build persistent memory —
            come back anytime and pick up where you left off.
          </p>
          <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
            {[
              "What can you remember about me?",
              "Tell me about your memory system",
              "Help me plan my week",
              "I want to learn something new",
            ].map((prompt) => (
              <button
                key={prompt}
                onClick={() => {
                  if (!conversation) onNewChat();
                  setTimeout(() => onSendMessage(prompt), 100);
                }}
                className="text-left text-sm p-3 rounded-xl border border-[#333] hover:bg-[#171717] transition-colors text-[#9a9a9a]"
              >
                {prompt}
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
      <div className="p-4 pb-6">
        <MessageInput
          onSend={onSendMessage}
          disabled={isStreaming}
        />
        <p className="text-[10px] text-[#666] text-center mt-2">
          OpenConch remembers across conversations. Your memories are stored locally.
        </p>
      </div>
    </div>
  );
}
