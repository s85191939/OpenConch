"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowUp } from "lucide-react";

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled: boolean;
}

export default function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [input, setInput] = useState("");
  const [focused, setFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 180) + "px";
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

  const hasContent = input.trim().length > 0;

  return (
    <div className="max-w-[680px] mx-auto">
      <div
        className="relative rounded-2xl transition-all duration-300"
        style={{
          background: focused ? 'var(--surface-1)' : 'var(--surface-0)',
          border: `1px solid ${focused ? 'var(--border-strong)' : 'var(--border-default)'}`,
          boxShadow: focused
            ? '0 0 0 3px var(--accent-soft), 0 4px 20px rgba(0,0,0,0.3)'
            : '0 2px 8px rgba(0,0,0,0.15)',
        }}
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Ask anything..."
          disabled={disabled}
          rows={1}
          className="w-full bg-transparent text-[15px] text-[var(--text-primary)] placeholder-[var(--text-faint)] pl-5 pr-14 py-4 resize-none outline-none max-h-[180px] leading-relaxed"
        />

        {/* Send button */}
        <button
          onClick={handleSubmit}
          disabled={!hasContent || disabled}
          className="absolute right-2.5 bottom-2.5 transition-all duration-200"
          style={{
            width: 32,
            height: 32,
            borderRadius: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: hasContent && !disabled ? 'var(--accent)' : 'var(--surface-2)',
            color: hasContent && !disabled ? '#fff' : 'var(--text-faint)',
            cursor: hasContent && !disabled ? 'pointer' : 'default',
            transform: hasContent ? 'scale(1)' : 'scale(0.92)',
            boxShadow: hasContent ? '0 2px 12px rgba(155, 138, 251, 0.3)' : 'none',
          }}
          aria-label="Send message"
        >
          <ArrowUp size={15} strokeWidth={2.5} />
        </button>
      </div>
    </div>
  );
}
