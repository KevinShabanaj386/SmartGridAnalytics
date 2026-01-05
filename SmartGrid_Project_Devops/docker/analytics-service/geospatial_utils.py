"""
Utilities për Geospatial Analytics me PostGIS
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def create_spatial_index(conn):
    """Krijon spatial index për performancë më të mirë"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_data_location 
            ON sensor_data USING GIST (location);
        """)
        conn.commit()
        logger.info("Spatial index created successfully")
    except Exception as e:
        logger.error(f"Error creating spatial index: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Llogarit distancën në kilometra midis dy pikave duke përdorur Haversine formula
    """
    from math import radians, cos, sin, asin, sqrt
    
    # Konverto në radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Rrezja e Tokës në kilometra
    r = 6371
    
    return c * r

def find_sensors_in_polygon(conn, polygon_coords: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
    """
    Gjen të gjithë sensorët brenda një poligoni
    polygon_coords: Lista e tuples (lat, lon)
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Krijo PostGIS Polygon
    coords_str = ', '.join([f"{lon} {lat}" for lat, lon in polygon_coords])
    polygon_wkt = f"POLYGON(({coords_str}))"
    
    try:
        cursor.execute("""
            SELECT 
                sensor_id,
                sensor_type,
                value,
                latitude,
                longitude,
                timestamp
            FROM sensor_data
            WHERE location IS NOT NULL
            AND ST_Within(
                location,
                ST_SetSRID(ST_GeomFromText(%s), 4326)
            )
            AND timestamp >= NOW() - INTERVAL '24 hours'
        """, (polygon_wkt,))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error finding sensors in polygon: {str(e)}")
        return []
    finally:
        cursor.close()

def get_clustering_data(conn, k: int = 5) -> List[Dict[str, Any]]:
    """
    Kthen të dhëna për clustering të sensorëve duke përdorur K-Means me PostGIS
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Përdor ST_ClusterKMeans për clustering
        cursor.execute("""
            SELECT 
                ST_ClusterKMeans(location, %s) OVER() as cluster_id,
                sensor_id,
                sensor_type,
                value,
                latitude,
                longitude
            FROM sensor_data
            WHERE location IS NOT NULL
            AND timestamp >= NOW() - INTERVAL '24 hours'
            ORDER BY cluster_id
        """, (k,))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting clustering data: {str(e)}")
        return []
    finally:
        cursor.close()

def get_convex_hull(conn) -> Dict[str, Any]:
    """
    Kthen convex hull të të gjitha sensorëve (kufiri minimal)
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                ST_AsGeoJSON(ST_ConvexHull(ST_Collect(location))) as convex_hull_geojson,
                ST_Area(ST_ConvexHull(ST_Collect(location))::geography) / 1000000 as area_km2
            FROM sensor_data
            WHERE location IS NOT NULL
            AND timestamp >= NOW() - INTERVAL '24 hours'
        """)
        
        result = cursor.fetchone()
        if result:
            import json
            return {
                'convex_hull': json.loads(result['convex_hull_geojson']),
                'area_km2': float(result['area_km2'])
            }
        return {}
    except Exception as e:
        logger.error(f"Error getting convex hull: {str(e)}")
        return {}
    finally:
        cursor.close()

