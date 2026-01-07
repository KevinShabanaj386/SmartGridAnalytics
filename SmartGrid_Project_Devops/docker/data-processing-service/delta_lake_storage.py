"""
Delta Lake Storage Implementation
Kombinim i fleksibilitetit të Data Lake dhe strukturës së Data Warehouse
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from delta import DeltaTable
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, lit, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

logger = logging.getLogger(__name__)

# Delta Lake storage path
DELTA_LAKE_BASE_PATH = os.getenv('DELTA_LAKE_BASE_PATH', '/data/delta-lake')
DELTA_LAKE_SENSOR_PATH = f"{DELTA_LAKE_BASE_PATH}/sensor_data"
DELTA_LAKE_METER_PATH = f"{DELTA_LAKE_BASE_PATH}/meter_readings"
DELTA_LAKE_WEATHER_PATH = f"{DELTA_LAKE_BASE_PATH}/weather_data"

def get_spark_session() -> Optional[SparkSession]:
    """Krijon Spark session me Delta Lake support"""
    try:
        spark = SparkSession.builder \
            .appName("SmartGrid-DeltaLake") \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
            .config("spark.databricks.delta.retentionDurationCheck.enabled", "false") \
            .getOrCreate()
        
        logger.info("Spark session me Delta Lake support u krijua me sukses")
        return spark
    except Exception as e:
        logger.error(f"Error creating Spark session: {str(e)}")
        return None

def create_delta_table(spark: SparkSession, table_path: str, schema: StructType, partition_cols: List[str] = None):
    """
    Krijon Delta Lake table nëse nuk ekziston
    
    Args:
        spark: SparkSession
        table_path: Path ku do të ruhet Delta table
        schema: Schema e tabelës
        partition_cols: Kolonat për partitioning (opsionale)
    """
    try:
        if not DeltaTable.isDeltaTable(spark, table_path):
            logger.info(f"Creating Delta table at {table_path}")
            
            # Krijon empty DataFrame me schema
            empty_df = spark.createDataFrame([], schema)
            
            # Shkruan si Delta table
            writer = empty_df.write.format("delta")
            
            if partition_cols:
                writer = writer.partitionBy(*partition_cols)
            
            writer.mode("overwrite").save(table_path)
            
            logger.info(f"Delta table created successfully at {table_path}")
        else:
            logger.info(f"Delta table already exists at {table_path}")
    except Exception as e:
        logger.error(f"Error creating Delta table: {str(e)}")
        raise

def get_sensor_data_schema() -> StructType:
    """Schema për sensor data Delta table"""
    return StructType([
        StructField("event_id", StringType(), False),
        StructField("sensor_id", StringType(), False),
        StructField("sensor_type", StringType(), False),
        StructField("value", DoubleType(), False),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("timestamp", TimestampType(), False),
        StructField("metadata", StringType(), True),  # JSON si string
        StructField("created_at", TimestampType(), False)
    ])

def get_meter_readings_schema() -> StructType:
    """Schema për meter readings Delta table"""
    return StructType([
        StructField("event_id", StringType(), False),
        StructField("meter_id", StringType(), False),
        StructField("customer_id", StringType(), False),
        StructField("reading", DoubleType(), False),
        StructField("unit", StringType(), True),
        StructField("timestamp", TimestampType(), False),
        StructField("created_at", TimestampType(), False)
    ])

def get_weather_data_schema() -> StructType:
    """Schema për weather data Delta table"""
    return StructType([
        StructField("timestamp", TimestampType(), False),
        StructField("temperature", DoubleType(), True),
        StructField("humidity", DoubleType(), True),
        StructField("pressure", DoubleType(), True),
        StructField("wind_speed", DoubleType(), True),
        StructField("weather_condition", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("created_at", TimestampType(), False)
    ])

def write_to_delta_lake(spark: SparkSession, data: List[Dict[str, Any]], table_path: str, 
                        schema: StructType, partition_cols: List[str] = None):
    """
    Shkruan të dhëna në Delta Lake table
    
    Args:
        spark: SparkSession
        data: Lista e të dhënave për të shkruar
        table_path: Path i Delta table
        schema: Schema e të dhënave
        partition_cols: Kolonat për partitioning
    """
    try:
        if not data:
            logger.warning("No data to write to Delta Lake")
            return
        
        # Krijon Delta table nëse nuk ekziston
        create_delta_table(spark, table_path, schema, partition_cols)
        
        # Konverton të dhënat në DataFrame
        df = spark.createDataFrame(data, schema)
        
        # Shton created_at nëse nuk ekziston
        if "created_at" not in [f.name for f in schema.fields]:
            df = df.withColumn("created_at", current_timestamp())
        
        # Shkruan në Delta table
        writer = df.write.format("delta").mode("append")
        
        if partition_cols:
            writer = writer.partitionBy(*partition_cols)
        
        writer.save(table_path)
        
        logger.info(f"Successfully wrote {len(data)} records to Delta Lake at {table_path}")
    except Exception as e:
        logger.error(f"Error writing to Delta Lake: {str(e)}")
        raise

def read_from_delta_lake(spark: SparkSession, table_path: str, filters: Dict[str, Any] = None) -> DataFrame:
    """
    Lexon të dhëna nga Delta Lake table
    
    Args:
        spark: SparkSession
        table_path: Path i Delta table
        filters: Dictionary me filters (opsionale)
    
    Returns:
        DataFrame me të dhënat
    """
    try:
        df = spark.read.format("delta").load(table_path)
        
        # Aplikon filters nëse janë dhënë
        if filters:
            for key, value in filters.items():
                df = df.filter(col(key) == value)
        
        return df
    except Exception as e:
        logger.error(f"Error reading from Delta Lake: {str(e)}")
        raise

def time_travel_query(spark: SparkSession, table_path: str, version: int = None, timestamp: str = None) -> DataFrame:
    """
    Time travel query - lexon version të vjetër të të dhënave
    
    Args:
        spark: SparkSession
        table_path: Path i Delta table
        version: Version number (opsionale)
        timestamp: Timestamp në format ISO (opsionale)
    
    Returns:
        DataFrame me të dhënat e versionit të specifikuar
    """
    try:
        if version is not None:
            df = spark.read.format("delta").option("versionAsOf", version).load(table_path)
            logger.info(f"Reading Delta table version {version}")
        elif timestamp:
            df = spark.read.format("delta").option("timestampAsOf", timestamp).load(table_path)
            logger.info(f"Reading Delta table at timestamp {timestamp}")
        else:
            # Lexon version aktual
            df = spark.read.format("delta").load(table_path)
        
        return df
    except Exception as e:
        logger.error(f"Error in time travel query: {str(e)}")
        raise

def get_table_history(spark: SparkSession, table_path: str) -> DataFrame:
    """
    Merr historikun e ndryshimeve të Delta table
    
    Args:
        spark: SparkSession
        table_path: Path i Delta table
    
    Returns:
        DataFrame me historikun
    """
    try:
        delta_table = DeltaTable.forPath(spark, table_path)
        history = delta_table.history()
        return history
    except Exception as e:
        logger.error(f"Error getting table history: {str(e)}")
        raise

def vacuum_delta_table(spark: SparkSession, table_path: str, retention_hours: int = 168):
    """
    Pastron file-et e vjetra nga Delta table (vacuum)
    
    Args:
        spark: SparkSession
        table_path: Path i Delta table
        retention_hours: Orët e retention (default: 7 ditë)
    """
    try:
        delta_table = DeltaTable.forPath(spark, table_path)
        delta_table.vacuum(retentionHours=retention_hours)
        logger.info(f"Vacuum completed for Delta table at {table_path}")
    except Exception as e:
        logger.error(f"Error vacuuming Delta table: {str(e)}")
        raise

def optimize_delta_table(spark: SparkSession, table_path: str):
    """
    Optimizon Delta table (compaction, Z-ordering)
    
    Args:
        spark: SparkSession
        table_path: Path i Delta table
    """
    try:
        delta_table = DeltaTable.forPath(spark, table_path)
        delta_table.optimize().executeCompaction()
        logger.info(f"Optimization completed for Delta table at {table_path}")
    except Exception as e:
        logger.error(f"Error optimizing Delta table: {str(e)}")
        raise

def store_sensor_data_delta(sensor_data: List[Dict[str, Any]]):
    """Shkruan sensor data në Delta Lake"""
    spark = get_spark_session()
    if not spark:
        logger.error("Failed to create Spark session")
        return
    
    try:
        schema = get_sensor_data_schema()
        write_to_delta_lake(
            spark, 
            sensor_data, 
            DELTA_LAKE_SENSOR_PATH,
            schema,
            partition_cols=["sensor_type", "timestamp"]  # Partitioning për performancë
        )
    except Exception as e:
        logger.error(f"Error storing sensor data in Delta Lake: {str(e)}")
    finally:
        spark.stop()

def store_meter_readings_delta(meter_readings: List[Dict[str, Any]]):
    """Shkruan meter readings në Delta Lake"""
    spark = get_spark_session()
    if not spark:
        logger.error("Failed to create Spark session")
        return
    
    try:
        schema = get_meter_readings_schema()
        write_to_delta_lake(
            spark,
            meter_readings,
            DELTA_LAKE_METER_PATH,
            schema,
            partition_cols=["customer_id", "timestamp"]
        )
    except Exception as e:
        logger.error(f"Error storing meter readings in Delta Lake: {str(e)}")
    finally:
        spark.stop()

def store_weather_data_delta(weather_data: List[Dict[str, Any]]):
    """Shkruan weather data në Delta Lake"""
    spark = get_spark_session()
    if not spark:
        logger.error("Failed to create Spark session")
        return
    
    try:
        schema = get_weather_data_schema()
        write_to_delta_lake(
            spark,
            weather_data,
            DELTA_LAKE_WEATHER_PATH,
            schema,
            partition_cols=["timestamp"]
        )
    except Exception as e:
        logger.error(f"Error storing weather data in Delta Lake: {str(e)}")
    finally:
        spark.stop()

