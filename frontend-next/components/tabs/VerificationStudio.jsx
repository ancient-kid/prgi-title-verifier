"use client";
import { useState, useRef, useCallback } from "react";
import {
  FileSearch, Scan, Lock, Type, X, Split, ShieldAlert,
  GitMerge, Activity, Volume2, SpellCheck2, Globe,
  AlertTriangle, Copy, Lightbulb, Gauge, CircleDashed,
  XCircle, CheckCircle2, MinusCircle, AlertCircle,
} from "lucide-react";

const CIRCLE_CIRCUMFERENCE = 339.292;

const PRESETS = [
  { title: "The Crime Investigation Daily", dot: "red",   tooltip: "Guideline 12 Disallowed Words",          label: "Crime Investigation Daily" },
  { title: "The Daily Mumbai Express",      dot: "green",  tooltip: "Anchor Extraction",                      label: "The Daily Mumbai Express" },
  { title: "The Daily News",                dot: "red",   tooltip: "Pure Generic Violation",                  label: "The Daily News" },
  { title: "Hindu Indian Express",          dot: "red",   tooltip: "Frankentitle Mashup",                     label: "Hindu Indian Express" },
  { title: "Namascar India",               dot: "red",   tooltip: "Phonetic Homophone",                      label: "Namascar India" },
  { title: "Daily Evening",                dot: "red",   tooltip: "Cross-Lingual Equivalent to Pratidin Sandhya", label: "Daily Evening" },
  { title: "Astra Quantum Aerospace Journal", dot: "green", tooltip: "Eligible Unique Title",                label: "Astra Quantum Aerospace" },
];

function getStepIcon(state) {
  if (state === "passed")  return <CheckCircle2 size={16} />;
  if (state === "failed")  return <XCircle size={16} />;
  if (state === "skipped") return <MinusCircle size={16} />;
  if (state === "warn")    return <AlertCircle size={16} />;
  return <CircleDashed size={16} />;
}

const initialStep = { state: "idle", sub: "" };

