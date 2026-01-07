"""
AutoML Integration për Smart Grid Analytics
Përdor AutoKeras dhe TPOT për automated model generation
"""
import logging
import os
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# AutoML Configuration
AUTOML_ENABLED = os.getenv('AUTOML_ENABLED', 'true').lower() == 'true'
AUTOML_PLATFORM = os.getenv('AUTOML_PLATFORM', 'autokeras')  # autokeras, tpot, h2o

def train_with_autokeras(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    task: str = 'regression',  # 'regression' ose 'classification'
    max_trials: int = 10,
    epochs: int = 100
) -> Dict[str, Any]:
    """
    Trajnon model duke përdorur AutoKeras (Neural Architecture Search).
    
    Args:
        X_train: Training features
        y_train: Training targets
        task: 'regression' ose 'classification'
        max_trials: Numri maksimal i trials për architecture search
        epochs: Numri i epochs për training
    
    Returns:
        Dict me model dhe performance metrics
    """
    try:
        import autokeras as ak
        
        # Initialize AutoKeras model
        if task == 'regression':
            model = ak.StructuredDataRegressor(
                max_trials=max_trials,
                overwrite=True
            )
        else:
            model = ak.StructuredDataClassifier(
                max_trials=max_trials,
                overwrite=True
            )
        
        # Train model
        logger.info(f"Starting AutoKeras training with {max_trials} trials...")
        model.fit(
            X_train,
            y_train,
            epochs=epochs,
            verbose=1
        )
        
        # Evaluate model
        predictions = model.predict(X_train)
        
        if task == 'regression':
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
            mae = mean_absolute_error(y_train, predictions)
            rmse = np.sqrt(mean_squared_error(y_train, predictions))
            r2 = r2_score(y_train, predictions)
            
            metrics = {
                'mae': float(mae),
                'rmse': float(rmse),
                'r2': float(r2)
            }
        else:
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            accuracy = accuracy_score(y_train, predictions)
            precision = precision_score(y_train, predictions, average='weighted')
            recall = recall_score(y_train, predictions, average='weighted')
            f1 = f1_score(y_train, predictions, average='weighted')
            
            metrics = {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1)
            }
        
        logger.info(f"AutoKeras training completed. Metrics: {metrics}")
        
        return {
            'status': 'success',
            'platform': 'autokeras',
            'model': model,
            'metrics': metrics,
            'task': task
        }
        
    except ImportError:
        logger.warning("AutoKeras not installed. Install with: pip install autokeras")
        return {
            'status': 'error',
            'error': 'AutoKeras not available'
        }
    except Exception as e:
        logger.error(f"Error in AutoKeras training: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def train_with_tpot(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    task: str = 'regression',
    generations: int = 5,
    population_size: int = 20,
    cv: int = 5
) -> Dict[str, Any]:
    """
    Trajnon model duke përdorur TPOT (Tree-based Pipeline Optimization Tool).
    
    Args:
        X_train: Training features
        y_train: Training targets
        task: 'regression' ose 'classification'
        generations: Numri i generations për genetic algorithm
        population_size: Madhësia e population
        cv: Cross-validation folds
    
    Returns:
        Dict me model pipeline dhe performance metrics
    """
    try:
        from tpot import TPOTRegressor, TPOTClassifier
        
        # Initialize TPOT
        if task == 'regression':
            tpot = TPOTRegressor(
                generations=generations,
                population_size=population_size,
                cv=cv,
                random_state=42,
                verbosity=2,
                n_jobs=-1
            )
        else:
            tpot = TPOTClassifier(
                generations=generations,
                population_size=population_size,
                cv=cv,
                random_state=42,
                verbosity=2,
                n_jobs=-1
            )
        
        # Train model
        logger.info(f"Starting TPOT training with {generations} generations...")
        tpot.fit(X_train, y_train)
        
        # Evaluate model
        score = tpot.score(X_train, y_train)
        
        logger.info(f"TPOT training completed. Score: {score}")
        logger.info(f"Best pipeline: {tpot.fitted_pipeline_}")
        
        return {
            'status': 'success',
            'platform': 'tpot',
            'model': tpot.fitted_pipeline_,
            'pipeline_code': tpot.export(),
            'score': float(score),
            'task': task
        }
        
    except ImportError:
        logger.warning("TPOT not installed. Install with: pip install tpot")
        return {
            'status': 'error',
            'error': 'TPOT not available'
        }
    except Exception as e:
        logger.error(f"Error in TPOT training: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def train_with_automl(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    task: str = 'regression',
    platform: str = AUTOML_PLATFORM,
    **kwargs
) -> Dict[str, Any]:
    """
    Trajnon model duke përdorur AutoML platform të specifikuar.
    
    Args:
        X_train: Training features
        y_train: Training targets
        task: 'regression' ose 'classification'
        platform: 'autokeras', 'tpot', ose 'h2o'
        **kwargs: Additional parameters për platform specifik
    
    Returns:
        Dict me model dhe performance metrics
    """
    if not AUTOML_ENABLED:
        return {
            'status': 'error',
            'error': 'AutoML is disabled'
        }
    
    if platform == 'autokeras':
        return train_with_autokeras(X_train, y_train, task, **kwargs)
    elif platform == 'tpot':
        return train_with_tpot(X_train, y_train, task, **kwargs)
    elif platform == 'h2o':
        return train_with_h2o_automl(X_train, y_train, task, **kwargs)
    else:
        return {
            'status': 'error',
            'error': f'Unknown AutoML platform: {platform}'
        }

def train_with_h2o_automl(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    task: str = 'regression',
    max_models: int = 10,
    max_runtime_secs: int = 3600
) -> Dict[str, Any]:
    """
    Trajnon model duke përdorur H2O AutoML.
    
    Args:
        X_train: Training features
        y_train: Training targets
        task: 'regression' ose 'classification'
        max_models: Numri maksimal i modeleve
        max_runtime_secs: Koha maksimale e training (seconds)
    
    Returns:
        Dict me model dhe performance metrics
    """
    try:
        import h2o
        from h2o.automl import H2OAutoML
        
        # Initialize H2O
        h2o.init()
        
        # Convert to H2O Frame
        train_frame = h2o.H2OFrame(pd.concat([X_train, y_train], axis=1))
        
        # Identify target column
        target_col = y_train.name if hasattr(y_train, 'name') else 'target'
        
        # Initialize AutoML
        aml = H2OAutoML(
            max_models=max_models,
            max_runtime_secs=max_runtime_secs,
            seed=42
        )
        
        # Train
        logger.info(f"Starting H2O AutoML training...")
        aml.train(
            y=target_col,
            training_frame=train_frame
        )
        
        # Get best model
        best_model = aml.leader
        
        # Get performance
        performance = best_model.model_performance(train_frame)
        
        logger.info(f"H2O AutoML training completed. Best model: {best_model.model_id}")
        
        return {
            'status': 'success',
            'platform': 'h2o',
            'model': best_model,
            'model_id': best_model.model_id,
            'performance': {
                'mse': float(performance.mse()) if task == 'regression' else None,
                'rmse': float(performance.rmse()) if task == 'regression' else None,
                'mae': float(performance.mae()) if task == 'regression' else None,
                'r2': float(performance.r2()) if task == 'regression' else None
            },
            'task': task
        }
        
    except ImportError:
        logger.warning("H2O not installed. Install with: pip install h2o")
        return {
            'status': 'error',
            'error': 'H2O not available'
        }
    except Exception as e:
        logger.error(f"Error in H2O AutoML training: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

