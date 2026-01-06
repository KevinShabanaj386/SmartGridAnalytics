# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project overview

This repo contains the Smart Grid Analytics platform, implemented as a Python-based microservices system with an event-driven architecture. Most application code and all DevOps assets live under `SmartGrid_Project_Devops/`, which includes Docker, Kubernetes, monitoring, ELK, MLflow, Terraform, and supporting runbooks.

High level pieces:
- `SmartGrid_Project_Devops/docker/`: all runtime services and infrastructure for local Docker Compose-based development.
- `SmartGrid_Project_Devops/kubernetes/`: manifests for production-style Kubernetes deployment.
- `SmartGrid_Project_Devops/monitoring/`, `grafana/`, `elk/`: Prometheus, Grafana, and ELK stack configuration.
- `SmartGrid_Project_Devops/mlflow/`: model definitions and training pipeline integrated with MLflow.
- `SmartGrid_Project_Devops/airflow/` and `data-quality/`: ETL DAG and Great Expectations-style data quality checks.
- `SmartGrid_Project_Devops/terraform/`: infra-as-code skeleton for cloud resources.

Core microservices (Python + Flask, all containerized):
- **API Gateway (`docker/api_gateway`)**: single entrypoint, routing to downstream services, JWT auth, circuit breaker/retry logic.
- **Data Ingestion (`docker/data-ingestion-service`)**: receives sensor/meter data over HTTP and publishes to Kafka topics.
- **Data Processing (`docker/data-processing-service`)**: consumes from Kafka, performs aggregations, writes to PostgreSQL.
- **Analytics (`docker/analytics-service`)**: reads from PostgreSQL/Redis and MLflow to expose analytics and ML endpoints.
- **Notification (`docker/notification-service`)**: produces alerts/notifications (email/SMS/webhook) via Kafka.
- **User Management (`docker/user-management-service`)**: user accounts, roles, JWT issuance/verification.
- **Frontend (`docker/frontend`)**: Flask-based web dashboard that talks to the API Gateway.
- **Weather Producer (`docker/weather-producer-service`)** and **Spark Streaming (`docker/spark-streaming-service`)**: auxiliary services for streaming/weather-enriched analytics.

Infrastructure services are brought up alongside the microservices via Docker Compose: PostgreSQL (+ exporter), Kafka/ZooKeeper (+ exporter), Redis, Prometheus, Grafana, ELK stack, Jaeger, MLflow+MinIO, Vault, Consul, and SonarQube.

Key high-level docs worth consulting:
- `README.md`: top-level summary and quick-start for Docker and Kubernetes.
- `SmartGrid_Project_Devops/ARCHITECTURE.md`: detailed microservice and infrastructure architecture, event flows, resiliency patterns, and security model.
- `SmartGrid_Project_Devops/QUICK_START.md` and `START_PROJECT.md`: end-to-end quick start plus main URLs and example API usage.
- `SmartGrid_Project_Devops/PORTS.md`: authoritative map of all exposed ports and default credentials.
- `SmartGrid_Project_Devops/RUNBOOKS.md`: incident response runbooks and playbooks based on Docker.

## Common local workflows

### Prerequisites

- Docker and Docker Compose installed locally.
- Python 3.11 available if you want to run CI checks locally (Docker is enough to just run the system).
- Ensure the ports listed in `SmartGrid_Project_Devops/PORTS.md` are free (notably 8080, 5000–5006, 3000, 5433, 9090, 9092, 5601, 5005, 16686, 9000–9001).

### Run the full stack with Docker Compose

From the repo root:

```bash
cd SmartGrid_Project_Devops/docker
# Build and start everything in the background
docker-compose up -d
```

Useful follow-up commands (same directory):
- Check status of all containers: `docker-compose ps`
- Tail logs for all services: `docker-compose logs -f`
- Tail logs for a single service, e.g. API Gateway: `docker-compose logs api-gateway`
- Stop everything: `docker-compose down`
- Stop and remove all containers + volumes (hard reset): `docker-compose down -v`

Key entrypoints once the stack is up (see `PORTS.md` for full list):
- Frontend dashboard: `http://localhost:8080` (default `admin` / `admin123`).
- API Gateway health & test: `http://localhost:5000/health` and `http://localhost:5000/api/test`.
- Monitoring: Grafana (`http://localhost:3000`, `admin`/`admin`), Prometheus (`http://localhost:9090`).
- Logs and tracing: Kibana (`http://localhost:5601`), Jaeger (`http://localhost:16686`).
- ML tooling: MLflow (`http://localhost:5005`), MinIO Console (`http://localhost:9001`).

### Running or rebuilding a single service

