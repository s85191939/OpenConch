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
    <div className="relative rounded-[24px] bg-[#f4f4f4] border border-[#e5e5e5] focus-within:border-[#c5c5c5] transition-colors shadow-sm">
      <textarea
        ref={ref}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
        }}
        placeholder="Ask anything"
        disabled={disabled}
        rows={1}
        className="w-full bg-transparent text-[16px] text-[#0d0d0d] placeholder-[#999] px-6 py-[14px] pr-[52px] resize-none outline-none max-h-[200px] leading-[24px]"
      />
      <button
        onClick={send}
        disabled={!active}
        className={`absolute right-2.5 bottom-2.5 w-[32px] h-[32px] rounded-full flex items-center justify-center transition-all cursor-pointer ${
          active
            ? "bg-[#0d0d0d] text-white hover:bg-[#333] active:bg-[#555]"
            : "bg-[#d9d9d9] text-white cursor-default"
        }`}
      >
        <ArrowUp size={16} strokeWidth={2.5} />
      </button>
    </div>
  );
}
