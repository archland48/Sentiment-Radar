#!/bin/bash

# Monitor Sentiment Radar deployment and processing

set -e

SERVICE_URL="https://sentimentradar.ai-builders.space"
SERVICE_NAME="sentimentradar"
API_BASE="https://space.ai-builders.com/backend"

echo "🔍 Monitoring Sentiment Radar: $SERVICE_URL"
echo "======================================================================"
echo ""

# Load environment variables (skip comments and invalid lines)
if [ -f .env ]; then
    # Only export lines that contain = and don't start with #
    while IFS= read -r line; do
        # Skip empty lines and comments
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
            continue
        fi
        # Only process lines with =
        if [[ "$line" =~ = ]]; then
            export "$line" 2>/dev/null || true
        fi
    done < .env
fi

if [ -z "$AI_BUILDER_TOKEN" ]; then
    echo "❌ AI_BUILDER_TOKEN not found. Please set it in .env file"
    exit 1
fi

# Function to check deployment status
check_deployment() {
    echo "📊 Deployment Status:"
    echo "----------------------------------------------------------------------"
    
    response=$(curl -s -X GET \
        "$API_BASE/v1/deployments/$SERVICE_NAME" \
        -H "Authorization: Bearer $AI_BUILDER_TOKEN" \
        -H "Content-Type: application/json")
    
    status=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    koyeb_status=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('koyeb_status', 'N/A'))" 2>/dev/null || echo "N/A")
    public_url=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('public_url', 'N/A'))" 2>/dev/null || echo "N/A")
    
    echo "Status: $status"
    echo "Koyeb Status: $koyeb_status"
    echo "Public URL: $public_url"
    echo ""
}

# Function to check service health
check_health() {
    echo "🏥 Service Health:"
    echo "----------------------------------------------------------------------"
    
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$SERVICE_URL/health" 2>/dev/null || echo "000")
    
    if [ "$http_code" = "200" ]; then
        health_data=$(curl -s --max-time 10 "$SERVICE_URL/health" 2>/dev/null || echo "{}")
        echo "✅ Service is healthy (HTTP $http_code)"
        echo "$health_data" | python3 -m json.tool 2>/dev/null || echo "$health_data"
    else
        echo "⚠️  Service health check failed (HTTP $http_code)"
    fi
    echo ""
}

# Function to get recent logs
get_logs() {
    echo "📋 Recent Runtime Logs (last 50 lines):"
    echo "----------------------------------------------------------------------"
    
    response=$(curl -s -X GET \
        "$API_BASE/v1/deployments/$SERVICE_NAME/logs?log_type=runtime&timeout=5" \
        -H "Authorization: Bearer $AI_BUILDER_TOKEN" \
        -H "Content-Type: application/json")
    
    logs=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('logs', ''))" 2>/dev/null || echo "")
    
    if [ -n "$logs" ]; then
        echo "$logs" | tail -50
    else
        echo "No logs available"
    fi
    echo ""
}

# Function to test a scan request
test_scan() {
    echo "🧪 Testing Scan Request:"
    echo "----------------------------------------------------------------------"
    echo "Sending test request with keyword: AAPL"
    echo ""
    
    start_time=$(date +%s)
    
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" \
        -X POST "$SERVICE_URL/scan" \
        -H "Content-Type: application/json" \
        -d '{
            "keywords": ["AAPL"],
            "max_tweets": 2,
            "options": {
                "skip_ai_insights": true,
                "skip_keyword_expansion": true
            }
        }' \
        --max-time 60)
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    curl_time=$(echo "$response" | grep "TIME:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d' | sed '/TIME:/d')
    
    echo "HTTP Status: $http_code"
    echo "Total Time: ${duration}s"
    echo "Curl Time: ${curl_time}s"
    echo ""
    
    if [ "$http_code" = "200" ]; then
        echo "✅ Scan completed successfully"
        echo ""
        echo "Response Summary:"
        echo "$body" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'stage1' in data:
        s1 = data['stage1']
        s2 = data['stage2']
        print(f\"Stage 1 Duration: {s1.get('duration_ms', 0)/1000:.2f}s\")
        print(f\"Stage 2 Duration: {s2.get('duration_ms', 0)/1000:.2f}s\")
        print(f\"Total Duration: {data.get('total_duration_ms', 0)/1000:.2f}s\")
        print(f\"Stage 1 Status: {s1.get('status', 'unknown')}\")
        print(f\"Stage 2 Status: {s2.get('status', 'unknown')}\")
        if 'result' in s1.get('result', {}):
            tweets = s1['result'].get('tweets', [])
            print(f\"Tweets Found: {len(tweets)}\")
except:
    print('Could not parse response')
" 2>/dev/null || echo "Could not parse response"
    elif [ "$http_code" = "504" ]; then
        echo "❌ Gateway Timeout (504)"
        echo "   Request took too long (> 30-60 seconds)"
        echo "   Check logs above for which stage is slow"
    elif [ "$http_code" = "503" ]; then
        echo "⚠️  Service Unavailable (503)"
        echo "   Service may be waking up from sleep"
        echo "   Wait 10 seconds and retry"
    else
        echo "❌ Error: HTTP $http_code"
        echo "Response:"
        echo "$body" | head -20
    fi
    echo ""
}

# Main monitoring loop
main() {
    check_deployment
    check_health
    get_logs
    
    read -p "Run test scan? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_scan
    fi
    
    echo "======================================================================"
    echo "Monitoring complete. Run again to check updates."
}

main
