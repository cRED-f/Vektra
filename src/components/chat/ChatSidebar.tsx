"use client";

import { useState, useEffect } from "react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
}

const STORAGE_KEY = "vektra-chat-sessions";

function loadSessions(): ChatSession[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveSessions(sessions: ChatSession[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

interface ChatSidebarProps {
  open: boolean;
  onNewChat: () => void;
  messages: ChatMessage[];
  onLoadSession?: (session: ChatSession) => void;
}

export default function ChatSidebar({ open, onNewChat, messages, onLoadSession }: ChatSidebarProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [hovered, setHovered] = useState<string | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  // Load sessions on mount
  useEffect(() => {
    setSessions(loadSessions());
  }, []);

  // Save current messages as a session when user sends first message
  useEffect(() => {
    if (messages.length === 0) return;

    const userMsg = messages.find((m) => m.role === "user");
    if (!userMsg) return;

    const title = userMsg.content.slice(0, 50);
    const now = Date.now();

    setSessions((prev) => {
      // If we have an active session, update it
      if (activeSessionId) {
        const updated = prev.map((s) =>
          s.id === activeSessionId ? { ...s, messages, title } : s
        );
        saveSessions(updated);
        return updated;
      }

      // Create a new session
      const newSession: ChatSession = {
        id: `chat-${now}`,
        title,
        messages,
        createdAt: now,
      };
      const next = [newSession, ...prev].slice(0, 50);
      saveSessions(next);
      setActiveSessionId(newSession.id);
      return next;
    });
  }, [messages]);

  const handleNewChat = () => {
    setActiveSessionId(null);
    onNewChat();
  };

  const handleLoadSession = (session: ChatSession) => {
    setActiveSessionId(session.id);
    onLoadSession?.(session);
  };

  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setSessions((prev) => {
      const next = prev.filter((s) => s.id !== sessionId);
      saveSessions(next);
      return next;
    });
    if (activeSessionId === sessionId) {
      setActiveSessionId(null);
      onNewChat();
    }
  };

  // Group sessions by date
  const grouped = sessions.reduce<Record<string, ChatSession[]>>((acc, s) => {
    const d = new Date(s.createdAt);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    let label: string;
    if (d.toDateString() === today.toDateString()) label = "Today";
    else if (d.toDateString() === yesterday.toDateString()) label = "Yesterday";
    else label = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });

    (acc[label] ??= []).push(s);
    return acc;
  }, {});

  if (!open) return null;

  return (
    <aside className="chat-sidebar">
      {/* Header */}
      <div className="chat-sidebar-header">
        <span className="chat-sidebar-title">Chat</span>
        <button onClick={handleNewChat} title="New chat" className="chat-icon-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 5v14M5 12h14" />
          </svg>
        </button>
      </div>

      <div className="chat-sidebar-divider" />

      {/* Session list */}
      <div className="chat-sidebar-list">
        {Object.entries(grouped).map(([label, items]) => (
          <div key={label}>
            <div className="chat-sidebar-group-label">{label}</div>
            {items.map((session) => (
              <div
                key={session.id}
                className={`chat-sidebar-item ${activeSessionId === session.id ? "chat-sidebar-item-active" : ""} ${hovered === session.id ? "chat-sidebar-item-hover" : ""}`}
                onClick={() => handleLoadSession(session)}
                onMouseEnter={() => setHovered(session.id)}
                onMouseLeave={() => setHovered(null)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  style={{ flexShrink: 0, opacity: 0.5 }}>
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                <span className="chat-sidebar-item-text">{session.title}</span>
                {(hovered === session.id || activeSessionId === session.id) && (
                  <button
                    className="chat-sidebar-delete-btn"
                    onClick={(e) => handleDeleteSession(e, session.id)}
                    title="Delete chat"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        ))}

        {sessions.length === 0 && (
          <div className="chat-sidebar-empty">
            <p>No chats yet</p>
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