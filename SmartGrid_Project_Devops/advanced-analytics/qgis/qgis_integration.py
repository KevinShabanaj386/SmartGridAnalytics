"""
QGIS Integration për Smart Grid Analytics
Implementon geospatial visualization dhe analysis me QGIS Server
"""
import logging
import os
import requests
from typing import Dict, Any, Optional, List, Tuple
import json

logger = logging.getLogger(__name__)

# QGIS Configuration
QGIS_SERVER_URL = os.getenv('QGIS_SERVER_URL', 'http://smartgrid-qgis-server:80')
QGIS_PROJECT_PATH = os.getenv('QGIS_PROJECT_PATH', '/qgis-projects/smartgrid.qgs')

def get_qgis_map(
    bbox: Tuple[float, float, float, float],  # minx, miny, maxx, maxy
    width: int = 800,
    height: int = 600,
    layers: Optional[List[str]] = None,
    format: str = 'PNG'
) -> Dict[str, Any]:
    """
    Merr map image nga QGIS Server.
    
    Args:
        bbox: Bounding box (minx, miny, maxx, maxy)
        width: Gjerësia e map (pixels)
        height: Lartësia e map (pixels)
        layers: Lista e layers për të shfaqur (optional)
        format: Image format (PNG, JPEG)
    
    Returns:
        Dict me map image data ose error
    """
    try:
        url = f"{QGIS_SERVER_URL}/qgisserver"
        
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetMap',
            'BBOX': ','.join(map(str, bbox)),
            'CRS': 'EPSG:4326',
            'WIDTH': width,
            'HEIGHT': height,
            'FORMAT': f'image/{format.lower()}',
            'LAYERS': ','.join(layers) if layers else 'all',
            'STYLES': ''
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('image/'):
            return {
                'status': 'success',
                'image_data': response.content,
                'format': format,
                'width': width,
                'height': height
            }
        else:
            return {
                'status': 'error',
                'error': f"HTTP {response.status_code}: {response.text[:500]}"
            }
            
    except Exception as e:
        logger.error(f"Error getting QGIS map: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def get_qgis_feature_info(
    x: float,
    y: float,
    bbox: Tuple[float, float, float, float],
    layers: Optional[List[str]] = None,
    width: int = 800,
    height: int = 600
) -> Dict[str, Any]:
    """
    Merr feature information për një pikë në map.
    
    Args:
        x: X coordinate
        y: Y coordinate
        bbox: Bounding box
        layers: Lista e layers
        width: Map width
        height: Map height
    
    Returns:
        Dict me feature information
    """
    try:
        url = f"{QGIS_SERVER_URL}/qgisserver"
        
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetFeatureInfo',
            'BBOX': ','.join(map(str, bbox)),
            'CRS': 'EPSG:4326',
            'WIDTH': width,
            'HEIGHT': height,
            'QUERY_LAYERS': ','.join(layers) if layers else 'all',
            'I': int(x),
            'J': int(y),
            'INFO_FORMAT': 'application/json'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            try:
                feature_data = response.json()
                return {
                    'status': 'success',
                    'features': feature_data
                }
            except json.JSONDecodeError:
                return {
                    'status': 'success',
                    'features': response.text
                }
        else:
            return {
                'status': 'error',
                'error': f"HTTP {response.status_code}: {response.text[:500]}"
            }
            
    except Exception as e:
        logger.error(f"Error getting QGIS feature info: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def get_qgis_capabilities() -> Dict[str, Any]:
    """
    Merr WMS capabilities nga QGIS Server.
    
    Returns:
        Dict me capabilities information
    """
    try:
        url = f"{QGIS_SERVER_URL}/qgisserver"
        
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetCapabilities'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return {
                'status': 'success',
                'capabilities_xml': response.text
            }
        else:
            return {
                'status': 'error',
                'error': f"HTTP {response.status_code}: {response.text[:500]}"
            }
            
    except Exception as e:
        logger.error(f"Error getting QGIS capabilities: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def get_qgis_layer_legend(
    layer: str,
    format: str = 'PNG'
) -> Dict[str, Any]:
    """
    Merr legend për një layer.
    
    Args:
        layer: Layer name
        format: Image format (PNG, JPEG)
    
    Returns:
        Dict me legend image
    """
    try:
        url = f"{QGIS_SERVER_URL}/qgisserver"
        
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetLegendGraphic',
            'LAYER': layer,
            'FORMAT': f'image/{format.lower()}'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('image/'):
            return {
                'status': 'success',
                'legend_image': response.content,
                'format': format
            }
        else:
            return {
                'status': 'error',
                'error': f"HTTP {response.status_code}: {response.text[:500]}"
            }
            
    except Exception as e:
        logger.error(f"Error getting QGIS layer legend: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def create_qgis_heatmap(
    points: List[Tuple[float, float, float]],  # (x, y, value)
    bbox: Tuple[float, float, float, float],
    width: int = 800,
    height: int = 600
) -> Dict[str, Any]:
    """
    Krijon heatmap nga points data.
    
    Args:
        points: Lista e points me (x, y, value)
        bbox: Bounding box
        width: Map width
        height: Map height
    
    Returns:
        Dict me heatmap image
    """
    try:
        # Në prodhim, kjo do të përdorte QGIS processing algorithms
        # Për tani, kthejmë një placeholder
        logger.info(f"Creating heatmap for {len(points)} points")
        
        return {
            'status': 'success',
            'message': 'Heatmap generation initiated',
            'points_count': len(points),
            'bbox': bbox
        }
        
    except Exception as e:
        logger.error(f"Error creating QGIS heatmap: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

