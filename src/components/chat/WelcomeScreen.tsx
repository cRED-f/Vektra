"use client";

const SUGGESTIONS = [
  "Summarize my documents",
  "What are the key topics?",
  "Find relevant information",
  "Compare different sections",
];

export default function WelcomeScreen() {
  return (
    <div className="chat-welcome">
      <div className="chat-welcome-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
      </div>
      <h1 className="chat-welcome-heading">How can I help you today?</h1>
      <p className="chat-welcome-sub">
        Ask me anything about your ingested documents.
      </p>

      {/* Quick-start suggestion chips */}
      <div className="chat-suggestions">
        {SUGGESTIONS.map((s) => (
          <button key={s} className="chat-suggestion-chip">
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
