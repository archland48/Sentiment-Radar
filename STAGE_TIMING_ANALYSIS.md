# Stage Timing Analysis

## Overview

This document analyzes which stage takes the most time in the `/scan` endpoint.

## Stage Breakdown

### Stage 1: Broad Scan (Tweet Discovery)

**Operations:**
1. Keyword expansion (yfinance/OpenFIGI API calls)
2. X API queries (Bearer Token auth + API calls)
3. Filter tweets (past 3 days, verified accounts)
4. Calculate popularity scores
5. Sort and select top tweets

**Time Components:**
- Keyword expansion: ~0.5-2 seconds per keyword
- X API authentication: ~0.1s (Bearer Token) or 1-3s (OAuth 2.0)
- X API queries: ~2-5 seconds per keyword
- Filtering & sorting: < 0.1 seconds (local operations)

**Typical Duration:**
- **Best case**: 3-8 seconds (Bearer Token, fast API)
- **Typical case**: 5-15 seconds (Bearer Token, normal API)
- **Worst case**: 8-20 seconds (OAuth 2.0, slow API)

**Bottlenecks:**
- X API query time (network latency)
- Multiple keyword queries (if not optimized)

### Stage 2: Deep Dive Analysis

**Operations:**
1. For each tweet from Stage 1:
   - LLM call to `perform_deep_dive_analysis()`
   - Extract URLs from tweet text
   - Add metadata (x_url, tweet_urls)
2. Generate aggregate insights
3. Generate AI-powered insights (additional LLM call)

**Time Components:**
- LLM call per tweet: ~2-6 seconds each
- Delay between calls: 0.3 seconds
- AI insights generation: ~3-8 seconds
- Data processing: < 0.1 seconds

**Typical Duration (for 3 tweets):**
- **Best case**: 9-20 seconds (3 tweets × 2s + 0.9s delay + 3s insights)
- **Typical case**: 12-28 seconds (3 tweets × 3-4s + 0.9s delay + 5s insights)
- **Worst case**: 20-40 seconds (3 tweets × 5-6s + 0.9s delay + 8s insights)

**Bottlenecks:**
- **Sequential LLM calls** (biggest bottleneck)
- Each tweet analyzed one at a time
- LLM response time varies (2-6 seconds per call)

## Comparison

### Current Configuration (3 tweets, Bearer Token)

| Stage | Best Case | Typical | Worst Case | Percentage |
|-------|-----------|---------|------------|------------|
| **Stage 1** | 3-8s | 5-15s | 8-20s | ~30-40% |
| **Stage 2** | 9-20s | 12-28s | 20-40s | ~60-70% |
| **Total** | 12-28s | 17-43s | 28-60s | 100% |

### Key Finding

**Stage 2 is the bottleneck** - It takes **60-70% of total processing time**

**Reasons:**
1. **Sequential LLM calls**: Each tweet analyzed one at a time
2. **LLM latency**: Each call takes 2-6 seconds
3. **Multiple operations**: Deep dive + insights generation
4. **No parallelization**: All calls are sequential

## Detailed Breakdown

### Stage 1 Time Distribution

```
Keyword Expansion:     ████░░░░░░ 20% (0.5-2s)
X API Auth:           █░░░░░░░░░  5% (0.1s with Bearer Token)
X API Queries:        ████████░░ 60% (2-5s per keyword)
Filtering/Sorting:    █░░░░░░░░░  5% (<0.1s)
Other:                ██░░░░░░░░ 10%
```

### Stage 2 Time Distribution

```
LLM Calls (per tweet): ████████████████████ 75% (2-6s × 3 = 6-18s)
Delays:                ██░░░░░░░░░░░░░░░░░░  5% (0.3s × 3 = 0.9s)
AI Insights:          █████░░░░░░░░░░░░░░░ 15% (3-8s)
Data Processing:       █░░░░░░░░░░░░░░░░░░  5% (<0.1s)
```

## Optimization Opportunities

### Stage 1 Optimizations (Already Implemented)
- ✅ Use Bearer Token (saves 1-3s)
- ✅ Merge keyword queries (reduces API calls)
- ✅ Filter before ranking (reduces processing)

### Stage 2 Optimizations (Potential)

#### Option 1: Parallel LLM Calls ⚡ (Biggest Impact)
```python
# Current: Sequential (slow)
for tweet in tweets:
    analysis = await perform_deep_dive_analysis(...)

# Optimized: Parallel (fast)
analyses = await asyncio.gather(*[
    perform_deep_dive_analysis(tweet_text, ...)
    for tweet in tweets
])
```
**Time Saved**: 6-12 seconds (reduces Stage 2 by 50-60%)

#### Option 2: Reduce Tweet Count
```python
max_tweets: 2  # Instead of 3
```
**Time Saved**: 2-6 seconds per tweet removed

#### Option 3: Skip AI Insights (Optional)
```python
if options.get("skip_ai_insights"):
    ai_insights = []
```
**Time Saved**: 3-8 seconds

#### Option 4: Reduce Delay Between Calls
```python
await asyncio.sleep(0.1)  # Instead of 0.3s
```
**Time Saved**: 0.6 seconds (for 3 tweets)

## Recommendations

### Immediate (Easy)
1. ✅ **Already done**: Use Bearer Token
2. ✅ **Already done**: Reduce max_tweets to 3
3. ⚠️ **Consider**: Reduce delay to 0.1s (if API allows)

### Medium Priority
1. ⚠️ **Implement parallel LLM calls** (biggest impact)
   - Could reduce Stage 2 time by 50-60%
   - Total time: 17-43s → 11-25s

### Long Term
1. ⚠️ **Background job processing**
   - Return immediately with job ID
   - Poll for results
   - Prevents timeout completely

## Expected Times After Optimization

### With Parallel LLM Calls

| Stage | Current | Optimized | Improvement |
|-------|---------|-----------|-------------|
| Stage 1 | 5-15s | 5-15s | 0% (already optimized) |
| Stage 2 | 12-28s | 6-15s | **50-60% faster** |
| **Total** | **17-43s** | **11-30s** | **35-50% faster** |

## Conclusion

**Stage 2 (Deep Dive Analysis) is the bottleneck**, taking 60-70% of total time.

**Main cause**: Sequential LLM calls (each tweet analyzed one at a time)

**Best optimization**: Implement parallel LLM calls to reduce Stage 2 time by 50-60%
