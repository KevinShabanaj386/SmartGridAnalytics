# AI Enhancement Layer

## 📊 Përmbledhje

Unified AI service për validation, enrichment, dhe anomaly detection të të dhënave nga të gjitha collectors.

## 🎯 Features

- ✅ **Data Quality Validation** - Scoring dhe issue detection
- ✅ **Anomaly Detection** - Statistical analysis (Z-score based)
- ✅ **AI Enrichment** - Automatic insights dhe recommendations
- ✅ **Multi-source Processing** - Weather, Prices, Consumption
- 🚧 **LLM Integration** - Optional LangChain/OpenAI support

## 🚀 Quick Start

```bash
# Start service
docker-compose up -d

# Validate data
curl -X POST http://localhost:5010/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{"temperature": 25, "humidity": 60, "data_type": "weather"}'

# Detect anomalies
curl -X POST http://localhost:5010/api/v1/anomalies/detect \
  -H "Content-Type: application/json" \
  -d '{"total_consumption_mw": 1500, "data_type": "consumption"}'

# Enhance data
curl -X POST http://localhost:5010/api/v1/enhance \
  -H "Content-Type: application/json" \
  -d '{"temperature": 35, "humidity": 70, "data_type": "weather"}'
```

## 📋 API Endpoints

- `GET /health` - Health check
- `POST /api/v1/validate` - Validate data quality
- `POST /api/v1/anomalies/detect` - Detect anomalies
- `POST /api/v1/enhance` - Full processing (validate + anomalies + enrichment)
- `GET /api/v1/stats` - Get processing statistics

## 🔧 Configuration

- `USE_LLM` - Enable LLM integration (default: false)
- `OPENAI_API_KEY` - OpenAI API key (if using LLM)
