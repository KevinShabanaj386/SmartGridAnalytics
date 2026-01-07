# Web Data Integration me AI për Rajonin e Kosovës

## 📊 Përmbledhje

Ky dokument paraqet ide dhe strategji për integrimin e të dhënave automatike nga web-i përmes AI për rajonin e Kosovës në Smart Grid Analytics.

---

## 🎯 Burimet e Të Dhënave për Kosovën

### 1. Të Dhëna Moti (Weather Data) 🌤️

**Burime publike:**
- **OpenWeatherMap API**: Të dhëna reale për Prishtinë, Prizren, Pejë, Gjilan, Mitrovicë
- **Meteoblue API**: Të dhëna të detajuara për rajonet e Kosovës
- **MeteoKosova** (nëse ka API publik): Të dhëna lokale
- **Weather Underground**: Historical dhe real-time data

**Të dhënat e nevojshme:**
- Temperatura (°C)
- Lagështia (%)
- Presioni atmosferik (hPa)
- Shpejtësia e erës (km/h)
- Konsumimi i energjisë korrelehet me temperaturën (ngrohje/freskim)

**Integrim:**
- Replace simulated weather data me real API calls
- Cache data për të reduktuar API calls
- Fallback në simulated data nëse API fails

---

### 2. Të Dhëna të Çmimeve të Energjisë ⚡

**Burime publike për Kosovën:**
- **KOSTT (Kosovo System Operator)**: Të dhëna publike të çmimeve
- **Energy Regulatory Office (ERO)**: Çmime dhe tarifa
- **KEK (Kosovo Energy Corporation)**: Çmime për konsumatorët
- Web scraping nga faqet zyrtare (nëse nuk ka API)

**Të dhënat e nevojshme:**
- Tarifa e energjisë elektrike (€/kWh)
- Çmime për konsumatorët rezidencialë/komercialë
- Peak/Off-peak pricing (nëse ka)
- Historical pricing trends

**AI Integration:**
- Web scraping me BeautifulSoup/Scrapy
- NLP për extraction të çmimeve nga PDF-ë dhe faqe web
- ML models për parashikim çmimesh të ardhshme

---

### 3. Të Dhëna Demografike dhe Popullata 👥

**Burime:**
- **ASK (Agjencia e Statistikave të Kosovës)**: Census data, statistikat e popullsisë
- **World Bank Open Data**: Economic indicators për Kosovën
- **UN Data**: Development indicators

**Të dhënat e nevojshme:**
- Popullata sipas rajonit (Prishtinë, Prizren, Pejë, etj.)
- Rritja e popullsisë
- Konsumi mesatar i energjisë për shtëpi
- Economic indicators që ndikojnë në konsum

---

### 4. Të Dhëna të Konsumit të Energjisë 📊

**Burime:**
- **KOSTT**: Real-time dhe historical consumption data
- **KEK**: Consumption statistics për rajonet
- **Transparency Platform Kosovo**: Open data initiatives
- Web scraping nga dashboard-e publike

**Të dhënat e nevojshme:**
- Total consumption për Kosovën (MW)
- Consumption sipas rajonit
- Peak hours dhe demand patterns
- Seasonal variations

---

### 5. Të Dhëna të Prodhimit të Energjisë (Renewable) 🌱

**Burime:**
- **KOSTT**: Renewable energy production data
- **Ministry of Economic Development**: Policies dhe statistics
- **Solar/Wind farm operators**: Production data (nëse publike)

**Të dhënat e nevojshme:**
- Solar energy production (MW)
- Wind energy production (MW)
- Hydroelectric production (MW)
- Grid capacity dhe availability

---

### 6. Të Dhëna të Trafikut dhe Urbanizimit 🚗

**Burime:**
- **Google Maps API**: Traffic data për rajonet e Kosovës
- **OpenStreetMap**: Geographic data
- **Municipality data**: Urban development plans

**Përdorimi:**
- Traffic patterns korrelojnë me consumption (industrial areas)
- Urban development ndikon në demand të energjisë
- Geographic data për optimal sensor placement

---

## 🤖 Teknologjitë e AI për Data Extraction

### 1. Web Scraping me AI

**Libraritë:**
- **BeautifulSoup4**: HTML parsing
- **Scrapy**: Web crawling framework
- **Selenium**: Dynamic content (JavaScript rendering)
- **Playwright**: Modern browser automation

