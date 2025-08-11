# 🤖 LLM Tracker - AI Visibility Analytics

Modern AI modellerinde web sitelerinin görünürlük analizini yapan kapsamlı araç. Gerçek AI modellerini (Gemini, ChatGPT, Claude) kullanarak marka bahsedilme oranlarını test eder.

![AI Tracker Dashboard](https://via.placeholder.com/800x400/4f46e5/ffffff?text=AI+Visibility+Analytics)

## ✨ Özellikler

### 🚀 **Real AI Testing**
- **Gemini AI Integration** - Google'ın Gemini modelini kullanarak gerçek testler
- **Multi-prompt Analysis** - 10 farklı prompt ile otomatik test
- **Custom Prompt Support** - Özel sorular ile targeted testing
- **Real-time Progress** - Anlık ilerleme takibi

### 📊 **Analytics Dashboard**
- **Modern Interface** - Responsive ve kullanıcı dostu tasarım
- **Visibility Scoring** - 0-100 arası detaylı puanlama sistemi
- **Sentiment Analysis** - Pozitif/negatif/nötr bağlam analizi
- **Ranking Detection** - AI cevaplarında sıralama tespiti
- **Competitive Analysis** - Rakip markaların karşılaştırılması

### 🛠️ **Analysis Tools**
- **Website Analysis** - Web sitesi içerik analizi
- **Prompt Analysis** - Kullanıcı prompt'larında marka tespiti
- **Trend Tracking** - Zaman içindeki değişimleri takip
- **Export Reports** - PDF/Excel rapor çıktısı

## 🛠️ Teknoloji Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Google Generative AI** - Gemini API entegrasyonu
- **Supabase** - Database ve authentication
- **Python 3.10+** - Core language

### Frontend
- **HTML5 + CSS3** - Modern responsive design
- **Vanilla JavaScript** - Native JS implementation
- **Chart.js** - Data visualization
- **Font Awesome** - Icons

### AI Models
- **Gemini Pro/Flash** - Google AI
- **OpenAI GPT** - ChatGPT integration (coming soon)
- **Claude** - Anthropic integration (coming soon)

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.10+
- Google AI Studio API Key
- Modern web browser

### 1. Repository'yi Klonla
```bash
git clone https://github.com/seoibrahimaydogdu/llm-tracker-workexe.git
cd llm-tracker-workexe
```

### 2. Backend Kurulumu
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 3. Environment Variables
```bash
# .env dosyası oluştur
cp .env.example .env

# API key'leri ekle:
GEMINI_API_KEY=your_gemini_api_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 4. Backend'i Başlat
```bash
uvicorn main:app --reload
```

### 5. Frontend'i Aç
```bash
# frontend/index.html dosyasını browser'da aç
# veya
cd frontend
python -m http.server 3000
```

## 📋 API Key Alma Rehberi

### 🔑 Google Gemini API Key
1. [Google AI Studio](https://makersuite.google.com/app/apikey)'ya git
2. "Create API Key" tıkla
3. API key'i kopyala
4. `.env` dosyasına `GEMINI_API_KEY=` olarak ekle

### 🗄️ Supabase Setup (Opsiyonel)
1. [Supabase](https://supabase.com) hesabı oluştur
2. Yeni proje oluştur
3. API URL ve Key'i al
4. `.env` dosyasına ekle

## 📊 Kullanım Örnekleri

### Real AI Test
```javascript
// Modal üzerinden test
1. "Real AI Test" butonuna tıkla
2. Website URL'ini gir (örn: workexe.co)
3. "Otomatik Test" seç (10 prompt)
4. "Testi Başlat" tıkla
5. Sonuçları incele
```

### API Usage
```python
# Python ile API kullanımı
import requests

response = requests.post('http://localhost:8000/run-real-visibility-test', json={
    'website': 'workexe.co',
    'prompts': []  # Auto-generate
})

data = response.json()
print(f"Visibility Score: {data['data']['summary']['average_visibility_score']}%")
```

## 📈 Test Sonuçları Örnekleri

### ✅ Başarılı Test (trendyol.com)
- **Visibility Score:** 45%
- **Mention Rate:** 100%
- **Ranking:** 1st
- **Sentiment:** Positive

### ❌ Düşük Visibility (küçük site)
- **Visibility Score:** 0%
- **Mention Rate:** 0%
- **Ranking:** Not Ranked
- **Sentiment:** Neutral

## 🗂️ Proje Yapısı

```
llm-tracker-workexe/
├── backend/
│   ├── main.py                 # FastAPI main app
│   ├── simple_ai_tester.py     # AI test engine
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # Environment variables
├── frontend/
│   └── index.html              # Web interface
├── docs/
│   ├── API.md                  # API documentation
│   └── SETUP.md               # Detailed setup guide
├── .gitignore
├── README.md
└── LICENSE
```

## 🛡️ API Endpoints

### POST `/run-real-visibility-test`
Gerçek Gemini AI ile visibility test yapar.

```json
{
  "website": "example.com",
  "prompts": ["custom prompt"] // optional
}
```

### POST `/analyze-prompt`
Kullanıcı prompt'unda website bahsedilme analizi.

```json
{
  "prompt": "Best SEO tools comparison",
  "websites": ["ahrefs.com", "semrush.com"]
}
```

### GET `/get-dashboard-stats`
Dashboard istatistiklerini getirir.

## 🎯 Roadmap

### v1.0 (Current)
- [x] Gemini API Integration
- [x] Real AI Testing
- [x] Modern Dashboard
- [x] Visibility Scoring
- [x] Modal Interface

### v1.1 (Coming Soon)
- [ ] OpenAI API Integration
- [ ] Claude API Integration  
- [ ] Scheduled Testing
- [ ] Email Reports

### v1.2 (Future)
- [ ] Historical Data
- [ ] Advanced Analytics
- [ ] Team Collaboration
- [ ] API Rate Limiting

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

Bu proje [MIT License](LICENSE) ile lisanslanmıştır.

## 👥 Team

**İbrahim Aydoğdu**
- Email: ibaywork@gmail.com
- GitHub: [@seoibrahimaydogdu](https://github.com/seoibrahimaydogdu)
- Website: [workexe.co](https://workexe.co)

## 🙏 Acknowledgments

- Google AI Studio for Gemini API
- FastAPI team for amazing framework
- Chart.js for data visualization
- Font Awesome for icons

## 📞 Support

Sorularınız için:
- 📧 Email: ibaywork@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/seoibrahimaydogdu/llm-tracker-workexe/issues)
- 📖 Wiki: [Project Wiki](https://github.com/seoibrahimaydogdu/llm-tracker-workexe/wiki)

---

⭐ **Projeyi beğendiyseniz star vermeyi unutmayın!**
