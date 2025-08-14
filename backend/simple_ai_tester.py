import google.generativeai as genai
import os
import asyncio
from datetime import datetime
from rapidfuzz import fuzz
import difflib

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

                # Mentioned flag: fuzzy ve difflib ile
                try:
                    response_lower = response_text.lower()
                    domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
                    company_name = domain.split('.')[0].lower()
                    short_name = company_name.replace('hotel', '').replace('oteller', '').replace('otel', '').strip()
                    otel_variants = [
                        f"{short_name} sorgun",
                        f"{short_name} belek",
                        f"{short_name} lara",
                        f"{short_name} bodrum",
                        f"{short_name} torba",
                        f"{short_name} + otel",
                        f"{short_name} hotel"
                    ]
                    all_names = [company_name, short_name] + otel_variants
                    words = response_lower.split()
                    mentioned = (
                        website.lower() in response_lower or
                        domain.lower() in response_lower or
                        company_name in response_lower or
                        (short_name and short_name in response_lower) or
                        any(variant in response_lower for variant in otel_variants) or
                        any(fuzz.partial_ratio(name, response_lower) > 80 for name in all_names if name.strip()) or
                        any(difflib.get_close_matches(name, words, n=1, cutoff=0.85) for name in all_names if name.strip())
                    )
                except Exception as e:
                    print(f"❌ Mentioned algoritmasında hata: {e}")
                    mentioned = False

                results.append({
                    'prompt': prompt,
                    'response': response_text,
                    'visibility_score': visibility_score,
                    'ranking': ranking_info,
                    'sentiment': sentiment,
                    'mentioned': mentioned,
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
        response_lower = response.lower()
        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        company_name = domain.split('.')[0].lower()
        short_name = company_name.replace('hotel', '').replace('oteller', '').replace('otel', '').strip()

        score = 0

        # 1. Tam domain
        if website.lower() in response_lower:
            score += 50
        # 2. Domain adı
        if domain.lower() in response_lower:
            score += 35
        # 3. Şirket adı
        if company_name in response_lower:
            score += 25
        # 4. Kısa marka adı
        if short_name and short_name in response_lower:
            score += 20

        # 5. Otel varyasyonları
        otel_variants = [
            f"{short_name} sorgun",
            f"{short_name} belek",
            f"{short_name} lara",
            f"{short_name} bodrum",
            f"{short_name} torba",
            f"{short_name} + otel",
            f"{short_name} hotel"
        ]
        for variant in otel_variants:
            if variant in response_lower:
                score += 15
                break

        # 6. Fuzzy matching (rapidfuzz)
        all_names = [company_name, short_name] + otel_variants
        for name in all_names:
            if not name.strip():
                continue
            fuzz_ratio = fuzz.partial_ratio(name, response_lower)
            if fuzz_ratio > 80:
                score += 15
                break

        # 7. difflib ile yakın eşleşme
        words = response_lower.split()
        for name in all_names:
            if not name.strip():
                continue
            matches = difflib.get_close_matches(name, words, n=1, cutoff=0.85)
            if matches:
                score += 10
                break

        return max(0, min(score, 100))
    
    def extract_ranking(self, response: str, website: str) -> str:
        """Ranking bilgisini çıkar"""
        response_lower = response.lower()
        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        company_name = domain.split('.')[0].lower()
        
        # Special handling for Turkish companies
        company_variations = [company_name]
        if company_name == "kahvedunyasi":
            company_variations.extend(["kahve dünyası", "kahve dünyasi", "kahvedünyası", "kahvedünyasi"])
        elif company_name == "workexe":
            company_variations.extend(["work exe", "workex"])
        elif company_name == "ahrefs":
            company_variations.extend(["ah refs", "ahref"])
        
        company_found = any(variation in response_lower for variation in company_variations)
        
        if company_found:
            if any(word in response_lower for word in ['birinci', 'first', '1.', 'en iyi']):
                return "1st"
            elif any(word in response_lower for word in ['ikinci', 'second', '2.']):
                return "2nd"
            elif any(word in response_lower for word in ['üçüncü', 'third', '3.']):
                return "3rd"
            elif any(word in response_lower for word in ['önde gelen', 'lider', 'top', 'büyük']):
                return "Top 10"
            else:
                return "Mentioned"
        
        return "Not Ranked"
    
    def analyze_sentiment(self, response: str, website: str) -> str:
        """Sentiment analizi"""
        response_lower = response.lower()
        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        company_name = domain.split('.')[0].lower()
        
        # Special handling for Turkish companies
        company_variations = [company_name]
        if company_name == "kahvedunyasi":
            company_variations.extend(["kahve dünyası", "kahve dünyasi", "kahvedünyası", "kahvedünyasi"])
        elif company_name == "workexe":
            company_variations.extend(["work exe", "workex"])
        elif company_name == "ahrefs":
            company_variations.extend(["ah refs", "ahref"])
        
        company_found = any(variation in response_lower for variation in company_variations)
        
        if not company_found:
            return "neutral"
        
        positive_words = ['mükemmel', 'harika', 'en iyi', 'önerir', 'güvenilir', 'profesyonel', 'kaliteli', 'başarılı', 'popüler', 'büyük', 'geniş']
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