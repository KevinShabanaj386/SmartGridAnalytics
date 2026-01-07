"""
Kosovo Energy Price Collector Service
Simulates scraping electricity price data for Kosovo from multiple sources.
"""
from flask import Flask, jsonify, request
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
    """Generate a simulated snapshot of electricity prices in €/kWh.

    Includes import-related metrics and simple trend signals so the
    dashboard can show how import prices are changing.
    """
    base_price = random.uniform(0.06, 0.12)  # average price range (€/kWh)
    peak_multiplier = random.uniform(1.1, 1.4)
    offpeak_multiplier = random.uniform(0.6, 0.9)

    # Simulate import vs. domestic prices (€/MWh) and trends
    import_price_eur_per_mwh = round(base_price * 1000 * random.uniform(1.05, 1.3), 2)
    domestic_price_eur_per_mwh = round(base_price * 1000 * random.uniform(0.9, 1.1), 2)
    change_24h_percent = round(random.uniform(-5, 15), 2)   # -5% to +15%
    change_7d_percent = round(random.uniform(-10, 30), 2)  # -10% to +30%
    import_share_percent = round(random.uniform(30, 70), 1)

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
        "import_price_eur_per_mwh": import_price_eur_per_mwh,
        "domestic_price_eur_per_mwh": domestic_price_eur_per_mwh,
        "import_share_percent": import_share_percent,
        "change_24h_percent": change_24h_percent,
        "change_7d_percent": change_7d_percent,
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


def generate_price_history(from_year: int, to_year: int) -> list:
    """Generate simulated yearly average prices and import share from 2010 onwards."""
    if from_year > to_year:
        from_year, to_year = to_year, from_year

    years = list(range(from_year, to_year + 1))
    history = []

    # Anchor values so the series looks smooth and realistic
    base_import_price = random.uniform(40, 60)  # €/MWh
    base_domestic_price = base_import_price * random.uniform(0.8, 0.95)
    base_import_share = random.uniform(25, 40)

    for idx, year in enumerate(years):
        # Gentle upward trend with a bit of noise
        growth_factor = 1 + 0.02 * idx + random.uniform(-0.01, 0.03)
        import_price = round(base_import_price * growth_factor, 2)
        domestic_price = round(base_domestic_price * (1 + 0.015 * idx), 2)
        import_share = round(min(80.0, base_import_share + idx * random.uniform(0.5, 1.5)), 1)

        avg_price_eur_per_kwh = round(
            (import_price / 1000.0) * (import_share / 100.0)
            + (domestic_price / 1000.0) * (1 - import_share / 100.0),
            4,
        )

        history.append(
            {
                "year": year,
                "import_price_eur_per_mwh": import_price,
                "domestic_price_eur_per_mwh": domestic_price,
                "import_share_percent": import_share,
                "average_price_eur_per_kwh": avg_price_eur_per_kwh,
                "timestamp": datetime(year, 1, 1).isoformat(),
            }
        )

    return history


@app.route("/api/v1/prices/historical", methods=["GET"])
def get_price_history():
    """Return simulated long-term price and import trends (2010–today)."""
    try:
        now_year = datetime.utcnow().year
        from_year = int(request.args.get("from_year", 2010))
        to_year = int(request.args.get("to_year", now_year))
        from_year = max(2010, from_year)
        to_year = min(now_year, to_year)

        history = generate_price_history(from_year, to_year)
        return jsonify({"status": "success", "data": history}), 200
    except Exception as e:
        logger.error(f"Error generating price history: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=False)
