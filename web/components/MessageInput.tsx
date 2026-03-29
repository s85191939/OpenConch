"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowUp } from "lucide-react";

interface Props {
  onSend: (content: string) => void;
  disabled: boolean;
}

export default function MessageInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (el) {
      el.style.height = "24px";
      el.style.height = Math.min(el.scrollHeight, 200) + "px";
    }
  }, [input]);

  const send = () => {
    const t = input.trim();
    if (!t || disabled) return;
    onSend(t);
    setInput("");
  };

  const active = input.trim().length > 0 && !disabled;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        borderRadius: 9999,
        backgroundColor: "#f4f4f4",
        border: "1px solid #e0e0e0",
        height: 52,
        paddingLeft: 24,
        paddingRight: 10,
      }}
    >
      <textarea
        ref={ref}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
        }}
        placeholder="Ask anything..."
        disabled={disabled}
        rows={1}
        style={{
          flex: 1,
          background: "transparent",
          fontSize: 16,
          color: "#1a1a1a",
          resize: "none",
          outline: "none",
          lineHeight: "24px",
          height: 24,
          maxHeight: 200,
          border: "none",
          padding: 0,
          fontFamily: "inherit",
        }}
      />
      <button
        onClick={send}
        disabled={!active}
        style={{
          width: 34,
          height: 34,
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          border: "none",
          cursor: active ? "pointer" : "default",
          backgroundColor: active ? "#1a1a1a" : "#d4d4d4",
          color: "white",
          transition: "background-color 0.15s",
        }}
      >
        <ArrowUp size={16} strokeWidth={2.5} />
      </button>
    </div>
  );
}
