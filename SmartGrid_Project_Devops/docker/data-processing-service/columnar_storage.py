"""
Columnar Storage Formats (Parquet/ORC) për Fast Analytical Queries
Përdoret për historical data dhe analytics workloads
"""
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

# Configuration
STORAGE_FORMAT = os.getenv('COLUMNAR_STORAGE_FORMAT', 'parquet')  # 'parquet' ose 'orc'
STORAGE_PATH = os.getenv('COLUMNAR_STORAGE_PATH', '/data/columnar')
USE_COLUMNAR_STORAGE = os.getenv('USE_COLUMNAR_STORAGE', 'true').lower() == 'true'

def init_columnar_storage():
    """Inicializon columnar storage directory"""
    if not USE_COLUMNAR_STORAGE:
        return False
    
    try:
        os.makedirs(STORAGE_PATH, exist_ok=True)
        logger.info(f"Columnar storage initialized: {STORAGE_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error initializing columnar storage: {e}")
        return False

def save_to_parquet(
    df: pd.DataFrame,
    table_name: str,
    partition_by: Optional[str] = None,
    compression: str = 'snappy'
) -> str:
    """
    Ruaj DataFrame në Parquet format
    
    Args:
        df: DataFrame për të ruajtur
        table_name: Emri i tabelës
        partition_by: Column për partitioning (opsionale)
        compression: Compression algorithm (snappy, gzip, brotli)
    
    Returns:
        Path për file të ruajtur
    """
    if not USE_COLUMNAR_STORAGE:
        return None
    
    try:
        table_path = os.path.join(STORAGE_PATH, table_name)
        
        if partition_by and partition_by in df.columns:
            # Partitioned write
            df.to_parquet(
                table_path,
                partition_cols=[partition_by],
                compression=compression,
                engine='pyarrow',
                index=False
            )
        else:
            # Simple write
            file_path = os.path.join(table_path, f"{table_name}_{datetime.now().strftime('%Y%m%d')}.parquet")
            os.makedirs(table_path, exist_ok=True)
            df.to_parquet(
                file_path,
                compression=compression,
                engine='pyarrow',
                index=False
            )
        
        logger.info(f"Saved to Parquet: {table_path}")
        return table_path
        
    except ImportError:
        logger.warning("pyarrow not installed. Parquet storage disabled.")
        return None
    except Exception as e:
        logger.error(f"Error saving to Parquet: {e}")
        return None

def save_to_orc(
    df: pd.DataFrame,
    table_name: str,
    partition_by: Optional[str] = None,
    compression: str = 'snappy'
) -> str:
    """
    Ruaj DataFrame në ORC format
    
    Args:
        df: DataFrame për të ruajtur
        table_name: Emri i tabelës
        partition_by: Column për partitioning (opsionale)
        compression: Compression algorithm (snappy, zlib, lzo)
    
    Returns:
        Path për file të ruajtur
    """
    if not USE_COLUMNAR_STORAGE:
        return None
    
    try:
        table_path = os.path.join(STORAGE_PATH, table_name)
        
        if partition_by and partition_by in df.columns:
            # Partitioned write
            df.to_orc(
                table_path,
                partition_cols=[partition_by],
                compression=compression,
                index=False
            )
        else:
            # Simple write
            file_path = os.path.join(table_path, f"{table_name}_{datetime.now().strftime('%Y%m%d')}.orc")
            os.makedirs(table_path, exist_ok=True)
            df.to_orc(
                file_path,
                compression=compression,
                index=False
            )
        
        logger.info(f"Saved to ORC: {table_path}")
        return table_path
        
    except ImportError:
        logger.warning("pyarrow not installed. ORC storage disabled.")
        return None
    except Exception as e:
        logger.error(f"Error saving to ORC: {e}")
        return None

def read_from_parquet(
    table_name: str,
    filters: Optional[List[tuple]] = None,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Lexo të dhëna nga Parquet format
    
    Args:
        table_name: Emri i tabelës
        filters: Filters për pushdown (opsionale)
        columns: Columns për të lexuar (opsionale)
    
    Returns:
        DataFrame me të dhënat
    """
    if not USE_COLUMNAR_STORAGE:
        return pd.DataFrame()
    
    try:
        table_path = os.path.join(STORAGE_PATH, table_name)
        
        df = pd.read_parquet(
            table_path,
            filters=filters,
            columns=columns,
            engine='pyarrow'
        )
        
        logger.debug(f"Read from Parquet: {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Error reading from Parquet: {e}")
        return pd.DataFrame()

def read_from_orc(
    table_name: str,
    filters: Optional[List[tuple]] = None,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Lexo të dhëna nga ORC format
    
    Args:
        table_name: Emri i tabelës
        filters: Filters për pushdown (opsionale)
        columns: Columns për të lexuar (opsionale)
    
    Returns:
        DataFrame me të dhënat
    """
    if not USE_COLUMNAR_STORAGE:
        return pd.DataFrame()
    
    try:
        table_path = os.path.join(STORAGE_PATH, table_name)
        
        df = pd.read_orc(
            table_path,
            filters=filters,
            columns=columns
        )
        
        logger.debug(f"Read from ORC: {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Error reading from ORC: {e}")
        return pd.DataFrame()

def save_sensor_data_columnar(
    df: pd.DataFrame,
    format: str = None
) -> str:
    """
    Ruaj sensor data në columnar format
    
    Args:
        df: DataFrame me sensor data
        format: Storage format ('parquet' ose 'orc')
    
    Returns:
        Path për file të ruajtur
    """
    format = format or STORAGE_FORMAT
    
    if format == 'parquet':
        return save_to_parquet(df, 'sensor_data', partition_by='sensor_type')
    elif format == 'orc':
        return save_to_orc(df, 'sensor_data', partition_by='sensor_type')
    else:
        logger.error(f"Unsupported storage format: {format}")
        return None

def save_meter_readings_columnar(
    df: pd.DataFrame,
    format: str = None
) -> str:
    """
    Ruaj meter readings në columnar format
    
    Args:
        df: DataFrame me meter readings
        format: Storage format ('parquet' ose 'orc')
    
    Returns:
        Path për file të ruajtur
    """
    format = format or STORAGE_FORMAT
    
    if format == 'parquet':
        return save_to_parquet(df, 'meter_readings', partition_by='customer_id')
    elif format == 'orc':
        return save_to_orc(df, 'meter_readings', partition_by='customer_id')
    else:
        logger.error(f"Unsupported storage format: {format}")
        return None

# Initialize columnar storage
init_columnar_storage()

