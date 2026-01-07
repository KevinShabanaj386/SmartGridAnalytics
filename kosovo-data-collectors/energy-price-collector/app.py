"""
Kosovo Energy Price Collector Service
Scrapes energy prices nga KOSTT dhe ERO websites, me AI-powered extraction
"""
from flask import Flask, jsonify, request
from kafka import KafkaProducer
import json
import logging
import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC_PRICES = os.getenv('KAFKA_TOPIC_PRICES', 'kosovo-energy-prices')
COLLECTION_INTERVAL = int(os.getenv('COLLECTION_INTERVAL', 86400))  # 24 orë default

# Kosovo energy sources
ENERGY_SOURCES = {
    'kostt': {
        'name': 'KOSTT',
        'url': 'https://kostt.com',
        'tariff_url': 'https://kostt.com/PublicConsumer/Tariff',
        'type': 'system_operator'
    },
    'ero': {
        'name': 'ERO',
        'url': 'https://ero-ks.org',
        'tariff_url': 'https://ero-ks.org',
        'type': 'regulator'
    },
    'kek': {
        'name': 'KEK',
        'url': 'https://kek-energy.com',
        'tariff_url': 'https://kek-energy.com',
        'type': 'utility'
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

def extract_price_from_text(text: str) -> Optional[float]:
    """
    Extract price nga text me regex patterns
    AI-ready: mund të integrohet me LLM për extraction më të avancuar
    """
    # Patterns për çmime në €/kWh
    patterns = [
        r'(\d+\.?\d*)\s*€\s*/\s*kWh',
        r'(\d+\.?\d*)\s*EUR\s*/\s*kWh',
        r'(\d+\.?\d*)\s*euro\s*/\s*kWh',
        r'(\d+\.?\d*)\s*€\s*/\s*KWh',
        # Patterns pa currency explicit
        r'(\d+\.?\d{3,4})\s*/\s*kWh',  # p.sh. 0.0850 / kWh
        r'çmim[:\s]+(\d+\.?\d*)',
        r'tarif[ëe][:\s]+(\d+\.?\d*)',
        r'price[:\s]+(\d+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                price = float(match.group(1))
                # Validate: çmimi i energjisë normalisht është 0.01-1.00 €/kWh për Kosovën
                if 0.01 <= price <= 1.00:
                    return round(price, 4)
            except (ValueError, IndexError):
                continue
    
    return None

def scrape_kostt_tariffs() -> Dict[str, Any]:
    """
    Scrape tariff information nga KOSTT website
    """
    try:
        url = ENERGY_SOURCES['kostt']['tariff_url']
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract text content
        text_content = soup.get_text()
        
        # Search for tariff information
        # KOSTT zakonisht ka tabela ose tekst me çmime
        tariff_data = {
            'source': 'KOSTT',
            'url': url,
            'scraped_at': datetime.utcnow().isoformat(),
            'prices': {},
            'raw_text': text_content[:500]  # First 500 chars për reference
        }
        
        # Try to find prices in tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    text = ' '.join([cell.get_text() for cell in cells])
                    price = extract_price_from_text(text)
                    if price:
                        # Try to identify tariff type
                        tariff_type = 'unknown'
                        if 'rezidencial' in text.lower() or 'household' in text.lower():
                            tariff_type = 'residential'
                        elif 'komercial' in text.lower() or 'commercial' in text.lower():
                            tariff_type = 'commercial'
                        elif 'industri' in text.lower() or 'industrial' in text.lower():
                            tariff_type = 'industrial'
                        
                        tariff_data['prices'][tariff_type] = {
                            'price_eur_per_kwh': price,
                            'unit': 'EUR/kWh',
                            'extracted_from': text[:100]
                        }
        
        # If no prices in tables, search in all text
        if not tariff_data['prices']:
            price = extract_price_from_text(text_content)
            if price:
                tariff_data['prices']['default'] = {
                    'price_eur_per_kwh': price,
                    'unit': 'EUR/kWh'
                }
        
        logger.info(f"Scraped KOSTT tariffs: {len(tariff_data['prices'])} prices found")
        return tariff_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping KOSTT: {e}")
        return {
            'source': 'KOSTT',
            'error': str(e),
            'scraped_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Unexpected error scraping KOSTT: {e}")
        return {
            'source': 'KOSTT',
            'error': str(e),
            'scraped_at': datetime.utcnow().isoformat()
        }

def scrape_ero_tariffs() -> Dict[str, Any]:
    """
    Scrape tariff information nga ERO website
    """
    try:
        url = ENERGY_SOURCES['ero']['tariff_url']
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = soup.get_text()
        
        tariff_data = {
            'source': 'ERO',
            'url': url,
            'scraped_at': datetime.utcnow().isoformat(),
            'prices': {},
            'raw_text': text_content[:500]
        }
        
        # Extract prices
        price = extract_price_from_text(text_content)
        if price:
            tariff_data['prices']['regulatory'] = {
                'price_eur_per_kwh': price,
                'unit': 'EUR/kWh'
            }
        
        logger.info(f"Scraped ERO tariffs: {len(tariff_data['prices'])} prices found")
        return tariff_data
        
    except Exception as e:
        logger.error(f"Error scraping ERO: {e}")
        return {
            'source': 'ERO',
            'error': str(e),
            'scraped_at': datetime.utcnow().isoformat()
        }

def scrape_all_energy_prices() -> List[Dict[str, Any]]:
    """
    Scrape energy prices nga të gjitha burimet
    """
    all_prices = []
    
    # Scrape KOSTT
    try:
        kostt_data = scrape_kostt_tariffs()
        all_prices.append(kostt_data)
        
        # Send to Kafka
        producer = get_producer()
        if producer and 'error' not in kostt_data:
            try:
                producer.send(
                    KAFKA_TOPIC_PRICES,
                    key='kostt'.encode('utf-8'),
                    value=kostt_data
                )
                logger.info("KOSTT prices sent to Kafka")
            except Exception as e:
                logger.error(f"Error sending KOSTT prices to Kafka: {e}")
    except Exception as e:
        logger.error(f"Error in KOSTT scraping: {e}")
    
    time.sleep(2)  # Delay për të mos overload servers
    
    # Scrape ERO
    try:
        ero_data = scrape_ero_tariffs()
        all_prices.append(ero_data)
        
        # Send to Kafka
        producer = get_producer()
        if producer and 'error' not in ero_data:
            try:
                producer.send(
                    KAFKA_TOPIC_PRICES,
                    key='ero'.encode('utf-8'),
                    value=ero_data
                )
                logger.info("ERO prices sent to Kafka")
            except Exception as e:
                logger.error(f"Error sending ERO prices to Kafka: {e}")
    except Exception as e:
        logger.error(f"Error in ERO scraping: {e}")
    
    return all_prices

def scheduled_collection():
    """Scheduled collection task"""
    logger.info("Starting scheduled energy price collection...")
    try:
        data = scrape_all_energy_prices()
        logger.info(f"Successfully collected prices from {len(data)} sources")
    except Exception as e:
        logger.error(f"Error in scheduled collection: {e}")

# Flask endpoints
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'kosovo-energy-price-collector',
        'sources': list(ENERGY_SOURCES.keys()),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/v1/collect', methods=['POST'])
def manual_collect():
    """Manual collection trigger"""
    try:
        source = request.json.get('source') if request.json else None
        
        if source and source in ENERGY_SOURCES:
            # Collect from specific source
            if source == 'kostt':
                data = scrape_kostt_tariffs()
            elif source == 'ero':
                data = scrape_ero_tariffs()
            else:
                return jsonify({'error': 'Unknown source'}), 400
        else:
            # Collect from all sources
            data = scrape_all_energy_prices()
        
        return jsonify({
            'status': 'success',
            'sources_collected': len(data) if isinstance(data, list) else 1,
            'data': data
        }), 200
    except Exception as e:
        logger.error(f"Error in manual collection: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/v1/sources', methods=['GET'])
def list_sources():
    """List all energy sources being monitored"""
    return jsonify({
        'sources': {
            key: {
                'name': info['name'],
                'url': info['url'],
                'type': info['type']
            }
            for key, info in ENERGY_SOURCES.items()
        }
    }), 200

@app.route('/api/v1/prices/latest', methods=['GET'])
def get_latest_prices():
    """Get latest collected prices"""
    try:
        # This would normally query from database
        # For now, perform a quick scrape
        data = scrape_all_energy_prices()
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

if __name__ == '__main__':
    # Initialize scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=scheduled_collection,
        trigger="interval",
        seconds=COLLECTION_INTERVAL,
        id='price_collection_job',
        name='Collect energy prices from Kosovo sources',
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Scheduler started. Collection interval: {COLLECTION_INTERVAL} seconds")
    
    # Initial collection
    logger.info("Performing initial energy price collection...")
    scheduled_collection()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5008, debug=False)
