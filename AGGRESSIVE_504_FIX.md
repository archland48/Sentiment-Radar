# Aggressive 504 Timeout Fix

## Current Optimizations Applied

1. ✅ Parallel LLM calls (Stage 2)
2. ✅ Reduced max_tweets: 3 → 2
3. ✅ Added timeout to LLM calls: 6 seconds
4. ✅ Reduced max_tokens: 300 → 200
5. ✅ Added timeout to AI insights: 10 seconds
6. ✅ Option to skip AI insights

## If Still Getting 504 Errors

### Option 1: Reduce to 1 Tweet (Fastest)

Update `.env` or frontend to use:
```python
max_tweets: 1
```

**Expected Time**: 7-18 seconds total

### Option 2: Skip AI Insights Completely

In frontend, add to request:
```javascript
{
  keywords: ["AAPL"],
  max_tweets: 2,
  options: {
    skip_ai_insights: true  // Saves 3-8 seconds
  }
}
```

**Expected Time**: 6-20 seconds total

### Option 3: Use Mock Data for Testing

```bash
# In .env
USE_MOCK_DATA=true
```

**Expected Time**: < 5 seconds total

### Option 4: Implement Background Jobs

For production, implement async processing:
1. Return immediately with job ID
2. Process in background
3. Poll for results

## Quick Test

Test with minimal configuration:
```bash
# Test with 1 tweet, skip insights
curl -X POST https://sentimentradar.ai-builders.space/scan \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AAPL"],
    "max_tweets": 1,
    "options": {"skip_ai_insights": true}
  }'
```

## Monitoring

Check actual processing times in logs:
- Look for `duration_ms` in response
- Compare Stage 1 vs Stage 2 times
- Identify which stage is slow

## Next Steps

1. Test with 1 tweet first
2. If still timeout, skip AI insights
3. If still timeout, check X API response times
4. Consider implementing background jobs
