"use client";

import { useEffect, useRef, useState } from "react";

type UseInViewOptions = {
  /** Trigger once, or every time it enters/exits */
  once?: boolean;
  /** Root margin for early trigger */
  rootMargin?: string;
  /** % of element visible to trigger */
  threshold?: number;
};

/**
 * Intersection Observer hook — reveals the target element when it scrolls
 * into view. Works by adding .revealed class which overrides the opacity:0
 * set by .js-ready .reveal in globals.css.
 *
 * Without JS, text is always visible (no-JS safety).
 */
export function useInView({
  once = true,
  rootMargin = "0px 0px -60px 0px",
  threshold = 0.15,
}: UseInViewOptions = {}) {
  const ref = useRef<HTMLDivElement>(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // If JS-ready class isn't on the element's ancestor, nothing to hide
    const isJsReady = document.documentElement.classList.contains("js-ready");

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          if (isJsReady) {
            el.classList.add("revealed");
            // Also reveal all child .reveal / .reveal-left / .reveal-scale elements
            el.querySelectorAll(".reveal, .reveal-left, .reveal-scale").forEach((child) => {
              child.classList.add("revealed");
            });
          }
          if (once) observer.unobserve(el);
        } else if (!once) {
          setIsInView(false);
          if (isJsReady) {
            el.classList.remove("revealed");
            el.querySelectorAll(".revealed").forEach((child) => {
              child.classList.remove("revealed");
            });
          }
        }
      },
      { rootMargin, threshold },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [once, rootMargin, threshold]);

  return { ref, isInView };
}
