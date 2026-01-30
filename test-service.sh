#!/bin/bash

# Test service availability with retry logic

SERVICE_URL="https://sentimentradar.ai-builders.space/"
MAX_RETRIES=3
RETRY_DELAY=10

echo "🔍 Testing service: $SERVICE_URL"
echo ""

for i in $(seq 1 $MAX_RETRIES); do
    echo "Attempt $i/$MAX_RETRIES..."
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$SERVICE_URL")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Service is responding (HTTP $HTTP_CODE)"
        echo ""
        echo "🌐 Service is available at: $SERVICE_URL"
        exit 0
    elif [ "$HTTP_CODE" = "503" ]; then
        echo "⚠️  Got 503 - Service might be waking up from sleep"
        if [ $i -lt $MAX_RETRIES ]; then
            echo "   Waiting ${RETRY_DELAY}s before retry..."
            sleep $RETRY_DELAY
        fi
    else
        echo "❌ Got HTTP $HTTP_CODE"
        if [ $i -lt $MAX_RETRIES ]; then
            echo "   Retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
        fi
    fi
done

echo ""
echo "❌ Service not responding after $MAX_RETRIES attempts"
echo "   Check deployment status: ./check-deployment.sh"
exit 1
