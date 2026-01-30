# X (Twitter) API OAuth 2.0 Setup Guide

## Overview

The application now supports X (Twitter) API authentication using OAuth 2.0 Client Credentials flow. This is the recommended method for server-to-server authentication.

## OAuth 2.0 vs Bearer Token

### OAuth 2.0 Client Credentials (Recommended)
- **Client ID**: Application identifier
- **Client Secret**: Secret key for authentication
- **Flow**: Automatically exchanges credentials for Bearer Token
- **Advantages**: More secure, supports token refresh, better for production

### Bearer Token (Legacy)
- **Direct Token**: Pre-generated Bearer Token
- **Advantages**: Simpler setup, no token exchange needed
- **Disadvantages**: Token expiration requires manual refresh

## Setup Steps

### 1. Get OAuth 2.0 Credentials

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/projects-and-apps)
2. Sign in with your Twitter account
3. Navigate to your Project and App
4. Go to "Keys and Tokens" section
5. Find **OAuth 2.0 Client ID and Client Secret**

### 2. Configure Environment Variables

Add your OAuth 2.0 credentials to the `.env` file:

```bash
# X (Twitter) API OAuth 2.0 Configuration
X_API_CLIENT_ID=your_client_id_here
X_API_CLIENT_SECRET=your_client_secret_here
```

**Important**: Never commit your `.env` file to version control. It's already in `.gitignore`.

### 3. How It Works

The application automatically:
1. Reads `X_API_CLIENT_ID` and `X_API_CLIENT_SECRET` from `.env`
2. Exchanges them for a Bearer Token using OAuth 2.0 Client Credentials flow
3. Uses the Bearer Token to authenticate with X API v2
4. Caches the token for the duration of the request

### 4. Fallback Behavior

The application supports multiple authentication methods with priority:

1. **OAuth 2.0** (if `X_API_CLIENT_ID` and `X_API_CLIENT_SECRET` are set)
2. **Bearer Token** (if `TWITTER_BEARER_TOKEN` is set)
3. **snscrape** (if API fails or no credentials)
4. **Mock Data** (if all else fails)

## Code Implementation

The OAuth 2.0 flow is implemented in `query_x_api()` function:

```python
# Check for OAuth 2.0 credentials
client_id = os.getenv('X_API_CLIENT_ID')
client_secret = os.getenv('X_API_CLIENT_SECRET')

if client_id and client_secret:
    # Exchange credentials for Bearer Token
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    response = await http_client.post(
        "https://api.twitter.com/2/oauth2/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"}
    )
    
    bearer_token = response.json().get('access_token')
```

## Environment Variables

### Required for OAuth 2.0
- `X_API_CLIENT_ID`: Your OAuth 2.0 Client ID
- `X_API_CLIENT_SECRET`: Your OAuth 2.0 Client Secret

### Optional (Legacy)
- `TWITTER_BEARER_TOKEN`: Direct Bearer Token (if not using OAuth 2.0)

### Test Mode
- `USE_MOCK_DATA`: Set to `true` to use mock data instead of API
- `USE_SNSCRAPE`: Set to `true` to use snscrape (violates ToS)

## Troubleshooting

### Error: Failed to obtain Bearer Token
- **Check**: Verify `X_API_CLIENT_ID` and `X_API_CLIENT_SECRET` are correct
- **Check**: Ensure credentials are not expired or revoked
- **Check**: Verify your app has the necessary permissions

### Error: Invalid credentials
- **Solution**: Regenerate Client Secret in Twitter Developer Portal
- **Solution**: Ensure no extra spaces or quotes in `.env` file

### Token Expiration
- OAuth 2.0 tokens typically expire after 2 hours
- The application automatically requests a new token when needed
- No manual intervention required

## Security Best Practices

1. **Never commit `.env` file**: Already in `.gitignore`
2. **Rotate secrets regularly**: Regenerate Client Secret periodically
3. **Use environment variables**: Never hardcode credentials
4. **Limit API permissions**: Only request necessary scopes
5. **Monitor usage**: Check Twitter Developer Portal for API usage

## Migration from Bearer Token

If you're migrating from Bearer Token to OAuth 2.0:

1. Add `X_API_CLIENT_ID` and `X_API_CLIENT_SECRET` to `.env`
2. Keep `TWITTER_BEARER_TOKEN` for backward compatibility (optional)
3. The application will automatically use OAuth 2.0 if available
4. Remove `TWITTER_BEARER_TOKEN` once OAuth 2.0 is verified working

## References

- [Twitter API v2 Authentication](https://developer.twitter.com/en/docs/authentication/oauth-2-0)
- [OAuth 2.0 Client Credentials Flow](https://developer.twitter.com/en/docs/authentication/oauth-2-0/user-access-token)
- [Tweepy Documentation](https://docs.tweepy.org/)
