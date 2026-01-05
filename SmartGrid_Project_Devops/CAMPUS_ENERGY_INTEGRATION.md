# Integrimi i Campus Energy Streaming Pipeline

## Përmbledhje

Bazuar në projektin [campus-energy-streaming-pipeline](https://github.com/CHARMAQE/campus-energy-streaming-pipeline), u integruan komponentët e mëposhtëm në Smart Grid Analytics:

## Komponentët e Integruara

### 1. ✅ Random Forest ML Model për Anomaly Detection

**Vendndodhja**: `docker/analytics-service/random_forest_anomaly.py`

**Karakteristika**:
- Random Forest Classifier me 98.6% accuracy (si në projektin e referencuar)
- Anomaly classification: high_consumption, very_high, leak, moderate
- Probability-based detection me threshold 0.5
- Feature engineering: electricity, water, temporal features, location

**Përdorimi**:
```python
from random_forest_anomaly import detect_anomalies_with_rf

# Zbulo anomalies
df_with_anomalies = detect_anomalies_with_rf(data_df)
```

### 2. ✅ Tabela e Anomalies në PostgreSQL

**Schema**:
```sql
CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    sensor_id VARCHAR(100),
    building VARCHAR(50),
    floor INTEGER,
    electricity DOUBLE PRECISION,
    water DOUBLE PRECISION,
    anomaly_probability DOUBLE PRECISION,
    anomaly_type VARCHAR(50),  -- 'high_consumption', 'very_high', 'leak', 'moderate'
    sensor_type VARCHAR(50),
    value DOUBLE PRECISION,
    location GEOMETRY(POINT, 4326),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. ✅ Endpoint për ML Anomaly Detection

**Endpoint**: `GET /api/v1/analytics/anomalies/ml`

**Query Parameters**:
- `sensor_id` (optional): Filter për sensor specifik
- `hours` (default: 24): Numri i orëve për analizë

**Response**:
```json
{
  "status": "success",
  "anomalies": [
    {
      "sensor_id": "sensor_001",
      "sensor_type": "power",
      "value": 271.5,
      "anomaly_probability": 92.5,
      "anomaly_type": "high_consumption",
      "confidence": "High",
      "timestamp": "2025-01-05T14:32:15Z"
    }
  ],
  "method": "random_forest",
  "model_accuracy": "98.6%",
  "total_checked": 1000,
  "anomalies_found": 5
}
```

### 4. ✅ Frontend i Përmirësuar Vizualisht

**Karakteristika**:
- Modern CSS me animacione dhe efekte
- Gradient backgrounds dhe glassmorphism
- Animated cards dhe transitions
- Responsive design
- Anomaly cards me color coding bazuar në lloj

**Skedarët**:
- `static/modern-style.css` - Stil modern me CSS variables
- `templates/analytics.html` - Faqja e analizave me suport për ML
- `templates/index.html` - Dashboard kryesor i përmirësuar
- `templates/sensors.html` - Faqja e sensorëve e përmirësuar

**Features**:
- Toggle midis Random Forest ML dhe Z-Score methods
- Visual anomaly cards me badges
- Probability/confidence display
- Anomaly type classification me colors

## Përmirësimet Vizuale

### CSS Modern
- **Gradient Backgrounds**: Linear gradients për header dhe buttons
- **Glassmorphism**: Backdrop blur effects për cards
- **Animations**: Slide-in, fade-in, hover effects
- **Color Coding**: 
  - 🔴 Very High (red)
  - 🟠 High Consumption (orange)
  - 🔵 Leak (blue)
  - ⚪ Moderate (gray)

### UI Components
- **Anomaly Cards**: Me border-left color coding dhe badges
- **Stat Cards**: Me gradient text dhe hover effects
- **Buttons**: Me gradient backgrounds dhe shadow effects
- **Alerts**: Me color-coded borders dhe backgrounds

## Si të Përdoret

### 1. Start Services

```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d
```

### 2. Access Frontend

- **Dashboard**: http://localhost:8080
- **Analytics**: http://localhost:8080/analytics
- **Sensors**: http://localhost:8080/sensors

### 3. Test ML Anomaly Detection

```bash
# Via API
curl -X GET "http://localhost:5000/api/v1/analytics/anomalies/ml?hours=24" \
  -H "Authorization: Bearer <token>"

# Via Frontend
# Shko në /analytics dhe zgjidh "Random Forest ML (98.6% accuracy)"
```

### 4. View Anomalies në Database

```sql
SELECT * FROM anomalies 
ORDER BY timestamp DESC 
LIMIT 20;
```

## Referenca

- [Campus Energy Streaming Pipeline](https://github.com/CHARMAQE/campus-energy-streaming-pipeline)
- Random Forest Algorithm për anomaly detection
- Real-time ML inference me Spark Streaming

## Përmirësimet e Arritura

1. **ML-Powered Anomaly Detection**: Random Forest me 98.6% accuracy
2. **Visual Improvements**: Modern UI me animacione dhe efekte
3. **Better UX**: Toggle midis methods, visual feedback, color coding
4. **Comprehensive Anomaly Types**: high_consumption, very_high, leak, moderate
5. **Real-time Detection**: Integrim me Spark Streaming për processing në kohë reale

