"use client";

import React, { useState } from "react";
import { Layers, Play, FilePlus, Download } from "lucide-react";

export default function BatchScreening() {
  const [text, setText] = useState(
    "The Crime Investigation Daily\nThe Daily Mumbai Express\nThe Daily News\nHindu Indian Express\nNamascar India\nDaily Evening\nZylophonic Quantum Astroflora"
  );
  const [loading, setLoading] = useState(false);
  const [batchResults, setBatchResults] = useState([]);

  const handleRunBatch = async () => {
    const lines = text
      .split("\n")
      .map((l) => l.strip ? l.strip() : l.trim())
      .filter((l) => l.length > 0);

    if (lines.length === 0) return;

    setLoading(true);
    try {
      const res = await fetch("/api/batch-verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ titles: lines }),
      });
      if (res.ok) {
        const data = await res.json();
        setBatchResults(data.results || []);
      }
    } catch (err) {
      console.error("Batch verification error:", err);
    } finally {
      setLoading(false);
    }
  };

  const total = batchResults.length;
  const approved = batchResults.filter((r) => (r.verification_probability || 0) >= 70).length;
  const rejected = batchResults.filter((r) => (r.verification_probability || 0) < 40).length;
  const review = total - approved - rejected;

  return (
    <div className="parchment-card p-6 flex flex-col gap-6">
      <div className="flex items-center justify-between border-b border-[#E3DAC7] pb-3">
        <div className="flex items-center gap-2 font-bold text-base text-[#1A202C]">
          <Layers className="w-5 h-5 text-[#1E7B62]" />
          <span>High-Throughput Batch Title Verification</span>
        </div>
        <span className="text-xs font-semibold px-3 py-1 bg-[#EAE4D6] text-[#4A5568] rounded-full">
          Screen Hundreds Simultaneously
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 flex flex-col gap-3">
          <label className="text-xs font-bold text-[#2D3748]">Enter Titles (One title per line):</label>
          <textarea
            rows={7}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type titles here..."
            className="input-field w-full text-xs font-mono"
          />
          <div className="flex flex-wrap gap-3 mt-1">
            <button onClick={handleRunBatch} disabled={loading} className="btn-emerald text-xs flex items-center gap-2">
              <Play className="w-3.5 h-3.5" />
              <span>{loading ? "Screening..." : "Run Batch Screen"}</span>
            </button>
            <button
              onClick={() =>
                setText(
                  "The Crime Investigation Daily\nThe Daily Mumbai Express\nThe Daily News\nHindu Indian Express\nNamascar India\nDaily Evening\nZylophonic Quantum Astroflora"
                )
              }
              className="btn-emerald-outline text-xs flex items-center gap-2"
            >
              <FilePlus className="w-3.5 h-3.5" />
              <span>Load Benchmark Sample</span>
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="lg:col-span-4 grid grid-cols-2 gap-3">
          <div className="p-4 rounded-xl bg-white/70 border border-[#E3DAC7] flex flex-col items-center justify-center">
            <span className="text-2xl font-extrabold text-[#1A202C]">{total}</span>
            <span className="text-[11px] font-bold text-[#64748B]">Total Processed</span>
          </div>
          <div className="p-4 rounded-xl bg-[#D5EDE3] border border-[#1E7B62]/20 flex flex-col items-center justify-center">
            <span className="text-2xl font-extrabold text-[#166552]">{approved}</span>
            <span className="text-[11px] font-bold text-[#166552]">Approved (≥70%)</span>
          </div>
          <div className="p-4 rounded-xl bg-[#FED7D7] border border-[#C53030]/20 flex flex-col items-center justify-center">
            <span className="text-2xl font-extrabold text-[#C53030]">{rejected}</span>
            <span className="text-[11px] font-bold text-[#C53030]">Rejected (&lt;40%)</span>
          </div>
          <div className="p-4 rounded-xl bg-[#FEFCBF] border border-[#D69E2E]/20 flex flex-col items-center justify-center">
            <span className="text-2xl font-extrabold text-[#975A16]">{review}</span>
            <span className="text-[11px] font-bold text-[#975A16]">Review Needed</span>
          </div>
        </div>
      </div>

      {/* Batch Results Table */}
      <div className="border border-[#E3DAC7] rounded-xl overflow-hidden bg-white/80">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#F7F2E8] border-b border-[#E3DAC7] text-[#4A5568] font-bold">
            <tr>
              <th className="p-3">#</th>
              <th className="p-3">Submitted Title</th>
              <th className="p-3">Probability</th>
              <th className="p-3">Status</th>
              <th className="p-3">Primary Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E3DAC7]">
            {batchResults.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-6 text-center text-[#64748B]">
                  No batch data loaded. Click 'Run Batch Screen' to analyze.
                </td>
              </tr>
            ) : (
              batchResults.map((item, i) => {
                const prob = Math.round(item.verification_probability || 0);
                return (
                  <tr key={i} className="hover:bg-[#F4F2E9]">
                    <td className="p-3 font-semibold">{i + 1}</td>
                    <td className="p-3 font-bold text-[#1A202C]">{item.raw_title}</td>
                    <td className="p-3 font-extrabold">{prob}%</td>
                    <td className="p-3">
                      <span
                        className={
                          prob >= 70 ? "badge-approved" : prob >= 40 ? "badge-review" : "badge-crimson"
                        }
                      >
                        {prob >= 70 ? "Approved" : prob >= 40 ? "Review" : "Rejected"}
                      </span>
                    </td>
                    <td className="p-3 text-[#64748B]">
                      {item.reasons?.[0]?.explanation || "Clean verification"}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
