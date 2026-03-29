"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";

interface Props {
  messages: Message[];
  isStreaming: boolean;
}

export default function MessageList({ messages, isStreaming }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, messages[messages.length - 1]?.content]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-[720px] mx-auto px-4 py-6">
        {messages.map((msg, i) => (
          <div key={msg.id} className="mb-8 last:mb-0 animate-in">
            {msg.role === "user" ? (
              <div className="flex justify-end mb-1">
                <div className="bg-[#2f2f2f] rounded-3xl px-5 py-3 max-w-[85%]">
                  <p className="text-[15px] leading-relaxed text-white whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ) : (
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-[#b4a0fb] flex items-center justify-center shrink-0 text-sm font-bold text-white mt-1">
                  🐚
                </div>
                <div className="flex-1 min-w-0 pt-1">
                  <div className="msg-content whitespace-pre-wrap">
                    {msg.content}
                    {isStreaming && i === messages.length - 1 && <span className="cursor-blink" />}
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
