#!/bin/bash

# Test Docker build and run for Sentiment Alpha Radar

set -e

echo "🐳 Testing Docker for Sentiment Alpha Radar..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop or Docker daemon."
    exit 1
fi

echo "✅ Docker is installed and running"
echo ""

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t sentiment-radar:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo ""
    
    # Test running the container
    echo "🚀 Testing container startup..."
    echo "   Starting container in detached mode..."
    
    # Stop and remove existing container if it exists
    docker stop sentiment-radar-test 2>/dev/null || true
    docker rm sentiment-radar-test 2>/dev/null || true
    
    # Run container
    docker run -d \
        --name sentiment-radar-test \
        -p 8000:8000 \
        --env-file .env.example \
        sentiment-radar:latest
    
    if [ $? -eq 0 ]; then
        echo "✅ Container started successfully!"
        echo ""
        echo "⏳ Waiting for container to be ready..."
        sleep 5
        
        # Test health endpoint
        echo "🏥 Testing health endpoint..."
        if curl -f http://localhost:8000/ > /dev/null 2>&1; then
            echo "✅ Application is responding!"
            echo ""
            echo "📊 Container status:"
            docker ps --filter "name=sentiment-radar-test" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            echo ""
            echo "🌐 Application is available at: http://localhost:8000"
            echo ""
            echo "To stop the test container, run:"
            echo "  docker stop sentiment-radar-test"
            echo "  docker rm sentiment-radar-test"
        else
            echo "⚠️  Container is running but application may not be ready yet."
            echo "   Check logs with: docker logs sentiment-radar-test"
        fi
    else
        echo "❌ Failed to start container"
        exit 1
    fi
else
    echo "❌ Docker build failed"
    exit 1
fi
