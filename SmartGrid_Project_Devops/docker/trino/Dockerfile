FROM trinodb/trino:latest

# Copy custom configuration
COPY config.properties /etc/trino/config.properties
COPY catalog/postgresql.properties /etc/trino/catalog/postgresql.properties
COPY catalog/mongodb.properties /etc/trino/catalog/mongodb.properties
COPY catalog/cassandra.properties /etc/trino/catalog/cassandra.properties
COPY catalog/kafka.properties /etc/trino/catalog/kafka.properties

# Create directories
RUN mkdir -p /etc/trino/catalog

# Set permissions (best-effort; ignore permission errors on base image files)
RUN chmod -R 755 /etc/trino || echo "Warning: could not change some Trino config permissions"

EXPOSE 8080

CMD ["/usr/lib/trino/bin/run-trino"]

