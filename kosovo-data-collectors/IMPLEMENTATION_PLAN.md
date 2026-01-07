# Kosovo Data Collectors - Implementation Plan

## 🎯 Qëllimi

Krijo shërbime të pavarura për mbledhje automatike të të dhënave nga web-i për rajonin e Kosovës, me AI-powered validation dhe enrichment.

## 📋 Faza e Implementimit

### ✅ Faza 1: Weather Data Collector (Complete)

**Status**: ✅ **100% Complete**

**Features:**
- ✅ Real weather data për 5 qytetet e Kosovës (Prishtinë, Prizren, Pejë, Gjilan, Mitrovicë)
- ✅ OpenWeatherMap API integration
- ✅ Automatic collection çdo orë
- ✅ AI validation dhe enrichment
- ✅ Kafka integration
- ✅ Docker Compose setup
- ✅ REST API endpoints

**Files:**
- `weather-collector/app.py` - Main application
- `weather-collector/Dockerfile` - Docker image
- `weather-collector/docker-compose.yml` - Service orchestration
- `weather-collector/requirements.txt` - Dependencies
- `weather-collector/start.sh` - Startup script

**Usage:**
```bash
cd weather-collector
./start.sh
```

---

### ✅ Faza 2: Energy Price Collector (Complete)

**Status**: ✅ **100% Complete**

**Features:**
- ✅ Web scraping nga KOSTT website
- ✅ Web scraping nga ERO website
- ✅ AI-powered price extraction me regex patterns
- ✅ Automatic collection çdo 24 orë
- ✅ Kafka integration
- ✅ REST API endpoints
- 🚧 PDF parsing për tariff reports (Next)
- 🚧 LLM extraction me LangChain (Next)
- 🚧 ML për parashikim çmimesh (Next)

**Implementation:**
```python
# energy-price-collector/app.py
from bs4 import BeautifulSoup
import requests
from langchain import LLMChain
import pdfplumber

def scrape_kostt_tariffs():
    """Scrape tariffs nga KOSTT website"""
    url = "https://kostt.com/PublicConsumer/Tariff"
    # Implementation...
```

**Dependencies:**
- beautifulsoup4
- scrapy
- pdfplumber
- langchain
- openai (optional)

---

### 🚧 Faza 3: Consumption Data Collector

**Status**: 🚧 **Planned**

**Features:**
- Real-time consumption data nga KOSTT dashboard
- Historical data collection
- Data validation me AI
- Kafka integration
- PostgreSQL storage

---

### 🚧 Faza 4: AI Enhancement Layer

**Status**: 🚧 **Planned**

**Features:**
- Unified AI validation service
- Data enrichment me LLMs
- Anomaly detection
- Data quality scoring
- Automated alerts

---

## 🏗️ Arkitektura

```
┌─────────────────────────────────────────┐
│     Kosovo Data Collectors Suite       │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │   Weather    │  │ Energy Price │   │
│  │  Collector   │  │  Collector   │   │
│  └──────┬───────┘  └──────┬───────┘   │
│         │                  │           │
│         └──────────┬───────┘           │
│                    ▼                   │
│            ┌─────────────┐             │
│            │    Kafka    │             │
│            │   Topics    │             │
│            └─────────────┘             │
│                    │                   │
│                    ▼                   │
│            ┌─────────────┐             │
│            │  Processing │             │
│            │   Pipeline  │             │
│            └─────────────┘             │
│                                         │
└─────────────────────────────────────────┘
```

## 🔧 Teknologjitë

### Core:
- **Python 3.11**
- **Flask** - REST API
- **Kafka** - Event streaming
- **Docker** - Containerization

### AI/ML:
- **LangChain** - LLM integration
- **OpenAI/Anthropic** - LLM APIs (optional)
- **BeautifulSoup4** - HTML parsing
- **Scrapy** - Web crawling
- **pdfplumber** - PDF parsing
- **Tesseract OCR** - Image text extraction

### Data Storage:
- **PostgreSQL** - Structured data
- **Redis** - Caching
- **MongoDB** - Document storage (optional)

## 📅 Timeline

### Muaji 1 (Current):
- ✅ Weather Data Collector
- ✅ Energy Price Collector (Complete)

### Muaji 2:
- ✅ Energy Price Collector (Complete)
- 🚧 Consumption Data Collector

### Muaji 3:
- ✅ Consumption Data Collector (Complete)
- 🚧 AI Enhancement Layer

### Muaji 4:
- ✅ AI Enhancement Layer (Complete)
- 🚧 Integration dhe testing

## 🚀 Quick Start Guide

### Weather Collector:
```bash
cd weather-collector
cp .env.example .env
# Edit .env and add OPENWEATHER_API_KEY
./start.sh
```

### Test:
```bash
# Health check
curl http://localhost:5007/health

# List cities
curl http://localhost:5007/api/v1/cities

# Manual collection
curl -X POST http://localhost:5007/api/v1/collect
```

## 📝 Next Steps

1. **Energy Price Collector**: Start me KOSTT website scraping
2. **PDF Parser**: Implement AI-powered PDF extraction
3. **Consumption Collector**: Design për KOSTT dashboard integration
4. **AI Enhancement**: Create unified validation service

## 🔗 Resources

- **OpenWeatherMap API**: https://openweathermap.org/api
- **KOSTT**: https://kostt.com
- **ERO**: https://ero-ks.org
- **KEK**: https://kek-energy.com
