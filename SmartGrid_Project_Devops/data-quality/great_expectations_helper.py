"""
Great Expectations Helper për Airflow Integration
Kjo modul përdoret për të integruar Great Expectations në Airflow DAG
"""
import great_expectations as ge
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.datasource.fluent import Datasource
from great_expectations.checkpoint import SimpleCheckpoint
import pandas as pd
import psycopg2
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Great Expectations root directory
GE_ROOT_DIR = os.path.join(os.path.dirname(__file__), "great_expectations")

def get_ge_context():
    """Merr Great Expectations context"""
    try:
        context = ge.get_context(project_root_dir=GE_ROOT_DIR)
        return context
    except Exception as e:
        logger.warning(f"Could not get GE context, creating new one: {e}")
        # Krijo context nëse nuk ekziston
        context = ge.get_context(mode="file")
        return context

def get_data_from_postgres(
    query: str,
    host: str = None,
    port: str = None,
    database: str = None,
    user: str = None,
    password: str = None
) -> pd.DataFrame:
    """Merr të dhëna nga PostgreSQL dhe i konverton në DataFrame"""
    # Përdor environment variables ose default values
    db_config = {
        'host': host or os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
        'port': port or os.getenv('POSTGRES_PORT', '5432'),
        'database': database or os.getenv('POSTGRES_DB', 'smartgrid_db'),
        'user': user or os.getenv('POSTGRES_USER', 'smartgrid'),
        'password': password or os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
    }
    
    conn = psycopg2.connect(**db_config)
    try:
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

def validate_sensor_data_with_ge(
    query: str = None,
    expectation_suite_name: str = "sensor_data_suite",
    **kwargs
) -> Dict[str, Any]:
    """
    Validon sensor data me Great Expectations
    
    Args:
        query: SQL query për të marrë të dhënat (nëse nuk është dhënë, përdor default)
        expectation_suite_name: Emri i expectation suite
        **kwargs: PostgreSQL connection parameters
    
    Returns:
        Dictionary me validation results
    """
    logger.info("Starting sensor data validation with Great Expectations...")
    
    # Default query nëse nuk është dhënë
    if not query:
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
    
    # Merr të dhënat
    df = get_data_from_postgres(query, **kwargs)
    
    if df.empty:
        logger.warning("No data to validate")
        return {
            'success': False,
            'error': 'No data to validate',
            'statistics': {}
        }
    
    # Krijo Great Expectations dataset
    ge_df = ge.from_pandas(df)
    
    # Load expectation suite
    try:
        # Përpiqemi të ngarkojmë expectation suite nga file
        expectations_path = os.path.join(
            os.path.dirname(__file__),
            "great_expectations",
            "expectations",
            f"{expectation_suite_name}.json"
        )
        
        if os.path.exists(expectations_path):
            import json
            with open(expectations_path, 'r') as f:
                suite = json.load(f)
            
            # Aplikoni expectations
            for expectation in suite.get('expectations', []):
                expectation_type = expectation['expectation_type']
                kwargs_expectation = expectation.get('kwargs', {})
                try:
                    getattr(ge_df, expectation_type)(**kwargs_expectation)
                except Exception as e:
                    logger.warning(f"Error applying expectation {expectation_type}: {e}")
        else:
            # Përdor expectations manuale nëse file nuk ekziston
            ge_df.expect_column_values_to_not_be_null("sensor_id")
            ge_df.expect_column_values_to_not_be_null("sensor_type")
            ge_df.expect_column_values_to_not_be_null("value")
            ge_df.expect_column_values_to_be_in_set(
                "sensor_type",
                ["voltage", "current", "power", "frequency"]
            )
            ge_df.expect_column_values_to_be_between("value", 0, 10000)
            
    except Exception as e:
        logger.error(f"Error loading expectation suite: {e}")
        # Fallback në expectations manuale
        ge_df.expect_column_values_to_not_be_null("sensor_id")
        ge_df.expect_column_values_to_not_be_null("sensor_type")
        ge_df.expect_column_values_to_be_between("value", 0, 10000)
    
    # Validim
    validation_result = ge_df.validate()
    
    # Përgatit rezultatet
    success = validation_result['success']
    statistics = {
        'evaluated_expectations': validation_result['statistics']['evaluated_expectations'],
        'successful_expectations': validation_result['statistics']['successful_expectations'],
        'unsuccessful_expectations': validation_result['statistics']['unsuccessful_expectations'],
        'success_percent': validation_result['statistics']['success_percent']
    }
    
    logger.info(f"Validation completed: {statistics['successful_expectations']}/{statistics['evaluated_expectations']} expectations passed")
    
    return {
        'success': success,
        'statistics': statistics,
        'results': validation_result['results'],
        'data_quality_score': statistics['success_percent']
    }

