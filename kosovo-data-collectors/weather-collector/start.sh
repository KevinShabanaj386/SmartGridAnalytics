#!/bin/bash

echo "🌤️  Starting Kosovo Weather Data Collector..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your OpenWeatherMap API key"
    echo "   Get your key from: https://openweathermap.org/api"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if API key is set
if [ -z "$OPENWEATHER_API_KEY" ] || [ "$OPENWEATHER_API_KEY" = "your_api_key_here" ]; then
    echo "❌ Error: OPENWEATHER_API_KEY not set in .env file"
    echo "   Get your key from: https://openweathermap.org/api"
    exit 1
fi

echo "✅ Configuration loaded"
echo "📊 Monitoring cities: ${CITIES:-prishtina,prizren,peje,gjilan,mitrovice}"
echo "⏰ Collection interval: ${COLLECTION_INTERVAL:-3600} seconds"
echo ""

# Start docker-compose
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "✅ Kosovo Weather Collector is running!"
echo ""
echo "📍 Endpoints:"
echo "   Health: http://localhost:5007/health"
echo "   Cities: http://localhost:5007/api/v1/cities"
echo "   Collect: http://localhost:5007/api/v1/collect (POST)"
echo ""
echo "📊 View logs: docker-compose logs -f kosovo-weather-collector"
echo "🛑 Stop: docker-compose down"
