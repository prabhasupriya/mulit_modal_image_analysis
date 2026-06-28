"use client";

import { useState } from "react";
import AnalysisDashboard from "../components/AnalysisDashboard";
import GenerationStudio from "../components/GenerationStudio";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState("analysis");

  return (
    <main className="app-shell">
      <header className="app-header">
        <h1>Multi-Modal AI Platform</h1>
        <span className="tag">VLM + DIFFUSION // ASYNC PIPELINE</span>
      </header>

      <nav className="tabs">
        <button
          className={`tab-button ${activeTab === "analysis" ? "active" : ""}`}
          onClick={() => setActiveTab("analysis")}
        >
          Analysis Dashboard
        </button>
        <button
          className={`tab-button ${activeTab === "generation" ? "active" : ""}`}
          onClick={() => setActiveTab("generation")}
        >
          Generation Studio
        </button>
      </nav>

      {activeTab === "analysis" ? <AnalysisDashboard /> : <GenerationStudio />}
    </main>
  );
}
