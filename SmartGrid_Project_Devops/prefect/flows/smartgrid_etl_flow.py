"""
Prefect ETL/ELT Flow për Smart Grid Analytics
Alternative ETL/ELT solution me Prefect
"""
from prefect import flow, task
from prefect.tasks import task_inputs
from prefect.blocks.system import Secret
from prefect_sqlalchemy import SqlAlchemyConnector
from datetime import datetime, timedelta
import pandas as pd
import logging
import os
import sys

# Shto path për data-quality module
data_quality_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data-quality')
if data_quality_path not in sys.path:
    sys.path.insert(0, data_quality_path)

logger = logging.getLogger(__name__)

@task(name="extract_sensor_data", retries=3, retry_delay_seconds=60)
def extract_sensor_data(start_time: datetime = None, end_time: datetime = None) -> pd.DataFrame:
    """
    Extract task: Merr sensor data nga PostgreSQL
    
    Args:
        start_time: Data fillestare (default: 1 orë më parë)
        end_time: Data përfundimtare (default: tani)
    
    Returns:
        DataFrame me sensor data
    """
    import psycopg2
    
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(hours=1)
    
    logger.info(f"Extracting sensor data from {start_time} to {end_time}")
    
    # PostgreSQL connection
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
        'user': os.getenv('POSTGRES_USER', 'smartgrid'),
        'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
    }
    
    query = """
        SELECT 
            sensor_id,
            sensor_type,
            value,
            timestamp,
            latitude,
            longitude
        FROM sensor_data
        WHERE timestamp >= %s AND timestamp < %s
    """
    
    conn = psycopg2.connect(**db_config)
    try:
        df = pd.read_sql_query(query, conn, params=(start_time, end_time))
        logger.info(f"Extracted {len(df)} sensor records")
        return df
    finally:
        conn.close()

@task(name="extract_meter_readings", retries=3, retry_delay_seconds=60)
def extract_meter_readings(start_time: datetime = None, end_time: datetime = None) -> pd.DataFrame:
    """
    Extract task: Merr meter readings nga PostgreSQL
    
    Args:
        start_time: Data fillestare
        end_time: Data përfundimtare
    
    Returns:
        DataFrame me meter readings
    """
    import psycopg2
    
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(hours=1)
    
    logger.info(f"Extracting meter readings from {start_time} to {end_time}")
    
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
        'user': os.getenv('POSTGRES_USER', 'smartgrid'),
        'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
    }
    
    query = """
        SELECT 
            meter_id,
            customer_id,
            reading,
            unit,
            timestamp
        FROM meter_readings
        WHERE timestamp >= %s AND timestamp < %s
    """
    
    conn = psycopg2.connect(**db_config)
    try:
        df = pd.read_sql_query(query, conn, params=(start_time, end_time))
        logger.info(f"Extracted {len(df)} meter reading records")
        return df
    finally:
        conn.close()

