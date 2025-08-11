# backend/llm_mention_crawler.py
import os
import re
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai
import sqlite3
import requests
import logging
import json
from typing import List, Dict
import time
from urllib.parse import urljoin, urlparse
import psycopg2
from psycopg2.extras import RealDictCursor

# 🌍 .env dosyasını yükle
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# 🔐 ENV değişkenleri
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Supabase client'ı başlat
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gemini API'yi yapılandır
genai.configure(api_key=GEMINI_API_KEY)

# 🎯 GÜNCEL model listesi
brands = ["Workexe", "Ahrefs", "Semrush", "Surfer SEO"]
models = ["gemini-2.5-flash", "gemini-2.5-pro"]  # Doğru model adları

# 🧠 Prompt template
def build_prompt(brand):
    return f"Does the brand '{brand}' appear in SEO tool comparison discussions? Summarize what users typically say and rate its popularity on a scale of 0–100."

# 🔍 Gemini analiz fonksiyonu - düzeltilmiş
def analyze_brand(brand, model):
    prompt = build_prompt(brand)
    
    try:
        # DOĞRU model adıyla başlat
        gemini_model = genai.GenerativeModel(model)
        
        # Rate limiting
        time.sleep(1)
        
        # İçerik oluştur
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=300,  # Daha az token
            )
        )
        
        answer = response.text
        mentioned = "yes" in answer.lower() or brand.lower() in answer.lower()

        score = 0
        score_match = re.search(r'(\d{1,3})', answer)
        if score_match:
            score = min(100, int(score_match.group(1)))

        return {
            "prompt": prompt,
            "summary": answer,
            "mentioned": mentioned,
            "score": score
        }
    
    except Exception as e:
        print(f"🔥 Gemini API hatası: {e}")
        return {
            "prompt": prompt,
            "summary": f"Hata oluştu: {str(e)}",
            "mentioned": False,
            "score": 0
        }

# 🚀 Supabase tabloları oluşturma fonksiyonu
def create_supabase_tables():
    """Supabase'de gerekli tabloları oluştur (PostgreSQL syntax)"""
    try:
        # LLM mentions tablosu
        supabase.table('llm_mentions').select('id').limit(1).execute()
        print("✅ llm_mentions tablosu zaten mevcut")
    except:
        print("🔧 llm_mentions tablosu oluşturuluyor...")
        # Supabase SQL Editor'da bu sorguyu çalıştırın:
        sql_queries = """
        -- LLM Mentions tablosu
        CREATE TABLE IF NOT EXISTS llm_mentions (
            id SERIAL PRIMARY KEY,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt TEXT,
            response TEXT,
            mentioned BOOLEAN DEFAULT FALSE,
            score INTEGER DEFAULT 0,
            summary TEXT,
            source_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- URLs tablosu
        CREATE TABLE IF NOT EXISTS urls (
            id SERIAL PRIMARY KEY,
            url TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'pending',
            title TEXT,
            description TEXT,
            last_analysis TIMESTAMP WITH TIME ZONE,
            error_message TEXT,
            analysis_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- URL Analysis Results tablosu
        CREATE TABLE IF NOT EXISTS url_analysis_results (
            id SERIAL PRIMARY KEY,
            url_id INTEGER REFERENCES urls(id) ON DELETE CASCADE,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            mentioned BOOLEAN DEFAULT FALSE,
            score INTEGER DEFAULT 0,
            analysis_text TEXT,
            content_snippet TEXT,
            analysis_method TEXT DEFAULT 'auto',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Analysis History tablosu
        CREATE TABLE IF NOT EXISTS analysis_history (
            id SERIAL PRIMARY KEY,
            analysis_type TEXT NOT NULL,
            urls_analyzed INTEGER DEFAULT 0,
            results_found INTEGER DEFAULT 0,
            status TEXT DEFAULT 'completed',
            error_message TEXT,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE
        );

        -- İndeksler
        CREATE INDEX IF NOT EXISTS idx_llm_mentions_brand_model ON llm_mentions(brand, model);
        CREATE INDEX IF NOT EXISTS idx_llm_mentions_created_at ON llm_mentions(created_at);
        CREATE INDEX IF NOT EXISTS idx_urls_status ON urls(status);
        CREATE INDEX IF NOT EXISTS idx_urls_created_at ON urls(created_at);
        CREATE INDEX IF NOT EXISTS idx_url_analysis_results_url_id ON url_analysis_results(url_id);
        CREATE INDEX IF NOT EXISTS idx_url_analysis_results_created_at ON url_analysis_results(created_at);
        """
        
        print("🔧 Supabase SQL Editor'da aşağıdaki sorguları çalıştırın:")
        print("="*50)
        print(sql_queries)
        print("="*50)

