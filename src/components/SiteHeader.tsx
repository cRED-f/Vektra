import { Logo } from "./Logo";

const NAV = [
  { label: "Chat", href: "#chat" },
  { label: "Retrieval", href: "#retrieval" },
  { label: "Models", href: "#models" },
  { label: "Benchmarks", href: "#benchmarks" },
  { label: "Docs", href: "#docs" },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-sm border-b border-gridline">
      <div className="mx-auto flex h-16 w-full max-w-[var(--page-max-width)] items-center justify-between gap-6 px-6">
        <a href="#" aria-label="Vektra home" className="shrink-0">
          <Logo />
        </a>

        <nav className="hidden items-center gap-6 md:flex">
          {NAV.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="font-suisse text-body font-medium text-ink transition-colors hover:text-ember-orange"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <span className="hidden items-center gap-2 font-mono text-caption tracking-[0.01em] text-slate sm:inline-flex">
            <span className="flex h-1.5 w-1.5 rounded-full bg-ember-orange" />
            local · ollama
          </span>
          <a
            href="#chat"
            className="inline-flex items-center gap-2 rounded-full bg-ember-orange px-[18px] py-[10px] font-suisse text-body font-medium tracking-[0.01em] text-white shadow-[0_0_0_6px_var(--color-ember-glow-light)] transition-opacity hover:opacity-90"
          >
            New query
          </a>
        </div>
      </div>
    </header>
  );
}