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

  // Auto-resize textarea
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
    <div className="max-w-3xl mx-auto relative">
      <div className="relative flex items-end bg-[#2f2f2f] rounded-2xl border border-[#333] focus-within:border-[#555] transition-colors">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message OpenConch..."
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent text-[15px] text-[#ececec] placeholder-[#666] px-4 py-3 pr-12 resize-none outline-none max-h-[200px]"
        />
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || disabled}
          className={`absolute right-2 bottom-2 p-1.5 rounded-lg transition-all ${
            input.trim() && !disabled
              ? "bg-[#ececec] text-[#0d0d0d] hover:bg-white"
              : "bg-[#444] text-[#666] cursor-not-allowed"
          }`}
        >
          <ArrowUp size={18} />
        </button>
      </div>
    </div>
  );
}
