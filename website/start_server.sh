#!/bin/bash

# PICO Platform Production Server Startup Script

echo "Starting PICO Calcium Processing Platform..."

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null
then
    echo "Gunicorn not found. Installing..."
    pip install gunicorn
fi

# Number of worker processes
WORKERS=4

# Bind address and port
BIND="0.0.0.0:5000"

# Timeout for worker processes (in seconds)
TIMEOUT=3600

# Log files
ACCESS_LOG="access.log"
ERROR_LOG="error.log"

# Start gunicorn
gunicorn \
    --workers $WORKERS \
    --bind $BIND \
    --timeout $TIMEOUT \
    --access-logfile $ACCESS_LOG \
    --error-logfile $ERROR_LOG \
    --log-level info \
    app:app

echo "Server stopped."
