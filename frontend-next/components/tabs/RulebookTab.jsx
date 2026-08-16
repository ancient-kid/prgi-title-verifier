"use client";
import { useState, useEffect } from "react";
import { BookOpen } from "lucide-react";

export default function RulebookTab({ isActive }) {
  const [guidelines, setGuidelines] = useState([]);

  useEffect(() => {
    if (!isActive) return;
    fetch("/api/guidelines")
      .then(r => r.json())
      .then(data => setGuidelines(data.guidelines || []))
      .catch(e => console.error("Guidelines load error:", e));
  }, [isActive]);

  return (
    <section id="rules-tab" className="tab-content active">
      <div className="card glass-card">
        <div className="card-header">
          <div className="card-title"><BookOpen size={18} /> PRGI Statutory Guidelines &amp; Prohibited Word Blacklists</div>
          <span className="pill-info">Press and Registration of Periodicals (PRP) Act, 2023</span>
        </div>

        <div className="rules-grid" id="rules-cards-container">
          {guidelines.map((g, i) => (
            <div key={i} className="rule-card">
              <span className="rule-badge">{g.guideline_ref}</span>
              <div className="rule-title">{g.title}</div>
              <div className="rule-desc">{g.description}</div>
              <div className="rule-examples">
                {g.examples?.map((ex, j) => <span key={j} className="ex-tag">{ex}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
