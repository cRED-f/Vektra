"use client";

import { useState } from "react";
import { useTypingPlaceholder } from "@/hooks/useTypingPlaceholder";

/**
 * Hero input bar per DESIGN.md "Search/Scrape Input Bar":
 * white container, 999px radius, gridline border, mono action chips,
 * trailing 36px square ember submit with arrow.
 * Animated: scale-in entrance, focus glow, chip hover, typing placeholder.
 */
const actionChips = ["Search", "Embed", "Rerank", "Stream"];

export function HeroInput() {
  const [value, setValue] = useState("");
  const placeholder = useTypingPlaceholder();

  return (
    <form
      className="animate-scale-in flex w-full max-w-[680px] items-center gap-2 rounded-[999px] border border-gridline bg-white p-2 pl-5 shadow-subtle focus-glow"
      style={{ animationDelay: "500ms" }}
      onSubmit={(e) => e.preventDefault()}
    >
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={`Ask your corpus… try "${placeholder}"`}
        className="flex-1 bg-transparent font-sans text-[14px] text-ink placeholder:text-stone focus:outline-none"
        aria-label="Ask your corpus"
      />

      <div className="hidden items-center gap-1 sm:flex">
        {actionChips.map((chip, i) => (
          <button
            key={chip}
            type="button"
            className={`rounded-[999px] px-2.5 py-1 font-mono text-[13px] font-medium transition-all duration-200 ${
              i === 0
                ? "bg-ink text-canvas"
                : "bg-vellum text-ink hover:bg-gridline hover:-translate-y-[1px]"
            }`}
          >
            {chip}
          </button>
        ))}
      </div>

      <button
        type="submit"
        aria-label="Ask"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-ember-orange text-canvas shadow-subtle transition-all duration-200 hover:bg-[#e64400] hover:scale-110 hover:shadow-xl active-scale"
      >
        <svg viewBox="0 0 16 16" className="h-4 w-4" fill="currentColor" aria-hidden>
          <path d="M7 4 11 8l-4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <path d="M3 8h7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      </button>
    </form>
  );
}
