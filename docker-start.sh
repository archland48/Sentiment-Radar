#!/bin/bash

# Start Docker container for Sentiment Alpha Radar

set -e

echo "🐳 Starting Sentiment Alpha Radar Docker container..."
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^sentiment-radar$"; then
    echo "📦 Found existing container. Stopping and removing..."
    docker stop sentiment-radar 2>/dev/null || true
    docker rm sentiment-radar 2>/dev/null || true
fi

# Build image if needed
if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^sentiment-radar:latest$"; then
    echo "🔨 Building Docker image..."
    docker build -t sentiment-radar:latest .
fi

# Start container
echo "🚀 Starting container..."
docker run -d \
    --name sentiment-radar \
    -p 8000:8000 \
    --env-file .env \
    sentiment-radar:latest

if [ $? -eq 0 ]; then
    echo "✅ Container started successfully!"
    echo ""
    echo "⏳ Waiting for application to start..."
    sleep 5
    
    # Check container status
    echo ""
    echo "📊 Container Status:"
    docker ps --filter "name=sentiment-radar" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    # Check logs
    echo "📋 Recent Logs:"
    docker logs sentiment-radar --tail 10
    echo ""
    
    # Test health endpoint
    if curl -f http://localhost:8000/ > /dev/null 2>&1; then
        echo "✅ Application is running and responding!"
        echo ""
        echo "🌐 Access the application at:"
        echo "   Frontend: http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs"
        echo ""
        echo "To view logs: docker logs -f sentiment-radar"
        echo "To stop: docker stop sentiment-radar"
        echo "To remove: docker rm sentiment-radar"
    else
        echo "⚠️  Container is running but application may still be starting..."
        echo "   Check logs with: docker logs sentiment-radar"
    fi
else
    echo "❌ Failed to start container"
    exit 1
fi
