# Kosovo Web Data Collectors - AI-Powered

## 📊 Përmbledhje

Koleksion i shërbimeve për mbledhje automatike të të dhënave nga web-i për rajonin e Kosovës, me AI-powered validation dhe enrichment.

## 🎯 Shërbimet e Implementuara

### 1. ✅ Weather Data Collector
- **Real weather data** për 5 qytetet e Kosovës
- **OpenWeatherMap API** integration
- **Automatic collection** çdo orë
- **AI validation** dhe enrichment

### 2. ✅ Energy Price Collector (Complete)
- Web scraping nga KOSTT, ERO websites
- AI-powered price extraction
- Automatic collection çdo 24 orë
- Kafka integration

### 3. ✅ Consumption Data Collector (Complete)
- Real-time consumption data nga KOSTT
- Regional tracking për 5 rajone
- Historical data collection
- Peak hours detection

### 4. ✅ AI Enhancement Layer (Complete)
- Unified data validation service
- Anomaly detection me statistical analysis
- AI-powered enrichment dhe insights
- Multi-source processing

## 🚀 Quick Start

```bash
# Start weather collector
cd weather-collector
docker-compose up

# Manual collection
curl -X POST http://localhost:5007/api/v1/collect
```

## 📁 Struktura

```
kosovo-data-collectors/
├── weather-collector/       # ✅ Complete (Port 5007)
├── energy-price-collector/  # ✅ Complete (Port 5008)
├── consumption-collector/   # ✅ Complete (Port 5009)
├── ai-enhancement/          # ✅ Complete (Port 5010)
└── shared/                  # Shared utilities
```

## 🔧 Teknologjitë

- Python 3.11
- Flask
- Kafka
- AI/ML libraries (LangChain, OpenAI)
- Web scraping (BeautifulSoup, Scrapy)
