import json
from datetime import datetime, date
import uuid
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

class PromptManager:
    def __init__(self):
        self.supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        
    def create_default_templates(self):
        """Varsayılan prompt şablonları oluştur"""
        templates = [
            {
                "name": "SEO Araç Karşılaştırması",
                "prompt": "SEO araçları karşılaştırıldığında '{brand}' nasıl konumlanıyor? Kullanıcılar genelde ne söylüyor ve 0-100 arası popülerlik puanı ver.",
                "category": "comparison"
            },
            {
                "name": "Genel Marka Farkındalığı", 
                "prompt": "'{brand}' hakkında genel olarak ne düşünülüyor? Güçlü yanları, zayıf yanları ve 0-100 arası bir skor ver.",
                "category": "awareness"
            },
            {
                "name": "Rekabet Analizi",
                "prompt": "SEO araçları arasında '{brand}' rakiplerine göre nasıl performans gösteriyor? 0-100 puan ver.",
                "category": "competition"
            }
        ]
        
        for template in templates:
            try:
                self.supabase.table("prompt_templates").insert(template).execute()
                print(f"✅ Template eklendi: {template['name']}")
            except Exception as e:
                print(f"❌ Template ekleme hatası: {e}")
                
    def get_active_templates(self):
        """Aktif template'ları getir"""
        try:
            response = self.supabase.table("prompt_templates").select("*").eq("active", True).execute()
            return response.data
        except Exception as e:
            print(f"❌ Template getirme hatası: {e}")
            return []
            
    def save_trend_data(self, brand, visibility_score, mention_count, query_count):
        """Trend verisi kaydet"""
        try:
            data = {
                "brand": brand,
                "date": date.today().isoformat(),
                "visibility_score": visibility_score,
                "mention_count": mention_count,
                "query_count": query_count
            }
            return self.supabase.table("brand_trends").insert(data).execute()
        except Exception as e:
            print(f"❌ Trend kaydetme hatası: {e}")
            return None

# Test fonksiyonu
if __name__ == "__main__":
    pm = PromptManager()
    pm.create_default_templates()