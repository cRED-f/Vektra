"use client";

import { useEffect, useState } from "react";

type UseTypewriterOptions = {
  text: string;
  speed?: number;
  delay?: number;
  enabled?: boolean;
};

/**
 * Character-by-character typewriter hook.
 * Returns the current displayed text and whether typing is complete.
 */
export function useTypewriter({
  text,
  speed = 28,
  delay = 0,
  enabled = true,
}: UseTypewriterOptions) {
  const [displayed, setDisplayed] = useState("");
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    if (!enabled) {
      setDisplayed(text);
      setIsDone(true);
      return;
    }

    setDisplayed("");
    setIsDone(false);

    const timeout = setTimeout(() => {
      let i = 0;
      const interval = setInterval(() => {
        i++;
        setDisplayed(text.slice(0, i));
        if (i >= text.length) {
          clearInterval(interval);
          setIsDone(true);
        }
      }, speed);

      return () => clearInterval(interval);
    }, delay);

    return () => clearTimeout(timeout);
  }, [text, speed, delay, enabled]);

  return { displayed, isDone };
}
