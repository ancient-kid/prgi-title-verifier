"use client";
import { createContext, useContext, useState } from "react";

const TabContext = createContext(null);

export function TabProvider({ children }) {
  const [activeTab, setActiveTab] = useState("studio-tab");
  return (
    <TabContext.Provider value={{ activeTab, setActiveTab }}>
      {children}
    </TabContext.Provider>
  );
}

export function useTab() {
  return useContext(TabContext);
}
