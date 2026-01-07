# SIEM Threat Detection - Smart Grid Analytics

## Përmbledhje

Sistemi i SIEM Threat Detection integron me ELK Stack për të detektuar dhe korreluar security threats në kohë reale.

## Komponentët

### 1. Logstash Threat Detection Rules
**Vendndodhja**: `elk/logstash/pipeline/threat-detection.conf`

**Threat Types të Detektuara:**
- ✅ Failed Login Attempts (Brute Force)
- ✅ SQL Injection Attacks
- ✅ XSS (Cross-Site Scripting) Attacks
- ✅ Unauthorized Access (401/403)
- ✅ Rate Limiting Violations
- ✅ IP Lockout Events
- ✅ High Risk Users (Behavioral Analytics)
- ✅ Unusual Access Patterns
- ✅ Sensitive Data Access (DAG)
- ✅ Service Errors
- ✅ JWT Token Violations
- ✅ OAuth2 Violations
- ✅ Kafka Consumer Lag
- ✅ Database Connection Failures
- ✅ Geographic Anomalies

### 2. Elasticsearch Watchers
**Vendndodhja**: `elk/elasticsearch/threat-detection-watcher.json`

**Features:**
- Real-time monitoring për high/critical threats
- Automatic alerts në notification service
- Correlation për multiple threats

### 3. Kibana Dashboards
**Vendndodhja**: `elk/kibana/threat-detection-dashboard.json`

**Visualizations:**
- Threat Events Timeline
- Threat Severity Distribution
- Top Threat Types
- Threats by IP Address

### 4. SIEM Threat Detection Service
**Vendndodhja**: `elk/siem-threat-detection-service.py`

**Functions:**
- `search_threats()` - Kërkon threats nga Elasticsearch
- `correlate_threats()` - Korrelon threats për attack patterns
- `get_threat_statistics()` - Merr statistika për threats
- `detect_brute_force_attack()` - Detekton brute force attacks
- `get_high_risk_ips()` - Merr IP addresses me risk të lartë

## Konfigurimi

### 1. Logstash Configuration

Shto threat detection në Logstash pipeline:

```bash
# Në docker-compose.yml, shto volume për threat-detection.conf
volumes:
  - ../elk/logstash/pipeline/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
  - ../elk/logstash/pipeline/threat-detection.conf:/usr/share/logstash/pipeline/threat-detection.conf
```

### 2. Elasticsearch Watcher

Instalo watcher në Elasticsearch:

```bash
# Në Elasticsearch, instalo watcher
PUT _watcher/watch/threat-detection
# Përdor content nga threat-detection-watcher.json
```

### 3. Kibana Dashboard

Importo dashboard në Kibana:

```bash
# Në Kibana UI:
# Management > Saved Objects > Import
# Upload threat-detection-dashboard.json
```

## Përdorimi

### Search Threats

```python
from elk.siem_threat_detection_service import search_threats

# Merr të gjitha high severity threats në 24 orët e fundit
threats = search_threats(
    severity="high",
    start_time=datetime.utcnow() - timedelta(hours=24)
)
```

### Correlate Threats

```python
from elk.siem_threat_detection_service import correlate_threats

# Korrelon threats në 5 minuta
correlated = correlate_threats(time_window_minutes=5, min_correlation_count=3)
```

### Get Threat Statistics

```python
from elk.siem_threat_detection_service import get_threat_statistics

# Merr statistika për 24 orët e fundit
stats = get_threat_statistics(hours=24)
print(f"Total threats: {stats['total_threats']}")
print(f"By severity: {stats['by_severity']}")
```

### Detect Brute Force

```python
from elk.siem_threat_detection_service import detect_brute_force_attack

# Detekton brute force attack për një IP
is_brute_force = detect_brute_force_attack("192.168.1.100", min_attempts=5)
```

### Get High Risk IPs

```python
from elk.siem_threat_detection_service import get_high_risk_ips

# Merr IP addresses me risk të lartë
high_risk_ips = get_high_risk_ips(hours=24, min_threat_count=5)
```

## Integration me Services

### Behavioral Analytics Integration

Threat detection integron me behavioral analytics për të detektuar high risk users:

```python
# Në Logstash, threat detection kontrollon risk_score
if [risk_score] > 70 {
  mutate {
    add_tag => [ "security_threat", "high_risk_user" ]
    add_field => { "threat_type" => "behavioral_anomaly" }
  }
}
```

### Data Access Governance Integration

Threat detection integron me DAG për të detektuar sensitive data access:

```python
# Në Logstash, threat detection kontrollon classification
if [classification] in ["CONFIDENTIAL", "RESTRICTED"] {
  mutate {
    add_tag => [ "security_threat", "sensitive_data_access" ]
  }
}
```

## Alerts

### Automatic Alerts

Elasticsearch Watcher dërgon alerts automatikisht në notification service për:
- High severity threats
- Critical threats
- Correlated attack patterns

### Alert Format

```json
{
  "type": "webhook",
  "recipient": "security-team@smartgrid.local",
  "subject": "SIEM Threat Alert",
  "message": "X high/critical threat(s) detected",
  "priority": "critical",
  "metadata": {
    "threats": [...]
  }
}
```

## Monitoring

### Kibana Dashboard

Hap Kibana dashboard për real-time threat monitoring:
1. Hap Kibana: http://localhost:5601
2. Shkoni te Dashboard > SIEM Threat Detection Dashboard
3. Shikoni threats në kohë reale

### Elasticsearch Queries

Query për threats:

```json
GET smartgrid-threats-*/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "@timestamp": {
              "gte": "now-1h"
            }
          }
        },
        {
          "terms": {
            "threat_severity": ["high", "critical"]
          }
        }
      ]
    }
  }
}
```

## Status

**SIEM Threat Detection: 80% Implementuar** ✅

**Çfarë është implementuar:**
- ✅ 15 threat detection rules
- ✅ Elasticsearch watchers për alerts
- ✅ Kibana dashboards për visualization
- ✅ Threat correlation për attack patterns
- ✅ Integration me Behavioral Analytics
- ✅ Integration me Data Access Governance
- ✅ High risk IP detection
- ✅ Brute force attack detection

**Çfarë mungon:**
- ⚠️ Threat intelligence integration (10%)
- ⚠️ Automated incident response (SOAR) (10%)

