import React from "react";

// Alt bileşenler (admin/llmfluence klasörü altında)
import VisibilityTrend from "./llmfluence/VisibilityTrend";
import IndustryRanking from "./llmfluence/IndustryRanking";
import YourMentions from "./llmfluence/YourMentions";
import ModelPerformance from "./llmfluence/ModelPerformance";
import TriggerLLMAnalysis from "./llmfluence/TriggerLLMAnalysis";

export default function LLMfluenceDashboard() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Panel Başlığı */}
      <h1 className="text-3xl font-bold text-purple-700 mb-6">
        🧠 Workexe LLMfluence Paneli
      </h1>

      {/* 0. Analiz Başlatıcı Buton */}
      <section className="mb-8">
        <TriggerLLMAnalysis />
      </section>

      {/* 1. Günlük Görünürlük Trendi */}
      <section className="mb-8">
        <VisibilityTrend />
      </section>

      {/* 2. Sektörel Görünürlük Sıralaması */}
      <section className="mb-8">
        <IndustryRanking />
      </section>

      {/* 3 & 4. Mention Listesi + Model Performansı */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <YourMentions />
        <ModelPerformance />
      </section>
    </div>
  );
}
