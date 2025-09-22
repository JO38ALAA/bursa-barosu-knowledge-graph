"""
Bursa Barosu Bilgi Grafı Projesi - Ana Orchestrator Script
Tüm süreci yöneten ana script
"""
import os
import json
import logging
from datetime import datetime
from tqdm import tqdm
import sys

# Proje modüllerini import et
from crawler.scraper import BursaBaroScraper
from nlp.processor import NLPProcessor
from graph.builder import GraphBuilder
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BursaBaroKnowledgeGraph:
    """Ana orchestrator sınıfı"""
    
    def __init__(self):
        """Orchestrator'ı başlat"""
        self.scraper = None
        self.nlp_processor = None
        self.graph_builder = None
        
        # Veri dizinlerini oluştur
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        
        logger.info("Bursa Barosu Bilgi Grafı Projesi başlatıldı")
    
    def initialize_components(self):
        """Tüm bileşenleri başlat"""
        try:
            logger.info("Bileşenler başlatılıyor...")
            
            self.scraper = BursaBaroScraper()
            self.nlp_processor = NLPProcessor()
            self.graph_builder = GraphBuilder()
            
            logger.info("Tüm bileşenler başarıyla başlatıldı")
            return True
            
        except Exception as e:
            logger.error(f"Bileşen başlatma hatası: {e}")
            return False
    
    def step1_fetch_urls(self) -> list:
        """Adım 1: Sitemap'ten URL'leri çek"""
        logger.info("=== ADIM 1: URL'ler çekiliyor ===")
        
        urls = self.scraper.fetch_sitemap()
        
        if not urls:
            logger.warning("Hiç URL bulunamadı, ana sayfa ile devam ediliyor")
            urls = ["https://bursabarosu.org.tr"]
        
        logger.info(f"Toplam {len(urls)} URL bulundu")
        return urls
    
    def step2_scrape_pages(self, urls: list) -> int:
        """Adım 2: Sayfaları kazı ve raw data olarak kaydet"""
        logger.info("=== ADIM 2: Sayfalar kazınıyor ===")
        
        scraped_count = 0
        failed_count = 0
        
        # Progress bar ile scraping
        for i, url in enumerate(tqdm(urls, desc="Sayfalar kazınıyor")):
            try:
                # Sayfa verilerini çek
                page_data = self.scraper.scrape_page(url)
                
                if page_data:
                    # Dosya adını oluştur (URL'den güvenli dosya adı)
                    safe_filename = self._url_to_filename(url)
                    file_path = os.path.join(RAW_DATA_DIR, f"{safe_filename}.json")
                    
                    # Metadata ekle
                    page_data['scraped_at'] = datetime.now().isoformat()
                    page_data['scrape_index'] = i
                    
                    # JSON olarak kaydet
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(page_data, f, ensure_ascii=False, indent=2)
                    
                    scraped_count += 1
                    logger.debug(f"Kaydedildi: {file_path}")
                else:
                    failed_count += 1
                    logger.warning(f"Sayfa çekilemedi: {url}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Scraping hatası ({url}): {e}")
        
        logger.info(f"Scraping tamamlandı: {scraped_count} başarılı, {failed_count} başarısız")
        return scraped_count
    
    def step3_process_nlp(self) -> int:
        """Adım 3: Raw verileri NLP ile işle"""
        logger.info("=== ADIM 3: NLP işleme başlıyor ===")
        
        # Raw data dosyalarını bul
        raw_files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith('.json')]
        
        if not raw_files:
            logger.error("İşlenecek raw data dosyası bulunamadı")
            return 0
        
        processed_count = 0
        
        # Progress bar ile NLP processing
        for filename in tqdm(raw_files, desc="NLP işleme"):
            try:
                raw_file_path = os.path.join(RAW_DATA_DIR, filename)
                processed_file_path = os.path.join(PROCESSED_DATA_DIR, filename)
                
                # Raw veriyi oku
                with open(raw_file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                # NLP işleme
                nlp_result = self.nlp_processor.process_text(raw_data['content'])
                
                # İşlenmiş veriyi hazırla
                processed_data = {
                    'url': raw_data['url'],
                    'title': raw_data['title'],
                    'content': raw_data['content'],
                    'scraped_at': raw_data.get('scraped_at'),
                    'processed_at': datetime.now().isoformat(),
                    'nlp_result': nlp_result
                }
                
                # İşlenmiş veriyi kaydet
                with open(processed_file_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, ensure_ascii=False, indent=2)
                
                processed_count += 1
                logger.debug(f"NLP işlendi: {filename}")
                
            except Exception as e:
                logger.error(f"NLP işleme hatası ({filename}): {e}")
        
        logger.info(f"NLP işleme tamamlandı: {processed_count} dosya işlendi")
        return processed_count
    
    def step4_build_graph(self) -> int:
        """Adım 4: İşlenmiş verileri graf veritabanına yaz"""
        logger.info("=== ADIM 4: Graf veritabanı oluşturuluyor ===")
        
        # İşlenmiş data dosyalarını bul
        processed_files = [f for f in os.listdir(PROCESSED_DATA_DIR) if f.endswith('.json')]
        
        if not processed_files:
            logger.error("İşlenecek processed data dosyası bulunamadı")
            return 0
        
        graph_count = 0
        
        # Progress bar ile graph building
        for filename in tqdm(processed_files, desc="Graf oluşturuluyor"):
            try:
                processed_file_path = os.path.join(PROCESSED_DATA_DIR, filename)
                
                # İşlenmiş veriyi oku
                with open(processed_file_path, 'r', encoding='utf-8') as f:
                    processed_data = json.load(f)
                
                # Doküman düğümünü oluştur
                document_data = {
                    'url': processed_data['url'],
                    'title': processed_data['title'],
                    'content': processed_data['content']
                }
                
                success = self.graph_builder.create_document_node(document_data)
                if not success:
                    logger.warning(f"Doküman düğümü oluşturulamadı: {filename}")
                    continue
                
                # Varlık düğümlerini oluştur
                nlp_result = processed_data['nlp_result']
                entities = nlp_result.get('entities', [])
                relationships = nlp_result.get('relationships', [])
                
                # Varlıkları oluştur
                for entity in entities:
                    self.graph_builder.create_or_update_node(entity)
                
                # Varlıkları dokümana bağla
                if entities:
                    self.graph_builder.link_entities_to_document(entities, processed_data['url'])
                
                # İlişkileri oluştur
                for relationship in relationships:
                    entity1 = {
                        'text': relationship['entity1'],
                        'label': relationship['entity1_label']
                    }
                    entity2 = {
                        'text': relationship['entity2'], 
                        'label': relationship['entity2_label']
                    }
                    
                    self.graph_builder.create_relationship(
                        entity1, 
                        entity2, 
                        relationship['relation_type'],
                        processed_data['url']
                    )
                
                graph_count += 1
                logger.debug(f"Graf'a eklendi: {filename}")
                
            except Exception as e:
                logger.error(f"Graf oluşturma hatası ({filename}): {e}")
        
        logger.info(f"Graf oluşturma tamamlandı: {graph_count} dosya işlendi")
        return graph_count
    
    def run_full_pipeline(self, max_pages=None):
        """Tam pipeline'ı çalıştır"""
        logger.info("🚀 TAM PİPELİNE BAŞLATIYOR 🚀")
        
        # Bileşenleri başlat
        if not self.initialize_components():
            logger.error("Bileşenler başlatılamadı, pipeline durduruluyor")
            return False
        
        try:
            # Adım 1: URL'leri çek
            urls = self.step1_fetch_urls()
            if not urls:
                logger.error("URL'ler çekilemedi")
                return False
            
            # Max pages limiti uygula
            if max_pages and max_pages < len(urls):
                logger.info(f"URL listesi {len(urls)}'den {max_pages}'e sınırlandırıldı")
                urls = urls[:max_pages]
            
            # Adım 2: Sayfaları kazı
            scraped_count = self.step2_scrape_pages(urls)
            if scraped_count == 0:
                logger.error("Hiç sayfa kazınamadı")
                return False
            
            # Adım 3: NLP işleme
            processed_count = self.step3_process_nlp()
            if processed_count == 0:
                logger.error("Hiç veri işlenemedi")
                return False
            
            # Adım 4: Graf oluştur
            graph_count = self.step4_build_graph()
            if graph_count == 0:
                logger.error("Graf oluşturulamadı")
                return False
            
            # Final istatistikler
            stats = self.graph_builder.get_graph_stats()
            
            logger.info("🎉 PİPELİNE BAŞARIYLA TAMAMLANDI! 🎉")
            logger.info(f"📊 Özet İstatistikler:")
            logger.info(f"   • Bulunan URL: {len(urls)}")
            logger.info(f"   • Kazınan sayfa: {scraped_count}")
            logger.info(f"   • İşlenen dosya: {processed_count}")
            logger.info(f"   • Graf'a eklenen: {graph_count}")
            logger.info(f"   • Toplam düğüm: {stats.get('total_nodes', 0)}")
            logger.info(f"   • Toplam ilişki: {stats.get('relationships', 0)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline hatası: {e}")
            return False
        
        finally:
            self.cleanup()
    
    def _url_to_filename(self, url: str) -> str:
        """URL'yi güvenli dosya adına çevir"""
        import re
        # URL'den protokol ve özel karakterleri temizle
        filename = re.sub(r'https?://', '', url)
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        filename = filename[:100]  # Maksimum uzunluk sınırı
        return filename
    
    def cleanup(self):
        """Kaynakları temizle"""
        try:
            if self.scraper:
                self.scraper.close()
            if self.graph_builder:
                self.graph_builder.close()
            logger.info("Kaynaklar temizlendi")
        except Exception as e:
            logger.error(f"Temizleme hatası: {e}")


def main():
    """Ana fonksiyon"""
    import argparse
    
    # Komut satırı argümanlarını parse et
    parser = argparse.ArgumentParser(description='Bursa Barosu Bilgi Grafı Pipeline')
    parser.add_argument('--max-pages', type=int, default=None, 
                       help='Maksimum işlenecek sayfa sayısı (varsayılan: tümü)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🏛️  BURSA BAROSU BİLGİ GRAFI PROJESİ  🏛️")
    print("=" * 60)
    
    if args.max_pages:
        print(f"📄 Maksimum sayfa limiti: {args.max_pages}")
    else:
        print("📄 Tüm sayfalar işlenecek")
    
    # Orchestrator'ı başlat
    orchestrator = BursaBaroKnowledgeGraph()
    
    # Pipeline'ı çalıştır
    success = orchestrator.run_full_pipeline(max_pages=args.max_pages)
    
    if success:
        print("\n✅ Proje başarıyla tamamlandı!")
        print("🌐 Neo4j Browser'da sonuçları görüntüleyebilirsiniz: http://localhost:7474")
        print("📊 Graf sorgularını çalıştırabilirsiniz:")
        print("   MATCH (n) RETURN n LIMIT 25")
        print("   MATCH (p:Person)-[r]->(o:Organization) RETURN p, r, o")
    else:
        print("\n❌ Proje tamamlanamadı. Loglara bakınız.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
