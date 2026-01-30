#!/bin/bash

# Stop Docker container for Sentiment Alpha Radar

echo "🛑 Stopping Sentiment Alpha Radar Docker container..."

if docker ps --format '{{.Names}}' | grep -q "^sentiment-radar$"; then
    docker stop sentiment-radar
    echo "✅ Container stopped"
else
    echo "ℹ️  Container is not running"
fi

if docker ps -a --format '{{.Names}}' | grep -q "^sentiment-radar$"; then
    read -p "Remove container? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker rm sentiment-radar
        echo "✅ Container removed"
    fi
fi
