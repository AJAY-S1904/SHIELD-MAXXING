"use client";

import React from "react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-cyan-500/15 bg-slate-950/80 backdrop-blur-xl relative z-10 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-white shadow-md">
                🛡️
              </div>
              <span className="font-extrabold text-lg text-white font-display tracking-tight">
                Indic<span className="text-cyan-400">Shield-JEV</span>
              </span>
            </div>
            <p className="text-sm text-cyan-100/70 max-w-md leading-relaxed">
              Sub-20ms Multilingual AI Safety Guardrail engineered specifically for 12+ native Indian scripts, Hinglish code-mixed transliteration, and adversarial social engineering exploits.
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="badge badge-blue">IndicBERTv2 (768d)</span>
              <span className="badge badge-purple">Qwen2.5-0.5B (896d)</span>
              <span className="badge badge-green">JEV Cross-Attention</span>
              <span className="badge badge-amber">18.4 MB Edge ONNX</span>
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-cyan-300 uppercase tracking-wider font-mono">
              Guardrail Modules
            </h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li>
                <Link href="/playground" className="hover:text-cyan-300 transition-colors">
                  Interactive Playground
                </Link>
              </li>
              <li>
                <Link href="/pipeline" className="hover:text-cyan-300 transition-colors">
                  Dual-Model & JEV X-Ray
                </Link>
              </li>
              <li>
                <Link href="/arena" className="hover:text-cyan-300 transition-colors">
                  Abliterated SLM Arena (Evidence)
                </Link>
              </li>
              <li>
                <Link href="/archetypes" className="hover:text-cyan-300 transition-colors">
                  32 Threat Archetypes
                </Link>
              </li>
            </ul>
          </div>

          {/* Repository & Specs */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-cyan-300 uppercase tracking-wider font-mono">
              Research & GitHub
            </h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li>
                <a
                  href="https://github.com/AJAY-S1904/SHIELD-MAXXING"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-cyan-300 transition-colors flex items-center space-x-1"
                >
                  <span>GitHub Repository</span>
                  <span>↗</span>
                </a>
              </li>
              <li>
                <Link href="/architecture" className="hover:text-cyan-300 transition-colors">
                  ONNX Standalone Architecture
                </Link>
              </li>
              <li>
                <span className="text-xs font-mono text-emerald-400">
                  Latency: 14.2ms avg edge inference
                </span>
              </li>
              <li>
                <span className="text-xs font-mono text-cyan-300">
                  Dual Backbone: Native Indic + English
                </span>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/5 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© 2026 IndicShield Project. Open source multilingual AI safety research.</p>
          <div className="flex items-center space-x-4">
            <span>Branch: <span className="font-mono text-slate-400">main</span></span>
            <span>Edge Ready: <span className="text-emerald-400">ONNX 18.4 MB</span></span>
          </div>
        </div>
      </div>
    </footer>
  );
}
