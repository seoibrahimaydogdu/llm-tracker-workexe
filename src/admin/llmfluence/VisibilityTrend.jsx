import React, { useEffect, useState } from "react";
import { supabase } from "../../lib/supabaseClient";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function VisibilityTrend() {
  const [data, setData] = useState([]);

  useEffect(() => {
    async function fetchTrendData() {
      const { data, error } = await supabase
        .from("llm_mentions")
        .select("created_at")
        .eq("brand", "workexe.co")
        .eq("mentioned", true);

      if (error) {
        console.error("Trend verisi alınamadı:", error);
        return;
      }

      // Tarihlere göre haftalık gruplama
      const trendMap = {};
      data.forEach((row) => {
        const date = new Date(row.created_at);
        const week = `${date.getFullYear()}-W${getWeekNumber(date)}`;
        trendMap[week] = (trendMap[week] || 0) + 1;
      });

      const formatted = Object.entries(trendMap).map(([week, count]) => ({
        week,
        count,
      }));

      setData(formatted);
    }

    fetchTrendData();
  }, []);

  // Yardımcı fonksiyon: ISO hafta numarası al
  function getWeekNumber(date) {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">📈 Görünürlük Trend Grafiği</h2>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid stroke="#ccc" />
          <XAxis dataKey="week" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Line type="monotone" dataKey="count" stroke="#8b5cf6" strokeWidth={3} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
