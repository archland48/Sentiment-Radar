# Weighted Engagement Metrics for Sentiment Monitoring

## Overview
The application now uses **weighted engagement metrics** to adjust sentiment scores based on tweet popularity and engagement. This ensures that more influential tweets have greater impact on sentiment analysis.

## Engagement Variables

### 1. **Views** 👁️
- **Weight**: 0.1 (10%)
- **Why low weight**: Views indicate exposure but don't directly indicate sentiment agreement
- **Use case**: Shows reach but minimal sentiment signal

### 2. **Likes** ❤️
- **Weight**: 0.3 (30%)
- **Why medium weight**: Likes indicate agreement/positive sentiment
- **Use case**: Strong indicator of sentiment alignment

### 3. **Retweets** 🔄
- **Weight**: 0.6 (60%)
- **Why high weight**: Retweets indicate strong agreement and active sharing of sentiment
- **Use case**: Most significant indicator of sentiment impact

## Weighted Sentiment Calculation

### Formula
```
Weighted Engagement Score = (Views × 0.1) + (Likes × 0.3) + (Retweets × 0.6)

Weighted Sentiment = Σ(Sentiment Score × Weighted Engagement) / Σ(Weighted Engagement)
```

### Example
Tweet A:
- Sentiment: +0.8 (positive)
- Views: 10,000 (weight: 0.1)
- Likes: 500 (weight: 0.3)
- Retweets: 100 (weight: 0.6)
- Weighted Engagement: (10,000 × 0.1) + (500 × 0.3) + (100 × 0.6) = 1,000 + 150 + 60 = 1,210
- Contribution: 0.8 × 1,210 = 968

Tweet B:
- Sentiment: -0.5 (negative)
- Views: 1,000 (weight: 0.1)
- Likes: 20 (weight: 0.3)
- Retweets: 5 (weight: 0.6)
- Weighted Engagement: (1,000 × 0.1) + (20 × 0.3) + (5 × 0.6) = 100 + 6 + 3 = 109
- Contribution: -0.5 × 109 = -54.5

**Weighted Average**: (968 - 54.5) / (1,210 + 109) = 913.5 / 1,319 = **+0.693**

## Metrics Displayed

### Summary Card
1. **Weighted Average Sentiment** (primary metric)
   - Engagement-weighted average sentiment score
   - More accurate for sentiment monitoring
   
2. **Unweighted Average Sentiment** (shown for comparison)
   - Simple mean of all sentiment scores
   - Useful for comparison

3. **Weighted Positive/Negative/Neutral**
   - Engagement-weighted counts
   - Shows influence-weighted sentiment distribution

### Individual Tweets
- **Views**: 👁️ count
- **Likes**: ❤️ count
- **Retweets**: 🔄 count
- **Weighted Engagement Score**: ⚖️ (calculated score)

## Why Weighted Metrics Matter

### For Sentiment Monitoring:
1. **More Accurate**: Popular tweets have more impact on market sentiment
2. **Influence-Based**: Reflects actual reach and engagement
3. **Better Decisions**: Weighted metrics better represent true sentiment impact

### Example Scenario:
- 1 viral tweet (10K retweets, positive sentiment) vs 100 small tweets (10 retweets each, mixed sentiment)
- **Unweighted**: Averages all tweets equally
- **Weighted**: Gives more weight to the viral tweet (more accurate for sentiment monitoring)

## Configuration

Engagement weights are defined in `main.py`:
```python
ENGAGEMENT_WEIGHTS = {
    "views": 0.1,      # Low: Just exposure
    "likes": 0.3,     # Medium: Indicates agreement
    "retweets": 0.6    # High: Strong agreement/sharing
}
```

These weights can be adjusted based on your sentiment monitoring objectives.

## Best Practices

1. **Monitor Weighted Average**: Primary metric for sentiment analysis
2. **Compare with Unweighted**: Helps identify if sentiment is driven by popular vs. many small tweets
3. **Check Weighted Engagement**: High engagement tweets have more influence
4. **Review Individual Scores**: Understand which tweets drive the weighted average
