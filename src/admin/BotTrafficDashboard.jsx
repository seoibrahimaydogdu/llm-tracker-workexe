// src/admin/BotTrafficDashboard.jsx
import { useEffect, useState, useMemo } from "react";
import { Card, CardContent } from "@/utils/components/ui/card";
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableCell,
  TableBody
} from "@/utils/components/ui/table";
import { detectAndLogBot } from "../lib/trackBot"; 
import { supabase } from "@/lib/supabaseClient"; 
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area // <-- Hata burada düzeltildi: Area bileşeni eklendi
} from 'recharts';

// Bot isimlerine özel ikonlar/semboller veya logo URL'leri
const botLogoMap = {
  "Googlebot": { type: "image", value: "https://media.wired.com/photos/5926ffe47034dc5f91bed4e8/3:2/w_2560%2Cc_limit/google-logo.jpg" }, // Google logosu
  "Bingbot": { type: "image", value: "https://placehold.co/20x20/0078D7/FFFFFF?text=B" },    // Placeholder Bing logosu
  "Slurp": { type: "text", value: "Y!" },
  "DuckDuckBot": { type: "text", value: "🦆" },
  "Baiduspider": { type: "text", value: "百度" },
  "YandexBot": { type: "text", value: "Я" },
  "Sogou": { type: "text", value: "搜狗" },
  "Exabot": { type: "text", value: "E" },
  "AhrefsBot": { type: "text", value: "A" },
  "SemrushBot": { type: "text", value: "S" },
  "MJ12bot": { type: "text", value: "M" },
  "DotBot": { type: "text", value: "•" },
  "rogerbot": { type: "text", value: "🦊" },
  "PetalBot": { type: "text", value: "🌸" },

  // YAPAY ZEKÂ / LLM / Web AI crawler'ları
  "ChatGPT-User": { type: "image", value: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTMdM9MEQ0ExL1PmInT3U5I8v63YXBEdoIT0Q&s" }, // ChatGPT logosu
  "ChatGPT": { type: "image", value: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTMdM9MEQ0ExL1PmInT3U5I8v63YXBEdoIT0Q&s" },
  "OpenAI": { type: "image", value: "https://placehold.co/20x20/46B994/FFFFFF?text=OAI" },
  "GPTBot": { type: "image", value: "https://placehold.co/20x20/000000/FFFFFF?text=GPT" },
  "Anthropic": { type: "text", value: "📜" },
  "ClaudeBot": { type: "text", value: "📖" },
  "PerplexityBot": { type: "text", value: "❓" },
  "Bytespider": { type: "text", value: "🎵" }, // TikTok
  "Amazonbot": { type: "text", value: "📦" },
  "NeevaBot": { type: "text", value: "✨" },
  "CohereBot": { type: "text", value: "🤝" },
  "YouBot": { type: "text", value: "💡" },
  "ai-crawler": { type: "text", value: "🤖" },
  "AIDataBot": { type: "text", value: "💾" },
  "QuoraBot": { type: "text", value: "❓" },
  "PresearchBot": { type: "text", value: "🔑" },

  // GENEL WEB CRAWLER'LAR ve SOSYAL MEDYA BOTLARI
  "facebookexternalhit": { type: "image", value: "https://placehold.co/20x20/1877F2/FFFFFF?text=f" }, // Placeholder Facebook
  "Facebot": { type: "text", value: "👥" },
  "Twitterbot": { type: "image", value: "https://placehold.co/20x20/1DA1F2/FFFFFF?text=X" }, // Hatalı base64 yerine placeholder URL
  "LinkedInBot": { type: "image", value: "https://placehold.co/20x20/0A66C2/FFFFFF?text=in" },       // Placeholder LinkedIn
  "Pinterestbot": { type: "image", value: "https://placehold.co/20x20/E60023/FFFFFF?text=P" },        // Placeholder Pinterest
  "Redditbot": { type: "image", value: "https://w7.pngwing.com/pngs/647/198/png-transparent-reddit-hd-logo-thumbnail.png" },           // Reddit logosu
  "WhatsApp": { type: "text", value: "WA" },           // WhatsApp kısaltması
  "TelegramBot": { type: "text", value: "✈️" },
  "Discordbot": { type: "text", value: "🎮" },
  "Viber": { type: "text", value: "V" },
  "SkypeUriPreview": { type: "text", value: "S" },
  "HeadlessChrome": { type: "text", value: "👻" },
  "PhantomJS": { type: "text", value: "🎭" },
  "curl": { type: "text", value: "〰️" },
  "Wget": { type: "text", value: "⬇️" },
  "Python-urllib": { type: "text", value: "🐍" },
  "Go-http-client": { type: "text", value: "🐹" },
  "Java": { type: "text", value: "☕" },
  "Ruby": { type: "text", value: "💎" },
  "PostmanRuntime": { type: "text", value: "📬" },
  "axios": { type: "text", value: "📡" },
  // Varsayılan ikon
  "Default": { type: "text", value: "🌐" } 
};

// Pasta grafik dilimleri için renkler
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#d0ed57', '#a4de6c', '#8dd1e1'];

// Özel Line dot bileşeni (logoyu noktada göstermek için)
const CustomDot = (props) => {
  const { cx, cy, payload, botName } = props; // botName prop'unu al

  // payload veya botName yoksa çizme
  if (!payload || !botName) {
    return null;
  }

  const logoInfo = botLogoMap[botName] || botLogoMap.Default; // botName'i kullan
  const logoSize = 20; // Logo boyutu

  return (
    <g>
      {logoInfo.type === "image" ? (
        <image
          href={logoInfo.value}
          x={cx - logoSize / 2}
          y={cy - logoSize / 2}
          width={logoSize}
          height={logoSize}
          onError={(e) => { e.target.style.display = 'none'; }} // Resim yüklenmezse gizle
        />
      ) : (
        <circle cx={cx} cy={cy} r={6} fill="#8884d8" stroke="#8884d8" strokeWidth={2} />
      )}
    </g>
  );
};


export default function BotTrafficDashboard() {
  const [botLogs, setBotLogs] = useState([]);
  const [totalVisits, setTotalVisits] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [allBotLogsForCharts, setAllBotLogsForCharts] = useState([]); // Tüm logları grafikler için sakla

  // Filtreleme state'leri
  const [filterBotName, setFilterBotName] = useState("");
  const [filterIp, setFilterIp] = useState("");
  const [filterUrl, setFilterUrl] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [filterCountry, setFilterCountry] = useState("");
  const [filterCity, setFilterCity] = useState("");
  const [minAnomalyScore, setMinAnomalyScore] = useState(""); // Yeni: Minimum anomali skoru
  const [maxAnomalyScore, setMaxAnomalyScore] = useState(""); // Yeni: Maksimum anomali skoru
  const [filterIsAnomaly, setFilterIsAnomaly] = useState("all"); // Yeni: Anomali filtresi ('all', 'true', 'false')
  const [filterIsBlocked, setFilterIsBlocked] = useState("all"); // Yeni: Engellenmiş filtresi ('all', 'true', 'false')
  const [filterOS, setFilterOS] = useState("all"); // Yeni: OS filtresi
  const [filterBrowser, setFilterBrowser] = useState("all"); // Yeni: Tarayıcı filtresi
  const [filterBotCategory, setFilterBotCategory] = useState("all"); // Yeni: Bot Kategori filtresi


  // Sayfalama state'leri
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10; // Sayfa başına gösterilecek kayıt sayısı

  // Grafik tipi state'i
  const [chartType, setChartType] = useState("bar"); // 'bar', 'line', 'pie'
  const [timeSeriesChartType, setTimeSeriesChartType] = useState("daily"); // 'daily', 'hourly'

  // Çizgi grafik için seçilen trafik tipini tutan state (Bot Dağılımı için)
  const [selectedBotDistributionLineType, setSelectedBotDistributionLineType] = useState('totalCount'); // 'totalCount', 'anomalyCount', 'regularCount'
  // Pasta grafik için seçilen trafik tipini tutan state
  const [selectedPieTrafficType, setSelectedPieTrafficType] = useState('totalCount'); // 'totalCount', 'anomalyCount', 'regularCount'
  // Zaman Serisi grafiği için seçilen trafik tipini tutan yeni state
  const [selectedTimeSeriesTrafficType, setSelectedTimeSeriesTrafficType] = useState('total'); // 'total', 'anomaly', 'regular'

  // Tema state'i
  const [theme, setTheme] = useState('light'); // 'light' veya 'dark'

  // Gerçek zamanlı anomali bildirimi state'i
  const [showRealtimeAnomalyAlert, setShowRealtimeAnomalyAlert] = useState(false);

  // Coğrafi Harita Detay Modalı State'i (Madde 4)
  const [showGeoDetailModal, setShowGeoDetailModal] = useState(false);
  const [selectedGeoCountry, setSelectedGeoCountry] = useState(null);
  const [selectedGeoCountryData, setSelectedGeoCountryData] = useState([]);

  // Tema değiştirme fonksiyonu
  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  // useEffect ile body sınıfını güncelle
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);


  // Çizgi grafikte kullanılacak botların renkleri
  const LINE_COLORS = {
    "Googlebot": "#4285F4", // Google Blue
    "Twitterbot": "#1DA1F2", // Twitter Blue
    "Redditbot": "#FF4500",  // Reddit Orange
    // Buraya daha fazla bot ve renk ekleyebilirsiniz
  };

  // Bot loglarını ve toplam ziyaret sayısını çekme fonksiyonu
  const fetchBotLogs = async () => {
    setLoading(true);
    setError(null);
    console.log("fetchBotLogs çalışıyor..."); 

    // Önce toplam sayıyı almak için sorgu
    let countQuery = supabase.from('bot_logs').select('*', { count: 'exact' });

    // Filtreleri countQuery'ye uygula
    if (filterBotName) {
      countQuery = countQuery.ilike('bot_name', `%${filterBotName}%`);
    }
    if (filterIp) {
      countQuery = countQuery.ilike('ip', `%${filterIp}%`);
    }
    if (filterUrl) {
      countQuery = countQuery.ilike('url', `%${filterUrl}%`);
    }
    if (startDate) {
      countQuery = countQuery.gte('timestamp', startDate);
    }
    if (endDate) {
      countQuery = countQuery.lte('timestamp', endDate + 'T23:59:59.999Z'); 
    }
    if (filterCountry) { 
      countQuery = countQuery.ilike('country', `%${filterCountry}%`);
    }
    if (filterCity) {     
      countQuery = countQuery.ilike('city', `%${filterCity}%`);
    }
    // Yeni anomali skoru filtreleri
    if (minAnomalyScore !== "") {
      countQuery = countQuery.gte('anomaly_score', parseInt(minAnomalyScore, 10));
    }
    if (maxAnomalyScore !== "") {
      countQuery = countQuery.lte('anomaly_score', parseInt(maxAnomalyScore, 10));
    }
    // Yeni is_anomaly filtresi
    if (filterIsAnomaly === "true") {
      countQuery = countQuery.eq('is_anomaly', true);
    } else if (filterIsAnomaly === "false") {
      countQuery = countQuery.eq('is_anomaly', false);
    }
    // Yeni is_blocked filtresi
    if (filterIsBlocked === "true") {
      countQuery = countQuery.eq('is_blocked', true);
    } else if (filterIsBlocked === "false") {
      countQuery = countQuery.eq('is_blocked', false);
    }
    // Yeni OS filtresi
    if (filterOS !== "all") {
      countQuery = countQuery.eq('os', filterOS);
    }
    // Yeni Tarayıcı filtresi
    if (filterBrowser !== "all") {
      countQuery = countQuery.eq('browser', filterBrowser);
    }
    // Yeni Bot Kategori filtresi
    if (filterBotCategory !== "all") {
      countQuery = countQuery.eq('bot_category', filterBotCategory);
    }


    const { count, error: countError } = await countQuery;

    if (countError) {
      console.error("Toplam log sayısını çekerken hata:", countError);
      setError("Toplam veri sayısı yüklenirken bir hata oluştu: " + countError.message);
      setBotLogs([]);
      setTotalVisits(0);
      setLoading(false);
      return;
    }
    setTotalVisits(count || 0);

    // Şimdi sayfalama yapılmış veriyi almak için sorgu
    let dataQuery = supabase.from('bot_logs').select('*');

    // Filtreleri dataQuery'ye uygula
    if (filterBotName) {
      dataQuery = dataQuery.ilike('bot_name', `%${filterBotName}%`);
    }
    if (filterIp) {
      dataQuery = dataQuery.ilike('ip', `%${filterIp}%`);
    }
    if (filterUrl) {
      dataQuery = dataQuery.ilike('url', `%${filterUrl}%`);
    }
    if (startDate) {
      dataQuery = dataQuery.gte('timestamp', startDate);
    }
    if (endDate) {
      dataQuery = dataQuery.lte('timestamp', endDate + 'T23:59:59.999Z'); 
    }
    if (filterCountry) { 
      dataQuery = dataQuery.ilike('country', `%${filterCountry}%`);
    }
    if (filterCity) {     
      dataQuery = dataQuery.ilike('city', `%${filterCity}%`);
    }
    // Yeni anomali skoru filtreleri
    if (minAnomalyScore !== "") {
      dataQuery = dataQuery.gte('anomaly_score', parseInt(minAnomalyScore, 10));
    }
    if (maxAnomalyScore !== "") {
      dataQuery = dataQuery.lte('anomaly_score', parseInt(maxAnomalyScore, 10));
    }
    // Yeni is_anomaly filtresi
    if (filterIsAnomaly === "true") {
      dataQuery = dataQuery.eq('is_anomaly', true);
    } else if (filterIsAnomaly === "false") {
      dataQuery = dataQuery.eq('is_anomaly', false);
    }
    // Yeni is_blocked filtresi
    if (filterIsBlocked === "true") {
      dataQuery = dataQuery.eq('is_blocked', true);
    } else if (filterIsBlocked === "false") {
      dataQuery = dataQuery.eq('is_blocked', false);
    }
    // Yeni OS filtresi
    if (filterOS !== "all") {
      dataQuery = dataQuery.eq('os', filterOS);
    }
    // Yeni Tarayıcı filtresi
    if (filterBrowser !== "all") {
      dataQuery = dataQuery.eq('browser', filterBrowser);
    }
    // Yeni Bot Kategori filtresi
    if (filterBotCategory !== "all") {
      dataQuery = dataQuery.eq('bot_category', filterBotCategory);
    }

    // Sıralama
    dataQuery = dataQuery.order('timestamp', { ascending: false });

    // Sayfalama
    const offset = (currentPage - 1) * itemsPerPage;
    dataQuery = dataQuery.range(offset, offset + itemsPerPage - 1);

    const { data, error: dataError } = await dataQuery;

    if (dataError) {
      console.error("Bot log verilerini çekerken hata:", dataError);
      setError("Veriler yüklenirken bir hata oluştu: " + dataError.message);
      setBotLogs([]); 
    } else {
      console.log("Supabase'den çekilen sayfalama verisi:", data); 
      setBotLogs(data || []);
    }
    setLoading(false);
  };

  // Zaman serisi ve dağılım grafikleri için tüm veriyi çekme (filtreler uygulanmış haliyle)
  // Bu fonksiyon, tablo verisinden ayrı olarak tüm filtrelenmiş veriyi çeker
  const fetchAllBotLogsForCharts = async () => {
    let query = supabase.from('bot_logs').select('*');

    if (filterBotName) { query = query.ilike('bot_name', `%${filterBotName}%`); }
    if (filterIp) { query = query.ilike('ip', `%${filterIp}%`); }
    if (filterUrl) { query = query.ilike('url', `%${filterUrl}%`); }
    if (startDate) { query = query.gte('timestamp', startDate); }
    if (endDate) { query = query.lte('timestamp', endDate + 'T23:59:59.999Z'); }
    if (filterCountry) { query = query.ilike('country', `%${filterCountry}%`); }
    if (filterCity) { query = query.ilike('city', `%${filterCity}%`); }
    // Yeni anomali skoru filtreleri
    if (minAnomalyScore !== "") {
      query = query.gte('anomaly_score', parseInt(minAnomalyScore, 10));
    }
    if (maxAnomalyScore !== "") {
      query = query.lte('anomaly_score', parseInt(maxAnomalyScore, 10));
    }
    // Yeni is_anomaly filtresi
    if (filterIsAnomaly === "true") {
      query = query.eq('is_anomaly', true);
    } else if (filterIsAnomaly === "false") {
      query = query.eq('is_anomaly', false);
    }
    // Yeni is_blocked filtresi
    if (filterIsBlocked === "true") {
      query = query.eq('is_blocked', true);
    } else if (filterIsBlocked === "false") {
      query = query.eq('is_blocked', false);
    }
    // Yeni OS filtresi
    if (filterOS !== "all") {
      query = query.eq('os', filterOS);
    }
    // Yeni Tarayıcı filtresi
    if (filterBrowser !== "all") {
      query = query.eq('browser', filterBrowser);
    }
    // Yeni Bot Kategori filtresi
    if (filterBotCategory !== "all") {
      query = query.eq('bot_category', filterBotCategory);
    }

    query = query.order('timestamp', { ascending: true }); // Zaman serisi için artan sıralama

    const { data, error } = await query;
    if (error) {
      console.error("Grafikler için tüm bot loglarını çekerken hata:", error);
      return [];
    }
    return data;
  };


  useEffect(() => {
    detectAndLogBot(); 
    fetchBotLogs(); // Tablo verisi için
    // Grafik verisi için ayrı bir fetch
    fetchAllBotLogsForCharts().then(data => {
      setAllBotLogsForCharts(data);
    });

    // Gerçek Zamanlı Anomali Bildirimleri (Madde 1)
    const realtimeChannel = supabase
      .channel('bot_logs_realtime')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'bot_logs' }, (payload) => {
        console.log('Gerçek zamanlı yeni log eklendi:', payload.new);
        if (payload.new.is_anomaly) {
          setShowRealtimeAnomalyAlert(true);
          // 5 saniye sonra uyarıyı kapat
          setTimeout(() => {
            setShowRealtimeAnomalyAlert(false);
          }, 5000);
        }
        // Tablo ve grafik verilerini yeniden çek
        fetchBotLogs();
        fetchAllBotLogsForCharts().then(data => {
          setAllBotLogsForCharts(data);
        });
      })
      .subscribe();

    return () => {
      supabase.removeChannel(realtimeChannel);
    };

  }, [filterBotName, filterIp, filterUrl, startDate, endDate, currentPage, filterCountry, filterCity, minAnomalyScore, maxAnomalyScore, filterIsAnomaly, filterIsBlocked, filterOS, filterBrowser, filterBotCategory]); 

  // Toplam sayfa sayısını hesapla
  const totalPages = Math.ceil(totalVisits / itemsPerPage);

  // Bot dağılım grafiği verileri (tüm logları kullanır)
  // Bu kısım, her bot için Toplam, Anormal ve Normal ziyaret sayılarını hesaplayacak şekilde güncellendi
  const botDistributionData = useMemo(() => {
    const counts = {};
    allBotLogsForCharts.forEach(log => {
      const botName = log.bot_name;
      if (!counts[botName]) {
        counts[botName] = { name: botName, totalCount: 0, anomalyCount: 0, regularCount: 0 };
      }
      counts[botName].totalCount++;
      if (log.is_anomaly) {
        counts[botName].anomalyCount++;
      } else {
        counts[botName].regularCount++;
      }
    });
    const data = Object.values(counts); // Objeyi diziye çevir
    console.log("Bot Dağılım Grafiği verisi hazırlanıyor (3 çubuk):", data); 
    return data;
  }, [allBotLogsForCharts]); // allBotLogsForCharts değiştiğinde yeniden hesapla

  // Zaman serisi grafiği verileri (tüm logları kullanır)
  const timeSeriesData = useMemo(() => {
    const data = allBotLogsForCharts;
    const aggregatedData = {};

    data.forEach(log => {
      const date = new Date(log.timestamp);
      let timeKey;
      if (timeSeriesChartType === 'daily') {
        timeKey = date.toISOString().split('T')[0]; // YYYY-MM-DD
      } else { // hourly
        timeKey = `${date.toISOString().split('T')[0]} ${date.getHours()}:00`; // YYYY-MM-DD HH:00
      }

      if (!aggregatedData[timeKey]) {
        aggregatedData[timeKey] = { time: timeKey };
      }

      const botName = log.bot_name;
      // Initialize counts for this bot and timeKey if they don't exist
      if (!aggregatedData[timeKey][`${botName}_total`]) {
        aggregatedData[timeKey][`${botName}_total`] = 0;
        aggregatedData[timeKey][`${botName}_anomaly`] = 0;
        aggregatedData[timeKey][`${botName}_regular`] = 0;
      }

      aggregatedData[timeKey][`${botName}_total`]++;
      if (log.is_anomaly) {
        aggregatedData[timeKey][`${botName}_anomaly`]++;
      } else {
        aggregatedData[timeKey][`${botName}_regular`]++;
      }
    });

    const sortedKeys = Object.keys(aggregatedData).sort();
    const formattedData = sortedKeys.map(key => aggregatedData[key]);
    console.log("Zaman Serisi Grafiği verisi hazırlanıyor (çoklu çizgi):", formattedData);
    return formattedData;
  }, [allBotLogsForCharts, timeSeriesChartType]);

  // X ekseni için özel etiket formatlayıcı (ikon ile)
  // Bu artık XAxis'in altında bot adını ve üstünde logosunu gösterecek.
  const formatXAxisTick = (props) => {
    const { x, y, payload } = props;
    const tickItem = payload.value;

    // tickItem'ın varlığını kontrol et
    if (tickItem === undefined || tickItem === null) {
        return null; // veya boş bir metin elementi döndür
    }

    const logoInfo = botLogoMap[tickItem] || botLogoMap.Default;
    const logoSize = 20; // Logo boyutu
    const textOffset = logoSize / 2 + 5; // Logo ile metin arasında boşluk

    return (
      <g transform={`translate(${x},${y})`}>
        {logoInfo.type === "image" ? (
          <image
            href={logoInfo.value}
            x={-logoSize / 2} // Ortalamak için
            y={-logoSize - 5} // Etiketin üstüne
            width={logoSize}
            height={logoSize}
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        ) : (
          <text 
            x={0} 
            y={-logoSize / 2 - 5} 
            fill="#666" 
            textAnchor="middle" 
            dominantBaseline="middle"
            fontSize="12"
          >
            {logoInfo.value}
          </text>
        )}
        <text x={0} y={textOffset} fill="#666" textAnchor="middle" dominantBaseline="hanging" fontSize="10">
          {tickItem}
        </text>
      </g>
    );
  };

  // Özel Line dot bileşeni (logoyu noktada göstermek için)
  const CustomDot = (props) => {
    const { cx, cy, payload, botName } = props; // botName prop'unu al

    // payload veya botName yoksa çizme
    if (!payload || !botName) {
      return null;
    }

    const logoInfo = botLogoMap[botName] || botLogoMap.Default; // botName'i kullan
    const logoSize = 20; // Logo boyutu

    return (
      <g>
        {logoInfo.type === "image" ? (
          <image
            href={logoInfo.value}
            x={cx - logoSize / 2}
            y={cy - logoSize / 2}
            width={logoSize}
            height={logoSize}
            onError={(e) => { e.target.style.display = 'none'; }} // Resim yüklenmezse gizle
          />
        ) : (
          <circle cx={cx} cy={cy} r={6} fill="#8884d8" stroke="#8884d8" strokeWidth={2} />
        )}
      </g>
    );
  };


  // Pasta grafik dilimleri için özel etiket formatlayıcı
  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name }) => {
    // name'in varlığını kontrol et
    if (name === undefined || name === null) {
        return null; // veya ikon olmadan varsayılan bir etiket döndür
    }
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * Math.PI / 180);
    const y = cy + radius * Math.sin(-midAngle * Math.PI / 180);
    const logoInfo = botLogoMap[name] || botLogoMap.Default;
    const logoSize = 20; // Logo boyutu

    return (
      <g>
        {logoInfo.type === "image" ? (
          <image
            href={logoInfo.value}
            x={x - logoSize / 2}
            y={y - logoSize / 2 - 10} // Metnin biraz üstüne konumlandır
            width={logoSize}
            height={logoSize}
            onError={(e) => { e.target.style.display = 'none'; }} // Resim yüklenmezse gizle
          />
        ) : (
          <text x={x} y={y + 10} fill="white" textAnchor="middle" dominantBaseline="central" fontSize="12">
            {logoInfo.value}
          </text>
        )}
        <text x={x} y={y + 10} fill="white" textAnchor="middle" dominantBaseline="central" fontSize="10">
          {`${(percent * 100).toFixed(0)}%`}
        </text>
      </g>
    );
  };

  // IP Engelleme fonksiyonu
  const toggleIpBlockedStatus = async (ip, currentStatus) => {
    setLoading(true);
    setError(null);
    try {
      // Belirli bir IP'ye sahip tüm kayıtları güncelle
      const { data, error } = await supabase
        .from('bot_logs')
        .update({ is_blocked: !currentStatus })
        .eq('ip', ip);

      if (error) {
        throw error;
      }
      // UI'ı güncellemek için logları yeniden çek
      await fetchBotLogs();
      await fetchAllBotLogsForCharts();
      console.log(`IP ${ip} engelleme durumu ${!currentStatus} olarak güncellendi.`);
    } catch (err) {
      console.error("IP engelleme durumu güncellenirken hata:", err.message);
      setError(`IP engelleme durumu güncellenirken hata: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Coğrafi Konum Dağılımı Verisi
  const geoDistributionData = useMemo(() => {
    const counts = {};
    allBotLogsForCharts.forEach(log => {
      const country = log.country || "Bilinmiyor";
      if (!counts[country]) {
        counts[country] = { name: country, count: 0 };
      }
      counts[country].count++;
    });
    return Object.values(counts).sort((a, b) => b.count - a.count).slice(0, 10); // En çok ziyaret gelen ilk 10 ülkeyi al
  }, [allBotLogsForCharts]);

  // Coğrafi Detay Modalını Açma Fonksiyonu (Madde 4)
  const handleGeoBarClick = (data) => {
    setSelectedGeoCountry(data.name);
    // Bu kısımda, seçilen ülkeye ait daha detaylı verileri filtreleyebiliriz
    const countrySpecificLogs = allBotLogsForCharts.filter(log => log.country === data.name);
    // Örneğin, bu ülkedeki botların dağılımını veya anomali skorlarını gösterebiliriz
    const detailedData = {};
    countrySpecificLogs.forEach(log => {
      const botName = log.bot_name;
      if (!detailedData[botName]) {
        detailedData[botName] = { name: botName, count: 0, anomalyCount: 0 };
      }
      detailedData[botName].count++;
      if (log.is_anomaly) {
        detailedData[botName].anomalyCount++;
      }
    });
    setSelectedGeoCountryData(Object.values(detailedData));
    setShowGeoDetailModal(true);
  };


  // En Çok Ziyaret Edilen Sayfalar (Botlar Tarafından)
  const mostVisitedPagesByBots = useMemo(() => {
    const pageCounts = {};
    allBotLogsForCharts.filter(log => log.bot_name !== "Human").forEach(log => {
      const url = log.url || "Bilinmiyor";
      if (!pageCounts[url]) {
        pageCounts[url] = { name: url, count: 0 };
      }
      pageCounts[url].count++;
    });
    return Object.values(pageCounts).sort((a, b) => b.count - a.count).slice(0, 10); // En çok ziyaret edilen ilk 10 sayfayı al
  }, [allBotLogsForCharts]);

  // Anomali Trend Analizi ve Tahmin
  const anomalyTrendData = useMemo(() => {
    const dailyAnomalyScores = {};
    allBotLogsForCharts.forEach(log => {
      const date = new Date(log.timestamp).toISOString().split('T')[0];
      if (!dailyAnomalyScores[date]) {
        dailyAnomalyScores[date] = { totalScore: 0, count: 0, avgScore: 0 };
      }
      dailyAnomalyScores[date].totalScore += (log.anomaly_score || 0);
      dailyAnomalyScores[date].count++;
    });

    const sortedDates = Object.keys(dailyAnomalyScores).sort();
    const trendData = sortedDates.map(date => {
      const data = dailyAnomalyScores[date];
      return {
        time: date,
        avgScore: data.count > 0 ? parseFloat((data.totalScore / data.count).toFixed(2)) : 0
      };
    });
    return trendData;
  }, [allBotLogsForCharts]);

  // Basit Anomali Tahmini
  const anomalyPrediction = useMemo(() => {
    if (anomalyTrendData.length < 2) return "Daha fazla veri gerekiyor.";
    
    const lastTwoDays = anomalyTrendData.slice(-2);
    if (lastTwoDays.length < 2) return "Daha fazla veri gerekiyor.";

    const [prevDay, currentDay] = lastTwoDays;
    if (currentDay.avgScore > prevDay.avgScore * 1.2) { // %20'den fazla artış
      return "Anomali skorunda belirgin bir artış gözlemleniyor. Dikkatli olunması önerilir!";
    } else if (currentDay.avgScore < prevDay.avgScore * 0.8) { // %20'den fazla düşüş
      return "Anomali skorunda düşüş var. Durum stabil görünüyor.";
    } else {
      return "Anomali skoru stabil seyrediyor.";
    }
  }, [anomalyTrendData]);

  // Kullanıcı Tanımlı Bot Grupları/Etiketleri (Gelişmiş Yönetim)
  const [editingIpForCategory, setEditingIpForCategory] = useState(null);
  const [selectedBotCategory, setSelectedBotCategory] = useState("");

  const handleEditBotCategory = (ip, currentCategory) => {
    setEditingIpForCategory(ip);
    setSelectedBotCategory(currentCategory || "unknown");
  };

  const handleSaveBotCategory = async (ip) => {
    setLoading(true);
    setError(null);
    try {
      const { data, error } = await supabase
        .from('bot_logs')
        .update({ bot_category: selectedBotCategory })
        .eq('ip', ip);

      if (error) {
        throw error;
      }
      await fetchBotLogs();
      await fetchAllBotLogsForCharts();
      setEditingIpForCategory(null);
      setSelectedBotCategory("");
      console.log(`IP ${ip} için bot kategorisi güncellendi: ${selectedBotCategory}`);
    } catch (err) {
      console.error("Bot kategorisi güncellenirken hata:", err.message);
      setError(`Bot kategorisi güncellenirken hata: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Otomatik Engelleme Kuralları (Gelişmiş Simülasyon)
  const [showAutomatedBlockingModal, setShowAutomatedBlockingModal] = useState(false);
  const [newBlockingRule, setNewBlockingRule] = useState({
    condition: '', 
    action: 'block_ip', 
    threshold: 0
  });

  const handleAddAutomatedBlockingRule = () => {
    console.log("Yeni otomatik engelleme kuralı eklendi (Simülasyon):", newBlockingRule);
    alert("Yeni otomatik engelleme kuralı eklendi (Bu sadece bir simülasyondur, gerçek bir backend entegrasyonu gereklidir).");
    setShowAutomatedBlockingModal(false);
    setNewBlockingRule({ condition: '', action: 'block_ip', threshold: 0 });
  };

  // Performans Metrikleri Grafiği
  const performanceMetricsData = useMemo(() => {
    const dailyMetrics = {};
    allBotLogsForCharts.forEach(log => {
      const date = new Date(log.timestamp).toISOString().split('T')[0];
      if (!dailyMetrics[date]) {
        dailyMetrics[date] = { totalPageLoadTime: 0, totalServerResponseTime: 0, count: 0 };
      }
      dailyMetrics[date].totalPageLoadTime += (log.page_load_time || 0);
      dailyMetrics[date].totalServerResponseTime += (log.server_response_time || 0);
      dailyMetrics[date].count++;
    });

    const sortedDates = Object.keys(dailyMetrics).sort();
    const formattedData = sortedDates.map(date => {
      const data = dailyMetrics[date];
      return {
        time: date,
        avgPageLoadTime: data.count > 0 ? parseFloat((data.totalPageLoadTime / data.count).toFixed(2)) : 0,
        avgServerResponseTime: data.count > 0 ? parseFloat((data.totalServerResponseTime / data.count).toFixed(2)) : 0
      };
    });
    return formattedData;
  }, [allBotLogsForCharts]);


  // Veri Dışa Aktarma (CSV)
  const handleExportCSV = async () => {
    setLoading(true);
    setError(null);
    try {
      // Tüm filtrelenmiş veriyi çek
      let query = supabase.from('bot_logs').select('*');

      if (filterBotName) { query = query.ilike('bot_name', `%${filterBotName}%`); }
      if (filterIp) { query = query.ilike('ip', `%${filterIp}%`); }
      if (filterUrl) { query = query.ilike('url', `%${filterUrl}%`); }
      if (startDate) { query = query.gte('timestamp', startDate); }
      if (endDate) { query = query.lte('timestamp', endDate + 'T23:59:59.999Z'); }
      if (filterCountry) { query = query.ilike('country', `%${filterCountry}%`); }
      if (filterCity) { query = query.ilike('city', `%${filterCity}%`); }
      if (minAnomalyScore !== "") { query = query.gte('anomaly_score', parseInt(minAnomalyScore, 10)); }
      if (maxAnomalyScore !== "") { query = query.lte('anomaly_score', parseInt(maxAnomalyScore, 10)); }
      if (filterIsAnomaly === "true") { query = query.eq('is_anomaly', true); } else if (filterIsAnomaly === "false") { query = query.eq('is_anomaly', false); }
      if (filterIsBlocked === "true") { query = query.eq('is_blocked', true); } else if (filterIsBlocked === "false") { query = query.eq('is_blocked', false); }
      if (filterOS !== "all") { query = query.eq('os', filterOS); }
      if (filterBrowser !== "all") { query = query.eq('browser', filterBrowser); }
      if (filterBotCategory !== "all") { query = query.eq('bot_category', filterBotCategory); }

      query = query.order('timestamp', { ascending: false });

      const { data, error: exportError } = await query;

      if (exportError) {
        throw exportError;
      }

      if (!data || data.length === 0) {
        alert("Dışa aktarılacak veri bulunamadı.");
        return;
      }

      // CSV başlıkları
      const headers = [
        "ID", "URL", "Bot Adı", "IP", "Zaman Damgası", "Referans", "Sayfa Başlığı",
        "Tam User Agent", "Ülke", "Şehir", "Oturum ID", "Ziyaret Edilen Sayfalar",
        "Anomali Mi?", "Anomali Nedeni", "Anomali Skoru", "Engellendi Mi?",
        "Bot Kategorisi", "Sayfa Yükleme Süresi (sn)", "Sunucu Yanıt Süresi (sn)"
      ];

      // CSV içeriği oluştur
      const csvContent = [
        headers.join(','),
        ...data.map(row => {
          // Tırnak işaretleri ve virgül kaçışları
          const escapeCsv = (value) => {
            if (value === null || value === undefined) return '';
            let str = String(value);
            if (typeof value === 'object') {
              str = JSON.stringify(value); // Nesneleri JSON string'e çevir
            }
            if (str.includes(',') || str.includes('"') || str.includes('\n')) {
              return `"${str.replace(/"/g, '""')}"`;
            }
            return str;
          };

          return [
            escapeCsv(row.id),
            escapeCsv(row.url),
            escapeCsv(row.bot_name),
            escapeCsv(row.ip),
            escapeCsv(new Date(row.timestamp).toISOString()),
            escapeCsv(row.referrer),
            escapeCsv(row.page_title),
            escapeCsv(row.full_user_agent),
            escapeCsv(row.country),
            escapeCsv(row.city),
            escapeCsv(row.session_id),
            escapeCsv(row.visited_pages), // Zaten JSON string
            escapeCsv(row.is_anomaly),
            escapeCsv(row.anomaly_reason), // Zaten JSON string
            escapeCsv(row.anomaly_score),
            escapeCsv(row.is_blocked),
            escapeCsv(row.bot_category),
            escapeCsv(row.page_load_time),
            escapeCsv(row.server_response_time)
          ].join(',');
        })
      ].join('\n');

      // CSV dosyasını indir
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', 'bot_logs.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
      alert("Veriler başarıyla CSV olarak dışa aktarıldı!");

    } catch (err) {
      console.error("CSV dışa aktarılırken hata:", err.message);
      setError(`CSV dışa aktarılırken hata: ${err.message}`);
      alert(`CSV dışa aktarılırken hata: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Bot Davranış Profili Öğrenimi ve Otomatik Sınıflandırma (Madde 3) simülasyonu
  const handleTrainMLModel = () => {
    alert("Makine öğrenimi modeli eğitiliyor... (Bu bir simülasyondur. Gerçek bir uygulama için backend ML entegrasyonu gereklidir.)");
    console.log("Simülasyon: Makine öğrenimi modeli eğitiliyor...");
    // Burada gerçek bir ML modelini eğitme veya bir ML API'sini çağırma mantığı olurdu.
  };


  return (
    <div className={`min-h-screen p-8 ${theme === 'dark' ? 'bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-900'}`}>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-4xl font-bold text-blue-600">
          Workexe AI Tracker Paneli
        </h1>
        <div className="flex items-center space-x-4">
          {showRealtimeAnomalyAlert && (
            <span className="animate-pulse text-red-500 font-bold text-lg">
              🚨 ANOMALİ TESPİT EDİLDİ! 🚨
            </span>
          )}
          <button
            onClick={toggleTheme}
            className={`py-2 px-4 rounded-md font-semibold ${theme === 'dark' ? 'bg-gray-700 text-white' : 'bg-gray-200 text-gray-800'} hover:bg-opacity-80 transition-colors duration-200`}
          >
            {theme === 'dark' ? 'Aydınlık Tema' : 'Karanlık Tema'}
          </button>
        </div>
      </div>
      <p className="text-xl mb-4">Toplam Ziyaret: {totalVisits}</p>

      {/* Filtreleme ve Arama Alanları */}
      <Card className={`mb-6 p-4 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4"> 
          <div>
            <label htmlFor="filterBotName" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Bot Adı:</label>
            <input
              type="text"
              id="filterBotName"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={filterBotName}
              onChange={(e) => {
                setFilterBotName(e.target.value);
                setCurrentPage(1); 
              }}
              placeholder="Bot adı ara..."
            />
          </div>
          <div>
            <label htmlFor="filterIp" className="block text-sm font-medium text-gray-700 dark:text-gray-300">IP Adresi:</label>
            <input
              type="text"
              id="filterIp"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={filterIp}
              onChange={(e) => {
                setFilterIp(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="IP adresi ara..."
            />
          </div>
          <div>
            <label htmlFor="filterUrl" className="block text-sm font-medium text-gray-700 dark:text-gray-300">URL:</label>
            <input
              type="text"
              id="filterUrl"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={filterUrl}
              onChange={(e) => {
                setFilterUrl(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="URL ara..."
            />
          </div>
          <div>
            <label htmlFor="filterCountry" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Ülke:</label> 
            <input
              type="text"
              id="filterCountry"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={filterCountry}
              onChange={(e) => {
                setFilterCountry(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Ülke ara..."
            />
          </div>
          <div>
            <label htmlFor="filterCity" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Şehir:</label> 
            <input
              type="text"
              id="filterCity"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={filterCity}
              onChange={(e) => {
                setFilterCity(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Şehir ara..."
            />
          </div>
          {/* Yeni Anomali Skoru Filtreleri */}
          <div>
            <label htmlFor="minAnomalyScore" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Min. Anomali Skoru:</label>
            <input
              type="number"
              id="minAnomalyScore"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={minAnomalyScore}
              onChange={(e) => {
                setMinAnomalyScore(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Min skor"
            />
          </div>
          <div>
            <label htmlFor="maxAnomalyScore" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Max. Anomali Skoru:</label>
            <input
              type="number"
              id="maxAnomalyScore"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={maxAnomalyScore}
              onChange={(e) => {
                setMaxAnomalyScore(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Max skor"
            />
          </div>
          {/* Yeni Anomali Durumu Filtresi */}
          <div>
            <label htmlFor="filterIsAnomaly" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Anomali Durumu:</label>
            <select
              id="filterIsAnomaly"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={filterIsAnomaly}
              onChange={(e) => {
                setFilterIsAnomaly(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option value="all">Tümü</option>
              <option value="true">Evet</option>
              <option value="false">Hayır</option>
            </select>
          </div>
          {/* Yeni Engellenmiş Durumu Filtresi */}
          <div>
            <label htmlFor="filterIsBlocked" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Engellenmiş Durumu:</label>
            <select
              id="filterIsBlocked"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={filterIsBlocked}
              onChange={(e) => {
                setFilterIsBlocked(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option value="all">Tümü</option>
              <option value="true">Engellenmiş</option>
              <option value="false">Engellenmemiş</option>
            </select>
          </div>
          {/* Yeni OS Filtresi */}
          <div>
            <label htmlFor="filterOS" className="block text-sm font-medium text-gray-700 dark:text-gray-300">İşletim Sistemi:</label>
            <select
              id="filterOS"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={filterOS}
              onChange={(e) => {
                setFilterOS(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option value="all">Tümü</option>
              <option value="Windows">Windows</option>
              <option value="macOS">macOS</option>
              <option value="Linux">Linux</option>
              <option value="Android">Android</option>
              <option value="iOS">iOS</option>
              <option value="Chrome OS">Chrome OS</option>
              <option value="Unknown OS">Bilinmiyor</option>
            </select>
          </div>
          {/* Yeni Tarayıcı Filtresi */}
          <div>
            <label htmlFor="filterBrowser" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Tarayıcı:</label>
            <select
              id="filterBrowser"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={filterBrowser}
              onChange={(e) => {
                setFilterBrowser(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option value="all">Tümü</option>
              <option value="Chrome">Chrome</option>
              <option value="Firefox">Firefox</option>
              <option value="Safari">Safari</option>
              <option value="Edge">Edge</option>
              <option value="IE">IE</option>
              <option value="Opera">Opera</option>
              <option value="Chromium">Chromium</option>
              <option value="Samsung Browser">Samsung Browser</option>
              <option value="UC Browser">UC Browser</option>
              <option value="Vivaldi">Vivaldi</option>
              <option value="Brave">Brave</option>
              <option value="Unknown Browser">Bilinmiyor</option>
            </select>
          </div>
          {/* Yeni Bot Kategori Filtresi */}
          <div>
            <label htmlFor="filterBotCategory" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Bot Kategorisi:</label>
            <select
              id="filterBotCategory"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
              value={filterBotCategory}
              onChange={(e) => {
                setFilterBotCategory(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option value="all">Tümü</option>
              <option value="unknown">Bilinmiyor</option>
              <option value="good">İyi Bot</option>
              <option value="bad">Kötü Bot</option>
              <option value="monitored">İzlenen</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => {
                setFilterBotName("");
                setFilterIp("");
                setFilterUrl("");
                setFilterCountry(""); 
                setFilterCity("");    
                setStartDate("");
                setEndDate("");
                setMinAnomalyScore(""); 
                setMaxAnomalyScore("");
                setFilterIsAnomaly("all"); 
                setFilterIsBlocked("all"); 
                setFilterOS("all"); 
                setFilterBrowser("all"); 
                setFilterBotCategory("all"); 
                setCurrentPage(1);
              }}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded-md shadow-sm dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
            >
              Filtreleri Temizle
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Grafik Tipi Seçimi */}
      <Card className={`mb-6 p-4 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent className="flex justify-center space-x-4">
          <button
            onClick={() => setChartType("bar")}
            className={`py-2 px-4 rounded-md font-semibold ${chartType === "bar" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
          >
            Çubuk Grafik
          </button>
          <button
            onClick={() => setChartType("line")}
            className={`py-2 px-4 rounded-md font-semibold ${chartType === "line" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
          >
            Çizgi Grafik
          </button>
          <button
            onClick={() => setChartType("pie")}
            className={`py-2 px-4 rounded-md font-semibold ${chartType === "pie" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
          >
            Pasta Grafik
          </button>
        </CardContent>
      </Card>

      {/* Bot Dağılım Grafiği */}
      <Card className={`mb-6 p-4 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent>
          <h2 className="text-xl font-semibold mb-4">Bot Dağılımı</h2>
          {/* Grafik verisi boşsa veya yükleniyorsa grafikleri gösterme */}
          {botDistributionData.length > 0 && !loading && botDistributionData[0].name !== undefined && botDistributionData[0].totalCount !== undefined ? (
            // Her grafik tipini kendi ResponsiveContainer'ı içinde koşullu olarak render et
            chartType === "bar" ? (
                <ResponsiveContainer width="100%" height={300} key="bar-chart-container">
                    <BarChart data={botDistributionData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" tick={formatXAxisTick} interval={0} /> 
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="totalCount" fill="#8884d8" name="Toplam Ziyaret" /> 
                        <Bar dataKey="anomalyCount" fill="#FF0000" name="Anormal Ziyaret" /> 
                        <Bar dataKey="regularCount" fill="#00C49F" name="Normal Ziyaret" /> 
                    </BarChart>
                </ResponsiveContainer>
            ) : chartType === "line" ? (
                // Çizgi grafikte bot dağılımı için filtreleme butonu ve tek çizgi gösterimi
                <>
                <div className="flex justify-center space-x-4 mb-4">
                    <button
                        onClick={() => setSelectedBotDistributionLineType('totalCount')}
                        className={`py-2 px-4 rounded-md font-semibold ${selectedBotDistributionLineType === "totalCount" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
                    >
                        Toplam Ziyaret
                    </button>
                    <button
                        onClick={() => setSelectedBotDistributionLineType('anomalyCount')}
                        className={`py-2 px-4 rounded-md font-semibold ${selectedBotDistributionLineType === "anomalyCount" ? "bg-red-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
                    >
                        Anormal Ziyaret
                    </button>
                    <button
                        onClick={() => setSelectedBotDistributionLineType('regularCount')}
                        className={`py-2 px-4 rounded-md font-semibold ${selectedBotDistributionLineType === "regularCount" ? "bg-green-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
                    >
                        Normal Ziyaret
                    </button>
                </div>
                <ResponsiveContainer width="100%" height={300} key="line-chart-container">
                    <LineChart data={botDistributionData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" tick={formatXAxisTick} /> 
                        <YAxis />
                        <Tooltip />
                        <Line 
                            type="monotone" 
                            dataKey={selectedBotDistributionLineType} 
                            stroke={
                                selectedBotDistributionLineType === 'totalCount' ? '#8884d8' :
                                selectedBotDistributionLineType === 'anomalyCount' ? '#FF0000' :
                                '#00C49F'
                            }
                            name={
                                selectedBotDistributionLineType === 'totalCount' ? 'Toplam Ziyaret' :
                                selectedBotDistributionLineType === 'anomalyCount' ? 'Anormal Ziyaret' :
                                'Normal Ziyaret'
                            }
                            activeDot={{ r: 8 }} 
                            dot={<CustomDot botName={props => props.payload.name} />} 
                        /> 
                    </LineChart>
                </ResponsiveContainer>
                </>
            ) : chartType === "pie" ? (
                <>
                <div className="flex justify-center space-x-4 mb-4">
                    <button
                        onClick={() => setSelectedPieTrafficType('totalCount')}
                        className={`py-2 px-4 rounded-md font-semibold ${selectedPieTrafficType === "totalCount" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
                    >
                        Toplam Ziyaret
                    </button>
                    <button
                        onClick={() => setSelectedPieTrafficType('anomalyCount')}
                        className={`py-2 px-4 rounded-md font-semibold ${selectedPieTrafficType === "anomalyCount" ? "bg-red-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
                    >
                        Anormal Ziyaret
                    </button>
                    <button
                        onClick={() => setSelectedPieTrafficType('regularCount')}
                        className={`py-2 px-4 rounded-md font-semibold ${selectedPieTrafficType === "regularCount" ? "bg-green-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
                    >
                        Normal Ziyaret
                    </button>
                </div>
                <ResponsiveContainer width="100%" height={300} key="pie-chart-container">
                    <PieChart>
                        <Pie
                            data={botDistributionData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={renderCustomizedLabel} 
                            outerRadius={120}
                            fill="#8884d8"
                            dataKey={selectedPieTrafficType} 
                        >
                            {botDistributionData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip />
                    </PieChart>
                </ResponsiveContainer>
                </>
            ) : null 
          ) : (
            <p className="text-center text-gray-500 dark:text-gray-400">
              {loading ? "Veriler yükleniyor..." : "Grafik için yeterli veri yok."}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Zaman Serisi Grafiği */}
      <Card className={`mb-6 p-4 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent>
          <h2 className="text-xl font-semibold mb-4">Zaman Serisi Analizi</h2>
          <div className="flex justify-center space-x-4 mb-4">
            <button
              onClick={() => setSelectedTimeSeriesTrafficType("total")}
              className={`py-2 px-4 rounded-md font-semibold ${selectedTimeSeriesTrafficType === "total" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
            >
              Toplam Ziyaret
            </button>
            <button
              onClick={() => setSelectedTimeSeriesTrafficType("anomaly")}
              className={`py-2 px-4 rounded-md font-semibold ${selectedTimeSeriesTrafficType === "anomaly" ? "bg-red-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
            >
              Anormal Ziyaret
            </button>
            <button
              onClick={() => setSelectedTimeSeriesTrafficType("regular")}
              className={`py-2 px-4 rounded-md font-semibold ${selectedTimeSeriesTrafficType === "regular" ? "bg-green-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"}`}
            >
              Normal Ziyaret
            </button>
          </div>
          {timeSeriesData.length > 0 && !loading ? (
            <ResponsiveContainer width="100%" height={300} key={`time-series-${timeSeriesChartType}`}>
              <LineChart data={timeSeriesData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                {/* Belirtilen botlar için dinamik çizgiler */}
                {["Googlebot", "Twitterbot", "Redditbot"].map(botName => (
                    <Line 
                        key={botName}
                        type="monotone" 
                        dataKey={`${botName}_${selectedTimeSeriesTrafficType}`} 
                        stroke={LINE_COLORS[botName] || "#8884d8"} 
                        name={`${botName} (${selectedTimeSeriesTrafficType === 'total' ? 'Toplam' : selectedTimeSeriesTrafficType === 'anomaly' ? 'Anormal' : 'Normal'})`}
                        activeDot={{ r: 8 }} 
                        dot={<CustomDot botName={botName} />} 
                    /> 
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-gray-500 dark:text-gray-400">
              {loading ? "Veriler yükleniyor..." : "Zaman serisi grafiği için yeterli veri yok."}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Anomali Trend Analizi ve Tahmin */}
      <Card className={`mb-6 p-4 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent>
          <h2 className="text-xl font-semibold mb-4">Anomali Trend Analizi ve Tahmin</h2>
          {anomalyTrendData.length > 0 && !loading ? (
            <>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={anomalyTrendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="avgScore" stroke="#FF5733" name="Ortalama Anomali Skoru" activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
              <p className="mt-4 text-center text-lg font-medium">
                **Tahmin:** {anomalyPrediction}
              </p>
            </>
          ) : (
            <p className="text-center text-gray-500 dark:text-gray-400">
              {loading ? "Veriler yükleniyor..." : "Anomali trend analizi için yeterli veri yok."}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Gelişmiş Performans Metrikleri Grafikleri */}
      <Card className={`mb-6 p-4 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent>
          <h2 className="text-xl font-semibold mb-4">Performans Metrikleri Trendi (Ortalama)</h2>
          {performanceMetricsData.length > 0 && !loading ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceMetricsData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="avgPageLoadTime" stroke="#8884d8" fill="#8884d8" name="Ort. Sayfa Yükleme Süresi (sn)" />
                <Area type="monotone" dataKey="avgServerResponseTime" stroke="#82ca9d" fill="#82ca9d" name="Ort. Sunucu Yanıt Süresi (sn)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-gray-500 dark:text-gray-400">
              {loading ? "Veriler yükleniyor..." : "Performans metrikleri grafiği için yeterli veri yok."}
            </p>
          )}
        </CardContent>
      </Card>

      {/* En Çok Ziyaret Edilen Sayfalar (Botlar Tarafından) */}
      <Card className={`mb-6 p-4 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent>
          <h2 className="text-xl font-semibold mb-4">Botlar Tarafından En Çok Ziyaret Edilen Sayfalar</h2>
          {mostVisitedPagesByBots.length > 0 && !loading ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={mostVisitedPagesByBots} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="name" width={150} tickFormatter={(value) => value.length > 30 ? value.substring(0, 27) + '...' : value} />
                <Tooltip />
                <Bar dataKey="count" fill="#82ca9d" name="Ziyaret Sayısı" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-gray-500 dark:text-gray-400">
              {loading ? "Veriler yükleniyor..." : "En çok ziyaret edilen sayfalar için yeterli veri yok."}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Coğrafi Konum Dağılımı (Etkileşimli Harita Simülasyonu) */}
      <Card className={`mb-6 p-4 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent>
          <h2 className="text-xl font-semibold mb-4">En Çok Ziyaret Eden Ülkeler (Etkileşimli Simülasyon)</h2>
          {geoDistributionData.length > 0 && !loading ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={geoDistributionData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar 
                  dataKey="count" 
                  fill="#32CD32" 
                  name="Ziyaret Sayısı" 
                  onClick={handleGeoBarClick} 
                  cursor="pointer" 
                /> 
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-gray-500 dark:text-gray-400">
              {loading ? "Veriler yükleniyor..." : "Coğrafi dağılım için yeterli veri yok."}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Coğrafi Detay Modalı */}
      {showGeoDetailModal && selectedGeoCountry && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex justify-center items-center z-50">
          <div className={`p-6 rounded-lg shadow-lg w-1/2 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
            <h3 className="text-2xl font-semibold mb-4">{selectedGeoCountry} Detaylı Trafik Analizi</h3>
            <p className="mb-4 text-gray-700 dark:text-gray-300">
              Bu, **{selectedGeoCountry}** ülkesinden gelen bot trafiğinin detaylı bir simülasyonudur. Gerçek bir uygulamada, bu alanda ülkeye özel daha derinlemesine grafikler ve veriler (örn. en aktif IP'ler, anomali trendleri) gösterilebilir.
            </p>
            {selectedGeoCountryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={selectedGeoCountryData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8884d8" name="Toplam Ziyaret" />
                  <Bar dataKey="anomalyCount" fill="#FF0000" name="Anormal Ziyaret" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-gray-500 dark:text-gray-400">Bu ülkeden detaylı bot trafiği verisi bulunamadı.</p>
            )}
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => setShowGeoDetailModal(false)}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md"
              >
                Kapat
              </button>
            </div>
          </div>
        </div>
      )}


      {/* Bot Davranış Profili Öğrenimi ve Otomatik Sınıflandırma */}
      <Card className={`mb-6 p-4 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent>
          <h2 className="text-xl font-semibold mb-4">Bot Davranış Profili Öğrenimi ve Otomatik Sınıflandırma (Simülasyon)</h2>
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            Bu bölüm, botların davranışlarını (ziyaret sıklığı, sayfa gezintisi, User Agent desenleri vb.) otomatik olarak analiz eden ve onları "iyi", "kötü" veya "şüpheli" gibi kategorilere ayıran bir makine öğrenimi sistemini simüle eder. Sistem, zamanla daha akıllı hale gelebilir ve manuel müdahale ihtiyacını azaltır.
          </p>
          <p className="text-gray-700 dark:text-gray-300">
            **Not:** Bu özellik, gerçek bir makine öğrenimi modeli ve backend altyapısı gerektirir. Buradaki buton sadece bir simülasyondur.
          </p>
          <button 
            onClick={handleTrainMLModel}
            className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-md shadow-sm"
          >
            Modeli Eğit (Simülasyon)
          </button>
        </CardContent>
      </Card>

      {/* Kural Yönetimi ve Uyarılar */}
      <Card className={`mb-6 p-4 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent>
          <h2 className="text-xl font-semibold mb-4">Kural Yönetimi ve Uyarılar</h2>
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            Burada, belirli bot davranışları veya anomali skorları için özel kurallar tanımlayabilir ve uyarılar alabilirsiniz. Örneğin: "Anomali skoru 50'den yüksek olan bir IP'den 10 dakika içinde 5'ten fazla ziyaret gelirse bana e-posta gönder."
          </p>
          <p className="text-gray-700 dark:text-gray-300">
            **Not:** Bu özellik için arka uç (backend) entegrasyonu (örn. Supabase Functions, webhook'lar) gereklidir. Şu anda sadece arayüzü simüle edilmektedir.
          </p>
          <button 
            onClick={() => setShowAutomatedBlockingModal(true)}
            className="mt-4 bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded-md shadow-sm"
          >
            Yeni Otomatik Engelleme Kuralı Tanımla (Simülasyon)
          </button>
        </CardContent>
      </Card>

      {/* Gelişmiş Güvenlik Entegrasyonları */}
      <Card className={`mb-6 p-4 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent>
          <h2 className="text-xl font-semibold mb-4">Tehdit İstihbaratı Entegrasyonu (Simülasyon)</h2>
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            Bu bölüm, bilinen kötü niyetli IP listeleri veya tehdit istihbaratı beslemeleri ile entegrasyonu simüle eder. Bu sayede, gelen trafiği otomatik olarak bu listelerle karşılaştırabilir ve potansiyel tehditleri işaretleyebilirsiniz.
          </p>
          <p className="text-gray-700 dark:text-gray-300">
            **Örnekler:** Spamhaus DROP listeleri, AbuseIPDB, Blocklist.de gibi kaynaklardan veri çekme.
          </p>
          <button className="mt-4 bg-yellow-600 hover:bg-yellow-700 text-white font-semibold py-2 px-4 rounded-md shadow-sm">
            Tehdit Beslemesi ile Senkronize Et (Simülasyon)
          </button>
        </CardContent>
      </Card>

      {/* Otomatik Engelleme Kuralı Tanımlama Modalı */}
      {showAutomatedBlockingModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex justify-center items-center z-50">
          <div className={`p-6 rounded-lg shadow-lg w-1/3 ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
            <h3 className="text-xl font-semibold mb-4">Yeni Otomatik Engelleme Kuralı</h3>
            <div className="mb-4">
              <label htmlFor="ruleCondition" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Koşul (Örn: anomaly_score &gt; 50 AND visits_in_5_min &gt; 10):</label>
              <input
                type="text"
                id="ruleCondition"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
                value={newBlockingRule.condition}
                onChange={(e) => setNewBlockingRule({ ...newBlockingRule, condition: e.target.value })}
                placeholder="Koşul girin..."
              />
            </div>
            <div className="mb-4">
              <label htmlFor="ruleAction" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Aksiyon:</label>
              <select
                id="ruleAction"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
                value={newBlockingRule.action}
                onChange={(e) => setNewBlockingRule({ ...newBlockingRule, action: e.target.value })}
              >
                <option value="block_ip">IP Engelle</option>
                <option value="send_alert">Uyarı Gönder</option>
              </select>
            </div>
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setShowAutomatedBlockingModal(false)}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded-md dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
              >
                İptal
              </button>
              <button
                onClick={handleAddAutomatedBlockingRule}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md"
              >
                Kuralı Ekle
              </button>
            </div>
          </div>
        </div>
      )}


      {/* Veri Dışa Aktarma Butonu */}
      <div className="flex justify-end mb-4">
        <button
          onClick={handleExportCSV}
          className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-md shadow-sm"
          disabled={loading}
        >
          {loading ? "Dışa Aktarılıyor..." : "Verileri CSV Olarak Dışa Aktar"}
        </button>
      </div>

      {/* Bot Logları Tablosu */}
      <Card className={`w-full ${theme === 'dark' ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-900'}`}>
        <CardContent>
          {loading || error ? ( 
            <div className="text-center py-4">
              {loading ? "Veriler yükleniyor..." : error ? `Hata: ${error}` : ""}
            </div>
          ) : (
            <div> 
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Sayfa</TableHead>
                    <TableHead>Bot</TableHead>
                    <TableHead>Zaman</TableHead>
                    <TableHead>IP</TableHead>
                    <TableHead>Ülke</TableHead>
                    <TableHead>Şehir</TableHead>
                    <TableHead>OS</TableHead> 
                    <TableHead>Tarayıcı</TableHead> 
                    <TableHead>Sayfa Yükleme Süresi (sn)</TableHead> 
                    <TableHead>Sunucu Yanıt Süresi (sn)</TableHead> 
                    <TableHead>Oturum ID</TableHead>
                    <TableHead>Ziyaret Edilen Sayfalar</TableHead>
                    <TableHead>Anomali</TableHead>
                    <TableHead>Anomali Nedeni</TableHead>
                    <TableHead>Anomali Skoru</TableHead>
                    <TableHead>Engellendi</TableHead>
                    <TableHead>Bot Kategorisi</TableHead> 
                    <TableHead>Referans</TableHead>
                    <TableHead>Sayfa Başlığı</TableHead>
                    <TableHead>Tam User Agent</TableHead>
                    <TableHead>Kullanıcı mı?</TableHead>
                    <TableHead>Aksiyon</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {botLogs.length > 0 ? (
                    botLogs.map((log) => (
                      <TableRow key={log.id} className={`${log.is_blocked ? 'bg-red-100 dark:bg-red-900' : ''}`}> 
                        <TableCell>{log.url}</TableCell>
                        <TableCell>{log.bot_name}</TableCell>
                        <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                        <TableCell className={`${log.is_blocked ? 'text-red-700 dark:text-red-300' : ''}`}>{log.ip || "N/A"}</TableCell> 
                        <TableCell>{log.country || "N/A"}</TableCell>
                        <TableCell>{log.city || "N/A"}</TableCell>
                        <TableCell>{log.os || "N/A"}</TableCell> 
                        <TableCell>{log.browser || "N/A"}</TableCell> 
                        <TableCell>{log.page_load_time !== null && log.page_load_time !== undefined ? log.page_load_time.toFixed(2) : "N/A"}</TableCell> 
                        <TableCell>{log.server_response_time !== null && log.server_response_time !== undefined ? log.server_response_time.toFixed(2) : "N/A"}</TableCell> 
                        <TableCell className="max-w-[100px] truncate">{log.session_id || "N/A"}</TableCell>
                        <TableCell className="max-w-[200px] truncate">
                          {log.visited_pages ? JSON.parse(log.visited_pages).join(', ') : "[]"}
                        </TableCell>
                        <TableCell>{log.is_anomaly ? "Evet" : "Hayır"}</TableCell>
                        <TableCell className="max-w-[150px] truncate">
                          {log.anomaly_reason ? JSON.parse(log.anomaly_reason).join(', ') : "Yok"}
                        </TableCell>
                        <TableCell>{log.anomaly_score !== null && log.anomaly_score !== undefined ? log.anomaly_score : "N/A"}</TableCell>
                        <TableCell>{log.is_blocked ? "Evet" : "Hayır"}</TableCell> 
                        <TableCell>
                          {editingIpForCategory === log.ip ? (
                            <select
                              value={selectedBotCategory}
                              onChange={(e) => setSelectedBotCategory(e.target.value)}
                              onBlur={() => handleSaveBotCategory(log.ip)}
                              className="w-24 p-1 border rounded bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
                            >
                              <option value="unknown">Bilinmiyor</option>
                              <option value="good">İyi Bot</option>
                              <option value="bad">Kötü Bot</option>
                              <option value="monitored">İzlenen</option>
                            </select>
                          ) : (
                            <span 
                              onClick={() => handleEditBotCategory(log.ip, log.bot_category)}
                              className="cursor-pointer hover:underline"
                            >
                              {log.bot_category || "Bilinmiyor"}
                            </span>
                          )}
                        </TableCell> 
                        <TableCell className="max-w-[150px] truncate">{log.referrer || "N/A"}</TableCell>
                        <TableCell className="max-w-[150px] truncate">{log.page_title || "N/A"}</TableCell>
                        <TableCell className="max-w-[200px] truncate">{log.full_user_agent || "N/A"}</TableCell>
                        <TableCell>{log.is_user ? "Evet" : "Hayır"}</TableCell>
                        <TableCell>
                          <button
                            onClick={() => toggleIpBlockedStatus(log.ip, log.is_blocked)}
                            className={`py-1 px-2 rounded-md text-sm font-semibold ${log.is_blocked ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-green-500 hover:bg-green-600 text-white'}`}
                          >
                            {log.is_blocked ? 'Engeli Kaldır' : 'Engelle'}
                          </button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={22} className="text-center"> 
                        Henüz bot trafiği kaydedilmedi veya filtrelere uygun veri bulunamadı.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>

              {totalPages > 1 && (
                <div className="flex justify-center items-center mt-4 space-x-2">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md disabled:opacity-50 disabled:cursor-not-allowed dark:bg-blue-700 dark:hover:bg-blue-800"
                  >
                    Önceki
                  </button>
                  <span className="text-gray-700 dark:text-gray-300">Sayfa {currentPage} / {totalPages}</span>
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={currentPage === totalPages}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md disabled:opacity-50 disabled:cursor-not-allowed dark:bg-blue-700 dark:hover:bg-blue-800"
                  >
                    Sonraki
                  </button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