def validate_meter_readings_with_ge(
    query: str = None,
    expectation_suite_name: str = "meter_readings_suite",
    **kwargs
) -> Dict[str, Any]:
    """
    Validon meter readings me Great Expectations
    
    Args:
        query: SQL query për të marrë të dhënat
        expectation_suite_name: Emri i expectation suite
        **kwargs: PostgreSQL connection parameters
    
    Returns:
        Dictionary me validation results
    """
    logger.info("Starting meter readings validation with Great Expectations...")
    
    # Default query nëse nuk është dhënë
    if not query:
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
    
    # Merr të dhënat
    df = get_data_from_postgres(query, **kwargs)
    
    if df.empty:
        logger.warning("No meter readings to validate")
        return {
            'success': False,
            'error': 'No data to validate',
            'statistics': {}
        }
    
    # Krijo Great Expectations dataset
    ge_df = ge.from_pandas(df)
    
    # Load expectation suite
    try:
        expectations_path = os.path.join(
            os.path.dirname(__file__),
            "great_expectations",
            "expectations",
            f"{expectation_suite_name}.json"
        )
        
        if os.path.exists(expectations_path):
            import json
            with open(expectations_path, 'r') as f:
                suite = json.load(f)
            
            # Aplikoni expectations
            for expectation in suite.get('expectations', []):
                expectation_type = expectation['expectation_type']
                kwargs_expectation = expectation.get('kwargs', {})
                try:
                    getattr(ge_df, expectation_type)(**kwargs_expectation)
                except Exception as e:
                    logger.warning(f"Error applying expectation {expectation_type}: {e}")
        else:
            # Fallback expectations
            ge_df.expect_column_values_to_not_be_null("meter_id")
            ge_df.expect_column_values_to_not_be_null("customer_id")
            ge_df.expect_column_values_to_not_be_null("reading")
            ge_df.expect_column_values_to_be_between("reading", 0, 1000000)
            ge_df.expect_column_values_to_be_in_set("unit", ["kWh"])
            
    except Exception as e:
        logger.error(f"Error loading expectation suite: {e}")
        # Fallback expectations
        ge_df.expect_column_values_to_not_be_null("meter_id")
        ge_df.expect_column_values_to_be_between("reading", 0, 1000000)
    
    # Validim
    validation_result = ge_df.validate()
    
    # Përgatit rezultatet
    success = validation_result['success']
    statistics = {
        'evaluated_expectations': validation_result['statistics']['evaluated_expectations'],
        'successful_expectations': validation_result['statistics']['successful_expectations'],
        'unsuccessful_expectations': validation_result['statistics']['unsuccessful_expectations'],
        'success_percent': validation_result['statistics']['success_percent']
    }
    
    logger.info(f"Meter readings validation: {statistics['successful_expectations']}/{statistics['evaluated_expectations']} expectations passed")
    
    return {
        'success': success,
        'statistics': statistics,
        'results': validation_result['results'],
        'data_quality_score': statistics['success_percent']
    }

def generate_data_docs(validation_result: Dict[str, Any], output_dir: str = None) -> str:
    """
    Gjeneron Data Docs (HTML reports) nga validation results
    
    Args:
        validation_result: Rezultatet e validimit
        output_dir: Directory për të ruajtur Data Docs
    
    Returns:
        Path për Data Docs file
    """
    if not output_dir:
        output_dir = os.path.join(GE_ROOT_DIR, "data_docs")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Krijo HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Quality Validation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .success {{ color: green; }}
            .failure {{ color: red; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Data Quality Validation Report</h1>
        <h2>Statistics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Evaluated Expectations</td>
                <td>{validation_result['statistics'].get('evaluated_expectations', 0)}</td>
            </tr>
            <tr>
                <td>Successful Expectations</td>
                <td class="success">{validation_result['statistics'].get('successful_expectations', 0)}</td>
            </tr>
            <tr>
                <td>Unsuccessful Expectations</td>
                <td class="failure">{validation_result['statistics'].get('unsuccessful_expectations', 0)}</td>
            </tr>
            <tr>
                <td>Success Percent</td>
                <td>{validation_result['statistics'].get('success_percent', 0)}%</td>
            </tr>
        </table>
        <h2>Overall Status</h2>
        <p class="{'success' if validation_result['success'] else 'failure'}">
            {'✅ Validation Passed' if validation_result['success'] else '❌ Validation Failed'}
        </p>
    </body>
    </html>
    """
    
    output_file = os.path.join(output_dir, "validation_report.html")
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    logger.info(f"Data Docs generated at: {output_file}")
    return output_file