**AI Features:**
- **Natural Language Processing (NLP)**: Extract text nga PDF-ë dhe images
- **OCR (Tesseract/Google Vision)**: Extract text nga screenshots/images
- **LLM Integration (GPT-4/Claude)**: Extract structured data nga unstructured text

### 2. Document Processing

**Libraritë:**
- **PyPDF2/pdfplumber**: PDF parsing
- **Pandas**: Data manipulation
- **LangChain**: Document processing me LLMs
- **unstructured**: AI-powered document parsing

**Përdorimi:**
- Extract data nga PDF reports (KOSTT, ERO)
- Convert tables në structured data
- Summarize dhe extract key metrics

### 3. API Integration me AI Enhancement

**Features:**
- **Rate limiting**: Respect API limits
- **Caching**: Redis për të reduktuar API calls
- **Data validation**: AI për të validuar të dhënat
- **Anomaly detection**: ML për të detektuar data të pasakta

---

## 🏗️ Arkitektura e Integrimit

### Komponentët e Reja:

```
┌─────────────────────────────────────────────────────────┐
│           Web Data Collector Service (AI-Powered)       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Weather      │  │ Energy Price │  │ Consumption  │ │
│  │ Scraper      │  │ Scraper      │  │ Scraper      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ PDF Parser   │  │ NLP Engine   │  │ OCR Service  │ │
│  │ (AI)         │  │ (LLM)        │  │ (Tesseract)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Data Validation & Enrichment (AI)         │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
                ┌───────────────┐
                │     Kafka     │
                │   (Topics)    │
                └───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Existing Processing Pipeline │
        │  (Spark, PostgreSQL, etc.)    │
        └───────────────────────────────┘
```

---

## 📝 Implementimi i Rekomanduar

### Faza 1: Weather Data Integration (Prioritet i Lartë)

**Service**: `kosovo-weather-collector`

**Features:**
- Integrim me OpenWeatherMap API për qytetet e Kosovës
- Scheduled collection (çdo orë)
- Data enrichment me AI (weather patterns prediction)
- Integration me existing weather-producer-service

**Kodi i Shembullit:**
```python
# docker/kosovo-weather-collector/app.py
import requests
import json
from kafka import KafkaProducer

KOSOVO_CITIES = {
    'prishtina': {'lat': 42.6629, 'lon': 21.1655},
    'prizren': {'lat': 42.2139, 'lon': 20.7397},
    'peje': {'lat': 42.6609, 'lon': 20.2891},
    'gjilan': {'lat': 42.4639, 'lon': 21.4694},
    'mitrovice': {'lat': 42.8833, 'lon': 20.8667}
}

def collect_kosovo_weather():
    """Collect real weather data për qytetet e Kosovës"""
    weather_data = []
    
    for city, coords in KOSOVO_CITIES.items():
        # API call to OpenWeatherMap
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': coords['lat'],
            'lon': coords['lon'],
            'appid': os.getenv('OPENWEATHER_API_KEY'),
            'units': 'metric'
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        weather_data.append({
            'city': city,
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': data['wind']['speed'],
            'condition': data['weather'][0]['main'],
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return weather_data
```

---

### Faza 2: Energy Price Scraper (AI-Powered)

**Service**: `kosovo-energy-price-collector`

**Features:**
- Web scraping nga faqet zyrtare (KOSTT, ERO)
- PDF parsing për tariff reports
- NLP për extraction të çmimeve
- ML për parashikim çmimesh

**Kodi i Shembullit:**
```python
# docker/kosovo-energy-price-collector/app.py
from bs4 import BeautifulSoup
import requests
from langchain import LLMChain
from langchain.llms import OpenAI

def scrape_energy_prices():
    """Scrape energy prices nga faqet zyrtare"""
    # Scrape from KOSTT website
    url = "https://kostt.com/PublicConsumer/Tariff"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract tariff information
    # Use AI/LLM për të extract structured data nga unstructured HTML
    # ...
    
def extract_from_pdf(pdf_path):
    """Extract tariff data nga PDF reports"""
    # Use pdfplumber ose PyPDF2
    # Use LLM për të extract structured data
    # ...
```

---

### Faza 3: Consumption Data Collector

**Service**: `kosovo-consumption-collector`

