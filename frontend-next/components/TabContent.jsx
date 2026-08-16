"use client";
import { useTab } from "@/context/TabContext";
import VerificationStudio from "@/components/tabs/VerificationStudio";
import BatchScreening from "@/components/tabs/BatchScreening";
import LockSimulator from "@/components/tabs/LockSimulator";
import RulebookTab from "@/components/tabs/RulebookTab";
import RegistryBrowser from "@/components/tabs/RegistryBrowser";

export default function TabContent() {
  const { activeTab } = useTab();

  return (
    <main className="main-container">
      <div style={{ display: activeTab === "studio-tab" ? "block" : "none" }}>
        <VerificationStudio />
      </div>
      <div style={{ display: activeTab === "batch-tab" ? "block" : "none" }}>
        <BatchScreening />
      </div>
      <div style={{ display: activeTab === "lock-tab" ? "block" : "none" }}>
        <LockSimulator />
      </div>
      <div style={{ display: activeTab === "rules-tab" ? "block" : "none" }}>
        <RulebookTab isActive={activeTab === "rules-tab"} />
      </div>
      <div style={{ display: activeTab === "db-tab" ? "block" : "none" }}>
        <RegistryBrowser isActive={activeTab === "db-tab"} />
      </div>
    </main>
  );
}
