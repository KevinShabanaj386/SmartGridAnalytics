"""
ML Model për Anomaly Detection në Smart Grid
Përdor Isolation Forest për zbulim të anomalive
"""
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import psycopg2
import logging
from datetime import datetime
import os
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurimi
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://smartgrid-mlflow:5000')
MLFLOW_EXPERIMENT_NAME = os.getenv('MLFLOW_EXPERIMENT_NAME_ANOMALY', 'smartgrid-anomaly-detection')

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
    'user': os.getenv('POSTGRES_USER', 'smartgrid'),
    'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
}

def get_anomaly_training_data(days: int = 7) -> pd.DataFrame:
    """Merr të dhënat për trajnim të anomaly detection"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    query = """
        SELECT 
            sensor_id,
            sensor_type,
            value,
            EXTRACT(HOUR FROM timestamp) as hour_of_day,
            EXTRACT(DOW FROM timestamp) as day_of_week,
            latitude,
            longitude
        FROM sensor_data
        WHERE timestamp >= NOW() - INTERVAL '%s days'
        AND value IS NOT NULL
        AND latitude IS NOT NULL
        AND longitude IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn, params=[days])
    conn.close()
    
    return df

def prepare_anomaly_features(df: pd.DataFrame) -> pd.DataFrame:
    """Përgatit features për anomaly detection"""
    # Krijo features
    features = pd.DataFrame()
    
    # Features numerike
    features['value'] = df['value']
    features['hour_of_day'] = df['hour_of_day']
    features['day_of_week'] = df['day_of_week']
    features['latitude'] = df['latitude']
    features['longitude'] = df['longitude']
    
    # Encoding për sensor_type
    sensor_type_encoded = pd.get_dummies(df['sensor_type'], prefix='sensor_type')
    features = pd.concat([features, sensor_type_encoded], axis=1)
    
    # Normalizo features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    return pd.DataFrame(features_scaled, columns=features.columns), scaler

def train_anomaly_detection_model(
    contamination: float = 0.1,
    n_estimators: int = 100,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Trajnon model për anomaly detection
    """
    logger.info("Starting anomaly detection model training...")
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    
    # Merr të dhënat
    df = get_anomaly_training_data(days=7)
    
    if df.empty:
        raise ValueError("No training data available")
    
    logger.info(f"Loaded {len(df)} records")
    
    # Përgatit features
    X, scaler = prepare_anomaly_features(df)
    
    # Start MLflow run
    with mlflow.start_run(run_name=f"anomaly_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        
        # Log parameters
        mlflow.log_param("contamination", contamination)
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("training_samples", len(X))
        
        # Trajno model
        logger.info("Training Isolation Forest model...")
        model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1
        )
        
        model.fit(X)
        
        # Bëj predictions
        predictions = model.predict(X)
        anomaly_scores = model.score_samples(X)
        
        # Llogarit metrikat
        n_anomalies = np.sum(predictions == -1)
        n_normal = np.sum(predictions == 1)
        anomaly_rate = n_anomalies / len(predictions)
        
        # Log metrikat
        mlflow.log_metric("n_anomalies", n_anomalies)
        mlflow.log_metric("n_normal", n_normal)
        mlflow.log_metric("anomaly_rate", anomaly_rate)
        mlflow.log_metric("mean_anomaly_score", np.mean(anomaly_scores))
        mlflow.log_metric("std_anomaly_score", np.std(anomaly_scores))
        
        # Log model dhe scaler
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="AnomalyDetectionModel"
        )
        
        # Log scaler si artifact
        import pickle
        scaler_path = "scaler.pkl"
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        mlflow.log_artifact(scaler_path)
        
        logger.info(f"Training completed. Anomalies detected: {n_anomalies} ({anomaly_rate*100:.2f}%)")
        
        return {
            'model': model,
            'scaler': scaler,
            'metrics': {
                'n_anomalies': n_anomalies,
                'n_normal': n_normal,
                'anomaly_rate': anomaly_rate,
                'mean_anomaly_score': np.mean(anomaly_scores)
            },
            'run_id': mlflow.active_run().info.run_id
        }

def detect_anomalies_with_model(
    data: pd.DataFrame,
    model_name: str = "AnomalyDetectionModel",
    stage: str = "Production"
) -> pd.DataFrame:
    """
    Zbulon anomalitë duke përdorur model të regjistruar në MLflow
    """
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Load model dhe scaler
    model_uri = f"models:/{model_name}/{stage}"
    model = mlflow.sklearn.load_model(model_uri)
    
    # Load scaler nga artifacts
    client = mlflow.tracking.MlflowClient()
    latest_version = client.get_latest_versions(model_name, stages=[stage])[0]
    scaler_path = mlflow.artifacts.download_artifacts(
        run_id=latest_version.run_id,
        artifact_path="scaler.pkl"
    )
    
    with open(scaler_path, 'rb') as f:
        import pickle
        scaler = pickle.load(f)
    
    # Përgatit features
    X, _ = prepare_anomaly_features(data)
    X_scaled = scaler.transform(X)
    
    # Bëj prediction
    predictions = model.predict(X_scaled)
    anomaly_scores = model.score_samples(X_scaled)
    
    # Shto rezultatet në dataframe
    data['is_anomaly'] = predictions == -1
    data['anomaly_score'] = anomaly_scores
    
    return data

if __name__ == '__main__':
    # Trajno model
    results = train_anomaly_detection_model(
        contamination=0.1,
        n_estimators=100
    )
    
    print(f"Anomaly detection model trained successfully!")
    print(f"Anomalies detected: {results['metrics']['n_anomalies']}")
    print(f"Anomaly rate: {results['metrics']['anomaly_rate']*100:.2f}%")
    print(f"Run ID: {results['run_id']}")

