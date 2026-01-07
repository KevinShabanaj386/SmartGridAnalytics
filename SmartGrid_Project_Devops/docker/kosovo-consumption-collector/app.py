"""
Kosovo Energy Consumption Collector Service
Simulates aggregated and historical electricity consumption for Kosovo.
"""
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import random
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simulated regions in Kosovo
REGIONS = {
    "central": {"name": "Prishtinë", "region": "Central", "estimated_population": 300_000},
    "south": {"name": "Prizren", "region": "South", "estimated_population": 180_000},
    "west": {"name": "Pejë", "region": "West", "estimated_population": 100_000},
    "east": {"name": "Gjilan", "region": "East", "estimated_population": 90_000},
    "north": {"name": "Mitrovicë", "region": "North", "estimated_population": 120_000},
}


def generate_latest_consumption() -> dict:
    """Generate a simulated latest consumption snapshot in MW."""
    regions_data = {}
    total = 0.0

    for key, info in REGIONS.items():
        base = random.uniform(50, 150)  # MW per region
        regions_data[key] = {
            "name": info["name"],
            "region": info["region"],
            "estimated_population": info["estimated_population"],
            "consumption_mw": round(base, 2),
        }
        total += base

    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_consumption_mw": round(total, 2),
        "regions": regions_data,
        "peak_period": datetime.utcnow().hour in range(17, 22),
    }
    return snapshot


def generate_historical_consumption(hours: int) -> list:
    """Generate a simple time series for total consumption over the last N hours."""
    now = datetime.utcnow()
    data = []

    for i in range(hours):
        ts = now - timedelta(hours=i)
        # Simulate diurnal pattern: higher during day/evening
        base = 400 + 100 * max(0, 1 - abs(ts.hour - 19) / 6)  # peak around 19:00
        noise = random.uniform(-40, 40)
        total = max(200, base + noise)
        data.append({
            "timestamp": ts.isoformat(),
            "total_consumption_mw": round(total, 2),
        })

    return data


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "service": "kosovo-consumption-collector",
            "regions": list(REGIONS.keys()),
            "timestamp": datetime.utcnow().isoformat(),
        }
    ), 200


@app.route("/api/v1/consumption/latest", methods=["GET"])
def get_latest_consumption():
    try:
        snapshot = generate_latest_consumption()
        return jsonify({"status": "success", "data": snapshot}), 200
    except Exception as e:
        logger.error(f"Error generating latest consumption: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/v1/consumption/historical", methods=["GET"])
def get_historical_consumption():
    try:
        hours = int(request.args.get("hours", 24))
        hours = max(1, min(hours, 168))
        series = generate_historical_consumption(hours)
        return jsonify({"status": "success", "data": series}), 200
    except Exception as e:
        logger.error(f"Error generating historical consumption: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=False)
