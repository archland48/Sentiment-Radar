# Solutions for Filtering Tweets to Follows and Follows-of-Follows

## Overview
You want to scan tweets and retweets only from:
1. **Direct follows**: Users you follow
2. **Follows-of-follows**: Users followed by those you follow

## Solution 1: Twitter API v2 with User Lookup + Filtering

### Approach
1. Use `GET /2/users/:id/following` to get your following list
2. For each user you follow, get their following list (`follows-of-follows`)
3. Combine both lists to create an allowed user ID set
4. Use `GET /2/tweets/search/recent` with `from:` operator to filter by user IDs
5. Filter results to only include tweets from allowed users

### Implementation Steps
```python
# Step 1: Get your following list
following_ids = get_following_list(user_id)

# Step 2: Get follows-of-follows (with rate limiting)
follows_of_follows = set()
for followed_user_id in following_ids:
    their_following = get_following_list(followed_user_id)
    follows_of_follows.update(their_following)

# Step 3: Combine allowed users
allowed_users = following_ids | follows_of_follows

# Step 4: Search with user filter
query = f"({keyword}) (from:{' OR from:'.join(allowed_users[:25])})"
# Note: Twitter API limits to 25 users per query
```

### Pros
- ✅ **Official API**: Reliable, supported by Twitter
- ✅ **Real-time data**: Gets current following relationships
- ✅ **Comprehensive**: Can get all follows-of-follows
- ✅ **Retweet support**: Can filter retweets from allowed users
- ✅ **Rate limits manageable**: With proper pagination

### Cons
- ❌ **Rate limit intensive**: 
  - Following list: 15 requests/15min per user
  - If you follow 100 users, need 100 requests = ~100 minutes
  - Search: 300 requests/15min
- ❌ **User limit per query**: Max 25 users per search query
  - Need to batch searches for large follow lists
- ❌ **Cost**: Requires Twitter API v2 access (paid tiers for higher limits)
- ❌ **Complex batching**: Need to split large user lists into chunks
- ❌ **Slow initial setup**: First run takes time to build user list

### Rate Limit Impact
- **Following endpoint**: 15 requests/15min per user
- **Search endpoint**: 300 requests/15min
- **Example**: Following 100 users = 100 requests = ~100 minutes minimum

---

## Solution 2: Twitter API v2 with Home Timeline

### Approach
1. Use `GET /2/users/:id/timelines/reverse_chronological` (Home Timeline)
2. This automatically includes tweets from your follows
3. Filter results by keywords
4. For follows-of-follows, you'd need to manually track or use Solution 1

### Pros
- ✅ **Simple**: Single endpoint call
- ✅ **Fast**: No need to fetch following lists
- ✅ **Includes retweets**: Automatically includes retweets from follows
- ✅ **Real-time**: Gets current timeline

### Cons
- ❌ **Limited to direct follows**: Doesn't include follows-of-follows
- ❌ **Limited history**: Only recent tweets (last ~800 tweets)
- ❌ **No keyword filtering at API level**: Must filter client-side
- ❌ **Rate limit**: 75 requests/15min per user
- ❌ **Requires user context**: Needs authenticated user's timeline

---

## Solution 3: Hybrid Approach - Cached User List + Search

### Approach
1. **Initial setup**: Build and cache allowed user list (follows + follows-of-follows)
2. **Periodic refresh**: Update user list daily/weekly (following relationships change slowly)
3. **Search phase**: Use cached user list to filter searches
4. **Batch searches**: Split user list into chunks of 25 for API queries

### Implementation Strategy
```python
# Cache structure
{
    "user_id": "your_user_id",
    "following_ids": [...],  # Cached list
    "follows_of_follows_ids": [...],  # Cached list
    "last_updated": "2024-01-30T...",
    "cache_ttl_hours": 24
}

# Search with cached list
allowed_users = get_cached_allowed_users()
batches = chunk_list(allowed_users, size=25)
for batch in batches:
    query = f"({keyword}) (from:{' OR from:'.join(batch)})"
    tweets = search_tweets(query)
```

### Pros
- ✅ **Fast searches**: No need to fetch following lists each time
- ✅ **Reduced API calls**: Only refresh user list periodically
- ✅ **Scalable**: Can handle large follow lists efficiently
- ✅ **Cost effective**: Minimizes API usage

### Cons
- ❌ **Stale data risk**: User list may be outdated if follows change frequently
- ❌ **Storage needed**: Must cache user relationships
- ❌ **Initial complexity**: Need to build caching system
- ❌ **Still rate limited**: Search queries still subject to limits

---

## Solution 4: Twitter API v2 with List-based Filtering

### Approach
1. Create Twitter Lists for your follows and follows-of-follows
2. Use `GET /2/lists/:id/tweets` to get tweets from list members
3. Filter by keywords client-side

### Pros
- ✅ **Twitter-native**: Uses Twitter's list feature
- ✅ **Manual control**: You control list membership
- ✅ **Simple API**: Single endpoint per list
- ✅ **Includes retweets**: From list members

