#!/bin/bash

PORT=${1:-8080}

echo "Liveness Client running at:"
echo "  Local:   http://localhost:$PORT"
echo "  Network: http://$(hostname -I | awk '{print $1}'):$PORT"
echo ""
echo "Press Ctrl+C to stop"

python3 -m http.server "$PORT" --directory "$(dirname "$0")"
