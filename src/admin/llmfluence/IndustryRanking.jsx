import React, { useEffect, useState } from "react";
import { supabase } from "../../lib/supabaseClient";

export default function IndustryRanking() {
  const [ranking, setRanking] = useState([]);

  useEffect(() => {
    const fetchRanking = async () => {
      const { data, error } = await supabase
        .from("llm_mentions")
        .select("brand, score")
        .order("score", { ascending: false });

      if (!error && data) {
        // Her markanın en yüksek skorunu alalım (tekrar edenleri eleyelim)
        const brandMaxScores = {};
        data.forEach(({ brand, score }) => {
          if (!brandMaxScores[brand] || score > brandMaxScores[brand]) {
            brandMaxScores[brand] = score;
          }
        });

        const sorted = Object.entries(brandMaxScores)
          .map(([brand, score]) => ({ brand, score }))
          .sort((a, b) => b.score - a.score);

        setRanking(sorted.slice(0, 10)); // İlk 10 marka
      } else {
        console.error("Sıralama verisi alınamadı:", error);
      }
    };

    fetchRanking();
  }, []);

  return (
    <div className="bg-white rounded shadow p-6">
      <h2 className="text-xl font-semibold mb-4 text-purple-700">
        🏆 Sektörde En Çok Önerilen Markalar
      </h2>

      <ol className="list-decimal pl-6 space-y-2 text-gray-800">
        {ranking.map((item, index) => (
          <li key={index}>
            <span className="font-semibold">{item.brand}</span> – 
            <span className="ml-2 text-purple-700">{item.score} puan</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
