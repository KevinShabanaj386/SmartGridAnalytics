"""
Training Pipeline për modelet ML të Smart Grid
Ekzekuton trajnim të të gjitha modeleve dhe i regjistron në MLflow
"""
import os
import sys
import logging
from datetime import datetime
import argparse

# Shto path për models
sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))

from load_forecasting_model import train_load_forecasting_model
from anomaly_detection_model import train_anomaly_detection_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def train_all_models():
    """Trajnon të gjitha modelet"""
    logger.info("Starting training pipeline for all models...")
    
    results = {}
    
    # 1. Train Load Forecasting Model
    try:
        logger.info("=" * 50)
        logger.info("Training Load Forecasting Model...")
        logger.info("=" * 50)
        
        load_forecast_results = train_load_forecasting_model(
            n_estimators=100,
            max_depth=10,
            min_samples_split=2,
            random_state=42
        )
        
        results['load_forecasting'] = load_forecast_results
        logger.info("✅ Load Forecasting Model trained successfully")
        
    except Exception as e:
        logger.error(f"❌ Error training Load Forecasting Model: {str(e)}")
        results['load_forecasting'] = {'error': str(e)}
    
    # 2. Train Anomaly Detection Model
    try:
        logger.info("=" * 50)
        logger.info("Training Anomaly Detection Model...")
        logger.info("=" * 50)
        
        anomaly_results = train_anomaly_detection_model(
            contamination=0.1,
            n_estimators=100,
            random_state=42
        )
        
        results['anomaly_detection'] = anomaly_results
        logger.info("✅ Anomaly Detection Model trained successfully")
        
    except Exception as e:
        logger.error(f"❌ Error training Anomaly Detection Model: {str(e)}")
        results['anomaly_detection'] = {'error': str(e)}
    
    # Përmbledhje
    logger.info("=" * 50)
    logger.info("Training Pipeline Summary")
    logger.info("=" * 50)
    
    for model_name, result in results.items():
        if 'error' in result:
            logger.error(f"{model_name}: FAILED - {result['error']}")
        else:
            logger.info(f"{model_name}: SUCCESS")
            if 'metrics' in result:
                logger.info(f"  Metrics: {result['metrics']}")
            if 'run_id' in result:
                logger.info(f"  Run ID: {result['run_id']}")
    
    return results

def promote_model_to_production(model_name: str, version: int = None):
    """Promovon model në Production stage"""
    import mlflow
    from mlflow.tracking import MlflowClient
    
    mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI', 'http://smartgrid-mlflow:5000'))
    client = MlflowClient()
    
    if version is None:
        # Merr version-in më të ri
        latest_version = client.get_latest_versions(model_name, stages=["None"])[0]
        version = latest_version.version
    
    # Promovo në Production
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage="Production"
    )
    
    logger.info(f"✅ Model {model_name} version {version} promoted to Production")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ML Training Pipeline')
    parser.add_argument('--model', type=str, choices=['all', 'load_forecasting', 'anomaly_detection'],
                       default='all', help='Model to train')
    parser.add_argument('--promote', type=str, help='Promote model to production')
    parser.add_argument('--version', type=int, help='Model version to promote')
    
    args = parser.parse_args()
    
    if args.promote:
        promote_model_to_production(args.promote, args.version)
    else:
        if args.model == 'all':
            train_all_models()
        elif args.model == 'load_forecasting':
            train_load_forecasting_model()
        elif args.model == 'anomaly_detection':
            train_anomaly_detection_model()

