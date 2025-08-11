import { Configuration, OpenAIApi } from "openai";

const config = new Configuration({
  apiKey: import.meta.env.VITE_OPENAI_API_KEY,
});
const openai = new OpenAIApi(config);

export async function analyzeLLMImpact(brand) {
  const prompt = `
Kullanıcı bir ürün ya da hizmet hakkında ChatGPT'den öneri istediğinde,
ChatGPT "${brand}" markasını öneriyor mu? Geçiyorsa neden ve hangi bağlamda?

Lütfen aşağıdaki gibi kısa JSON yanıtı ver:
{
  "brand": "${brand}",
  "mentioned": true | false,
  "score": 0-100,
  "summary": "GPT’de ne şekilde geçtiği"
}`;

  const res = await openai.createChatCompletion({
    model: "gpt-4o",
    messages: [{ role: "user", content: prompt }],
  });

  const output = res.data.choices[0].message.content;
  return JSON.parse(output); // ⚠️ Try/catch ile sarmala istersen
}
