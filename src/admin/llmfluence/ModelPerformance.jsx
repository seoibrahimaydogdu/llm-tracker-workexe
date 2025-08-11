// src/admin/llmfluence/ModelPerformance.jsx
import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { supabase } from "../../lib/supabaseClient";

export default function ModelPerformance() {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchModelPerformance = async () => {
      const { data: mentions, error } = await supabase
        .from("llm_mentions")
        .select("model, score");

      if (error) {
        console.error("Model verisi çekilemedi:", error);
        return;
      }

      // Model başına ortalama skor hesapla
      const scoreMap = {};
      const countMap = {};

      mentions.forEach(({ model, score }) => {
        if (model) {
          scoreMap[model] = (scoreMap[model] || 0) + score;
          countMap[model] = (countMap[model] || 0) + 1;
        }
      });

      const formattedData = Object.keys(scoreMap).map((model) => ({
        model,
        averageScore: Math.round(scoreMap[model] / countMap[model]),
      }));

      setData(formattedData);
    };

    fetchModelPerformance();
  }, []);

  return (
    <div className="bg-white rounded shadow p-6">
      <h2 className="text-xl font-semibold mb-4 text-purple-700">
        🧠 LLM Model Performansları
      </h2>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="model" />
          <YAxis domain={[0, 100]} />
          <Tooltip />
          <Bar dataKey="averageScore" fill="#7e22ce" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
