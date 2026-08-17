"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, Layers, Lock, BookOpen, Database, ShieldCheck } from "lucide-react";

export default function Header({ activeTab, setActiveTab }) {
  const [systemStatus, setSystemStatus] = useState("160,000+ Titles Indexed");

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch("/api/health");
        if (res.ok) {
          const data = await res.json();
          // if (data.total_registered_titles) {
          //   setSystemStatus(`${data.total_registered_titles.toLocaleString()}+ Titles Indexed`);
          // }
        }
      } catch (e) {
        // Fallback default
      }
    };
    checkHealth();
  }, []);

  const tabs = [
    { id: "studio", label: "Verification Studio", icon: Sparkles },
    { id: "batch", label: "Batch Screening", icon: Layers },
    { id: "lock", label: "Lock Simulator", icon: Lock },
    { id: "rules", label: "PRGI Rulebook", icon: BookOpen },
    { id: "db", label: "Registry Browser", icon: Database },
  ];

  return (
    <header className="flex flex-col md:flex-row items-center justify-between gap-4 py-4 px-6 mb-6 parchment-card bg-[#F7F2E8] border border-[#E3DAC7]">
      {/* Brand & Emblem */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-[#1E7B62] text-white flex items-center justify-center shadow-sm">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-[#1A202C]">PRGI TITLE VERIFIER</h1>
          </div>
          <p className="text-xs text-[#64748B] font-medium">Press Registrar General of India &bull; PRP Act 2023</p>
        </div>
      </div>

      {/* Navigation Pills */}
      <nav className="flex items-center gap-1.5 bg-[#EAE4D6] p-1.5 rounded-full overflow-x-auto max-w-full">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-full transition-all duration-200 whitespace-nowrap ${
                isActive
                  ? "bg-[#1E7B62] text-white shadow-sm"
                  : "text-[#4A5568] hover:text-[#1A202C] hover:bg-[#E2DDD0]"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Status Badge */}
      <div className="hidden lg:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#D5EDE3] text-[#166552] text-xs font-semibold">
        <span className="w-2 h-2 rounded-full bg-[#1E7B62] animate-pulse"></span>
        <span>{systemStatus}</span>
      </div>
    </header>
  );
}
