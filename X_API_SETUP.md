# X (Twitter) API Integration Setup Guide

## Overview

The application now supports real X (Twitter) API v2 integration for querying tweets. The system will automatically use the real API if configured, otherwise it falls back to mock data.

## Setup Steps

### 1. Get Twitter API Access

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Sign in with your Twitter account
3. Create a new Project and App
4. Navigate to your App's "Keys and Tokens" section
5. Generate a **Bearer Token** (read-only access is sufficient)

### 2. Configure Environment Variable

Add your Bearer Token to the `.env` file:

```bash
TWITTER_BEARER_TOKEN=your_actual_bearer_token_here
```

**Important**: Never commit your `.env` file to version control. It's already in `.gitignore`.

### 3. Install Dependencies

Install the required Python package:

```bash
pip install tweepy==4.14.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 4. Verify Setup

The application will automatically detect if `TWITTER_BEARER_TOKEN` is configured:
- **If configured**: Uses real X API to query tweets
- **If not configured**: Falls back to mock data (for development/testing)

## API Features

### Current Implementation

- **Endpoint**: Twitter API v2 `search_recent_tweets`
- **Query**: Searches for tweets from past 7 days
- **Filters**: 
  - Excludes retweets (`-is:retweet`)
  - English language only (`lang:en`)
- **Fields Retrieved**:
  - Tweet text
  - Created timestamp
  - Public metrics (likes, retweets, views, replies)
  - Author information (username, name)

### Rate Limits

Twitter API v2 Free Tier:
- **Recent Search**: 300 requests per 15 minutes
- **Max results per request**: 100 tweets
- **Rate limit handling**: Automatically waits when limits are hit

### Query Strategy

The application:
1. Expands keywords to all variations (e.g., "AAPL" → ["AAPL", "Apple", "$AAPL"])
2. Queries X API for each variation
3. Combines and deduplicates results
4. Filters to past week
5. Ranks by popularity score
6. Returns top 10 most popular tweets

## Fallback Behavior

If the API is unavailable or not configured:
- Uses mock data from `MOCK_TWEETS_DB`
- Logs a message: "Twitter Bearer Token not configured. Using mock data."
- Application continues to function normally

## Troubleshooting

### "tweepy not installed"
```bash
pip install tweepy==4.14.0
```

### "Twitter API authentication failed"
- Check that `TWITTER_BEARER_TOKEN` is set correctly in `.env`
- Verify your Bearer Token is valid in Twitter Developer Portal
- Ensure token has read permissions

### "Rate limit reached"
- The application automatically waits and retries
- For higher limits, consider upgrading to Twitter API Basic or Pro tier
- Reduce number of keyword variations to query fewer times

### "No tweets found"
- Check that your search query matches real tweets
- Verify date range (searches past 7 days only)
- Try broader keywords or variations

## API Tiers Comparison

| Tier | Monthly Cost | Rate Limits | Features |
|------|-------------|-------------|----------|
| Free | $0 | 300 req/15min | Recent search, basic metrics |
| Basic | $100 | 3,000 req/15min | Recent search, advanced metrics |
| Pro | $5,000 | 10,000 req/15min | Full archive, advanced features |

For most use cases, the Free tier is sufficient for development and testing.

## Security Notes

- **Never commit** `.env` file with real tokens
- **Rotate tokens** periodically for security
- **Use environment variables** in production (not hardcoded values)
- **Monitor API usage** in Twitter Developer Portal

## Example .env File

```bash
# AI Builders API
AI_BUILDER_TOKEN=sk_abfba6d6_...

# Twitter API v2
TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAA...
```

## Next Steps

### Official Twitter API (Required)
1. Set up Twitter Developer account
2. Create app and generate Bearer Token
3. Add token to `.env` file: `TWITTER_BEARER_TOKEN=your_token`
4. Install tweepy: `pip install tweepy`
5. Restart the application
6. Test with a search query

The application will automatically use the configured API!
