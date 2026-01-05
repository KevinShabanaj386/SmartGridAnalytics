"""
ML Model për Load Forecasting në Smart Grid
Përdor MLflow për tracking, registry dhe versioning
"""
import mlflow
import mlflow.sklearn
import mlflow.pyfunc
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import psycopg2
import logging
from datetime import datetime, timedelta
import os
import pickle
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurimi i MLflow
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://smartgrid-mlflow:5000')
MLFLOW_EXPERIMENT_NAME = os.getenv('MLFLOW_EXPERIMENT_NAME', 'smartgrid-load-forecasting')

# PostgreSQL konfigurim
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
    'user': os.getenv('POSTGRES_USER', 'smartgrid'),
    'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
}

def get_training_data(days: int = 30) -> pd.DataFrame:
    """Merr të dhënat historike për trajnim"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    query = """
        SELECT 
            DATE_TRUNC('hour', timestamp) as hour_bucket,
            sensor_id,
            sensor_type,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value,
            COUNT(*) as count,
            EXTRACT(HOUR FROM timestamp) as hour_of_day,
            EXTRACT(DOW FROM timestamp) as day_of_week,
            EXTRACT(MONTH FROM timestamp) as month
        FROM sensor_data
        WHERE sensor_type = 'power'
        AND timestamp >= NOW() - INTERVAL '%s days'
        GROUP BY 
            DATE_TRUNC('hour', timestamp),
            sensor_id,
            sensor_type,
            EXTRACT(HOUR FROM timestamp),
            EXTRACT(DOW FROM timestamp),
            EXTRACT(MONTH FROM timestamp)
        ORDER BY hour_bucket
    """
    
    df = pd.read_sql_query(query, conn, params=[days])
    conn.close()
    
    return df

def prepare_features(df: pd.DataFrame) -> tuple:
    """Përgatit features për model"""
    # Features për trajnim
    feature_columns = [
        'hour_of_day',
        'day_of_week',
        'month',
        'min_value',
        'max_value',
        'count'
    ]
    
    # Krijo lag features (vlerat e orës së kaluar)
    df['prev_hour_avg'] = df['avg_value'].shift(1)
    df['prev_hour_min'] = df['min_value'].shift(1)
    df['prev_hour_max'] = df['max_value'].shift(1)
    
    # Krijo rolling averages
    df['rolling_avg_3h'] = df['avg_value'].rolling(window=3, min_periods=1).mean()
    df['rolling_avg_24h'] = df['avg_value'].rolling(window=24, min_periods=1).mean()
    
    # Features përfundimtare
    feature_columns.extend(['prev_hour_avg', 'prev_hour_min', 'prev_hour_max', 
                          'rolling_avg_3h', 'rolling_avg_24h'])
    
    # Target variable
    target_column = 'avg_value'
    
    # Hiq NaN values
    df = df.dropna()
    
    X = df[feature_columns]
    y = df[target_column]
    
    return X, y, feature_columns

def train_load_forecasting_model(
    n_estimators: int = 100,
    max_depth: int = 10,
    min_samples_split: int = 2,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Trajnon model për load forecasting dhe e regjistron në MLflow
    """
    logger.info("Starting model training...")
    
    # Konfiguro MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    
    # Merr të dhënat
    logger.info("Loading training data...")
    df = get_training_data(days=30)
    
    if df.empty:
        raise ValueError("No training data available")
    
    logger.info(f"Loaded {len(df)} records")
    
    # Përgatit features
    X, y, feature_columns = prepare_features(df)
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, shuffle=False
    )
    
    logger.info(f"Training set: {len(X_train)}, Test set: {len(X_test)}")
    
    # Start MLflow run
    with mlflow.start_run(run_name=f"load_forecasting_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        
        # Log parameters
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("min_samples_split", min_samples_split)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("training_samples", len(X_train))
        mlflow.log_param("test_samples", len(X_test))
        mlflow.log_param("features", feature_columns)
        
        # Trajno model
        logger.info("Training Random Forest model...")
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            random_state=random_state,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Bëj predictions
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        # Llogarit metrikat
        train_mae = mean_absolute_error(y_train, y_train_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        train_r2 = r2_score(y_train, y_train_pred)
        
        test_mae = mean_absolute_error(y_test, y_test_pred)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        test_r2 = r2_score(y_test, y_test_pred)
        
        # Log metrikat
        mlflow.log_metric("train_mae", train_mae)
        mlflow.log_metric("train_rmse", train_rmse)
        mlflow.log_metric("train_r2", train_r2)
        mlflow.log_metric("test_mae", test_mae)
        mlflow.log_metric("test_rmse", test_rmse)
        mlflow.log_metric("test_r2", test_r2)
        
        # Log model
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="LoadForecastingModel"
        )
        
        # Log feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        mlflow.log_text(
            feature_importance.to_string(),
            "feature_importance.txt"
        )
        
        logger.info(f"Training completed. Test R2: {test_r2:.4f}, Test MAE: {test_mae:.4f}")
        
        return {
            'model': model,
            'metrics': {
                'train_mae': train_mae,
                'train_rmse': train_rmse,
                'train_r2': train_r2,
                'test_mae': test_mae,
                'test_rmse': test_rmse,
                'test_r2': test_r2
            },
            'feature_importance': feature_importance,
            'run_id': mlflow.active_run().info.run_id
        }

def predict_with_mlflow_model(
    model_name: str = "LoadForecastingModel",
    stage: str = "Production"
) -> np.ndarray:
    """
    Bën prediction duke përdorur model të regjistruar në MLflow
    """
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Load model nga registry
    model_uri = f"models:/{model_name}/{stage}"
    model = mlflow.sklearn.load_model(model_uri)
    
    # Merr të dhënat e fundit për prediction
    df = get_training_data(days=1)
    X, _, _ = prepare_features(df)
    
    # Bëj prediction
    predictions = model.predict(X.tail(24))  # 24 orët e ardhshme
    
    return predictions

if __name__ == '__main__':
    # Trajno model
    results = train_load_forecasting_model(
        n_estimators=100,
        max_depth=10,
        min_samples_split=2
    )
    
    print(f"Model trained successfully!")
    print(f"Test R2 Score: {results['metrics']['test_r2']:.4f}")
    print(f"Test MAE: {results['metrics']['test_mae']:.4f}")
    print(f"Run ID: {results['run_id']}")

