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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      {/* Header */}
      <div className="space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 text-xs font-mono">
          <span>THREAT CLASSIFICATION TAXONOMY</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black font-display text-white">
          32 Threat Archetype Prototype Fingerprints
        </h1>
        <p className="text-sm sm:text-base text-slate-300 max-w-3xl leading-relaxed">
          The JEV Evidence module measures cosine similarity against 32 standardized threat vectors tailored specifically for Indic morphology, vernacular slang, and code-mixed deception attacks.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-strong rounded-3xl p-6 border border-cyan-500/20 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Category Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 w-full sm:w-auto">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-mono transition-all ${
                  selectedCategory === cat
                    ? "bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20"
                    : "bg-white/5 text-slate-300 hover:bg-white/10"
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
              className="w-full bg-slate-950/80 rounded-xl px-3.5 py-2 text-xs font-mono text-slate-100 border border-white/10 focus:border-cyan-400 focus:outline-none"
            />
          </div>
        </div>
      </div>

      {/* Archetypes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredArchetypes.map((arch: ThreatArchetype) => (
          <div
            key={arch.id}
            className="glass rounded-2xl p-5 border border-white/10 hover:border-cyan-400/40 transition-all hover:-translate-y-1 flex flex-col justify-between space-y-4"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-cyan-400 font-bold">
                  Prototype #{arch.id}
                </span>
                <span
                  className={`badge ${
                    arch.severity === "CRITICAL"
                      ? "badge-red"
                      : arch.severity === "HIGH"
                      ? "badge-amber"
                      : "badge-blue"
                  } text-[10px]`}
                >
                  {arch.severity}
                </span>
              </div>

              <h3 className="text-base font-bold text-white font-display mb-1.5">
                {arch.name}
              </h3>

              <div className="text-[11px] font-mono text-purple-300 mb-2">
                Category: {arch.category}
              </div>

              <p className="text-xs text-slate-300/80 leading-relaxed">
                {arch.description}
              </p>
            </div>

            <div className="space-y-2 pt-3 border-t border-white/5 text-xs font-mono">
              <div className="text-[11px] text-cyan-300/80">
                <span className="text-slate-400">Indic Target:</span> {arch.indic_target}
              </div>
              <div className="bg-black/60 p-2.5 rounded-lg text-[11px] text-slate-300 border border-white/5 truncate">
                <span className="text-slate-500">Ex: </span>
                {arch.example_prompt}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom CTA */}
      <div className="glass p-6 rounded-3xl border border-cyan-500/20 text-center space-y-3">
        <h3 className="text-lg font-bold text-white font-display">
          Ready to test these archetypes against live models?
        </h3>
        <p className="text-xs text-slate-300 max-w-xl mx-auto">
          Launch our live testing suite to see how IndicShield fingerprinting matches these archetypes in real time with sub-millisecond execution.
        </p>
        <div className="pt-2 flex justify-center gap-4">
          <Link
            href="/playground"
            className="px-6 py-2.5 rounded-xl text-xs font-bold text-slate-950 bg-cyan-400 hover:bg-cyan-300 transition-all shadow-md shadow-cyan-400/20"
          >
            Go to Playground →
          </Link>
          <Link
            href="/arena"
            className="px-6 py-2.5 rounded-xl text-xs font-bold text-rose-300 bg-rose-950/40 border border-rose-500/30 hover:bg-rose-900/40 transition-all"
          >
            View SLM Arena ⚔️
          </Link>
        </div>
      </div>
    </div>
  );
}
