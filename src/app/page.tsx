"use client";

import { useInView } from "@/hooks/useInView";
import { Button } from "@/components/Button";
import { CodeWindow } from "@/components/CodeWindow";
import { HeroInput } from "@/components/HeroInput";
import { NavBar } from "@/components/NavBar";
import { SectionHeader } from "@/components/SectionHeader";

/* ------------------------------------------------------------------ */
/*  Static data                                                        */
/* ------------------------------------------------------------------ */

const features = [
  {
    icon: (
      <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" aria-hidden>
        <path d="M4 6h16M8 12h8M6 18h12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    ),
    title: "Hybrid retrieval",
    body: "Dense + BM25 fused with RRF, then cross-encoder reranked. Query rewriting and multi-hop decomposition for complex questions.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" aria-hidden>
        <path d="M12 3v3m0 12v3M3 12h3m12 0h3M6.3 6.3l2.1 2.1m7.2 7.2 2.1 2.1m0-11.4-2.1 2.1m-7.2 7.2-2.1 2.1" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        <circle cx="12" cy="12" r="3" fill="currentColor" />
      </svg>
    ),
    title: "Model serving",
    body: "Ollama or vLLM behind one interface with dynamic batching and KV-cache tracking. Quantize with GGUF, GPTQ, or AWQ and measure the trade-off.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" aria-hidden>
        <path d="M3 13l4-5 4 7 4-9 6 7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    title: "Observability & eval",
    body: "Prometheus metrics and Grafana dashboards for latency p50/p95/p99, tokens/sec, and queue depth. An eval gate blocks merges on regression.",
  },
];

const models = [
  { name: "nomic-embed-text", params: "0.1B", type: "Embeddings", status: "live" },
  { name: "qwen2.5:1.5b", params: "1.5B", type: "Generation · GGUF Q4", status: "live" },
  { name: "ms-marco-MiniLM-L-6-v2", params: "22.7M", type: "Cross-encoder", status: "live" },
];

const endpoints = [
  "POST /retrieve",
  "POST /chat",
  "POST /benchmark",
  "GET  /models",
  "GET  /health",
];

/* ------------------------------------------------------------------ */
/*  Section wrappers with scroll-reveal                                */
/* ------------------------------------------------------------------ */

