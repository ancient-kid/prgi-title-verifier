"use client";

import React, { useState, useEffect } from "react";
import { BookOpen, Search, ShieldCheck } from "lucide-react";

export default function PRGIRulebook() {
  const [guidelines, setGuidelines] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRules = async () => {
      try {
        const res = await fetch("/api/guidelines");
        if (res.ok) {
          const data = await res.json();
          setGuidelines(data.guidelines || []);
        }
      } catch (err) {
        console.error("Fetch guidelines error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchRules();
  }, []);

  const filteredRules = guidelines.filter(
    (g) =>
      g.title?.toLowerCase().includes(search.toLowerCase()) ||
      g.guideline_ref?.toLowerCase().includes(search.toLowerCase()) ||
      g.category?.toLowerCase().includes(search.toLowerCase()) ||
      g.description?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="parchment-card p-6 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-[#E3DAC7] pb-4 gap-3">
        <div>
          <div className="flex items-center gap-2 font-bold text-base text-[#1A202C]">
            <BookOpen className="w-5 h-5 text-[#1E7B62]" />
            <span>PRGI Guidelines for Admissibility of Titles (18 Statutory Rules)</span>
          </div>
          <p className="text-xs text-[#64748B] mt-1">
            <strong>GOVERNMENT OF INDIA</strong> &bull; Office of the Press Registrar General of India (M/o I&B) &bull; Implemented w.e.f. <strong>01.07.2025</strong> under Sec 5(3)(C) read with Sec 2(g) of the PRP Act 2023
          </p>
        </div>
        <span className="text-xs font-semibold px-3 py-1 bg-[#D5EDE3] text-[#166552] rounded-full self-start md:self-auto">
          18 Statutory Rules
        </span>
      </div>

      {/* Search Input */}
      <div className="relative">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter all 18 rules by keyword, topic, or rule number (e.g. 'root word', 'police', 'Guideline 12')..."
          className="w-full input-field pl-10 text-xs font-medium"
        />
        <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
      </div>

      {/* Rules Grid */}
      {loading ? (
        <div className="text-center py-10 text-xs text-[#64748B]">Loading statutory guidelines...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredRules.map((rule, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-white/80 border border-[#E3DAC7] hover:border-[#1E7B62] transition-all flex flex-col justify-between gap-3"
            >
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-extrabold text-[#1E7B62] uppercase tracking-wider">
                    {rule.guideline_ref}
                  </span>
                  {rule.category && (
                    <span className="text-[10px] px-2 py-0.5 rounded-md bg-[#EAE4D6] text-[#4A5568] font-bold">
                      {rule.category}
                    </span>
                  )}
                </div>
                <h3 className="text-xs font-bold text-[#1A202C] leading-snug">{rule.title}</h3>
                <p className="text-[11px] text-[#64748B] leading-relaxed mt-1">{rule.description}</p>
              </div>

              {rule.examples && rule.examples.length > 0 && (
                <div className="pt-2 border-t border-[#E3DAC7]/60">
                  <span className="text-[10px] font-bold text-[#64748B] uppercase">Examples:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {rule.examples.map((ex, exIdx) => (
                      <span
                        key={exIdx}
                        className="text-[10px] px-2 py-0.5 bg-[#F4F2E9] text-[#2D3748] rounded border border-[#E3DAC7]"
                      >
                        {ex}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
