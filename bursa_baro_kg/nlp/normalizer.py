"""
Metin normalizasyon ve anahtar üretim yardımcıları
"""
import re
import unicodedata

# Türkçe özel karakterleri ASCII'ye yaklaştırmak için tablo (isteğe bağlı)
_TR_ASCII_MAP = str.maketrans({
    "ç": "c", "Ç": "c",
    "ğ": "g", "Ğ": "g",
    "ı": "i", "I": "i",
    "İ": "i",
    "ö": "o", "Ö": "o",
    "ş": "s", "Ş": "s",
    "ü": "u", "Ü": "u",
})

def normalize_text(text: str) -> str:
    """Görüntüleme için hafif normalizasyon: boşluk temizleme, unicode düzenleme"""
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def make_key(text: str, ascii_fold: bool = True) -> str:
    """Eşleşme anahtarı: küçük harfe çevir, unicode normalize, opsiyonel ASCII fold
    Bu anahtar Neo4j'de normalized_key alanında tutulur ve MATCH işlemlerinde kullanılır.
    """
    if not text:
        return ""
    t = normalize_text(text).lower()
    if ascii_fold:
        t = t.translate(_TR_ASCII_MAP)
        t = unicodedata.normalize("NFKD", t)
        t = "".join(ch for ch in t if not unicodedata.combining(ch))
    # noktalama ve gereksiz karakterleri kaldır
    t = re.sub(r"[^a-z0-9\s._-]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t
