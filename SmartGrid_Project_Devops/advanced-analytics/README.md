# Advanced Analytics & Data Intelligence Layer

## Përmbledhje

Ky layer implementon Advanced Analytics dhe Data Intelligence capabilities për Smart Grid Analytics, duke përfshirë MLOps, real-time reporting, dhe data mining.

## Komponentët

### 1. MLOps & Model Deployment

#### ✅ TensorFlow Serving
- **Status**: Implementuar
- **Location**: `docker/tensorflow-serving/`
- **Ports**: 
  - 8500 (gRPC API)
  - 8501 (REST API)
- **Features**:
  - RESTful API për predictions
  - gRPC API për low-latency
  - Model versioning
  - Automatic model reloading

**Usage**:
```python
from docker.tensorflow-serving.tf_serving_client import predict_with_tf_serving

# Bëj prediction
result = predict_with_tf_serving(
    instances=[[feature1, feature2, ...]],
    model_name='smartgrid-load-forecasting'
)
```

#### ✅ AutoML Platforms
- **Status**: Implementuar
- **Location**: `advanced-analytics/automl/automl_integration.py`
- **Platforms**:
  - **AutoKeras**: Neural architecture search
  - **TPOT**: Genetic programming për ML pipelines
  - **H2O AutoML**: Automated ML workflows

**Usage**:
```python
from advanced_analytics.automl.automl_integration import train_with_automl

# Trajno model me AutoML
result = train_with_automl(
    X_train=X_train,
    y_train=y_train,
    task='regression',
    platform='autokeras'  # ose 'tpot', 'h2o'
)
```

#### ✅ MLflow (Existing)
- **Status**: Implementuar
- **Location**: `mlflow/`
- **Features**:
  - Model tracking
  - Model registry
  - Versioning
  - Artifact storage

### 2. Real-Time Reporting & Notifications

#### ✅ Grafana Dashboards
- **Status**: Implementuar
- **Location**: `grafana/dashboards/`
- **Features**:
  - Real-time interactive dashboards
  - Live metrics visualization
  - Custom alerting rules
  - Advanced analytics panels

#### ✅ Power BI Embedded
- **Status**: Implementuar
- **Location**: `advanced-analytics/powerbi/powerbi_embedded.py`
- **Features**:
  - Interactive reports
  - Data visualization
  - Export capabilities (PDF, Excel)
  - Embed tokens për secure access

**API Endpoints**:
- `GET /api/v1/analytics/powerbi/reports` - Lista e reports
- `GET /api/v1/analytics/powerbi/embed-token?report_id=<id>` - Embed token

**Configuration**:
```bash
export POWERBI_CLIENT_ID="your-client-id"
export POWERBI_CLIENT_SECRET="your-client-secret"
export POWERBI_TENANT_ID="your-tenant-id"
export POWERBI_WORKSPACE_ID="your-workspace-id"
```

#### ✅ QGIS Integration
- **Status**: Implementuar
- **Location**: `advanced-analytics/qgis/qgis_integration.py`
- **Features**:
  - Spatial data visualization
  - Geographic analysis
  - Map generation
  - Feature information queries

**API Endpoints**:
- `GET /api/v1/analytics/qgis/map?bbox=minx,miny,maxx,maxy&width=800&height=600` - Map image
- `GET /api/v1/analytics/qgis/feature-info?x=lon&y=lat&bbox=...` - Feature info

**Configuration**:
```bash
export QGIS_SERVER_URL="http://smartgrid-qgis-server:80"
export QGIS_PROJECT_PATH="/qgis-projects/smartgrid.qgs"
```

### 3. Event-Driven Notifications

#### ✅ Webhooks
- **Status**: Implementuar
- **Location**: `docker/notification-service/webhook_handler.py`
- **Features**:
  - HTTP POST to external systems
  - Retry logic with exponential backoff
  - HMAC signature verification
  - Batch webhook sending

**Usage**:
```python
from webhook_handler import send_webhook

result = send_webhook(
    url='https://external-system.com/webhook',
    payload={'message': 'Alert', 'severity': 'high'},
    secret='webhook-secret-key'
)
```

#### ✅ SMS Notifications
- **Status**: Implementuar
- **Location**: `docker/notification-service/sms_handler.py`
- **Providers**:
  - Twilio (production)
  - AWS SNS (alternative)

**Usage**:
```python
from sms_handler import send_sms

result = send_sms(
    to_phone='+1234567890',
    message='Critical alert: Sensor anomaly detected',
    provider='twilio'  # ose 'aws_sns'
)
```

**Configuration**:
```bash
# Twilio
export TWILIO_ACCOUNT_SID="your-account-sid"
export TWILIO_AUTH_TOKEN="your-auth-token"
export TWILIO_PHONE_NUMBER="+1234567890"

# AWS SNS
export AWS_SNS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

#### ✅ Push Notifications
- **Status**: Implementuar
- **Location**: `docker/notification-service/push_notification_handler.py`
- **Protocols**:
  - FCM (Firebase Cloud Messaging)
  - APNS (Apple Push Notification Service)
  - Web Push (browser)

**Usage**:
```python
from push_notification_handler import send_push_notification

result = send_push_notification(
    device_token='fcm-device-token',
    title='Smart Grid Alert',
    body='Anomaly detected in sensor network',
    platform='fcm',  # ose 'apns', 'webpush'
    data={'sensor_id': 'sensor_001', 'severity': 'high'}
)
```

**Configuration**:
```bash
# FCM
export FCM_SERVER_KEY="your-fcm-server-key"
export FCM_PROJECT_ID="your-project-id"

