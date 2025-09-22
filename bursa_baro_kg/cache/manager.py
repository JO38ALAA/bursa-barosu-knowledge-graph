"""
Bursa Barosu Cache Yönetim Modülü
Performans optimizasyonu için cache sistemi
"""
import json
import hashlib
import logging
from typing import Any, Optional, Dict
from cachetools import TTLCache
import time

# Redis import (opsiyonel)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheManager:
    """Gelişmiş cache yönetim sistemi"""
    
    def __init__(self, 
                 use_redis: bool = False,
                 redis_host: str = 'localhost',
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 memory_cache_size: int = 1000,
                 default_ttl: int = 3600):  # 1 saat
        """
        Cache Manager'ı başlat
        
        Args:
            use_redis: Redis kullanılsın mı?
            redis_host: Redis sunucu adresi
            redis_port: Redis port
            redis_db: Redis veritabanı numarası
            memory_cache_size: Bellek cache boyutu
            default_ttl: Varsayılan cache süresi (saniye)
        """
        self.use_redis = use_redis and REDIS_AVAILABLE
        self.default_ttl = default_ttl
        
        # In-memory cache (her zaman aktif)
        self.memory_cache = TTLCache(maxsize=memory_cache_size, ttl=default_ttl)
        
        # Redis cache (opsiyonel)
        self.redis_client = None
        if self.use_redis:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True
                )
                # Redis bağlantısını test et
                self.redis_client.ping()
                logger.info(f"Redis cache aktif: {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis bağlantısı başarısız: {e}. In-memory cache kullanılacak.")
                self.use_redis = False
                self.redis_client = None
        
        logger.info(f"Cache Manager başlatıldı - Redis: {self.use_redis}, Memory: {memory_cache_size}")
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Cache anahtarı oluştur"""
        # Veriyi string'e çevir ve hash'le
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        hash_obj = hashlib.md5(data_str.encode('utf-8'))
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'den veri al"""
        try:
            # Önce memory cache'e bak
            if key in self.memory_cache:
                logger.debug(f"Memory cache hit: {key}")
                return self.memory_cache[key]
            
            # Redis cache'e bak
            if self.use_redis and self.redis_client:
                redis_value = self.redis_client.get(key)
                if redis_value:
                    logger.debug(f"Redis cache hit: {key}")
                    # Redis'ten aldığımız veriyi memory cache'e de koy
                    value = json.loads(redis_value)
                    self.memory_cache[key] = value
                    return value
            
            logger.debug(f"Cache miss: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get hatası: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Cache'e veri kaydet"""
        try:
            ttl = ttl or self.default_ttl
            
            # Memory cache'e kaydet
            self.memory_cache[key] = value
            
            # Redis cache'e kaydet
            if self.use_redis and self.redis_client:
                json_value = json.dumps(value, ensure_ascii=False)
                self.redis_client.setex(key, ttl, json_value)
            
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set hatası: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Cache'den veri sil"""
        try:
            # Memory cache'den sil
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Redis cache'den sil
            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)
            
            logger.debug(f"Cache deleted: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete hatası: {e}")
            return False
    
    def clear(self) -> bool:
        """Tüm cache'i temizle"""
        try:
            # Memory cache'i temizle
            self.memory_cache.clear()
            
            # Redis cache'i temizle
            if self.use_redis and self.redis_client:
                self.redis_client.flushdb()
            
            logger.info("Cache temizlendi")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear hatası: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Cache istatistikleri"""
        stats = {
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_maxsize': self.memory_cache.maxsize,
            'redis_enabled': self.use_redis,
            'default_ttl': self.default_ttl
        }
        
        if self.use_redis and self.redis_client:
            try:
                redis_info = self.redis_client.info()
                stats['redis_keys'] = redis_info.get('db0', {}).get('keys', 0)
                stats['redis_memory'] = redis_info.get('used_memory_human', 'N/A')
            except:
                stats['redis_keys'] = 'Error'
                stats['redis_memory'] = 'Error'
        
        return stats


# Decorator fonksiyonları
def cached(cache_manager: CacheManager, prefix: str = "default", ttl: Optional[int] = None):
    """
    Fonksiyon sonuçlarını cache'leyen decorator
    
    Usage:
        @cached(cache_manager, "search", 300)
        def search_function(query):
            return expensive_operation(query)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Cache anahtarı oluştur
            cache_key = cache_manager._generate_key(prefix, {'args': args, 'kwargs': kwargs})
            
            # Cache'den kontrol et
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Fonksiyonu çalıştır ve sonucu cache'le
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Global cache instance
_global_cache = None

def get_cache_manager() -> CacheManager:
    """Global cache manager instance'ını al"""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache


# Test fonksiyonu
if __name__ == "__main__":
    # Cache manager test
    cache = CacheManager(use_redis=False)
    
    # Test verileri
    test_data = {
        "query": "Bursa Barosu",
        "results": [
            {"name": "Bursa Barosu", "type": "Organization"},
            {"name": "Bursa", "type": "Location"}
        ],
        "timestamp": time.time()
    }
    
    # Cache'e kaydet
    key = cache._generate_key("test", test_data["query"])
    cache.set(key, test_data)
    
    # Cache'den al
    cached_data = cache.get(key)
    print("Cache test başarılı:", cached_data is not None)
    
    # İstatistikler
    stats = cache.get_stats()
    print("Cache stats:", stats)
    
    # Decorator test
    @cached(cache, "expensive_func", 60)
    def expensive_function(x, y):
        print(f"Expensive operation: {x} + {y}")
        time.sleep(0.1)  # Simulate expensive operation
        return x + y
    
    # İlk çağrı (cache miss)
    result1 = expensive_function(5, 3)
    print("First call result:", result1)
    
    # İkinci çağrı (cache hit)
    result2 = expensive_function(5, 3)
    print("Second call result:", result2)
    
    print("Cache manager test tamamlandı!")
