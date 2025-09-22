"""
Bursa Barosu NLP İşleme Modülü
SpaCy mevcut olmadığı için regex tabanlı basit NLP işlemleri yapar.
"""
import re
import logging
from typing import List, Dict, Tuple
import sys
import os

# Config dosyasını import etmek için path ekliyoruz
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import (
    USE_SPACY,
    SPACY_MODEL,
    USE_TRANSFORMERS_NER,
    NER_MODEL_NAME,
    USE_STANZA,
)

# Normalizasyon yardımcıları
from nlp.normalizer import normalize_text

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NLPProcessor:
    """Türkçe metin işleme için NLP sınıfı"""
    
    def __init__(self):
        """NLP Processor'ı başlat"""
        self.use_spacy = USE_SPACY
        self.use_transformers_ner = USE_TRANSFORMERS_NER
        
        if self.use_spacy:
            try:
                import spacy
                self.nlp = spacy.load(SPACY_MODEL)
                logger.info(f"SpaCy modeli yüklendi: {SPACY_MODEL}")
            except Exception as e:
                logger.warning(f"SpaCy yüklenemedi: {e}. Regex tabanlı işleme kullanılacak.")
                self.use_spacy = False
        
        # Transformer tabanlı NER
        self.ner_pipeline = None
        if self.use_transformers_ner:
            try:
                from transformers import pipeline
                self.ner_pipeline = pipeline(
                    task="token-classification",
                    model=NER_MODEL_NAME,
                    aggregation_strategy="simple",
                )
                logger.info(f"Transformers NER modeli yüklendi: {NER_MODEL_NAME}")
            except Exception as e:
                logger.warning(f"Transformers NER yüklenemedi: {e}. Regex tabanlı işleme kullanılacak.")
                self.use_transformers_ner = False
        
        if not self.use_spacy:
            logger.info("Regex tabanlı NLP işleme kullanılıyor")
            self._init_regex_patterns()
    
    def _init_regex_patterns(self):
        """Gelişmiş regex pattern'lerini başlat"""
        # Türkçe isim pattern'leri - daha akıllı
        # Unvan + isim kombinasyonları
        self.person_patterns = [
            # Prof. Dr. Ahmet Yılmaz gibi unvanlı isimler
            re.compile(r'\b(?:Prof\.?\s*Dr\.?|Dr\.?|Doç\.?\s*Dr\.?|Av\.?)\s+[A-ZÇĞIÖŞÜ][a-zçğıöşü]+\s+[A-ZÇĞIÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞIÖŞÜ][a-zçğıöşü]+)*\b'),
            # Başkan/Müdür + isim
            re.compile(r'\b(?:Başkan|Müdür|Dekan|Rektör|Genel\s+Müdür)\s+[A-ZÇĞIÖŞÜ][a-zçğıöşü]+\s+[A-ZÇĞIÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞIÖŞÜ][a-zçğıöşü]+)*\b'),
            # Sadece isim (2-3 kelime)
            re.compile(r'\b[A-ZÇĞIÖŞÜ][a-zçğıöşü]{2,}\s+[A-ZÇĞIÖŞÜ][a-zçğıöşü]{2,}(?:\s+[A-ZÇĞIÖŞÜ][a-zçğıöşü]{2,})?\b')
        ]
        
        # Kurum pattern'leri - çok daha kapsamlı
        self.organization_patterns = [
            # Baro ile ilgili
            re.compile(r'\b(?:Bursa\s+)?Baro(?:su|lar\s+Birliği)?\b', re.IGNORECASE),
            re.compile(r'\bTürkiye\s+Barolar\s+Birliği\b', re.IGNORECASE),
            # Mahkemeler
            re.compile(r'\b\w+\s+(?:Mahkeme|Mahkemesi|Sulh\s+Hukuk\s+Mahkemesi|Asliye\s+Hukuk\s+Mahkemesi)\b', re.IGNORECASE),
            re.compile(r'\b(?:Yargıtay|Danıştay|Anayasa\s+Mahkemesi)\b', re.IGNORECASE),
            # Üniversiteler
            re.compile(r'\b\w+\s+Üniversitesi(?:\s+\w+\s+Fakültesi)?\b', re.IGNORECASE),
            # Bakanlıklar ve kamu kurumları
            re.compile(r'\b(?:Adalet|İçişleri|Dışişleri|Maliye)\s+Bakanlığı\b', re.IGNORECASE),
            re.compile(r'\b\w+\s+(?:Bakanlığı|Müdürlüğü|Başkanlığı)\b', re.IGNORECASE),
            # Dernekler ve vakıflar
            re.compile(r'\b\w+(?:\s+\w+)*\s+(?:Derneği|Vakfı|Federasyonu|Birliği)\b', re.IGNORECASE),
            # Şirketler
            re.compile(r'\b\w+(?:\s+\w+)*\s+(?:A\.Ş\.|Ltd\.?\s*Şti\.?|Şirketi)\b', re.IGNORECASE),
            re.compile(r'\b(?:Bakanlık|Bakanlığı)\b', re.IGNORECASE),
            re.compile(r'\b(?:Müdürlük|Müdürlüğü)\b', re.IGNORECASE),
            re.compile(r'\b(?:Dernek|Derneği)\b', re.IGNORECASE),
            re.compile(r'\b(?:Vakıf|Vakfı)\b', re.IGNORECASE),
            re.compile(r'\b(?:Ltd|A\.Ş\.|Şti)\b', re.IGNORECASE),
            re.compile(r'\b(?:MERKEZİ?|MERKEZ)\b', re.IGNORECASE),
            re.compile(r'\b(?:DANIŞMA|DANIŞ)\b', re.IGNORECASE),
            re.compile(r'\b(?:BİLGİ\s+(?:DANIŞMA\s+)?MERKEZİ?)\b', re.IGNORECASE),
        ]
        
        # Yer pattern'leri
        self.location_patterns = [
            re.compile(r'\bBURSA\b', re.IGNORECASE),
            re.compile(r'\bBursa\b', re.IGNORECASE),
            re.compile(r'\b(?:İstanbul|Ankara|İzmir|Antalya|Adana|Konya)\b', re.IGNORECASE),
            re.compile(r'\b[A-ZÇĞIÖŞÜ][a-zçğıöşü]+\s+(?:İli?|Şehri?|Mahallesi?|Caddesi?|Sokağı?)\b'),
        ]
        
        # Tarih pattern'leri
        self.date_patterns = [
            re.compile(r'\b\d{1,2}[./]\d{1,2}[./]\d{4}\b'),  # 01.01.2023
            re.compile(r'\b\d{4}[./]\d{1,2}[./]\d{1,2}\b'),  # 2023.01.01
            re.compile(r'\b\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}\b', re.IGNORECASE),
        ]
        
        # Hukuki terimler pattern'leri
        self.legal_terms_patterns = [
            re.compile(r'\b(?:AVUKAT|Avukat)\b', re.IGNORECASE),
            re.compile(r'\b(?:HUKUK|Hukuk)\b', re.IGNORECASE),
            re.compile(r'\b(?:DAVA|Dava)\b', re.IGNORECASE),
            re.compile(r'\b(?:MAHKEMESİ?|Mahkeme)\b', re.IGNORECASE),
            re.compile(r'\b(?:SAVCI|Savcı)\b', re.IGNORECASE),
            re.compile(r'\b(?:HAKİM|Hakim)\b', re.IGNORECASE),
        ]
    
    def process_text(self, text: str) -> Dict:
        """
        Metni işleyerek varlıkları ve ilişkileri çıkarır
        
        Args:
            text (str): İşlenecek metin
            
        Returns:
            Dict: Varlıklar ve ilişkiler içeren dictionary
        """
        text = normalize_text(text)
        if self.use_spacy:
            return self._process_with_spacy(text)
        if self.use_transformers_ner and self.ner_pipeline is not None:
            return self._process_with_transformers(text)
        return self._process_with_regex(text)
    
    def _process_with_spacy(self, text: str) -> Dict:
        """SpaCy ile metin işleme (gelecekte kullanım için)"""
        # TODO: SpaCy implementasyonu
        pass
    
    def _process_with_transformers(self, text: str) -> Dict:
        """Hugging Face pipeline ile Türkçe NER ve basit ilişki çıkarımı"""
        entities = []
        relationships = []
        
        # Cümlelere böl (basit)
        sentences = re.split(r'[.!?]+', text)
        
        # NER çalıştır ve cümlelere dağıt
        label_map = {
            'PER': 'PERSON', 'B-PER': 'PERSON', 'I-PER': 'PERSON',
            'ORG': 'ORGANIZATION', 'B-ORG': 'ORGANIZATION', 'I-ORG': 'ORGANIZATION',
            'LOC': 'LOCATION', 'B-LOC': 'LOCATION', 'I-LOC': 'LOCATION',
            # Bazı modeller MISC döndürebilir; şimdilik Entity olarak sayalım
            'MISC': 'Entity'
        }
        
        # Tüm metinde NER
        try:
            ner_results = self.ner_pipeline(text)
        except Exception as e:
            logger.warning(f"NER pipeline hatası, regex'e dönülüyor: {e}")
            return self._process_with_regex(text)
        
        # NER sonuçlarını varlık listesine dönüştür
        for item in ner_results:
            raw_label = item.get('entity_group') or item.get('entity')
            label = label_map.get(raw_label, 'Entity')
            ent_text = item['word'].strip()
            if not ent_text:
                continue
            # Çok kısa/tek kelime filtreleri gerektiğinde eklenebilir
            entities.append({
                'text': ent_text,
                'label': label,
                'sentence_idx': None,
                'sentence': None,
            })
        
        # Ek olarak regex ile Tarih ve Hukuki terimler ekle (transformer NER’de olmayabilir)
        regex_only = self._process_with_regex(text)
        for e in regex_only['entities']:
            if e['label'] in ('DATE', 'LEGAL_TERM'):
                entities.append(e)
        
        # Cümle bazlı ilişki: aynı cümlede geçen farklı tipte varlıklar
        # Basit cümle bölme; ileride Stanza ile geliştirilebilir
        for sentence_idx, sentence in enumerate(sentences):
            s = sentence.strip()
            if len(s) < 10:
                continue
            sent_ents = []
            for ent in entities:
                if ent.get('sentence_idx') is not None:
                    continue
                # kaba eşleme: metindeki span bilgimiz yok; içerme kontrolü
                if ent['text'] and ent['text'] in s:
                    ent_local = ent.copy()
                    ent_local['sentence_idx'] = sentence_idx
                    ent_local['sentence'] = s
                    sent_ents.append(ent_local)
            # farklı tiplerdeki her çiftten ilişki kur
            for i in range(len(sent_ents)):
                for j in range(i + 1, len(sent_ents)):
                    e1, e2 = sent_ents[i], sent_ents[j]
                    if e1['label'] != e2['label']:
                        relationships.append({
                            'entity1': e1['text'],
                            'entity1_label': e1['label'],
                            'entity2': e2['text'],
                            'entity2_label': e2['label'],
                            'relation_type': 'MENTIONED_WITH',
                            'sentence': s,
                            'sentence_idx': sentence_idx,
                        })
        
        # Duplicate temizliği (regex yöntemindekiyle aynı mantık)
        unique_entities = []
        seen_entities = set()
        for entity in entities:
            key = (entity['text'].lower(), entity['label'])
            if key not in seen_entities:
                seen_entities.add(key)
                unique_entities.append(entity)
        
        unique_relationships = []
        seen_relationships = set()
        for rel in relationships:
            key = (rel['entity1'].lower(), rel['entity2'].lower(), rel['relation_type'])
            if key not in seen_relationships:
                seen_relationships.add(key)
                unique_relationships.append(rel)
        
        return {
            'entities': unique_entities,
            'relationships': unique_relationships,
            'total_sentences': len(sentences),
            'processed_sentences': len([s for s in sentences if len(s.strip()) >= 10])
        }
    
    def _process_with_regex(self, text: str) -> Dict:
        """Regex ile metin işleme"""
        entities = []
        relationships = []
        
        # Cümlelere böl
        sentences = re.split(r'[.!?]+', text)
        
        for sentence_idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 10:  # Çok kısa cümleleri atla
                continue
            
            sentence_entities = []
            
            # Kişi isimlerini bul - gelişmiş pattern'lerle
            for pattern in self.person_patterns:
                person_matches = pattern.finditer(sentence)
                for match in person_matches:
                    person_text = match.group().strip()
                    # Çok kısa isimleri filtrele
                    if len(person_text) > 5 and ' ' in person_text:
                        entity = {
                            'text': person_text,
                            'label': 'PERSON',
                            'sentence_idx': sentence_idx,
                            'sentence': sentence
                        }
                        entities.append(entity)
                        sentence_entities.append(entity)
            
            # Kurum isimlerini bul
            for pattern in self.organization_patterns:
                org_matches = pattern.finditer(sentence)
                for match in org_matches:
                    # Kurum isminin tam halini bul (önceki ve sonraki kelimeleri dahil et)
                    start = max(0, match.start() - 50)
                    end = min(len(sentence), match.end() + 50)
                    context = sentence[start:end]
                    
                    # Kurum ismini çıkar
                    org_words = context.split()
                    org_name = match.group()
                    
                    # Önceki kelimeleri kontrol et
                    match_word_idx = -1
                    for i, word in enumerate(org_words):
                        if pattern.search(word):
                            match_word_idx = i
                            break
                    
                    if match_word_idx > 0:
                        # Önceki 1-2 kelimeyi dahil et
                        start_idx = max(0, match_word_idx - 2)
                        org_name = ' '.join(org_words[start_idx:match_word_idx + 1])
                    
                    entity = {
                        'text': org_name.strip(),
                        'label': 'ORGANIZATION',
                        'sentence_idx': sentence_idx,
                        'sentence': sentence
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
                        'sentence': sentence
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
                        'sentence': sentence
                    }
                    entities.append(entity)
                    sentence_entities.append(entity)
            
            # Hukuki terimleri bul
            for pattern in self.legal_terms_patterns:
                legal_matches = pattern.finditer(sentence)
                for match in legal_matches:
                    entity = {
                        'text': match.group().strip(),
                        'label': 'LEGAL_TERM',
                        'sentence_idx': sentence_idx,
                        'sentence': sentence
                    }
                    entities.append(entity)
                    sentence_entities.append(entity)
            
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
                            'sentence': sentence,
                            'sentence_idx': sentence_idx
                        }
                        relationships.append(relationship)
        
        # Duplicate'leri temizle
        unique_entities = []
        seen_entities = set()
        for entity in entities:
            entity_key = (entity['text'].lower(), entity['label'])
            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                unique_entities.append(entity)
        
        unique_relationships = []
        seen_relationships = set()
        for rel in relationships:
            rel_key = (rel['entity1'].lower(), rel['entity2'].lower(), rel['relation_type'])
            if rel_key not in seen_relationships:
                seen_relationships.add(rel_key)
                unique_relationships.append(rel)
        
        result = {
            'entities': unique_entities,
            'relationships': unique_relationships,
            'total_sentences': len(sentences),
            'processed_sentences': len([s for s in sentences if len(s.strip()) >= 10])
        }
        
        logger.info(f"Metin işlendi: {len(unique_entities)} varlık, {len(unique_relationships)} ilişki bulundu")
        
        return result


# Test fonksiyonu
if __name__ == "__main__":
    processor = NLPProcessor()
    
    # Test metni
    test_text = """
    Bursa Barosu Başkanı Ahmet Yılmaz, 15 Ocak 2024 tarihinde İstanbul'da düzenlenen 
    toplantıya katıldı. Toplantıda Adalet Bakanlığı temsilcileri de hazır bulundu. 
    Bursa Üniversitesi Hukuk Fakültesi Dekanı Prof. Dr. Mehmet Özkan da konuşma yaptı.
    """
    
    result = processor.process_text(test_text)
    
    print("=== BULUNAN VARLIKLAR ===")
    for entity in result['entities']:
        print(f"- {entity['text']} ({entity['label']})")
    
    print("\n=== BULUNAN İLİŞKİLER ===")
    for rel in result['relationships']:
        print(f"- {rel['entity1']} ({rel['entity1_label']}) -> {rel['relation_type']} -> {rel['entity2']} ({rel['entity2_label']})")
    
    print(f"\nToplam cümle: {result['total_sentences']}")
    print(f"İşlenen cümle: {result['processed_sentences']}")
