# Troubleshooting HTTP 504 Gateway Timeout Errors

## Common Causes

### 1. Long Processing Time (Most Common)

The `/scan` endpoint performs multiple operations that can take time:
- **Stage 1**: X API queries (OAuth token exchange + API calls)
- **Stage 2**: Deep Dive Analysis (LLM calls for each tweet)

**Typical Processing Times:**
- Stage 1: 5-15 seconds (X API queries)
- Stage 2: 10-30 seconds (5 tweets × 2-6 seconds per LLM call)
- **Total: 15-45 seconds**

**Gateway Timeout Limits:**
- Koyeb: Usually 30-60 seconds
- If processing exceeds this, you get 504

### 2. X API OAuth Token Exchange Delay

**Symptoms:**
- First request after inactivity takes longer
- OAuth 2.0 token exchange adds 1-3 seconds

**Solution:**
- Use Bearer Token directly (faster)
- Cache OAuth tokens (if possible)

### 3. Multiple Sequential LLM Calls

**Problem:**
- Stage 2 calls LLM for each tweet sequentially
- 5 tweets × 2-6 seconds = 10-30 seconds
- Plus 0.5s delay between calls

**Solution:**
- Reduce number of tweets analyzed
- Implement parallel processing (if API supports)
- Add timeout handling

## Solutions

### Solution 1: Reduce Processing Time

#### Option A: Reduce Number of Tweets
```python
# In ScanRequest model
max_tweets: Optional[int] = 3  # Instead of 5
```

#### Option B: Skip Deep Dive for Testing
```python
# Add option to skip Stage 2
options = {"skip_deep_dive": True}
```

#### Option C: Use Bearer Token (Faster)
```bash
# In .env - Bearer Token is faster than OAuth 2.0
TWITTER_BEARER_TOKEN=your_token_here
```

### Solution 2: Add Timeout Handling

Add timeout to prevent hanging requests:

```python
import asyncio

@app.post("/scan")
async def run_thoughts_scan(request: ScanRequest):
    try:
        # Set overall timeout (e.g., 50 seconds)
        result = await asyncio.wait_for(
            perform_scan(request),
            timeout=50.0
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Request timeout. Processing took too long."
        )
```

### Solution 3: Implement Async Processing

For long-running scans, consider:
1. **Background Jobs**: Queue the scan, return immediately
2. **Webhooks**: Notify when scan completes
3. **Polling**: Check status endpoint periodically

### Solution 4: Optimize API Calls

#### Parallel LLM Calls (if supported)
```python
# Instead of sequential:
for tweet in tweets:
    analysis = await perform_deep_dive_analysis(...)

# Use asyncio.gather for parallel:
analyses = await asyncio.gather(*[
    perform_deep_dive_analysis(tweet_text, ...)
    for tweet in tweets
])
```

#### Cache OAuth Tokens
```python
# Cache token for reuse
_oauth_token_cache = None
_token_expires_at = None

async def get_bearer_token():
    global _oauth_token_cache, _token_expires_at
    if _oauth_token_cache and datetime.now() < _token_expires_at:
        return _oauth_token_cache
    # ... exchange token ...
    _oauth_token_cache = token
    _token_expires_at = datetime.now() + timedelta(hours=2)
    return token
```

## Quick Fixes

### Immediate: Reduce Tweet Count
```bash
# In frontend, reduce max_tweets
max_tweets: 3  # Instead of 5
```

### Immediate: Use Bearer Token
```bash
# In .env - faster than OAuth 2.0
TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAKEv7QEAAAAAFjZlodrV3qQSTHWQIssSS6BIrdo%3D1S5aQkN5Du2PsW0VgoS99OacTVm9B00p68fBjpXqXJDP8FdHNW
```

### Immediate: Add Timeout to Frontend
```javascript
// In static/index.html
const response = await fetch('/scan', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(requestData),
    signal: AbortSignal.timeout(60000) // 60 second timeout
});
```

## Monitoring

### Check Processing Time
```python
# Add timing logs
start_time = datetime.now()
# ... processing ...
duration = (datetime.now() - start_time).total_seconds()
print(f"Total processing time: {duration}s")
```

### Check Which Stage is Slow
```python
# Log each stage duration
print(f"Stage 1 duration: {stage1_duration}ms")
print(f"Stage 2 duration: {stage2_duration}ms")
```

## Expected Processing Times

### Best Case (Mock Data)
- Stage 1: < 1 second
- Stage 2: 5-10 seconds (5 tweets)
- **Total: 6-11 seconds** ✅

### Typical Case (X API + LLM)
- Stage 1: 5-15 seconds (X API queries)
- Stage 2: 10-30 seconds (5 tweets × LLM calls)
- **Total: 15-45 seconds** ⚠️

### Worst Case (Slow APIs)
- Stage 1: 20-30 seconds (slow X API)
- Stage 2: 30-60 seconds (slow LLM)
- **Total: 50-90 seconds** ❌ (Will timeout)

## Recommendations

1. **For Production**: Implement background job processing
2. **For Testing**: Use mock data or reduce tweet count
3. **For Speed**: Use Bearer Token instead of OAuth 2.0
4. **For Reliability**: Add timeout handling and error recovery

## Next Steps

1. ✅ Check current processing times in logs
2. ✅ Reduce `max_tweets` to 3 for faster processing
3. ✅ Ensure Bearer Token is configured (faster than OAuth)
4. ⚠️ Consider implementing background jobs for production
