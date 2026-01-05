FROM bitnami/spark:3.5

USER root

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install PostgreSQL JDBC driver
RUN curl -L https://jdbc.postgresql.org/download/postgresql-42.7.1.jar -o /opt/bitnami/spark/jars/postgresql-42.7.1.jar

# Install Kafka connector
RUN curl -L https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.0/spark-sql-kafka-0-10_2.12-3.5.0.jar -o /opt/bitnami/spark/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar

# Copy application code
COPY spark_consumer.py /app/spark_consumer.py

WORKDIR /app

# Set environment variables
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0", "spark_consumer.py"]

