import requests
import json

def test_seo_comparison_prompt():
    """SEO karşılaştırma prompt testi"""
    
    url = "http://localhost:8000/analyze-prompt"
    data = {
        "prompt": "Workexe vs Ahrefs hangisi daha iyi SEO analizi yapıyor?",
        "websites": ["workexe.co", "ahrefs.com", "semrush.com"]
    }
    
    try:
        print("🔍 SEO KARŞILAŞTIRMA PROMPTU ANALİZİ...")
        print(f"📋 Prompt: {data['prompt']}")
        print(f"🌐 Test edilecek siteler: {', '.join(data['websites'])}")
        print()
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            
            print("=== WORKEXE VS AHREFS KARŞILAŞTIRMA ANALİZİ ===")
            print(f"✅ Status: {result['status']}")
            print(f"📝 Prompt: {result['data']['original_prompt']}")
            print(f"📊 Bahsedilen Website: {result['data']['total_websites_mentioned']}")
            print(f"🎯 Analiz Skoru: {result['data']['analysis_score']}/150")
            print(f"💡 Önerilen Site: {result['data'].get('recommended_website', 'Yok')}")
            print()
            
            print("🌐 WEBSITE ANALİZİ:")
            for website, analysis in result['data']['website_analysis'].items():
                status = "✅ BAHSEDİLDİ" if analysis['mentioned'] else "❌ BAHSEDİLMEDİ"
                print(f"   📍 {website}: {status}")
                if analysis['mentioned']:
                    print(f"     → Bağlam: {analysis['context']}")
                    print(f"     → Company Found: {analysis.get('company_found', 'N/A')}")
                    print(f"     → Found Company Name: '{analysis.get('found_company_name', 'N/A')}'")
            print()
            
            print("🔮 GEMINI AI DETAYLI ANALİZİ:")
            print(result['data']['ai_analysis'])
            print()
            
            print("📋 DETAYLI RAPOR:")
            print(result['data']['detailed_report'])
            
        else:
            print(f"❌ HTTP Hatası: {response.status_code}")
            print(f"Hata mesajı: {response.text}")
    
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    test_seo_comparison_prompt()