"""
Bursa Barosu Semantik Arama Motoru
Neo4j graf veritabanı üzerinde gelişmiş arama işlemleri yapar.
"""
import logging
from typing import List, Dict, Optional, Any
from neo4j import GraphDatabase
import sys
import os
import time

# Config dosyasını import etmek için path ekliyoruz
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from cache.manager import CacheManager, cached

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """Graf tabanlı semantik arama motoru"""
    
    def __init__(self):
        """Arama motorunu başlat"""
        try:
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            # Cache manager'ı başlat
            self.cache = CacheManager(use_redis=False, memory_cache_size=500, default_ttl=1800)  # 30 dakika
            logger.info("Arama motoru Neo4j bağlantısı kuruldu")
            
        except Exception as e:
            logger.error(f"Arama motoru Neo4j bağlantı hatası: {e}")
            raise
    
    def search_entities(self, query: str, entity_type: str = None, limit: int = 10) -> List[Dict]:
        """
        Varlık arama (Cache destekli)
        
        Args:
            query (str): Arama sorgusu
            entity_type (str): Varlık türü filtresi (Person, Organization, Location, Date, LegalTerm)
            limit (int): Maksimum sonuç sayısı
            
        Returns:
            List[Dict]: Bulunan varlıklar
        """
        # Cache anahtarı oluştur
        cache_key = self.cache._generate_key("search_entities", {
            "query": query,
            "entity_type": entity_type,
            "limit": limit
        })
        
        # Cache'den kontrol et
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for entity search: {query}")
            return cached_result
        try:
            with self.driver.session() as session:
                if entity_type:
                    cypher_query = f"""
                    MATCH (n:{entity_type})
                    WHERE toLower(n.name) CONTAINS toLower($query)
                    RETURN n.name as name, labels(n) as labels, n.mention_count as mention_count
                    ORDER BY n.mention_count DESC
                    LIMIT $limit
                    """
                else:
                    cypher_query = """
                    MATCH (n)
                    WHERE toLower(n.name) CONTAINS toLower($query)
                    AND NOT 'Document' IN labels(n)
                    RETURN n.name as name, labels(n) as labels, n.mention_count as mention_count
                    ORDER BY n.mention_count DESC
                    LIMIT $limit
                    """
                
                result = session.run(cypher_query, {'query': query, 'limit': limit})
                
                entities = []
                for record in result:
                    entities.append({
                        'name': record['name'],
                        'type': record['labels'][0] if record['labels'] else 'Unknown',
                        'mention_count': record['mention_count'] or 0
                    })
                
                # Sonucu cache'e kaydet
                self.cache.set(cache_key, entities, ttl=1800)  # 30 dakika
                logger.info(f"Varlık araması: '{query}' -> {len(entities)} sonuç")
                return entities
                
        except Exception as e:
            logger.error(f"Varlık arama hatası: {e}")
            return []
    
    def find_relationships(self, entity1: str, entity2: str = None, relation_type: str = None) -> List[Dict]:
        """
        İlişki arama
        
        Args:
            entity1 (str): İlk varlık adı
            entity2 (str): İkinci varlık adı (opsiyonel)
            relation_type (str): İlişki türü (opsiyonel)
            
        Returns:
            List[Dict]: Bulunan ilişkiler
        """
        try:
            with self.driver.session() as session:
                if entity2:
                    # İki varlık arasındaki ilişkileri bul
                    if relation_type:
                        cypher_query = f"""
                        MATCH (e1)-[r:{relation_type}]->(e2)
                        WHERE toLower(e1.name) CONTAINS toLower($entity1)
                        AND toLower(e2.name) CONTAINS toLower($entity2)
                        RETURN e1.name as entity1, type(r) as relation, e2.name as entity2,
                               labels(e1) as entity1_labels, labels(e2) as entity2_labels,
                               r.strength as strength
                        ORDER BY r.strength DESC
                        LIMIT 20
                        """
                    else:
                        cypher_query = """
                        MATCH (e1)-[r]->(e2)
                        WHERE toLower(e1.name) CONTAINS toLower($entity1)
                        AND toLower(e2.name) CONTAINS toLower($entity2)
                        RETURN e1.name as entity1, type(r) as relation, e2.name as entity2,
                               labels(e1) as entity1_labels, labels(e2) as entity2_labels,
                               r.strength as strength
                        ORDER BY r.strength DESC
                        LIMIT 20
                        """
                    
                    result = session.run(cypher_query, {'entity1': entity1, 'entity2': entity2})
                else:
                    # Bir varlığın tüm ilişkilerini bul
                    cypher_query = """
                    MATCH (e1)-[r]->(e2)
                    WHERE toLower(e1.name) CONTAINS toLower($entity1)
                    RETURN e1.name as entity1, type(r) as relation, e2.name as entity2,
                           labels(e1) as entity1_labels, labels(e2) as entity2_labels,
                           r.strength as strength
                    ORDER BY r.strength DESC
                    LIMIT 20
                    """
                    
                    result = session.run(cypher_query, {'entity1': entity1})
                
                relationships = []
                for record in result:
                    relationships.append({
                        'entity1': record['entity1'],
                        'entity1_type': record['entity1_labels'][0] if record['entity1_labels'] else 'Unknown',
                        'relation': record['relation'],
                        'entity2': record['entity2'],
                        'entity2_type': record['entity2_labels'][0] if record['entity2_labels'] else 'Unknown',
                        'strength': record['strength'] or 1
                    })
                
                logger.info(f"İlişki araması: '{entity1}' -> {len(relationships)} sonuç")
                return relationships
                
        except Exception as e:
            logger.error(f"İlişki arama hatası: {e}")
            return []
    
    def search_documents(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Doküman arama
        
        Args:
            query (str): Arama sorgusu
            limit (int): Maksimum sonuç sayısı
            
        Returns:
            List[Dict]: Bulunan dokümanlar
        """
        try:
            with self.driver.session() as session:
                cypher_query = """
                MATCH (d:Document)
                WHERE toLower(d.title) CONTAINS toLower($query)
                OR toLower(d.content) CONTAINS toLower($query)
                RETURN d.url as url, d.title as title, d.content_length as content_length
                ORDER BY d.content_length DESC
                LIMIT $limit
                """
                
                result = session.run(cypher_query, {'query': query, 'limit': limit})
                
                documents = []
                for record in result:
                    documents.append({
                        'url': record['url'],
                        'title': record['title'],
                        'content_length': record['content_length'] or 0
                    })
                
                logger.info(f"Doküman araması: '{query}' -> {len(documents)} sonuç")
                return documents
                
        except Exception as e:
            logger.error(f"Doküman arama hatası: {e}")
            return []
    
    def get_entity_context(self, entity_name: str) -> Dict:
        """
        Bir varlığın tam bağlamını getir (ilişkiler, dokümanlar)
        
        Args:
            entity_name (str): Varlık adı
            
        Returns:
            Dict: Varlık bağlamı
        """
        try:
            with self.driver.session() as session:
                # Varlık bilgilerini al
                entity_query = """
                MATCH (e)
                WHERE toLower(e.name) = toLower($entity_name)
                RETURN e.name as name, labels(e) as labels, e.mention_count as mention_count
                LIMIT 1
                """
                
                entity_result = session.run(entity_query, {'entity_name': entity_name})
                entity_record = entity_result.single()
                
                if not entity_record:
                    return {'error': 'Varlık bulunamadı'}
                
                # İlişkileri al
                relations_query = """
                MATCH (e1)-[r]->(e2)
                WHERE toLower(e1.name) = toLower($entity_name)
                RETURN e2.name as connected_entity, type(r) as relation_type, 
                       labels(e2) as connected_entity_labels, r.strength as strength
                ORDER BY r.strength DESC
                LIMIT 10
                """
                
                relations_result = session.run(relations_query, {'entity_name': entity_name})
                
                # Dokümanları al
                docs_query = """
                MATCH (e)-[r:MENTIONED_IN]->(d:Document)
                WHERE toLower(e.name) = toLower($entity_name)
                RETURN d.title as document_title, d.url as document_url
                LIMIT 5
                """
                
                docs_result = session.run(docs_query, {'entity_name': entity_name})
                
                context = {
                    'entity': {
                        'name': entity_record['name'],
                        'type': entity_record['labels'][0] if entity_record['labels'] else 'Unknown',
                        'mention_count': entity_record['mention_count'] or 0
                    },
                    'relationships': [],
                    'documents': []
                }
                
                for record in relations_result:
                    context['relationships'].append({
                        'connected_entity': record['connected_entity'],
                        'connected_entity_type': record['connected_entity_labels'][0] if record['connected_entity_labels'] else 'Unknown',
                        'relation_type': record['relation_type'],
                        'strength': record['strength'] or 1
                    })
                
                for record in docs_result:
                    context['documents'].append({
                        'title': record['document_title'],
                        'url': record['document_url']
                    })
                
                logger.info(f"Varlık bağlamı: '{entity_name}' -> {len(context['relationships'])} ilişki, {len(context['documents'])} doküman")
                return context
                
        except Exception as e:
            logger.error(f"Varlık bağlamı alma hatası: {e}")
            return {'error': str(e)}
    
    def advanced_search(self, query: str) -> Dict:
        """
        Gelişmiş arama - sorguyu analiz ederek uygun arama tipini belirler
        
        Args:
            query (str): Arama sorgusu
            
        Returns:
            Dict: Arama sonuçları
        """
        query_lower = query.lower()
        
        # Sorgu tipini belirle
        if 'ile ilişkisi' in query_lower or 'arasındaki' in query_lower:
            # İlişki araması
            entities = self._extract_entities_from_query(query)
            if len(entities) >= 2:
                relationships = self.find_relationships(entities[0], entities[1])
                return {
                    'search_type': 'relationship',
                    'query': query,
                    'results': relationships
                }
        
        elif 'kimdir' in query_lower or 'nedir' in query_lower or 'hakkında' in query_lower:
            # Varlık bağlamı araması
            entity = self._extract_main_entity(query)
            if entity:
                context = self.get_entity_context(entity)
                return {
                    'search_type': 'entity_context',
                    'query': query,
                    'results': context
                }
        
        elif 'doküman' in query_lower or 'sayfa' in query_lower or 'belge' in query_lower:
            # Doküman araması
            search_term = self._extract_search_term(query)
            documents = self.search_documents(search_term)
            return {
                'search_type': 'document',
                'query': query,
                'results': documents
            }
        
        # Genel varlık araması
        entities = self.search_entities(query)
        return {
            'search_type': 'entity',
            'query': query,
            'results': entities
        }
    
    def _extract_entities_from_query(self, query: str) -> List[str]:
        """Sorgudan varlık isimlerini çıkar"""
        # Basit pattern matching - geliştirilmeye açık
        words = query.split()
        entities = []
        
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2:
                # Büyük harfle başlayan kelimeler muhtemelen varlık
                if i < len(words) - 1 and words[i+1][0].isupper():
                    # İki kelimeli varlık
                    entities.append(f"{word} {words[i+1]}")
                else:
                    entities.append(word)
        
        return entities[:2]  # En fazla 2 varlık
    
    def _extract_main_entity(self, query: str) -> str:
        """Sorgudan ana varlığı çıkar"""
        # "X kimdir", "X nedir" gibi sorguları parse et
        patterns = [
            r'(\w+(?:\s+\w+)*)\s+(?:kimdir|nedir|hakkında)',
            r'(?:kimdir|nedir|hakkında)\s+(\w+(?:\s+\w+)*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Pattern bulunamazsa ilk büyük harfli kelimeyi al
        words = query.split()
        for word in words:
            if word[0].isupper() and len(word) > 2:
                return word
        
        return query.split()[0] if query.split() else ""
    
    def _extract_search_term(self, query: str) -> str:
        """Sorgudan arama terimini çıkar"""
        # "doküman", "sayfa" gibi kelimeleri kaldır
        stop_words = ['doküman', 'sayfa', 'belge', 'hakkında', 'ile', 'ilgili']
        words = [word for word in query.split() if word.lower() not in stop_words]
        return ' '.join(words)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Graf istatistiklerini getir (Cache destekli)
        
        Returns:
            Dict: Graf istatistikleri (düğüm sayıları, ilişki sayısı)
        """
        # Cache anahtarı
        cache_key = "graph_statistics"
        
        # Cache'den kontrol et
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug("Cache hit for statistics")
            return cached_result
        
        try:
            with self.driver.session() as session:
                # Düğüm türlerine göre sayıları al
                query = """
                MATCH (n)
                RETURN labels(n)[0] as node_type, count(n) as count
                ORDER BY count DESC
                """
                
                result = session.run(query)
                stats = {}
                total_nodes = 0
                
                for record in result:
                    node_type = record['node_type'] or 'Unknown'
                    count = record['count']
                    stats[node_type] = count
                    total_nodes += count
                
                # İlişki sayısını al
                rel_query = "MATCH ()-[r]->() RETURN count(r) as rel_count"
                rel_result = session.run(rel_query)
                rel_count = rel_result.single()['rel_count']
                
                statistics = {
                    'nodes': stats,
                    'total_nodes': total_nodes,
                    'total_relationships': rel_count
                }
                
                # Sonucu cache'e kaydet (10 dakika)
                self.cache.set(cache_key, statistics, ttl=600)
                
                return statistics
                
        except Exception as e:
            logger.error(f"İstatistik alma hatası: {e}")
            return {}
    
    def close(self):
        """Neo4j bağlantısını kapat"""
        if hasattr(self, 'driver'):
            self.driver.close()
            logger.info("Arama motoru Neo4j bağlantısı kapatıldı")


# Test fonksiyonu
if __name__ == "__main__":
    search_engine = SemanticSearchEngine()
    
    print("=== Bursa Barosu Semantik Arama Motoru Test ===\n")
    
    # İstatistikler
    stats = search_engine.get_statistics()
    print("📊 Graf İstatistikleri:")
    for node_type, count in stats.get('nodes', {}).items():
        print(f"   • {node_type}: {count}")
    print(f"   • Toplam İlişki: {stats.get('total_relationships', 0)}\n")
    
    # Test aramaları
    test_queries = [
        "Bursa",
        "Baro",
        "Avukat",
        "Mahkeme",
        "Bursa Barosu kimdir",
        "Bursa ile İstanbul arasındaki ilişki"
    ]
    
    for query in test_queries:
        print(f"🔍 Arama: '{query}'")
        results = search_engine.advanced_search(query)
        print(f"   Tip: {results['search_type']}")
        
        if results['search_type'] == 'entity':
            entities = results['results'][:3]  # İlk 3 sonuç
            for entity in entities:
                print(f"   • {entity['name']} ({entity['type']}) - {entity['mention_count']} kez geçiyor")
        
        elif results['search_type'] == 'entity_context':
            context = results['results']
            if 'entity' in context:
                entity = context['entity']
                print(f"   • {entity['name']} ({entity['type']}) - {entity['mention_count']} kez geçiyor")
                print(f"   • {len(context['relationships'])} ilişki, {len(context['documents'])} doküman")
        
        print()
    
    search_engine.close()
