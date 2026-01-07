# Kosovo Energy Consumption Collector

## 📊 Përmbledhje

Shërbim për collection automatike të të dhënave të konsumit të energjisë nga burime zyrtare në Kosovë (KOSTT), me AI-powered validation dhe enrichment.

## 🎯 Features

- ✅ **Web scraping** nga KOSTT dashboard
- ✅ **Regional consumption** tracking për 5 rajone
- ✅ **Automatic collection** çdo orë
- ✅ **Kafka integration** për streaming
- ✅ **REST API** endpoints
- ✅ **Simulated data** si fallback
- 🚧 **Historical data** storage (në plan)
- 🚧 **PostgreSQL** integration (në plan)

## 🚀 Quick Start

```bash
# Start service
docker-compose up -d

# Manual collection
curl -X POST http://localhost:5009/api/v1/collect

# Get latest consumption
curl http://localhost:5009/api/v1/consumption/latest

# Get historical (24 hours)
curl http://localhost:5009/api/v1/consumption/historical?hours=24

# List regions
curl http://localhost:5009/api/v1/regions
```

## 📋 API Endpoints

- `GET /health` - Health check
- `POST /api/v1/collect` - Manual collection trigger
- `GET /api/v1/regions` - List all monitored regions
- `GET /api/v1/consumption/latest` - Get latest consumption data
- `GET /api/v1/consumption/historical?hours=24` - Get historical data

## 📊 Regional Data

Monitoring për 5 rajone:
- Prishtinë (Central) - ~30% e konsumit total
- Prizren (South) - ~22%
- Pejë (West) - ~18%
- Gjilan (East) - ~16%
- Mitrovicë (North) - ~14%

## 🔧 Configuration

Environment variables:
- `KAFKA_BROKER` - Kafka broker address (default: localhost:9092)
- `KAFKA_TOPIC_CONSUMPTION` - Kafka topic (default: kosovo-energy-consumption)
- `COLLECTION_INTERVAL` - Collection interval në sekonda (default: 3600 = 1 orë)

## 📝 Next Steps

- Integration me KOSTT API (nëse publike)
- PostgreSQL storage për historical data
- ML models për consumption prediction
- Real-time alerts për peak consumption
