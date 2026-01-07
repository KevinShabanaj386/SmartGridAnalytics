#!/bin/bash
# Script për të kontrolluar statusin e Kosovo Collectors

echo "🔍 Checking Kosovo Data Collectors Status..."
echo ""

# Check Weather Collector (5007)
echo "🌤️  Weather Collector (Port 5007):"
if lsof -i :5007 > /dev/null 2>&1; then
    echo "   ✅ Port 5007 is in use"
    if curl -s http://localhost:5007/health > /dev/null 2>&1; then
        echo "   ✅ Health endpoint responding"
        curl -s http://localhost:5007/health | head -3
    elif curl -s http://localhost:5007/api/v1/collect > /dev/null 2>&1; then
        echo "   ✅ API endpoint responding"
    else
        echo "   ⚠️  Port in use but service not responding"
    fi
else
    echo "   ❌ Port 5007 is NOT in use"
    echo "   💡 Start with: cd weather-collector && docker-compose up -d"
fi

echo ""

# Check Price Collector (5008)
echo "⚡ Energy Price Collector (Port 5008):"
if lsof -i :5008 > /dev/null 2>&1; then
    echo "   ✅ Port 5008 is in use"
    if curl -s http://localhost:5008/health > /dev/null 2>&1; then
        echo "   ✅ Health endpoint responding"
        curl -s http://localhost:5008/health | head -3
    elif curl -s http://localhost:5008/api/v1/prices/latest > /dev/null 2>&1; then
        echo "   ✅ API endpoint responding"
    else
        echo "   ⚠️  Port in use but service not responding"
    fi
else
    echo "   ❌ Port 5008 is NOT in use"
    echo "   💡 Start with: cd energy-price-collector && docker-compose up -d"
fi

echo ""

# Check Docker containers
echo "🐳 Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(kosovo|weather|price|5007|5008)" || echo "   No Kosovo containers running"

echo ""
echo "📋 Quick Start Commands:"
echo "   Weather:  cd kosovo-data-collectors/weather-collector && docker-compose up -d"
echo "   Price:    cd kosovo-data-collectors/energy-price-collector && docker-compose up -d"
