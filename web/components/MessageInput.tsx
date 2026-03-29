"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowUp } from "lucide-react";

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled: boolean;
}

export default function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 200) + "px";
    }
  }, [input]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="max-w-2xl mx-auto relative">
      <div className="relative flex items-end bg-white/[0.04] rounded-2xl border border-white/[0.08] focus-within:border-[#a78bfa]/30 focus-within:bg-white/[0.05] transition-all duration-300 focus-within:shadow-[0_0_30px_rgba(167,139,250,0.08)]">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message OpenConch..."
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent text-[15px] text-[#fafafa] placeholder-[#52525b] px-5 py-4 pr-14 resize-none outline-none max-h-[200px]"
        />
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || disabled}
          className={`absolute right-3 bottom-3 p-2 rounded-xl transition-all duration-300 ${
            input.trim() && !disabled
              ? "bg-[#a78bfa] text-white hover:bg-[#8b5cf6] shadow-lg shadow-[#a78bfa]/20 scale-100"
              : "bg-white/[0.06] text-[#52525b] cursor-not-allowed scale-95"
          }`}
        >
          <ArrowUp size={16} strokeWidth={2.5} />
        </button>
      </div>
    </div>
  );
}
