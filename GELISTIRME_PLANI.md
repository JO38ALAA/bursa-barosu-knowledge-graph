# Geliştirme Planı ve Notları

Bu doküman, Bursa Barosu Bilgi Grafı projesinde yapılan iyileştirmeleri ve gelecek planlarını özetlemektedir.

## Tamamlanan İyileştirmeler (Aşama 1)

Bu aşamadaki temel hedef, "ilişki kurulamadı" hatalarını çözmek, varlık tanıma doğruluğunu artırmak ve daha sağlam bir graf mimarisi oluşturmaktı.

### 1. Varlık Tanıma (NER) Güçlendirildi
- **Eski Yöntem:** Regex tabanlı, hataya açık varlık tanıma.
- **Yeni Yöntem:** Türkçe metinler için özel olarak eğitilmiş, modern bir Transformer (AI) modeli olan `savasy/bert-base-turkish-ner-cased` entegre edildi.
- **Kazanım:** Kişi, Kurum ve Yer isimleri artık çok daha yüksek doğrulukla tespit ediliyor.

### 2. Normalizasyon ve Tekilleştirme
- **Problem:** "Bursa Barosu", "bursa barosu" gibi farklı yazımlar ayrı varlıklar olarak kabul ediliyordu.
- **Çözüm:** Her varlık için tekil bir anahtar (`normalized_key`) üreten bir normalizasyon katmanı eklendi. Bu katman, büyük/küçük harf, Türkçe karakterler ve fazla boşlukları standart hale getirir.
- **Kazanım:** Aynı varlığın grafikte birden çok kopyasının oluşması engellendi.

### 3. Graf Mimarisi İyileştirildi
- **Problem:** İlişkiler, isimlerdeki küçük farklılıklar nedeniyle doğru düğümleri bulamıyordu.
- **Çözüm:** Neo4j'deki tüm düğüm oluşturma, eşleştirme ve ilişki kurma işlemleri artık `normalized_key` üzerinden yapılıyor. Bu anahtar üzerine `index` (dizin) oluşturularak performans da artırıldı.
- **Kazanım:** "İlişki oluşturulamadı" hataları büyük ölçüde çözüldü ve graf bütünlüğü sağlandı.

### 4. Sistem Altyapısı Güncellendi
- `requirements.txt` dosyasına `transformers`, `torch` ve `rapidfuzz` gibi modern AI kütüphaneleri eklendi.
- Projenin Docker imajı, bu yeni bağımlılıklar ve kod değişiklikleriyle güncellendi.

---

## Gelecek Planları (Yol Haritası)

### Aşama 2: İlişki Kalitesini ve Anlamını Artırma (Kısa Vade)
- **Hedef:** Mevcut `MENTIONED_WITH` (Birlikte Anıldı) ilişkisini daha anlamlı ve spesifik ilişkilerle zenginleştirmek.
- **Yapılacaklar:**
    1. **Kural Tabanlı İlişki Çıkarımı:** Türkçe dil yapısına uygun kalıplar (örn. "X'in başkanı", "Y'ye katıldı") kullanarak `BAŞKANIDIR`, `ÜYESİDİR`, `KATILDI` gibi spesifik ilişkiler üretmek.
    2. **Gelişmiş İlişki Çıkarımı (RE Modeli):** Opsiyonel olarak `Babelscape/mrebel-large` gibi çok dilli RE modellerini entegre ederek kuralların kaçırdığı daha karmaşık ilişkileri yakalamak.
    3. **Güven Skoru:** Her ilişkiye bir `strength` (güç) veya `confidence` (güven) skoru ekleyerek, bilginin ne kadar güvenilir olduğunu modellemek.

### Aşama 3: Performans, Ölçeklenebilirlik ve Kullanıcı Geri Bildirimi (Orta Vade)
- **Hedef:** Veri miktarı arttıkça sistemin hızlı çalışmasını sağlamak ve graf kalitesini sürekli iyileştirmek.
- **Yapılacaklar:**
    1. **Önbellekleme (Caching):** AI model sonuçlarını `cache` mekanizmasıyla saklayarak aynı metinlerin tekrar işlenmesini önlemek ve hızı artırmak.
    2. **Fuzzy Eşleştirme:** `rapidfuzz` kütüphanesi ile "Ahmet Yılmaz" ve "Ahmet Yilmaz" gibi çok benzer ama tam eşleşmeyen isimleri de aynı varlık olarak birleştirmek.
    3. **Geri Bildirim Döngüsü:** Arayüz üzerinden kullanıcıların hatalı verileri (yanlış ilişki, hatalı varlık) bildirmesine olanak tanıyan bir mekanizma kurmak.
