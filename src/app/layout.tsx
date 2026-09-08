import type { Metadata } from "next";
import { Inter, Geist_Mono } from "next/font/google";
import "./globals.css";

// DESIGN.md font pairing: Suisse (humanist grotesque) + Geist Mono.
// Suisse is not free → Inter is the documented substitute; Geist Mono is free.
const suisse = Inter({
  variable: "--font-suisse",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Vektra",
  description:
    "Production retrieval and model serving platform — hybrid RAG, dynamic batching, and measured latency on free, open-source infrastructure.",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${suisse.variable} ${geistMono.variable} h-full antialiased js-ready`}
    >
      <body className="min-h-full flex flex-col bg-canvas text-ink">
        {children}
      </body>
    </html>
  );
}