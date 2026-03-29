"use client";

import { Conversation } from "@/lib/types";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import { PanelLeft, SquarePen } from "lucide-react";

interface ChatProps {
  conversation: Conversation | null;
  isStreaming: boolean;
  onSendMessage: (content: string) => void;
  onNewChat: () => void;
  onGoHome: () => void;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export default function Chat({
  conversation, isStreaming, onSendMessage, onNewChat, onGoHome, sidebarOpen, onToggleSidebar,
}: ChatProps) {
  const isEmpty = !conversation || conversation.messages.length === 0;

  return (
    <main className="flex-1 flex flex-col h-full bg-white min-w-0">
      {/* Header */}
      <header className="h-[56px] flex items-center justify-between px-5 shrink-0 border-b border-gray-100">
        <div className="flex items-center gap-1">
          {!sidebarOpen && (
            <>
              <button onClick={onToggleSidebar} className="w-[36px] h-[36px] flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                <PanelLeft size={20} className="text-gray-500" />
              </button>
              <button onClick={onNewChat} className="w-[36px] h-[36px] flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                <SquarePen size={18} className="text-gray-500" />
              </button>
            </>
          )}
        </div>
        <button onClick={onGoHome} className="text-[16px] font-semibold text-gray-900 hover:text-[#7c3aed] transition-colors cursor-pointer select-none">
          OpenConch
        </button>
        <div className="w-[72px]" />
      </header>

      {isEmpty ? (
        <div className="flex-1 flex flex-col items-center justify-center px-6 pb-[80px]">
          <h1 className="text-[30px] font-semibold text-gray-900 tracking-[-0.02em] mb-10">
            Where should we begin?
          </h1>
          <div className="w-full max-w-[680px] px-4">
            <MessageInput onSend={onSendMessage} disabled={isStreaming} />
          </div>
        </div>
      ) : (
        <>
          <MessageList messages={conversation.messages} isStreaming={isStreaming} />
          <div style={{ flexShrink: 0, width: '100%', maxWidth: 720, marginLeft: 'auto', marginRight: 'auto', padding: '8px 40px 24px 40px' }}>
            <MessageInput onSend={onSendMessage} disabled={isStreaming} />
            <p style={{ fontSize: 11, color: '#999', textAlign: 'center', marginTop: 12, userSelect: 'none' }}>
              OpenConch can make mistakes. Memories stored in your browser.
            </p>
          </div>
        </>
      )}
    </main>
  );
}