### Cons
- ❌ **Manual setup**: Must manually create/maintain lists
- ❌ **Doesn't scale**: Lists limited to 5,000 members
- ❌ **No automatic follows-of-follows**: Must manually add users
- ❌ **Rate limit**: 75 requests/15min per list
- ❌ **Not dynamic**: Lists don't auto-update when follows change

---

## Solution 5: Third-Party Services (Tweepy, TwitterAPI, etc.)

### Approach
Use libraries/services that abstract Twitter API complexity:
- Tweepy (Python library)
- TwitterAPI (Python wrapper)
- N8N/Zapier workflows
- Custom scraping services

### Pros
- ✅ **Simplified API**: Easier to use than raw Twitter API
- ✅ **Built-in pagination**: Handles rate limits automatically
- ✅ **Community support**: Well-documented examples
- ✅ **Error handling**: Libraries handle retries/errors

### Cons
- ❌ **Same limitations**: Still subject to Twitter API limits
- ❌ **Additional dependency**: Another layer to maintain
- ❌ **Cost**: Some services charge fees
- ❌ **Privacy concerns**: Third-party services access your data

---

## Solution 6: Post-Fetch Filtering (Current Mock Approach)

### Approach
1. Fetch tweets using general search (no user filtering)
2. Get your following list separately
3. Filter results client-side to only include tweets from allowed users

### Pros
- ✅ **Simple**: No complex API queries
- ✅ **Flexible**: Can apply any filtering logic
- ✅ **No query limits**: Not limited by user count in query

### Cons
- ❌ **Inefficient**: Fetches many irrelevant tweets
- ❌ **Rate limit waste**: Uses API quota on unwanted tweets
- ❌ **Slower**: More data to process
- ❌ **May miss tweets**: If search doesn't return all relevant tweets

---

## Recommended Solution: **Hybrid Approach (Solution 3)**

### Why This Works Best
1. **Efficiency**: Cache user relationships, refresh periodically
2. **Scalability**: Handles large follow lists by batching
3. **Performance**: Fast searches using cached data
4. **Cost-effective**: Minimizes API calls

### Implementation Plan

#### Phase 1: User List Builder
```python
async def build_allowed_users_list(user_id: str) -> Set[str]:
    """Build set of allowed user IDs (follows + follows-of-follows)"""
    # Get your following
    following = await get_following_list(user_id)
    
    # Get follows-of-follows (with rate limit handling)
    follows_of_follows = set()
    for followed_id in following:
        their_following = await get_following_list(followed_id)
        follows_of_follows.update(their_following)
        await rate_limit_delay()  # Respect API limits
    
    return following | follows_of_follows
```

#### Phase 2: Cached Search
```python
async def search_tweets_from_allowed_users(
    keywords: List[str],
    allowed_users: Set[str],
    max_tweets: int = 10
) -> List[Dict]:
    """Search tweets only from allowed users"""
    # Batch users (Twitter limit: 25 per query)
    user_batches = chunk_list(list(allowed_users), size=25)
    
    all_tweets = []
    for batch in user_batches:
        # Build query: keyword AND (from:user1 OR from:user2 ...)
        user_filter = " OR ".join([f"from:{uid}" for uid in batch])
        query = f"({' OR '.join(keywords)}) ({user_filter})"
        
        tweets = await search_tweets_api(query)
        all_tweets.extend(tweets)
    
    return all_tweets[:max_tweets]
```

#### Phase 3: Cache Management
```python
# Store in database or file
cache = {
    "allowed_users": list(allowed_users),
    "last_updated": datetime.now(),
    "ttl_hours": 24
}

# Refresh logic
if cache_expired(cache):
    allowed_users = await build_allowed_users_list(user_id)
    update_cache(cache, allowed_users)
```

---

## Rate Limit Considerations

### Twitter API v2 Limits (Essential Tier)
- **Following list**: 15 requests/15min per user
- **Search**: 300 requests/15min
- **Timeline**: 75 requests/15min

### Example Calculation
- **Following 100 users**: 
  - Initial build: 100 requests = ~100 minutes (with delays)
  - Daily refresh: Same time, but can run overnight
- **Search with 100 allowed users**:
  - Need 4 batches (25 users each) = 4 search requests
  - Well within 300 requests/15min limit ✅

---

## Cost Considerations

### Twitter API Pricing (as of 2024)
- **Free tier**: Very limited (1,500 tweets/month)
- **Basic tier**: $100/month (10,000 tweets/month)
- **Pro tier**: $5,000/month (1M tweets/month)

### Recommendation
- Start with Basic tier for MVP
- Use caching to maximize efficiency
- Consider Pro tier if scaling

---

## Implementation Priority

1. **MVP**: Use Solution 2 (Home Timeline) - simplest, gets direct follows
2. **Phase 2**: Implement Solution 3 (Hybrid) - add follows-of-follows with caching
3. **Production**: Optimize caching and batching for scale

---

## Next Steps

Would you like me to implement one of these solutions? I recommend starting with **Solution 3 (Hybrid Approach)** as it provides the best balance of functionality, performance, and cost.
