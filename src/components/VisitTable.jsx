import React, { useEffect, useState } from "react";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_API_KEY = import.meta.env.VITE_SUPABASE_API_KEY;

export default function VisitTable() {
  const [visits, setVisits] = useState([]);

  useEffect(() => {
    const fetchVisits = async () => {
      try {
        const response = await fetch(
          `${SUPABASE_URL}/rest/v1/user_visits?select=*`,
          {
            headers: {
              apikey: SUPABASE_API_KEY,
              Authorization: `Bearer ${SUPABASE_API_KEY}`,
              "Content-Type": "application/json",
            },
          }
        );
        const data = await response.json();
        setVisits(data);
      } catch (error) {
        console.error("Veri çekme hatası:", error);
      }
    };

    fetchVisits();
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Ziyaretçi Takibi</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full border border-gray-300 bg-white">
          <thead>
            <tr className="bg-gray-100 text-left text-sm font-semibold">
              <th className="p-2 border">Tarih</th>
              <th className="p-2 border">URL</th>
              <th className="p-2 border">Referrer</th>
              <th className="p-2 border">User Agent</th>
              <th className="p-2 border">Session ID</th>
            </tr>
          </thead>
          <tbody>
            {visits.length > 0 ? (
              visits.map((visit, idx) => (
                <tr key={idx} className="border-t text-sm">
                  <td className="p-2 border">
                    {new Date(visit.created_at).toLocaleString()}
                  </td>
                  <td className="p-2 border">{visit.url}</td>
                  <td className="p-2 border">{visit.referrer || "—"}</td>
                  <td className="p-2 border">
                    {visit.user_agent?.slice(0, 40) || "—"}...
                  </td>
                  <td className="p-2 border">{visit.session_id}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" className="p-4 text-center text-gray-500">
                  Kayıt bulunamadı.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}