# Most Popular Metrics in Sentiment Alpha Radar

## Overview
Based on the application's implementation, here are the metrics tracked and their popularity/importance:

## 🏆 Top Metrics (Most Popular/Important)

### 1. **Average Sentiment Score** ⭐⭐⭐⭐⭐
- **What it is**: Average sentiment across all analyzed tweets (-1 to 1)
- **Where shown**: Summary card (prominently displayed)
- **Why popular**: 
  - Single number that summarizes overall market sentiment
  - Easy to understand and compare
  - Most actionable for trading decisions
- **Usage**: Primary KPI for sentiment analysis

### 2. **Likes & Retweets** ⭐⭐⭐⭐⭐
- **What it is**: Engagement metrics showing tweet popularity
- **Where shown**: 
  - Broad Scan Report (top 10 tweets)
  - Individual tweet cards
- **Why popular**:
  - Indicates tweet reach and influence
  - Popular tweets = more significant sentiment impact
  - Standard social media engagement metrics
- **Usage**: Filters for "most popular" tweets, validates tweet importance

### 3. **Positive/Negative/Neutral Counts** ⭐⭐⭐⭐
- **What it is**: Number of tweets in each sentiment category
- **Where shown**: Summary card
- **Why popular**:
  - Shows sentiment distribution
  - Helps understand sentiment balance
  - Easy to visualize (positive vs negative)
- **Usage**: Quick sentiment overview

### 4. **Sentiment Score (Per Tweet)** ⭐⭐⭐⭐
- **What it is**: Individual tweet sentiment (-1 to 1)
- **Where shown**: Each tweet card with sentiment badge
- **Why popular**:
  - Granular analysis per tweet
  - Helps identify outliers
  - Shows sentiment variation
- **Usage**: Detailed tweet-level analysis

### 5. **Importance Rating (Deep Dive)** ⭐⭐⭐⭐
- **What it is**: Strategic importance: "High", "Medium", "Low"
- **Where shown**: Deep Dive Report
- **Why popular**:
  - Prioritizes URLs/content by strategic value
  - Helps focus on most relevant information
  - Actionable for decision-making
- **Usage**: Filters content by strategic relevance

## 📊 Secondary Metrics

### 6. **Total Tweets Analyzed** ⭐⭐⭐
- Shows volume of data processed
- Helps understand sample size

### 7. **Sentiment Confidence** ⭐⭐⭐
- Indicates reliability of sentiment analysis
- Used for AI enhancement decisions

### 8. **URLs Analyzed** ⭐⭐
- Shows depth of analysis
- Part of Deep Dive Report

### 9. **Processing Time** ⭐⭐
- Performance metric
- Less relevant for end users

## 🎯 Most Popular Metrics by Use Case

### For Trading Decisions:
1. **Average Sentiment Score** (most important)
2. **Positive/Negative Counts**
3. **Likes & Retweets** (validates importance)

### For Content Discovery:
1. **Likes & Retweets** (finds popular content)
2. **Importance Rating** (strategic relevance)
3. **Sentiment Score** (content tone)

### For Trend Analysis:
1. **Average Sentiment Score** (overall trend)
2. **Positive/Negative Counts** (sentiment shift)
3. **Total Tweets Analyzed** (sample size)

## 💡 Recommendations

### Most Valuable Metrics to Track:
1. **Average Sentiment Score** - Core metric
2. **Engagement Metrics (Likes/Retweets)** - Popularity indicator
3. **Sentiment Distribution (Pos/Neg/Neu)** - Balance indicator
4. **Importance Rating** - Strategic relevance

### Metrics to Consider Adding:
- **Sentiment Trend** (change over time)
- **Engagement Rate** (likes + retweets per tweet)
- **Influence Score** (author follower count × engagement)
- **Sentiment Volatility** (standard deviation of scores)
- **Keyword Frequency** (most mentioned terms)

## Current Implementation Priority

Based on UI prominence and code usage:

1. **Average Sentiment Score** - Featured in summary
2. **Likes & Retweets** - Shown in Broad Scan and tweets
3. **Sentiment Counts** - Featured in summary
4. **Importance Rating** - Featured in Deep Dive Report
5. **Individual Sentiment Scores** - Shown per tweet

These are the metrics users see most prominently and are most actionable for financial sentiment analysis.