function FeaturesSection() {
  const { ref } = useInView();
  return (
    <section ref={ref} className="py-20">
      <SectionHeader
        index="01"
        label="main features"
        title="One platform from"
        highlight="document to answer."
      />
      <div className="mx-auto mt-12 grid max-w-[var(--page-max-width)] gap-6 px-6 md:grid-cols-3">
        {features.map((f, i) => (
          <div
            key={f.title}
            className="reveal hover-lift flex flex-col items-center gap-4 rounded-[16px] border border-gridline bg-vellum p-8 text-center"
            style={{ transitionDelay: `${i * 100}ms` }}
          >
            <span className="grid h-10 w-10 place-items-center rounded-full bg-ember-glow-light text-ember-orange transition-transform duration-300 group-hover:scale-110">
              {f.icon}
            </span>
            <h3 className="text-[16px] font-medium text-ink">{f.title}</h3>
            <p className="text-[14px] leading-[1.5] text-slate">{f.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function QuickstartSection() {
  const { ref } = useInView();
  return (
    <section className="py-20">
      <SectionHeader
        index="02"
        label="quickstart"
        title="One typed API for every stage."
      />
      <div className="mx-auto mt-12 grid max-w-[var(--page-max-width)] items-center gap-12 px-6 lg:grid-cols-2">
        <CodeWindow />
        <div ref={ref} className="flex flex-col gap-6">
          {endpoints.map((ep, i) => (
            <div
              key={ep}
              className="reveal flex items-center justify-between border-b border-gridline pb-3 transition-colors duration-200 hover:border-ember-orange/30"
              style={{ transitionDelay: `${i * 80}ms` }}
            >
              <span className="font-mono text-[14px] text-ink">{ep}</span>
              <span className="font-mono text-[12px] text-ember-orange">200</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ModelsSection() {
  const { ref } = useInView();
  return (
    <section className="py-20">
      <SectionHeader index="03" label="registry" title="Models you control." highlight="Locally." />
      <div ref={ref} className="mx-auto mt-12 grid max-w-[var(--page-max-width)] gap-6 px-6 md:grid-cols-3">
        {models.map((m, i) => (
          <div
            key={m.name}
            className="reveal hover-lift flex flex-col gap-3 rounded-[16px] border border-gridline bg-canvas p-6"
            style={{ transitionDelay: `${i * 100}ms` }}
          >
            <div className="flex items-center justify-between">
              <span className="rounded-[999px] bg-ember-orange px-2 py-0.5 font-mono text-[12px] font-medium text-canvas transition-all duration-300 hover:scale-105">
                {m.status}
              </span>
              <span className="font-mono text-[12px] text-ash">{m.params}</span>
            </div>
            <p className="font-mono text-[14px] text-ink">{m.name}</p>
            <p className="text-[14px] text-slate">{m.type}</p>
          </div>
        ))}
      </div>
      <div className="mt-12 flex justify-center gap-4">
        <Button href="#">View the dashboard</Button>
        <Button href="#" variant="ghost">
          Read the docs
        </Button>
      </div>
    </section>
  );
}

function FooterSection() {
  const { ref } = useInView({ rootMargin: "0px" });
  return (
    <footer ref={ref} className="border-t border-gridline">
      <div className="reveal mx-auto flex w-full max-w-[var(--page-max-width)] flex-col items-center gap-4 px-6 py-10 text-center">
        <span className="font-mono text-[12px] text-slate">
          vector · index · retrieve · serve
        </span>
        <p className="text-[14px] text-slate">
          Vektra — built on free, open-source tools. No API fees, no vendor lock-in.
        </p>
      </div>
    </footer>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <NavBar />

      {/* Hero — staggered entrance animations */}
      <section className="relative overflow-hidden border-b border-gridline bg-canvas">
        {/* Grid pattern — fades in slowly as ambient layer */}
        <div className="pointer-events-none absolute inset-0 animate-fade-in bg-grid opacity-0 [mask-image:radial-gradient(600px_300px_at_50%_0%,black,transparent)]" style={{ animationDuration: "1.5s", animationFillMode: "forwards" }} />

        <div className="relative mx-auto flex w-full max-w-[var(--page-max-width)] flex-col items-center gap-8 px-6 py-24 text-center">
          {/* Badge — enter first */}
          <span
            className="animate-fade-in-up inline-flex items-center gap-1.5 rounded-[999px] bg-vellum px-3 py-1 font-mono text-[12px] text-ink"
            style={{ animationDelay: "80ms" }}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-ember-orange" />
            intro · v1.0 · free &amp; open-source
          </span>

          {/* Heading — enter second */}
          <h1
            className="animate-fade-in-up text-[52px] leading-[1.07] font-medium tracking-[-0.26px] text-ink sm:text-[60px]"
            style={{ animationDelay: "200ms" }}
          >
            Retrieval you can <span className="text-ember-orange">ship.</span>
          </h1>

          {/* Subtitle — enter third */}
          <p
            className="animate-fade-in-up max-w-xl text-[16px] leading-[1.5] text-slate"
            style={{ animationDelay: "340ms" }}
          >
            Vektra ingests your documents, indexes them for hybrid retrieval, and serves local
            models behind one typed API — with measured latency, autoscaling, and evaluation
            gated into CI.
          </p>

          {/* Input bar — enters fourth with scale */}
          <HeroInput />

          {/* Tech tag — enter last */}
          <p
            className="animate-fade-in font-mono text-[12px] text-ash"
            style={{ animationDelay: "650ms" }}
          >
            local-first · Ollama + pgvector · cloud free tier in the final phase
          </p>
        </div>
      </section>

      {/* Scroll-triggered sections */}
      <FeaturesSection />
      <QuickstartSection />
      <ModelsSection />
      <FooterSection />
    </div>
  );
}
