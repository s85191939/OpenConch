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
    <div className="flex items-center gap-2 rounded-full bg-[#f4f4f4] border border-[#e0e0e0] focus-within:border-[#c0c0c0] transition-colors h-[48px] pl-5 pr-[7px]">
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
        className="flex-1 bg-transparent text-[16px] text-[#1a1a1a] placeholder-[#999] resize-none outline-none leading-[24px] py-0 self-center"
        style={{ height: "24px", maxHeight: "200px" }}
      />
      <button
        onClick={send}
        disabled={!active}
        className={`w-[34px] h-[34px] rounded-full flex items-center justify-center shrink-0 transition-colors ${
          active
            ? "bg-[#1a1a1a] text-white hover:bg-[#333] cursor-pointer"
            : "bg-[#d4d4d4] text-white cursor-default"
        }`}
      >
        <ArrowUp size={16} strokeWidth={2.5} />
      </button>
    </div>
  );
}
