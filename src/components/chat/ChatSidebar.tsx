"use client";

import { useState } from "react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatSidebarProps {
  open: boolean;
  onNewChat: () => void;
  messages: Message[];
}

export default function ChatSidebar({ open, onNewChat, messages }: ChatSidebarProps) {
  const [hovered, setHovered] = useState<string | null>(null);

  const title =
    messages.find((m) => m.role === "user")?.content.slice(0, 30) || "New chat";

  if (!open) return null;

  return (
    <aside className="chat-sidebar">
      {/* Header */}
      <div className="chat-sidebar-header">
        <span className="chat-sidebar-title">Chat</span>
        <button
          onClick={onNewChat}
          title="New chat"
          className={`chat-icon-btn ${hovered === "new" ? "chat-icon-btn-hover" : ""}`}
          onMouseEnter={() => setHovered("new")}
          onMouseLeave={() => setHovered(null)}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 5v14M5 12h14" />
          </svg>
        </button>
      </div>

      <div className="chat-sidebar-divider" />

      {/* Conversation list */}
      <div className="chat-sidebar-list">
        {messages.length > 0 && (
          <div
            className={`chat-sidebar-item ${hovered === "current" ? "chat-sidebar-item-hover" : ""}`}
            onMouseEnter={() => setHovered("current")}
            onMouseLeave={() => setHovered(null)}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
              style={{ flexShrink: 0, opacity: 0.5 }}>
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <span>{title}</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="chat-sidebar-footer">
        <div className="chat-sidebar-divider" style={{ margin: 0, marginBottom: 10 }} />
        <div className="chat-sidebar-model">Model: qwen2.5:1.5b via Ollama</div>
      </div>
    </aside>
  );
}
