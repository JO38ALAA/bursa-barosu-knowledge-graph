# Proje Başlatma: Bursa Barosu için Bilgi Grafı ve Arama Sistemi

Merhaba, sen Python dilinde veri boru hatları, NLP ve graf veritabanları konusunda uzman bir asistansın. "Bursa Barosu" web sitesi için bir bilgi grafı ve semantik arama sistemi prototipi oluşturmak istiyorum. Projeyi modüler bir yapıda, adım adım inşa etmeme yardımcı olmanı istiyorum.

**Projenin Amacı:** `bursabarosu.org.tr` sitesindeki metin içeriklerini tarayarak bu içeriklerden anlamlı varlıkları (kişi, kurum, tarih vb.) ve aralarındaki ilişkileri çıkaran, bunları bir Neo4j graf veritabanında saklayan bir sistem kurmak.

**Kullanılacak Teknolojiler:**
- **Python 3.10+**
- **Veri Çekme:** `requests`, `beautifulsoup4`
- **NLP:** `spacy` ve `tr_core_news_sm` Türkçe modeli
- **Veritabanı:** `neo4j` Python driver
- **Yardımcı:** `tqdm`

Lütfen aşağıdaki dosya yapısını ve her dosyanın içeriği için başlangıç kodlarını oluştur. Kodların içinde açıklamalar, "TODO" yorumları ve en iyi pratikleri (hata yönetimi, modülerlik) içermesine özen göster.

### 1. Proje Dosya Yapısı

Lütfen aşağıdaki gibi bir klasör ve dosya yapısı öner ve her bir dosyanın görevini açıkla:

```
bursa_baro_kg/
|
|-- crawler/
|   |-- __init__.py
|   |-- scraper.py
|
|-- nlp/
|   |-- __init__.py
|   |-- processor.py
|
|-- graph/
|   |-- __init__.py
|   |-- builder.py
|
|-- data/
|   |-- raw/         # Taranan ham JSON dosyaları buraya gelecek
|   |-- processed/   # NLP ile işlenmiş yapısal JSON dosyaları buraya gelecek
|
|-- main.py          # Tüm süreci yöneten ana script
|-- config.py        # Neo4j bağlantı bilgileri gibi ayarlar
|-- requirements.txt # Gerekli kütüphaneler
```

### 2. Dosyaların İçerikleri için Başlangıç Kodları

**a) `requirements.txt`**
Bu dosyayı gerekli kütüphanelerle doldur.

**b) `config.py`**
Neo4j bağlantı bilgilerini (URI, USER, PASSWORD) içerecek şekilde bu dosyayı oluştur.

**c) `crawler/scraper.py`**
- `BursaBaroScraper` adında bir sınıf oluştur.
- Bu sınıfın `fetch_sitemap()` metodu `sitemap.xml` dosyasını çekip içindeki tüm URL'leri bir liste olarak döndürsün.
- `scrape_page(url)` metodu, verilen bir URL'deki sayfanın başlığını ve ana metin içeriğini (örneğin `<article>` veya `.content` gibi bir alandan) ayıklasın. Sonuç olarak bir dictionary (`{'url': url, 'title': title, 'content': content}`) döndürsün. Hata yönetimi için `try-except` blokları kullansın.

**d) `nlp/processor.py`**
- `NLPProcessor` adında bir sınıf oluştur.
- `__init__` metodunda, `spacy`'nin `tr_core_news_sm` modelini yüklesin.
- `process_text(text)` adında bir metot oluştur. Bu metot, ham metni alsın ve spaCy kullanarak içindeki varlıkları (Kişi - `PER`, Organizasyon - `ORG`, Yer - `LOC`, Tarih - `DATE`) tespit etsin.
- Sonuç olarak varlıkların listesini (`[{'text': 'Ahmet Yılmaz', 'label': 'PER'}, ...]`) ve cümleler arasındaki basit ilişkileri (aynı cümlede geçen varlıklar) içeren bir dictionary döndürsün.

**e) `graph/builder.py`**
- `GraphBuilder` adında bir sınıf oluştur.
- `__init__` metodunda `config.py` dosyasından aldığı bilgilerle Neo4j veritabanına bağlantı kursun. Bir de `close()` metodu ile bağlantıyı kapatsın.
- `create_or_update_node(entity)` metodu, bir varlık (entity) dict'ini alsın ve Neo4j'de bu varlık için `MERGE` komutunu kullanarak bir düğüm oluştursun. (Örn: `MERGE (n:Person {name: 'Ahmet Yılmaz'})`)
- `create_relationship(entity1, entity2, relation_type)` metodu, iki varlık arasında bir ilişki oluştursun.

**f) `main.py`**
- Bu script tüm akışın yöneticisi (orchestrator) olsun.
- Adım 1: `BursaBaroScraper`'ı kullanarak tüm URL'leri çeksin.
- Adım 2: `tqdm` ile bir ilerleme çubuğu göstererek her bir URL için sayfayı kazısın ve `data/raw/` klasörüne JSON olarak kaydetsin.
- Adım 3: `data/raw/` klasöründeki her bir JSON dosyası için `NLPProcessor`'ı kullanarak veriyi işlesin ve `data/processed/` klasörüne yeni JSON olarak kaydetsin.
- Adım 4: `data/processed/` klasöründeki her bir dosya için `GraphBuilder`'ı kullanarak düğümleri ve ilişkileri Neo4j veritabanına yazsın.
- Her adımda ne yapıldığını konsola yazdırsın.

Lütfen bu yapıya uygun, çalıştırılabilir ve iyi belgelenmiş başlangıç kodlarını üret.