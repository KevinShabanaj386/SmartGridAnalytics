"""
ETL Pipeline për Smart Grid Analytics me Apache Airflow
Kjo DAG përpunon të dhënat nga PostgreSQL dhe i eksporton për analizë
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import logging

logger = logging.getLogger(__name__)

# Konfigurimi i DAG
default_args = {
    'owner': 'smartgrid-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'smartgrid_etl_pipeline',
    default_args=default_args,
    description='ETL Pipeline për të dhënat e Smart Grid',
    schedule_interval=timedelta(hours=1),  # Ekzekutohet çdo orë
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['smartgrid', 'etl', 'data-processing'],
)

def extract_sensor_data(**context):
    """Ekstrakton të dhënat e sensorëve për orën e fundit"""
    postgres_hook = PostgresHook(postgres_conn_id='smartgrid_postgres')
    
    query = """
        SELECT 
            sensor_id,
            sensor_type,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value,
            COUNT(*) as count,
            DATE_TRUNC('hour', timestamp) as hour_bucket
        FROM sensor_data
        WHERE timestamp >= NOW() - INTERVAL '1 hour'
        GROUP BY sensor_id, sensor_type, DATE_TRUNC('hour', timestamp)
    """
    
    results = postgres_hook.get_records(query)
    logger.info(f"Extracted {len(results)} sensor data records")
    
    # Ruaj rezultatet në XCom për task-in tjetër
    context['ti'].xcom_push(key='sensor_data', value=results)
    return results

def transform_data(**context):
    """Transformon të dhënat dhe aplikon rregulla të cilësisë"""
    sensor_data = context['ti'].xcom_pull(key='sensor_data', task_ids='extract_sensor_data')
    
    transformed_data = []
    for record in sensor_data:
        sensor_id, sensor_type, avg_value, min_value, max_value, count, hour_bucket = record
        
        # Rregulla të cilësisë
        if avg_value is None or avg_value < 0:
            logger.warning(f"Invalid data for sensor {sensor_id}: avg_value={avg_value}")
            continue
        
        if count < 1:
            logger.warning(f"Insufficient data for sensor {sensor_id}: count={count}")
            continue
        
        # Normalizim i të dhënave
        normalized_record = {
            'sensor_id': sensor_id,
            'sensor_type': sensor_type,
            'avg_value': float(avg_value),
            'min_value': float(min_value),
            'max_value': float(max_value),
            'count': int(count),
            'hour_bucket': hour_bucket.isoformat() if hasattr(hour_bucket, 'isoformat') else str(hour_bucket),
            'data_quality_score': min(100, (count / 60) * 100)  # Score bazuar në numrin e leximit
        }
        
        transformed_data.append(normalized_record)
    
    logger.info(f"Transformed {len(transformed_data)} records")
    context['ti'].xcom_push(key='transformed_data', value=transformed_data)
    return transformed_data

def load_to_warehouse(**context):
    """Ngarkon të dhënat e transformuara në data warehouse (tabela agregates)"""
    postgres_hook = PostgresHook(postgres_conn_id='smartgrid_postgres')
    transformed_data = context['ti'].xcom_pull(key='transformed_data', task_ids='transform_data')
    
    if not transformed_data:
        logger.warning("No transformed data to load")
        return
    
    # Ngarko në tabelën e agregatave
    for record in transformed_data:
        insert_query = """
            INSERT INTO sensor_aggregates 
            (sensor_id, sensor_type, avg_value, min_value, max_value, count, hour_bucket)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (sensor_id, sensor_type, hour_bucket) 
            DO UPDATE SET
                avg_value = EXCLUDED.avg_value,
                min_value = EXCLUDED.min_value,
                max_value = EXCLUDED.max_value,
                count = EXCLUDED.count
        """
        
        postgres_hook.run(
            insert_query,
            parameters=(
                record['sensor_id'],
                record['sensor_type'],
                record['avg_value'],
                record['min_value'],
                record['max_value'],
                record['count'],
                record['hour_bucket']
            )
        )
    
    logger.info(f"Loaded {len(transformed_data)} records to warehouse")

def validate_data_quality(**context):
    """Validon cilësinë e të dhënave me Great Expectations (100% INTEGRIM)"""
    try:
        # Import Great Expectations helper
        import sys
        import os
        # Shto path për data-quality module
        data_quality_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data-quality')
        if data_quality_path not in sys.path:
            sys.path.insert(0, data_quality_path)
        
        from great_expectations_helper import (
            validate_sensor_data_with_ge,
            validate_meter_readings_with_ge,
            generate_data_docs
        )
        
        # Merr PostgreSQL connection nga Airflow connection
        postgres_hook = PostgresHook(postgres_conn_id='smartgrid_postgres')
        conn = postgres_hook.get_conn()
        db_config = {
            'host': conn.info.host,
            'port': str(conn.info.port),
            'database': conn.info.dbname,
            'user': conn.info.user,
            'password': conn.info.password
        }
        conn.close()
        
        # Validim për sensor data
        logger.info("Validating sensor data with Great Expectations...")
        sensor_validation = validate_sensor_data_with_ge(
            query="""
                SELECT 
                    sensor_id,
                    sensor_type,
                    value,
                    timestamp,
                    latitude,
                    longitude
                FROM sensor_data
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
            """,
            expectation_suite_name="sensor_data_suite",
            **db_config
        )
        
        # Validim për meter readings
        logger.info("Validating meter readings with Great Expectations...")
        meter_validation = validate_meter_readings_with_ge(
            query="""
                SELECT 
                    meter_id,
                    customer_id,
                    reading,
                    unit,
                    timestamp
                FROM meter_readings
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
            """,
            expectation_suite_name="meter_readings_suite",
            **db_config
        )
        
        # Gjenero Data Docs
        sensor_docs_path = generate_data_docs(sensor_validation, output_dir="/tmp/ge_data_docs/sensor")
        meter_docs_path = generate_data_docs(meter_validation, output_dir="/tmp/ge_data_docs/meter")
        
        # Ruaj rezultatet në XCom
        context['ti'].xcom_push(key='sensor_validation', value=sensor_validation)
        context['ti'].xcom_push(key='meter_validation', value=meter_validation)
        context['ti'].xcom_push(key='sensor_docs_path', value=sensor_docs_path)
        context['ti'].xcom_push(key='meter_docs_path', value=meter_docs_path)
        
        # Kontrollo nëse validimi ka dështuar
        if not sensor_validation.get('success', False):
            logger.error(f"Sensor data validation failed: {sensor_validation.get('statistics', {})}")
            raise ValueError(f"Sensor data validation failed: {sensor_validation.get('statistics', {}).get('unsuccessful_expectations', 0)} expectations failed")
        
        if not meter_validation.get('success', False):
            logger.error(f"Meter readings validation failed: {meter_validation.get('statistics', {})}")
            raise ValueError(f"Meter readings validation failed: {meter_validation.get('statistics', {}).get('unsuccessful_expectations', 0)} expectations failed")
        
        logger.info("✅ Data quality validation passed with Great Expectations")
        logger.info(f"Sensor data quality score: {sensor_validation.get('data_quality_score', 0)}%")
        logger.info(f"Meter readings quality score: {meter_validation.get('data_quality_score', 0)}%")
        
        return {
            'success': True,
            'sensor_validation': sensor_validation,
            'meter_validation': meter_validation,
            'sensor_docs_path': sensor_docs_path,
            'meter_docs_path': meter_docs_path
        }
        
    except ImportError as e:
        logger.warning(f"Great Expectations not available, falling back to simple validation: {e}")
        # Fallback në validim të thjeshtë
        transformed_data = context['ti'].xcom_pull(key='transformed_data', task_ids='transform_data')
        
        if not transformed_data:
            raise ValueError("No data to validate")
        
        validation_errors = []
        for record in transformed_data:
            if record['sensor_type'] == 'voltage':
                if record['avg_value'] < 100 or record['avg_value'] > 400:
                    validation_errors.append(f"Voltage out of range: {record['avg_value']}V")
            elif record['sensor_type'] == 'current':
                if record['avg_value'] < 0 or record['avg_value'] > 1000:
                    validation_errors.append(f"Current out of range: {record['avg_value']}A")
            elif record['sensor_type'] == 'power':
                if record['avg_value'] < 0:
                    validation_errors.append(f"Power cannot be negative: {record['avg_value']}W")
        
        if validation_errors:
            logger.error(f"Data quality validation failed: {validation_errors}")
            raise ValueError(f"Data quality validation failed: {len(validation_errors)} errors")
        
        logger.info("Data quality validation passed (simple validation)")
        return True
        
    except Exception as e:
        logger.error(f"Error in data quality validation: {str(e)}")
        raise

# Task-et e DAG
extract_task = PythonOperator(
    task_id='extract_sensor_data',
    python_callable=extract_sensor_data,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_data_quality',
    python_callable=validate_data_quality,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_to_warehouse',
    python_callable=load_to_warehouse,
    dag=dag,
)

# Task për cleanup të të dhënave të vjetra
cleanup_task = PostgresOperator(
    task_id='cleanup_old_data',
    postgres_conn_id='smartgrid_postgres',
    sql="""
        DELETE FROM sensor_data 
        WHERE timestamp < NOW() - INTERVAL '90 days';
        
        DELETE FROM meter_readings 
        WHERE timestamp < NOW() - INTERVAL '90 days';
    """,
    dag=dag,
)

# Definimi i dependencies
extract_task >> transform_task >> validate_task >> load_task
load_task >> cleanup_task

