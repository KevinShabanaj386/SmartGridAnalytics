"""
Apache Spark Batch Processing për Smart Grid Analytics
Përpunon të dhëna historike nga PostgreSQL me Spark Batch API
Unified platform për real-time dhe batch processing
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, min, max, count, stddev, sum, date_trunc, window
from pyspark.sql.types import *
import os
import logging
from datetime import datetime, timedelta
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Consul Config Management
try:
    from consul_config import get_config
    POSTGRES_HOST = get_config('postgres/host', os.getenv('POSTGRES_HOST', 'smartgrid-postgres'))
    POSTGRES_PORT = get_config('postgres/port', os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB = get_config('postgres/database', os.getenv('POSTGRES_DB', 'smartgrid_db'))
    POSTGRES_USER = get_config('postgres/user', os.getenv('POSTGRES_USER', 'smartgrid'))
    POSTGRES_PASSWORD = get_config('postgres/password', os.getenv('POSTGRES_PASSWORD', 'smartgrid123'))
except ImportError:
    logger.warning("Consul config module not available, using environment variables")
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'smartgrid-postgres')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'smartgrid_db')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'smartgrid')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'smartgrid123')

def create_spark_session(app_name: str = "SmartGridBatchProcessing"):
    """Krijon Spark session për batch processing"""
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.5.4") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    logger.info(f"Spark session created for batch processing: {app_name}")
    return spark

def process_sensor_data_batch(
    spark: SparkSession,
    start_date: str = None,
    end_date: str = None,
    output_table: str = "sensor_aggregates_batch"
):
    """
    Përpunon sensor data historike nga PostgreSQL (BATCH PROCESSING)
    
    Args:
        spark: Spark session
        start_date: Data fillestare (YYYY-MM-DD) - default: 7 ditë më parë
        end_date: Data përfundimtare (YYYY-MM-DD) - default: sot
        output_table: Tabela për të shkruar rezultatet
    """
    logger.info("Starting batch processing for sensor data...")
    
    # Default dates
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    logger.info(f"Processing sensor data from {start_date} to {end_date}")
    
    # Lexo të dhëna nga PostgreSQL
    jdbc_url = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    jdbc_properties = {
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
        "driver": "org.postgresql.Driver"
    }
    
    query = f"""
        (SELECT 
            sensor_id,
            sensor_type,
            value,
            timestamp,
            latitude,
            longitude
        FROM sensor_data
        WHERE timestamp >= '{start_date}' 
        AND timestamp < '{end_date}'
        ) AS sensor_data_query
    """
    
    try:
        # Lexo nga PostgreSQL
        sensor_df = spark.read.jdbc(
            url=jdbc_url,
            table=query,
            properties=jdbc_properties
        )
        
        logger.info(f"Loaded {sensor_df.count()} sensor records from PostgreSQL")
        
        # Agregata për çdo orë
        aggregated_df = sensor_df \
            .withColumn("hour_bucket", date_trunc("hour", col("timestamp"))) \
            .groupBy(
                col("hour_bucket"),
                col("sensor_type"),
                col("sensor_id")
            ) \
            .agg(
                avg("value").alias("avg_value"),
                min("value").alias("min_value"),
                max("value").alias("max_value"),
                count("*").alias("count"),
                stddev("value").alias("stddev_value")
            ) \
            .select(
                col("hour_bucket").alias("window_start"),
                (col("hour_bucket") + expr("INTERVAL 1 HOUR")).alias("window_end"),
                col("sensor_type"),
                col("sensor_id"),
                col("avg_value"),
                col("min_value"),
                col("max_value"),
                col("count"),
                col("stddev_value")
            )
        
        # Shkruaj në PostgreSQL
        aggregated_df.write \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", output_table) \
            .option("user", POSTGRES_USER) \
            .option("password", POSTGRES_PASSWORD) \
            .option("driver", "org.postgresql.Driver") \
            .mode("overwrite") \
            .save()
        
        logger.info(f"✅ Batch processing completed: {aggregated_df.count()} aggregated records written to {output_table}")
        
        return aggregated_df
        
    except Exception as e:
        logger.error(f"Error in batch processing sensor data: {str(e)}")
        raise

def process_meter_readings_batch(
    spark: SparkSession,
    start_date: str = None,
    end_date: str = None,
    output_table: str = "consumption_aggregates_batch"
):
    """
    Përpunon meter readings historike nga PostgreSQL (BATCH PROCESSING)
    
    Args:
        spark: Spark session
        start_date: Data fillestare (YYYY-MM-DD)
        end_date: Data përfundimtare (YYYY-MM-DD)
        output_table: Tabela për të shkruar rezultatet
    """
    logger.info("Starting batch processing for meter readings...")
    
    # Default dates
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    logger.info(f"Processing meter readings from {start_date} to {end_date}")
    
    # Lexo të dhëna nga PostgreSQL
    jdbc_url = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    jdbc_properties = {
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
        "driver": "org.postgresql.Driver"
    }
    
    query = f"""
        (SELECT 
            meter_id,
            customer_id,
            reading,
            unit,
            timestamp
        FROM meter_readings
        WHERE timestamp >= '{start_date}' 
        AND timestamp < '{end_date}'
        ) AS meter_readings_query
    """
    
    try:
        # Lexo nga PostgreSQL
        meter_df = spark.read.jdbc(
            url=jdbc_url,
            table=query,
            properties=jdbc_properties
        )
        
        logger.info(f"Loaded {meter_df.count()} meter reading records from PostgreSQL")
        
        # Agregata për çdo ditë
        aggregated_df = meter_df \
            .withColumn("day_bucket", date_trunc("day", col("timestamp"))) \
            .groupBy(
                col("day_bucket"),
                col("customer_id")
            ) \
            .agg(
                sum("reading").alias("total_consumption"),
                avg("reading").alias("avg_consumption"),
                count("*").alias("reading_count"),
                min("reading").alias("min_reading"),
                max("reading").alias("max_reading")
            ) \
            .select(
                col("day_bucket").alias("window_start"),
                (col("day_bucket") + expr("INTERVAL 1 DAY")).alias("window_end"),
                col("customer_id"),
                col("total_consumption"),
                col("avg_consumption"),
                col("reading_count"),
                col("min_reading"),
                col("max_reading")
            )
        
        # Shkruaj në PostgreSQL
        aggregated_df.write \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", output_table) \
            .option("user", POSTGRES_USER) \
            .option("password", POSTGRES_PASSWORD) \
            .option("driver", "org.postgresql.Driver") \
            .mode("overwrite") \
            .save()
        
        logger.info(f"✅ Batch processing completed: {aggregated_df.count()} aggregated records written to {output_table}")
        
        return aggregated_df
        
    except Exception as e:
        logger.error(f"Error in batch processing meter readings: {str(e)}")
        raise

def process_historical_data(
    spark: SparkSession,
    days_back: int = 30,
    output_suffix: str = "batch"
):
    """
    Përpunon të gjitha të dhënat historike (BATCH PROCESSING)
    
    Args:
        spark: Spark session
        days_back: Numri i ditëve për të përpunuar (default: 30)
        output_suffix: Suffix për output tables
    """
    logger.info(f"Starting historical data processing for last {days_back} days...")
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    # Process sensor data
    sensor_df = process_sensor_data_batch(
        spark=spark,
        start_date=start_date,
        end_date=end_date,
        output_table=f"sensor_aggregates_{output_suffix}"
    )
    
    # Process meter readings
    meter_df = process_meter_readings_batch(
        spark=spark,
        start_date=start_date,
        end_date=end_date,
        output_table=f"consumption_aggregates_{output_suffix}"
    )
    
    logger.info("✅ Historical data processing completed")
    
    return {
        'sensor_aggregates': sensor_df,
        'consumption_aggregates': meter_df
    }

def main():
    """Funksioni kryesor për batch processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Spark Batch Processing për Smart Grid Analytics')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--days-back', type=int, default=7, help='Number of days to process (default: 7)')
    parser.add_argument('--data-type', type=str, choices=['sensor', 'meter', 'all'], default='all',
                       help='Type of data to process (default: all)')
    
    args = parser.parse_args()
    
    logger.info("Starting Spark Batch Processing...")
    
    spark = create_spark_session("SmartGridBatchProcessing")
    
    try:
        if args.data_type == 'sensor':
            process_sensor_data_batch(
                spark=spark,
                start_date=args.start_date,
                end_date=args.end_date
            )
        elif args.data_type == 'meter':
            process_meter_readings_batch(
                spark=spark,
                start_date=args.start_date,
                end_date=args.end_date
            )
        else:  # all
            if args.start_date and args.end_date:
                process_sensor_data_batch(
                    spark=spark,
                    start_date=args.start_date,
                    end_date=args.end_date
                )
                process_meter_readings_batch(
                    spark=spark,
                    start_date=args.start_date,
                    end_date=args.end_date
                )
            else:
                process_historical_data(
                    spark=spark,
                    days_back=args.days_back
                )
        
        logger.info("✅ Batch processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        raise
    finally:
        spark.stop()
        logger.info("Spark session stopped")

if __name__ == "__main__":
    # Import expr për date arithmetic
    from pyspark.sql.functions import expr
    main()

