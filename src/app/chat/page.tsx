"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ChatSidebar from "@/components/chat/ChatSidebar";
import MessageBubble from "@/components/chat/MessageBubble";
import ChatInput from "@/components/chat/ChatInput";
import WelcomeScreen from "@/components/chat/WelcomeScreen";

const API_URL = "http://localhost:8000";

function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(true);
  useEffect(() => {
    const mql = window.matchMedia(query);
    setMatches(mql.matches);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [query]);
  return matches;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const wideScreen = useMediaQuery("(min-width: 768px)");

  // Auto-close sidebar on narrow screens
  useEffect(() => {
    if (!wideScreen) setSidebarOpen(false);
  }, [wideScreen]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      if (e) e.preventDefault();
      const query = input.trim();
      if (!query || isLoading) return;

      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: query,
      };

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "",
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setInput("");
      setIsLoading(true);

      try {
        const res = await fetch(`${API_URL}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            stream: true,
            top_k: 5,
          }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Request failed" }));
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessage.id
                ? { ...m, content: err.detail || "Something went wrong." }
                : m
            )
          );
          return;
        }

        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
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
              if (data === "[DONE]") break;
              if (data) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMessage.id
                      ? { ...m, content: m.content + data }
                      : m
                  )
                );
              }
            }
          }
        }
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? { ...m, content: "Failed to connect to the server." }
              : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [input, isLoading]
  );

  const handleNewChat = () => {
    setMessages([]);
    setInput("");
    setIsLoading(false);
  };

  return (
    <div className="chat-root">
      {/* Sidebar */}
      <ChatSidebar
        open={sidebarOpen && wideScreen}
        onNewChat={handleNewChat}
        messages={messages}
      />

      {/* Main area */}
      <div className="chat-main">
        {/* Top bar */}
        <header className="chat-header">
          <button
            className="chat-toggle"
            onClick={() => setSidebarOpen((v) => !v)}
            title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {sidebarOpen ? (
                <>
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <line x1="9" y1="3" x2="9" y2="21" />
                </>
              ) : (
                <>
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </>
              )}
            </svg>
          </button>

          {/* Vektra icon mark */}
          <span className="chat-header-logo">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor">
              <circle cx="8" cy="3" r="2" />
              <circle cx="3.5" cy="12" r="2" />
              <circle cx="12.5" cy="12" r="2" />
              <path d="M7 4.6 4.6 10.2M9 4.6l2.4 5.6" stroke="currentColor" strokeWidth="1.4" />
            </svg>
          </span>

          <span className="chat-header-title">Vektra</span>
          <div className="chat-header-spacer" />
        </header>

        {/* Scrollable messages */}
        <div ref={scrollRef} className="chat-scroll">
          {messages.length === 0 ? (
            <WelcomeScreen />
          ) : (
            <div className="chat-messages">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
            </div>
          )}
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <ChatInput
            value={input}
            onChange={setInput}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
          <p className="chat-input-hint">
            Vektra can make mistakes. Check important info.
          </p>
        </div>
      </div>
    </div>
  );
}
