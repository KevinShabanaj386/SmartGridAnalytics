# ELK Stack për Log Aggregation - Smart Grid Analytics

## Përmbledhje

ELK Stack (Elasticsearch, Logstash, Kibana) përdoret për agregimin, përpunimin dhe vizualizimin e logs nga të gjitha shërbimet e Smart Grid Analytics.

## Komponentët

### Elasticsearch
- **Qëllimi**: Storage dhe search engine për logs
- **Port**: 9200
- **Features**:
  - Indexing dhe searching e logs
  - Full-text search
  - Aggregations për analizë

### Logstash
- **Qëllimi**: Përpunim dhe transformim i logs
- **Ports**: 
  - 5044: Beats input
  - 5000: TCP input
  - 9600: Monitoring API
- **Features**:
  - Parsing i logs
  - Filtering dhe enrichment
  - Output në Elasticsearch

### Kibana
- **Qëllimi**: Vizualizim dhe analizë e logs
- **Port**: 5601
- **Features**:
  - Dashboards për logs
  - Discover për search
  - Visualizations

## Përdorimi

### 1. Nisni ELK Stack

```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d elasticsearch logstash kibana
```

### 2. Kontrolloni Status

```bash
# Elasticsearch
curl http://localhost:9200/_cluster/health

# Logstash
curl http://localhost:9600/_node/stats

# Kibana
# Hapni në shfletues: http://localhost:5601
```

### 3. Shikoni Logs në Kibana

1. Hapni Kibana: http://localhost:5601
2. Shkoni te **Discover**
3. Krijoni index pattern: `smartgrid-logs-*`
4. Shikoni logs në kohë reale

## Konfigurimi i Logs

### Nga Aplikacionet

Aplikacionet duhet të dërgojnë logs në Logstash:

```python
import logging
import socket

# Konfiguro logging për të dërguar në Logstash
logstash_handler = logging.handlers.SocketHandler('smartgrid-logstash', 5000)
logger.addHandler(logstash_handler)
```

### Ose përdorni Filebeat

Filebeat mund të instalohet në çdo shërbim për të dërguar logs:

```yaml
filebeat.inputs:
  - type: log
    paths:
      - /var/log/smartgrid/*.log
    fields:
      service: api-gateway
    fields_under_root: true

output.logstash:
  hosts: ["smartgrid-logstash:5044"]
```

## Index Patterns

Kibana kërkon index patterns për të shfaqur logs:

1. **Pattern**: `smartgrid-logs-*`
2. **Time field**: `@timestamp`
3. **Refresh**: Automatik

## Dashboards

### Krijo Dashboard në Kibana

1. Shkoni te **Dashboard**
2. Klikoni **Create dashboard**
3. Shtoni visualizations:
   - Log count over time
   - Error rate by service
   - Top services by log volume
   - Log level distribution

### Sample Queries

```json
// Gjej të gjitha errors
{
  "query": {
    "match": {
      "level": "ERROR"
    }
  }
}

// Logs nga një shërbim specifik
{
  "query": {
    "match": {
      "service": "api-gateway"
    }
  }
}

// Logs në orët e fundit
{
  "query": {
    "range": {
      "@timestamp": {
        "gte": "now-1h"
      }
    }
  }
}
```

## Monitoring

### Elasticsearch Health

```bash
curl http://localhost:9200/_cluster/health?pretty
```

### Logstash Pipeline Status

```bash
curl http://localhost:9600/_node/stats/pipelines?pretty
```

### Index Stats

```bash
curl http://localhost:9200/smartgrid-logs-*/_stats?pretty
```

## Retention Policy

Konfiguroni retention për logs:

```bash
# Fshi logs më të vjetër se 30 ditë
curl -X DELETE "http://localhost:9200/smartgrid-logs-$(date -d '30 days ago' +%Y.%m.%d)"
```

Ose përdorni Index Lifecycle Management (ILM) në Elasticsearch.

## Best Practices

1. **Index Rotation**: Përdorni daily indexes (`smartgrid-logs-YYYY.MM.dd`)
2. **Retention**: Fshini logs të vjetra për të kursyer hapësirë
3. **Parsing**: Përdorni Grok patterns për parsing të saktë
4. **Filtering**: Filtroni logs që nuk janë të rëndësishme
5. **Monitoring**: Monitoroni Elasticsearch cluster health

## Troubleshooting

### Logstash nuk merr logs
```bash
# Kontrollo Logstash logs
docker logs smartgrid-logstash

# Test input
echo '{"message": "test"}' | nc localhost 5000
```

### Elasticsearch disk space
```bash
# Shikoni disk usage
curl http://localhost:9200/_cat/allocation?v

# Fshi indexes të vjetra
curl -X DELETE "http://localhost:9200/smartgrid-logs-2024.01.*"
```

### Kibana nuk shfaq logs
- Kontrollo që index pattern është krijuar
- Verifikoni që ka logs në Elasticsearch
- Kontrollo time range në Discover

## Integrim me Aplikacionet

Për të dërguar logs nga aplikacionet Python:

```python
import logging
import json
import socket

class LogstashHandler(logging.Handler):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
    
    def emit(self, record):
        log_entry = {
            '@timestamp': self.format(record.created),
            'level': record.levelname,
            'message': record.getMessage(),
            'service': 'analytics-service',
            'logger': record.name
        }
        self.socket.send(json.dumps(log_entry).encode() + b'\n')

# Përdorimi
logger = logging.getLogger(__name__)
logger.addHandler(LogstashHandler('smartgrid-logstash', 5000))
```

## Hapi Tjetër

- [ ] Konfiguro Index Lifecycle Management
- [ ] Krijo dashboards të detajuara
- [ ] Shto alerting në Kibana
- [ ] Integro me monitoring tools
- [ ] Shto log sampling për volume të lartë

