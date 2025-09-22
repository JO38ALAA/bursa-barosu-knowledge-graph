"""
Bursa Barosu Otomatik Veri Güncelleme Sistemi
Belirli aralıklarla web sitesini tarayıp graf'ı günceller
"""
import schedule
import time
import logging
import threading
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, Any

# Proje modüllerini import et
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from crawler.scraper import BursaBaroScraper
from nlp.processor import NLPProcessor
from graph.builder import GraphBuilder
from cache.manager import CacheManager

logger = logging.getLogger(__name__)


class AutoUpdater:
    """Otomatik veri güncelleme sistemi"""
    
    def __init__(self, 
                 update_interval_hours: int = 24,
                 max_pages_per_update: int = 200):
        """
        Auto Updater'ı başlat
        
        Args:
            update_interval_hours: Güncelleme aralığı (saat)
            max_pages_per_update: Her güncellemede maksimum sayfa sayısı
        """
        self.update_interval = update_interval_hours
        self.max_pages = max_pages_per_update
        self.is_running = False
        self.last_update = None
        self.update_stats = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'last_update_time': None,
            'last_update_duration': None,
            'pages_processed': 0,
            'entities_added': 0,
            'relationships_added': 0
        }
        
        # Cache manager (güncellemeler sonrası cache temizlemek için)
        self.cache = CacheManager()
        
        logger.info(f"Auto Updater başlatıldı - Güncelleme aralığı: {update_interval_hours} saat")
    
    def start_scheduler(self):
        """Scheduler'ı başlat"""
        if self.is_running:
            logger.warning("Scheduler zaten çalışıyor")
            return
        
        # Günlük güncelleme planla
        schedule.every(self.update_interval).hours.do(self.run_update)
        
        # İlk güncellemeyi hemen yap (opsiyonel)
        # schedule.every().minute.do(self.run_update).tag('immediate')
        
        self.is_running = True
        logger.info(f"Scheduler başlatıldı - {self.update_interval} saatte bir güncelleme yapılacak")
        
        # Scheduler thread'i başlat
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Scheduler'ı durdur"""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler durduruldu")
    
    def _run_scheduler(self):
        """Scheduler'ı çalıştır (thread içinde)"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Her dakika kontrol et
    
    def run_update(self):
        """Manuel güncelleme çalıştır"""
        if not self.is_running:
            logger.warning("Scheduler çalışmıyor, güncelleme atlandı")
            return
        
        start_time = datetime.now()
        logger.info("🔄 Otomatik veri güncelleme başlatıldı")
        
        try:
            self.update_stats['total_updates'] += 1
            
            # 1. Web sitesini tara
            scraper = BursaBaroScraper()
            urls = scraper.fetch_sitemap()
            
            if not urls:
                logger.warning("URL bulunamadı, güncelleme atlandı")
                self.update_stats['failed_updates'] += 1
                return
            
            # Tüm sayfaları işle
            urls = urls[:self.max_pages]
            
            logger.info(f"📄 {len(urls)} sayfa işlenecek")
            
            # 2. Sayfaları kazı
            scraped_data = []
            for i, url in enumerate(urls):
                try:
                    page_data = scraper.scrape_page(url)
                    if page_data and page_data.get('content') and len(page_data['content'].strip()) > 100:
                        scraped_data.append({
                            'url': url,
                            'title': page_data.get('title', ''),
                            'content': page_data['content'],
                            'scraped_at': datetime.now().isoformat()
                        })
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"📄 {i + 1}/{len(urls)} sayfa kazındı")
                        
                except Exception as e:
                    logger.error(f"Sayfa kazıma hatası {url}: {e}")
                    continue
            
            scraper.close()
            
            if not scraped_data:
                logger.warning("Hiç veri kazınamadı, güncelleme atlandı")
                self.update_stats['failed_updates'] += 1
                return
            
            logger.info(f"✅ {len(scraped_data)} sayfa başarıyla kazındı")
            
            # 3. NLP işleme
            nlp_processor = NLPProcessor()
            processed_data = []
            
            total_entities = 0
            total_relationships = 0
            
            for data in scraped_data:
                try:
                    result = nlp_processor.process_text(data['content'])
                    
                    processed_data.append({
                        'url': data['url'],
                        'content': data['content'],
                        'entities': result['entities'],
                        'relationships': result['relationships'],
                        'scraped_at': data['scraped_at']
                    })
                    
                    total_entities += len(result['entities'])
                    total_relationships += len(result['relationships'])
                    
                except Exception as e:
                    logger.error(f"NLP işleme hatası {data['url']}: {e}")
                    continue
            
            logger.info(f"🧠 NLP işleme tamamlandı: {total_entities} varlık, {total_relationships} ilişki")
            
            # 4. Graf'a ekle
            graph_builder = GraphBuilder()
            
            for data in processed_data:
                try:
                    # Doküman düğümü oluştur
                    document_data = {
                        'url': data['url'],
                        'title': data.get('title', ''),
                        'content': data['content']
                    }
                    graph_builder.create_document_node(document_data)
                    
                    # Varlıkları ekle
                    for entity in data['entities']:
                        graph_builder.create_entity_node(
                            entity['text'], 
                            entity['label']
                        )
                        # Varlığı dokümanla bağla
                        entity_dict = {
                            'text': entity['text'],
                            'label': entity['label']
                        }
                        document_dict = {
                            'text': data['url'],
                            'label': 'Document'
                        }
                        graph_builder.create_relationship(
                            entity_dict,
                            document_dict,
                            'MENTIONED_IN',
                            data['url']
                        )
                    
                    # İlişkileri ekle
                    for rel in data['relationships']:
                        entity1 = {
                            'text': rel['entity1'],
                            'label': rel['entity1_label']
                        }
                        entity2 = {
                            'text': rel['entity2'], 
                            'label': rel['entity2_label']
                        }
                        graph_builder.create_relationship(
                            entity1,
                            entity2,
                            rel['relation_type'],
                            data['url']
                        )
                
                except Exception as e:
                    logger.error(f"Graf güncelleme hatası {data['url']}: {e}")
                    continue
            
            graph_builder.close()
            
            # 5. Cache'i temizle (yeni veriler için)
            self.cache.clear()
            logger.info("🗑️ Cache temizlendi")
            
            # İstatistikleri güncelle
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.update_stats.update({
                'successful_updates': self.update_stats['successful_updates'] + 1,
                'last_update_time': end_time.isoformat(),
                'last_update_duration': duration,
                'pages_processed': len(scraped_data),
                'entities_added': total_entities,
                'relationships_added': total_relationships
            })
            
            self.last_update = end_time
            
            logger.info(f"✅ Otomatik güncelleme tamamlandı - Süre: {duration:.1f}s")
            logger.info(f"📊 İşlenen: {len(scraped_data)} sayfa, {total_entities} varlık, {total_relationships} ilişki")
            
        except Exception as e:
            logger.error(f"❌ Otomatik güncelleme hatası: {e}")
            self.update_stats['failed_updates'] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Güncelleyici durumunu getir"""
        next_run = None
        if self.is_running and schedule.jobs:
            next_job = min(schedule.jobs, key=lambda job: job.next_run)
            next_run = next_job.next_run.isoformat() if next_job.next_run else None
        
        return {
            'is_running': self.is_running,
            'update_interval_hours': self.update_interval,
            'max_pages_per_update': self.max_pages,
            'next_scheduled_update': next_run,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'stats': self.update_stats
        }
    
    def force_update(self):
        """Zorla güncelleme yap (manuel tetikleme)"""
        logger.info("🔄 Manuel güncelleme tetiklendi")
        
        # Yeni thread'de çalıştır (blocking olmamak için)
        update_thread = threading.Thread(target=self.run_update, daemon=True)
        update_thread.start()
        
        return {"message": "Güncelleme başlatıldı", "status": "started"}


