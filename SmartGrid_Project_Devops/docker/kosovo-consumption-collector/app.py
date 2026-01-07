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


def generate_yearly_consumption(from_year: int, to_year: int) -> list:
    """Generate simulated yearly consumption and import share since 2010."""
    if from_year > to_year:
        from_year, to_year = to_year, from_year

    years = list(range(from_year, to_year + 1))
    data = []

    base_consumption = random.uniform(4500, 5500)  # GWh
    base_import_share = random.uniform(20, 35)

    for idx, year in enumerate(years):
        # Gentle long-term growth with some noise
        trend = 1 + 0.01 * idx + random.uniform(-0.01, 0.02)
        yearly_total_gwh = round(base_consumption * trend, 1)
        import_share = round(min(75.0, base_import_share + idx * random.uniform(0.3, 1.0)), 1)

        data.append(
            {
                "year": year,
                "total_consumption_gwh": yearly_total_gwh,
                "import_share_percent": import_share,
                "timestamp": datetime(year, 1, 1).isoformat(),
            }
        )

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


@app.route("/api/v1/consumption/historical-yearly", methods=["GET"])
def get_historical_consumption_yearly():
    """Return simulated yearly consumption and import share from 2010 onwards."""
    try:
        now_year = datetime.utcnow().year
        from_year = int(request.args.get("from_year", 2010))
        to_year = int(request.args.get("to_year", now_year))
        from_year = max(2010, from_year)
        to_year = min(now_year, to_year)

        series = generate_yearly_consumption(from_year, to_year)
        return jsonify({"status": "success", "data": series}), 200
    except Exception as e:
        logger.error(f"Error generating yearly consumption: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=False)
