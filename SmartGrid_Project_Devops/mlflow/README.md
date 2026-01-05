# MLflow Model Management për Smart Grid Analytics

## Përmbledhje

MLflow përdoret për menaxhimin e plotë të modeleve të machine learning në Smart Grid Analytics, duke përfshirë tracking, registry, versioning dhe serving.

## Komponentët

### 1. MLflow Server
- Tracking server për eksperimente
- Model registry për versioning
- Artifact storage (MinIO/S3)

### 2. Modelet ML

#### Load Forecasting Model
- **Lloji**: Random Forest Regressor
- **Qëllimi**: Parashikon ngarkesën e energjisë për orët e ardhshme
- **Features**: 
  - hour_of_day, day_of_week, month
  - min_value, max_value, count
  - prev_hour_avg, prev_hour_min, prev_hour_max
  - rolling_avg_3h, rolling_avg_24h
- **Metrikat**: MAE, RMSE, R2 Score

#### Anomaly Detection Model
- **Lloji**: Isolation Forest
- **Qëllimi**: Zbulon anomalitë në të dhënat e sensorëve
- **Features**:
  - value, hour_of_day, day_of_week
  - latitude, longitude
  - sensor_type (encoded)
- **Metrikat**: Anomaly rate, Anomaly scores

## Përdorimi

### 1. Nisni MLflow Server

MLflow server niset automatikisht me docker-compose:

```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d mlflow minio
```

MLflow UI: http://localhost:5005
MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

### 2. Trajno Modelet

```bash
cd SmartGrid_Project_Devops/mlflow

# Trajno të gjitha modelet
python training_pipeline.py --model all

# Ose trajno një model specifik
python training_pipeline.py --model load_forecasting
python training_pipeline.py --model anomaly_detection
```

### 3. Promovo Model në Production

```bash
# Promovo version-in më të ri
python training_pipeline.py --promote LoadForecastingModel

# Ose promovo një version specifik
python training_pipeline.py --promote LoadForecastingModel --version 1
```

### 4. Përdor Model për Prediction

Modelet përdoren automatikisht në Analytics Service:

```bash
# Parashikim me ML model
curl -X GET "http://localhost:5000/api/v1/analytics/predictive/load-forecast?use_ml=true" \
  -H "Authorization: Bearer <token>"

# Parashikim me metodë të thjeshtë (fallback)
curl -X GET "http://localhost:5000/api/v1/analytics/predictive/load-forecast?use_ml=false" \
  -H "Authorization: Bearer <token>"
```

## Struktura e Eksperimenteve

### Load Forecasting Experiment
- **Name**: `smartgrid-load-forecasting`
- **Parameters**:
  - n_estimators
  - max_depth
  - min_samples_split
  - random_state
- **Metrics**:
  - train_mae, train_rmse, train_r2
  - test_mae, test_rmse, test_r2
- **Artifacts**:
  - model (sklearn)
  - feature_importance.txt

### Anomaly Detection Experiment
- **Name**: `smartgrid-anomaly-detection`
- **Parameters**:
  - contamination
  - n_estimators
  - random_state
- **Metrics**:
  - n_anomalies
  - n_normal
  - anomaly_rate
  - mean_anomaly_score
- **Artifacts**:
  - model (sklearn)
  - scaler.pkl

## Model Registry

Modelet regjistrohen me emra:
- `LoadForecastingModel`
- `AnomalyDetectionModel`

### Stages
- **None**: Model i ri i trajnuar
- **Staging**: Model në test
- **Production**: Model i prodhimit
- **Archived**: Model i arkivuar

## API Integration

Analytics Service integrohet automatikisht me MLflow:

1. **Load Forecasting**: Përdor `LoadForecastingModel/Production` për predictions
2. **Anomaly Detection**: Mund të integrohet për zbulim më të saktë të anomalive

## Monitoring

### MLflow UI
- Shikoni eksperimentet: http://localhost:5005
- Krahasoni runs
- Shikoni metrikat dhe artifacts
- Shkarkoni modelet

### Model Performance
- Metrikat loggohen në çdo run
- Mund të krahasoni performance të modeleve të ndryshme
- Tracking i versioning për çdo model

## Best Practices

1. **Versioning**: Çdo model version regjistrohet automatikisht
2. **Staging**: Testoni modelet në Staging para Production
3. **Monitoring**: Monitoroni performance në prodhim
4. **Retraining**: Retrajno modelet periodikisht me të dhëna të reja
5. **A/B Testing**: Krahasoni modelet e ndryshme në MLflow UI

## Troubleshooting

### MLflow nuk lidhet
```bash
# Kontrollo që MLflow server është në funksion
docker ps | grep mlflow

# Kontrollo logs
docker logs smartgrid-mlflow
```

### Model nuk gjendet
```bash
# Kontrollo që model është promovuar në Production
# Në MLflow UI, shikoni Model Registry
```

### MinIO connection issues
```bash
# Kontrollo që MinIO është në funksion
docker ps | grep minio

# Test connection
curl http://localhost:9000/minio/health/live
```

## Hapi Tjetër

- [ ] Shto më shumë modele ML (time series forecasting, clustering)
- [ ] Automatizo retraining me Airflow
- [ ] Model serving me MLflow Serving
- [ ] A/B testing framework
- [ ] Model monitoring dhe alerting

