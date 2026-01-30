#!/bin/bash

# Check deployment status for Sentiment Radar

set -e

SERVICE_NAME="sentimentradar"
API_BASE="https://space.ai-builders.com/backend"

echo "🔍 Checking deployment status for $SERVICE_NAME..."
echo ""

# Check if we have the API token
if [ -z "$AI_BUILDER_TOKEN" ]; then
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    else
        echo "❌ AI_BUILDER_TOKEN not found. Please set it in .env file"
        exit 1
    fi
fi

# Check deployment status
response=$(curl -s -X GET \
    "$API_BASE/v1/deployments/$SERVICE_NAME" \
    -H "Authorization: Bearer $AI_BUILDER_TOKEN" \
    -H "Content-Type: application/json")

# Parse and display status
status=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null || echo "unknown")
public_url=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('public_url', 'N/A'))" 2>/dev/null || echo "N/A")
message=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('message', ''))" 2>/dev/null || echo "")

echo "Status: $status"
echo "Public URL: $public_url"
if [ -n "$message" ]; then
    echo ""
    echo "Message: $message"
fi

echo ""
if [ "$status" = "HEALTHY" ]; then
    echo "✅ Deployment is healthy!"
    echo "🌐 Your application is available at: $public_url"
elif [ "$status" = "deploying" ] || [ "$status" = "queued" ]; then
    echo "⏳ Deployment is still in progress..."
    echo "   This usually takes 5-10 minutes."
    echo "   Run this script again to check status."
else
    echo "⚠️  Deployment status: $status"
    echo "   Check logs or contact support if issues persist."
fi
