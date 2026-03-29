"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
}

export default function MessageList({ messages, isStreaming }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, messages[messages.length - 1]?.content]);

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto">
      <div className="max-w-[680px] mx-auto px-5 sm:px-6 py-8">
        {messages.map((message, idx) => {
          const isUser = message.role === "user";
          const isLast = idx === messages.length - 1;

          return (
            <div
              key={message.id}
              className={`mb-7 last:mb-0 ${isUser ? 'anim-slide-right' : 'anim-slide-left'}`}
              style={{ animationDelay: `${Math.min(idx * 0.06, 0.25)}s` }}
            >
              {isUser ? (
                /* ── User Message ── */
                <div className="flex justify-end">
                  <div className="max-w-[82%] bg-[var(--surface-2)] border border-[var(--border-default)] rounded-[16px] rounded-br-[4px] px-5 py-3.5">
                    <p className="text-[15px] leading-[1.65] text-[var(--text-primary)] whitespace-pre-wrap">
                      {message.content}
                    </p>
                  </div>
                </div>
              ) : (
                /* ── Assistant Message ── */
                <div className="flex gap-3.5">
                  {/* Avatar */}
                  <div className="shrink-0 mt-1">
                    <div
                      className="w-7 h-7 rounded-[8px] flex items-center justify-center"
                      style={{
                        background: 'linear-gradient(135deg, var(--accent-soft), var(--accent-medium))',
                        border: '1px solid var(--accent-soft)',
                      }}
                    >
                      <span className="text-[11px]">🐚</span>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 pt-0.5">
                    <div className="message-content whitespace-pre-wrap">
                      {message.content}
                      {isStreaming && isLast && (
                        <span className="typing-cursor" />
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
        <div ref={endRef} />
      </div>
    </div>
  );
}