All microservices under `SmartGrid_Project_Devops/docker/` are individual Docker build contexts used by `docker-compose.yml`.

From `SmartGrid_Project_Devops/docker`:
- Rebuild and restart a single service after code changes, e.g. analytics:
  - `docker-compose build analytics-service`
  - `docker-compose up -d analytics-service`
- Restart a service without rebuilding, e.g. frontend: `docker-compose restart frontend`

Service names match the keys in `docker-compose.yml`, e.g. `api-gateway`, `data-ingestion-service`, `data-processing-service`, `analytics-service`, `notification-service`, `user-management-service`, `frontend`, `weather-producer`, `spark-streaming`.

### Local CI-style checks (linting and smoke tests)

The CI pipeline (`.github/workflows/ci-cd.yml`) runs lightweight checks to ensure each service imports correctly and that basic style checks pass.

To approximate the same locally:

1. From the repo root, install generic tools:
   ```bash
   python -m pip install --upgrade pip
   pip install flake8 pytest pytest-cov
   ```

2. Lint the primary service entrypoints (same as CI):
   ```bash
   flake8 SmartGrid_Project_Devops/docker/*/app.py --max-line-length=120 --ignore=E501,W503
   ```

3. For a given service (for example, API Gateway), run the import smoke test:
   ```bash
   cd SmartGrid_Project_Devops/docker/api_gateway
   pip install -r requirements.txt
   python -c "import app; print('API Gateway imports OK')"
   ```

   You can repeat this pattern for the other services in their respective directories (`data-ingestion-service`, `data-processing-service`, `analytics-service`, `notification-service`, `user-management-service`, `frontend`, `weather-producer-service`).

There is currently no dedicated `pytest` test suite; CI focuses on importability and basic static analysis.

## Docker and deployment notes

- The canonical development entrypoint is `SmartGrid_Project_Devops/docker/docker-compose.yml`. It brings up infrastructure (PostgreSQL, Kafka/ZooKeeper, Redis, Prometheus, Grafana, ELK, MLflow+MinIO, Vault, Consul, SonarQube, Jaeger) and all Python microservices.
- Each Python service uses a `Dockerfile`/`dockerfile` in its directory; images are built automatically by `docker-compose` using relative contexts.
- The API Gateway Dockerfile has been aligned with the rest of the stack to use `python:3.11-slim` and exposes port 5000.
- For production, Kubernetes manifests under `SmartGrid_Project_Devops/kubernetes/` mirror the same services and wiring as Docker Compose. The CI workflow includes a `deploy` job that applies these manifests to a `smartgrid` namespace, assuming a configured `KUBECONFIG` secret.
- Terraform files in `SmartGrid_Project_Devops/terraform/` are intended to provision cloud infrastructure (e.g., Kubernetes cluster, databases, networking) but may need environment-specific variables and backend configuration before use.

## Observability, runbooks, and troubleshooting

- Prometheus configuration lives in `SmartGrid_Project_Devops/monitoring/prometheus.yml`; Grafana dashboards are under `SmartGrid_Project_Devops/grafana/dashboards/` with provisioning in `SmartGrid_Project_Devops/grafana/provisioning/`.
- ELK stack configuration is under `SmartGrid_Project_Devops/elk/` (Logstash pipeline and config) and is wired to the application containers via `docker-compose.yml`.
- Incident handling and operational playbooks are documented in `SmartGrid_Project_Devops/RUNBOOKS.md` and assume the system is managed via Docker Compose.

When diagnosing issues, prefer the existing runbooks:
- Start with `docker-compose ps` and `docker-compose logs <service>` from `SmartGrid_Project_Devops/docker`.
- Use the health endpoints documented in `ARCHITECTURE.md` and `RUNBOOKS.md` (e.g., `/health` on each microservice, `/api/test` on the API Gateway).

## CI/CD and quality gates

- `.github/workflows/ci-cd.yml` defines the main pipeline:
  - `test` job: flake8 linting and import smoke tests for each Python service.
  - `build` job: builds (and on push, pushes) Docker images for each service to GHCR using `docker/build-push-action`.
  - `deploy` job: applies Kubernetes manifests to a `smartgrid` namespace when pushing to `main` with a configured `KUBECONFIG` secret.
  - `security` job: runs Trivy filesystem scans and uploads results to GitHub Security.
- `SmartGrid_Project_Devops/.github/workflows/code-quality.yml` sets up a SonarQube analysis job and a simple code review checklist.

When making changes that affect deployment or service contracts, keep Dockerfiles, `docker-compose.yml`, and the Kubernetes manifests in sync so that CI/CD and local Docker usage remain aligned.