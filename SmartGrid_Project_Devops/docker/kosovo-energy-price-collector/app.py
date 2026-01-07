"""
Kosovo Energy Price Collector Service
Simulates scraping electricity price data for Kosovo from multiple sources.
"""
from flask import Flask, jsonify
from datetime import datetime, timedelta
import random
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simulated sources of price data
PRICE_SOURCES = [
    "KESCO Official Tariff",
    "Market Spot Price",
    "Regional Exchange",
]


def generate_price_snapshot() -> dict:
    """Generate a simulated snapshot of electricity prices in €/kWh."""
    base_price = random.uniform(0.06, 0.12)  # average price range
    peak_multiplier = random.uniform(1.1, 1.4)
    offpeak_multiplier = random.uniform(0.6, 0.9)

    prices = {
        "base": {
            "price_eur_per_kwh": round(base_price, 4),
            "extracted_from": "Simulated base tariff for Kosovo households",
        },
        "peak": {
            "price_eur_per_kwh": round(base_price * peak_multiplier, 4),
            "extracted_from": "Simulated peak tariff (17:00-22:00)",
        },
        "offpeak": {
            "price_eur_per_kwh": round(base_price * offpeak_multiplier, 4),
            "extracted_from": "Simulated off-peak tariff (22:00-06:00)",
        },
    }

    return {
        "source": random.choice(PRICE_SOURCES),
        "scraped_at": datetime.utcnow().isoformat(),
        "prices": prices,
    }


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "service": "kosovo-energy-price-collector",
            "timestamp": datetime.utcnow().isoformat(),
        }
    ), 200


@app.route("/api/v1/prices/latest", methods=["GET"])
def get_latest_prices():
    """Return simulated latest electricity price data for Kosovo."""
    try:
        snapshots = [generate_price_snapshot() for _ in range(2)]
        return (
            jsonify({"status": "success", "sources_collected": len(snapshots), "data": snapshots}),
            200,
        )
    except Exception as e:
        logger.error(f"Error generating price data: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=False)
