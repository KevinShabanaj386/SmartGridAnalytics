# SmartGrid DevOps / Platform

## Pjesa DevOps / Monitoring

### Docker Compose
- PostgreSQL + Kafka + Zookeeper + Exporters + Prometheus + Grafana
- API Gateway minimal me JWT të simuluar

### Testim i API Gateway
- Endpoint `/api/test`
- Token: `Bearer mysecrettoken`

### CI/CD (teorik)
- Build docker images: `docker build -t <image_name> ./<service_folder>`
- Run shërbimet: `docker-compose up -d`
- Integrim me GitHub Actions ose Jenkins:
  - **Build** → Docker images
  - **Test** → curl ose unit tests
  - **Deploy** → docker-compose update / restart

### Security
- JWT simulim në API Gateway
- Në prodhim do të përdoret validim real JWT

### Monitoring
- Prometheus scrape exporters (Postgres, Kafka, API metrics)
- Grafana dashboards për metrics
