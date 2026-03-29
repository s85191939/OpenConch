"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";

interface Props {
  messages: Message[];
  isStreaming: boolean;
}

export default function MessageList({ messages, isStreaming }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Smooth scroll that doesn't jank during streaming
  useEffect(() => {
    const el = containerRef.current;
    if (el) {
      requestAnimationFrame(() => {
        el.scrollTo({ top: el.scrollHeight, behavior: isStreaming ? "instant" : "smooth" });
      });
    }
  }, [messages, messages[messages.length - 1]?.content, isStreaming]);

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto">
      <div className="max-w-[680px] mx-auto px-4 py-6">
        {messages.map((msg, i) => (
          <div key={msg.id} className={msg.role === "user" ? "mb-6" : "mb-8"}>
            {msg.role === "user" ? (
              <div className="flex justify-end">
                <div className="bg-[#f0f0f0] rounded-[20px] px-5 py-3 max-w-[80%]">
                  <p className="text-[16px] leading-[1.6] text-[#0d0d0d] whitespace-pre-wrap">
                    {msg.content}
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex gap-4 items-start">
                <div className="w-[32px] h-[32px] rounded-full bg-[#7c3aed] flex items-center justify-center shrink-0 text-[14px] select-none mt-0.5">
                  🐚
                </div>
                <div className="flex-1 min-w-0 pt-[2px]">
                  <div className="prose whitespace-pre-wrap">
                    {msg.content}
                    {isStreaming && i === messages.length - 1 && <span className="typing" />}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
