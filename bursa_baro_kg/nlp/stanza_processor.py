"""
Bursa Barosu Gelişmiş NLP İşleme Modülü - Stanza ile
Stanford NLP Stanza kullanarak Türkçe metin işleme
"""
import stanza
import logging
from typing import List, Dict, Tuple
import sys
import os
import re

# Config dosyasını import etmek için path ekliyoruz
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import USE_SPACY, SPACY_MODEL

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StanzaNLPProcessor:
    """Stanza tabanlı gelişmiş Türkçe NLP işlemcisi"""
    
    def __init__(self):
        """Stanza NLP Processor'ı başlat"""
        try:
            logger.info("Stanza Türkçe modeli yükleniyor...")
            self.nlp = stanza.Pipeline(
                lang='tr',
                processors='tokenize,pos,lemma,ner',
                use_gpu=False,
                verbose=False
            )
            logger.info("Stanza Türkçe modeli başarıyla yüklendi")
            self.use_stanza = True
        except Exception as e:
            logger.error(f"Stanza yüklenemedi: {e}. Regex tabanlı işleme kullanılacak.")
            self.use_stanza = False
            self._init_regex_patterns()
    
    def _init_regex_patterns(self):
        """Fallback regex pattern'lerini başlat"""
        # Türkçe isim pattern'leri
        self.person_pattern = re.compile(r'\b[A-ZÇĞIÖŞÜ][a-zçğıöşü]+\s+[A-ZÇĞIÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞIÖŞÜ][a-zçğıöşü]+)*\b')
        
        # Kurum pattern'leri
        self.organization_patterns = [
            re.compile(r'\b(?:BURSA\s+)?BARO(?:SU)?\b', re.IGNORECASE),
            re.compile(r'\b(?:Barosu?|Baro)\b', re.IGNORECASE),
            re.compile(r'\b(?:Mahkeme|Mahkemesi)\b', re.IGNORECASE),
            re.compile(r'\b(?:Üniversite|Üniversitesi)\b', re.IGNORECASE),
            re.compile(r'\b(?:Bakanlık|Bakanlığı)\b', re.IGNORECASE),
            re.compile(r'\b(?:Müdürlük|Müdürlüğü)\b', re.IGNORECASE),
            re.compile(r'\b(?:Dernek|Derneği)\b', re.IGNORECASE),
            re.compile(r'\b(?:Vakıf|Vakfı)\b', re.IGNORECASE),
            re.compile(r'\b(?:Ltd|A\.Ş\.|Şti)\b', re.IGNORECASE),
            re.compile(r'\b(?:MERKEZİ?|MERKEZ)\b', re.IGNORECASE),
            re.compile(r'\b(?:BİLGİ\s+(?:DANIŞMA\s+)?MERKEZİ?)\b', re.IGNORECASE),
        ]
        
        # Yer pattern'leri
        self.location_patterns = [
            re.compile(r'\bBURSA\b', re.IGNORECASE),
            re.compile(r'\bBursa\b', re.IGNORECASE),
            re.compile(r'\b(?:İstanbul|Ankara|İzmir|Antalya|Adana|Konya)\b', re.IGNORECASE),
        ]
        
        # Tarih pattern'leri
        self.date_patterns = [
            re.compile(r'\b\d{1,2}[./]\d{1,2}[./]\d{4}\b'),
            re.compile(r'\b\d{4}[./]\d{1,2}[./]\d{1,2}\b'),
            re.compile(r'\b\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}\b', re.IGNORECASE),
        ]
    
    def process_text(self, text: str) -> Dict:
        """
        Metni işleyerek varlıkları ve ilişkileri çıkarır
        
        Args:
            text (str): İşlenecek metin
            
        Returns:
            Dict: Varlıklar ve ilişkiler içeren dictionary
        """
        if self.use_stanza:
            return self._process_with_stanza(text)
        else:
            return self._process_with_regex(text)
    
    def _process_with_stanza(self, text: str) -> Dict:
        """Stanza ile gelişmiş metin işleme"""
        entities = []
        relationships = []
        
        try:
            # Stanza ile metni işle
            doc = self.nlp(text)
            
            # Her cümleyi işle
            for sent_idx, sentence in enumerate(doc.sentences):
                sentence_text = sentence.text
                sentence_entities = []
                
                # Named Entity Recognition (NER)
                for ent in sentence.ents:
                    entity_text = ent.text.strip()
                    entity_type = self._map_stanza_entity_type(ent.type)
                    
                    if len(entity_text) > 1 and entity_type:  # Tek karakterli varlıkları filtrele
                        entity = {
                            'text': entity_text,
                            'label': entity_type,
                            'sentence_idx': sent_idx,
                            'sentence': sentence_text,
                            'confidence': 1.0  # Stanza confidence score
                        }
                        entities.append(entity)
                        sentence_entities.append(entity)
                
                # Ek pattern tabanlı varlık tanıma (Stanza'nın kaçırdıklarını yakala)
                additional_entities = self._extract_additional_entities(sentence_text, sent_idx)
                entities.extend(additional_entities)
                sentence_entities.extend(additional_entities)
                
                # Aynı cümlede bulunan varlıklar arasında ilişki kur
                for i in range(len(sentence_entities)):
                    for j in range(i + 1, len(sentence_entities)):
                        entity1 = sentence_entities[i]
                        entity2 = sentence_entities[j]
                        
                        # Aynı tip varlıklar arasında ilişki kurma
                        if entity1['label'] != entity2['label']:
                            relationship = {
                                'entity1': entity1['text'],
                                'entity1_label': entity1['label'],
                                'entity2': entity2['text'],
                                'entity2_label': entity2['label'],
                                'relation_type': 'MENTIONED_WITH',
                                'sentence': sentence_text,
                                'sentence_idx': sent_idx,
                                'confidence': min(entity1.get('confidence', 1.0), entity2.get('confidence', 1.0))
                            }
                            relationships.append(relationship)
            
            # Duplicate'leri temizle
            unique_entities = self._remove_duplicate_entities(entities)
            unique_relationships = self._remove_duplicate_relationships(relationships)
            
            result = {
                'entities': unique_entities,
                'relationships': unique_relationships,
                'total_sentences': len(doc.sentences),
                'processed_sentences': len(doc.sentences),
                'nlp_method': 'stanza'
            }
            
            logger.info(f"Stanza ile metin işlendi: {len(unique_entities)} varlık, {len(unique_relationships)} ilişki bulundu")
            
        except Exception as e:
            logger.error(f"Stanza işleme hatası: {e}")
            # Fallback to regex
            result = self._process_with_regex(text)
        
        return result
    
    def _map_stanza_entity_type(self, stanza_type: str) -> str:
        """Stanza varlık tiplerini kendi tipimize çevir"""
        type_mapping = {
            'PER': 'PERSON',        # Person
            'PERSON': 'PERSON',
            'ORG': 'ORGANIZATION',  # Organization
            'ORGANIZATION': 'ORGANIZATION',
            'LOC': 'LOCATION',      # Location
            'LOCATION': 'LOCATION',
            'GPE': 'LOCATION',      # Geopolitical entity
            'DATE': 'DATE',
            'TIME': 'DATE',
            'MONEY': 'MONETARY',
            'PERCENT': 'PERCENTAGE',
            'MISC': 'MISCELLANEOUS'
        }
        return type_mapping.get(stanza_type.upper(), 'ENTITY')
    
    def _extract_additional_entities(self, sentence: str, sent_idx: int) -> List[Dict]:
        """Stanza'nın kaçırdığı varlıkları pattern ile yakala"""
        additional_entities = []
        
        # Hukuki terimler
        legal_terms = ['avukat', 'hukuk', 'dava', 'mahkeme', 'hakim', 'savcı', 'kanun', 'yasa']
        for term in legal_terms:
            if term.lower() in sentence.lower():
                # Tam kelime eşleşmesi kontrol et
                pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                matches = pattern.finditer(sentence)
                for match in matches:
                    entity = {
                        'text': match.group(),
                        'label': 'LEGAL_TERM',
                        'sentence_idx': sent_idx,
                        'sentence': sentence,
                        'confidence': 0.8  # Pattern tabanlı düşük confidence
                    }
                    additional_entities.append(entity)
        
        # Kurum isimleri (Stanza'nın kaçırdıkları)
        org_patterns = [
            r'\b(?:Bursa\s+)?Baro(?:su)?\b',
            r'\b\w+\s+(?:Bakanlığı?|Müdürlüğü?|Derneği?|Vakfı?)\b',
            r'\b\w+\s+(?:Üniversitesi?|Mahkemesi?)\b'
        ]
        
        for pattern_str in org_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.finditer(sentence)
            for match in matches:
                entity_text = match.group().strip()
                if len(entity_text) > 3:  # Çok kısa eşleşmeleri filtrele
                    entity = {
                        'text': entity_text,
                        'label': 'ORGANIZATION',
                        'sentence_idx': sent_idx,
                        'sentence': sentence,
                        'confidence': 0.7
                    }
                    additional_entities.append(entity)
        
        return additional_entities
    
    def _process_with_regex(self, text: str) -> Dict:
        """Fallback regex ile metin işleme (eski yöntem)"""
        entities = []
        relationships = []
        
        # Cümlelere böl
        sentences = re.split(r'[.!?]+', text)
        
        for sentence_idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            sentence_entities = []
            
            # Kişi isimlerini bul
            person_matches = self.person_pattern.findall(sentence)
            for match in person_matches:
                entity = {
                    'text': match.strip(),
                    'label': 'PERSON',
                    'sentence_idx': sentence_idx,
                    'sentence': sentence,
                    'confidence': 0.6
                }
                entities.append(entity)
                sentence_entities.append(entity)
            
            # Kurum isimlerini bul
            for pattern in self.organization_patterns:
                org_matches = pattern.finditer(sentence)
                for match in org_matches:
                    entity = {
                        'text': match.group().strip(),
                        'label': 'ORGANIZATION',
                        'sentence_idx': sentence_idx,
                        'sentence': sentence,
                        'confidence': 0.6
                    }
                    entities.append(entity)
                    sentence_entities.append(entity)
            
            # Yer isimlerini bul
            for pattern in self.location_patterns:
                loc_matches = pattern.finditer(sentence)
                for match in loc_matches:
                    entity = {
                        'text': match.group().strip(),
                        'label': 'LOCATION',
                        'sentence_idx': sentence_idx,
                        'sentence': sentence,
                        'confidence': 0.6
                    }
                    entities.append(entity)
                    sentence_entities.append(entity)
            
            # Tarihleri bul
            for pattern in self.date_patterns:
                date_matches = pattern.finditer(sentence)
                for match in date_matches:
                    entity = {
                        'text': match.group().strip(),
                        'label': 'DATE',
                        'sentence_idx': sentence_idx,
                        'sentence': sentence,
                        'confidence': 0.8
                    }
                    entities.append(entity)
                    sentence_entities.append(entity)
            
            # İlişkileri kur
            for i in range(len(sentence_entities)):
                for j in range(i + 1, len(sentence_entities)):
                    entity1 = sentence_entities[i]
                    entity2 = sentence_entities[j]
                    
                    if entity1['label'] != entity2['label']:
                        relationship = {
                            'entity1': entity1['text'],
                            'entity1_label': entity1['label'],
                            'entity2': entity2['text'],
                            'entity2_label': entity2['label'],
                            'relation_type': 'MENTIONED_WITH',
                            'sentence': sentence,
                            'sentence_idx': sentence_idx,
                            'confidence': 0.5
                        }
                        relationships.append(relationship)
        
        # Duplicate'leri temizle
        unique_entities = self._remove_duplicate_entities(entities)
        unique_relationships = self._remove_duplicate_relationships(relationships)
        
        result = {
            'entities': unique_entities,
            'relationships': unique_relationships,
            'total_sentences': len(sentences),
            'processed_sentences': len([s for s in sentences if len(s.strip()) >= 10]),
            'nlp_method': 'regex'
        }
        
        logger.info(f"Regex ile metin işlendi: {len(unique_entities)} varlık, {len(unique_relationships)} ilişki bulundu")
        
        return result
    
    def _remove_duplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Duplicate varlıkları temizle"""
        unique_entities = []
        seen_entities = set()
        
        for entity in entities:
            entity_key = (entity['text'].lower().strip(), entity['label'])
            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _remove_duplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """Duplicate ilişkileri temizle"""
        unique_relationships = []
        seen_relationships = set()
        
        for rel in relationships:
            rel_key = (
                rel['entity1'].lower().strip(),
                rel['entity2'].lower().strip(),
                rel['relation_type']
            )
            if rel_key not in seen_relationships:
                seen_relationships.add(rel_key)
                unique_relationships.append(rel)
        
        return unique_relationships


# Test fonksiyonu
if __name__ == "__main__":
    processor = StanzaNLPProcessor()
    
    # Test metni
    test_text = """
    Bursa Barosu Başkanı Ahmet Yılmaz, 15 Ocak 2024 tarihinde İstanbul'da düzenlenen 
    toplantıya katıldı. Toplantıda Adalet Bakanlığı temsilcileri de hazır bulundu. 
    Bursa Üniversitesi Hukuk Fakültesi Dekanı Prof. Dr. Mehmet Özkan da konuşma yaptı.
    Avukatların haklarını korumak için yeni bir kanun tasarısı hazırlanıyor.
    """
    
    result = processor.process_text(test_text)
    
    print(f"=== NLP Yöntemi: {result.get('nlp_method', 'unknown')} ===")
    print("=== BULUNAN VARLIKLAR ===")
    for entity in result['entities']:
        confidence = entity.get('confidence', 1.0)
        print(f"- {entity['text']} ({entity['label']}) - Güven: {confidence:.2f}")
    
    print("\n=== BULUNAN İLİŞKİLER ===")
    for rel in result['relationships'][:10]:  # İlk 10 ilişki
        confidence = rel.get('confidence', 1.0)
        print(f"- {rel['entity1']} ({rel['entity1_label']}) -> {rel['relation_type']} -> {rel['entity2']} ({rel['entity2_label']}) - Güven: {confidence:.2f}")
    
    print(f"\nToplam cümle: {result['total_sentences']}")
    print(f"İşlenen cümle: {result['processed_sentences']}")
