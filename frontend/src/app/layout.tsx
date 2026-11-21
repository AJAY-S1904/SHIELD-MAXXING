import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IndicShield-JEV | Multilingual AI Safety Guardrail",
  description: "IndicBERTv2 x Qwen2.5-0.5B x JEV Architecture Multilingual Jailbreak & Safety Guardrail",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased selection:bg-cyan-400 selection:text-black">
        {children}
      </body>
    </html>
  );
}
