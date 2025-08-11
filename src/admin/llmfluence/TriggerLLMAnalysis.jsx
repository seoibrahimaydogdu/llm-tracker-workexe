// admin/llmfluence/TriggerLLMAnalysis.jsx
import React, { useState } from "react";

export default function TriggerLLMAnalysis() {
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  const handleRunAnalysis = async () => {
    setLoading(true);
    setStatusMessage("");

    try {
      const res = await fetch("http://localhost:8000/run-llm-mention-analysis");
      const data = await res.json();
      setStatusMessage(data.message || "İşlem tamamlandı.");
    } catch (error) {
      console.error("Hata:", error);
      setStatusMessage("Bir hata oluştu.");
    }

    setLoading(false);
  };

  return (
    <div className="bg-white p-6 rounded shadow mb-8">
      <h2 className="text-lg font-semibold text-purple-700 mb-3">
        ⚡ LLM Mention Analizi Başlat
      </h2>
      <button
        onClick={handleRunAnalysis}
        className={`bg-purple-700 text-white px-4 py-2 rounded ${loading ? "opacity-50 cursor-not-allowed" : "hover:bg-purple-800"}`}
        disabled={loading}
      >
        {loading ? "Çalışıyor..." : "Analizi Başlat"}
      </button>
      {statusMessage && (
        <p className="mt-4 text-gray-700">{statusMessage}</p>
      )}
    </div>
  );
}
