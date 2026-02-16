#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Run database migrations
echo "Running database migrations..."
#alembic upgrade head

# Start the application with Gunicorn
# Adjust workers/bind address as needed via environment variables or defaults
WORKERS=${GUNICORN_WORKERS:-4}
BIND_ADDRESS=${BIND_ADDRESS:-0.0.0.0:8000}

echo "Starting application with Gunicorn ($WORKERS workers) on $BIND_ADDRESS..."
exec gunicorn -w "$WORKERS" -k uvicorn.workers.UvicornWorker main:app --bind "$BIND_ADDRESS"
