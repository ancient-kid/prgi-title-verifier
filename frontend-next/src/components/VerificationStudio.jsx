"use client";

import React, { useState } from "react";
import {
  FileSearch,
  X,
  Scan,
  Lock,
  Gauge,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  CircleAlert,
  CheckCircle2,
  CircleDashed,
  AlertCircle,
  Volume2,
  SpellCheck,
  Globe,
  Copy,
  Lightbulb
} from "lucide-react";

export default function VerificationStudio() {
  const [title, setTitle] = useState("");
  const [language, setLanguage] = useState("English");
  const [periodicity, setPeriodicity] = useState("Daily");
  const [stateUt, setStateUt] = useState("National");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(true);

  const presets = [
    { title: "News+", label: "News+ (Symbols)", type: "red" },
    { title: "2024", label: "2024 (Numeric Only)", type: "red" },
    { title: "The Crime Investigation Daily", label: "Crime Investigation Daily", type: "red" },
    { title: "The Daily Mumbai Express", label: "The Daily Mumbai Express", type: "green" },
    { title: "The Daily News", label: "The Daily News", type: "red" },
    { title: "Hindu Indian Express", label: "Hindu Indian Express", type: "red" },
    { title: "Namascar India", label: "Namascar India", type: "red" },
    { title: "Daily Evening", label: "Daily Evening", type: "red" },
    { title: "Zylophonic Quantum Astroflora", label: "Zylophonic Quantum Astroflora", type: "green" },
  ];

  const handleVerify = async (inputTitle = title) => {
    if (!inputTitle.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("/api/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: inputTitle,
          language,
          periodicity,
          state: stateUt
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (err) {
      console.error("Verification error:", err);
    } finally {
      setLoading(false);
    }
  };

  const prob = result ? Math.round(result.verification_probability || 0) : 0;
  const isRejected = result ? (result.status === "Rejected" || prob < 40) : false;

  // --- Dynamic Stage Status Helpers ---
  const getStage1 = () => {
    if (!result) return { status: "awaiting", subtext: "Extracts anchor and strips generic modifiers" };
    const s1 = result.stage_results?.stage1;
    if (!s1) return { status: "skipped", subtext: "Skipped" };

    if (s1.is_valid_structure === false) {
      let sub = s1.rejection_reason || "Failed: Structural validation error.";
      if (s1.error_type === "PROHIBITED_SYMBOLS") sub = "Failed: Prohibited non-text characters, symbols, or emojis detected.";
      else if (s1.error_type === "PURE_NUMERIC") sub = "Failed: Numeric-only title prohibited (substantive text required).";
      return { status: "failed", subtext: sub };
    }
    if (s1.is_purely_generic) {
      return { status: "failed", subtext: "Failed: Purely generic modifiers without distinctive anchor word." };
    }
    const stripped = (s1.stripped_prefixes || []).concat(s1.stripped_suffixes || []).join(", ");
    return {
      status: "passed",
      subtext: `Extracted Anchor: "${s1.anchor_words || s1.cleaned_title}"${stripped ? ` (Stripped: ${stripped})` : ""}`
    };
  };

  const getStage2 = () => {
    if (!result) return { status: "awaiting", subtext: "Disallowed words, Emblems Act, Police/CBI terms" };
    const s2 = result.stage_results?.stage2;
    if (!s2) return { status: "skipped", subtext: "Skipped due to prior stage rejection." };
    if (!s2.passed) {
      const terms = (s2.violations || []).map(v => v.term).join(", ");
      return { status: "failed", subtext: `Failed: Violated PRGI blacklist${terms ? ` (${terms})` : ""}` };
    }
    return { status: "passed", subtext: "Passed: No prohibited security or law-enforcement terms detected." };
  };

  const getStage3 = () => {
    if (!result) return { status: "awaiting", subtext: "Aho-Corasick compound title detection" };
    const s3 = result.stage_results?.stage3;
    if (!s3) return { status: "skipped", subtext: "Skipped due to prior stage rejection." };
    if (s3.is_frankentitle) {
      const comps = (s3.components || []).join("' + '");
      return { status: "failed", subtext: `Failed: Compound title formed from '${comps}'` };
    }
    return { status: "passed", subtext: "Passed: Not a combination of existing registered titles." };
  };

  const getStage4 = () => {
    if (!result) return { status: "awaiting", subtext: "Phonetic, Orthographic & Cross-Lingual Semantic" };
    const s4 = result.stage_results?.stage4;
    if (!s4) return { status: "skipped", subtext: "Skipped due to prior stage rejection." };
    const highestSim = result.highest_similarity_score || 0;
    if (highestSim >= 70) {
      return { status: "failed", subtext: `Failed: High similarity score (${highestSim}%) against existing database titles.` };
    } else if (highestSim >= 40) {
      return { status: "review", subtext: `Review: Moderate similarity (${highestSim}%).` };
    }
    return { status: "passed", subtext: `Passed: Distinctive title (Highest similarity: ${highestSim}%).` };
  };

  const stage1Info = getStage1();
  const stage2Info = getStage2();
  const stage3Info = getStage3();
  const stage4Info = getStage4();

  const renderStatusBadge = (info) => {
    if (info.status === "failed") {
      return (
        <span className="text-[#C53030] font-bold flex items-center gap-1">
          {info.subtext} <CircleAlert className="w-3.5 h-3.5 fill-[#C53030] text-white shrink-0" />
        </span>
      );
    }
    if (info.status === "passed") {
      return (
        <span className="text-[#1E7B62] font-semibold flex items-center gap-1">
          {info.subtext} <CheckCircle2 className="w-3.5 h-3.5 text-[#1E7B62] shrink-0" />
        </span>
      );
    }
    if (info.status === "review") {
      return (
        <span className="text-[#D69E2E] font-semibold flex items-center gap-1">
          {info.subtext} <AlertCircle className="w-3.5 h-3.5 text-[#D69E2E] shrink-0" />
        </span>
      );
    }
    return (
      <span className="text-[#64748B] flex items-center gap-1">
        {info.subtext} <CircleDashed className="w-3.5 h-3.5 text-gray-400 shrink-0" />
      </span>
    );
  };

  const vectorScores = result?.max_scores;
  const topMatches = result?.top_matches || [];
  const suggestions = result?.suggestions || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Input & Controls Panel */}
      <div className="lg:col-span-5 parchment-card p-6 flex flex-col gap-5">
        <div className="flex items-center justify-between border-b border-[#E3DAC7] pb-3">
          <div className="flex items-center gap-2 font-bold text-base text-[#1A202C]">
            <FileSearch className="w-5 h-5 text-[#1E7B62]" />
            <span>Title Application Verification</span>
          </div>
          <span className="text-[11px] font-semibold px-2.5 py-1 bg-[#EAE4D6] text-[#4A5568] rounded-full">
            Real-time Multi-Stage Funnel
          </span>
        </div>

        {/* Title Input */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-bold text-[#2D3748]">Proposed Periodical / Newspaper Title</label>
          <div className="relative">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. The Daily Mumbai Express, Namascar India..."
              className="w-full input-field pr-10 text-sm font-medium"
            />
            {title && (
              <button
                onClick={() => setTitle("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Dropdowns */}
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-[#2D3748]">Target Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="input-field text-xs font-medium cursor-pointer"
            >
              <option value="English">English</option>
              <option value="Hindi">Hindi (हिंदी)</option>
              <option value="Bengali">Bengali (বাংলা)</option>
              <option value="Marathi">Marathi (मराठी)</option>
              <option value="Tamil">Tamil (தமிழ்)</option>
              <option value="Telugu">Telugu (తెలుగు)</option>
              <option value="Gujarati">Gujarati (ગુજરાતી)</option>
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-[#2D3748]">Periodicity</label>
            <select
              value={periodicity}
              onChange={(e) => setPeriodicity(e.target.value)}
              className="input-field text-xs font-medium cursor-pointer"
            >
              <option value="Daily">Daily</option>
              <option value="Weekly">Weekly</option>
              <option value="Fortnightly">Fortnightly</option>
              <option value="Monthly">Monthly</option>
              <option value="Quarterly">Quarterly</option>
            </select>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-bold text-[#2D3748]">State / UT</label>
          <select
            value={stateUt}
            onChange={(e) => setStateUt(e.target.value)}
            className="input-field text-xs font-medium cursor-pointer"
          >
            <option value="National">National (All India)</option>
            <option value="Delhi">Delhi</option>
            <option value="Maharashtra">Maharashtra</option>
            <option value="Uttar Pradesh">Uttar Pradesh</option>
            <option value="West Bengal">West Bengal</option>
            <option value="Tamil Nadu">Tamil Nadu</option>
            <option value="Karnataka">Karnataka</option>
          </select>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3 mt-2">
          <button
            onClick={() => handleVerify(title)}
            disabled={loading}
            className="btn-emerald flex items-center justify-center gap-2 text-sm shadow-sm"
          >
            <Scan className="w-4 h-4" />
            <span>{loading ? "Verifying..." : "Verify Title Now"}</span>
          </button>
          <button
            disabled={!result || isRejected}
            className={`btn-emerald-outline flex items-center justify-center gap-2 text-sm ${
              !result || isRejected ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            <Lock className="w-4 h-4" />
            <span>Submit & Lock Title</span>
          </button>
        </div>

        {/* Quick Benchmarks Presets */}
        <div className="mt-4 pt-4 border-t border-[#E3DAC7]">
          <span className="text-[11px] font-bold tracking-wide uppercase text-[#64748B]">
            Quick Verification Benchmarks:
          </span>
          <div className="flex flex-wrap gap-2 mt-2.5">
            {presets.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setTitle(preset.title);
                  handleVerify(preset.title);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#E8ECEF] text-[#2D3748] text-xs font-semibold hover:bg-[#DCE1E5] transition-all"
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    preset.type === "green" ? "bg-[#1E7B62]" : "bg-[#C53030]"
                  }`}
                ></span>
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Right Results & Report Panel */}
      <div className="lg:col-span-7 parchment-card p-6 flex flex-col gap-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#E3DAC7] pb-3">
          <div className="flex items-center gap-2 font-bold text-base text-[#1A202C]">
            <Gauge className="w-5 h-5 text-[#1E7B62]" />
            <span>Verification Report & Probability</span>
          </div>
          <span className="text-xs font-semibold px-3 py-1 bg-[#D5EDE3] text-[#166552] rounded-full">
            Latency {result?.execution_time_ms || 200} ms
          </span>
        </div>

        {/* Gauge & Verdict Banner */}
        <div className="flex flex-col items-center justify-center text-center gap-3 py-2">
          {/* Semi-circular Speedometer SVG Gauge */}
          <div className="relative w-56 h-32 flex flex-col items-center justify-center">
            <svg className="w-56 h-28" viewBox="0 0 200 110">
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke="#1A365D"
                strokeWidth="16"
                strokeLinecap="round"
              />
              {result && (
                <path
                  d="M 20 100 A 80 80 0 0 1 180 100"
                  fill="none"
                  stroke={prob >= 70 ? "#1E7B62" : prob >= 40 ? "#D69E2E" : "#C53030"}
                  strokeWidth="16"
                  strokeDasharray="251.2"
                  strokeDashoffset={251.2 - (251.2 * prob) / 100}
                  strokeLinecap="round"
                  className="transition-all duration-700 ease-out"
                />
              )}
            </svg>
            <div className="absolute bottom-1 flex flex-col items-center">
              <span className="text-3xl font-extrabold tracking-tight text-[#1A202C]">
                {result ? `${prob}%` : "--%"}
              </span>
              <span className="text-[10px] font-bold tracking-widest text-[#64748B] uppercase">
                Probability
              </span>
            </div>
          </div>

          {/* Verdict Pill */}
          <div className="mt-1">
            {result ? (
              <span className={isRejected ? "badge-crimson" : prob >= 70 ? "badge-approved" : "badge-review"}>
                {result.decision || (isRejected ? "REJECTED / GUIDELINE CONFLICT" : "APPROVED")}
              </span>
            ) : (
              <span className="px-3.5 py-1 bg-[#EAE4D6] text-[#4A5568] text-xs font-bold rounded-full">
                Ready to Verify
              </span>
            )}
          </div>

          <h3 className="text-lg font-extrabold text-[#1A202C]">
            {result ? result.raw_title : "Enter a title to begin verification"}
          </h3>
          <p className="text-xs text-[#64748B] max-w-lg leading-relaxed">
            {result?.reasons?.[0]?.explanation ||
              "The multi-stage pipeline tests anchor distinctiveness, PRGI guideline blacklists, Frankentitle combinations, and tri-vector similarity."}
          </p>
        </div>

        {/* 5-Stage Funnel Status Visualizer */}
        <div className="flex flex-col gap-2.5 border-t border-[#E3DAC7] pt-4">
          {/* Stage 1 */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-white/70 border border-[#E3DAC7] text-xs">
            <span className="font-semibold text-[#1A202C]">Stage 1: Pre-processing & Anchor Word</span>
            {renderStatusBadge(stage1Info)}
          </div>

          {/* Stage 2 */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-white/70 border border-[#E3DAC7] text-xs">
            <span className="font-semibold text-[#1A202C]">Stage 2: Guideline Enforcement (Blacklists)</span>
            {renderStatusBadge(stage2Info)}
          </div>

          {/* Stage 3 */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-white/70 border border-[#E3DAC7] text-xs">
            <span className="font-semibold text-[#1A202C]">Stage 3: 'Frankentitle' Combination Check</span>
            {renderStatusBadge(stage3Info)}
          </div>

          {/* Stage 4 */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-white/70 border border-[#E3DAC7] text-xs">
            <span className="font-semibold text-[#1A202C]">Stage 4: Tri-Vector Similarity Core</span>
            {renderStatusBadge(stage4Info)}
          </div>
        </div>

        {/* Vector Scores Breakdown */}
        {vectorScores && (
          <div className="p-4 rounded-xl bg-white/80 border border-[#E3DAC7] flex flex-col gap-3">
            <div className="text-xs font-bold text-[#1A202C] flex items-center gap-1.5">
              <span>Stage 4 Tri-Vector Similarity Breakdown</span>
            </div>

            <div className="flex flex-col gap-2 text-xs">
              <div>
                <div className="flex justify-between font-semibold text-[#4A5568] mb-1">
                  <span className="flex items-center gap-1"><Volume2 className="w-3.5 h-3.5 text-[#1E7B62]" /> 4A: Phonetic (Double Metaphone + Indic)</span>
                  <span className="font-bold text-[#1A202C]">{vectorScores.phonetic || 0}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-[#EAE4D6] overflow-hidden">
                  <div className="h-full bg-[#1E7B62] rounded-full transition-all duration-500" style={{ width: `${vectorScores.phonetic || 0}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between font-semibold text-[#4A5568] mb-1">
                  <span className="flex items-center gap-1"><SpellCheck className="w-3.5 h-3.5 text-[#1E7B62]" /> 4B: Orthographic (Levenshtein / Jaro-Winkler)</span>
                  <span className="font-bold text-[#1A202C]">{vectorScores.orthographic || 0}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-[#EAE4D6] overflow-hidden">
                  <div className="h-full bg-[#1E7B62] rounded-full transition-all duration-500" style={{ width: `${vectorScores.orthographic || 0}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between font-semibold text-[#4A5568] mb-1">
                  <span className="flex items-center gap-1"><Globe className="w-3.5 h-3.5 text-[#1E7B62]" /> 4C: Cross-Lingual Semantic (Embeddings)</span>
                  <span className="font-bold text-[#1A202C]">{vectorScores.semantic || 0}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-[#EAE4D6] overflow-hidden">
                  <div className="h-full bg-[#1E7B62] rounded-full transition-all duration-500" style={{ width: `${vectorScores.semantic || 0}%` }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Collapsible Diagnostic Findings */}
        {result && result.reasons && result.reasons.length > 0 && (
          <div className="border border-[#E3DAC7] rounded-xl bg-white/80 overflow-hidden">
            <button
              onClick={() => setDiagnosticsOpen(!diagnosticsOpen)}
              className="w-full flex items-center justify-between p-3.5 text-xs font-bold text-[#1A202C] bg-[#F7F2E8] hover:bg-[#EAE4D6] transition-all"
            >
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-[#1E7B62]" />
                <span>Diagnostic Findings & Guidelines</span>
              </div>
              {diagnosticsOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {diagnosticsOpen && (
              <div className="p-4 text-xs text-[#4A5568] flex flex-col gap-2 border-t border-[#E3DAC7]">
                {result.reasons.map((reason, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-[#F4F2E9] border border-[#E3DAC7]">
                    <div className="font-bold text-[#C53030]">{reason.rule}</div>
                    <div className="text-[11px] text-[#64748B] mt-0.5">{reason.explanation}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Top Matches Table */}
        {topMatches.length > 0 && (
          <div className="border border-[#E3DAC7] rounded-xl bg-white/80 overflow-hidden p-4 flex flex-col gap-3">
            <div className="text-xs font-bold text-[#1A202C] flex items-center gap-1.5">
              <Copy className="w-4 h-4 text-[#1E7B62]" />
              <span>Top Matching Registered Titles in Database</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#F7F2E8] border-b border-[#E3DAC7] text-[#4A5568] font-bold">
                  <tr>
                    <th className="p-2">Registered Title</th>
                    <th className="p-2">Similarity</th>
                    <th className="p-2">Phonetic</th>
                    <th className="p-2">Orthographic</th>
                    <th className="p-2">Semantic</th>
                    <th className="p-2">Reg. No / State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E3DAC7]">
                  {topMatches.map((match, i) => {
                    const simVal = match.highest_similarity ?? match.similarity_score ?? 0;
                    const phVal = match.phonetic_similarity ?? match.phonetic_score ?? 0;
                    const orthoVal = match.orthographic_similarity ?? match.orthographic_score ?? 0;
                    const semVal = match.semantic_similarity ?? match.semantic_score ?? 0;

                    const simPct = Math.round(simVal <= 1 ? simVal * 100 : simVal);
                    const phPct = Math.round(phVal <= 1 ? phVal * 100 : phVal);
                    const orthoPct = Math.round(orthoVal <= 1 ? orthoVal * 100 : orthoVal);
                    const semPct = Math.round(semVal <= 1 ? semVal * 100 : semVal);

                    const regInfo = [match.registration_no || match.reg_no, match.state].filter(Boolean).join(" • ") || "National";

                    return (
                      <tr key={i} className="hover:bg-[#F4F2E9]">
                        <td className="p-2 font-bold text-[#1A202C]">{match.title}</td>
                        <td className="p-2 font-extrabold text-[#C53030]">{simPct}%</td>
                        <td className="p-2 font-semibold text-[#4A5568]">{phPct}%</td>
                        <td className="p-2 font-semibold text-[#4A5568]">{orthoPct}%</td>
                        <td className="p-2 font-semibold text-[#4A5568]">{semPct}%</td>
                        <td className="p-2 text-[#64748B]">{regInfo}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Actionable Recommendations */}
        {suggestions.length > 0 && (
          <div className="p-4 rounded-xl bg-white/80 border border-[#E3DAC7] flex flex-col gap-2 text-xs">
            <div className="font-bold text-[#1A202C] flex items-center gap-1.5">
              <Lightbulb className="w-4 h-4 text-[#1E7B62]" />
              <span>PRGI Actionable Recommendations</span>
            </div>
            <ul className="list-disc list-inside text-[#4A5568] flex flex-col gap-1 text-[11px] leading-relaxed">
              {suggestions.map((sug, i) => (
                <li key={i}>{sug}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
