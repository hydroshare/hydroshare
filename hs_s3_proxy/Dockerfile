FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Set Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Copy application code
COPY ./api /app/api

# Expose S3 port
EXPOSE 9000

# Run the application
CMD ["python", "-m", "api.main"]
