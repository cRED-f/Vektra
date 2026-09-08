import Link from "next/link";

type LogoProps = {
  className?: string;
};

/**
 * Vektra mark — an orange glyph (index/graph node) + wordmark.
 */
export function Logo({ className }: LogoProps) {
  return (
    <Link
      href="/"
      className={`group inline-flex items-center gap-2 font-sans ${className ?? ""}`}
      aria-label="Vektra home"
    >
      <span className="grid h-6 w-6 place-items-center rounded-full bg-ember-orange text-canvas">
        <svg
          viewBox="0 0 16 16"
          className="h-3.5 w-3.5"
          fill="currentColor"
          aria-hidden
        >
          <circle cx="8" cy="3" r="2" />
          <circle cx="3.5" cy="12" r="2" />
          <circle cx="12.5" cy="12" r="2" />
          <path d="M7 4.6 4.6 10.2M9 4.6l2.4 5.6" stroke="currentColor" strokeWidth="1.4" />
        </svg>
      </span>
      <span className="text-[15px] font-medium tracking-tight text-ink">Vektra</span>
    </Link>
  );
}