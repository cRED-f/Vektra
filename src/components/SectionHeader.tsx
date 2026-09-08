import { useInView } from "@/hooks/useInView";

type SectionHeaderProps = {
  index: string;
  label: string;
  title: string;
  highlight?: string;
};

/**
 * Numbered section header per DESIGN.md: orange dot + mono index + "/" +
 * uppercase mono label, on a 2px orange vertical line, below a display heading.
 * Animated: slide-in-left on scroll, heading fade-in-up with stagger.
 */
export function SectionHeader({ index, label, title, highlight }: SectionHeaderProps) {
  const { ref } = useInView();

  return (
    <div ref={ref} className="mx-auto flex max-w-[var(--page-max-width)] flex-col gap-8 px-6">
      <div className="reveal-left border-l-2 border-ember-orange pl-4">
        <div className="flex items-center gap-2">
          <span className="h-1 w-1 rounded-full bg-ember-orange" />
          <span className="font-mono text-[12px] text-slate">{index}</span>
          <span className="font-mono text-[12px] text-slate">/</span>
          <span className="font-mono text-[12px] uppercase tracking-wide text-slate">{label}</span>
        </div>
      </div>
      <h2 className="reveal max-w-3xl text-[40px] font-medium leading-[1.1] tracking-[-0.2px] text-ink" style={{ transitionDelay: "120ms" }}>
        {title}
        {highlight ? (
          <>
            {" "}
            <span className="text-ember-orange">{highlight}</span>
          </>
        ) : null}
      </h2>
    </div>
  );
}
