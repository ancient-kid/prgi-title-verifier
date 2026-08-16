"use client";
import { useState } from "react";
import { Layers, Play, FilePlus, Download } from "lucide-react";

const SAMPLE = [
  "The Crime Investigation Daily",
  "The Daily Mumbai Express",
  "The Daily News",
  "Hindu Indian Express",
  "Namascar India",
  "Daily Evening",
  "Daineq Bhaskar",
  "The Tymes of India",
  "Morning News",
  "Astra Quantum Aerospace Journal",
  "Himachal Alpine Flora Gazette",
].join("\n");

export default function BatchScreening() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({ total: 0, approved: 0, rejected: 0, review: 0 });
  const [rows, setRows] = useState([]);
  const [cache, setCache] = useState([]);
  const exportEnabled = cache.length > 0;

  async function runBatch() {
    const lines = text.split("\n").map(l => l.trim()).filter(l => l.length > 0);
    if (!lines.length) { alert("Please enter one or more titles in the textarea."); return; }
    setLoading(true);
    try {
      const res = await fetch("/api/batch-verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ titles: lines }),
      });
      const data = await res.json();
      setCache(data.results);
      setStats({ total: data.total_processed, approved: data.approved_count, rejected: data.rejected_count, review: data.review_needed_count });
      setRows(data.results);
    } catch (e) {
      console.error(e);
      alert("Batch processing failed.");
    } finally {
      setLoading(false);
    }
  }

  function exportCSV() {
    if (!cache.length) return;
    let csv = "Index,Title,Verification Probability,Status,Decision,Execution Time (ms),Primary Reason\n";
    cache.forEach((r, i) => {
      const reason = r.reasons?.length > 0 ? r.reasons[0].explanation.replace(/"/g, '""') : "";
      csv += `${i + 1},"${r.raw_title}",${r.verification_probability}%,${r.status},${r.decision},${r.execution_time_ms},"${reason}"\n`;
    });
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `prgi_title_verification_report_${Date.now()}.csv`;
    a.click();
  }

  return (
    <section id="batch-tab" className="tab-content active">
      <div className="card glass-card">
        <div className="card-header">
          <div className="card-title"><Layers size={18} /> High-Throughput Batch Title Verification</div>
          <span className="pill-info">Screen Hundreds of Titles Simultaneously</span>
        </div>

        <div className="batch-grid">
          <div className="batch-input-col">
            <label htmlFor="batch-textarea">Enter Titles (One title per line):</label>
            <textarea
              id="batch-textarea"
              rows={8}
              placeholder={"The Crime Investigation Daily\nThe Daily Mumbai Express\nThe Daily News\nHindu Indian Express\nNamascar India\nDaily Evening\nAstra Quantum Aerospace Journal"}
              value={text}
              onChange={e => setText(e.target.value)}
            />
            <div className="batch-actions">
              <button id="batch-run-btn" className="btn btn-primary" disabled={loading} onClick={runBatch}>
                {loading ? <><span className="animate-spin" style={{ display:"inline-block" }}>⟳</span> Screening...</> : <><Play size={15} /> Run Batch Screen</>}
              </button>
              <button id="batch-sample-btn" className="btn btn-secondary" onClick={() => setText(SAMPLE)}>
                <FilePlus size={15} /> Load Benchmark Sample
              </button>
              <button id="batch-export-btn" className="btn btn-secondary" disabled={!exportEnabled} onClick={exportCSV}>
                <Download size={15} /> Export CSV Report
              </button>
            </div>
          </div>

          <div className="batch-stats-col">
            <div className="stat-card">
              <div className="stat-num" id="stat-total">{stats.total}</div>
              <div className="stat-label">Total Processed</div>
            </div>
            <div className="stat-card approved">
              <div className="stat-num" id="stat-approved">{stats.approved}</div>
              <div className="stat-label">Approved (&ge;70%)</div>
            </div>
            <div className="stat-card rejected">
              <div className="stat-num" id="stat-rejected">{stats.rejected}</div>
              <div className="stat-label">Rejected (&lt;40%)</div>
            </div>
            <div className="stat-card review">
              <div className="stat-num" id="stat-review">{stats.review}</div>
              <div className="stat-label">Review Needed</div>
            </div>
          </div>
        </div>

        <div className="table-wrapper batch-table-wrap">
          <table className="custom-table" id="batch-results-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Submitted Title</th>
                <th>Probability</th>
                <th>Status</th>
                <th>Triggered Stage / Rule</th>
                <th>Primary Reason</th>
              </tr>
            </thead>
            <tbody id="batch-results-tbody">
              {rows.length === 0 ? (
                <tr><td colSpan={6} className="text-center text-muted">No batch data loaded. Click &apos;Run Batch Screen&apos; to analyze.</td></tr>
              ) : rows.map((r, idx) => {
                const statusClass = r.status === "Approved" ? "approved" : r.status === "Rejected" ? "rejected" : "review";
                const triggerStage = r.reasons?.length > 0 ? r.reasons[0].stage : "Stage 4";
                const mainReason   = r.reasons?.length > 0 ? r.reasons[0].explanation : "Distinctive title";
                return (
                  <tr key={idx}>
                    <td>{idx + 1}</td>
                    <td><strong>{r.raw_title}</strong></td>
                    <td><span className={`sim-badge ${r.verification_probability >= 70 ? "low" : "high"}`}>{r.verification_probability}%</span></td>
                    <td><span className={`verdict-pill ${statusClass}`}>{r.status}</span></td>
                    <td><span className="text-muted">{triggerStage}</span></td>
                    <td><small>{mainReason}</small></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
