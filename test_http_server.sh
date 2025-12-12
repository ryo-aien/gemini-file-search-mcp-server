#!/bin/bash

# Test HTTP server locally before deploying

echo "Testing HTTP server locally..."

# Set test environment variables
export GEMINI_API_KEY="${GEMINI_API_KEY:-test-key}"
export PORT=8080

# Start the server in background
python -m uvicorn src.http_server:app --host 0.0.0.0 --port 8080 &
SERVER_PID=$!

echo "Server started with PID: $SERVER_PID"

# Wait for server to start
sleep 5

# Test health endpoint
echo ""
echo "Testing /health endpoint..."
curl -v http://localhost:8080/health

# Test root endpoint
echo ""
echo ""
echo "Testing / endpoint..."
curl -v http://localhost:8080/

# Kill the server
echo ""
echo ""
echo "Stopping server..."
kill $SERVER_PID

echo "Test complete!"