# APNS
export APNS_KEY_PATH="/path/to/apns-key.p8"
export APNS_KEY_ID="your-key-id"
export APNS_TEAM_ID="your-team-id"
export APNS_BUNDLE_ID="com.smartgrid.app"
export APNS_USE_SANDBOX="true"

# Web Push
export VAPID_PRIVATE_KEY="your-vapid-private-key"
export VAPID_EMAIL="mailto:admin@smartgrid.local"
```

### 4. Data Mining & Pattern Discovery

#### ✅ Clustering Algorithms
- **Status**: Implementuar
- **Location**: `docker/analytics-service/data_mining.py`
- **Algorithms**:
  - **K-Means**: Structured clustering
  - **DBSCAN**: Density-based clustering dhe outlier detection

**API Endpoints**:
- `POST /api/v1/analytics/data-mining/clustering/kmeans`
- `POST /api/v1/analytics/data-mining/clustering/dbscan`

#### ✅ Association Rule Mining
- **Status**: Implementuar
- **Location**: `docker/analytics-service/data_mining.py`
- **Algorithms**:
  - **Apriori**: Frequent itemset mining
  - **FP-Growth**: Efficient pattern discovery

**API Endpoints**:
- `POST /api/v1/analytics/data-mining/association-rules/apriori`
- `POST /api/v1/analytics/data-mining/association-rules/fp-growth`

## Deployment

### Docker Compose

TensorFlow Serving niset automatikisht me docker-compose:

```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d tensorflow-serving
```

### Kubernetes

TensorFlow Serving mund të deployohet në Kubernetes:

```bash
kubectl apply -f kubernetes/tensorflow-serving/
```

## Testing

### Test TensorFlow Serving

```bash
# Check model status
curl http://localhost:8501/v1/models/smartgrid-load-forecasting

# Bëj prediction
curl -X POST http://localhost:8501/v1/models/smartgrid-load-forecasting:predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [[feature1, feature2, ...]]}'
```

### Test Power BI Integration

```bash
# Merr reports
curl -X GET "http://localhost:5002/api/v1/analytics/powerbi/reports" \
  -H "Authorization: Bearer <token>"

# Merr embed token
curl -X GET "http://localhost:5002/api/v1/analytics/powerbi/embed-token?report_id=<report-id>" \
  -H "Authorization: Bearer <token>"
```

### Test QGIS Integration

```bash
# Merr map
curl -X GET "http://localhost:5002/api/v1/analytics/qgis/map?bbox=-180,-90,180,90&width=800&height=600" \
  -H "Authorization: Bearer <token>"

# Merr feature info
curl -X GET "http://localhost:5002/api/v1/analytics/qgis/feature-info?x=0&y=0&bbox=-180,-90,180,90" \
  -H "Authorization: Bearer <token>"
```

### Test Notifications

```bash
# Send webhook
curl -X POST "http://localhost:5003/api/v1/notifications/send" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "https://external-system.com/webhook",
    "type": "webhook",
    "message": "Test notification",
    "priority": "high"
  }'

# Send SMS
curl -X POST "http://localhost:5003/api/v1/notifications/send" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "+1234567890",
    "type": "sms",
    "message": "Test SMS",
    "priority": "critical"
  }'

# Send push notification
curl -X POST "http://localhost:5003/api/v1/notifications/send" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "fcm-device-token",
    "type": "push",
    "subject": "Test Push",
    "message": "Test push notification",
    "platform": "fcm"
  }'
```

## Best Practices

1. **Model Versioning**: Të gjitha modelet versioned në MLflow
2. **A/B Testing**: TensorFlow Serving për model comparison
3. **Monitoring**: Real-time model performance tracking
4. **Automation**: AutoML për continuous improvement
5. **Scalability**: Horizontal scaling për TensorFlow Serving
6. **Security**: Authentication për të gjitha APIs
7. **Low Latency**: gRPC për real-time predictions
8. **Reliability**: Retry logic për notifications

## Troubleshooting

### TensorFlow Serving nuk niset

```bash
# Kontrollo logs
docker logs smartgrid-tensorflow-serving

# Kontrollo që models directory ekziston
docker exec smartgrid-tensorflow-serving ls -la /models
```

### Power BI authentication fails

```bash
# Verifikoni credentials
echo $POWERBI_CLIENT_ID
echo $POWERBI_TENANT_ID

# Test access token
python -c "from advanced_analytics.powerbi.powerbi_embedded import get_powerbi_access_token; print(get_powerbi_access_token())"
```

### QGIS Server nuk përgjigjet

```bash
# Kontrollo që QGIS Server është running
curl http://smartgrid-qgis-server:80/qgisserver?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities
```

### SMS/Webhook/Push notifications dështojnë

```bash
# Kontrollo provider credentials
echo $TWILIO_ACCOUNT_SID
echo $FCM_SERVER_KEY

# Kontrollo logs
docker logs smartgrid-notification-service
```

## Next Steps

- [x] TensorFlow Serving deployment
- [x] AutoML integration
- [x] Power BI Embedded
- [x] QGIS integration
- [x] Enhanced webhooks
- [x] SMS notifications
- [x] Push notifications
- [x] Data Mining algorithms verification
- [ ] QGIS Server deployment në docker-compose
- [ ] Enhanced Grafana dashboards me predictive visualizations
- [ ] Model performance monitoring dhe alerting
- [ ] Automated retraining pipelines

