"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";
import { User, Bot } from "lucide-react";

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
}

export default function MessageList({ messages, isStreaming }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, messages[messages.length - 1]?.content]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        {messages.map((message, idx) => (
          <div key={message.id} className="flex gap-4">
            {/* Avatar */}
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                message.role === "user"
                  ? "bg-[#2f2f2f]"
                  : "bg-[#10a37f]"
              }`}
            >
              {message.role === "user" ? (
                <User size={16} className="text-[#ececec]" />
              ) : (
                <span className="text-sm">🐚</span>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium text-[#9a9a9a] mb-1">
                {message.role === "user" ? "You" : "OpenConch"}
              </div>
              <div className="message-content text-[15px] leading-relaxed whitespace-pre-wrap break-words">
                {message.content}
                {isStreaming &&
                  message.role === "assistant" &&
                  idx === messages.length - 1 && (
                    <span className="typing-cursor" />
                  )}
              </div>
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