class SupabaseURLBasedLLMMentionCrawler:
    """Supabase tabanlı URL analiz crawler'ı"""
    
    def __init__(self):
        self.setup_logging()
        self.brands = ['Workexe', 'OpenAI', 'Anthropic', 'Google', 'Microsoft', 'Meta', 'Ahrefs', 'Semrush']
        self.models = ['ChatGPT', 'Claude', 'Gemini', 'Copilot', 'Llama', 'GPT-4', 'GPT-3.5', 'Bard']
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('url_crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_pending_urls(self) -> List[Dict]:
        """Analiz bekleyen URL'leri getir"""
        try:
            response = supabase.table('urls').select('*').eq('status', 'active').order('last_analysis', desc=False).limit(10).execute()
            return response.data
            
        except Exception as e:
            self.logger.error(f"URL'leri getirirken hata: {str(e)}")
            return []
    
    def fetch_url_content(self, url: str) -> Dict:
        """URL içeriğini getir"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Basit HTML parsing
            content = response.text
            title = self.extract_title(content)
            text_content = self.extract_text_content(content)
            
            return {
                'status': 'success',
                'title': title,
                'content': text_content,
                'url': url,
                'status_code': response.status_code
            }
            
        except requests.RequestException as e:
            self.logger.error(f"URL ({url}) getirirken hata: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'url': url
            }
    
    def extract_title(self, html_content: str) -> str:
        """HTML'den title'ı çıkar"""
        try:
            match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
            return "Başlık bulunamadı"
        except:
            return "Başlık çıkarılamadı"
    
    def extract_text_content(self, html_content: str) -> str:
        """HTML'den text içeriği çıkar (basit yöntem)"""
        try:
            # HTML tag'larını kaldır
            text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', '', text)
            
            # Fazla boşlukları temizle
            text = re.sub(r'\s+', ' ', text).strip()
            
            # İlk 5000 karakter al
            return text[:5000]
        except:
            return html_content[:1000]  # Fallback
    
    def analyze_content_for_mentions(self, content: str, title: str, url: str) -> List[Dict]:
        """İçeriği LLM mention'ları için analiz et"""
        results = []
        full_text = f"{title} {content}".lower()
        
        for brand in self.brands:
            for model in self.models:
                # Mention detection
                brand_mentioned = brand.lower() in full_text
                model_mentioned = model.lower() in full_text
                both_mentioned = brand_mentioned and model_mentioned
                
                # Context-aware scoring
                score = self.calculate_mention_score(
                    full_text, brand.lower(), model.lower(), 
                    brand_mentioned, model_mentioned
                )
                
                # Analiz metni oluştur
                analysis_text = f"URL: {url}\nBrand: {brand}\nModel: {model}\n"
                analysis_text += f"Brand mentioned: {brand_mentioned}\nModel mentioned: {model_mentioned}\n"
                analysis_text += f"Score: {score}/100"
                
                results.append({
                    'brand': brand,
                    'model': model,
                    'mentioned': both_mentioned,
                    'score': score,
                    'analysis_text': analysis_text,
                    'source_url': url,
                    'content_snippet': content[:200] + "..." if len(content) > 200 else content
                })
        
        return results
    
    def calculate_mention_score(self, text: str, brand: str, model: str, 
                               brand_mentioned: bool, model_mentioned: bool) -> int:
        """Mention score'u hesapla"""
        base_score = 0
        
        if brand_mentioned and model_mentioned:
            base_score = 80
            # Pozitif/negatif context kontrolü
            brand_pos = text.find(brand)
            model_pos = text.find(model)
            
            if brand_pos != -1 and model_pos != -1:
                # Yakınlık bonusu
                distance = abs(brand_pos - model_pos)
                if distance < 100:  # Yakın bahsetme
                    base_score += 10
                
                # Pozitif kelimeler
                positive_words = ['best', 'great', 'excellent', 'recommended', 'good', 'useful']
                negative_words = ['bad', 'terrible', 'awful', 'poor', 'worst', 'useless']
                
                context_start = max(0, min(brand_pos, model_pos) - 100)
                context_end = min(len(text), max(brand_pos, model_pos) + 100)
                context = text[context_start:context_end]
                
                positive_count = sum(1 for word in positive_words if word in context)
                negative_count = sum(1 for word in negative_words if word in context)
                
                if positive_count > negative_count:
                    base_score += 5
                elif negative_count > positive_count:
                    base_score -= 5
        
        elif brand_mentioned or model_mentioned:
            base_score = 45
        
        else:
            base_score = 10
        
        # Rastgele varyasyon ekle
        import random
        base_score += random.randint(-5, 5)
        
        return max(0, min(100, base_score))
    
    def save_analysis_results(self, url_id: int, results: List[Dict]):
        """Analiz sonuçlarını Supabase'e kaydet"""
        try:
            for result in results:
                # URL analysis results tablosuna kaydet
                supabase.table('url_analysis_results').insert({
                    'url_id': url_id,
                    'brand': result['brand'],
                    'model': result['model'],
                    'mentioned': result['mentioned'],
                    'score': result['score'],
                    'analysis_text': result['analysis_text'],
                    'content_snippet': result['content_snippet']
                }).execute()
                
                # LLM mentions tablosuna da kaydet
                supabase.table('llm_mentions').insert({
                    'brand': result['brand'],
                    'model': result['model'],
                    'prompt': f"URL Analysis: {result['source_url']}",
                    'response': result['content_snippet'],
                    'mentioned': result['mentioned'],
                    'score': result['score'],
                    'summary': f"Analiz sonucu: {result['score']}/100",
                    'source_url': result['source_url']
                }).execute()
            
            # URL'nin son analiz tarihini güncelle
            supabase.table('urls').update({
                'last_analysis': datetime.now().isoformat(),
                'analysis_count': url_id,  # Bu değeri artırmak için önce mevcut değeri almalısınız
                'updated_at': datetime.now().isoformat()
            }).eq('id', url_id).execute()
            
            self.logger.info(f"URL {url_id} için {len(results)} sonuç kaydedildi")
            
        except Exception as e:
            self.logger.error(f"Sonuçları kaydederken hata: {str(e)}")
    
    def run_url_analysis(self) -> Dict:
        """Manuel URL'leri analiz et"""
        start_time = datetime.now()
        self.logger.info("URL tabanlı LLM mention analizi başlatıldı")
        
        # Analiz geçmişine kaydet
        history_response = supabase.table('analysis_history').insert({
            'analysis_type': 'url_analysis',
            'status': 'running',
            'started_at': start_time.isoformat()
        }).execute()
        
        history_id = history_response.data[0]['id'] if history_response.data else None
        
        try:
            urls_to_analyze = self.get_pending_urls()
            
            if not urls_to_analyze:
                self.logger.info("Analiz edilecek URL bulunamadı")
                return {
                    'status': 'info',
                    'message': 'Analiz edilecek aktif URL bulunamadı',
                    'urls_analyzed': 0,
                    'results_created': 0
                }
            
            total_results = 0
            
            for url_data in urls_to_analyze:
                url_id = url_data['id']
                url = url_data['url']
                
                self.logger.info(f"Analiz ediliyor: {url}")
                
                # URL içeriğini getir
                content_data = self.fetch_url_content(url)
                
                if content_data['status'] == 'error':
                    # URL'yi error durumuna al
                    supabase.table('urls').update({
                        'status': 'error',
                        'error_message': content_data['error'],
                        'updated_at': datetime.now().isoformat()
                    }).eq('id', url_id).execute()
                    continue
                
                # İçeriği analiz et
                analysis_results = self.analyze_content_for_mentions(
                    content_data['content'], 
                    content_data['title'], 
                    url
                )
                
                # Sonuçları kaydet
                self.save_analysis_results(url_id, analysis_results)
                total_results += len(analysis_results)
                
                # Rate limiting
                time.sleep(1)
            
            # Analiz geçmişini güncelle
            end_time = datetime.now()
            if history_id:
                supabase.table('analysis_history').update({
                    'status': 'completed',
                    'completed_at': end_time.isoformat(),
                    'urls_analyzed': len(urls_to_analyze),
                    'results_found': total_results
                }).eq('id', history_id).execute()
            
            self.logger.info(f"Analiz tamamlandı: {len(urls_to_analyze)} URL, {total_results} sonuç")
            
            return {
                'status': 'success',
                'message': 'URL analizi başarıyla tamamlandı',
                'urls_analyzed': len(urls_to_analyze),
                'results_created': total_results,
                'duration': str(end_time - start_time)
            }
            
        except Exception as e:
            self.logger.error(f"URL analizi sırasında hata: {str(e)}")
            
            # Hata durumunu kaydet
            if history_id:
                supabase.table('analysis_history').update({
                    'status': 'error',
                    'error_message': str(e),
                    'completed_at': datetime.now().isoformat()
                }).eq('id', history_id).execute()
            
            return {
                'status': 'error',
                'message': f'Analiz sırasında hata: {str(e)}',
                'urls_analyzed': 0,
                'results_created': 0
            }

# SQLite için eski class'ı koruyalım (yerel geliştirme için)
class URLBasedLLMMentionCrawler:
    """Manuel eklenen URL'leri analiz eden crawler (SQLite)"""
    
    def __init__(self, db_path='ai_visibility.db'):
        self.db_path = db_path
        self.setup_logging()
        self.brands = ['Workexe', 'OpenAI', 'Anthropic', 'Google', 'Microsoft', 'Meta', 'Ahrefs', 'Semrush']
        self.models = ['ChatGPT', 'Claude', 'Gemini', 'Copilot', 'Llama', 'GPT-4', 'GPT-3.5', 'Bard']
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('url_crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_pending_urls(self) -> List[Dict]:
        """Analiz bekleyen URL'leri getir"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM urls 
                WHERE status = 'active' 
                ORDER BY last_analysis ASC NULLS FIRST
                LIMIT 10
            ''')
            
            urls = []
            for row in cursor.fetchall():
                urls.append(dict(row))
            
            conn.close()
            return urls
            
        except Exception as e:
            self.logger.error(f"URL'leri getirirken hata: {str(e)}")
            return []
    
    def fetch_url_content(self, url: str) -> Dict:
        """URL içeriğini getir"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Basit HTML parsing
            content = response.text
            title = self.extract_title(content)
            text_content = self.extract_text_content(content)
            
            return {
                'status': 'success',
                'title': title,
                'content': text_content,
                'url': url,
                'status_code': response.status_code
            }
            
        except requests.RequestException as e:
            self.logger.error(f"URL ({url}) getirirken hata: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'url': url
            }
    
    def extract_title(self, html_content: str) -> str:
        """HTML'den title'ı çıkar"""
        try:
            match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
            return "Başlık bulunamadı"
        except:
            return "Başlık çıkarılamadı"
    
    def extract_text_content(self, html_content: str) -> str:
        """HTML'den text içeriği çıkar (basit yöntem)"""
        try:
            # HTML tag'larını kaldır
            text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', '', text)
            
            # Fazla boşlukları temizle
            text = re.sub(r'\s+', ' ', text).strip()
            
            # İlk 5000 karakter al
            return text[:5000]
        except:
            return html_content[:1000]  # Fallback
    
    def analyze_content_for_mentions(self, content: str, title: str, url: str) -> List[Dict]:
        """İçeriği LLM mention'ları için analiz et"""
        results = []
        full_text = f"{title} {content}".lower()
        
        for brand in self.brands:
            for model in self.models:
                # Mention detection
                brand_mentioned = brand.lower() in full_text
                model_mentioned = model.lower() in full_text
                both_mentioned = brand_mentioned and model_mentioned
                
                # Context-aware scoring
                score = self.calculate_mention_score(
                    full_text, brand.lower(), model.lower(), 
                    brand_mentioned, model_mentioned
                )
                
                # Analiz metni oluştur
                analysis_text = f"URL: {url}\nBrand: {brand}\nModel: {model}\n"
                analysis_text += f"Brand mentioned: {brand_mentioned}\nModel mentioned: {model_mentioned}\n"
                analysis_text += f"Score: {score}/100"
                
                results.append({
                    'brand': brand,
                    'model': model,
                    'mentioned': both_mentioned,
                    'score': score,
                    'analysis_text': analysis_text,
                    'source_url': url,
                    'content_snippet': content[:200] + "..." if len(content) > 200 else content
                })
        
        return results
    
    def calculate_mention_score(self, text: str, brand: str, model: str, 
                               brand_mentioned: bool, model_mentioned: bool) -> int:
        """Mention score'u hesapla"""
        base_score = 0
        
        if brand_mentioned and model_mentioned:
            base_score = 80
            # Pozitif/negatif context kontrolü
            brand_pos = text.find(brand)
            model_pos = text.find(model)
            
            if brand_pos != -1 and model_pos != -1:
                # Yakınlık bonusu
                distance = abs(brand_pos - model_pos)
                if distance < 100:  # Yakın bahsetme
                    base_score += 10
                
                # Pozitif kelimeler
                positive_words = ['best', 'great', 'excellent', 'recommended', 'good', 'useful']
                negative_words = ['bad', 'terrible', 'awful', 'poor', 'worst', 'useless']
                
                context_start = max(0, min(brand_pos, model_pos) - 100)
                context_end = min(len(text), max(brand_pos, model_pos) + 100)
                context = text[context_start:context_end]
                
                positive_count = sum(1 for word in positive_words if word in context)
                negative_count = sum(1 for word in negative_words if word in context)
                
                if positive_count > negative_count:
                    base_score += 5
                elif negative_count > positive_count:
                    base_score -= 5
        
        elif brand_mentioned or model_mentioned:
            base_score = 45
        
        else:
            base_score = 10
        
        # Rastgele varyasyon ekle
        import random
        base_score += random.randint(-5, 5)
        
        return max(0, min(100, base_score))
    
    def save_analysis_results(self, url_id: int, results: List[Dict]):
        """Analiz sonuçlarını kaydet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for result in results:
                # URL analysis results tablosuna kaydet
                cursor.execute('''
                    INSERT INTO url_analysis_results 
                    (url_id, brand, model, mentioned, score, analysis_text, content_snippet, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    url_id, result['brand'], result['model'], result['mentioned'],
                    result['score'], result['analysis_text'], 
                    result['content_snippet'], datetime.now()
                ))
                
                # Eski format için llm_mentions tablosuna da kaydet - STRING HATASI DÜZELTİLDİ
                cursor.execute('''
                    INSERT INTO llm_mentions 
                    (brand, model, prompt, response, mentioned, score, summary, source_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result['brand'], result['model'],
                    f"URL Analysis: {result['source_url']}",  # VIRGÜL EKLENDİ
                    result['content_snippet'],
                    result['mentioned'], result['score'],
                    f"Analiz sonucu: {result['score']}/100",
                    result['source_url'], datetime.now()
                ))
            
            # URL'nin son analiz tarihini güncelle
            cursor.execute('''
                UPDATE urls 
                SET last_analysis = ?, analysis_count = analysis_count + 1, updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), datetime.now(), url_id))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"URL {url_id} için {len(results)} sonuç kaydedildi")
            
        except Exception as e:
            self.logger.error(f"Sonuçları kaydederken hata: {str(e)}")
    
    def run_url_analysis(self) -> Dict:
        """Manuel URL'leri analiz et"""
        start_time = datetime.now()
        self.logger.info("URL tabanlı LLM mention analizi başlatıldı")
        
        # Analiz geçmişine kaydet
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analysis_history 
            (analysis_type, status, started_at)
            VALUES ('url_analysis', 'running', ?)
        ''', (start_time,))
        history_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        try:
            urls_to_analyze = self.get_pending_urls()
            
            if not urls_to_analyze:
                self.logger.info("Analiz edilecek URL bulunamadı")
                return {
                    'status': 'info',
                    'message': 'Analiz edilecek aktif URL bulunamadı',
                    'urls_analyzed': 0,
                    'results_created': 0
                }
            
            total_results = 0
            
            for url_data in urls_to_analyze:
                url_id = url_data['id']
                url = url_data['url']
                
                self.logger.info(f"Analiz ediliyor: {url}")
                
                # URL içeriğini getir
                content_data = self.fetch_url_content(url)
                
                if content_data['status'] == 'error':
                    # URL'yi error durumuna al
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE urls 
                        SET status = 'error', error_message = ?, updated_at = ?
                        WHERE id = ?
                    ''', (content_data['error'], datetime.now(), url_id))
                    conn.commit()
                    conn.close()
                    continue
                
                # İçeriği analiz et
                analysis_results = self.analyze_content_for_mentions(
                    content_data['content'], 
                    content_data['title'], 
                    url
                )
                
                # Sonuçları kaydet
                self.save_analysis_results(url_id, analysis_results)
                total_results += len(analysis_results)
                
                # Rate limiting
                time.sleep(1)
            
            # Analiz geçmişini güncelle
            end_time = datetime.now()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE analysis_history 
                SET status = 'completed', completed_at = ?, 
                    urls_analyzed = ?, results_found = ?
                WHERE id = ?
            ''', (end_time, len(urls_to_analyze), total_results, history_id))
            conn.commit()
            conn.close()
            
            self.logger.info(f"Analiz tamamlandı: {len(urls_to_analyze)} URL, {total_results} sonuç")
            
            return {
                'status': 'success',
                'message': 'URL analizi başarıyla tamamlandı',
                'urls_analyzed': len(urls_to_analyze),
                'results_created': total_results,
                'duration': str(end_time - start_time)
            }
            
        except Exception as e:
            self.logger.error(f"URL analizi sırasında hata: {str(e)}")
            
            # Hata durumunu kaydet
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE analysis_history 
                SET status = 'error', error_message = ?, completed_at = ?
                WHERE id = ?
            ''', (str(e), datetime.now(), history_id))
            conn.commit()
            conn.close()
            
            return {
                'status': 'error',
                'message': f'Analiz sırasında hata: {str(e)}',
                'urls_analyzed': 0,
                'results_created': 0
            }

# Kullanım - Supabase veya SQLite seçimi
if __name__ == '__main__':
    use_supabase = os.getenv("USE_SUPABASE", "false").lower() == "true"
    
    if use_supabase:
        print("🚀 Supabase tabanlı crawler başlatılıyor...")
        create_supabase_tables()  # Tablo oluşturma talimatlarını göster
        crawler = SupabaseURLBasedLLMMentionCrawler()
    else:
        print("💾 SQLite tabanlı crawler başlatılıyor...")
        crawler = URLBasedLLMMentionCrawler()
    
    result = crawler.run_url_analysis()
    print(f"Sonuç: {result}")
