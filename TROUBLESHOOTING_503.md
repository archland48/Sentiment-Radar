# Troubleshooting HTTP 503 Errors

## Common Causes

### 1. Service Deep Sleep (Most Common)

Koyeb free tier services enter "deep sleep" after 300 seconds (5 minutes) of inactivity.

**Symptoms:**
- First request after inactivity returns 503
- Subsequent requests work fine
- Logs show "Waking up from deep sleep"

**Solution:**
- Wait 5-10 seconds and retry the request
- The service automatically wakes up when receiving requests
- Consider implementing a health check ping to keep service awake

### 2. Service Restarting

**Symptoms:**
- Intermittent 503 errors
- Logs show "Instance is stopping" and "Instance created"

**Solution:**
- Wait for service to fully restart (usually 30-60 seconds)
- Check deployment status: `./check-deployment.sh`

### 3. Health Check Failure

**Symptoms:**
- Persistent 503 errors
- Logs show health check failures

**Solution:**
- Check application logs for startup errors
- Verify PORT environment variable is honored
- Ensure application responds to `/` endpoint

## Quick Diagnostics

### Check Deployment Status
```bash
./check-deployment.sh
```

### Check Service Logs
```bash
python3 -c "
import httpx
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('AI_BUILDER_TOKEN')
response = httpx.get(
    'https://space.ai-builders.com/backend/v1/deployments/sentimentradar/logs?log_type=runtime&timeout=5',
    headers={'Authorization': f'Bearer {token}'},
    timeout=15.0
)
data = response.json()
print(data.get('logs', '')[-1000:])  # Last 1000 chars
"
```

### Test Service Directly
```bash
curl -v https://sentimentradar.ai-builders.space/
```

## Solutions

### Solution 1: Retry After Deep Sleep

If you see 503, wait 5-10 seconds and retry:
```bash
sleep 10 && curl https://sentimentradar.ai-builders.space/
```

### Solution 2: Keep Service Awake

Add a health check endpoint and ping it periodically:
```python
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

Then ping it every 4 minutes:
```bash
# Using cron or scheduled task
*/4 * * * * curl -s https://sentimentradar.ai-builders.space/health > /dev/null
```

### Solution 3: Check Application Startup

Ensure your application:
- ✅ Honors PORT environment variable
- ✅ Responds to GET / within health check timeout
- ✅ Has no startup errors
- ✅ All dependencies are installed

### Solution 4: Verify Environment Variables

Check that required environment variables are set:
- `AI_BUILDER_TOKEN` (automatically injected by platform)
- `X_API_CLIENT_ID` (if using X API)
- `X_API_CLIENT_SECRET` (if using X API)
- `TWITTER_BEARER_TOKEN` (if using Bearer Token)

## Current Status

Based on logs:
- ✅ Service is HEALTHY
- ✅ Application starts successfully
- ✅ Responds to requests (200 OK)
- ⚠️ Enters deep sleep after 5 minutes of inactivity
- ✅ Automatically wakes up on new requests

## Prevention

1. **Keep Service Active**: Implement periodic health checks
2. **Handle Retries**: Add retry logic in your client code
3. **Monitor Logs**: Regularly check deployment logs
4. **Upgrade Plan**: Consider upgrading to paid tier for always-on service

## Getting Help

If 503 errors persist:
1. Check deployment logs for errors
2. Verify environment variables are set correctly
3. Test locally with Docker to ensure app works
4. Contact support with deployment logs
