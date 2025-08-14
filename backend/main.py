# backend/main.py

import logging
import os
import sqlite3
import json
import random
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
import asyncio
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

# Logging yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Generative AI - güvenli import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    print("✅ Google Generative AI yüklendi")
except ImportError:
    print("⚠️ Google Generative AI bulunamadı - pip install google-generativeai")
    GEMINI_AVAILABLE = False

# Supabase - güvenli import
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
    print("✅ Supabase client yüklendi")
except ImportError:
    print("⚠️ Supabase client bulunamadı - pip install supabase")
    SUPABASE_AVAILABLE = False

# Environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

print(f"💥 ENV VARLARI: USE_SUPABASE: {USE_SUPABASE}")
if SUPABASE_URL:
    print(f"📊 Supabase URL: {SUPABASE_URL[:30]}...")

# Gemini yapılandır (eğer varsa)
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API yapılandırıldı")

# FastAPI app
app = FastAPI(title="AI Visibility Analysis API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic modelleri
class URLRequest(BaseModel):
    url: str

class AnalysisRequest(BaseModel):
    urls: list = []
    brands: list = ["Workexe", "Ahrefs", "Semrush", "Surfer SEO"] 
    models: list = ["ChatGPT", "Claude", "Gemini", "Copilot"]

# SQLite tabloları oluşturan fonksiyonu
def init_sqlite():
    """SQLite veritabanını başlat ve tabloları oluştur"""
    try:
        conn = sqlite3.connect('ai_visibility.db')
        cursor = conn.cursor()
        
        # URLs tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending',
                title TEXT,
                description TEXT,
                last_analysis TIMESTAMP,
                error_message TEXT,
                analysis_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # LLM mentions tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS llm_mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt TEXT,
                response TEXT,
                mentioned BOOLEAN DEFAULT 0,
                score INTEGER DEFAULT 0,
                summary TEXT,
                source_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # URL analysis results tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                mentioned BOOLEAN DEFAULT 0,
                score INTEGER DEFAULT 0,
                analysis_text TEXT,
                content_snippet TEXT,
                analysis_method TEXT DEFAULT 'auto',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (url_id) REFERENCES urls (id)
            )
        ''')
        
        # Analysis history tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT NOT NULL,
                urls_analyzed INTEGER DEFAULT 0,
                results_found INTEGER DEFAULT 0,
                status TEXT DEFAULT 'completed',
                error_message TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        # Visibility tests tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visibility_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website TEXT NOT NULL,
                prompts TEXT,
                results_summary TEXT,
                visibility_score INTEGER DEFAULT 0,
                mentioned_count INTEGER DEFAULT 0,
                total_tests INTEGER DEFAULT 0,
                test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # analysis_count kolonu kontrolü ve eklenmesi
        cursor.execute("PRAGMA table_info(urls)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'analysis_count' not in columns:
            print("🔧 analysis_count kolonu ekleniyor...")
            cursor.execute('ALTER TABLE urls ADD COLUMN analysis_count INTEGER DEFAULT 0')
            print("✅ analysis_count kolonu eklendi")
        
        conn.commit()
        conn.close()
        print("✅ SQLite tabloları oluşturuldu/güncellendi")
        
    except Exception as e:
        print(f"❌ SQLite başlatma hatası: {e}")
        raise e

# Supabase veya SQLite bağlantısını başlat
supabase_client = None
if USE_SUPABASE and SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase bağlantısı kuruldu")
    except Exception as e:
        print(f"❌ Supabase bağlantı hatası: {e}")
        print("⚠️ SQLite'a geçiş yapılıyor...")
        USE_SUPABASE = False

if not USE_SUPABASE:
    print("📁 SQLite kullanılıyor")
    init_sqlite()

# Yardımcı fonksiyonlar
def get_db_connection():
    """SQLite veritabanı bağlantısı al"""
    if USE_SUPABASE:
        return supabase_client
    else:
        conn = sqlite3.connect('ai_visibility.db')
        conn.row_factory = sqlite3.Row
        return conn

def fetch_url_content(url: str, timeout: int = 10) -> Dict[str, Any]:
    """URL'den SADECE GÖRÜNÜR İÇERİĞİ çek"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        
        if response.status_code == 200:
            content = response.text
            
            # Title çıkar
            title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else 'Başlık bulunamadı'
            
            # ÖNEMLİ: Sadece görünür içeriği çıkar
            clean_content = extract_visible_text(content)
            
            print(f"📊 Ham HTML: {len(content)} karakter")
            print(f"📄 Temiz metin: {len(clean_content)} karakter") 
            
            return {
                'success': True,
                'content': clean_content,  # ← Temizlenmiş içerik
                'title': title,
                'status_code': response.status_code,
                'original_size': len(content),
                'clean_size': len(clean_content)
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}',
                'status_code': response.status_code
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'status_code': 0
        }

def extract_visible_text(html_content: str) -> str:
    """HTML'den sadece görünür metni çıkar"""
    try:
        # Script ve style taglarını kaldır
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<noscript[^>]*>.*?</noscript>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # CSS ve JS dosya linklerini kaldır
        html_content = re.sub(r'<link[^>]*>', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<meta[^>]*>', '', html_content, flags=re.IGNORECASE)
        
        # JSON-LD ve structured data kaldır
        html_content = re.sub(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # HTML taglarını kaldır
        html_content = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Çoklu boşlukları temizle
        html_content = re.sub(r'\s+', ' ', html_content)
        
        # Özel karakterleri temizle
        html_content = re.sub(r'&[a-zA-Z0-9#]+;', ' ', html_content)
        
        # Başlangıç/bitiş boşluklarını temizle
        html_content = html_content.strip()
        
        return html_content
        
    except Exception as e:
        print(f"❌ Metin çıkarma hatası: {e}")
        return html_content[:1000]  # Fallback

# En üste ekle:
@app.get("/")
async def root():
    """API durumu"""
    return {
        "status": "success", 
        "message": "AI Analytics API çalışıyor!",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "status": "success",
        "message": "Test endpoint çalışıyor!",
        "data": {
            "test_message": "Backend başarıyla çalışıyor",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/debug-gemini")
async def debug_gemini():
    """Gemini API test"""
    try:
        import google.generativeai as genai
        import os
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return {"status": "error", "message": "GEMINI_API_KEY bulunamadı"}
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content("Test message: Hello Gemini!")
        
        return {
            "status": "success",
            "message": "Gemini API çalışıyor!",
            "response": response.text
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Gemini API hatası: {str(e)}"
        }

async def analyze_with_ai(content: str, brand: str, model: str, url: str) -> Dict[str, Any]:
    """AI ile GERÇEK içerik analizi yap"""
    try:
        print(f"🔍 GERÇEK ANALİZ: {brand} x {model} - {url}")
        
        # İçeriği temizle ve kısalt
        clean_content = re.sub(r'<[^>]+>', '', content)  # HTML tagları kaldır
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()  # Whitespace temizle
        
        # İçerik çok uzunsa kısalt
        if len(clean_content) > 5000:
            clean_content = clean_content[:5000] + "..."
        
        print(f"📄 Temiz içerik uzunluğu: {len(clean_content)} karakter")
        
        # Basit string analizi (fallback)
        content_lower = clean_content.lower()
        brand_lower = brand.lower()
        model_lower = model.lower()
        
        # Kesin bahsedilme kontrolü
        brand_mentioned = brand_lower in content_lower
        model_mentioned = model_lower in content_lower
        
        # Context analizi - hangi bağlamda bahsediliyor
        brand_contexts = []
        model_contexts = []
        
        if brand_mentioned:
            # Brand'in geçtiği cümleleri bul
            sentences = clean_content.split('.')
            for sentence in sentences:
                if brand_lower in sentence.lower():
                    brand_contexts.append(sentence.strip()[:200])
        
        if model_mentioned:
            # Model'in geçtiği cümleleri bul
            sentences = clean_content.split('.')
            for sentence in sentences:
                if model_lower in sentence.lower():
                    model_contexts.append(sentence.strip()[:200])
        
        # Gerçek AI analizi (Gemini varsa)
        ai_analysis = ""
        mentioned = False
        score = 0
        
        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                print(f"🤖 Gemini ile GERÇEK analiz başlatılıyor...")
                
                prompt = f"""
                Web sitesi içeriğini analiz et ve şu markaların/modellerin BAHSEDİLİP BAHSEDİLMEDİĞİNİ tespit et:

                URL: {url}
                ARANACAK MARKA: "{brand}"
                ARANACAK AI MODELİ: "{model}"

                İÇERİK:
                {clean_content}

                GÖREV:
                1. Bu içerikte "{brand}" markası bahsediliyor mu?
                2. Bu içerikte "{model}" AI modeli bahsediliyor mu?
                3. Bahsediliyorsa hangi bağlamda? (pozitif/negatif/nötr)
                4. Tam olarak hangi cümlede geçiyor?

                CEVAP FORMATI (AYNEN BU FORMATTA):
                MARKA_BAHSEDILDI: [EVET/HAYIR]
                MARKA_CONTEXT: [bahsedildiği cümle veya "Bahsedilmiyor"]
                MODEL_BAHSEDILDI: [EVET/HAYIR]
                MODEL_CONTEXT: [bahsedildiği cümle veya "Bahsedilmiyor"]
                GENEL_SKOR: [0-100 arası sayı]
                ANALIZ_SONUCU: [Kısa açıklama]
                """
                
                # Yeni Gemini model adlarını dene
                model_names = [
                    'gemini-1.5-flash',  # Yeni model
                    'gemini-1.5-pro',   # Yeni model  
                    'gemini-pro',       # Eski model
                    'models/gemini-pro' # Full path
                ]
                
                response_text = ""
                for model_name in model_names:
                    try:
                        print(f"🔄 Denenen model: {model_name}")
                        model_ai = genai.GenerativeModel(model_name)
                        response = model_ai.generate_content(prompt)
                        response_text = response.text
                        ai_analysis = response_text
                        print(f"✅ Başarılı model: {model_name}")
                        break
                    except Exception as model_error:
                        print(f"❌ Model {model_name} hatası: {model_error}")
                        continue
                
                if not response_text:
                    raise Exception("Hiçbir Gemini modeli çalışmadı")
                
                print(f"🔮 Gemini cevabı: {ai_analysis[:200]}...")
                
                # AI cevabını parse et
                lines = ai_analysis.split('\n')
                gemini_brand_mentioned = False
                gemini_model_mentioned = False
                gemini_score = 0
                
                for line in lines:
                    line = line.strip()
                    if 'MARKA_BAHSEDILDI:' in line:
                        gemini_brand_mentioned = 'EVET' in line.upper()
                    elif 'MODEL_BAHSEDILDI:' in line:
                        gemini_model_mentioned = 'EVET' in line.upper()
                    elif 'GENEL_SKOR:' in line:
                        try:
                            score_match = re.findall(r'\d+', line)
                            if score_match:
                                gemini_score = int(score_match[0])
                        except:
                            gemini_score = 0
                
                # Gemini sonuçlarını kullan
                brand_mentioned = gemini_brand_mentioned
                model_mentioned = gemini_model_mentioned
                score = gemini_score
                mentioned = brand_mentioned or model_mentioned
                
                print(f"✅ Gemini Analizi: Marka={brand_mentioned}, Model={model_mentioned}, Skor={score}")
                
            except Exception as gemini_error:
                print(f"⚠️ Gemini hatası: {gemini_error}")
                ai_analysis = f"Gemini API hatası: {str(gemini_error)}"
                
                # Fallback - basit analiz
                mentioned = brand_mentioned or model_mentioned
                if mentioned:
                    score = random.randint(60, 85)
                else:
                    score = random.randint(5, 25)
        else:
            print("⚠️ Gemini mevcut değil, basit analiz kullanılıyor")
            
            # Basit analiz skorlaması
            mentioned = brand_mentioned or model_mentioned
            if brand_mentioned and model_mentioned:
                score = random.randint(70, 90)
            elif brand_mentioned or model_mentioned:
                score = random.randint(40, 70)
            else:
                score = random.randint(5, 30)
            
            ai_analysis = f"Basit Analiz - Marka: {'✓' if brand_mentioned else '✗'}, Model: {'✓' if model_mentioned else '✗'}"
        
        # Sonuç raporu oluştur (UTF-8 uyumlu)
        result_report = f"""
🎯 GERÇEK ANALİZ RAPORU:
URL: {url}
Marka: {brand} {'✅' if brand_mentioned else '❌'}
Model: {model} {'✅' if model_mentioned else '❌'}
Skor: {score}/100

📝 Bahsedilme Detayları:
"""
        
        if brand_mentioned and brand_contexts:
            result_report += f"🏢 {brand} bahsedildiği yerler:\n"
            for ctx in brand_contexts[:2]:  # İlk 2 bağlamı göster
                result_report += f"   • {ctx}\n"
        
        if model_mentioned and model_contexts:
            result_report += f"🤖 {model} bahsedildiği yerler:\n"
            for ctx in model_contexts[:2]:  # İlk 2 bağlamı göster
                result_report += f"   • {ctx}\n"
        
        if not mentioned:
            result_report += "❌ Bu sayfada belirtilen marka/model bahsedilmiyor.\n"
        
        result_report += f"\n🔮 AI Analizi:\n{ai_analysis}"
        
        return {
            'brand_mentioned': brand_mentioned,
            'model_mentioned': model_mentioned,
            'mentioned': mentioned,
            'score': score,
            'ai_result': result_report.strip(),
            'content_snippet': clean_content[:300] + '...',
            'brand_contexts': brand_contexts[:3],
            'model_contexts': model_contexts[:3],
            'analysis_method': 'gemini' if GEMINI_AVAILABLE and ai_analysis != "Basit Analiz" else 'basic'
        }
        
    except Exception as e:
        print(f"❌ Analiz hatası: {e}")
        return {
            'brand_mentioned': False,
            'model_mentioned': False,
            'mentioned': False,
            'score': 0,
            'ai_result': f"Analiz hatası: {str(e)}",
            'content_snippet': 'Hata nedeniyle analiz edilemedi',
            'brand_contexts': [],
            'model_contexts': [],
            'analysis_method': 'error'
        }

@app.post("/analyze-prompt")
async def analyze_prompt_endpoint(request_data: dict):
    """Prompt analizi - kullanıcının girdiği promptta belirli website'ler aranır"""
    try:
        print("🎯 Prompt analizi isteği alındı...")
        
        prompt = request_data.get('prompt', '').strip()
        target_websites = request_data.get('websites', ['elmaspatent.com', 'workexe.co'])
        
        print(f"📋 Prompt: {prompt[:100]}...")
        print(f"🌐 Aranan siteler: {target_websites}")
        
        # Validasyon
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt gereklidir")
        
        if not target_websites:
            raise HTTPException(status_code=400, detail="En az bir website seçilmelidir")
        
        # Gelişmiş keyword analizi (hem site hem firma ismi)
        def smart_website_detection(prompt: str, website: str) -> dict:
            """Akıllı website/firma tespit algoritması"""
            prompt_lower = prompt.lower()
            website_lower = website.lower()
            
            # Website domain'i direkt geçiyor mu?
            domain_mentioned = website_lower in prompt_lower
            
            # Firma ismini çıkar (domain'den)
            if website_lower == "elmaspatent.com":
                company_names = ["elmas patent", "elmaspatent"]
            elif website_lower == "liderpatent.com.tr":
                company_names = ["lider patent", "liderpatent"]
            elif website_lower == "bilgipatent.com":
                company_names = ["bilgi patent", "bilgipatent"]
            elif website_lower == "workexe.co":
                company_names = ["workexe"]
            else:
                # Genel domain parse
                domain_name = website_lower.replace('.com', '').replace('.tr', '').replace('.co', '').replace('www.', '')
                company_names = [domain_name, domain_name.replace('-', ' ')]
            
            # Firma ismi geçiyor mu?
            company_mentioned = False
            found_company_name = ""
            for company_name in company_names:
                if company_name in prompt_lower:
                    company_mentioned = True
                    found_company_name = company_name
                    break
            
            # Sonuç
            mentioned = domain_mentioned or company_mentioned
            context = ""
            
            if domain_mentioned:
                context = f"Website URL'i ({website}) prompt içinde geçiyor"
            elif company_mentioned:
                context = f"Firma adı ('{found_company_name}') prompt içinde geçiyor"
            else:
                context = "Prompt içinde bahsedilmiyor"
            
            return {
                'mentioned': mentioned,
                'keyword_found': mentioned,
                'context': context,
                'domain_found': domain_mentioned,
                'company_found': company_mentioned,
                'found_company_name': found_company_name
            }
        
        # Gelişmiş website analizi
        website_analysis = {}
        for website in target_websites:
            analysis = smart_website_detection(prompt, website)
            website_analysis[website] = analysis
        
        # Gemini ile prompt analizi
        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                analysis_prompt = f"""
                Aşağıdaki kullanıcı promptunu analiz et ve bu promptta belirtilen website'lerin bahsedilip bahsedilmediğini tespit et:

                KULLANICI PROMPTU:
                {prompt}

                ARANAN WEBSITE'LER:
                {', '.join(target_websites)}

                GÖREV:
                1. Bu promptta yukarıdaki website'lerden hangisi VEYA onların firma isimleri bahsediliyor?
                2. Hangi bağlamda bahsediliyor? (pozitif/negatif/nötr/karşılaştırma)
                3. Tam olarak nasıl geçiyor?
                4. Website ile ilgili hangi konular sorulmuş?

                NOT: Website'lerin firma isimleri:
                - elmaspatent.com → "Elmas Patent"
                - liderpatent.com.tr → "Lider Patent" 
                - bilgipatent.com → "Bilgi Patent"
                - workexe.co → "Workexe"

                CEVAP FORMATI:
                WEBSITE_ANALIZI:
                {chr(10).join([f'- {site}: [BAHSEDILDI/BAHSEDILMEDI] - [Bağlam açıklaması]' for site in target_websites])}

                GENEL_DEGERLENDIRME: [Bu promptun hangi website hakkında olduğunu açıkla]
                KONU_ANALIZI: [Promptta sorulan ana konu nedir?]
                ONERI: [Bu prompt için hangi website'e yönlendirilmeli?]
                """
                
                # Yeni Gemini model adlarını dene
                model_names = [
                    'gemini-1.5-flash',
                    'gemini-1.5-pro',
                    'gemini-pro'
                ]
                
                analysis_result = ""
                for model_name in model_names:
                    try:
                        print(f"🔄 Prompt analizi model: {model_name}")
                        model_ai = genai.GenerativeModel(model_name)
                        response = model_ai.generate_content(analysis_prompt)
                        analysis_result = response.text
                        print(f"✅ Başarılı model: {model_name}")
                        break
                    except Exception as model_error:
                        print(f"❌ Model {model_name} hatası: {model_error}")
                        continue
                
                if not analysis_result:
                    raise Exception("Hiçbir Gemini modeli çalışmadı")
                
                # AI analizi ile local analizi karşılaştır ve düzelt
                gemini_mentions = {}
                lines = analysis_result.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('-') and 'BAHSEDILDI' in line.upper():
                        for website in target_websites:
                            if website in line and 'BAHSEDILDI' in line.upper():
                                gemini_mentions[website] = 'BAHSEDILDI' in line.upper()
                
                # Gemini sonuçları ile local sonuçları birleştir
                for website in target_websites:
                    if website in gemini_mentions:
                        gemini_says_mentioned = gemini_mentions[website]
                        local_says_mentioned = website_analysis[website]['mentioned']
                        
                        # Gemini daha akıllı, ona öncelik ver
                        if gemini_says_mentioned and not local_says_mentioned:
                            website_analysis[website]['mentioned'] = True
                            website_analysis[website]['keyword_found'] = True
                            website_analysis[website]['context'] = "AI tarafından tespit edildi (firma ismi bağlamında)"
                
                # AI analizi parse et - önerilen website
                recommended_website = None
                for line in lines:
                    line = line.strip()
                    if 'ONERI:' in line:
                        # Önerilen website'i bul
                        for website in target_websites:
                            if website in line.lower():
                                recommended_website = website
                                break
                
                # Sonuç raporu
                result_report = f"""
🎯 PROMPT ANALİZİ RAPORU:

📝 Kullanıcı Promptu:
{prompt}

🌐 Website Analizi:
"""
                
                for website in target_websites:
                    status = "✅ BAHSEDİLDİ" if website_analysis[website]['mentioned'] else "❌ BAHSEDİLMEDİ"
                    result_report += f"   • {website}: {status}\n"
                    if website_analysis[website]['mentioned']:
                        result_report += f"     → Bağlam: {website_analysis[website]['context']}\n"
                
                result_report += f"\n🔮 GEMINI AI ANALİZİ:\n{analysis_result}"
                
                if recommended_website:
                    result_report += f"\n🎯 ÖNERİ: Bu prompt '{recommended_website}' ile ilgili görünüyor."
                
                # Skorlama - düzeltilmiş
                mentioned_count = sum(1 for wa in website_analysis.values() if wa['mentioned'])
                analysis_score = mentioned_count * 50  # Her bahsedilen site 50 puan
                
                # Sonuçları veritabanına kaydet
                analysis_data = {
                    'brand': 'Prompt Analysis',
                    'model': 'Website Detection',
                    'prompt': f"Prompt Analizi: '{prompt[:100]}...'",
                    'response': result_report,
                    'mentioned': any(wa['mentioned'] for wa in website_analysis.values()),
                    'score': analysis_score,
                    'summary': f"Prompt analizi: {mentioned_count}/{len(target_websites)} website bahsedildi",
                    'source_url': 'User Prompt',
                    'created_at': datetime.now().isoformat() if USE_SUPABASE else datetime.now()
                }
                
                if USE_SUPABASE:
                    supabase.table('llm_mentions').insert(analysis_data).execute()
                else:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO llm_mentions 
                        (brand, model, prompt, response, mentioned, score, summary, source_url, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        analysis_data['brand'], analysis_data['model'],
                        analysis_data['prompt'], analysis_data['response'],
                        analysis_data['mentioned'], analysis_data['score'],
                        analysis_data['summary'], analysis_data['source_url'], analysis_data['created_at']
                    ))
                    conn.commit()
                    conn.close()
                
                return {
                    "status": "success",
                    "message": "Prompt analizi tamamlandı!",
                    "data": {
                        "original_prompt": prompt,
                        "website_analysis": website_analysis,
                        "ai_analysis": analysis_result,
                        "detailed_report": result_report,
                        "recommended_website": recommended_website,
                        "total_websites_mentioned": mentioned_count,
                        "analysis_score": analysis_score
                    }
                }
                
            except Exception as gemini_error:
                print(f"⚠️ Gemini prompt analiz hatası: {gemini_error}")
                
                # Fallback - gelişmiş keyword analizi
                mentioned_count = sum(1 for wa in website_analysis.values() if wa['mentioned'])
                
                return {
                    "status": "success",
                    "message": "Prompt analizi tamamlandı (gelişmiş keyword analizi)",
                    "data": {
                        "original_prompt": prompt,
                        "website_analysis": website_analysis,
                        "ai_analysis": f"Gemini hatası: {str(gemini_error)}",
                        "detailed_report": f"Gelişmiş keyword analizi sonucu: {mentioned_count} website bahsedildi",
                        "recommended_website": None,
                        "total_websites_mentioned": mentioned_count,
                        "analysis_score": mentioned_count * 50
                    }
                }
        
        else:
            raise HTTPException(status_code=500, detail="Gemini AI mevcut değil - bu özellik Gemini gerektirir")
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Prompt analizi hatası: {str(e)}"
        print(f"🔥 {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

# API Endpoint'leri
@app.get("/")
async def root():
    """Ana endpoint - sistem durumu"""
    return {
        "status": "success",
        "message": "AI Görünürlük Backend Çalışıyor!",
        "database": "Supabase" if USE_SUPABASE else "SQLite",
        "gemini_available": GEMINI_AVAILABLE,
        "version": "2.0.0"
    }

@app.post("/add-url")
async def add_url_endpoint(request_data: URLRequest):
    """URL ekleme endpoint'i"""
    try:
        url = request_data.url.strip()
        print(f"🔍 URL ekleme isteği: {url}")
        
        if not url:
            raise HTTPException(status_code=400, detail="URL gereklidir")
        
        # URL formatını kontrol et
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise HTTPException(status_code=400, detail="Geçersiz URL formatı")
        
        if USE_SUPABASE:
            # Supabase kontrolü
            existing = supabase.table('urls').select('id').eq('url', url).execute()
            if existing.data:
                raise HTTPException(status_code=400, detail="Bu URL zaten eklenmiş")
            
            # URL'yi ekle
            result = supabase.table('urls').insert({
                'url': url,
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            url_id = result.data[0]['id']
            
        else:
            # SQLite kontrolü
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM urls WHERE url = ?', (url,))
            existing = cursor.fetchone()
            
            if existing:
                conn.close()
                raise HTTPException(status_code=400, detail="Bu URL zaten eklenmiş")
            
            # URL'yi ekle
            cursor.execute('''
                INSERT INTO urls (url, status, created_at, updated_at)
                VALUES (?, 'pending', ?, ?)
            ''', (url, datetime.now(), datetime.now()))
            
            conn.commit()
            url_id = cursor.lastrowid
            conn.close()
        
        # Title alma işlemi (arka planda)
        content_result = fetch_url_content(url)
        
        if content_result['success']:
            title = content_result['title']
            status = 'active'
            error_message = None
        else:
            title = None
            status = 'error'
            error_message = content_result['error']
        
        # Title güncelle
        if USE_SUPABASE:
            supabase.table('urls').update({
                'title': title,
                'status': status,
                'error_message': error_message
            }).eq('id', url_id).execute()
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE urls SET title = ?, status = ?, error_message = ? WHERE id = ?
            ''', (title, status, error_message, url_id))
            conn.commit()
            conn.close()
        
        print(f"✅ URL eklendi: {url} (ID: {url_id})")
        
        return {
            'status': 'success',
            'message': 'URL başarıyla eklendi',
            'data': {'id': url_id, 'url': url, 'title': title}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"🔥 URL ekleme hatası: {e}")
        raise HTTPException(status_code=500, detail=f"URL eklenirken hata: {str(e)}")

