// src/App.jsx
import { useEffect } from "react";
import { Routes, Route, useNavigate } from "react-router-dom"; 
import { detectAndLogBot } from "./lib/trackBot";

// Sayfalar
import BotTrafficDashboard from "./admin/BotTrafficDashboard";
import LLMfluenceDashboard from "./admin/LLMfluenceDashboard"; // ✅ Yeni ekran eklendi

// Ana uygulama içeriğini barındıran bileşen
function MainAppContent() {
  const navigate = useNavigate();

  useEffect(() => {
    detectAndLogBot();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-4xl font-bold text-blue-600 mb-6">
        Workexe AI Tracker
      </h1>

      <div className="flex gap-4 mb-6">
        <button
          onClick={() => navigate("/tracker")}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded"
        >
          Bot Trafiği Paneline Git
        </button>

        <button
          onClick={() => navigate("/llmfluence")}
          className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded"
        >
          LLMfluence Paneline Git
        </button>
      </div>

      <p className="text-lg text-gray-700">
        Ana sayfa içeriği burada yer alabilir. Bot trafiği veya GPT'deki görünürlük için yukarıdaki panellere geçin.
      </p>
    </div>
  );
}

// Router'ı içeren ana App bileşeni
export default function App() {
  return (
    <Routes>
      {/* Ana sayfa */}
      <Route path="/" element={<MainAppContent />} />

      {/* Bot Trafiği Paneli */}
      <Route path="/tracker" element={<BotTrafficDashboard />} />

      {/* GPT'de Görünürlük Paneli */}
      <Route path="/llmfluence" element={<LLMfluenceDashboard />} />
    </Routes>
  );
}
