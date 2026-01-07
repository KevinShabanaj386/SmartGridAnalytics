# Kosovo Energy Price Collector

## 📊 Përmbledhje

Shërbim për scraping automatike të çmimeve të energjisë nga burime zyrtare në Kosovë (KOSTT, ERO, KEK), me AI-powered extraction dhe validation.

## 🎯 Features

- ✅ **Web scraping** nga KOSTT, ERO websites
- ✅ **AI-powered extraction** me regex patterns
- ✅ **Automatic collection** çdo 24 orë
- ✅ **Kafka integration** për streaming
- ✅ **REST API** endpoints
- 🚧 **PDF parsing** (në plan)
- 🚧 **LLM extraction** (në plan)

## 🚀 Quick Start

```bash
# Start service
docker-compose up -d

# Manual collection
curl -X POST http://localhost:5008/api/v1/collect

# Get latest prices
curl http://localhost:5008/api/v1/prices/latest

# List sources
curl http://localhost:5008/api/v1/sources
```

## 📋 API Endpoints

- `GET /health` - Health check
- `POST /api/v1/collect` - Manual collection (optional: `{"source": "kostt"}`)
- `GET /api/v1/sources` - List all monitored sources
- `GET /api/v1/prices/latest` - Get latest collected prices

## 🔧 Configuration

Environment variables:
- `KAFKA_BROKER` - Kafka broker address (default: localhost:9092)
- `KAFKA_TOPIC_PRICES` - Kafka topic për prices (default: kosovo-energy-prices)
- `COLLECTION_INTERVAL` - Collection interval në sekonda (default: 86400 = 24 orë)

## 📝 Next Steps

- PDF parsing për tariff reports
- LLM integration për extraction më të avancuar
- Historical price storage në PostgreSQL
- ML models për price prediction
