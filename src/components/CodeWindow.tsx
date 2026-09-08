"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useInView } from "@/hooks/useInView";
import { useTypewriter } from "@/hooks/useTypewriter";

/* ------------------------------------------------------------------ */
/*  Code examples — one per language / transport                       */
/* ------------------------------------------------------------------ */

type CodeTab = {
  id: string;
  label: string;
  filename: string;
  code: string;
};

const codeTabs: CodeTab[] = [
  {
    id: "curl",
    label: "cURL",
    filename: "chat.sh",
    code: [
      "curl -X POST http://localhost:8000/chat \\",
      '  -H "Authorization: Bearer $VEKTRA_TOKEN" \\',
      '  -H "Content-Type: application/json" \\',
      '  -d \'{"query":"how does reranking work?","stream":true}\'',
    ].join("\n"),
  },
  {
    id: "python",
    label: "Python",
    filename: "chat.py",
    code: [
      "from vektra import Vektra",
      "",
      "client = Vektra(base_url='http://localhost:8000')",
      "",
      "stream = client.chat(",
      '    query="how does reranking work?",',
      "    stream=True,",
      ")",
      "",
      "for chunk in stream:",
      "    print(chunk.content, end='')",
    ].join("\n"),
  },
  {
    id: "typescript",
    label: "TypeScript",
    filename: "chat.ts",
    code: [
      "import { VektraClient } from '@vektra/sdk';",
      "",
      "const client = new VektraClient({",
      "  baseUrl: 'http://localhost:8000',",
      "});",
      "",
      "const stream = await client.chat({",
      '  query: "how does reranking work?",',
      "  stream: true,",
      "});",
      "",
      "for await (const chunk of stream) {",
      "  process.stdout.write(chunk.content);",
      "}",
    ].join("\n"),
  },
  {
    id: "websocket",
    label: "WebSocket",
    filename: "stream.ts",
    code: [
      "const ws = new WebSocket(",
      "  'ws://localhost:8000/ws/chat'",
      ");",
      "",
      "ws.onopen = () =>",
      '  ws.send(JSON.stringify({',
      '    query: "how does reranking work?",',
      "    stream: true",
      "}));",
      "",
      "ws.onmessage = (e) => {",
      "  const { delta } = JSON.parse(e.data);",
      "  process.stdout.write(delta);",
      "};",
    ].join("\n"),
  },
];

/* ------------------------------------------------------------------ */
/*  Typewriter code body                                               */
/* ------------------------------------------------------------------ */

function TypewriterCode({ code, isActive }: { code: string; isActive: boolean }) {
  const { displayed, isDone } = useTypewriter({
    text: code,
    speed: 14,
    delay: 300,
    enabled: isActive,
  });

  return (
    <pre className="font-mono text-[13px] leading-[1.57] text-ink whitespace-pre">
      {displayed}
      {!isDone && (
        <span className="animate-cursor ml-[1px] inline-block h-[15px] w-[2px] translate-y-[2px] bg-ember-orange" />
      )}
    </pre>
  );
}

/* ------------------------------------------------------------------ */
/*  CodeWindow — swappable carousel                                    */
/* ------------------------------------------------------------------ */

type CodeWindowProps = {
  className?: string;
};

/**
 * Code window per DESIGN.md — vellum surface, 8px radius, traffic-light dots,
 * mono filename, copy button. Now with:
 *  - Tabbed carousel (cURL / Python / TypeScript / WebSocket)
 *  - Drag/swipe to swap tabs
 *  - Typewriter animation on the active tab
 */
