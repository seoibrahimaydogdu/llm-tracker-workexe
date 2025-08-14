import { GoogleGenerativeAI } from "@google/generative-ai";

const genAI = new GoogleGenerativeAI(import.meta.env.VITE_GEMINI_API_KEY);

export async function analyzeLLMImpact(brand) {
  const prompt = `
Kullanıcı bir ürün ya da hizmet hakkında ChatGPT'den öneri istediğinde,
ChatGPT "${brand}" markasını öneriyor mu? Geçiyorsa neden ve hangi bağlamda?

Lütfen aşağıdaki gibi kısa JSON yanıtı ver:
{
  "brand": "${brand}",
  "mentioned": true | false,
  "score": 0-100,
  "summary": "GPT'de ne şekilde geçtiği"
}`;

  try {
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
    
    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();
    
    // JSON yanıtını parse et
    return JSON.parse(text);
  } catch (error) {
    console.error("Gemini API hatası:", error);
    return {
      brand: brand,
      mentioned: false,
      score: 0,
      summary: "API hatası nedeniyle analiz yapılamadı"
    };
  }
}
