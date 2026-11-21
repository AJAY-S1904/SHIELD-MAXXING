"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();
  const [backendOnline, setBackendOnline] = useState<boolean>(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  useEffect(() => {
    // Health probe to backend
    const checkHealth = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/health", { method: "GET" });
        setBackendOnline(res.ok);
      } catch {
        setBackendOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  const navLinks = [
    { href: "/", label: "Overview" },
    { href: "/playground", label: "Live Testing" },
    { href: "/pipeline", label: "Dual Model & JEV X-Ray" },
    { href: "/arena", label: "Abliterated Arena" },
    { href: "/archetypes", label: "32 Archetypes" },
    { href: "/architecture", label: "ONNX & Edge" },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 nav-bar border-b border-cyan-500/15">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand Logo & Model Tag */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/30 group-hover:scale-105 transition-transform">
            <span className="text-lg">🛡️</span>
            <div className="absolute inset-0 rounded-xl bg-cyan-400/30 blur-sm opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-base tracking-tight text-white font-display">
                Indic<span className="text-cyan-400">Shield</span>
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/60 text-cyan-300 border border-cyan-500/30">
                JEV-v2
              </span>
            </div>
            <p className="text-[10px] text-cyan-200/60 font-mono tracking-wider -mt-0.5">
              IndicBERT ✕ Qwen2.5 ✕ JEV
            </p>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center space-x-1">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold tracking-wide transition-all ${
                  isActive
                    ? "bg-cyan-500/15 text-cyan-300 border border-cyan-400/40 shadow-sm shadow-cyan-500/20"
                    : "text-slate-300 hover:text-white hover:bg-white/5"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Right Status Indicator & Action CTA */}
        <div className="hidden sm:flex items-center space-x-3">
          <div
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-[11px] font-mono border ${
              backendOnline
                ? "bg-emerald-950/40 border-emerald-500/30 text-emerald-300"
                : "bg-amber-950/40 border-amber-500/30 text-amber-300"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                backendOnline ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
              }`}
            />
            <span>{backendOnline ? "PyTorch Engine Live" : "Client Simulation"}</span>
          </div>

          <Link
            href="/playground"
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-950 bg-gradient-to-r from-cyan-400 to-teal-300 hover:from-cyan-300 hover:to-teal-200 shadow-md shadow-cyan-500/25 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            Launch Playground
          </Link>
        </div>

        {/* Mobile menu toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden p-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/10"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {mobileMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-cyan-500/20 bg-slate-950/95 backdrop-blur-2xl px-4 py-4 space-y-2">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-4 py-2.5 rounded-lg text-sm font-medium ${
                pathname === link.href
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/30"
                  : "text-slate-300 hover:bg-white/5"
              }`}
            >
              {link.label}
            </Link>
          ))}
          <div className="pt-2">
            <Link
              href="/playground"
              onClick={() => setMobileMenuOpen(false)}
              className="block w-full text-center py-2.5 rounded-xl text-xs font-bold text-slate-950 bg-gradient-to-r from-cyan-400 to-teal-300"
            >
              Launch Playground
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
