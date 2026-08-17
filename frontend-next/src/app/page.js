"use client";

import React, { useState } from "react";
import Header from "@/components/Header";
import VerificationStudio from "@/components/VerificationStudio";
import BatchScreening from "@/components/BatchScreening";
import LockSimulator from "@/components/LockSimulator";
import PRGIRulebook from "@/components/PRGIRulebook";
import RegistryBrowser from "@/components/RegistryBrowser";

export default function Home() {
  const [activeTab, setActiveTab] = useState("studio");

  return (
    <div className="min-h-screen max-w-7xl mx-auto p-4 md:p-6 flex flex-col">
      {/* Header with emblem & tabs */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Tab Views */}
      <main className="flex-1">
        {activeTab === "studio" && <VerificationStudio setActiveTab={setActiveTab} />}
        {activeTab === "batch" && <BatchScreening />}
        {activeTab === "lock" && <LockSimulator />}
        {activeTab === "rules" && <PRGIRulebook />}
        {activeTab === "db" && <RegistryBrowser />}
      </main>

      {/* Footer */}
      <footer className="mt-8 pt-4 border-t border-[#E3DAC7] flex flex-col sm:flex-row items-center justify-between text-xs text-[#64748B] gap-2">
        <div>
          <span>Press Registrar General of India (PRGI) Title Verification Subsystem &bull; Autonomous Architecture</span>
        </div>
        <div>
          <span>FastAPI &bull; Double Metaphone &bull; Indic-Soundex &bull; Aho-Corasick &bull; Multilingual Vectors</span>
        </div>
      </footer>
    </div>
  );
}