# Global updater instance
_global_updater = None

def get_updater() -> AutoUpdater:
    """Global updater instance'ını al"""
    global _global_updater
    if _global_updater is None:
        _global_updater = AutoUpdater(update_interval_hours=24, max_pages_per_update=20)
    return _global_updater


# Test ve CLI kullanımı
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bursa Barosu Otomatik Güncelleme Sistemi")
    parser.add_argument("--start", action="store_true", help="Scheduler'ı başlat")
    parser.add_argument("--update", action="store_true", help="Tek seferlik güncelleme yap")
    parser.add_argument("--status", action="store_true", help="Durum bilgisi göster")
    parser.add_argument("--interval", type=int, default=24, help="Güncelleme aralığı (saat)")
    parser.add_argument("--max-pages", type=int, default=20, help="Maksimum sayfa sayısı")
    
    args = parser.parse_args()
    
    # Logging ayarla
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    updater = AutoUpdater(
        update_interval_hours=args.interval,
        max_pages_per_update=args.max_pages
    )
    
    if args.start:
        print("🚀 Scheduler başlatılıyor...")
        updater.start_scheduler()
        
        try:
            # Ana thread'i canlı tut
            while True:
                time.sleep(10)
                if not updater.is_running:
                    break
        except KeyboardInterrupt:
            print("\n⏹️ Scheduler durduruluyor...")
            updater.stop_scheduler()
    
    elif args.update:
        print("🔄 Tek seferlik güncelleme başlatılıyor...")
        updater.is_running = True  # Manuel güncelleme için
        updater.run_update()
    
    elif args.status:
        status = updater.get_status()
        print("📊 Updater Durumu:")
        for key, value in status.items():
            print(f"   • {key}: {value}")
    
    else:
        parser.print_help()
