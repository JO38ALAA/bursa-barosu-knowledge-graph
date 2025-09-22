"""
Bursa Barosu Web Scraper Modülü
Bu modül web sitesinden veri çekme işlemlerini gerçekleştirir.
"""
import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import sys
import os

# Config dosyasını import etmek için path ekliyoruz
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import BASE_URL, SITEMAP_URL, REQUEST_TIMEOUT, REQUEST_DELAY

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BursaBaroScraper:
    """Bursa Barosu web sitesi için scraper sınıfı"""
    
    def __init__(self):
        """Scraper'ı başlat"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        logger.info("BursaBaroScraper başlatıldı")
    
    def fetch_sitemap(self) -> List[str]:
        """
        Sitemap.xml dosyasını çeker ve içindeki tüm URL'leri döndürür
        Sitemap başarısız olursa alternatif URL keşfi yapar
        
        Returns:
            List[str]: URL listesi
        """
        urls = []
        
        # Önce sitemap'i dene
        try:
            logger.info(f"Sitemap çekiliyor: {SITEMAP_URL}")
            response = self.session.get(SITEMAP_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # XML parse et
            root = ET.fromstring(response.content)
            
            # XML namespace'i bul
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # URL'leri çıkar
            for url_element in root.findall('.//ns:url', namespace):
                loc_element = url_element.find('ns:loc', namespace)
                if loc_element is not None:
                    urls.append(loc_element.text)
            
            logger.info(f"Sitemap'ten {len(urls)} URL bulundu")
            
        except requests.RequestException as e:
            logger.error(f"Sitemap çekilirken hata: {e}")
            logger.info("Alternatif URL keşfi başlatılıyor...")
            urls = self._discover_urls_from_homepage()
        except ET.ParseError as e:
            logger.error(f"Sitemap XML parse hatası: {e}")
            logger.info("Alternatif URL keşfi başlatılıyor...")
            urls = self._discover_urls_from_homepage()
        except Exception as e:
            logger.error(f"Beklenmeyen hata: {e}")
            logger.info("Alternatif URL keşfi başlatılıyor...")
            urls = self._discover_urls_from_homepage()
        
        return urls
    
    def _discover_urls_from_homepage(self) -> List[str]:
        """
        Ana sayfadan link keşfi yaparak URL'leri toplar
        
        Returns:
            List[str]: Keşfedilen URL listesi
        """
        discovered_urls = set()
        discovered_urls.add(BASE_URL)  # Ana sayfayı ekle
        
        try:
            logger.info(f"Ana sayfa taranıyor: {BASE_URL}")
            response = self.session.get(BASE_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Tüm linkleri bul
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                
                # Relatif URL'leri tam URL'ye çevir
                full_url = urljoin(BASE_URL, href)
                
                # Sadece aynı domain'deki linkleri al
                if urlparse(full_url).netloc == urlparse(BASE_URL).netloc:
                    # Gereksiz linkleri filtrele
                    if not self._should_skip_url(full_url):
                        discovered_urls.add(full_url)
            
            # Yaygın sayfa pattern'lerini ekle
            common_pages = [
                '/hakkimizda',
                '/iletisim',
                '/duyurular',
                '/haberler',
                '/etkinlikler',
                '/hizmetler',
                '/avukatlar',
                '/komisyonlar',
                '/mevzuat',
                '/formlar',
                '/basin',
                '/galeri'
            ]
            
            for page in common_pages:
                test_url = BASE_URL + page
                discovered_urls.add(test_url)
            
            logger.info(f"Ana sayfadan {len(discovered_urls)} URL keşfedildi")
            
        except Exception as e:
            logger.error(f"URL keşfi hatası: {e}")
            # En azından ana sayfayı döndür
            discovered_urls = {BASE_URL}
        
        return list(discovered_urls)
    
    def _should_skip_url(self, url: str) -> bool:
        """
        URL'nin atlanıp atlanmayacağını belirler
        
        Args:
            url (str): Kontrol edilecek URL
            
        Returns:
            bool: True ise atla, False ise işle
        """
        skip_patterns = [
            'javascript:',
            'mailto:',
            'tel:',
            '#',
            '.pdf',
            '.doc',
            '.docx',
            '.xls',
            '.xlsx',
            '.jpg',
            '.jpeg',
            '.png',
            '.gif',
            'wp-admin',
            'wp-content',
            'feed',
            'rss'
        ]
        
        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return True
        
        return False
    
    def scrape_page(self, url: str) -> Optional[Dict[str, str]]:
        """
        Verilen URL'deki sayfanın başlığını ve içeriğini çeker
        
        Args:
            url (str): Çekilecek sayfa URL'i
            
        Returns:
            Optional[Dict[str, str]]: {'url': url, 'title': title, 'content': content} 
                                    veya hata durumunda None
        """
        try:
            logger.info(f"Sayfa çekiliyor: {url}")
            
            # İstek gönder
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # HTML parse et
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Başlığı çıkar
            title_element = soup.find('title')
            title = title_element.get_text().strip() if title_element else "Başlık Bulunamadı"
            
            # İçeriği çıkar - birden fazla selector dene
            content = ""
            
            # Önce article tag'ini dene
            article = soup.find('article')
            if article:
                content = article.get_text(separator=' ', strip=True)
            else:
                # Alternatif content selector'ları dene
                content_selectors = [
                    '.content',
                    '.main-content',
                    '#content',
                    '.post-content',
                    '.entry-content',
                    'main',
                    '.container'
                ]
                
                for selector in content_selectors:
                    content_element = soup.select_one(selector)
                    if content_element:
                        content = content_element.get_text(separator=' ', strip=True)
                        break
                
                # Hiçbiri bulunamazsa body'den al
                if not content:
                    body = soup.find('body')
                    if body:
                        # Script ve style tag'lerini kaldır
                        for script in body(["script", "style", "nav", "header", "footer"]):
                            script.decompose()
                        content = body.get_text(separator=' ', strip=True)
            
            # İçeriği temizle
            content = ' '.join(content.split())  # Fazla boşlukları kaldır
            
            # Minimum içerik kontrolü
            if len(content) < 50:
                logger.warning(f"Sayfa çok kısa içerik: {url}")
            
            result = {
                'url': url,
                'title': title,
                'content': content
            }
            
            logger.info(f"Sayfa başarıyla çekildi: {title[:50]}...")
            
            # Rate limiting
            time.sleep(REQUEST_DELAY)
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"HTTP hatası ({url}): {e}")
            return None
        except Exception as e:
            logger.error(f"Beklenmeyen hata ({url}): {e}")
            return None
    
    def close(self):
        """Session'ı kapat"""
        self.session.close()
        logger.info("Scraper kapatıldı")


# Test fonksiyonu
if __name__ == "__main__":
    scraper = BursaBaroScraper()
    
    # Sitemap test
    urls = scraper.fetch_sitemap()
    print(f"Bulunan URL sayısı: {len(urls)}")
    
    # İlk birkaç URL'yi test et
    for i, url in enumerate(urls[:3]):
        print(f"\n--- Test {i+1}: {url} ---")
        result = scraper.scrape_page(url)
        if result:
            print(f"Başlık: {result['title']}")
            print(f"İçerik uzunluğu: {len(result['content'])} karakter")
            print(f"İçerik önizleme: {result['content'][:200]}...")
        else:
            print("Sayfa çekilemedi")
    
    scraper.close()
