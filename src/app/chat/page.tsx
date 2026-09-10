"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ChatSidebar from "@/components/chat/ChatSidebar";
import MessageBubble from "@/components/chat/MessageBubble";
import ChatInput from "@/components/chat/ChatInput";
import WelcomeScreen from "@/components/chat/WelcomeScreen";
import FileUploader, {
  type FileUploaderHandle,
  type UploadItem,
} from "@/components/chat/FileUploader";

const API_URL = "http://localhost:8000";
const API_TOKEN = "dev-token-change-in-production";

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
  const [statusBarOpen, setStatusBarOpen] = useState(false);
  const [uploadItems, setUploadItems] = useState<UploadItem[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const uploaderRef = useRef<FileUploaderHandle>(null);
  const wideScreen = useMediaQuery("(min-width: 768px)");

  useEffect(() => {
    if (!wideScreen) setSidebarOpen(false);
  }, [wideScreen]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, uploadItems, statusBarOpen]);

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      if (e) e.preventDefault();
      const query = input.trim();
      if (!query || isLoading) return;

      const userMessage: Message = { id: crypto.randomUUID(), role: "user", content: query };
      const assistantMessage: Message = { id: crypto.randomUUID(), role: "assistant", content: "" };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setInput("");
      setIsLoading(true);

      // Build conversation history for backend
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      try {
        const res = await fetch(`${API_URL}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${API_TOKEN}` },
          body: JSON.stringify({
            query,
            stream: true,
            top_k: 5,
            history,
          }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Request failed" }));
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessage.id ? { ...m, content: err.detail || "Something went wrong." } : m
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
              if (data)
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMessage.id ? { ...m, content: m.content + data } : m
                  )
                );
            }
          }
        }
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id ? { ...m, content: "Failed to connect to server." } : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [input, isLoading, messages]
  );

  const handleNewChat = () => {
    setMessages([]);
    setInput("");
    setIsLoading(false);
    setUploadItems([]);
    setStatusBarOpen(false);
  };

  const handleLoadSession = useCallback((session: { messages: Message[] }) => {
    setMessages(session.messages);
    setInput("");
    setUploadItems([]);
    setStatusBarOpen(false);
  }, []);

  const handleFilesComplete = useCallback((completed: number) => {
    setStatusBarOpen(true);
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `✓ ${completed} file(s) ingested and indexed.`,
      },
    ]);
  }, []);

  const handleUploadProgress = useCallback((items: UploadItem[]) => {
    setUploadItems(items);
    if (items.length > 0) setStatusBarOpen(true);
  }, []);

  const openFilePicker = () => uploaderRef.current?.openPicker();

  const statusCount = uploadItems.filter((i) => i.status === "completed").length;

  return (
    <div className="chat-root">
      <ChatSidebar
        open={sidebarOpen && wideScreen}
        onNewChat={handleNewChat}
        messages={messages}
        onLoadSession={handleLoadSession}
      />

      <div className="chat-main">
        {/* Header */}
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

          {/* Status bar toggle */}
          {uploadItems.length > 0 && (
            <button
              className={`chat-status-toggle ${statusBarOpen ? "active" : ""}`}
              onClick={() => setStatusBarOpen((v) => !v)}
              title="Processing status"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
              <span className="chat-status-badge">{statusCount}/{uploadItems.length}</span>
            </button>
          )}
        </header>

        {/* Hidden file input */}
        <FileUploader
          ref={uploaderRef}
          onFilesComplete={handleFilesComplete}
          onProgressUpdate={handleUploadProgress}
        />

        {/* Body: chat scroll area with inline status bar below last message */}
        <div className="chat-body">
          <div ref={scrollRef} className="chat-scroll">
            {messages.length === 0 && uploadItems.length === 0 ? (
              <WelcomeScreen />
            ) : (
              <div className="chat-messages">
                {messages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}

                {/* Vertical status bar — rendered below the last chat message */}
                {statusBarOpen && uploadItems.length > 0 && (
                  <div className="status-vertical-bar">
                    <div className="status-bar-header">
                      <span className="status-bar-title">Processing</span>
                      <button
                        className="status-bar-close"
                        onClick={() => setStatusBarOpen(false)}
                        title="Hide"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                          stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="18" y1="6" x2="6" y2="18" />
                          <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                      </button>
                    </div>

                    <div className="status-bar-list">
                      {uploadItems.map((item) => (
                        <div key={item.fileName} className="status-bar-item">
                          <div className="status-bar-item-top">
                            <div className={`status-dot ${item.status}`} />
                            <span className="status-bar-item-name">{item.fileName}</span>
                          </div>
                          <div className="status-bar-track">
                            <div
                              className={`status-bar-fill ${item.status}`}
                              style={{ width: `${item.progress}%` }}
                            />
                          </div>
                          <div className="status-bar-item-bottom">
                            <span className="status-bar-item-msg">{item.message}</span>
                            <span className="status-bar-item-pct">{item.progress}%</span>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="status-bar-footer">
                      {statusCount > 0 && (
                        <p className="status-bar-done">✓ {statusCount} file(s) ready</p>
                      )}
                      <p className="status-bar-hint">Files appear here during processing</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Input area */}
        <div className="chat-input-area">
          <ChatInput
            value={input}
            onChange={setInput}
            onSubmit={handleSubmit}
            onFileSelect={openFilePicker}
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