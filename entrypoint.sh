#!/bin/sh

# Exit on error
set -e

echo "Waiting for PostgreSQL..."

# Wait for PostgreSQL to be ready with a timeout
TIMEOUT=300  # 5 minutes timeout
ELAPSED=0

until pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -q; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        echo "Timeout reached waiting for PostgreSQL"
        exit 1
    fi
done

echo "PostgreSQL is up - executing commands"

# Create directories if they don't exist (with proper permissions)
mkdir -p /app/staticfiles
mkdir -p /app/media
chmod 755 /app/staticfiles
chmod 755 /app/media

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files 
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start server with gunicorn
echo "Starting gunicorn server..."
exec gunicorn resortproject.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
