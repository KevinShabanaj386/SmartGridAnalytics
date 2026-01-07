"""
Random Forest ML Model për Anomaly Detection (bazuar në campus-energy-streaming-pipeline)
98.6% accuracy si në projektin e referencuar
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import logging
import pickle
import os
from typing import Dict, List, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Model configuration
MODEL_DIR = os.getenv('MODEL_DIR', '/app/models')
MODEL_NAME = 'random_forest_anomaly'
ANOMALY_THRESHOLD = 0.5  # Probability threshold për anomaly

def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, StandardScaler]:
    """
    Përgatit features për Random Forest model
    Features: electricity, water, hour_of_day, day_of_week, building, floor
    """
    # Krijo features
    features = pd.DataFrame()
    
    # Features numerike - konverto në float
    if 'value' in df.columns:
        features['electricity'] = pd.to_numeric(df['value'], errors='coerce').fillna(0).astype(float)
    elif 'reading' in df.columns:
        features['electricity'] = pd.to_numeric(df['reading'], errors='coerce').fillna(0).astype(float)
    else:
        features['electricity'] = 0
    
    # Water consumption (nëse ekziston)
    if 'water' in df.columns:
        features['water'] = df['water'].fillna(0)
    else:
        features['water'] = 0
    
    # Temporal features
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        features['hour_of_day'] = df['timestamp'].dt.hour
        features['day_of_week'] = df['timestamp'].dt.dayofweek
        features['month'] = df['timestamp'].dt.month
    else:
        features['hour_of_day'] = datetime.now().hour
        features['day_of_week'] = datetime.now().weekday()
        features['month'] = datetime.now().month
    
    # Location features (nëse ekzistojnë) - konverto në float
    if 'latitude' in df.columns and 'longitude' in df.columns:
        features['latitude'] = pd.to_numeric(df['latitude'], errors='coerce').fillna(0).astype(float)
        features['longitude'] = pd.to_numeric(df['longitude'], errors='coerce').fillna(0).astype(float)
    else:
        features['latitude'] = 0.0
        features['longitude'] = 0.0
    
    # Normalize features - sigurohu që të gjitha kolonat janë float
    scaler = StandardScaler()
    feature_columns = ['electricity', 'water', 'hour_of_day', 'day_of_week', 'month', 'latitude', 'longitude']
    
    # Konverto të gjitha kolonat në float
    for col in feature_columns:
        if col in features.columns:
            features[col] = pd.to_numeric(features[col], errors='coerce').fillna(0).astype(float)
        else:
            features[col] = 0.0
    
    features_scaled = scaler.fit_transform(features[feature_columns])
    
    return pd.DataFrame(features_scaled, columns=feature_columns), scaler

def train_random_forest_model(
    training_data: pd.DataFrame,
    labels: pd.Series,
    n_estimators: int = 100,
    max_depth: int = 20,
    min_samples_split: int = 2,
    random_state: int = 42
) -> Tuple[RandomForestClassifier, StandardScaler, Dict[str, Any]]:
    """
    Trajnon Random Forest model për anomaly detection
    """
    logger.info("Training Random Forest model for anomaly detection...")
    
    # Përgatit features
    X, scaler = prepare_features(training_data)
    y = labels.values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        random_state=random_state,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]  # Probability për anomaly class
    
    accuracy = accuracy_score(y_test, y_pred)
    
    logger.info(f"Model trained with accuracy: {accuracy:.4f}")
    logger.info(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")
    
    # Save model
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, f"{MODEL_NAME}.pkl")
    scaler_path = os.path.join(MODEL_DIR, f"{MODEL_NAME}_scaler.pkl")
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    logger.info(f"Model saved to {model_path}")
    
    metrics = {
        'accuracy': float(accuracy),
        'n_estimators': n_estimators,
        'max_depth': max_depth,
        'training_samples': len(X_train),
        'test_samples': len(X_test),
        'anomaly_rate': float(np.mean(y_test))
    }
    
    return model, scaler, metrics

def detect_anomalies_with_rf(
    data: pd.DataFrame,
    model_path: str = None,
    scaler_path: str = None
) -> pd.DataFrame:
    """
    Zbulon anomalitë duke përdorur Random Forest model
    """
    # Load model
    if model_path is None:
        model_path = os.path.join(MODEL_DIR, f"{MODEL_NAME}.pkl")
    if scaler_path is None:
        scaler_path = os.path.join(MODEL_DIR, f"{MODEL_NAME}_scaler.pkl")
    
    if not os.path.exists(model_path):
        logger.warning(f"Model not found at {model_path}, using default threshold")
        # Fallback në metodën e thjeshtë
        # Sigurohu që 'value' është float
        if 'value' in data.columns:
            data['value'] = pd.to_numeric(data['value'], errors='coerce').fillna(0).astype(float)
        else:
            data['value'] = 0.0
        
        data['is_anomaly'] = data['value'] > data['value'].quantile(0.99)
        data['anomaly_probability'] = 0.5
        data['anomaly_type'] = 'high_consumption'
        return data
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    # Përgatit features
    X, _ = prepare_features(data)
    feature_columns = ['electricity', 'water', 'hour_of_day', 'day_of_week', 'month', 'latitude', 'longitude']
    X_scaled = scaler.transform(X[feature_columns])
    
    # Predict
    predictions = model.predict(X_scaled)
    probabilities = model.predict_proba(X_scaled)[:, 1]  # Probability për anomaly
    
    # Shto rezultatet
    data['is_anomaly'] = (probabilities >= ANOMALY_THRESHOLD) | (predictions == 1)
    data['anomaly_probability'] = probabilities
    
    # Classify anomaly type
    data['anomaly_type'] = 'normal'
    if 'value' in data.columns or 'reading' in data.columns:
        consumption = data['value'] if 'value' in data.columns else data['reading']
        mean_consumption = consumption.mean()
        std_consumption = consumption.std()
        
        # High consumption (2-3x normal)
        high_threshold = mean_consumption + 2 * std_consumption
        very_high_threshold = mean_consumption + 3 * std_consumption
        
        data.loc[data['is_anomaly'] & (consumption >= very_high_threshold), 'anomaly_type'] = 'very_high'
        data.loc[data['is_anomaly'] & (consumption >= high_threshold) & (consumption < very_high_threshold), 'anomaly_type'] = 'high_consumption'
        data.loc[data['is_anomaly'] & (consumption < high_threshold), 'anomaly_type'] = 'moderate'
    
    return data

def classify_anomaly_type(electricity: float, water: float, mean_electricity: float, mean_water: float) -> str:
    """
    Klasifikon llojin e anomalisë bazuar në konsumim
    """
    electricity_ratio = electricity / mean_electricity if mean_electricity > 0 else 1
    water_ratio = water / mean_water if mean_water > 0 else 1
    
    # Very high consumption (>3x normal)
    if electricity_ratio >= 3.0:
        return 'very_high'
    
    # High consumption (2-3x normal)
    if electricity_ratio >= 2.0:
        return 'high_consumption'
    
    # Water leak (water >> electricity)
    if water_ratio >= 2.0 and electricity_ratio < 1.5:
        return 'leak'
    
    return 'moderate'

