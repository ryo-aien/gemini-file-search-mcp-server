#!/bin/bash

# Startup script for Cloud Run

set -e

echo "Starting Gemini File Search MCP Server..."
echo "PORT: ${PORT:-8080}"
echo "Python version: $(python --version)"

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY is not set"
    exit 1
fi

echo "GEMINI_API_KEY is set"

# Start the server
exec uvicorn src.http_server:app \
    --host 0.0.0.0 \
    --port "${PORT:-8080}" \
    --log-level info \
    --access-log