export function CodeWindow({ className = "" }: CodeWindowProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const { ref: inViewRef, ref: containerRef } = useInView({ rootMargin: "0px 0px -40px 0px" });

  // Merge the two refs
  const setRefs = useCallback(
    (node: HTMLDivElement | null) => {
      (containerRef as React.MutableRefObject<HTMLDivElement | null>).current = node;
      (inViewRef as React.MutableRefObject<HTMLDivElement | null>).current = node;
    },
    [containerRef, inViewRef],
  );

  // Drag state
  const dragRef = useRef({ startX: 0, isDragging: false });
  const [dragOffset, setDragOffset] = useState(0);

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    dragRef.current = { startX: e.clientX, isDragging: true };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, []);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragRef.current.isDragging) return;
    const dx = e.clientX - dragRef.current.startX;
    setDragOffset(dx);
  }, []);

  const handlePointerUp = useCallback(() => {
    if (!dragRef.current.isDragging) return;
    dragRef.current.isDragging = false;

    const threshold = 80;
    if (dragOffset < -threshold && activeIndex < codeTabs.length - 1) {
      setActiveIndex((i) => i + 1);
    } else if (dragOffset > threshold && activeIndex > 0) {
      setActiveIndex((i) => i - 1);
    }
    setDragOffset(0);
  }, [dragOffset, activeIndex]);

  const activeTab = codeTabs[activeIndex];

  // Keyboard nav
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" && activeIndex < codeTabs.length - 1) {
        setActiveIndex((i) => i + 1);
      } else if (e.key === "ArrowLeft" && activeIndex > 0) {
        setActiveIndex((i) => i - 1);
      }
    };
    el.addEventListener("keydown", handler);
    return () => el.removeEventListener("keydown", handler);
  }, [activeIndex, containerRef]);

  return (
    <div
      ref={setRefs}
      tabIndex={0}
      className={`reveal overflow-hidden rounded-[8px] border border-gridline bg-vellum shadow-subtle-3 outline-none ${className}`}
    >
      {/* Tab bar + traffic lights + copy */}
      <div className="flex h-10 items-center gap-3 border-b border-gridline px-4">
        <span className="flex gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-gridline animate-float" style={{ animationDelay: "0ms" }} />
          <span className="h-1.5 w-1.5 rounded-full bg-gridline animate-float" style={{ animationDelay: "200ms" }} />
          <span className="h-1.5 w-1.5 rounded-full bg-gridline animate-float" style={{ animationDelay: "400ms" }} />
        </span>

        {/* Tabs */}
        <div className="flex flex-1 items-center justify-center gap-1">
          {codeTabs.map((tab, i) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveIndex(i)}
              className={`rounded-[999px] px-3 py-0.5 font-mono text-[12px] transition-all duration-200 ${
                i === activeIndex
                  ? "bg-ink text-canvas"
                  : "text-slate hover:bg-gridline hover:text-ink"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Filename + copy */}
        <div className="flex items-center gap-2">
          <span className="font-mono text-[12px] text-slate">{activeTab.filename}</span>
          <button
            type="button"
            className="rounded px-2 py-0.5 font-mono text-[12px] text-ink transition-all duration-200 hover:bg-gridline hover:scale-105 active-scale"
            onClick={() => navigator.clipboard?.writeText(activeTab.code)}
          >
            copy
          </button>
        </div>
      </div>

      {/* Code body — draggable + typewriter */}
      <div
        className="overflow-x-auto p-5 select-none touch-pan-y"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
        style={{
          cursor: dragRef.current.isDragging ? "grabbing" : "grab",
        }}
      >
        <div
          className="transition-transform duration-300 ease-out"
          style={{
            transform: `translateX(${dragOffset * 0.4}px)`,
          }}
        >
          <TypewriterCode code={activeTab.code} isActive={true} />
        </div>
      </div>

      {/* Swipe dots */}
      <div className="flex items-center justify-center gap-1.5 pb-3">
        {codeTabs.map((tab, i) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveIndex(i)}
            className={`rounded-full transition-all duration-300 ${
              i === activeIndex
                ? "h-1.5 w-4 bg-ember-orange"
                : "h-1.5 w-1.5 bg-stone hover:bg-ash"
            }`}
            aria-label={`Switch to ${tab.label} example`}
          />
        ))}
      </div>
    </div>
  );
}
