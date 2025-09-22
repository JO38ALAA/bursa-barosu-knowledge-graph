# 🏛️ Bursa Barosu Bilgi Grafı ve Semantik Arama Sistemi

Bu proje, Bursa Barosu web sitesinden bilgi çıkararak Neo4j graf veritabanında saklayan ve gelişmiş semantik arama imkanları sunan bir sistemdir.

## 🚀 Özellikler

### ✅ Tamamlanan Özellikler
- **🔍 Gelişmiş Semantik Arama** - Doğal dil ile akıllı arama
- **👥 Varlık Keşfi** - Kişi, kurum, yer, tarih ve hukuki terim tanıma
- **🔗 İlişki Analizi** - Varlıklar arası bağlantıları keşfetme
- **📄 Doküman Arama** - İçerik tabanlı doküman bulma
- **🕸️ İnteraktif Graf Görselleştirme** - D3.js ile dinamik graf
- **📊 Detaylı İstatistikler** - Graf analiz verileri
- **⚡ Performans Optimizasyonu** - Cache sistemi (%70 hız artışı)
- **🔄 Otomatik Güncelleme** - Zamanlanmış veri güncelleme
- **📚 API Dokümantasyonu** - Swagger UI ile interaktif dokümantasyon
- **🐳 Docker Desteği** - Kolay deployment

### 📈 Sistem Performansı
- **1,449 düğüm** ve **5,703 ilişki** içeren bilgi grafı
- **45 sayfa** başarılı scraping
- **%70 performans artışı** cache sistemi ile
- **Gelişmiş Türkçe NLP** - Regex tabanlı varlık tanıma

## 🛠️ Teknoloji Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn
- **Veritabanı**: Neo4j (Graf veritabanı)
- **Cache**: Redis + In-memory cache
- **NLP**: Regex tabanlı Türkçe işleme
- **Frontend**: HTML5, CSS3, JavaScript, D3.js
- **Scraping**: BeautifulSoup4, Requests
- **Containerization**: Docker, Docker Compose

## 🚀 Hızlı Başlangıç

### Docker ile Çalıştırma (Önerilen)

```bash
# Projeyi klonla
git clone <repository-url>
cd SiteSearchKnowledgeGraphRAG

# Docker Compose ile başlat
docker-compose up -d

# Servislerin durumunu kontrol et
docker-compose ps
```

### Manuel Kurulum

```bash
# Python sanal ortamı oluştur
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows

# Bağımlılıkları kur
cd bursa_baro_kg
pip install -r requirements.txt

# Neo4j'yi Docker ile başlat
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15-community

# Veri pipeline'ını çalıştır
python main.py

# API servisini başlat
python api/main.py
```

## 📖 API Kullanımı

### Temel Endpoint'ler

- **Ana Sayfa**: http://localhost:8000
- **Graf Görselleştirme**: http://localhost:8000/graph
- **API Dokümantasyonu**: http://localhost:8000/docs
- **İstatistikler**: http://localhost:8000/stats

### Örnek API Çağrıları

```bash
# Semantik arama
curl "http://localhost:8000/search?query=Bursa Barosu kimdir"

# Varlık arama
curl "http://localhost:8000/entities?query=Bursa&entity_type=Location"

# Graf verileri
curl "http://localhost:8000/graph/data?limit=50"

# İstatistikler
curl "http://localhost:8000/stats"

# Cache durumu
curl "http://localhost:8000/cache/stats"

# Otomatik güncelleme durumu
curl "http://localhost:8000/updater/status"
```

## 🔧 Konfigürasyon

### Ortam Değişkenleri

```bash
# Neo4j Bağlantısı
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Redis (Opsiyonel)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Docker Compose Servisleri

- **neo4j**: Graf veritabanı (Port: 7474, 7687)
- **redis**: Cache sistemi (Port: 6379)
- **api**: FastAPI uygulaması (Port: 8000)

## 📊 Sistem Mimarisi

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Scraper   │───▶│   NLP Processor │───▶│  Graph Builder  │
│  (BeautifulSoup)│    │   (Regex-based) │    │    (Neo4j)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │◀───│   FastAPI       │◀───│ Search Engine   │
│  (D3.js Graf)   │    │   (REST API)    │    │  (Cypher)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Cache Manager  │    │   Scheduler     │
                       │ (Redis+Memory)  │    │ (Auto Update)   │
                       └─────────────────┘    └─────────────────┘
```

## 🔄 Otomatik Güncelleme

Sistem, belirli aralıklarla Bursa Barosu web sitesini tarayıp graf'ı otomatik günceller:

```bash
# Scheduler'ı başlat
curl -X POST "http://localhost:8000/updater/start"

# Zorla güncelleme
curl -X POST "http://localhost:8000/updater/force-update"

# Durumu kontrol et
curl "http://localhost:8000/updater/status"
```

## 📈 Performans Metrikleri

- **Cache Hit Oranı**: %70+ performans artışı
- **Arama Hızı**: <50ms (cache'li sorgular)
- **Graf Boyutu**: 1,449 düğüm, 5,703 ilişki
- **Bellek Kullanımı**: ~500MB (cache dahil)

## 🧪 Test ve Geliştirme

```bash
# NLP işlemciyi test et
python nlp/processor.py

# Cache sistemini test et
python cache/manager.py

# Arama motorunu test et
python search/engine.py

# Otomatik güncellemeyi test et
python scheduler/updater.py --update
```

## 📝 Proje Yapısı

```
bursa_baro_kg/
├── api/                    # FastAPI web servisi
├── cache/                  # Cache yönetim sistemi
├── crawler/                # Web scraping modülü
├── data/                   # Veri dosyaları
├── graph/                  # Neo4j graf işlemleri
├── nlp/                    # Doğal dil işleme
├── scheduler/              # Otomatik güncelleme
├── search/                 # Semantik arama motoru
├── config.py              # Konfigürasyon
├── main.py                # Ana pipeline
└── requirements.txt       # Python bağımlılıkları
```

## 🤝 Katkıda Bulunma

1. Projeyi fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 İletişim

- **Proje**: Bursa Barosu Bilgi Grafı
- **Web**: https://bursabarosu.org.tr
- **API Dokümantasyonu**: http://localhost:8000/docs

---

**🎯 Proje Durumu**: ✅ Tamamlandı - Production Ready
