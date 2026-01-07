"""
TensorFlow Serving Client për Smart Grid Analytics
Përdoret për të dërguar requests në TensorFlow Serving server
"""
import requests
import json
import logging
from typing import Dict, List, Any, Optional
import os

logger = logging.getLogger(__name__)

# TensorFlow Serving configuration
TENSORFLOW_SERVING_URL = os.getenv(
    'TENSORFLOW_SERVING_URL',
    'http://smartgrid-tensorflow-serving:8501'
)
MODEL_NAME = os.getenv('TENSORFLOW_MODEL_NAME', 'smartgrid-load-forecasting')
MODEL_VERSION = os.getenv('TENSORFLOW_MODEL_VERSION', '1')

def predict_with_tf_serving(
    instances: List[List[float]],
    model_name: str = MODEL_NAME,
    version: Optional[int] = None
) -> Dict[str, Any]:
    """
    Bën prediction duke përdorur TensorFlow Serving REST API.
    
    Args:
        instances: Lista e input instances (features)
        model_name: Emri i modelit
        version: Version i modelit (optional, përdor latest nëse nuk specifikohet)
    
    Returns:
        Dict me predictions
    """
    try:
        # Build URL
        if version:
            url = f"{TENSORFLOW_SERVING_URL}/v1/models/{model_name}/versions/{version}:predict"
        else:
            url = f"{TENSORFLOW_SERVING_URL}/v1/models/{model_name}:predict"
        
        # Prepare request body
        payload = {
            "instances": instances
        }
        
        # Send request
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Successfully got predictions from TensorFlow Serving")
            return {
                'status': 'success',
                'predictions': result.get('predictions', []),
                'model_name': model_name,
                'version': version or 'latest'
            }
        else:
            logger.error(f"TensorFlow Serving error: {response.status_code} - {response.text}")
            return {
                'status': 'error',
                'error': f"HTTP {response.status_code}: {response.text}"
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to TensorFlow Serving: {str(e)}")
        return {
            'status': 'error',
            'error': f"Connection error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error in TensorFlow Serving client: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def get_model_status(model_name: str = MODEL_NAME) -> Dict[str, Any]:
    """
    Merr status të modelit nga TensorFlow Serving.
    
    Args:
        model_name: Emri i modelit
    
    Returns:
        Dict me model status
    """
    try:
        url = f"{TENSORFLOW_SERVING_URL}/v1/models/{model_name}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            return {
                'status': 'success',
                'model_info': response.json()
            }
        else:
            return {
                'status': 'error',
                'error': f"HTTP {response.status_code}: {response.text}"
            }
    except Exception as e:
        logger.error(f"Error getting model status: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def list_models() -> Dict[str, Any]:
    """
    Liston të gjitha modelet e disponueshme në TensorFlow Serving.
    
    Returns:
        Dict me lista të modeleve
    """
    try:
        url = f"{TENSORFLOW_SERVING_URL}/v1/models"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            return {
                'status': 'success',
                'models': response.json()
            }
        else:
            return {
                'status': 'error',
                'error': f"HTTP {response.status_code}: {response.text}"
            }
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

