"""
Apache Spark Structured Streaming Consumer për Smart Grid Analytics
Bazuar në Real-Time Energy Monitoring System
Përpunon të dhëna në kohë reale nga Kafka me Spark Structured Streaming
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, window, avg, min, max, count, stddev, sum, last
from pyspark.sql.types import *
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurimi
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'smartgrid-kafka:9092')
KAFKA_TOPIC_SENSOR_DATA = os.getenv('KAFKA_TOPIC_SENSOR_DATA', 'smartgrid-sensor-data')
KAFKA_TOPIC_METER_READINGS = os.getenv('KAFKA_TOPIC_METER_READINGS', 'smartgrid-meter-readings')
KAFKA_TOPIC_WEATHER = os.getenv('KAFKA_TOPIC_WEATHER', 'smartgrid-weather-data')

# PostgreSQL konfigurim
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'smartgrid-postgres')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'smartgrid_db')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'smartgrid')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'smartgrid123')

# Schema për sensor data
sensor_schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("sensor_id", StringType(), True),
    StructField("sensor_type", StringType(), True),
    StructField("value", DoubleType(), True),
    StructField("location", StructType([
        StructField("lat", DoubleType(), True),
        StructField("lon", DoubleType(), True)
    ]), True),
    StructField("timestamp", StringType(), True),
    StructField("metadata", MapType(StringType(), StringType()), True)
])

# Schema për meter readings
meter_schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("meter_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("reading", DoubleType(), True),
    StructField("unit", StringType(), True),
    StructField("timestamp", StringType(), True)
])

# Schema për weather data
weather_schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("temperature", DoubleType(), True),
    StructField("humidity", DoubleType(), True),
    StructField("pressure", DoubleType(), True),
    StructField("wind_speed", DoubleType(), True),
    StructField("weather_condition", StringType(), True),
    StructField("location", StructType([
        StructField("lat", DoubleType(), True),
        StructField("lon", DoubleType(), True)
    ]), True)
])

def create_spark_session():
    """Krijon Spark session me konfigurim për Structured Streaming"""
    spark = SparkSession.builder \
        .appName("SmartGridSparkStreaming") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoint") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    logger.info("Spark session created successfully")
    return spark

def process_sensor_stream(spark):
    """Përpunon stream-in e të dhënave të sensorëve"""
    logger.info(f"Starting sensor data stream from topic: {KAFKA_TOPIC_SENSOR_DATA}")
    
    # Lexo stream nga Kafka
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC_SENSOR_DATA) \
        .option("startingOffsets", "latest") \
        .load()
    
    # Parse JSON dhe aplikoni schema
    sensor_df = df.select(
        from_json(col("value").cast("string"), sensor_schema).alias("data")
    ).select("data.*")
    
    # Agregata në kohë reale (windowed aggregations)
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
        ) \
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("sensor_type"),
            col("sensor_id"),
            col("avg_value"),
            col("min_value"),
            col("max_value"),
            col("count"),
            col("stddev_value")
        )
    
    # Shkruaj në PostgreSQL (batch mode)
    def write_to_postgres(batch_df, batch_id):
        """Shkruan batch në PostgreSQL"""
        try:
            batch_df.write \
                .format("jdbc") \
                .option("url", f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}") \
                .option("dbtable", "sensor_aggregates_realtime") \
                .option("user", POSTGRES_USER) \
                .option("password", POSTGRES_PASSWORD) \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()
            
            logger.info(f"Batch {batch_id} written to PostgreSQL successfully")
        except Exception as e:
            logger.error(f"Error writing batch {batch_id} to PostgreSQL: {str(e)}")
    
    # Start streaming query
    query = windowed_agg \
        .writeStream \
        .foreachBatch(write_to_postgres) \
        .outputMode("update") \
        .trigger(processingTime='30 seconds') \
        .start()
    
    return query

def process_meter_stream(spark):
    """Përpunon stream-in e leximit të matësve"""
    logger.info(f"Starting meter readings stream from topic: {KAFKA_TOPIC_METER_READINGS}")
    
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC_METER_READINGS) \
        .option("startingOffsets", "latest") \
        .load()
    
    meter_df = df.select(
        from_json(col("value").cast("string"), meter_schema).alias("data")
    ).select("data.*")
    
    # Agregata për konsumim total
    consumption_agg = meter_df \
        .withWatermark("timestamp", "10 minutes") \
        .groupBy(
            window(col("timestamp"), "1 hour"),
            col("customer_id")
        ) \
        .agg(
            sum("reading").alias("total_consumption"),
            avg("reading").alias("avg_consumption"),
            count("*").alias("reading_count")
        ) \
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("customer_id"),
            col("total_consumption"),
            col("avg_consumption"),
            col("reading_count")
        )
    
    def write_consumption_to_postgres(batch_df, batch_id):
        try:
            batch_df.write \
                .format("jdbc") \
                .option("url", f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}") \
                .option("dbtable", "consumption_aggregates_realtime") \
                .option("user", POSTGRES_USER) \
                .option("password", POSTGRES_PASSWORD) \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()
            
            logger.info(f"Consumption batch {batch_id} written to PostgreSQL")
        except Exception as e:
            logger.error(f"Error writing consumption batch {batch_id}: {str(e)}")
    
    query = consumption_agg \
        .writeStream \
        .foreachBatch(write_consumption_to_postgres) \
        .outputMode("update") \
        .trigger(processingTime='1 minute') \
        .start()
    
    return query

def process_weather_stream(spark):
    """Përpunon stream-in e të dhënave të motit"""
    logger.info(f"Starting weather data stream from topic: {KAFKA_TOPIC_WEATHER}")
    
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC_WEATHER) \
        .option("startingOffsets", "latest") \
        .load()
    
    weather_df = df.select(
        from_json(col("value").cast("string"), weather_schema).alias("data")
    ).select("data.*")
    
    # Agregata për motin
    weather_agg = weather_df \
        .withWatermark("timestamp", "10 minutes") \
        .groupBy(
            window(col("timestamp"), "1 hour")
        ) \
        .agg(
            avg("temperature").alias("avg_temperature"),
            avg("humidity").alias("avg_humidity"),
            avg("pressure").alias("avg_pressure"),
            avg("wind_speed").alias("avg_wind_speed"),
            last("weather_condition").alias("weather_condition")
        ) \
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("avg_temperature"),
            col("avg_humidity"),
            col("avg_pressure"),
            col("avg_wind_speed"),
            col("weather_condition")
        )
    
    def write_weather_to_postgres(batch_df, batch_id):
        try:
            batch_df.write \
                .format("jdbc") \
                .option("url", f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}") \
                .option("dbtable", "weather_aggregates_realtime") \
                .option("user", POSTGRES_USER) \
                .option("password", POSTGRES_PASSWORD) \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()
            
            logger.info(f"Weather batch {batch_id} written to PostgreSQL")
        except Exception as e:
            logger.error(f"Error writing weather batch {batch_id}: {str(e)}")
    
    query = weather_agg \
        .writeStream \
        .foreachBatch(write_weather_to_postgres) \
        .outputMode("update") \
        .trigger(processingTime='1 minute') \
        .start()
    
    return query

def main():
    """Funksioni kryesor"""
    logger.info("Starting Spark Structured Streaming for Smart Grid Analytics")
    
    spark = create_spark_session()
    queries = []
    
    try:
        # Start të gjitha stream-et
        sensor_query = process_sensor_stream(spark)
        meter_query = process_meter_stream(spark)
        weather_query = process_weather_stream(spark)
        
        queries = [sensor_query, meter_query, weather_query]
        
        logger.info("All streaming queries started successfully")
        
        # Prit deri sa të ndalojnë (prit në të gjitha query-t)
        import threading
        
        def await_query(query, name):
            try:
                query.awaitTermination()
            except Exception as e:
                logger.error(f"Error in {name} query: {str(e)}")
        
        threads = [
            threading.Thread(target=await_query, args=(sensor_query, "sensor"), daemon=True),
            threading.Thread(target=await_query, args=(meter_query, "meter"), daemon=True),
            threading.Thread(target=await_query, args=(weather_query, "weather"), daemon=True)
        ]
        
        for thread in threads:
            thread.start()
        
        # Prit deri sa të gjitha thread-et të mbarojnë
        for thread in threads:
            thread.join()
        
    except KeyboardInterrupt:
        logger.info("Stopping streaming queries...")
        for query in queries:
            try:
                query.stop()
            except:
                pass
    except Exception as e:
        logger.error(f"Error in streaming: {str(e)}")
        for query in queries:
            try:
                query.stop()
            except:
                pass
        raise
    finally:
        spark.stop()
        logger.info("Spark session stopped")

if __name__ == "__main__":
    main()

