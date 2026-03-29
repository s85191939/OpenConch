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
      el.style.height = "28px";
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
    <div className="flex items-end gap-3 rounded-[28px] bg-[#f4f4f4] px-6 py-4 border border-transparent focus-within:border-gray-300 transition-colors">
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
        className="flex-1 bg-transparent text-[16px] text-gray-900 placeholder-gray-400 resize-none outline-none max-h-[200px] leading-[28px]"
      />
      <button
        onClick={send}
        disabled={!active}
        className={`w-[36px] h-[36px] rounded-full flex items-center justify-center shrink-0 transition-colors ${
          active
            ? "bg-black text-white hover:bg-gray-800 cursor-pointer"
            : "bg-gray-300 text-white cursor-default"
        }`}
      >
        <ArrowUp size={18} strokeWidth={2.5} />
      </button>
    </div>
  );
}
