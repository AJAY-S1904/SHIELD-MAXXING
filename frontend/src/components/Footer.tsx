"use client";

import React from "react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-white/20 aero-glass-strong relative z-10 py-12 mt-16">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-200 via-emerald-400 to-teal-700 shadow-md flex items-center justify-center text-white border border-white/70">
                🛡️
              </div>
              <span className="font-extrabold text-xl text-white font-display tracking-tight drop-shadow">
                Indic<span className="text-emerald-200">Shield</span>
              </span>
            </div>
            <p className="text-xs sm:text-sm text-white/85 max-w-md leading-relaxed font-sans">
              Sub-20ms Multilingual AI Safety Guardrail engineered specifically for 12+ native Indian scripts, Hinglish code-mixed transliteration, and adversarial social engineering exploits.
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="aero-pill text-[11px]">IndicBERTv2 (768d)</span>
              <span className="aero-pill text-[11px]">Qwen2.5-0.5B (896d)</span>
              <span className="aero-pill text-[11px]">JEV Cross-Attention</span>
              <span className="aero-pill text-[11px]">18.4 MB ONNX Edge</span>
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
              Guardrail Modules
            </h4>
            <ul className="space-y-2 text-xs text-white/85 font-sans">
              <li>
                <Link href="/playground" className="hover:text-emerald-200 transition-colors">
                  Live Testing Playground
                </Link>
              </li>
              <li>
                <Link href="/arena" className="hover:text-emerald-200 transition-colors">
                  Abliterated SLM Arena
                </Link>
              </li>
              <li>
                <Link href="/pipeline" className="hover:text-emerald-200 transition-colors">
                  Dual-Model & JEV X-Ray
                </Link>
              </li>
              <li>
                <Link href="/archetypes" className="hover:text-emerald-200 transition-colors">
                  32 Threat Archetypes
                </Link>
              </li>
            </ul>
          </div>

          {/* Repository & Specs */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
              Research & GitHub
            </h4>
            <ul className="space-y-2 text-xs text-white/85 font-sans">
              <li>
                <a
                  href="https://github.com/AJAY-S1904/SHIELD-MAXXING"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-emerald-200 transition-colors flex items-center space-x-1"
                >
                  <span>GitHub Repository</span>
                  <span>↗</span>
                </a>
              </li>
              <li>
                <Link href="/architecture" className="hover:text-emerald-200 transition-colors">
                  ONNX Standalone Architecture
                </Link>
              </li>
              <li>
                <span className="text-emerald-200 font-mono">
                  Latency: 12.4ms avg edge inference
                </span>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/20 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-white/70 gap-4 font-mono">
          <p>© 2026 IndicShield Project · Frutiger Aero Safety Intelligence</p>
          <div className="flex items-center space-x-4">
            <span>Branch: <strong className="text-white">main</strong></span>
            <span>Edge Ready: <strong className="text-emerald-300">ONNX 18.4 MB</strong></span>
          </div>
        </div>
      </div>
    </footer>
  );
}