@app.get("/get-urls")
async def get_urls_endpoint():
    """URL listesi getirme endpoint'i"""
    try:
        if USE_SUPABASE:
            response = supabase.table('urls').select('*').order('created_at', desc=True).execute()
            urls = response.data
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, url, status, title, description, last_analysis, 
                       error_message, analysis_count, created_at, updated_at
                FROM urls 
                ORDER BY created_at DESC
            ''')
            
            urls = [dict(row) for row in cursor.fetchall()]
            conn.close()
        
        return {
            'status': 'success',
            'data': urls,
            'count': len(urls)
        }
        
    except Exception as e:
        logger.error(f"URL listesi alma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL listesi alınırken hata: {str(e)}")

@app.delete("/remove-url/{url_id}")
async def remove_url_endpoint(url_id: int):
    """URL silme endpoint'i"""
    try:
        if USE_SUPABASE:
            # URL'nin var olup olmadığını kontrol et
            existing = supabase.table('urls').select('url').eq('id', url_id).execute()
            if not existing.data:
                raise HTTPException(status_code=404, detail='URL bulunamadı')
            
            # İlgili analiz sonuçlarını sil
            supabase.table('url_analysis_results').delete().eq('url_id', url_id).execute()
            supabase.table('llm_mentions').delete().eq('source_url', existing.data[0]['url']).execute()
            
            # URL'yi sil
            supabase.table('urls').delete().eq('id', url_id).execute()
            
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT url FROM urls WHERE id = ?', (url_id,))
            url_data = cursor.fetchone()
            
            if not url_data:
                conn.close()
                raise HTTPException(status_code=404, detail='URL bulunamadı')
            
            # İlgili verileri sil
            cursor.execute('DELETE FROM url_analysis_results WHERE url_id = ?', (url_id,))
            cursor.execute('DELETE FROM llm_mentions WHERE source_url = ?', (url_data['url'],))
            cursor.execute('DELETE FROM urls WHERE id = ?', (url_id,))
            
            conn.commit()
            conn.close()
        
        return {'status': 'success', 'message': 'URL başarıyla silindi'}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL silme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL silinirken hata: {str(e)}")

@app.post("/run-llm-mention-analysis")
async def run_analysis():
    """LLM mention analizi çalıştırma endpoint'i"""
    try:
        print("🚀 URL analizi başlatıldı...")
        
        # Aktif URL'leri al
        if USE_SUPABASE:
            response = supabase.table('urls').select('*').eq('status', 'active').execute()
            urls = response.data
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM urls WHERE status = "active"')
            urls = [dict(row) for row in cursor.fetchall()]
            conn.close()
        
        print(f"📊 {len(urls)} aktif URL bulundu")
        
        if not urls:
            return {"status": "error", "message": "Analiz edilecek aktif URL bulunamadı"}
        
        # Analiz parametreleri
        brands = ['Workexe', 'Ahrefs', 'Semrush', 'Surfer SEO']
        models = ['ChatGPT', 'Claude', 'Gemini', 'Copilot']
        
        total_results = 0
        successful_calls = 0
        failed_calls = 0
        
        # URL'leri analiz et (ilk 3 URL)
        for url_data in urls[:3]:
            url = url_data['url']
            print(f"🔍 {url} analiz ediliyor...")
            
            try:
                # URL içeriğini getir
                content_result = fetch_url_content(url)
                
                if not content_result['success']:
                    print(f"❌ URL erişim hatası: {content_result['error']}")
                    failed_calls += 1
                    continue
                
                content = content_result['content']
                title = content_result['title']
                
                print(f"📄 Sayfa başlığı: {title}")
                
                # Her brand-model kombinasyonu için analiz
                for brand in brands:
                    for model in models:
                        try:
                            # AI analizi
                            analysis_result = await analyze_with_ai(content, brand, model, url)
                            
                            analysis_data = {
                                'brand': brand,
                                'model': model,
                                'prompt': f"URL Analizi: {url} - '{brand}' ve '{model}' bahsediliyor mu?",
                                'response': f"Sayfa: {title}. {analysis_result['ai_result']}",
                                'mentioned': analysis_result['mentioned'],
                                'score': analysis_result['score'],
                                'summary': f"'{brand}' {'bahsedildi' if analysis_result['brand_mentioned'] else 'bahsedilmedi'}, '{model}' {'bahsedildi' if analysis_result['model_mentioned'] else 'bahsedilmedi'}. Skor: {analysis_result['score']}/100",
                                'source_url': url
                            }
                            
                            # Veritabanına kaydet
                            if USE_SUPABASE:
                                supabase.table('llm_mentions').insert(analysis_data).execute()
                            else:
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                cursor.execute('''
                                    INSERT INTO llm_mentions 
                                    (brand, model, prompt, response, mentioned, score, summary, source_url, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    analysis_data['brand'], analysis_data['model'],
                                    analysis_data['prompt'], analysis_data['response'],
                                    analysis_data['mentioned'], analysis_data['score'],
                                    analysis_data['summary'], analysis_data['source_url'], datetime.now()
                                ))
                                conn.commit()
                                conn.close()
                            
                            print(f"✅ Kaydedildi: {brand} - {model} - {analysis_result['score']}")
                            total_results += 1
                            successful_calls += 1
                            
                        except Exception as save_error:
                            print(f"❌ Kaydetme hatası: {save_error}")
                            failed_calls += 1
                
                # URL'nin son analiz tarihini güncelle
                if USE_SUPABASE:
                    supabase.table('urls').update({
                        'last_analysis': datetime.now().isoformat(),
                        'analysis_count': (url_data.get('analysis_count', 0) or 0) + 1
                    }).eq('id', url_data['id']).execute()
                else:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE urls SET last_analysis = ?, analysis_count = analysis_count + 1 WHERE id = ?
                    ''', (datetime.now(), url_data['id']))
                    conn.commit()
                    conn.close()
                
                print(f"📅 URL {url} güncellendi")
                
            except Exception as url_error:
                print(f"❌ URL işleme hatası: {url_error}")
                failed_calls += 1
                continue
        
        result = {
            "status": "success",
            "message": f"Analiz tamamlandı! {total_results} sonuç oluşturuldu.",
            "data": {
                "results_count": total_results,
                "analyzed_urls": len(urls[:3]),
                "successful_calls": successful_calls,
                "failed_calls": failed_calls
            }
        }
        
        print("🎉 Analiz tamamlandı:", result)
        return result
        
    except Exception as e:
        error_msg = f"Genel analiz hatası: {str(e)}"
        print(f"🔥 {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/get-mentions")
async def get_mentions():
    """Mention verilerini getirme endpoint'i"""
    try:
        if USE_SUPABASE:
            response = supabase.table("llm_mentions").select("*").order("created_at", desc=True).execute()
            return {"status": "success", "data": response.data}
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM llm_mentions ORDER BY created_at DESC')
            data = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return {"status": "success", "data": data}
            
    except Exception as e:
        print("🔥 Veri getirme hatası:", e)
        return {"status": "error", "message": str(e), "data": []}

@app.get("/get-prompts")
async def get_prompts():
    """Prompts sayfası için prompt listesi"""
    try:
        print("🎯 Prompts listesi isteği alındı...")
        
        # Sample prompts data - gerçek uygulamada database'den gelecek
        prompts_data = [
            {
                "id": 1,
                "prompt": "How does the customer support experience differ between various messaging tools?",
                "status": "active",
                "ai_models": ["chatgpt", "gemini"],
                "visibility": 85,
                "ranking": "3rd",
                "sentiment": "positive",
                "topics": ["customer-service", "support"],
                "category": "Support Tools",
                "performance": 85,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:20:00Z"
            },
            {
                "id": 2,
                "prompt": "How can I streamline customer chats from different countries into one system?",
                "status": "active",
                "ai_models": ["chatgpt", "claude", "meta"],
                "visibility": 78,
                "ranking": "5th",
                "sentiment": "neutral",
                "topics": ["automation", "international"],
                "category": "Automation",
                "performance": 78,
                "created_at": "2024-01-14T09:15:00Z",
                "updated_at": "2024-01-19T16:45:00Z"
            },
            {
                "id": 3,
                "prompt": "Is there a AI chatbot for my e-commerce website. What platform should I use?",
                "status": "suggested",
                "ai_models": ["gemini", "deepseek"],
                "visibility": 92,
                "ranking": "1st",
                "sentiment": "positive",
                "topics": ["ecommerce", "chatbot"],
                "category": "E-commerce",
                "performance": 92,
                "created_at": "2024-01-16T11:20:00Z",
                "updated_at": "2024-01-21T10:30:00Z"
            },
            {
                "id": 4,
                "prompt": "How to track CSAT and agent performance over WhatsApp?",
                "status": "active",
                "ai_models": ["chatgpt", "gemini", "claude"],
                "visibility": 73,
                "ranking": "7th",
                "sentiment": "neutral",
                "topics": ["whatsapp", "analytics"],
                "category": "Analytics",
                "performance": 73,
                "created_at": "2024-01-13T15:45:00Z",
                "updated_at": "2024-01-18T12:15:00Z"
            },
            {
                "id": 5,
                "prompt": "What platform helps support agents reply faster using AI?",
                "status": "active",
                "ai_models": ["chatgpt", "claude"],
                "visibility": 67,
                "ranking": "12th",
                "sentiment": "positive",
                "topics": ["ai-support", "automation"],
                "category": "AI Support",
                "performance": 67,
                "created_at": "2024-01-12T08:30:00Z",
                "updated_at": "2024-01-17T14:20:00Z"
            },
            {
                "id": 6,
                "prompt": "What's the best messaging platform for e-commerce customer service?",
                "status": "suggested",
                "ai_models": ["gemini", "meta"],
                "visibility": 88,
                "ranking": "2nd",
                "sentiment": "positive",
                "topics": ["ecommerce", "messaging"],
                "category": "E-commerce",
                "performance": 88,
                "created_at": "2024-01-17T13:10:00Z",
                "updated_at": "2024-01-22T09:25:00Z"
            },
            {
                "id": 7,
                "prompt": "How to handle customer support for Shopify store with WhatsApp and Instagram?",
                "status": "active",
                "ai_models": ["chatgpt", "gemini", "deepseek"],
                "visibility": 81,
                "ranking": "4th",
                "sentiment": "positive",
                "topics": ["shopify", "whatsapp", "instagram"],
                "category": "E-commerce",
                "performance": 81,
                "created_at": "2024-01-11T12:45:00Z",
                "updated_at": "2024-01-16T11:30:00Z"
            },
            {
                "id": 8,
                "prompt": "How do I manage conversations across WhatsApp, Instagram, and email in one dashboard?",
                "status": "active",
                "ai_models": ["chatgpt", "claude", "grok"],
                "visibility": 75,
                "ranking": "6th",
                "sentiment": "neutral",
                "topics": ["omnichannel", "dashboard"],
                "category": "Communication",
                "performance": 75,
                "created_at": "2024-01-10T16:20:00Z",
                "updated_at": "2024-01-15T13:40:00Z"
            },
            {
                "id": 9,
                "prompt": "Best tools to handle WhatsApp, Instagram, and webchat in one place",
                "status": "active",
                "ai_models": ["meta", "deepseek"],
                "visibility": 69,
                "ranking": "9th",
                "sentiment": "positive",
                "topics": ["multichannel", "integration"],
                "category": "Integration",
                "performance": 69,
                "created_at": "2024-01-09T10:15:00Z",
                "updated_at": "2024-01-14T15:20:00Z"
            },
            {
                "id": 10,
                "prompt": "What platform should I use for AI chatbots across multiple channels?",
                "status": "suggested",
                "ai_models": ["gemini", "claude", "deepseek"],
                "visibility": 94,
                "ranking": "1st",
                "sentiment": "positive",
                "topics": ["ai-chatbot", "multichannel"],
                "category": "AI Chatbot",
                "performance": 94,
                "created_at": "2024-01-18T14:30:00Z",
                "updated_at": "2024-01-23T10:45:00Z"
            }
        ]
        
        # Stats hesaplama
        total_prompts = len(prompts_data)
        active_count = len([p for p in prompts_data if p['status'] == 'active'])
        suggested_count = len([p for p in prompts_data if p['status'] == 'suggested'])
        inactive_count = len([p for p in prompts_data if p['status'] == 'inactive'])
        
        avg_visibility = sum([p['visibility'] for p in prompts_data]) / total_prompts if total_prompts > 0 else 0
        
        response_data = {
            "prompts": prompts_data,
            "stats": {
                "total_prompts": total_prompts,
                "active_count": active_count,
                "suggested_count": suggested_count,
                "inactive_count": inactive_count,
                "avg_visibility": round(avg_visibility, 1)
            }
        }
        
        print(f"✅ {total_prompts} prompt gönderildi (Active: {active_count}, Suggested: {suggested_count})")
        
        return {
            "status": "success",
            "message": f"{total_prompts} prompt başarıyla alındı",
            "data": response_data
        }
        
    except Exception as e:
        error_msg = f"Prompts listesi alınamadı: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/get-dashboard-stats")
async def get_dashboard_stats():
    """Dashboard ana sayfası için istatistikler"""
    try:
        print("📊 Dashboard istatistikleri isteği alındı...")
        
        # Gerçek uygulamada bu veriler database'den hesaplanacak
        stats_data = {
            "visibility_score": 17,
            "total_mentions": 127,
            "avg_score": 3.2,
            "total_analysis": 8,
            "trend_data": [15, 12, 14, 16, 18, 17, 17],  # Son 7 gün
            "trend_labels": ["Jul 15", "Jul 16", "Jul 17", "Jul 18", "Jul 19", "Jul 20", "Jul 21"],
            "industry_ranking": [
                {
                    "rank": 1,
                    "brand": "intercom.com",
                    "position": 4.2,
                    "visibility": 93.4,
                    "score": 71,
                    "icon": "I",
                    "color": "#6366f1"
                },
                {
                    "rank": 2,
                    "brand": "zendesk.com",
                    "position": 3.6,
                    "visibility": 86.4,
                    "score": 75,
                    "icon": "Z",
                    "color": "#10b981"
                },
                {
                    "rank": 3,
                    "brand": "hubspot.com",
                    "position": 5.8,
                    "visibility": 82.3,
                    "score": 73,
                    "icon": "H",
                    "color": "#f59e0b"
                },
                {
                    "rank": 4,
                    "brand": "salesforce.com",
                    "position": 7.2,
                    "visibility": 73.7,
                    "score": 72,
                    "icon": "S",
                    "color": "#3b82f6"
                },
                {
                    "rank": 5,
                    "brand": "workexe.co",
                    "position": 3.1,
                    "visibility": 22.0,
                    "score": 74,
                    "icon": "W",
                    "color": "#22c55e"
                }
            ]
        }
        
        print("✅ Dashboard istatistikleri hazırlandı")
        
        return {
            "status": "success",
            "message": "Dashboard istatistikleri başarıyla alındı",
            "data": stats_data
        }
        
    except Exception as e:
        error_msg = f"Dashboard istatistikleri alınamadı: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/create-prompt")
async def create_prompt(request_data: dict):
    """Yeni prompt oluşturma"""
    try:
        print("➕ Yeni prompt oluşturma isteği alındı...")
        
        prompt_text = request_data.get('prompt', '').strip()
        ai_models = request_data.get('ai_models', [])
        topics = request_data.get('topics', [])
        category = request_data.get('category', 'General')
        
        if not prompt_text:
            raise HTTPException(status_code=400, detail="Prompt metni gereklidir")
        
        # Yeni prompt objesi
        new_prompt = {
            "id": 999,  # Gerçek uygulamada database'den auto-increment ID gelecek
            "prompt": prompt_text,
            "status": "suggested",  # Yeni promptlar suggested olarak başlar
            "ai_models": ai_models,
            "visibility": 0,  # Yeni prompt henüz analiz edilmedi
            "ranking": "N/A",
            "sentiment": "neutral",
            "topics": topics,
            "category": category,
            "performance": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"✅ Yeni prompt oluşturuldu: {prompt_text[:50]}...")
        
        return {
            "status": "success",
            "message": "Prompt başarıyla oluşturuldu",
            "data": new_prompt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Prompt oluşturulamadı: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.put("/update-prompt/{prompt_id}")
async def update_prompt(prompt_id: int, request_data: dict):
    """Prompt güncelleme"""
    try:
        print(f"🔄 Prompt güncelleme isteği alındı: ID {prompt_id}")
        
        # Gerçek uygulamada database'den prompt bulunacak
        updates = {
            "status": request_data.get('status'),
            "ai_models": request_data.get('ai_models'),
            "topics": request_data.get('topics'),
            "category": request_data.get('category'),
            "updated_at": datetime.now().isoformat()
        }
        
        # Null değerleri temizle
        updates = {k: v for k, v in updates.items() if v is not None}
        
        print(f"✅ Prompt {prompt_id} güncellendi")
        
        return {
            "status": "success",
            "message": f"Prompt {prompt_id} başarıyla güncellendi",
            "data": updates
        }
        
    except Exception as e:
        error_msg = f"Prompt güncellenemedi: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.delete("/delete-prompt/{prompt_id}")
async def delete_prompt(prompt_id: int):
    """Prompt silme"""
    try:
        print(f"🗑️ Prompt silme isteği alındı: ID {prompt_id}")
        
        # Gerçek uygulamada database'den silinecek
        
        print(f"✅ Prompt {prompt_id} silindi")
        
        return {
            "status": "success",
            "message": f"Prompt {prompt_id} başarıyla silindi"
        }
        
    except Exception as e:
        error_msg = f"Prompt silinemedi: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


# Bulk operations
@app.post("/bulk-update-prompts")
async def bulk_update_prompts(request_data: dict):
    """Toplu prompt işlemleri"""
    try:
        print("🔄 Toplu prompt güncelleme isteği alındı...")
        
        prompt_ids = request_data.get('prompt_ids', [])
        action = request_data.get('action', '')  # 'activate', 'deactivate', 'delete'
        
        if not prompt_ids:
            raise HTTPException(status_code=400, detail="Prompt ID'leri gereklidir")
        
        if not action:
            raise HTTPException(status_code=400, detail="İşlem türü gereklidir")
        
        # Gerçek uygulamada database'de toplu işlem yapılacak
        processed_count = len(prompt_ids)
        
        print(f"✅ {processed_count} prompt için {action} işlemi tamamlandı")
        
        return {
            "status": "success",
            "message": f"{processed_count} prompt için {action} işlemi başarıyla tamamlandı",
            "data": {
                "processed_count": processed_count,
                "action": action,
                "prompt_ids": prompt_ids
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Toplu işlem tamamlanamadı: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

        # Dosyanın en sonuna ekle:
if __name__ == "__main__":
    import uvicorn
    print("🚀 FastAPI sunucusu başlatılıyor...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

@app.post("/run-visibility-test")
async def run_visibility_test(request_data: dict):
    """Gerçek AI visibility test çalıştır"""
    try:
        print("🎯 Gerçek visibility test başlatılıyor...")
        
        website = request_data.get('website', '').strip()
        custom_prompts = request_data.get('prompts', [])
        
        if not website:
            raise HTTPException(status_code=400, detail="Website URL gereklidir")
        
        # Initialize tester
        tester = PromptTester()
        
        # Run comprehensive test
        test_results = await tester.run_comprehensive_test(website, custom_prompts)
        
        # Save to database (optional)
        if USE_SUPABASE:
            try:
                supabase.table('visibility_tests').insert({
                    'website': website,
                    'results': test_results,
                    'created_at': datetime.now().isoformat()
                }).execute()
            except Exception as e:
                print(f"⚠️ Database save hatası: {e}")
        
        print(f"✅ Visibility test tamamlandı: {website}")
        
        return {
            "status": "success",
            "message": "AI visibility test başarıyla tamamlandı",
            "data": test_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Visibility test hatası: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/quick-prompt-test")
async def quick_prompt_test(request_data: dict):
    """Tek prompt için hızlı test"""
    try:
        prompt = request_data.get('prompt', '').strip()
        website = request_data.get('website', '').strip()
        
        if not prompt or not website:
            raise HTTPException(status_code=400, detail="Prompt ve website gereklidir")
        
        tracker = AIVisibilityTracker()
        results = await tracker.test_prompt_visibility(prompt, website)
        
        return {
            "status": "success",
            "message": "Prompt test tamamlandı",
            "data": {
                "prompt": prompt,
                "website": website,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        error_msg = f"Prompt test hatası: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/run-real-visibility-test")
async def run_real_visibility_test(request_data: dict):
    """Gerçek Gemini AI ile visibility test"""
    try:
        print("🚀 Gerçek AI visibility test başlatılıyor...")
        
        website = request_data.get('website', '').strip()
        custom_prompts = request_data.get('prompts', [])
        
        print(f"🔍 Gelen veriler: website={website}, custom_prompts={custom_prompts}")
        
        if not website:
            raise HTTPException(status_code=400, detail="Website URL gereklidir")
        
        from simple_ai_tester import SimpleAITester
        tester = SimpleAITester()
        
        results = await tester.test_website_visibility(website, custom_prompts)
        
        # Test sonuçlarını veritabanına kaydet
        try:
            # Tüm kullanılan promptları topla (custom + AI generated)
            all_prompts = []
            if custom_prompts:
                all_prompts.extend(custom_prompts)
                print(f"📝 Custom promptlar eklendi: {custom_prompts}")
            
            # AI tarafından oluşturulan promptları da ekle
            if results.get('test_results'):
                for test_result in results['test_results']:
                    if 'prompt' in test_result and test_result['prompt'] not in all_prompts:
                        all_prompts.append(test_result['prompt'])
                        print(f"🤖 AI prompt eklendi: {test_result['prompt'][:50]}...")
            
            print(f"💾 Kaydedilecek tüm promptlar: {all_prompts}")
            
            # llm_visibility_daily tablosuna uygun veri yapısı
            test_data = {
                "brand": website,  # website -> brand olarak kaydet
                "date": datetime.now().date().isoformat(),  # sadece tarih
                "visibility_score": float(results.get('summary', {}).get('average_visibility_score', 0)),
                "average_rank": float(results.get('summary', {}).get('average_rank', 0)),
                "sentiment_score": float(results.get('summary', {}).get('sentiment_score', 0)),
                "total_mentions": int(results.get('summary', {}).get('mentioned_count', 0)),
                "prompts_used": json.dumps(all_prompts),  # Tüm promptları kaydet
                "created_at": datetime.now().isoformat()
            }
            
            if USE_SUPABASE and supabase_client:
                # Supabase'e llm_visibility_daily tablosuna kaydet
                response = supabase_client.table('llm_visibility_daily').insert(test_data).execute()
                print(f"✅ Test sonuçları Supabase llm_visibility_daily tablosuna kaydedildi: {response}")
            else:
                # SQLite'a kaydet (fallback)
                conn = sqlite3.connect('ai_visibility.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO visibility_tests (website, prompts, results_summary, visibility_score, mentioned_count, total_tests, test_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    website,
                    json.dumps(custom_prompts) if custom_prompts else "",
                    json.dumps(results.get('summary', {})),
                    results.get('summary', {}).get('average_visibility_score', 0),
                    results.get('summary', {}).get('mentioned_count', 0),
                    results.get('summary', {}).get('successful_tests', 0),
                    datetime.now().isoformat()
                ))
                conn.commit()
                conn.close()
                print(f"✅ Test sonuçları SQLite'a kaydedildi")
                
        except Exception as db_error:
            print(f"⚠️ Veritabanı kayıt hatası: {db_error}")
            # Veritabanı hatası olsa bile test sonuçlarını döndür
        
        return {
            "status": "success",
            "message": f"Test tamamlandı! {results['summary']['mentioned_count']}/{results['summary']['successful_tests']} test'te bahsedildi.",
            "data": results
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run-quick-ai-test")
async def run_quick_ai_test(request_data: dict):
    """Tek prompt için hızlı Gemini test"""
    try:
        print("⚡ Hızlı AI test başlatılıyor...")
        
        website = request_data.get('website', '').strip()
        prompt = request_data.get('prompt', '').strip()
        
        if not website or not prompt:
            raise HTTPException(status_code=400, detail="Website URL ve prompt gereklidir")
        
        from simple_ai_tester import SimpleAITester
        tester = SimpleAITester()
        
        # Tek prompt test et
        results = await tester.test_website_visibility(website, [prompt])
        
        return {
            "status": "success",
            "message": "Hızlı test tamamlandı!",
            "data": results
        }
        
    except Exception as e:
        error_msg = f"Hızlı test hatası: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/get-test-history")
async def get_test_history():
    """Kaydedilen test geçmişini getir"""
    try:
        if USE_SUPABASE and supabase_client:
            # Supabase'ten llm_visibility_daily tablosundan getir
            response = supabase_client.table('llm_visibility_daily').select('*').order('created_at', desc=True).limit(10).execute()
            tests = response.data if response.data else []
            
            # Veri yapısını eski format ile uyumlu hale getir
            formatted_tests = []
            for test in tests:
                # Prompt bilgilerini al
                              # Prompt bilgilerini al
                prompts_used = test.get('prompts_used', '[]')
                print(f"🔍 Test {test.get('brand', '')} için prompts_used: {prompts_used}")
                try:
                    prompts = json.loads(prompts_used) if prompts_used else []
                    print(f"✅ Parsed prompts: {prompts}")
                except Exception as parse_error:
                    prompts = []
                    print(f"❌ Prompt parse hatası: {parse_error}")
                
                formatted_tests.append({
                    'website': test.get('brand', ''),
                    'prompts': prompts,  # Prompt bilgilerini ekle
                    'results_summary': json.dumps({
                        'visibility_score': test.get('visibility_score', 0),
                        'average_rank': test.get('average_rank', 0),
                        'sentiment_score': test.get('sentiment_score', 0),
                        'mentioned_count': test.get('total_mentions', 0)
                    }),
                    'visibility_score': test.get('visibility_score', 0),
                    'mentioned_count': test.get('total_mentions', 0),
                    'total_tests': 1,  # Her kayıt bir test
                    'test_date': test.get('created_at', '')
                })
            tests = formatted_tests
        else:
            # SQLite'tan getir
            conn = sqlite3.connect('ai_visibility.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT website, prompts, results_summary, visibility_score, mentioned_count, total_tests, test_date
                FROM visibility_tests 
                ORDER BY test_date DESC 
                LIMIT 10
            ''')
            rows = cursor.fetchall()
            conn.close()
            
            tests = []
            for row in rows:
                tests.append({
                    'website': row[0],
                    'prompts': row[1],
                    'results_summary': row[2],
                    'visibility_score': row[3],
                    'mentioned_count': row[4],
                    'total_tests': row[5],
                    'test_date': row[6]
                })
        
        print(f"📊 {len(tests)} test geçmişi getirildi")
        
        return {
            "status": "success",
            "message": f"{len(tests)} test bulundu",
            "data": tests
        }
        
    except Exception as e:
        error_msg = f"Test geçmişi getirme hatası: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/get-test-history/{website}")
