#!/bin/bash

# Liveness Detection Server
# Usage: ./run.sh [dev|prod]

MODE=${1:-dev}

echo "🚀 Starting Liveness Detection Server..."
echo "Mode: $MODE"
echo ""

if [ "$MODE" == "prod" ]; then
    # Production mode with gunicorn
    echo "Production mode - 4 workers"
    gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
else
    # Development mode with auto-reload
    echo "Development mode - auto-reload enabled"
    uvicorn app:app --host 0.0.0.0 --port 8001 --reload
fi
