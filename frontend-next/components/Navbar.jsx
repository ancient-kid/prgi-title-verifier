"use client";
import { useTab } from "@/context/TabContext";
import {
  ShieldCheck,
  Sparkles,
  Layers,
  Lock,
  BookOpen,
  Database,
} from "lucide-react";

export default function Navbar({ statusLabel }) {
  const { activeTab, setActiveTab } = useTab();

  const tabs = [
    { id: "studio-tab", icon: <Sparkles size={15} />, label: "Verification Studio" },
    { id: "batch-tab",  icon: <Layers size={15} />,   label: "Batch Screening" },
    { id: "lock-tab",   icon: <Lock size={15} />,     label: "Lock Simulator" },
    { id: "rules-tab",  icon: <BookOpen size={15} />, label: "PRGI Rulebook" },
    { id: "db-tab",     icon: <Database size={15} />, label: "Registry Browser" },
  ];

  return (
    <header className="navbar">
      <div className="nav-brand">
        <div className="emblem-container">
          <div className="ashoka-icon">
            <ShieldCheck size={22} />
          </div>
        </div>
        <div className="brand-text">
          <div className="brand-title">
            PRGI TITLE VERIFIER <span className="badge-tag">AI CORE</span>
          </div>
          <div className="brand-sub">Press Registrar General of India &bull; PRP Act 2023</div>
        </div>
      </div>

      <nav className="nav-links">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`nav-tab${activeTab === tab.id ? " active" : ""}`}
            data-tab={tab.id}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </nav>

      <div className="nav-status">
        <div className="status-indicator online"></div>
        <span className="status-text" id="system-status-label">{statusLabel}</span>
      </div>
    </header>
  );
}
