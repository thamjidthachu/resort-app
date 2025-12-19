FROM python:3.12.3-slim AS base

WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    vim \
    libpq-dev \
    python3-dev \
    python3-psycopg2 \
    postgresql-client \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create non-root user first
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Command to run the application
CMD ["gunicorn", "resortproject.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
