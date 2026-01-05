"""
Data Quality Validation me Great Expectations
Kjo skript validon cilësinë e të dhënave të Smart Grid
"""
import great_expectations as ge
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.datasource.fluent import Datasource
import psycopg2
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurimi i PostgreSQL
DB_CONFIG = {
    'host': 'smartgrid-postgres',
    'port': '5432',
    'database': 'smartgrid_db',
    'user': 'smartgrid',
    'password': 'smartgrid123'
}

def get_data_from_postgres(query: str) -> pd.DataFrame:
    """Merr të dhëna nga PostgreSQL dhe i konverton në DataFrame"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

def validate_sensor_data():
    """Validon të dhënat e sensorëve"""
    logger.info("Starting sensor data validation...")
    
    # Merr të dhënat
    query = """
        SELECT 
            sensor_id,
            sensor_type,
            value,
            timestamp,
            latitude,
            longitude
        FROM sensor_data
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
        LIMIT 10000
    """
    
    df = get_data_from_postgres(query)
    
    if df.empty:
        logger.warning("No data to validate")
        return
    
    # Krijon Great Expectations context
    context = ge.get_context()
    
    # Rregulla të validimit
    expectations = []
    
    # 1. Kontrollo që sensor_id nuk është null
    expectations.append({
        'expectation_type': 'expect_column_values_to_not_be_null',
        'kwargs': {'column': 'sensor_id'}
    })
    
    # 2. Kontrollo që sensor_type është në listën e pritur
    expectations.append({
        'expectation_type': 'expect_column_values_to_be_in_set',
        'kwargs': {
            'column': 'sensor_type',
            'value_set': ['voltage', 'current', 'power', 'frequency']
        }
    })
    
    # 3. Kontrollo që value është pozitive
    expectations.append({
        'expectation_type': 'expect_column_values_to_be_between',
        'kwargs': {
            'column': 'value',
            'min_value': 0,
            'max_value': 10000
        }
    })
    
    # 4. Kontrollo që voltage është në rangun e pritur (100-400V)
    voltage_df = df[df['sensor_type'] == 'voltage']
    if not voltage_df.empty:
        expectations.append({
            'expectation_type': 'expect_column_values_to_be_between',
            'kwargs': {
                'column': 'value',
                'min_value': 100,
                'max_value': 400,
                'condition': 'sensor_type == "voltage"'
            }
        })
    
    # 5. Kontrollo që timestamp nuk është në të ardhmen
    expectations.append({
        'expectation_type': 'expect_column_values_to_be_between',
        'kwargs': {
            'column': 'timestamp',
            'min_value': pd.Timestamp.now() - pd.Timedelta(days=365),
            'max_value': pd.Timestamp.now()
        }
    })
    
    # 6. Kontrollo që latitude dhe longitude janë në rangun e pritur
    if 'latitude' in df.columns:
        expectations.append({
            'expectation_type': 'expect_column_values_to_be_between',
            'kwargs': {
                'column': 'latitude',
                'min_value': -90,
                'max_value': 90
            }
        })
    
    if 'longitude' in df.columns:
        expectations.append({
            'expectation_type': 'expect_column_values_to_be_between',
            'kwargs': {
                'column': 'longitude',
                'min_value': -180,
                'max_value': 180
            }
        })
    
    # Ekzekuto validimin
    validation_results = []
    for expectation in expectations:
        try:
            result = ge.dataset.PandasDataset(df).expectation(**expectation['kwargs'])
            validation_results.append({
                'expectation': expectation['expectation_type'],
                'success': result['success'],
                'result': result
            })
        except Exception as e:
            logger.error(f"Error validating {expectation['expectation_type']}: {str(e)}")
            validation_results.append({
                'expectation': expectation['expectation_type'],
                'success': False,
                'error': str(e)
            })
    
    # Raporto rezultatet
    success_count = sum(1 for r in validation_results if r['success'])
    total_count = len(validation_results)
    
    logger.info(f"Validation completed: {success_count}/{total_count} expectations passed")
    
    for result in validation_results:
        if not result['success']:
            logger.warning(f"Failed expectation: {result['expectation']}")
    
    return {
        'success': success_count == total_count,
        'results': validation_results,
        'data_quality_score': (success_count / total_count) * 100 if total_count > 0 else 0
    }

def validate_meter_readings():
    """Validon leximet e matësve"""
    logger.info("Starting meter readings validation...")
    
    query = """
        SELECT 
            meter_id,
            customer_id,
            reading,
            unit,
            timestamp
        FROM meter_readings
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
        LIMIT 10000
    """
    
    df = get_data_from_postgres(query)
    
    if df.empty:
        logger.warning("No meter readings to validate")
        return
    
    # Rregulla të validimit
    expectations = []
    
    # 1. Kontrollo që reading është pozitive
    expectations.append({
        'expectation_type': 'expect_column_values_to_be_between',
        'kwargs': {
            'column': 'reading',
            'min_value': 0,
            'max_value': 1000000  # 1M kWh
        }
    })
    
    # 2. Kontrollo që unit është 'kWh'
    expectations.append({
        'expectation_type': 'expect_column_values_to_be_in_set',
        'kwargs': {
            'column': 'unit',
            'value_set': ['kWh']
        }
    })
    
    # Ekzekuto validimin
    validation_results = []
    for expectation in expectations:
        try:
            result = ge.dataset.PandasDataset(df).expectation(**expectation['kwargs'])
            validation_results.append({
                'expectation': expectation['expectation_type'],
                'success': result['success']
            })
        except Exception as e:
            logger.error(f"Error: {str(e)}")
    
    success_count = sum(1 for r in validation_results if r['success'])
    total_count = len(validation_results)
    
    logger.info(f"Meter readings validation: {success_count}/{total_count} passed")
    
    return {
        'success': success_count == total_count,
        'results': validation_results
    }

if __name__ == '__main__':
    logger.info("Starting data quality validation...")
    
    sensor_results = validate_sensor_data()
    meter_results = validate_meter_readings()
    
    if sensor_results and sensor_results['success'] and meter_results and meter_results['success']:
        logger.info("✅ All data quality checks passed!")
    else:
        logger.error("❌ Some data quality checks failed!")
        exit(1)

