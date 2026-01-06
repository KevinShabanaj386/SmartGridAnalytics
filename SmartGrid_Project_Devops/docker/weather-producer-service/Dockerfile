FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy schema files and schema registry client
COPY app.py .
COPY schema_registry_client.py .
COPY ../../schemas/avro/ /app/schemas/avro/

EXPOSE 5006

CMD ["python", "app.py"]

