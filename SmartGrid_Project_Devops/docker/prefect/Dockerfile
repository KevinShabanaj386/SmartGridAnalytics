FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY flows/ ./flows/
COPY deploy.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PREFECT_HOME=/app/.prefect

# Expose Prefect server port
EXPOSE 4200

# Default command: start Prefect server
CMD ["prefect", "server", "start", "--host", "0.0.0.0"]

