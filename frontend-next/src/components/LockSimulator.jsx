"use client";

import React, { useState, useEffect } from "react";
import { Lock, UserCheck, UserX, ArrowRight, AlertOctagon, RefreshCw, Send, Trash2 } from "lucide-react";

export default function LockSimulator() {
  const [titleA, setTitleA] = useState("Sunrise Orbit Chronicle");
  const [titleB, setTitleB] = useState("Sunrise Orbit Chronicle");
  const [resA, setResA] = useState("Awaiting submission...");
  const [resB, setResB] = useState("Awaiting User B attempt...");

  const [locks, setLocks] = useState([]);
  const [loadingLocks, setLoadingLocks] = useState(false);

  const fetchLocks = async () => {
    setLoadingLocks(true);
    try {
      const res = await fetch("/api/locks");
      if (res.ok) {
        const data = await res.json();
        setLocks(Array.isArray(data) ? data : data.active_locks || []);
      }
    } catch (err) {
      console.error("Fetch locks error:", err);
    } finally {
      setLoadingLocks(false);
    }
  };

  useEffect(() => {
    fetchLocks();
  }, []);

  const handleUserAApply = async () => {
    setResA("Submitting Application...");
    try {
      const res = await fetch("/api/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: titleA,
          applicant_id: "User_A_9918",
          applicant_name: "User A (Simulated Publisher)",
          ttl_seconds: 600
        })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setResA(`Lock Acquired! Application ID: ${data.application_no}. Pending title lock active in Redis.`);
        fetchLocks();
      } else {
        setResA(`Lock Failed: ${data.message || "Error acquiring lock"}`);
      }
    } catch (err) {
      setResA(`Error: ${err.message}`);
    }
  };

  const handleUserBAttempt = async () => {
    setResB("Verifying Title for User B...");
    try {
      const res = await fetch("/api/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: titleB,
          applicant_id: "User_B_7721"
        })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === "Rejected" && data.decision === "REJECTED_PENDING_COLLISION") {
          setResB(`Conflict Blocked! ${data.reasons?.[0]?.explanation || "Title is locked under an active pending application."}`);
        } else {
          setResB(`Verification Result: ${data.status} (Probability: ${data.verification_probability}%)`);
        }
      } else {
        setResB("Error running verification check.");
      }
    } catch (err) {
      setResB(`Error: ${err.message}`);
    }
  };

  const handleReleaseLock = async (lockTitle, applicantId) => {
    try {
      const res = await fetch(`/api/locks/release?title=${encodeURIComponent(lockTitle)}&applicant_id=${encodeURIComponent(applicantId || "")}`, {
        method: "POST"
      });
      if (res.ok) {
        fetchLocks();
      }
    } catch (err) {
      console.error("Release lock error:", err);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Simulator Flow Panel */}
      <div className="lg:col-span-6 parchment-card p-6 flex flex-col gap-5">
        <div className="flex items-center justify-between border-b border-[#E3DAC7] pb-3">
          <div className="flex items-center gap-2 font-bold text-base text-[#1A202C]">
            <Lock className="w-5 h-5 text-[#1E7B62]" />
            <span>Concurrency Lock Collision Simulator</span>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-[#EAE4D6] text-[#4A5568] rounded-full">
            Redis TTL Architecture
          </span>
        </div>

        <p className="text-xs text-[#64748B] leading-relaxed">
          Demonstrates how PRGI prevents race conditions. When User A files for a title, it is locked in Redis with a 10-minute TTL. If User B attempts to apply 5 minutes later, User B is immediately rejected.
        </p>

        {/* User A Section */}
        <div className="p-4 rounded-xl bg-white/70 border border-[#E3DAC7] flex flex-col gap-3">
          <div className="flex items-center gap-2 font-bold text-xs text-[#166552]">
            <UserCheck className="w-4 h-4" />
            <span>User A (First Applicant)</span>
          </div>
          <input
            type="text"
            value={titleA}
            onChange={(e) => setTitleA(e.target.value)}
            className="input-field text-xs font-medium"
            placeholder="Title for User A"
          />
          <button onClick={handleUserAApply} className="btn-emerald text-xs flex items-center justify-center gap-2">
            <Send className="w-3.5 h-3.5" />
            <span>User A Applies (Acquire Lock)</span>
          </button>
          <div className="text-[11px] p-2.5 rounded-lg bg-[#F4F2E9] text-[#2D3748] font-mono border border-[#E3DAC7]">
            {resA}
          </div>
        </div>

        {/* Divider */}
        <div className="flex items-center justify-center gap-2 text-xs font-bold text-[#64748B] my-1">
          <ArrowRight className="w-4 h-4 text-[#1E7B62]" />
          <span>5 Minutes Later</span>
        </div>

        {/* User B Section */}
        <div className="p-4 rounded-xl bg-white/70 border border-[#E3DAC7] flex flex-col gap-3">
          <div className="flex items-center gap-2 font-bold text-xs text-[#C53030]">
            <UserX className="w-4 h-4" />
            <span>User B (Second Applicant)</span>
          </div>
          <input
            type="text"
            value={titleB}
            onChange={(e) => setTitleB(e.target.value)}
            className="input-field text-xs font-medium"
            placeholder="Title for User B"
          />
          <button
            onClick={handleUserBAttempt}
            className="px-4 py-2 bg-[#C53030] hover:bg-[#9B2C2C] text-white font-semibold text-xs rounded-xl flex items-center justify-center gap-2 transition-all shadow-sm"
          >
            <AlertOctagon className="w-3.5 h-3.5" />
            <span>User B Attempts Application</span>
          </button>
          <div className="text-[11px] p-2.5 rounded-lg bg-[#FED7D7] text-[#C53030] font-mono border border-[#C53030]/30 leading-relaxed">
            {resB}
          </div>
        </div>
      </div>

      {/* Active Locks Table Panel */}
      <div className="lg:col-span-6 parchment-card p-6 flex flex-col gap-5">
        <div className="flex items-center justify-between border-b border-[#E3DAC7] pb-3">
          <div className="flex items-center gap-2 font-bold text-base text-[#1A202C]">
            <Lock className="w-5 h-5 text-[#1E7B62]" />
            <span>Active Pending Application Locks in Redis Cache</span>
          </div>
          <button
            onClick={fetchLocks}
            disabled={loadingLocks}
            className="btn-emerald-outline text-xs px-3 py-1 flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingLocks ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        <div className="border border-[#E3DAC7] rounded-xl overflow-hidden bg-white/80">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F7F2E8] border-b border-[#E3DAC7] text-[#4A5568] font-bold">
              <tr>
                <th className="p-3">Locked Title</th>
                <th className="p-3">Applicant ID</th>
                <th className="p-3">TTL Remaining</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E3DAC7]">
              {locks.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-6 text-center text-[#64748B]">
                    No active locks in cache.
                  </td>
                </tr>
              ) : (
                locks.map((lock, i) => (
                  <tr key={i} className="hover:bg-[#F4F2E9]">
                    <td className="p-3 font-bold text-[#1A202C]">{lock.title}</td>
                    <td className="p-3 font-mono text-[11px]">{lock.applicant_id}</td>
                    <td className="p-3 text-[#166552] font-bold">{lock.ttl_remaining}s</td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => handleReleaseLock(lock.title, lock.applicant_id)}
                        className="px-2.5 py-1 text-[11px] font-semibold text-[#C53030] bg-[#FED7D7] hover:bg-[#FEB2B2] rounded-lg transition-all flex items-center gap-1 ml-auto"
                      >
                        <Trash2 className="w-3 h-3" />
                        <span>Release</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
