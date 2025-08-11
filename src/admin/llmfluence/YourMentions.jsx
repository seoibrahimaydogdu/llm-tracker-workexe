// src/admin/llmfluence/YourMentions.jsx
import React, { useEffect, useState } from "react";
import { supabase } from "../../lib/supabaseClient";

export default function YourMentions() {
  const [mentions, setMentions] = useState([]);

  useEffect(() => {
    const fetchMentions = async () => {
      const { data, error } = await supabase
        .from("llm_mentions")
        .select("prompt, model, mentioned, score, source_url, created_at")
        .order("created_at", { ascending: false })
        .limit(10);

      if (error) {
        console.error("Mention listesi alınamadı:", error);
      } else {
        setMentions(data);
      }
    };

    fetchMentions();
  }, []);

  return (
    <div className="bg-white rounded shadow p-6 overflow-auto">
      <h2 className="text-xl font-semibold mb-4 text-purple-700">
        ✅ Markanızın Geçtiği Promptlar
      </h2>

      <table className="min-w-full table-auto">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="px-4 py-2 text-sm text-gray-700">Model</th>
            <th className="px-4 py-2 text-sm text-gray-700">Mentioned</th>
            <th className="px-4 py-2 text-sm text-gray-700">Score</th>
            <th className="px-4 py-2 text-sm text-gray-700">Prompt</th>
            <th className="px-4 py-2 text-sm text-gray-700">Kaynak</th>
          </tr>
        </thead>
        <tbody>
          {mentions.map((item, index) => (
            <tr key={index} className="border-t">
              <td className="px-4 py-2 text-sm">{item.model}</td>
              <td className="px-4 py-2">
                {item.mentioned ? (
                  <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium">
                    Geçti
                  </span>
                ) : (
                  <span className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs font-medium">
                    Geçmedi
                  </span>
                )}
              </td>
              <td className="px-4 py-2 text-sm">{item.score}</td>
              <td className="px-4 py-2 text-sm max-w-xs truncate" title={item.prompt}>
                {item.prompt?.slice(0, 60) || "-"}
              </td>
              <td className="px-4 py-2 text-sm">
                {item.source_url ? (
                  <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                    Git
                  </a>
                ) : (
                  "-"
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
