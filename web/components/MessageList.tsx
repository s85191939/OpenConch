"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";

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
      <div className="max-w-2xl mx-auto px-6 py-8 space-y-8">
        {messages.map((message, idx) => (
          <div
            key={message.id}
            className="animate-fade-in-up"
            style={{ animationDelay: `${Math.min(idx * 0.05, 0.3)}s` }}
          >
            {message.role === "user" ? (
              /* User message */
              <div className="flex justify-end">
                <div className="max-w-[85%] bg-white/[0.07] border border-white/[0.06] rounded-2xl rounded-br-md px-5 py-3.5">
                  <p className="text-[15px] leading-relaxed">{message.content}</p>
                </div>
              </div>
            ) : (
              /* Assistant message */
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#a78bfa]/20 to-[#6366f1]/20 border border-[#a78bfa]/10 flex items-center justify-center shrink-0 mt-0.5">
                  <span className="text-sm">🐚</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[11px] font-medium text-[#a78bfa] mb-2 uppercase tracking-wider">
                    OpenConch
                  </div>
                  <div className="message-content text-[15px] leading-[1.75] text-[#d4d4d8]">
                    {message.content}
                    {isStreaming && idx === messages.length - 1 && (
                      <span className="typing-cursor" />
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
