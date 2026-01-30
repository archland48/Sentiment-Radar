# Quick Fix for 504 Errors

## Immediate Solutions

### Solution 1: Use 1 Tweet (Fastest Fix)

The default is now 2 tweets. To use 1 tweet:

**In Frontend** (static/index.html):
- The frontend will use the default from backend (currently 2)
- Or modify the request to explicitly set `max_tweets: 1`

**Expected Time**: 7-18 seconds (much less likely to timeout)

### Solution 2: Skip AI Insights

Add to request options:
```json
{
  "keywords": ["AAPL"],
  "max_tweets": 2,
  "options": {
    "skip_ai_insights": true
  }
}
```

**Time Saved**: 3-8 seconds

### Solution 3: Check Actual Processing Time

Add logging to see what's slow:
```python
print(f"Stage 1 took: {stage1_duration}ms")
print(f"Stage 2 took: {stage2_duration}ms")
print(f"Total: {total_duration}ms")
```

## Current Configuration

- **Default tweets**: 2 (reduced from 3)
- **Parallel LLM**: ✅ Enabled
- **Timeouts**: ✅ 6s per LLM call, 10s for insights
- **Max tokens**: 200 (reduced from 300)

## Expected Times

| Configuration | Stage 1 | Stage 2 | Total |
|---------------|---------|---------|-------|
| **2 tweets, with insights** | 5-15s | 4-12s | 9-27s |
| **2 tweets, no insights** | 5-15s | 2-8s | 7-23s |
| **1 tweet, with insights** | 5-15s | 2-6s | 7-21s |
| **1 tweet, no insights** | 5-15s | 1-3s | 6-18s |

## If Still Timing Out

1. **Check X API**: May be slow (5-20s)
2. **Check LLM API**: May be slow (2-6s per call)
3. **Use Mock Data**: For testing only
4. **Implement Background Jobs**: For production

## Debug Steps

1. Check deployment logs for actual times
2. Test with mock data (instant)
3. Test with 1 tweet
4. Test without AI insights
5. Check if X API is slow
