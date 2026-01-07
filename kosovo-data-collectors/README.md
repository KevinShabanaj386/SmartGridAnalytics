# Kosovo Web Data Collectors - AI-Powered

## 📊 Përmbledhje

Koleksion i shërbimeve për mbledhje automatike të të dhënave nga web-i për rajonin e Kosovës, me AI-powered validation dhe enrichment.

## 🎯 Shërbimet e Implementuara

### 1. ✅ Weather Data Collector
- **Real weather data** për 5 qytetet e Kosovës
- **OpenWeatherMap API** integration
- **Automatic collection** çdo orë
- **AI validation** dhe enrichment

### 2. 🚧 Energy Price Collector (Next)
- Web scraping nga KOSTT, ERO websites
- PDF parsing me AI
- NLP extraction

### 3. 🚧 Consumption Data Collector (Next)
- Real-time consumption data nga KOSTT
- Historical data collection

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
├── weather-collector/       # ✅ Implementuar
├── energy-price-collector/  # 🚧 Next
├── consumption-collector/   # 🚧 Next
└── shared/                  # Shared utilities
```

## 🔧 Teknologjitë

- Python 3.11
- Flask
- Kafka
- AI/ML libraries (LangChain, OpenAI)
- Web scraping (BeautifulSoup, Scrapy)
