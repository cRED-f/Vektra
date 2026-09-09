"use client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`chat-msg ${isUser ? "chat-msg-user" : "chat-msg-assistant"}`}>
      <div className="chat-msg-inner">
        {/* Avatar */}
        <div className={`chat-avatar ${isUser ? "chat-avatar-user" : "chat-avatar-bot"}`}>
          {isUser ? "U" : "V"}
        </div>

        {/* Message content */}
        <div className="chat-msg-content">
          {message.content === "" ? (
            <div className="chat-typing">
              <span />
              <span />
              <span />
            </div>
          ) : (
            message.content
          )}
        </div>
      </div>
    </div>
  );
}