@task(name="transform_sensor_data")
def transform_sensor_data(sensor_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform task: Transformon sensor data dhe aplikon rregulla cilësie
    
    Args:
        sensor_df: DataFrame me sensor data
    
    Returns:
        Transformed DataFrame
    """
    logger.info("Transforming sensor data...")
    
    if sensor_df.empty:
        logger.warning("No sensor data to transform")
        return sensor_df
    
    # Agregata për çdo orë
    sensor_df['timestamp'] = pd.to_datetime(sensor_df['timestamp'])
    sensor_df['hour_bucket'] = sensor_df['timestamp'].dt.floor('H')
    
    transformed_df = sensor_df.groupby(['hour_bucket', 'sensor_type', 'sensor_id']).agg({
        'value': ['mean', 'min', 'max', 'count', 'std']
    }).reset_index()
    
    # Flatten column names
    transformed_df.columns = [
        'hour_bucket', 'sensor_type', 'sensor_id',
        'avg_value', 'min_value', 'max_value', 'count', 'stddev_value'
    ]
    
    # Data quality scoring
    transformed_df['data_quality_score'] = transformed_df['count'].apply(
        lambda x: min(100, (x / 60) * 100)  # Score bazuar në numrin e leximit
    )
    
    logger.info(f"Transformed {len(transformed_df)} sensor records")
    return transformed_df

@task(name="transform_meter_readings")
def transform_meter_readings(meter_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform task: Transformon meter readings
    
    Args:
        meter_df: DataFrame me meter readings
    
    Returns:
        Transformed DataFrame
    """
    logger.info("Transforming meter readings...")
    
    if meter_df.empty:
        logger.warning("No meter readings to transform")
        return meter_df
    
    # Agregata për çdo ditë
    meter_df['timestamp'] = pd.to_datetime(meter_df['timestamp'])
    meter_df['day_bucket'] = meter_df['timestamp'].dt.floor('D')
    
    transformed_df = meter_df.groupby(['day_bucket', 'customer_id']).agg({
        'reading': ['sum', 'mean', 'count', 'min', 'max']
    }).reset_index()
    
    # Flatten column names
    transformed_df.columns = [
        'day_bucket', 'customer_id',
        'total_consumption', 'avg_consumption', 'reading_count', 'min_reading', 'max_reading'
    ]
    
    logger.info(f"Transformed {len(transformed_df)} meter reading records")
    return transformed_df

@task(name="validate_data_quality", retries=2)
def validate_data_quality(
    sensor_df: pd.DataFrame = None,
    meter_df: pd.DataFrame = None
) -> dict:
    """
    Validate task: Validon cilësinë e të dhënave me Great Expectations
    
    Args:
        sensor_df: Sensor data DataFrame
        meter_df: Meter readings DataFrame
    
    Returns:
        Dictionary me validation results
    """
    logger.info("Validating data quality with Great Expectations...")
    
    results = {}
    
    try:
        from great_expectations_helper import (
            validate_sensor_data_with_ge,
            validate_meter_readings_with_ge
        )
        
        # Validim për sensor data
        if sensor_df is not None and not sensor_df.empty:
            # Krijo temporary table ose përdor DataFrame direkt
            sensor_validation = validate_sensor_data_with_ge(
                query=None,  # Do të përdorim DataFrame direkt
                expectation_suite_name="sensor_data_suite"
            )
            results['sensor_validation'] = sensor_validation
            logger.info(f"Sensor data validation: {sensor_validation.get('data_quality_score', 0)}%")
        
        # Validim për meter readings
        if meter_df is not None and not meter_df.empty:
            meter_validation = validate_meter_readings_with_ge(
                query=None,
                expectation_suite_name="meter_readings_suite"
            )
            results['meter_validation'] = meter_validation
            logger.info(f"Meter readings validation: {meter_validation.get('data_quality_score', 0)}%")
        
        # Kontrollo nëse validimi ka dështuar
        if results.get('sensor_validation') and not results['sensor_validation'].get('success', False):
            raise ValueError(f"Sensor data validation failed: {results['sensor_validation'].get('statistics', {})}")
        
        if results.get('meter_validation') and not results['meter_validation'].get('success', False):
            raise ValueError(f"Meter readings validation failed: {results['meter_validation'].get('statistics', {})}")
        
        logger.info("✅ Data quality validation passed")
        return results
        
    except ImportError:
        logger.warning("Great Expectations not available, skipping validation")
        return {'success': True, 'note': 'Great Expectations not available'}
    except Exception as e:
        logger.error(f"Error in data quality validation: {str(e)}")
        raise

@task(name="load_to_warehouse")
def load_to_warehouse(
    sensor_aggregates: pd.DataFrame = None,
    meter_aggregates: pd.DataFrame = None
) -> dict:
    """
    Load task: Ngarkon të dhënat e transformuara në data warehouse
    
    Args:
        sensor_aggregates: Sensor aggregates DataFrame
        meter_aggregates: Meter aggregates DataFrame
    
    Returns:
        Dictionary me load results
    """
    import psycopg2
    from psycopg2.extras import execute_values
    
    logger.info("Loading data to warehouse...")
    
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
        'user': os.getenv('POSTGRES_USER', 'smartgrid'),
        'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
    }
    
    results = {}
    conn = psycopg2.connect(**db_config)
    
    try:
        cursor = conn.cursor()
        
        # Load sensor aggregates
        if sensor_aggregates is not None and not sensor_aggregates.empty:
            insert_query = """
                INSERT INTO sensor_aggregates 
                (sensor_id, sensor_type, avg_value, min_value, max_value, count, hour_bucket, data_quality_score)
                VALUES %s
                ON CONFLICT (sensor_id, sensor_type, hour_bucket) 
                DO UPDATE SET
                    avg_value = EXCLUDED.avg_value,
                    min_value = EXCLUDED.min_value,
                    max_value = EXCLUDED.max_value,
                    count = EXCLUDED.count,
                    data_quality_score = EXCLUDED.data_quality_score
            """
            
            values = [
                (
                    row['sensor_id'],
                    row['sensor_type'],
                    row['avg_value'],
                    row['min_value'],
                    row['max_value'],
                    row['count'],
                    row['hour_bucket'],
                    row.get('data_quality_score', 100)
                )
                for _, row in sensor_aggregates.iterrows()
            ]
            
            execute_values(cursor, insert_query, values)
            results['sensor_records_loaded'] = len(values)
            logger.info(f"Loaded {len(values)} sensor aggregate records")
        
        # Load meter aggregates
        if meter_aggregates is not None and not meter_aggregates.empty:
            insert_query = """
                INSERT INTO consumption_aggregates 
                (customer_id, total_consumption, avg_consumption, reading_count, day_bucket, min_reading, max_reading)
                VALUES %s
                ON CONFLICT (customer_id, day_bucket) 
                DO UPDATE SET
                    total_consumption = EXCLUDED.total_consumption,
                    avg_consumption = EXCLUDED.avg_consumption,
                    reading_count = EXCLUDED.reading_count,
                    min_reading = EXCLUDED.min_reading,
                    max_reading = EXCLUDED.max_reading
            """
            
            values = [
                (
                    row['customer_id'],
                    row['total_consumption'],
                    row['avg_consumption'],
                    row['reading_count'],
                    row['day_bucket'],
                    row.get('min_reading', 0),
                    row.get('max_reading', 0)
                )
                for _, row in meter_aggregates.iterrows()
            ]
            
            execute_values(cursor, insert_query, values)
            results['meter_records_loaded'] = len(values)
            logger.info(f"Loaded {len(values)} meter aggregate records")
        
        conn.commit()
        logger.info("✅ Data loaded to warehouse successfully")
        return results
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading data to warehouse: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

