#!/bin/bash
# Test script për Delta Lake dhe Trino në Docker Compose

set -e

echo "=========================================="
echo "Testing Delta Lake and Trino in Docker Compose"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Check if services are running
echo "1. Checking if services are running..."
echo ""

# Check Trino
if docker ps | grep -q "smartgrid-trino"; then
    echo -e "${GREEN}✅ Trino service is running${NC}"
    docker ps | grep "smartgrid-trino"
else
    echo -e "${YELLOW}⚠️ Trino service is not running${NC}"
    echo "   Start it with: docker-compose up -d trino"
fi

echo ""

# Check data-processing-service (Delta Lake)
if docker ps | grep -q "smartgrid-data-processing"; then
    echo -e "${GREEN}✅ Data Processing service is running${NC}"
    docker ps | grep "smartgrid-data-processing"
else
    echo -e "${YELLOW}⚠️ Data Processing service is not running${NC}"
    echo "   Start it with: docker-compose up -d data-processing-service"
fi

echo ""

# Check analytics-service (Trino client)
if docker ps | grep -q "smartgrid-analytics"; then
    echo -e "${GREEN}✅ Analytics service is running${NC}"
    docker ps | grep "smartgrid-analytics"
else
    echo -e "${YELLOW}⚠️ Analytics service is not running${NC}"
    echo "   Start it with: docker-compose up -d analytics-service"
fi

echo ""

# Test 2: Check Trino health
echo "2. Testing Trino health endpoint..."
if docker ps | grep -q "smartgrid-trino"; then
    if curl -s http://localhost:8080/v1/info > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Trino health check passed${NC}"
        curl -s http://localhost:8080/v1/info | head -5
    else
        echo -e "${YELLOW}⚠️ Trino health check failed (service may still be starting)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Trino service not running, skipping health check${NC}"
fi

echo ""

# Test 3: Check Trino catalogs
echo "3. Testing Trino catalogs..."
if docker ps | grep -q "smartgrid-trino"; then
    if curl -s http://localhost:8080/v1/statement -X POST -H "Content-Type: text/plain" -d "SHOW CATALOGS" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Trino catalogs query successful${NC}"
    else
        echo -e "${YELLOW}⚠️ Trino catalogs query failed (service may still be starting)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Trino service not running, skipping catalog test${NC}"
fi

echo ""

# Test 4: Check Delta Lake volume
echo "4. Checking Delta Lake volume..."
if docker volume ls | grep -q "delta_lake_data"; then
    echo -e "${GREEN}✅ Delta Lake volume exists${NC}"
    docker volume ls | grep "delta_lake_data"
else
    echo -e "${YELLOW}⚠️ Delta Lake volume not found${NC}"
    echo "   It will be created when you run: docker-compose up -d"
fi

echo ""

# Test 5: Check Trino volume
echo "5. Checking Trino volume..."
if docker volume ls | grep -q "trino_data"; then
    echo -e "${GREEN}✅ Trino volume exists${NC}"
    docker volume ls | grep "trino_data"
else
    echo -e "${YELLOW}⚠️ Trino volume not found${NC}"
    echo "   It will be created when you run: docker-compose up -d"
fi

echo ""

# Test 6: Check logs for errors
echo "6. Checking service logs for errors..."
echo ""

if docker ps | grep -q "smartgrid-trino"; then
    echo "Trino logs (last 10 lines):"
    docker logs smartgrid-trino --tail 10 2>&1 | grep -i "error\|exception\|failed" || echo "  No errors found"
fi

echo ""

if docker ps | grep -q "smartgrid-data-processing"; then
    echo "Data Processing logs (last 10 lines):"
    docker logs smartgrid-data-processing --tail 10 2>&1 | grep -i "error\|exception\|failed\|delta" || echo "  No errors found"
fi

echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "✅ Services checked"
echo "✅ Health checks performed"
echo "✅ Volumes verified"
echo ""
echo "Next steps:"
echo "1. Start services: docker-compose up -d"
echo "2. Wait for services to be ready (30-60 seconds)"
echo "3. Run Python tests:"
echo "   - python test_delta_lake.py"
echo "   - python test_trino.py"
echo ""

