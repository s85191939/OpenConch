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
    <div ref={containerRef} style={{ flex: 1, overflowY: 'auto' }}>
      <div style={{ maxWidth: 720, margin: '0 auto', padding: '32px 40px' }}>
        {messages.map((msg, i) => (
          <div key={msg.id} style={{ marginBottom: 32 }}>
            {msg.role === "user" ? (
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <div style={{
                  background: '#f0f0f0',
                  borderRadius: 20,
                  padding: '10px 18px',
                  maxWidth: '75%',
                }}>
                  <p style={{ fontSize: 16, lineHeight: 1.5, color: '#1a1a1a', whiteSpace: 'pre-wrap', margin: 0 }}>
                    {msg.content}
                  </p>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
                <div style={{
                  width: 34,
                  height: 34,
                  borderRadius: '50%',
                  background: '#7c3aed',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  fontSize: 15,
                  marginTop: 2,
                }}>
                  🐚
                </div>
                <div style={{ flex: 1, minWidth: 0, paddingTop: 4 }} className="prose">
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
