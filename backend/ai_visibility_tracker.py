import asyncio
from typing import Dict, List, Any
import google.generativeai as genai
import openai
from datetime import datetime

class AIVisibilityTracker:
    def __init__(self):
        # AI API keys
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Configure APIs
        genai.configure(api_key=self.gemini_api_key)
        openai.api_key = self.openai_api_key
    
    async def test_prompt_visibility(self, prompt: str, target_website: str) -> Dict[str, Any]:
        """Gerçek AI modellerinde prompt test et"""
        results = {}
        
        # Test different AI models
        models_to_test = [
            {"name": "ChatGPT", "function": self.test_chatgpt},
            {"name": "Gemini", "function": self.test_gemini},
            {"name": "Claude", "function": self.test_claude}  # Anthropic API gerekli
        ]
        
        for model in models_to_test:
            try:
                print(f"🤖 {model['name']} test ediliyor...")
                response = await model['function'](prompt)
                
                # Response'ta website bahsediliyor mu?
                visibility_score = self.analyze_website_mention(response, target_website)
                ranking = self.extract_ranking_info(response, target_website)
                
                results[model['name']] = {
                    "response": response,
                    "visibility_score": visibility_score,
                    "ranking": ranking,
                    "mentioned": visibility_score > 0,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                print(f"❌ {model['name']} hatası: {e}")
                results[model['name']] = {
                    "error": str(e),
                    "visibility_score": 0,
                    "mentioned": False
                }
        
        return results
    
    async def test_chatgpt(self, prompt: str) -> str:
        """ChatGPT API ile test"""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"ChatGPT API hatası: {e}")
    
    async def test_gemini(self, prompt: str) -> str:
        """Gemini API ile test"""
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = await model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API hatası: {e}")
    
    def analyze_website_mention(self, response: str, website: str) -> int:
        """Response'ta website bahsedilme skorunu hesapla"""
        response_lower = response.lower()
        website_lower = website.lower()
        
        # Domain name extraction
        domain_name = website_lower.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        company_name = domain_name.split('.')[0]
        
        score = 0
        
        # Direct mention
        if website_lower in response_lower:
            score += 50
        
        if domain_name in response_lower:
            score += 30
        
        if company_name in response_lower:
            score += 20
        
        # Context-based scoring
        if any(keyword in response_lower for keyword in ['recommend', 'suggest', 'best', 'top']):
            if company_name in response_lower:
                score += 30
        
        return min(score, 100)
    
    def extract_ranking_info(self, response: str, website: str) -> str:
        """Response'tan ranking bilgisini çıkar"""
        response_lower = response.lower()
        
        # Look for ranking keywords
        ranking_patterns = [
            r'(\d+)\..*?' + website.lower(),
            r'(\d+)\s*-.*?' + website.lower(),
            r'top\s*(\d+)',
            r'first|1st|#1' 
        ]
        
        # Bu basit bir implementasyon - daha gelişmiş NLP gerekebilir
        if 'first' in response_lower or '#1' in response_lower or '1st' in response_lower:
            return "1st"
        elif 'second' in response_lower or '2nd' in response_lower:
            return "2nd"
        elif 'third' in response_lower or '3rd' in response_lower:
            return "3rd"
        else:
            return "N/A"

# Usage example
tracker = AIVisibilityTracker()