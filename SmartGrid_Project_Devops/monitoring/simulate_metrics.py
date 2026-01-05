from prometheus_client import Gauge, start_http_server
import random
import time

# Start Prometheus metrics server
start_http_server(8000)  # Porti ku Prometheus do lexojë metrics

# Create metrics (default registry)
g = Gauge('energy_consumption', 'Simulated energy consumption in kW', ['location'])

while True:
    g.labels(location='building1').set(random.randint(50, 150))
    g.labels(location='building2').set(random.randint(30, 120))
    time.sleep(5)
