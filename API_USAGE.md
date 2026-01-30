# API Usage Configuration

## Current Configuration

The application is now configured to use **X API** with OAuth 2.0 authentication.

### Environment Variables

```bash
# X API OAuth 2.0 (Active)
X_API_CLIENT_ID=TElmaVV3Vm1idnNxQlJPcWpfbGw6MTpjaQ
X_API_CLIENT_SECRET=M_wkyDt6VSXo1VMwk7-bB_ghXzT_inHG8YOR4NhsIi8a6RtK17

# Data Source Priority
USE_MOCK_DATA=false  # Use X API instead of mock data
USE_SNSCRAPE=false   # Don't use snscrape
```

## Data Source Priority

The application uses the following priority order:

1. **X API (OAuth 2.0)** ✅ **Currently Active**
   - Uses `X_API_CLIENT_ID` and `X_API_CLIENT_SECRET`
   - Automatically exchanges credentials for Bearer Token
   - Queries real tweets from X (Twitter) API v2
   - Filters: Verified accounts only, past 3 days, English

2. **snscrape** (Fallback)
   - Only used if X API fails or `USE_SNSCRAPE=true`
   - ⚠️ Violates Twitter's Terms of Service

3. **Mock Data** (Fallback)
   - Only used if both X API and snscrape fail
   - Or if `USE_MOCK_DATA=true`

## Switching Between Modes

### Use X API (Production)
```bash
USE_MOCK_DATA=false
USE_SNSCRAPE=false
# Ensure X_API_CLIENT_ID and X_API_CLIENT_SECRET are set
```

### Use Mock Data (Testing)
```bash
USE_MOCK_DATA=true
USE_SNSCRAPE=false
```

### Use snscrape (Not Recommended)
```bash
USE_MOCK_DATA=false
USE_SNSCRAPE=true
```

## API Features

### X API v2 Features
- **Endpoint**: `/2/tweets/search/recent`
- **Authentication**: OAuth 2.0 Client Credentials
- **Rate Limits**: 
  - Free tier: 300 requests per 15 minutes
  - Max 100 tweets per request
- **Filters Applied**:
  - `is:verified` - Only verified accounts (藍勾認證帳號)
  - `lang:en` - English language only
  - `-is:retweet` - Exclude retweets
  - Past 3 days only

### Query Strategy
1. Expands keywords to variations (e.g., "AAPL" → ["AAPL", "Apple", "$AAPL"])
2. Merges variations into single OR query per keyword
3. Queries X API for each keyword
4. Filters results to past 3 days
5. Ranks by popularity score (weighted: views 0.1, likes 0.3, retweets 0.6)
6. Returns top 5 most popular tweets

## Monitoring

### Check API Usage
- Visit [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
- Check API usage and rate limits
- Monitor for any errors or warnings

### Logs
The application logs:
- OAuth 2.0 token acquisition
- API query strings
- Number of tweets retrieved
- Any errors or fallbacks

## Troubleshooting

### X API Not Working
1. **Check credentials**: Verify `X_API_CLIENT_ID` and `X_API_CLIENT_SECRET` are correct
2. **Check rate limits**: Ensure you haven't exceeded API limits
3. **Check permissions**: Verify your app has necessary permissions
4. **Check logs**: Look for error messages in application logs

### Fallback to Mock Data
If X API fails, the application will:
1. Log the error
2. Fallback to snscrape (if enabled)
3. Fallback to mock data (if snscrape also fails)

## Next Steps

- ✅ OAuth 2.0 configured
- ✅ X API enabled
- ✅ Mock data disabled
- 🎯 Ready to use real X API data!
