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
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 200) + "px";
    }
  }, [input]);

  const send = () => {
    const text = input.trim();
    if (!text || disabled) return;
    onSend(text);
    setInput("");
  };

  return (
    <div className="relative bg-[#303030] rounded-3xl border border-[#424242] focus-within:border-[#555] transition-colors shadow-lg">
      <textarea
        ref={ref}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
        placeholder="Message OpenConch..."
        disabled={disabled}
        rows={1}
        className="w-full bg-transparent text-[15px] text-white placeholder-[#666] pl-5 pr-14 py-3.5 resize-none outline-none max-h-[200px]"
      />
      <button
        onClick={send}
        disabled={!input.trim() || disabled}
        className={`absolute right-2 bottom-2 w-8 h-8 rounded-full flex items-center justify-center transition-all ${
          input.trim() && !disabled
            ? "bg-white text-black hover:bg-gray-200"
            : "bg-[#424242] text-[#666] cursor-default"
        }`}
      >
        <ArrowUp size={16} strokeWidth={2.5} />
      </button>
    </div>
  );
}