export default function VerificationStudio() {
  const [title, setTitle] = useState("");
  const [language, setLanguage] = useState("English");
  const [periodicity, setPeriodicity] = useState("Daily");
  const [state, setState] = useState("National");

  // Gauge
  const [prob, setProb] = useState(null);
  const [gaugeColor, setGaugeColor] = useState("#64748B");
  const [verdictClass, setVerdictClass] = useState("neutral");
  const [verdictLabel, setVerdictLabel] = useState("Ready to Verify");
  const [verdictTitle, setVerdictTitle] = useState("Enter a title to begin verification");
  const [verdictDesc, setVerdictDesc] = useState("The multi-stage pipeline tests anchor distinctiveness, PRGI guideline blacklists, Frankentitle combinations, and tri-vector similarity.");
  const [latency, setLatency] = useState("Latency: 0 ms");

  // Steps
  const [step1, setStep1] = useState({ state: "idle", sub: "Extracts anchor and strips generic modifiers" });
  const [step2, setStep2] = useState({ state: "idle", sub: "Disallowed words, Emblems Act, Police/CBI terms" });
  const [step3, setStep3] = useState({ state: "idle", sub: "Aho-Corasick compound title detection" });
  const [step4, setStep4] = useState({ state: "idle", sub: "Phonetic, Orthographic & Cross-Lingual Semantic" });

  // Results
  const [vectorScores, setVectorScores] = useState(null);
  const [reasons, setReasons] = useState([]);
  const [matches, setMatches] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [applyEnabled, setApplyEnabled] = useState(false);
  const [loading, setLoading] = useState(false);

  function resetUI() {
    setProb(null);
    setGaugeColor("#64748B");
    setVerdictClass("neutral");
    setVerdictLabel("Ready to Verify");
    setVerdictTitle("Enter a title to begin verification");
    setVerdictDesc("The multi-stage pipeline tests anchor distinctiveness, PRGI guideline blacklists, Frankentitle combinations, and tri-vector similarity.");
    setLatency("Latency: 0 ms");
    setStep1({ state: "idle", sub: "Extracts anchor and strips generic modifiers" });
    setStep2({ state: "idle", sub: "Disallowed words, Emblems Act, Police/CBI terms" });
    setStep3({ state: "idle", sub: "Aho-Corasick compound title detection" });
    setStep4({ state: "idle", sub: "Phonetic, Orthographic & Cross-Lingual Semantic" });
    setVectorScores(null);
    setReasons([]);
    setMatches([]);
    setSuggestions([]);
    setApplyEnabled(false);
  }

  function gaugeOffset(pct) {
    return CIRCLE_CIRCUMFERENCE - (pct / 100) * CIRCLE_CIRCUMFERENCE;
  }

  async function runVerification(overrideTitle) {
    const t = (overrideTitle ?? title).trim();
    if (!t) { alert("Please enter a title to verify."); return; }

    setLoading(true);
    resetUI();
    try {
      const res = await fetch("/api/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: t, language, state, periodicity, applicant_id: "USER_WEB_ACTIVE" }),
      });
      if (!res.ok) throw new Error(`Server ${res.status}`);
      const data = await res.json();
      renderResults(data);
    } catch (err) {
      console.error(err);
      alert("Failed to complete verification. Please verify backend service status.");
    } finally {
      setLoading(false);
    }
  }

  function renderResults(data) {
    const p = data.verification_probability;
    const s = data.status;

    // Gauge colour
    let color = "#64748B";
    if (s === "Approved")      color = "#10B981";
    else if (s === "Rejected") color = "#EF4444";
    else if (s === "Review Needed") color = "#F59E0B";
    setProb(p);
    setGaugeColor(color);
    setLatency(`Latency: ${data.execution_time_ms} ms`);
    setVerdictTitle(`"${data.raw_title}"`);

    if (s === "Approved") {
      setVerdictClass("approved"); setVerdictLabel("Approved / High Distinctiveness");
      setVerdictDesc("Title passed all guideline, phonetic, orthographic, and cross-lingual checks. No conflicting registration found.");
      setApplyEnabled(true);
    } else if (s === "Rejected") {
      setVerdictClass("rejected"); setVerdictLabel("Rejected / Guideline Conflict");
      setVerdictDesc(data.reasons?.length > 0 ? data.reasons[0].explanation : "High similarity with registered titles.");
      setApplyEnabled(false);
    } else {
      setVerdictClass("review"); setVerdictLabel("Officer Review Needed");
      setVerdictDesc("Moderate similarity detected. Further manual verification by PRGI officer is recommended.");
      setApplyEnabled(true);
    }

    // Stages
    const s1 = data.stage_results?.stage1;
    const s2 = data.stage_results?.stage2;
    const s3 = data.stage_results?.stage3;
    const s4 = data.stage_results?.stage4;

    if (s1) {
      if (s1.is_purely_generic) setStep1({ state: "failed", sub: "Failed: Purely generic modifiers without distinctive anchor word." });
      else setStep1({ state: "passed", sub: `Extracted Anchor: "${s1.anchor_words}" (Stripped: ${[...s1.stripped_prefixes, ...s1.stripped_suffixes].join(", ") || "None"})` });
    }
    if (s2) {
      if (!s2.passed) setStep2({ state: "failed", sub: `Failed: Violated PRGI blacklist (${s2.violations.map(v => v.term).join(", ")})` });
      else setStep2({ state: "passed", sub: "Passed: No prohibited security or law-enforcement terms detected." });
    } else setStep2({ state: "skipped", sub: "Skipped due to prior stage rejection." });

    if (s3) {
      if (s3.is_frankentitle) setStep3({ state: "failed", sub: `Failed: Compound title formed from '${s3.components.join("' + '")}'` });
      else setStep3({ state: "passed", sub: "Passed: Not a combination of existing registered titles." });
    } else setStep3({ state: "skipped", sub: "Skipped due to prior stage rejection." });

    if (s4) {
      const highest = data.highest_similarity_score || 0;
      if (highest >= 70)      setStep4({ state: "failed", sub: `Failed: High similarity score (${highest}%) against existing database titles.` });
      else if (highest >= 40) setStep4({ state: "warn",   sub: `Review: Moderate similarity (${highest}%).` });
      else                    setStep4({ state: "passed", sub: `Passed: Distinctive title (Highest similarity: ${highest}%).` });

      if (data.max_scores) setVectorScores(data.max_scores);
    } else {
      setStep4({ state: "skipped", sub: "Skipped due to prior stage rejection." });
      setVectorScores(null);
    }

    setReasons(data.reasons || []);
    setMatches(data.top_matches || []);
    setSuggestions(data.suggestions || []);
  }

  async function handleApply() {
    const t = title.trim();
    if (!t) return;
    const applicantName = prompt("Enter Applicant / Publishing Company Name:", "Times Group Media");
    if (!applicantName) return;
    setApplyEnabled(false);
    try {
      const res = await fetch("/api/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: t, applicant_id: `APP_${Math.floor(1000 + Math.random() * 9000)}`,
          applicant_name: applicantName, language, state, periodicity, ttl_seconds: 600,
        }),
      });
      const data = await res.json();
      if (data.success) alert(`Application Success!\nApplication No: ${data.application_no}\n${data.message}`);
      else alert(`Application Error:\n${data.message}`);
    } catch { alert("Failed to submit application."); }
    finally { setApplyEnabled(true); }
  }

  const probPct = prob ?? 0;
  const offset  = gaugeOffset(probPct);

  return (
    <section id="studio-tab" className="tab-content active">
      <div className="studio-grid">

        {/* Left: Input Panel */}
        <div className="card glass-card input-panel">
          <div className="card-header">
            <div className="card-title"><FileSearch size={18} /> Title Application Verification</div>
            <span className="pill-info">Real-time Multi-Stage Funnel</span>
          </div>

          <div className="input-group">
            <label htmlFor="title-input">Proposed Periodical / Newspaper Title</label>
            <div className="input-wrapper">
              <Type className="input-icon" size={18} />
              <input
                type="text"
                id="title-input"
                placeholder="e.g. The Daily Mumbai Express, Namascar India..."
                autoComplete="off"
                value={title}
                onChange={e => setTitle(e.target.value)}
                onKeyDown={e => e.key === "Enter" && runVerification()}
              />
              <button id="clear-btn" className="icon-btn" title="Clear input" onClick={() => { setTitle(""); resetUI(); }}>
                <X size={16} />
              </button>
            </div>
          </div>

          <div className="form-row">
            <div className="input-group">
              <label htmlFor="language-select">Target Language</label>
              <select id="language-select" value={language} onChange={e => setLanguage(e.target.value)}>
                <option value="English">English</option>
                <option value="Hindi">Hindi (हिंदी)</option>
                <option value="Bengali">Bengali (বাংলা)</option>
                <option value="Marathi">Marathi (मराठी)</option>
                <option value="Tamil">Tamil (தமிழ்)</option>
                <option value="Telugu">Telugu (తెలుగు)</option>
                <option value="Gujarati">Gujarati (ગુજરાતી)</option>
                <option value="Kannada">Kannada (ಕನ್ನಡ)</option>
                <option value="Malayalam">Malayalam (മലയാളം)</option>
                <option value="Punjabi">Punjabi (ਪੰਜਾਬੀ)</option>
                <option value="Urdu">Urdu (اردو)</option>
                <option value="Odia">Odia (ଓଡ଼ିଆ)</option>
              </select>
            </div>
            <div className="input-group">
              <label htmlFor="periodicity-select">Periodicity</label>
              <select id="periodicity-select" value={periodicity} onChange={e => setPeriodicity(e.target.value)}>
                <option value="Daily">Daily</option>
                <option value="Weekly">Weekly</option>
                <option value="Fortnightly">Fortnightly</option>
                <option value="Monthly">Monthly</option>
                <option value="Quarterly">Quarterly</option>
              </select>
            </div>
            <div className="input-group">
              <label htmlFor="state-select">State / UT</label>
              <select id="state-select" value={state} onChange={e => setState(e.target.value)}>
                <option value="National">National (All India)</option>
                <option value="Delhi">Delhi</option>
                <option value="Maharashtra">Maharashtra</option>
                <option value="Uttar Pradesh">Uttar Pradesh</option>
                <option value="West Bengal">West Bengal</option>
                <option value="Tamil Nadu">Tamil Nadu</option>
                <option value="Karnataka">Karnataka</option>
                <option value="Gujarat">Gujarat</option>
                <option value="Telangana">Telangana</option>
                <option value="Kerala">Kerala</option>
                <option value="Punjab">Punjab</option>
              </select>
            </div>
          </div>

          <div className="action-buttons">
            <button id="verify-btn" className="btn btn-primary" disabled={loading} onClick={() => runVerification()}>
              {loading
                ? <><span className="animate-spin" style={{ display: "inline-block" }}>⟳</span> Processing...</>
                : <><Scan size={16} /> Verify Title Now</>}
            </button>
            <button id="apply-btn" className="btn btn-success" disabled={!applyEnabled} onClick={handleApply}>
              <Lock size={16} /> Submit &amp; Lock Title
            </button>
          </div>

          {/* Presets */}
          <div className="presets-section">
            <div className="presets-label">Quick Verification Benchmarks:</div>
            <div className="preset-chips">
              {PRESETS.map((p, i) => (
                <button
                  key={i}
                  className="chip"
                  data-title={p.title}
                  data-tooltip={p.tooltip}
                  onClick={() => { setTitle(p.title); runVerification(p.title); }}
                >
                  <span className={`chip-dot ${p.dot}`}></span>
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Results Panel */}
        <div className="card glass-card result-panel">
          <div className="card-header">
            <div className="card-title"><Gauge size={18} /> Verification Report &amp; Probability</div>
            <div id="execution-time" className="time-badge">{latency}</div>
          </div>

          {/* Probability Hero */}
          <div className="probability-hero">
            <div className="gauge-wrapper">
              <svg className="progress-ring" width="140" height="140">
                <circle className="progress-ring__circle-bg" stroke="#1E293B" strokeWidth="12" fill="transparent" r="54" cx="70" cy="70" />
                <circle
                  id="prob-circle"
                  className="progress-ring__circle"
                  stroke={gaugeColor}
                  strokeWidth="12"
                  fill="transparent"
                  r="54"
                  cx="70"
                  cy="70"
                  style={{ strokeDashoffset: offset, strokeDasharray: CIRCLE_CIRCUMFERENCE }}
                />
              </svg>
              <div className="gauge-center">
                <span id="prob-percentage" className="prob-num" style={{ color: prob !== null ? gaugeColor : undefined }}>
                  {prob !== null ? `${Math.round(prob)}%` : "--%"}
                </span>
                <span className="prob-label">PROBABILITY</span>
              </div>
            </div>

            <div className="verdict-info">
              <div id="verdict-badge" className={`verdict-pill ${verdictClass}`}>{verdictLabel}</div>
              <div id="verdict-title" className="submitted-title-display">{verdictTitle}</div>
              <div id="verdict-summary" className="verdict-desc">{verdictDesc}</div>
            </div>
          </div>

          {/* 5-Stage Funnel */}
          <div className="funnel-container">
            {[
              { id: "step-1", step: step1, icon: <Split size={15} />,       name: "Stage 1: Pre-processing & Anchor Word" },
              { id: "step-2", step: step2, icon: <ShieldAlert size={15} />, name: "Stage 2: Guideline Enforcement (Blacklists)" },
              { id: "step-3", step: step3, icon: <GitMerge size={15} />,    name: "Stage 3: 'Frankentitle' Combination Check" },
              { id: "step-4", step: step4, icon: <Activity size={15} />,    name: "Stage 4: Tri-Vector Similarity Core" },
            ].map(({ id, step, icon, name }, idx) => (
              <div key={id} id={id} className={`funnel-step${step.state !== "idle" ? ` ${step.state === "warn" ? "passed" : step.state}` : ""}`}>
                <div className="step-icon">{icon}</div>
                <div className="step-details">
                  <div className="step-name">{name}</div>
                  <div className="step-sub" id={`${id}-sub`}>{step.sub}</div>
                </div>
                <div className="step-status" id={`${id}-status`}>{getStepIcon(step.state)}</div>
              </div>
            ))}
          </div>

          {/* Vector Scores */}
          {vectorScores && (
            <div id="vector-scores-card" className="vector-scores-card">
              {[
                { icon: <Volume2 size={14} />,    label: "4A: Phonetic (Double Metaphone + Indic)",          val: vectorScores.phonetic,      id: "phonetic" },
                { icon: <SpellCheck2 size={14} />, label: "4B: Orthographic (Levenshtein / Jaro-Winkler)", val: vectorScores.orthographic,   id: "ortho" },
                { icon: <Globe size={14} />,       label: "4C: Cross-Lingual Semantic (Embeddings & Lexicon)", val: vectorScores.semantic,   id: "semantic" },
              ].map(({ icon, label, val, id }) => (
                <div key={id} className="vector-score-item">
                  <div className="vs-header">
                    <span>{icon} {label}</span>
                    <strong id={`${id}-score-val`}>{val}%</strong>
                  </div>
                  <div className="progress-bar-bg">
                    <div id={`${id}-bar`} className="progress-bar-fill" style={{ width: `${val}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Reasons */}
          {reasons.length > 0 && (
            <div id="reasons-container" className="reasons-container">
              <div className="section-subtitle"><AlertTriangle size={15} /> Diagnostic Findings &amp; Guidelines</div>
              <div id="reasons-list" className="reasons-list">
                {reasons.map((r, i) => (
                  <div key={i} className={`reason-item${verdictClass === "approved" ? " safe" : ""}`}>
                    <div className="reason-rule">{r.stage} &bull; {r.rule} ({r.guideline_ref})</div>
                    <div>{r.explanation}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Matches Table */}
          {matches.length > 0 && (
            <div id="matches-container" className="matches-container">
              <div className="section-subtitle"><Copy size={15} /> Top Matching Registered Titles in Database</div>
              <div className="table-wrapper">
                <table className="custom-table" id="matches-table">
                  <thead>
                    <tr>
                      <th>Registered Title</th>
                      <th>Similarity</th>
                      <th>Phonetic</th>
                      <th>Orthographic</th>
                      <th>Semantic</th>
                      <th>Reg. No / State</th>
                    </tr>
                  </thead>
                  <tbody id="matches-tbody">
                    {matches.map((m, i) => {
                      const simPct = Math.round(m.highest_similarity * 100);
                      const badgeClass = simPct >= 70 ? "high" : simPct >= 40 ? "med" : "low";
                      return (
                        <tr key={i}>
                          <td><strong>{m.title}</strong></td>
                          <td><span className={`sim-badge ${badgeClass}`}>{simPct}%</span></td>
                          <td>{Math.round(m.phonetic_similarity * 100)}%</td>
                          <td>{Math.round(m.orthographic_similarity * 100)}%</td>
                          <td>{Math.round(m.semantic_similarity * 100)}%</td>
                          <td><span className="text-muted">{m.registration_no} &bull; {m.state}</span></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div id="suggestions-container" className="suggestions-container">
              <div className="section-subtitle"><Lightbulb size={15} /> PRGI Actionable Recommendations</div>
              <ul id="suggestions-list" className="suggestions-list">
                {suggestions.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
