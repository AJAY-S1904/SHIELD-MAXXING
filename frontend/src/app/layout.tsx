import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import AnimatedBackground from "@/components/AnimatedBackground";

export const metadata: Metadata = {
  title: "IndicShield-JEV | Multilingual AI Safety Guardrail",
  description: "IndicBERTv2 ✕ Qwen2.5-0.5B ✕ JEV Cross-Attention Multilingual Safety Guardrail for Indic Languages and Code-Mixed Exploits",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased selection:bg-cyan-400 selection:text-black min-h-screen flex flex-col bg-[#03080f] text-slate-100 overflow-x-hidden font-sans">
        <AnimatedBackground />
        <Navbar />
        <main className="flex-1 pt-16 relative z-10 flex flex-col">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
