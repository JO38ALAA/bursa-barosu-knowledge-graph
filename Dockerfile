# Bursa Barosu Knowledge Graph API Dockerfile
FROM python:3.12-slim

# Sistem paketlerini güncelle ve gerekli paketleri kur
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# Python requirements'ı kopyala ve kur
COPY bursa_baro_kg/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY bursa_baro_kg/ ./bursa_baro_kg/

# Çalışma dizinini bursa_baro_kg olarak ayarla
WORKDIR /app/bursa_baro_kg

# Port'u expose et
EXPOSE 8000

# Health check ekle
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Uygulamayı başlat
CMD ["python", "api/main.py"]
