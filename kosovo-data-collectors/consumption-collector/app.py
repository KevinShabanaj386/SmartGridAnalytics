"""
Kosovo Energy Consumption Data Collector Service
Collects consumption data nga KOSTT dashboard dhe other sources
AI-powered validation dhe enrichment
"""
from flask import Flask, jsonify, request
from kafka import KafkaProducer
import json
import logging
import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC_CONSUMPTION = os.getenv('KAFKA_TOPIC_CONSUMPTION', 'kosovo-energy-consumption')
COLLECTION_INTERVAL = int(os.getenv('COLLECTION_INTERVAL', 3600))  # 1 orë default

# Kosovo regions për consumption tracking
KOSOVO_REGIONS = {
    'prishtina': {
        'name': 'Prishtinë',
        'region': 'Central',
        'estimated_population': 200000
    },
    'prizren': {
        'name': 'Prizren',
        'region': 'South',
        'estimated_population': 180000
    },
    'peje': {
        'name': 'Pejë',
        'region': 'West',
        'estimated_population': 100000
    },
    'gjilan': {
        'name': 'Gjilan',
        'region': 'East',
        'estimated_population': 90000
    },
    'mitrovice': {
        'name': 'Mitrovicë',
        'region': 'North',
        'estimated_population': 85000
    }
}

# Kafka Producer
_producer = None

def get_producer():
    """Kthen Kafka producer"""
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3
            )
            logger.info(f"Kafka producer initialized: {KAFKA_BROKER}")
        except Exception as e:
            logger.warning(f"Could not create Kafka producer: {e}. Continuing without Kafka.")
            return None
    return _producer

