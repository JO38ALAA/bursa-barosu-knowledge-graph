"""
Bursa Barosu Graf Veritabanı Builder Modülü
Neo4j veritabanında düğüm ve ilişki oluşturma işlemlerini gerçekleştirir.
"""
from neo4j import GraphDatabase
import logging
from typing import Dict, List, Optional
import sys
import os
from nlp.normalizer import make_key, normalize_text

# Config dosyasını import etmek için path ekliyoruz
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphBuilder:
    """Neo4j graf veritabanı builder sınıfı"""
    
    def __init__(self):
        """Graf builder'ı başlat ve Neo4j bağlantısı kur"""
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI, 
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            
            # Bağlantıyı test et
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    logger.info("Neo4j bağlantısı başarıyla kuruldu")
                else:
                    raise Exception("Neo4j test sorgusu başarısız")
            
            # İndeksleri oluştur
            self._create_indexes()
            
        except Exception as e:
            logger.error(f"Neo4j bağlantı hatası: {e}")
            raise

    def clean_database(self):
        """Veritabanındaki tüm düğüm ve ilişkileri siler."""
        try:
            with self.driver.session() as session:
                logger.warning("Veritabanı temizleniyor... Tüm düğümler ve ilişkiler silinecek.")
                query = "MATCH (n) DETACH DELETE n"
                session.run(query)
                logger.info("Veritabanı başarıyla temizlendi.")
                # İndekslerin yeniden oluştuğundan emin ol
                self._create_indexes()
        except Exception as e:
            logger.error(f"Veritabanı temizleme hatası: {e}")
            raise
    
    def _create_indexes(self):
        """Performans için gerekli indeksleri oluştur"""
        try:
            with self.driver.session() as session:
                # Varlık türleri için indeksler
                indexes = [
                    "CREATE INDEX person_norm_index IF NOT EXISTS FOR (p:Person) ON (p.normalized_key)",
                    "CREATE INDEX organization_norm_index IF NOT EXISTS FOR (o:Organization) ON (o.normalized_key)",
                    "CREATE INDEX location_norm_index IF NOT EXISTS FOR (l:Location) ON (l.normalized_key)",
                    "CREATE INDEX date_norm_index IF NOT EXISTS FOR (d:Date) ON (d.normalized_key)",
                    "CREATE INDEX entity_norm_index IF NOT EXISTS FOR (e:Entity) ON (e.normalized_key)",
                    "CREATE INDEX document_url_index IF NOT EXISTS FOR (doc:Document) ON (doc.url)"
                ]
                
                for index_query in indexes:
                    try:
                        session.run(index_query)
                        logger.debug(f"İndeks oluşturuldu: {index_query}")
                    except Exception as e:
                        logger.warning(f"İndeks oluşturma hatası: {e}")
                
                logger.info("Neo4j indeksleri kontrol edildi/oluşturuldu")
                
        except Exception as e:
            logger.error(f"İndeks oluşturma hatası: {e}")
    
    def create_document_node(self, document_data: Dict) -> bool:
        """
        Doküman düğümü oluştur
        
        Args:
            document_data (Dict): {'url': str, 'title': str, 'content': str}
            
        Returns:
            bool: Başarı durumu
        """
        try:
            with self.driver.session() as session:
                query = """
                MERGE (doc:Document {url: $url})
                SET doc.title = $title,
                    doc.content = $content,
                    doc.content_length = $content_length,
                    doc.updated_at = datetime()
                RETURN doc.url as url
                """
                
                result = session.run(query, {
                    'url': document_data['url'],
                    'title': document_data['title'],
                    'content': document_data['content'],
                    'content_length': len(document_data['content'])
                })
                
                created_url = result.single()["url"]
                logger.info(f"Doküman düğümü oluşturuldu: {created_url}")
                return True
                
        except Exception as e:
            logger.error(f"Doküman düğümü oluşturma hatası: {e}")
            return False
    
    def create_entity_node(self, entity_text: str, entity_label: str) -> bool:
        """
        Varlık düğümü oluştur (updater için basit interface)
        
        Args:
            entity_text (str): Varlık metni
            entity_label (str): Varlık etiketi
            
        Returns:
            bool: Başarı durumu
        """
        entity = {'text': entity_text, 'label': entity_label}
        return self.create_or_update_node(entity)
    
    def create_or_update_node(self, entity: Dict) -> bool:
        """
        Varlık düğümü oluştur veya güncelle
        
        Args:
            entity (Dict): {'text': str, 'label': str, 'sentence': str, ...}
            
        Returns:
            bool: Başarı durumu
        """
        try:
            entity_name = normalize_text(entity['text'].strip())
            entity_label = entity['label']
            norm_key = make_key(entity_name)
            
            # Label'a göre düğüm türünü belirle
            node_label = self._get_node_label(entity_label)
            
            with self.driver.session() as session:
                if node_label == "Date":
                    query = f"""
                    MERGE (n:{node_label} {{normalized_key: $normalized_key}})
                    SET n.value = $name,
                        n.updated_at = datetime(),
                        n.mention_count = COALESCE(n.mention_count, 0) + 1
                    RETURN n.value as name
                    """
                elif node_label in ("Person", "Organization", "Location"):
                    query = f"""
                    MERGE (n:{node_label} {{normalized_key: $normalized_key}})
                    SET n.name = COALESCE(n.name, $name),
                        n.updated_at = datetime(),
                        n.mention_count = COALESCE(n.mention_count, 0) + 1
                    RETURN n.name as name
                    """
                else:
                    # Genel varlık düğümü
                    query = f"""
                    MERGE (n:Entity {{normalized_key: $normalized_key}})
                    SET n.name = COALESCE(n.name, $name),
                        n.type = $type,
                        n.updated_at = datetime(),
                        n.mention_count = COALESCE(n.mention_count, 0) + 1
                    RETURN n.name as name
                    """
                
                result = session.run(query, {
                    'name': entity_name,
                    'type': entity_label,
                    'normalized_key': norm_key,
                })
                
                created_name = result.single()["name"]
                logger.debug(f"{node_label} düğümü oluşturuldu/güncellendi: {created_name}")
                return True
                
        except Exception as e:
            logger.error(f"Varlık düğümü oluşturma hatası: {e}")
            return False
    
    def create_relationship(self, entity1: Dict, entity2: Dict, relation_type: str, document_url: str = None) -> bool:
        """
        İki varlık arasında ilişki oluştur
        
        Args:
            entity1 (Dict): İlk varlık
            entity2 (Dict): İkinci varlık  
            relation_type (str): İlişki türü
            document_url (str): İlişkinin bulunduğu doküman URL'i
            
        Returns:
            bool: Başarı durumu
        """
        try:
            entity1_name = normalize_text(entity1['text'].strip())
            entity2_name = normalize_text(entity2['text'].strip())
            entity1_label = self._get_node_label(entity1['label'])
            entity2_label = self._get_node_label(entity2['label'])
            e1_key = make_key(entity1_name)
            e2_key = make_key(entity2_name)
            
            with self.driver.session() as session:
                query = f"""
                MATCH (e1:{entity1_label} {{normalized_key: $e1_key}})
                MATCH (e2:{entity2_label} {{normalized_key: $e2_key}})
                MERGE (e1)-[r:{relation_type}]->(e2)
                SET r.updated_at = datetime(),
                    r.strength = COALESCE(r.strength, 0) + 1,
                    r.document_url = $document_url
                RETURN r
                """
                
                result = session.run(query, {
                    'e1_key': e1_key,
                    'e2_key': e2_key,
                    'document_url': document_url
                })
                
                if result.single():
                    logger.debug(f"İlişki oluşturuldu: {entity1_name} -{relation_type}-> {entity2_name}")
                    return True
                else:
                    logger.warning(f"İlişki oluşturulamadı: {entity1_name} -{relation_type}-> {entity2_name}")
                    return False
                
        except Exception as e:
            logger.error(f"İlişki oluşturma hatası: {e}")
            return False
    
    def link_entities_to_document(self, entities: List[Dict], document_url: str) -> bool:
        """
        Varlıkları dokümana bağla
        
        Args:
            entities (List[Dict]): Varlık listesi
            document_url (str): Doküman URL'i
            
        Returns:
            bool: Başarı durumu
        """
        try:
            with self.driver.session() as session:
                for entity in entities:
                    entity_name = normalize_text(entity['text'].strip())
                    entity_label = self._get_node_label(entity['label'])
                    norm_key = make_key(entity_name)
                    
                    query = f"""
                    MATCH (doc:Document {{url: $document_url}})
                    MATCH (e:{entity_label} {{normalized_key: $normalized_key}})
                    MERGE (e)-[r:MENTIONED_IN]->(doc)
                    SET r.sentence = $sentence,
                        r.updated_at = datetime()
                    """
                    
                    session.run(query, {
                        'document_url': document_url,
                        'normalized_key': norm_key,
                        'sentence': entity.get('sentence', '')
                    })
                
                logger.info(f"{len(entities)} varlık doküman ile bağlandı: {document_url}")
                return True
                
        except Exception as e:
            logger.error(f"Varlık-doküman bağlama hatası: {e}")
            return False
    
    def _get_node_label(self, entity_label: str) -> str:
        """Varlık etiketini Neo4j düğüm etiketine çevir"""
        label_mapping = {
            'PERSON': 'Person',
            'ORGANIZATION': 'Organization', 
            'LOCATION': 'Location',
            'DATE': 'Date',
            'LEGAL_TERM': 'LegalTerm'
        }
        return label_mapping.get(entity_label, 'Entity')
    
    def get_graph_stats(self) -> Dict:
        """Graf istatistiklerini getir"""
        try:
            with self.driver.session() as session:
                # Düğüm sayıları
                node_counts = {}
                labels = ['Person', 'Organization', 'Location', 'Date', 'Document', 'Entity', 'LegalTerm']
                
                for label in labels:
                    result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                    count = result.single()["count"]
                    node_counts[label] = count
                
                # İlişki sayısı
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                relationship_count = result.single()["count"]
                
                stats = {
                    'nodes': node_counts,
                    'relationships': relationship_count,
                    'total_nodes': sum(node_counts.values())
                }
                
                logger.info(f"Graf istatistikleri: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"İstatistik alma hatası: {e}")
            return {}
    
    def close(self):
        """Neo4j bağlantısını kapat"""
        if hasattr(self, 'driver'):
            self.driver.close()
            logger.info("Neo4j bağlantısı kapatıldı")


# Test fonksiyonu
if __name__ == "__main__":
    builder = GraphBuilder()
    
    # Test varlıkları
    test_entities = [
        {'text': 'Ahmet Yılmaz', 'label': 'PERSON', 'sentence': 'Test cümlesi'},
        {'text': 'Bursa Barosu', 'label': 'ORGANIZATION', 'sentence': 'Test cümlesi'},
        {'text': 'İstanbul', 'label': 'LOCATION', 'sentence': 'Test cümlesi'}
    ]
    
    # Test dokümanı
    test_document = {
        'url': 'https://test.com/test',
        'title': 'Test Doküman',
        'content': 'Bu bir test dokümanıdır.'
    }
    
    print("=== Graf Builder Test ===")
    
    # Doküman oluştur
    builder.create_document_node(test_document)
    
    # Varlıkları oluştur
    for entity in test_entities:
        builder.create_or_update_node(entity)
    
    # Varlıkları dokümana bağla
    builder.link_entities_to_document(test_entities, test_document['url'])
    
    # İlişki oluştur
    builder.create_relationship(test_entities[0], test_entities[1], 'WORKS_AT', test_document['url'])
    
    # İstatistikleri göster
    stats = builder.get_graph_stats()
    print("Graf İstatistikleri:", stats)
    
    builder.close()
