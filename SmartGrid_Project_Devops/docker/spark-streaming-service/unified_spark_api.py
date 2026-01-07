"""
Unified Spark API për Real-time dhe Batch Processing
Kjo modul ofron një API të unifikuar për të përdorur Spark për real-time dhe batch processing
"""
from pyspark.sql import SparkSession
from typing import Dict, Any, Optional, Literal
import logging
import os

logger = logging.getLogger(__name__)

class UnifiedSparkProcessor:
    """
    Unified processor për real-time dhe batch processing me Spark
    """
    
    def __init__(self, app_name: str = "SmartGridUnifiedProcessor"):
        """Initialize unified processor"""
        self.app_name = app_name
        self.spark = None
        self.mode = None  # 'streaming' ose 'batch'
    
    def create_spark_session(
        self,
        mode: Literal['streaming', 'batch'] = 'batch',
        checkpoint_location: str = None
    ) -> SparkSession:
        """
        Krijon Spark session për streaming ose batch processing
        
        Args:
            mode: 'streaming' ose 'batch'
            checkpoint_location: Location për checkpointing (vetëm për streaming)
        """
        self.mode = mode
        
        builder = SparkSession.builder \
            .appName(f"{self.app_name}_{mode}") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.jars.packages", "org.postgresql:postgresql:42.5.4,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
        
        if mode == 'streaming' and checkpoint_location:
            builder.config("spark.sql.streaming.checkpointLocation", checkpoint_location)
        
        self.spark = builder.getOrCreate()
        self.spark.sparkContext.setLogLevel("WARN")
        
        logger.info(f"Spark session created for {mode} processing")
        return self.spark
    
    def process_sensor_data(
        self,
        source: Literal['kafka', 'postgresql'],
        start_date: str = None,
        end_date: str = None,
        kafka_topic: str = None,
        kafka_broker: str = None,
        output_table: str = "sensor_aggregates"
    ):
        """
        Përpunon sensor data nga Kafka (streaming) ose PostgreSQL (batch)
        
        Args:
            source: 'kafka' për streaming, 'postgresql' për batch
            start_date: Data fillestare (vetëm për batch)
            end_date: Data përfundimtare (vetëm për batch)
            kafka_topic: Kafka topic (vetëm për streaming)
            kafka_broker: Kafka broker (vetëm për streaming)
            output_table: Tabela për output
        """
        if source == 'kafka':
            return self._process_sensor_streaming(kafka_topic, kafka_broker, output_table)
        elif source == 'postgresql':
            return self._process_sensor_batch(start_date, end_date, output_table)
        else:
            raise ValueError(f"Unsupported source: {source}")
    
    def process_meter_readings(
        self,
        source: Literal['kafka', 'postgresql'],
        start_date: str = None,
        end_date: str = None,
        kafka_topic: str = None,
        kafka_broker: str = None,
        output_table: str = "consumption_aggregates"
    ):
        """
        Përpunon meter readings nga Kafka (streaming) ose PostgreSQL (batch)
        
        Args:
            source: 'kafka' për streaming, 'postgresql' për batch
            start_date: Data fillestare (vetëm për batch)
            end_date: Data përfundimtare (vetëm për batch)
            kafka_topic: Kafka topic (vetëm për streaming)
            kafka_broker: Kafka broker (vetëm për streaming)
            output_table: Tabela për output
        """
        if source == 'kafka':
            return self._process_meter_streaming(kafka_topic, kafka_broker, output_table)
        elif source == 'postgresql':
            return self._process_meter_batch(start_date, end_date, output_table)
        else:
            raise ValueError(f"Unsupported source: {source}")
    
    def _process_sensor_streaming(self, kafka_topic: str, kafka_broker: str, output_table: str):
        """Process sensor data nga Kafka (streaming)"""
        from pyspark.sql.functions import col, from_json, window, avg, min, max, count, stddev
        from pyspark.sql.types import StructType, StructField, StringType, DoubleType
        
        if not self.spark or self.mode != 'streaming':
            self.create_spark_session(mode='streaming')
        
        # Schema për sensor data
        sensor_schema = StructType([
            StructField("sensor_id", StringType(), True),
            StructField("sensor_type", StringType(), True),
            StructField("value", DoubleType(), True),
            StructField("timestamp", StringType(), True),
        ])
        
        # Lexo nga Kafka
        df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", kafka_broker) \
            .option("subscribe", kafka_topic) \
            .option("startingOffsets", "latest") \
            .load()
        
        # Parse JSON
        sensor_df = df.select(
            from_json(col("value").cast("string"), sensor_schema).alias("data")
        ).select("data.*")
        
        # Agregata
        windowed_agg = sensor_df \
            .withWatermark("timestamp", "10 minutes") \
            .groupBy(
                window(col("timestamp"), "5 minutes"),
                col("sensor_type"),
                col("sensor_id")
            ) \
            .agg(
                avg("value").alias("avg_value"),
                min("value").alias("min_value"),
                max("value").alias("max_value"),
                count("*").alias("count"),
                stddev("value").alias("stddev_value")
            )
        
        # Shkruaj në PostgreSQL
        query = windowed_agg \
            .writeStream \
            .foreachBatch(lambda batch_df, batch_id: self._write_to_postgres(batch_df, output_table)) \
            .outputMode("update") \
            .trigger(processingTime='30 seconds') \
            .start()
        
        return query
    
    def _process_sensor_batch(self, start_date: str, end_date: str, output_table: str):
        """Process sensor data nga PostgreSQL (batch)"""
        from pyspark.sql.functions import date_trunc, avg, min, max, count, stddev, expr
        
        if not self.spark or self.mode != 'batch':
            self.create_spark_session(mode='batch')
        
        # Lexo nga PostgreSQL
        jdbc_url = f"jdbc:postgresql://{os.getenv('POSTGRES_HOST', 'smartgrid-postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'smartgrid_db')}"
        jdbc_properties = {
            "user": os.getenv('POSTGRES_USER', 'smartgrid'),
            "password": os.getenv('POSTGRES_PASSWORD', 'smartgrid123'),
            "driver": "org.postgresql.Driver"
        }
        
        query = f"""
            (SELECT * FROM sensor_data
            WHERE timestamp >= '{start_date}' AND timestamp < '{end_date}'
            ) AS sensor_data_query
        """
        
        sensor_df = self.spark.read.jdbc(url=jdbc_url, table=query, properties=jdbc_properties)
        
        # Agregata
        aggregated_df = sensor_df \
            .withColumn("hour_bucket", date_trunc("hour", col("timestamp"))) \
            .groupBy("hour_bucket", "sensor_type", "sensor_id") \
            .agg(
                avg("value").alias("avg_value"),
                min("value").alias("min_value"),
                max("value").alias("max_value"),
                count("*").alias("count"),
                stddev("value").alias("stddev_value")
            )
        
        # Shkruaj në PostgreSQL
        aggregated_df.write \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", output_table) \
            .option("user", jdbc_properties["user"]) \
            .option("password", jdbc_properties["password"]) \
            .option("driver", jdbc_properties["driver"]) \
            .mode("overwrite") \
            .save()
        
        return aggregated_df
    
    def _process_meter_streaming(self, kafka_topic: str, kafka_broker: str, output_table: str):
        """Process meter readings nga Kafka (streaming)"""
        # Similar implementation si _process_sensor_streaming
        pass
    
    def _process_meter_batch(self, start_date: str, end_date: str, output_table: str):
        """Process meter readings nga PostgreSQL (batch)"""
        # Similar implementation si _process_sensor_batch
        pass
    
    def _write_to_postgres(self, batch_df, table_name: str):
        """Helper për të shkruar batch në PostgreSQL"""
        jdbc_url = f"jdbc:postgresql://{os.getenv('POSTGRES_HOST', 'smartgrid-postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'smartgrid_db')}"
        batch_df.write \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", table_name) \
            .option("user", os.getenv('POSTGRES_USER', 'smartgrid')) \
            .option("password", os.getenv('POSTGRES_PASSWORD', 'smartgrid123')) \
            .option("driver", "org.postgresql.Driver") \
            .mode("append") \
            .save()
    
    def stop(self):
        """Stop Spark session"""
        if self.spark:
            self.spark.stop()
            logger.info("Spark session stopped")

