"""
Bursa Barosu Bilgi Grafı Projesi - Konfigürasyon Dosyası
"""
import os

# Neo4j Veritabanı Bağlantı Ayarları
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Web Scraping Ayarları
BASE_URL = "https://bursabarosu.org.tr"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1  # Saniye cinsinden istekler arası bekleme süresi

# Dosya Yolları
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# NLP Ayarları
# SpaCy modeli mevcut olmadığı için basit regex tabanlı yaklaşım kullanacağız
USE_SPACY = False
SPACY_MODEL = "tr_core_news_sm"  # Gelecekte kullanım için

# Transformer tabanlı NER ayarları
USE_TRANSFORMERS_NER = os.getenv("USE_TRANSFORMERS_NER", "true").lower() == "true"
NER_MODEL_NAME = os.getenv("NER_MODEL_NAME", "savasy/bert-base-turkish-ner-cased")
USE_STANZA = os.getenv("USE_STANZA", "false").lower() == "true"  # Cümleleme/parse için opsiyonel
USE_MREBEL = os.getenv("USE_MREBEL", "false").lower() == "true"   # Çok dilli RE için opsiyonel

# Normalizasyon ve eşleştirme ayarları
ENABLE_NORMALIZATION = os.getenv("ENABLE_NORMALIZATION", "true").lower() == "true"
ENABLE_FUZZY_MATCH = os.getenv("ENABLE_FUZZY_MATCH", "true").lower() == "true"
FUZZY_THRESHOLD = int(os.getenv("FUZZY_THRESHOLD", "90"))

# Logging Ayarları
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
