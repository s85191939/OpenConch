"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";
import ReactMarkdown from "react-markdown";

interface Props {
  messages: Message[];
  isStreaming: boolean;
}

export default function MessageList({ messages, isStreaming }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

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
      <div className="max-w-[720px] mx-auto px-8 py-8">
        {messages.map((msg, i) => (
          <div key={msg.id} className="mb-8 last:mb-0">
            {msg.role === "user" ? (
              <div className="flex justify-end">
                <div className="bg-[#f0f0f0] rounded-[24px] px-6 py-3 max-w-[75%]">
                  <p className="text-[16px] leading-[1.7] text-[#1a1a1a] whitespace-pre-wrap">
                    {msg.content}
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex gap-4 items-start">
                <div className="w-[34px] h-[34px] rounded-full bg-[#7c3aed] flex items-center justify-center shrink-0 text-[15px] select-none mt-0.5 shadow-sm">
                  🐚
                </div>
                <div className="flex-1 min-w-0 pt-1 prose">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                  {isStreaming && i === messages.length - 1 && <span className="typing" />}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
