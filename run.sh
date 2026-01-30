#!/bin/bash
# Startup script for deployment
# Honors PORT environment variable (required by Koyeb)

PORT=${PORT:-8001}

echo "Starting Sentiment Alpha Radar on port $PORT"

uvicorn main:app --host 0.0.0.0 --port $PORT
