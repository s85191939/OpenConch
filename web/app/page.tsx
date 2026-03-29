"use client";

import { useState, useEffect, useCallback } from "react";
import { Conversation, Message } from "@/lib/types";
import { getConversations, saveConversation, deleteConversation } from "@/lib/store";
import { findRelevantMemories, createMemory, getAllMemories, removeMemory, formatMemoriesForContext } from "@/lib/memory";
import Sidebar from "@/components/Sidebar";
import Chat from "@/components/Chat";
import MemoryPanel from "@/components/MemoryPanel";

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [memoryPanelOpen, setMemoryPanelOpen] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [memories, setMemories] = useState<ReturnType<typeof getAllMemories>>([]);

  // Load conversations and memories from localStorage (client only)
  useEffect(() => {
    setConversations(getConversations());
    setMemories(getAllMemories());
  }, []);

  const createNewChat = useCallback(() => {
    const newConversation: Conversation = {
      id: crypto.randomUUID(),
      title: "New chat",
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    setActiveConversation(newConversation);
  }, []);

  const handleSelectConversation = useCallback((id: string) => {
    const conv = conversations.find((c) => c.id === id);
    if (conv) setActiveConversation(conv);
  }, [conversations]);

  const handleDeleteConversation = useCallback((id: string) => {
    deleteConversation(id);
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeConversation?.id === id) {
      setActiveConversation(null);
    }
  }, [activeConversation]);

  const handleSendMessage = useCallback(async (content: string) => {
    if (isStreaming) return;

    // Auto-create conversation if none active
    let conv = activeConversation;
    if (!conv) {
      conv = {
        id: crypto.randomUUID(),
        title: "New chat",
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: Date.now(),
    };

    // Update conversation with user message
    const updated = {
      ...conv,
      messages: [...conv.messages, userMessage],
      updatedAt: Date.now(),
    };

    // Set title from first message
    if (updated.messages.length === 1) {
      updated.title = content.slice(0, 40) + (content.length > 40 ? "..." : "");
    }

    setActiveConversation(updated);
    saveConversation(updated);
    setConversations((prev) => {
      const idx = prev.findIndex((c) => c.id === updated.id);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = updated;
        return next;
      }
      return [updated, ...prev];
    });

    // Get relevant memories
    const memories = findRelevantMemories(content);
    const memoryStrings = memories.map((m) => m.content);

    // Stream assistant response
    setIsStreaming(true);
    const assistantMessage: Message = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
      timestamp: Date.now(),
    };

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: updated.messages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
          memories: memoryStrings,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let fullText = "";
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data === "[DONE]") continue;
              try {
                const parsed = JSON.parse(data);
                if (parsed.error) {
                  throw new Error(parsed.error);
                }
                if (parsed.text) {
                  fullText += parsed.text;
                  assistantMessage.content = fullText;

                  const withAssistant = {
                    ...updated,
                    messages: [...updated.messages, { ...assistantMessage }],
                    updatedAt: Date.now(),
                  };
                  setActiveConversation(withAssistant);
                }
              } catch (e) {
                if (e instanceof SyntaxError) continue;
                throw e;
              }
            }
          }
        }

        if (!fullText) {
          throw new Error("No response received from AI");
        }

        // Save final state
        const finalConv = {
          ...updated,
          messages: [...updated.messages, assistantMessage],
          updatedAt: Date.now(),
        };
        setActiveConversation(finalConv);
        saveConversation(finalConv);
        setConversations((prev) => {
          const idx = prev.findIndex((c) => c.id === finalConv.id);
          if (idx >= 0) {
            const next = [...prev];
            next[idx] = finalConv;
            return next;
          }
          return [finalConv, ...prev];
        });

        // Extract memories from the conversation
        try {
          const convText = `User: ${content}\nAssistant: ${assistantMessage.content}`;
          const memResponse = await fetch("/api/memories", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ conversation: convText }),
          });
          const { facts } = await memResponse.json();
          for (const fact of facts) {
            createMemory(fact);
          }
          setMemories(getAllMemories());
        } catch { /* memory extraction is best-effort */ }
      }
    } catch (error) {
      console.error("Chat error:", error);
      assistantMessage.content = "Sorry, something went wrong. Please try again.";
      const errorConv = {
        ...updated,
        messages: [...updated.messages, assistantMessage],
      };
      setActiveConversation(errorConv);
      saveConversation(errorConv);
    } finally {
      setIsStreaming(false);
    }
  }, [activeConversation, isStreaming]);

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeId={activeConversation?.id}
        isOpen={sidebarOpen}
        memoryCount={memories.length}
        onNewChat={createNewChat}
        onSelect={handleSelectConversation}
        onDelete={handleDeleteConversation}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onToggleMemory={() => setMemoryPanelOpen(!memoryPanelOpen)}
        onGoHome={() => setActiveConversation(null)}
      />

      {/* Main chat area */}
      <Chat
        conversation={activeConversation}
        isStreaming={isStreaming}
        onSendMessage={handleSendMessage}
        onNewChat={createNewChat}
        onGoHome={() => setActiveConversation(null)}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
      />

      {/* Memory panel */}
      <MemoryPanel
        isOpen={memoryPanelOpen}
        onClose={() => setMemoryPanelOpen(false)}
        memories={memories}
        onDelete={(id: string) => { removeMemory(id); setMemories(getAllMemories()); }}
      />
    </div>
  );
}
