"use client";

import { useState } from "react";

type Mode = "chat" | "retrieve" | "benchmark";

const MODES: { id: Mode; label: string }[] = [
  { id: "chat", label: "chat" },
  { id: "retrieve", label: "retrieve" },
  { id: "benchmark", label: "benchmark" },
];

export function QueryBar() {
  const [mode, setMode] = useState<Mode>("chat");
  const [query, setQuery] = useState("");

  return (
    <form
      className="relative flex w-full max-w-3xl items-center gap-2 rounded-full border border-gridline bg-white px-5 py-2 shadow-subtle"
      onSubmit={(e) => e.preventDefault()}
      aria-label="Query the corpus"
    >
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask anything across your corpus…"
        className="min-w-0 flex-1 bg-transparent font-suisse text-body text-ink outline-none placeholder:text-stone"
      />

      <div className="flex items-center gap-1">
        {MODES.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            onClick={() => setMode(id)}
            aria-pressed={mode === id}
            className={`rounded-full px-[10px] py-1 font-mono text-caption font-medium tracking-[0.01em] transition-colors ${
              mode === id
                ? "bg-ink text-white"
                : "bg-vellum text-ink hover:bg-gridline/60"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <button
        type="submit"
        aria-label={`Submit ${mode} query`}
        className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-ember-orange text-white transition-opacity hover:opacity-90"
      >
        <svg width={16} height={16} viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path
            d="M2 8h11M9 3.5 13.5 8 9 12.5"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </form>
  );
}