**Features:**
- Collect consumption data nga KOSTT dashboard (nëse publike)
- Historical data collection
- Real-time monitoring
- Data validation me AI

---

## 🔧 Teknologjitë e Rekomanduara

### Python Libraries:
```txt
# Web Scraping
beautifulsoup4==4.12.2
scrapy==2.11.0
selenium==4.15.0
playwright==1.40.0

# AI/ML
openai==1.3.0
langchain==0.0.350
transformers==4.35.0
tesseract-ocr==0.1.3

# Document Processing
PyPDF2==3.0.1
pdfplumber==0.10.3
pandas==2.1.3

# API Integration
requests==2.31.0
aiohttp==3.9.1

# Scheduling
celery==5.3.4
APScheduler==3.10.4
```

---

## 📅 Plan Implementimi

### Muaji 1: Weather Data Integration
- ✅ Integrim me OpenWeatherMap API
- ✅ Replace simulated weather me real data
- ✅ Testing dhe validation

### Muaji 2: Energy Price Collection
- ✅ Web scraping setup
- ✅ PDF parsing me AI
- ✅ Data validation
- ✅ Integration me analytics service

### Muaji 3: Consumption Data
- ✅ Consumption data collection
- ✅ Historical data import
- ✅ Real-time monitoring setup

### Muaji 4: AI Enhancement
- ✅ ML models për predictions
- ✅ Anomaly detection
- ✅ Data enrichment
- ✅ Optimization

---

## 💡 Ide Shtesë

### 1. Social Media Monitoring (AI)
- Monitor Twitter/X për power outages (Kosovo energy companies)
- Sentiment analysis për consumer satisfaction
- Extract information nga posts (outage reports, complaints)

### 2. News Article Analysis
- Scrape news articles rreth energjisë në Kosovë
- Use NLP për të extract key events (blackouts, price changes, policy updates)
- Correlate me consumption patterns

### 3. Satellite Data
- Use satellite imagery për të monitoruar solar installations
- Estimate renewable energy capacity
- Track urban development

### 4. IoT Device Integration
- Integrate me smart meters (nëse publike ose partners)
- Real-time consumption data
- Granular regional data

---

## 🚀 Quick Start: Weather Integration

### Step 1: Krijo Weather Collector Service

```bash
mkdir -p docker/kosovo-weather-collector
cd docker/kosovo-weather-collector
```

### Step 2: Install Dependencies

```txt
# requirements.txt
requests==2.31.0
kafka-python==2.0.2
python-dotenv==1.0.0
APScheduler==3.10.4
```

### Step 3: Integro në docker-compose.yml

```yaml
kosovo-weather-collector:
  build: ./kosovo-weather-collector
  container_name: smartgrid-kosovo-weather
  environment:
    - OPENWEATHER_API_KEY=${OPENWEATHER_API_KEY}
    - KAFKA_BROKER=smartgrid-kafka:9092
    - KOSOVO_CITIES=prishtina,prizren,peje,gjilan,mitrovice
  depends_on:
    - kafka
  restart: unless-stopped
```

---

## 📊 Benefits

1. **Real Data**: Zëvendësoj simulated data me të dhëna reale
2. **Accuracy**: Më të sakta analytics dhe predictions
3. **Regional Insights**: Të dhëna specifike për Kosovën
4. **AI-Powered**: Automatic extraction dhe validation
5. **Scalable**: Easily extensible për më shumë burime të dhënash

---

## ⚠️ Considerations

1. **API Limits**: Respect rate limits nga APIs
2. **Legal Compliance**: Ensure web scraping është legal
3. **Data Privacy**: Follow GDPR dhe privacy regulations
4. **Error Handling**: Robust error handling për API failures
5. **Caching**: Cache data për të reduktuar API calls
6. **Cost**: Monitor API costs (OpenWeatherMap, etc.)

---

## 🔗 Resources për Kosovën

- **KOSTT**: https://kostt.com
- **ERO**: https://ero-ks.org
- **KEK**: https://kek-energy.com
- **ASK**: https://ask.rks-gov.net
- **Ministry of Economic Development**: https://me.rks-gov.net

---

## 📝 Next Steps

1. Start me Weather Data integration (easiest, highest value)
2. Setup OpenWeatherMap API key
3. Create `kosovo-weather-collector` service
4. Test me real data
5. Expand për më shumë data sources
