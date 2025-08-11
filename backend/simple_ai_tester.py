import google.generativeai as genai
import os
import asyncio
from datetime import datetime

class SimpleAITester:
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=self.gemini_api_key)
        
        # Try different model names
        try:
            # First try the new model name
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Using gemini-1.5-flash model")
        except:
            try:
                self.model = genai.GenerativeModel('gemini-1.0-pro')
                print("✅ Using gemini-1.0-pro model")
            except:
                try:
                    self.model = genai.GenerativeModel('models/gemini-1.5-flash')
                    print("✅ Using models/gemini-1.5-flash")
                except Exception as e:
                    print(f"❌ Model initialization error: {e}")
                    # List available models
                    self.list_available_models()
                    raise e
    
    def list_available_models(self):
        """List all available Gemini models"""
        try:
            print("📋 Available Gemini models:")
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    print(f"   ✅ {model.name}")
        except Exception as e:
            print(f"❌ Could not list models: {e}")
    
    async def test_website_visibility(self, website: str, test_prompts: list = None):
        """Gemini ile website visibility test"""
        print(f"🎯 Testing visibility for: {website}")
        
        if not test_prompts:
            # Auto-generated test prompts
            domain_name = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
            company_name = domain_name.split('.')[0]
            
            test_prompts = [
                f"Türkiye'de marka tescil süreci nasıl işler ve bu süreçte {company_name} gibi firmalar nasıl yardımcı olabilir?",
                f"{company_name} gibi patent firmaları hangi hizmetleri sunmaktadır?",
                f"Marka tescil için hangi firmaları tercih etmeliyim? {company_name} hakkında ne düşünüyorsun?",
                f"Patent başvuru sürecinde {company_name} benzeri şirketlerin avantajları nelerdir?",
                f"Türkiye'de fikri mülkiyet alanında çalışan en iyi firmalar hangileridir? {company_name} nasıl?",
            ]
        
        results = []
        
        for i, prompt in enumerate(test_prompts):
            print(f"🤖 Test {i+1}/{len(test_prompts)}: {prompt[:50]}...")
            
            try:
                # Gemini'ye prompt gönder
                response = self.model.generate_content(prompt)
                response_text = response.text if response.text else "No response generated"
                
                # Website bahsediliyor mu analiz et
                visibility_score = self.calculate_visibility_score(response_text, website)
                ranking_info = self.extract_ranking(response_text, website)
                sentiment = self.analyze_sentiment(response_text, website)
                
                results.append({
                    'prompt': prompt,
                    'response': response_text,
                    'visibility_score': visibility_score,
                    'ranking': ranking_info,
                    'sentiment': sentiment,
                    'mentioned': visibility_score > 0,
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"   ✅ Score: {visibility_score}/100, Ranking: {ranking_info}")
                
                # Rate limiting
                await asyncio.sleep(3)  # Increased delay
                
            except Exception as e:
                print(f"   ❌ Test hatası: {e}")
                results.append({
                    'prompt': prompt,
                    'error': str(e),
                    'visibility_score': 0,
                    'ranking': 'Error',
                    'sentiment': 'neutral',
                    'mentioned': False
                })
        
        summary = self.calculate_summary(results)
        
        return {
            'website': website,
            'test_results': results,
            'summary': summary,
            'completion_time': datetime.now().isoformat()
        }
    
    def calculate_visibility_score(self, response: str, website: str) -> int:
        """Response'ta website bahsedilme skorunu hesapla"""
        response_lower = response.lower()
        
        # Domain extraction
        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        company_name = domain.split('.')[0].lower()
        
        score = 0
        
        # Direct mentions
        if website.lower() in response_lower:
            score += 50
            print(f"      🎯 Direct website mention found!")
        
        if domain.lower() in response_lower:
            score += 35
            print(f"      🌐 Domain mention found!")
        
        if company_name in response_lower:
            score += 25
            print(f"      🏢 Company name mention found!")
        
        # Context scoring
        positive_context = ['önerir', 'tavsiye', 'en iyi', 'kaliteli', 'güvenilir', 'profesyonel']
        if any(ctx in response_lower for ctx in positive_context):
            if company_name in response_lower:
                score += 20
                print(f"      ⭐ Positive context found!")
        
        return max(0, min(score, 100))
    
    def extract_ranking(self, response: str, website: str) -> str:
        """Ranking bilgisini çıkar"""
        response_lower = response.lower()
        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        company_name = domain.split('.')[0].lower()
        
        if company_name in response_lower:
            if any(word in response_lower for word in ['birinci', 'first', '1.', 'en iyi']):
                return "1st"
            elif any(word in response_lower for word in ['ikinci', 'second', '2.']):
                return "2nd"
            elif any(word in response_lower for word in ['üçüncü', 'third', '3.']):
                return "3rd"
            elif any(word in response_lower for word in ['önde gelen', 'lider', 'top']):
                return "Top 10"
            else:
                return "Mentioned"
        
        return "Not Ranked"
    
    def analyze_sentiment(self, response: str, website: str) -> str:
        """Sentiment analizi"""
        response_lower = response.lower()
        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        company_name = domain.split('.')[0].lower()
        
        if company_name not in response_lower:
            return "neutral"
        
        positive_words = ['mükemmel', 'harika', 'en iyi', 'önerir', 'güvenilir', 'profesyonel', 'kaliteli', 'başarılı']
        negative_words = ['kötü', 'berbat', 'tavsiye etmem', 'sorunlu', 'yetersiz', 'güvenilmez']
        
        positive_count = sum(1 for word in positive_words if word in response_lower)
        negative_count = sum(1 for word in negative_words if word in response_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def calculate_summary(self, results: list) -> dict:
        """Test sonuçlarının özetini çıkar"""
        total_tests = len(results)
        mentioned_count = len([r for r in results if r.get('mentioned', False)])
        successful_tests = len([r for r in results if 'error' not in r])
        
        if successful_tests > 0:
            avg_score = sum([r.get('visibility_score', 0) for r in results if 'error' not in r]) / successful_tests
        else:
            avg_score = 0
        
        # Sentiment breakdown
        sentiments = [r.get('sentiment', 'neutral') for r in results if r.get('mentioned', False)]
        sentiment_breakdown = {
            'positive': sentiments.count('positive'),
            'negative': sentiments.count('negative'),
            'neutral': sentiments.count('neutral')
        }
        
        # Best performing prompt
        best_prompt = None
        if successful_tests > 0:
            best_prompt = max([r for r in results if 'error' not in r], 
                            key=lambda x: x.get('visibility_score', 0))
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'mentioned_count': mentioned_count,
            'mention_rate': round((mentioned_count / successful_tests) * 100, 1) if successful_tests > 0 else 0,
            'average_visibility_score': round(avg_score, 1),
            'sentiment_breakdown': sentiment_breakdown,
            'best_performing_prompt': best_prompt,
            'recommendation': self.get_recommendation(avg_score, mentioned_count, successful_tests)
        }
    
    def get_recommendation(self, avg_score: float, mentioned_count: int, total_tests: int) -> str:
        """Öneriler üret"""
        mention_rate = (mentioned_count / total_tests) * 100 if total_tests > 0 else 0
        
        if mention_rate >= 80 and avg_score >= 70:
            return "🟢 MÜKEMMEL: Web siteniz Gemini AI'da çok iyi görünürlüğe sahip!"
        elif mention_rate >= 50 and avg_score >= 50:
            return "🟡 İYİ: Görünürlük iyi, içerik pazarlama ile daha da geliştirilebilir."
        elif mention_rate >= 20:
            return "🟠 ORTA: Görünürlük sınırlı. SEO ve içerik stratejisine odaklanın."
        else:
            return "🔴 DÜŞÜK: Görünürlük çok düşük. Marka bilinirliği çalışması gerekli."