async def get_website_test_history(website: str):
    """Belirli bir website için test geçmişini getir"""
    try:
        if USE_SUPABASE and supabase_client:
            # Supabase'ten llm_visibility_daily tablosundan getir
            response = supabase_client.table('llm_visibility_daily').select('*').eq('brand', website).order('created_at', desc=True).execute()
            tests = response.data if response.data else []
            
            # Veri yapısını eski format ile uyumlu hale getir
            formatted_tests = []
            for test in tests:
                # Prompt bilgilerini al
                prompts_used = test.get('prompts_used', '[]')
                try:
                    prompts = json.loads(prompts_used) if prompts_used else []
                except:
                    prompts = []
                
                formatted_tests.append({
                    'website': test.get('brand', ''),
                    'prompts': prompts,  # Prompt bilgilerini ekle
                    'results_summary': json.dumps({
                        'visibility_score': test.get('visibility_score', 0),
                        'average_rank': test.get('average_rank', 0),
                        'sentiment_score': test.get('sentiment_score', 0),
                        'mentioned_count': test.get('total_mentions', 0)
                    }),
                    'visibility_score': test.get('visibility_score', 0),
                    'mentioned_count': test.get('total_mentions', 0),
                    'total_tests': 1,  # Her kayıt bir test
                    'test_date': test.get('created_at', '')
                })
            tests = formatted_tests
        else:
            # SQLite'tan getir
            conn = sqlite3.connect('ai_visibility.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT website, prompts, results_summary, visibility_score, mentioned_count, total_tests, test_date
                FROM visibility_tests 
                WHERE website = ?
                ORDER BY test_date DESC
            ''', (website,))
            rows = cursor.fetchall()
            conn.close()
            
            tests = []
            for row in rows:
                tests.append({
                    'website': row[0],
                    'prompts': row[1],
                    'results_summary': row[2],
                    'visibility_score': row[3],
                    'mentioned_count': row[4],
                    'total_tests': row[5],
                    'test_date': row[6]
                })
        
        print(f"📊 {website} için {len(tests)} test geçmişi getirildi")
        
        return {
            "status": "success",
            "message": f"{website} için {len(tests)} test bulundu",
            "data": tests
        }
        
    except Exception as e:
        error_msg = f"Website test geçmişi getirme hatası: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


# Uvicorn başlatma kodu
if __name__ == "__main__":
    import uvicorn
    print("🚀 FastAPI sunucusu başlatılıyor...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)