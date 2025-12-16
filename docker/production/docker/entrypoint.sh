#!/bin/bash

# Production entrypoint script for OnlineVekalat API

# Set default environment variables
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-"config.settings"}
export PYTHONPATH=${PYTHONPATH:-"/home/app/api"}
export WORKERS=${WORKERS:-5}
export TIMEOUT=${TIMEOUT:-1900}
export PORT=${PORT:-8089}

# Change to the application directory
cd "${PYTHONPATH}" || exit 1

# Display environment information
echo "Starting OnlineVekalat API server"
echo "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE}"
echo "PORT: ${PORT}"
echo "WORKERS: ${WORKERS}"
echo "TIMEOUT: ${TIMEOUT}"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create cache table if needed
echo "Creating cache table..."
python manage.py createcachetable

# Start Gunicorn server with optimized settings
echo "Starting Gunicorn server..."
gunicorn \
    --bind="0.0.0.0:${PORT}" \
    --workers="${WORKERS}" \
    --timeout="${TIMEOUT}" \
    --log-level=info \
    --access-logfile=/home/app/logs/gunicorn-access.log \
    --error-logfile=/home/app/logs/gunicorn-error.log \
    --log-file=/home/app/logs/gunicorn.log \
    --worker-tmp-dir=/dev/shm \
    --worker-class=gevent \
    --max-requests=1000 \
    --max-requests-jitter=50 \
    --keep-alive=30 \
    --graceful-timeout=30 \
    config.wsgi
