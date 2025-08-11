import { useState } from "react";
import { analyzeLLMImpact } from "./analyzeLLMImpact";

export function useLLMfluence() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const runAnalysis = async (brand) => {
    setLoading(true);
    try {
      const data = await analyzeLLMImpact(brand);
      setResult(data);
    } catch (err) {
      console.error("LLM analysis error:", err);
    }
    setLoading(false);
  };

  return { loading, result, runAnalysis };
}
