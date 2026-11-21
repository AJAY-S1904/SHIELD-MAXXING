"use client";

import React, { useState } from "react";
import Link from "next/link";
import { THREAT_ARCHETYPES_CATALOG, ThreatArchetype } from "@/lib/types";

export default function ArchetypesPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [searchTerm, setSearchTerm] = useState<string>("");

  const categories = ["All", "Jailbreak", "Deception", "Cyber", "Theft", "Harmful", "Vernacular"];

  const filteredArchetypes = THREAT_ARCHETYPES_CATALOG.filter((item) => {
    const matchesCategory = selectedCategory === "All" || item.category === selectedCategory;
    const matchesSearch =
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.indic_target.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-16 pb-12 space-y-8">
      {/* Header */}
      <div className="space-y-3 pb-4 border-b border-white/20">
        <div className="aero-pill text-xs font-mono">
          THREAT CLASSIFICATION TAXONOMY
        </div>
        <h1 className="text-4xl sm:text-5xl font-black font-display text-white tracking-tight drop-shadow">
          32 Threat Archetype Prototype Fingerprints
        </h1>
        <p className="text-sm sm:text-base text-white/85 max-w-3xl leading-relaxed font-sans">
          The JEV Evidence module measures cosine similarity against 32 standardized threat vectors tailored specifically for Indic morphology, vernacular slang, and code-mixed deception attacks.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="aero-glass-strong rounded-3xl p-6 border border-white/60 shadow-2xl space-y-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Category Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 w-full sm:w-auto">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-mono transition-all ${
                  selectedCategory === cat
                    ? "aero-pill-active font-bold text-white shadow-md"
                    : "aero-pill text-white/80 hover:bg-white/20"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="w-full sm:w-72">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search threat name or keyword..."
              className="w-full aero-glass-dark rounded-full px-4 py-2 text-xs font-mono text-white border border-white/40 focus:border-white focus:outline-none placeholder-white/50"
            />
          </div>
        </div>
      </div>

      {/* Archetypes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredArchetypes.map((arch: ThreatArchetype) => (
          <div
            key={arch.id}
            className="aero-glass rounded-3xl p-6 border border-white/50 hover:-translate-y-1 transition-all flex flex-col justify-between space-y-4 shadow-xl"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-emerald-200 font-bold">
                  Prototype #{arch.id}
                </span>
                <span
                  className={`aero-pill text-[10px] font-bold ${
                    arch.severity === "CRITICAL"
                      ? "text-rose-200 bg-rose-500/30 border-rose-300"
                      : arch.severity === "HIGH"
                      ? "text-amber-200 bg-amber-500/30 border-amber-300"
                      : "text-emerald-200 bg-emerald-500/30 border-emerald-300"
                  }`}
                >
                  {arch.severity}
                </span>
              </div>

              <h3 className="text-base font-bold text-white font-display mb-1.5 drop-shadow">
                {arch.name}
              </h3>

              <div className="text-[11px] font-mono text-cyan-200 mb-2">
                Category: {arch.category}
              </div>

              <p className="text-xs text-white/85 leading-relaxed font-sans">
                {arch.description}
              </p>
            </div>

            <div className="space-y-2 pt-3 border-t border-white/15 text-xs font-mono">
              <div className="text-[11px] text-white/80">
                <span className="text-emerald-200">Indic Target:</span> {arch.indic_target}
              </div>
              <div className="bg-black/50 p-2.5 rounded-xl text-[11px] text-white/90 border border-white/10 truncate">
                <span className="text-white/50">Ex: </span>
                {arch.example_prompt}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom CTA */}
      <div className="aero-glass-strong p-8 rounded-3xl border border-white/60 text-center space-y-4 shadow-2xl">
        <h3 className="text-xl font-bold text-white font-display drop-shadow">
          Ready to test these archetypes against live models?
        </h3>
        <p className="text-xs text-white/85 max-w-xl mx-auto font-sans leading-relaxed">
          Launch our live testing suite to see how IndicShield fingerprinting matches these archetypes in real time with sub-millisecond execution.
        </p>
        <div className="pt-2 flex justify-center gap-4">
          <Link href="/playground" className="btn-aero-green">
            <span>Go to Playground →</span>
          </Link>
          <Link href="/arena" className="btn-aero-glass">
            <span>View SLM Arena ⚔️</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
