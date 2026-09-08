"use client";

import { useEffect, useState } from "react";

const PHRASES = [
  "how does reranking work?",
  "explain hybrid retrieval",
  "compare quantization methods",
  "summarize the documentation",
  "what models are available?",
];

/**
 * Cycles through placeholder phrases with a typewriter effect.
 * Types out each phrase, pauses, deletes it, then moves to the next.
 */
export function useTypingPlaceholder({
  typeSpeed = 55,
  deleteSpeed = 30,
  pauseAfter = 2400,
  pauseBefore = 400,
}: {
  typeSpeed?: number;
  deleteSpeed?: number;
  pauseAfter?: number;
  pauseBefore?: number;
} = {}) {
  const [text, setText] = useState("");
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const phrase = PHRASES[phraseIndex];

    // Typing phase
    if (!isDeleting) {
      if (text.length < phrase.length) {
        const timer = setTimeout(() => {
          setText(phrase.slice(0, text.length + 1));
        }, typeSpeed);
        return () => clearTimeout(timer);
      }
      // Finished typing — pause then start deleting
      const timer = setTimeout(() => setIsDeleting(true), pauseAfter);
      return () => clearTimeout(timer);
    }

    // Deleting phase
    if (text.length > 0) {
      const timer = setTimeout(() => {
        setText(text.slice(0, -1));
      }, deleteSpeed);
      return () => clearTimeout(timer);
    }

    // Finished deleting — move to next phrase after a short pause
    const timer = setTimeout(() => {
      setPhraseIndex((i) => (i + 1) % PHRASES.length);
      setIsDeleting(false);
    }, pauseBefore);
    return () => clearTimeout(timer);
  }, [text, isDeleting, phraseIndex, typeSpeed, deleteSpeed, pauseAfter, pauseBefore]);

  return text;
}