def extract_consumption_from_text(text: str) -> Optional[float]:
    """
    Extract consumption value nga text me regex patterns
    AI-ready: mund të integrohet me LLM për extraction më të avancuar
    """
    # Patterns për consumption në MW, MWh, GWh
    patterns = [
        r'(\d+\.?\d*)\s*MW',
        r'(\d+\.?\d*)\s*MWh',
        r'(\d+\.?\d*)\s*GWh',
        r'konsum[im]*[:\s]+(\d+\.?\d*)',
        r'consumption[:\s]+(\d+\.?\d*)',
        r'demand[:\s]+(\d+\.?\d*)',
        r'ngarkes[ëe][:\s]+(\d+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1))
                # Validate: consumption për Kosovën normalisht është 100-1000 MW
                if 100 <= value <= 10000:  # Flexible range
                    return round(value, 2)
            except (ValueError, IndexError):
                continue
    
    return None

def scrape_kostt_consumption() -> Dict[str, Any]:
    """
    Scrape consumption data nga KOSTT dashboard
    Note: Në prodhim, kjo do të integrohet me KOSTT API ose dashboard publik
    """
    try:
        # KOSTT mund të ketë dashboard publik ose API
        url = 'https://kostt.com'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = soup.get_text()
        
        consumption_data = {
            'source': 'KOSTT',
            'url': url,
            'scraped_at': datetime.utcnow().isoformat(),
            'total_consumption_mw': None,
            'regions': {},
            'raw_text': text_content[:500]
        }
        
        # Try to extract total consumption
        total_consumption = extract_consumption_from_text(text_content)
        if total_consumption:
            consumption_data['total_consumption_mw'] = total_consumption
        
        # Try to extract regional data
        # KOSTT zakonisht ka tabela me data për rajone
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    text = ' '.join([cell.get_text() for cell in cells])
                    # Check if this row mentions a region
                    for region_key, region_info in KOSOVO_REGIONS.items():
                        if region_info['name'].lower() in text.lower() or region_key in text.lower():
                            consumption = extract_consumption_from_text(text)
                            if consumption:
                                consumption_data['regions'][region_key] = {
                                    'name': region_info['name'],
                                    'consumption_mw': consumption,
                                    'region': region_info['region']
                                }
        
        logger.info(f"Scraped KOSTT consumption: {consumption_data.get('total_consumption_mw', 'N/A')} MW")
        return consumption_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping KOSTT consumption: {e}")
        return generate_simulated_consumption()
    except Exception as e:
        logger.error(f"Unexpected error scraping KOSTT consumption: {e}")
        return generate_simulated_consumption()

def generate_simulated_consumption() -> Dict[str, Any]:
    """
    Generate simulated consumption data si fallback
    Based on estimated patterns për Kosovën
    """
    import random
    from datetime import datetime
    
    # Base consumption për Kosovën: ~800-1200 MW në pikë
    hour = datetime.utcnow().hour
    base_consumption = 800
    
    # Peak hours: 8-10 AM dhe 6-8 PM
    if hour in [8, 9, 10, 18, 19, 20]:
        peak_multiplier = random.uniform(1.3, 1.5)
    # Low hours: 2-6 AM
    elif hour in [2, 3, 4, 5]:
        peak_multiplier = random.uniform(0.7, 0.9)
    else:
        peak_multiplier = random.uniform(1.0, 1.2)
    
    total_consumption = round(base_consumption * peak_multiplier, 2)
    
    # Regional distribution (approximate)
    regional_distribution = {
        'prishtina': 0.30,  # 30% - largest city
        'prizren': 0.22,    # 22%
        'peje': 0.18,       # 18%
        'gjilan': 0.16,     # 16%
        'mitrovice': 0.14   # 14%
    }
    
    regions = {}
    for region_key, region_info in KOSOVO_REGIONS.items():
        share = regional_distribution.get(region_key, 0.14)
        consumption = round(total_consumption * share, 2)
        regions[region_key] = {
            'name': region_info['name'],
            'consumption_mw': consumption,
            'region': region_info['region'],
            'estimated_population': region_info['estimated_population']
        }
    
    return {
        'source': 'simulated',
        'url': None,
        'scraped_at': datetime.utcnow().isoformat(),
        'total_consumption_mw': total_consumption,
        'regions': regions,
        'hour_of_day': hour,
        'peak_period': hour in [8, 9, 10, 18, 19, 20],
        'note': 'Simulated data - Replace me real API when available'
    }

def collect_all_consumption_data() -> Dict[str, Any]:
    """
    Collect consumption data nga të gjitha burimet
    """
    try:
        # Try to scrape from KOSTT
        consumption_data = scrape_kostt_consumption()
        
        # Send to Kafka
        producer = get_producer()
        if producer:
            try:
                producer.send(
                    KAFKA_TOPIC_CONSUMPTION,
                    key='kostt'.encode('utf-8'),
                    value=consumption_data
                )
                logger.info("Consumption data sent to Kafka")
            except Exception as e:
                logger.error(f"Error sending consumption data to Kafka: {e}")
        
        return consumption_data
        
    except Exception as e:
        logger.error(f"Error in consumption collection: {e}")
        return generate_simulated_consumption()

def scheduled_collection():
    """Scheduled collection task"""
    logger.info("Starting scheduled consumption data collection...")
    try:
        data = collect_all_consumption_data()
        total_mw = data.get('total_consumption_mw', 'N/A')
        logger.info(f"Successfully collected consumption data: {total_mw} MW")
    except Exception as e:
        logger.error(f"Error in scheduled collection: {e}")

# Flask endpoints
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'kosovo-consumption-collector',
        'regions': list(KOSOVO_REGIONS.keys()),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/v1/collect', methods=['POST'])
def manual_collect():
    """Manual collection trigger"""
    try:
        data = collect_all_consumption_data()
        return jsonify({
            'status': 'success',
            'data': data
        }), 200
    except Exception as e:
        logger.error(f"Error in manual collection: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/v1/regions', methods=['GET'])
def list_regions():
    """List all Kosovo regions being monitored"""
    return jsonify({
        'regions': {
            key: {
                'name': info['name'],
                'region': info['region'],
                'estimated_population': info['estimated_population']
            }
            for key, info in KOSOVO_REGIONS.items()
        }
    }), 200

@app.route('/api/v1/consumption/latest', methods=['GET'])
def get_latest_consumption():
    """Get latest collected consumption data"""
    try:
        data = collect_all_consumption_data()
        return jsonify({
            'status': 'success',
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/v1/consumption/historical', methods=['GET'])
def get_historical_consumption():
    """
    Get historical consumption data
    Note: Në prodhim, kjo do të query nga database
    """
    try:
        # For now, return simulated historical data
        # In production, this would query PostgreSQL
        hours = int(request.args.get('hours', 24))
        
        historical_data = []
        for i in range(hours):
            timestamp = datetime.utcnow() - timedelta(hours=i)
            # Generate simulated data for each hour
            consumption = generate_simulated_consumption()
            consumption['timestamp'] = timestamp.isoformat()
            historical_data.append(consumption)
        
        return jsonify({
            'status': 'success',
            'hours': hours,
            'data': historical_data,
            'note': 'Simulated data - Replace me database query in production'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=scheduled_collection,
        trigger="interval",
        seconds=COLLECTION_INTERVAL,
        id='consumption_collection_job',
        name='Collect energy consumption from Kosovo sources',
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Scheduler started. Collection interval: {COLLECTION_INTERVAL} seconds")
    
    # Initial collection
    logger.info("Performing initial consumption data collection...")
    scheduled_collection()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5009, debug=False)
