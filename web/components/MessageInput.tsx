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
      className="rounded-[24px] bg-[#f4f4f4] border border-[#e0e0e0] focus-within:border-[#c0c0c0] transition-colors overflow-hidden"
    >
      <div className="flex items-end min-h-[52px]">
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
          className="flex-1 bg-transparent text-[16px] text-[#1a1a1a] placeholder-[#999] pl-5 pr-2 py-[14px] resize-none outline-none max-h-[200px] leading-[24px]"
        />
        <div className="p-2 shrink-0">
          <button
            onClick={send}
            disabled={!active}
            className={`w-[34px] h-[34px] rounded-full flex items-center justify-center transition-colors ${
              active
                ? "bg-[#1a1a1a] text-white hover:bg-[#333] cursor-pointer"
                : "bg-[#d4d4d4] text-white cursor-default"
            }`}
          >
            <ArrowUp size={16} strokeWidth={2.5} />
          </button>
        </div>
      </div>
    </div>
  );
}
