"""
Airflow DAG për Spark Batch Processing
Ekzekuton Spark batch jobs për historical data processing
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import logging

logger = logging.getLogger(__name__)

# Konfigurimi i DAG
default_args = {
    'owner': 'smartgrid-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'spark_batch_processing',
    default_args=default_args,
    description='Spark Batch Processing për historical data',
    schedule_interval=timedelta(days=1),  # Ekzekutohet çdo ditë (për të dhëna të djeshme)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['smartgrid', 'spark', 'batch-processing'],
)

def run_spark_batch_job(**context):
    """
    Ekzekuton Spark batch job për historical data processing
    """
    import subprocess
    import os
    
    # Merr date range (për djeshme)
    execution_date = context['execution_date']
    end_date = execution_date.strftime("%Y-%m-%d")
    start_date = (execution_date - timedelta(days=1)).strftime("%Y-%m-%d")
    
    logger.info(f"Running Spark batch job for {start_date} to {end_date}")
    
    # Path për spark_batch.py
    spark_batch_script = os.path.join(
        os.path.dirname(__file__),
        '..', '..', 'docker', 'spark-streaming-service', 'spark_batch.py'
    )
    
    # Ekzekuto Spark batch job
    cmd = [
        'spark-submit',
        '--master', 'local[*]',
        '--packages', 'org.postgresql:postgresql:42.5.4',
        spark_batch_script,
        '--start-date', start_date,
        '--end-date', end_date,
        '--data-type', 'all'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Spark batch job completed successfully: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Spark batch job failed: {e.stderr}")
        raise

# Task për Spark batch processing
spark_batch_task = PythonOperator(
    task_id='run_spark_batch_job',
    python_callable=run_spark_batch_job,
    dag=dag,
)

# Task për verification
verify_batch_results = BashOperator(
    task_id='verify_batch_results',
    bash_command="""
    echo "Verifying batch processing results..."
    # Këtu mund të shtohen komanda për të verifikuar rezultatet
    """,
    dag=dag,
)

# Dependencies
spark_batch_task >> verify_batch_results