@task(name="cleanup_old_data")
def cleanup_old_data(days_to_keep: int = 90) -> dict:
    """
    Cleanup task: Fshin të dhëna të vjetra
    
    Args:
        days_to_keep: Numri i ditëve për të mbajtur të dhënat (default: 90)
    
    Returns:
        Dictionary me cleanup results
    """
    import psycopg2
    
    logger.info(f"Cleaning up data older than {days_to_keep} days...")
    
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
        'user': os.getenv('POSTGRES_USER', 'smartgrid'),
        'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
    }
    
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # Cleanup sensor_data
        cursor.execute("""
            DELETE FROM sensor_data 
            WHERE timestamp < NOW() - INTERVAL '%s days'
        """, (days_to_keep,))
        sensor_deleted = cursor.rowcount
        
        # Cleanup meter_readings
        cursor.execute("""
            DELETE FROM meter_readings 
            WHERE timestamp < NOW() - INTERVAL '%s days'
        """, (days_to_keep,))
        meter_deleted = cursor.rowcount
        
        conn.commit()
        
        results = {
            'sensor_records_deleted': sensor_deleted,
            'meter_records_deleted': meter_deleted
        }
        
        logger.info(f"✅ Cleanup completed: {sensor_deleted} sensor records, {meter_deleted} meter records deleted")
        return results
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in cleanup: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

@flow(name="smartgrid_etl_flow", log_prints=True)
def smartgrid_etl_flow(
    start_time: datetime = None,
    end_time: datetime = None,
    enable_validation: bool = True,
    enable_cleanup: bool = True
):
    """
    Main ETL Flow për Smart Grid Analytics me Prefect
    
    Args:
        start_time: Data fillestare për processing
        end_time: Data përfundimtare për processing
        enable_validation: Nëse duhet të ekzekutojë validation
        enable_cleanup: Nëse duhet të ekzekutojë cleanup
    """
    logger.info("Starting Smart Grid ETL Flow with Prefect...")
    
    # Extract
    sensor_df = extract_sensor_data(start_time=start_time, end_time=end_time)
    meter_df = extract_meter_readings(start_time=start_time, end_time=end_time)
    
    # Transform
    sensor_aggregates = transform_sensor_data(sensor_df)
    meter_aggregates = transform_meter_readings(meter_df)
    
    # Validate (opsionale)
    if enable_validation:
        validation_results = validate_data_quality(
            sensor_df=sensor_df,
            meter_df=meter_df
        )
        logger.info(f"Validation results: {validation_results}")
    
    # Load
    load_results = load_to_warehouse(
        sensor_aggregates=sensor_aggregates,
        meter_aggregates=meter_aggregates
    )
    
    # Cleanup (opsionale)
    if enable_cleanup:
        cleanup_results = cleanup_old_data(days_to_keep=90)
        logger.info(f"Cleanup results: {cleanup_results}")
    
    logger.info("✅ Smart Grid ETL Flow completed successfully")
    
    return {
        'extract': {
            'sensor_records': len(sensor_df),
            'meter_records': len(meter_df)
        },
        'transform': {
            'sensor_aggregates': len(sensor_aggregates),
            'meter_aggregates': len(meter_aggregates)
        },
        'load': load_results,
        'validation': validation_results if enable_validation else None,
        'cleanup': cleanup_results if enable_cleanup else None
    }

if __name__ == "__main__":
    # Run flow lokal
    result = smartgrid_etl_flow()
    print(f"Flow completed: {result}")

