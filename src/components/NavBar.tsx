"use client";

import { Button } from "./Button";
import { Logo } from "./Logo";

/**
 * Navigation bar per DESIGN.md — white, 64px, hairline bottom border.
 * Left: logo. Center: product links. Right: CTA pill.
 * Animated: logo fades in, links stagger, status dot pulses.
 */
const navLinks = ["Retrieval", "Serving", "Benchmarks", "Models"];

export function NavBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-gridline bg-canvas/95 backdrop-blur animate-fade-in">
      <nav className="mx-auto flex h-16 w-full max-w-[var(--page-max-width)] items-center justify-between px-6">
        <div className="animate-fade-in-up" style={{ animationDelay: "0ms" }}>
          <Logo />
        </div>

        <div className="hidden items-center gap-6 md:flex">
          {navLinks.map((link, i) => (
            <a
              key={link}
              href="#"
              className="animate-fade-in text-[14px] font-medium text-ink transition-colors duration-200 hover:text-ember-orange"
              style={{ animationDelay: `${100 + i * 60}ms` }}
            >
              {link}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <span className="hidden items-center gap-1.5 font-mono text-[13px] text-slate lg:flex">
            <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-ember-orange" />
            status: green
          </span>
          <div className="animate-fade-in" style={{ animationDelay: "300ms" }}>
            <Button href="#" variant="ghost" className="hidden sm:inline-flex">
              Sign in
            </Button>
          </div>
          <div className="animate-fade-in" style={{ animationDelay: "380ms" }}>
            <Button href="#">Get started</Button>
          </div>
        </div>
      </nav>
    </header>
  );
}
