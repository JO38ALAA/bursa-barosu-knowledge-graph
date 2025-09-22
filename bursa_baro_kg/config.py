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

# Logging Ayarları
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
