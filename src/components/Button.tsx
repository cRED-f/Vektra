import Link from "next/link";

type ButtonProps = {
  children: React.ReactNode;
  href?: string;
  variant?: "primary" | "ghost";
  className?: string;
};

/**
 * Pill buttons per DESIGN.md:
 *  - primary: filled ember-orange, white text, soft glow ring, 999px radius
 *  - ghost:   transparent, ink text, vellum fill on hover
 * Animated: press scale, smooth transitions.
 */
export function Button({
  children,
  href,
  variant = "primary",
  className = "",
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-1.5 rounded-[999px] px-[18px] py-[10px] text-[14px] font-medium tracking-[0.01em] transition-all duration-200 ease-out active-scale";
  const styles = {
    primary:
      "bg-ember-orange text-canvas shadow-subtle hover:bg-[#e64400] hover:shadow-xl hover:-translate-y-[1px]",
    ghost: "text-ink hover:bg-vellum hover:-translate-y-[1px]",
  } as const;

  if (href) {
    return (
      <Link href={href} className={`${base} ${styles[variant]} ${className}`}>
        {children}
      </Link>
    );
  }
  return (
    <button className={`${base} ${styles[variant]} ${className}`}>
      {children}
    </button>
  );
}
