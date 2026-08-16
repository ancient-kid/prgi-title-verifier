"use client";
import { useState, useEffect, useCallback } from "react";
import { Lock, Clock, UserCheck, UserX, ArrowRight, RefreshCw, Send, AlertOctagon } from "lucide-react";

export default function LockSimulator() {
  const [titleA, setTitleA] = useState("Sunrise Orbit Chronicle");
  const [titleB, setTitleB] = useState("Sunrise Orbit Chronicle");
  const [resA, setResA] = useState({ text: "Awaiting submission...", cls: "" });
  const [resB, setResB] = useState({ text: "Awaiting User B attempt...", cls: "" });
  const [loadingA, setLoadingA] = useState(false);
  const [loadingB, setLoadingB] = useState(false);
  const [locks, setLocks] = useState([]);

  const loadActiveLocks = useCallback(async () => {
    try {
      const res = await fetch("/api/locks");
      if (!res.ok) return; // backend down or proxy error — fail silently
      const data = await res.json();
      setLocks(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Lock load error:", e);
    }
  }, []);

  useEffect(() => { loadActiveLocks(); }, [loadActiveLocks]);

  async function handleRelease(title, applicant_id) {
    await fetch(`/api/locks/release?title=${encodeURIComponent(title)}&applicant_id=${encodeURIComponent(applicant_id)}`, { method: "POST" });
    loadActiveLocks();
  }

  async function userAApply() {
    const t = titleA.trim();
    if (!t) return;
    setLoadingA(true);
    setResA({ text: "Submitting User A application...", cls: "" });
    try {
      const res = await fetch("/api/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: t, applicant_id: "USER_A_ALPHA", applicant_name: "Applicant Alpha", ttl_seconds: 600 }),
      });
      const data = await res.json();
      if (data.success) {
        setResA({ cls: "success", text: `LOCK ACQUIRED (200 OK)\nApplication No: ${data.application_no}\nTitle is now locked for 600s in Redis.` });
      } else {
        setResA({ cls: "error", text: `REJECTED\n${data.message}` });
      }
      loadActiveLocks();
    } catch {
      setResA({ cls: "error", text: "Simulation network error." });
    } finally {
      setLoadingA(false);
    }
  }

  async function userBAttempt() {
    const t = titleB.trim();
    if (!t) return;
    setLoadingB(true);
    setResB({ text: "User B attempting verification 5 mins later...", cls: "" });
    try {
      const res = await fetch("/api/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: t, applicant_id: "USER_B_BETA" }),
      });
      const data = await res.json();
      if (data.status === "Rejected" && data.decision === "REJECTED_PENDING_COLLISION") {
        setResB({ cls: "error", text: `COLLISION DETECTED (0% Probability)\n${data.reasons[0].explanation}` });
      } else if (data.status === "Approved") {
        setResB({ cls: "success", text: `No Collision: Title verification probability is ${data.verification_probability}%.` });
      } else {
        setResB({ cls: "error", text: `Rejected: ${data.reasons[0].explanation}` });
      }
    } catch {
      setResB({ cls: "error", text: "Simulation network error." });
    } finally {
      setLoadingB(false);
    }
  }

  return (
    <section id="lock-tab" className="tab-content active">
      <div className="lock-grid">
        {/* Lock Simulator Card */}
        <div className="card glass-card">
          <div className="card-header">
            <div className="card-title"><Lock size={18} /> Concurrency Lock Collision Simulator</div>
            <span className="pill-info">Redis TTL Architecture Demo</span>
          </div>
          <p className="section-desc">
            Demonstrates how PRGI prevents race conditions. When User A files for a title, it is locked in Redis with a 10-minute TTL. If User B attempts to apply 5 minutes later, User B is immediately rejected.
          </p>

          <div className="sim-flow-box">
            {/* User A */}
            <div className="sim-actor">
              <div className="actor-header"><UserCheck size={16} /> User A (First Applicant)</div>
              <div className="input-group">
                <input type="text" id="sim-title-a" value={titleA} onChange={e => setTitleA(e.target.value)} placeholder="Title for User A" />
              </div>
              <button id="sim-user-a-btn" className="btn btn-success" disabled={loadingA} onClick={userAApply}>
                <Send size={15} /> User A Applies (Acquire Lock)
              </button>
              <div id="sim-res-a" className={`sim-result-box${resA.cls ? ` ${resA.cls}` : ""}`}
                style={{ whiteSpace: "pre-line" }}>{resA.text}</div>
            </div>

            {/* Divider */}
            <div className="sim-divider">
              <ArrowRight size={16} /><span>5 Mins Later</span>
            </div>

            {/* User B */}
            <div className="sim-actor">
              <div className="actor-header"><UserX size={16} /> User B (Second Applicant)</div>
              <div className="input-group">
                <input type="text" id="sim-title-b" value={titleB} onChange={e => setTitleB(e.target.value)} placeholder="Title for User B" />
              </div>
              <button id="sim-user-b-btn" className="btn btn-danger" disabled={loadingB} onClick={userBAttempt}>
                <AlertOctagon size={15} /> User B Attempts Application
              </button>
              <div id="sim-res-b" className={`sim-result-box${resB.cls ? ` ${resB.cls}` : ""}`}
                style={{ whiteSpace: "pre-line" }}>{resB.text}</div>
            </div>
          </div>
        </div>

        {/* Active Locks Card */}
        <div className="card glass-card">
          <div className="card-header">
            <div className="card-title"><Clock size={18} /> Active Pending Application Locks in Redis Cache</div>
            <button id="refresh-locks-btn" className="btn btn-sm btn-secondary" onClick={loadActiveLocks}>
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
          <div className="table-wrapper">
            <table className="custom-table" id="locks-table">
              <thead>
                <tr>
                  <th>Locked Title</th>
                  <th>Applicant ID</th>
                  <th>Applicant Name</th>
                  <th>TTL Remaining</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody id="locks-tbody">
                {locks.length === 0 ? (
                  <tr><td colSpan={5} className="text-center text-muted">No active locks in cache.</td></tr>
                ) : locks.map((lock, i) => (
                  <tr key={i}>
                    <td><strong>{lock.title}</strong></td>
                    <td><code>{lock.applicant_id}</code></td>
                    <td>{lock.applicant_name}</td>
                    <td><span className="sim-badge med">{lock.ttl_remaining}s</span></td>
                    <td>
                      <button
                        className="btn btn-sm btn-secondary release-lock-btn"
                        data-title={lock.title}
                        data-applicant={lock.applicant_id}
                        onClick={() => handleRelease(lock.title, lock.applicant_id)}
                      >
                        Release
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}
