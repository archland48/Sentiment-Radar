from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime
import re
from textblob import TextBlob
import random
import os
import httpx
from urllib.parse import urlparse
from dotenv import load_dotenv
from ai_client import (
    analyze_thoughts_with_ai, 
    generate_insights_with_ai, 
    perform_deep_dive_analysis
)

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Sentiment Alpha Radar API",
    description="API for analyzing user thoughts on X (Twitter) for keywords, ticker symbols, and company names",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")


class ScanRequest(BaseModel):
    """Request model for thoughts scan"""
    keywords: List[str]
    max_tweets: Optional[int] = 3  # Default to 3 popular tweets
    options: Optional[Dict[str, Any]] = None


class Tweet(BaseModel):
    """Tweet model"""
    id: str
    text: str
    author: str
    timestamp: str
    likes: int
    retweets: int
    views: int
    thoughts_score: float
    thoughts_label: str


class ScanStageResult(BaseModel):
    """Result from a single scan stage"""
    stage: int
    status: str
    result: Dict[str, Any]
    timestamp: str
    duration_ms: float


class ScanResponse(BaseModel):
    """Response model for scan endpoint"""
    scan_id: str
    status: str
    keywords: List[str]
    stage1: ScanStageResult
    stage2: ScanStageResult
    total_duration_ms: float
    timestamp: str


class TickerResult(BaseModel):
    """Ticker search result"""
    symbol: str
    name: str
    exchange: Optional[str] = None
    type: Optional[str] = None


class TickerSearchResponse(BaseModel):
    """Response model for ticker search"""
    query: str
    results: List[TickerResult]
    count: int


# Mock tweet database for MVP (replace with actual Twitter API in production)
# Includes variations: ticker symbols, company names, and $ticker formats
MOCK_TWEETS_DB = {
    # AAPL / Apple variations
    "AAPL": [
        {"text": "Apple's new iPhone is amazing! $AAPL https://www.apple.com/newsroom/2024/01/apple-announces-record-quarter/", "author": "@techfan", "likes": 150, "retweets": 45, "views": 5000},
        {"text": "Not impressed with Apple's latest earnings. $AAPL https://www.reuters.com/technology/apple-earnings", "author": "@investor", "likes": 23, "retweets": 8, "views": 1200},
        {"text": "Apple stock looking bullish today! $AAPL", "author": "@trader", "likes": 89, "retweets": 32, "views": 3500},
    ],
    "APPLE": [
        {"text": "Apple Inc. just announced amazing quarterly results!", "author": "@marketwatch", "likes": 203, "retweets": 67, "views": 8500},
        {"text": "Thinking about buying more Apple shares", "author": "@investor", "likes": 45, "retweets": 12, "views": 1800},
        {"text": "Apple's ecosystem is unbeatable", "author": "@techguru", "likes": 112, "retweets": 34, "views": 4200},
    ],
    "APPLE INC": [
        {"text": "Apple Inc. continues to innovate in the tech space", "author": "@analyst", "likes": 78, "retweets": 23, "views": 2800},
    ],
    # TSLA / Tesla variations
    "TSLA": [
        {"text": "Tesla's innovation is incredible! $TSLA https://www.tesla.com/blog/tesla-q4-2024-update", "author": "@evfan", "likes": 234, "retweets": 67, "views": 12000},
        {"text": "Concerned about Tesla's production delays $TSLA https://www.bloomberg.com/news/articles/2024-01-30/tesla-production", "author": "@analyst", "likes": 45, "retweets": 12, "views": 2500},
        {"text": "Elon Musk is revolutionizing transportation! $TSLA", "author": "@follower", "likes": 178, "retweets": 54, "views": 6800},
    ],
    "TESLA": [
        {"text": "Tesla Model 3 is the best EV on the market", "author": "@evfan", "likes": 189, "retweets": 56, "views": 7500},
        {"text": "Tesla's Supercharger network is expanding rapidly", "author": "@evnews", "likes": 134, "retweets": 41, "views": 5200},
        {"text": "Long Tesla for the next decade", "author": "@trader", "likes": 92, "retweets": 28, "views": 3200},
    ],
    # MSFT / Microsoft variations
    "MSFT": [
        {"text": "Microsoft Azure is dominating cloud computing! $MSFT https://azure.microsoft.com/en-us/blog/", "author": "@clouddev", "likes": 112, "retweets": 28, "views": 4500},
        {"text": "Microsoft's AI investments paying off $MSFT https://www.microsoft.com/en-us/investor", "author": "@technews", "likes": 156, "retweets": 41, "views": 6200},
    ],
    "MICROSOFT": [
        {"text": "Microsoft Copilot is changing how we work", "author": "@productivity", "likes": 167, "retweets": 52, "views": 7800},
        {"text": "Microsoft's cloud revenue keeps growing", "author": "@cloudanalyst", "likes": 98, "retweets": 31, "views": 3800},
    ],
    # GOOGL / Google variations
    "GOOGL": [
        {"text": "Google's search dominance continues $GOOGL", "author": "@seoexpert", "likes": 98, "retweets": 19, "views": 3400},
        {"text": "Alphabet stock performing well $GOOGL", "author": "@investor", "likes": 67, "retweets": 15, "views": 2100},
    ],
    "GOOGLE": [
        {"text": "Google's AI research is groundbreaking", "author": "@technews", "likes": 145, "retweets": 43, "views": 5600},
        {"text": "Google Cloud is gaining market share", "author": "@clouddev", "likes": 89, "retweets": 27, "views": 2900},
    ],
    "ALPHABET": [
        {"text": "Alphabet's diverse portfolio is impressive", "author": "@investor", "likes": 76, "retweets": 22, "views": 2600},
    ],
    "default": [
        {"text": "Great company with strong fundamentals!", "author": "@investor", "likes": 50, "retweets": 10, "views": 1500},
        {"text": "Mixed feelings about this stock", "author": "@trader", "likes": 30, "retweets": 5, "views": 800},
        {"text": "Bullish on this one!", "author": "@bull", "likes": 75, "retweets": 20, "views": 2200},
    ]
}


async def expand_keyword_to_variations(keyword: str) -> Dict[str, List[str]]:
    """
    Expand a single keyword (ticker symbol or company name) to all related variations.
    
    For example:
    - "AAPL" → ["AAPL", "Apple", "$AAPL", "Apple Inc."]
    - "Apple" → ["AAPL", "Apple", "$AAPL", "Apple Inc."]
    - "$AAPL" → ["AAPL", "Apple", "$AAPL", "Apple Inc."]
    
    Returns a dict with:
    - "ticker": ticker symbol (e.g., "AAPL")
    - "company_name": company name (e.g., "Apple")
    - "variations": list of all keyword variations to search
    """
    keyword_clean = keyword.strip().upper().replace("$", "")
    
    # Try to look up ticker info
    ticker_symbol = None
    company_name = None
    
    # Check if it's already a ticker symbol (short, uppercase, alphanumeric)
    if len(keyword_clean) <= 5 and keyword_clean.isalpha():
        ticker_symbol = keyword_clean
        # Try to get company name from ticker APIs
        try:
            import yfinance as yf
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            if info:
                company_name = info.get('longName') or info.get('shortName') or ticker_symbol
        except:
            # Fallback: use common mappings
            common_companies = {
                "AAPL": "Apple",
                "TSLA": "Tesla",
                "MSFT": "Microsoft",
                "GOOGL": "Google",
                "AMZN": "Amazon",
                "META": "Meta",
                "NVDA": "NVIDIA"
            }
            company_name = common_companies.get(ticker_symbol, ticker_symbol)
    else:
        # It's likely a company name, try to find ticker
        company_name = keyword.strip()
        # Try to search for ticker using APIs
        try:
            # Use OpenFIGI or Finnhub to find ticker
            async with httpx.AsyncClient(timeout=3.0) as client:
                # Try OpenFIGI first
                url = "https://api.openfigi.com/v3/search"
                payload = [{"query": company_name, "exchCode": "US"}]
                response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0 and len(data[0].get('data', [])) > 0:
                        ticker_symbol = data[0]['data'][0].get('ticker', '').upper()
        except:
            pass
    
    # If we still don't have both, use defaults
    if not ticker_symbol:
        ticker_symbol = keyword_clean
    if not company_name:
        company_name = keyword.strip()
    
    # Generate all variations
    variations = []
    
    # Add ticker variations
    if ticker_symbol:
        variations.append(ticker_symbol)  # AAPL
        variations.append(f"${ticker_symbol}")  # $AAPL
    
    # Add company name variations
    if company_name:
        variations.append(company_name)  # Apple
        # Add common variations
        if "Inc." not in company_name and "Corporation" not in company_name:
            variations.append(f"{company_name} Inc.")  # Apple Inc.
        if "Corp" not in company_name.lower():
            variations.append(f"{company_name} Corp")  # Apple Corp
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for v in variations:
        v_lower = v.lower()
        if v_lower not in seen:
            seen.add(v_lower)
            unique_variations.append(v)
    
    return {
        "ticker": ticker_symbol,
        "company_name": company_name,
        "variations": unique_variations
    }


# Engagement weights for thoughts monitoring
# Higher weight = more important for thoughts analysis
ENGAGEMENT_WEIGHTS = {
    "views": 0.1,      # Low: Just exposure, doesn't indicate thoughts
    "likes": 0.3,     # Medium: Indicates agreement/positive thoughts
    "retweets": 0.6    # High: Indicates strong agreement/sharing thoughts
}


def calculate_weighted_engagement(likes: int, retweets: int, views: int) -> float:
    """
    Calculate weighted engagement score for thoughts monitoring
    
    Args:
        likes: Number of likes
        retweets: Number of retweets
        views: Number of views
    
    Returns:
        Weighted engagement score
    """
    weighted_score = (
        likes * ENGAGEMENT_WEIGHTS["likes"] +
        retweets * ENGAGEMENT_WEIGHTS["retweets"] +
        views * ENGAGEMENT_WEIGHTS["views"]
    )
    return round(weighted_score, 2)


def analyze_thoughts(text: str) -> Dict[str, Any]:
    """
    Analyze thoughts of text using TextBlob
    
    Returns thoughts score (-1 to 1) and label
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    # Classify thoughts
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"
    
    return {
        "score": round(polarity, 3),
        "label": label,
        "confidence": round(abs(polarity), 3)
    }


async def query_x_api_snscrape(query: str, max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Query X (Twitter) using snscrape (free, no API key required)
    
    ⚠️ WARNING: This violates Twitter's Terms of Service. Use at your own risk.
    
    Args:
        query: Search query string
        max_results: Maximum number of results
    
    Returns:
        List of tweet dictionaries with X data
    """
    try:
        import snscrape.modules.twitter as sntwitter
        
        tweets_data = []
        
        # Build query with filters
        # Filter to past 3 days, English only, and verified accounts only (藍勾認證帳號)
        from datetime import timedelta
        since_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        full_query = f"{query} lang:en since:{since_date} filter:verified"
        
        print(f"Scraping tweets with snscrape (verified accounts only): {full_query}")
        
        # Scrape tweets
        scraper = sntwitter.TwitterSearchScraper(full_query)
        
        for i, tweet in enumerate(scraper.get_items()):
            if i >= max_results:
                break
            
            try:
                # Check if user is verified (snscrape may have verified field)
                is_verified = False
                if tweet.user:
                    # Check verified status from user object
                    is_verified = getattr(tweet.user, 'verified', False) or getattr(tweet.user, 'blue', False)
                
                # Only include verified accounts
                if not is_verified:
                    continue
                
                tweet_user = tweet.user
                username = tweet_user.username if tweet_user else None
                tweet_dict = {
                    "id": str(tweet.id),
                    "text": tweet.rawContent or tweet.content,
                    "author": f"@{username}" if username else "Unknown",
                    "author_type": tweet_user.displayname if tweet_user else "Unknown",
                    "verified": True,  # Mark as verified account
                    "timestamp": tweet.date.isoformat() if tweet.date else datetime.now().isoformat(),
                    "likes": tweet.likeCount or 0,
                    "retweets": tweet.retweetCount or 0,
                    "views": tweet.viewCount or 0,  # May not always be available
                    "replies": tweet.replyCount or 0,
                    "x_url": f"https://x.com/{username}/status/{tweet.id}" if username and tweet.id else None,  # X.com link to the tweet
                }
                
                # Estimate views if not available
                if tweet_dict["views"] == 0:
                    tweet_dict["views"] = (tweet_dict["likes"] + tweet_dict["retweets"]) * 10
                
                tweets_data.append(tweet_dict)
            except Exception as e:
                print(f"Error processing tweet: {e}")
                continue
        
        print(f"Scraped {len(tweets_data)} tweets using snscrape")
        return tweets_data
        
    except ImportError:
        print("snscrape not installed. Install with: pip install snscrape")
        return []
    except Exception as e:
        print(f"Error scraping with snscrape: {e}")
        return []


async def query_x_api(query: str, max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Query X (Twitter) API v2 for tweets (verified accounts only - 藍勾認證帳號)
    
    Args:
        query: Search query string
        max_results: Maximum number of results (API limit: 100 per request)
    
    Returns:
        List of tweet dictionaries with X API data (only verified accounts)
    """
    import tweepy
    import base64
    import httpx
    
    # Priority 1: Use Bearer Token directly (faster, no token exchange needed)
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    
    # Priority 2: If no Bearer Token, try to get one using OAuth 2.0 Client Credentials (slower)
    if not bearer_token or bearer_token == 'your_twitter_bearer_token_here':
        client_id = os.getenv('X_API_CLIENT_ID')
        client_secret = os.getenv('X_API_CLIENT_SECRET')
        
        if client_id and client_secret and client_id != 'your_client_id_here':
            try:
                # OAuth 2.0 Client Credentials flow to get Bearer Token
                # Encode client credentials
                credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
                
                # Request Bearer Token (with timeout to prevent hanging)
                async with httpx.AsyncClient(timeout=10.0) as http_client:
                    response = await http_client.post(
                        "https://api.twitter.com/2/oauth2/token",
                        headers={
                            "Authorization": f"Basic {credentials}",
                            "Content-Type": "application/x-www-form-urlencoded"
                        },
                        data={"grant_type": "client_credentials"}
                    )
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        bearer_token = token_data.get('access_token')
                        print("✅ Successfully obtained Bearer Token using OAuth 2.0")
                    else:
                        print(f"⚠️ Failed to obtain Bearer Token: {response.status_code} - {response.text}")
                        return []
            except Exception as e:
                print(f"⚠️ Error obtaining Bearer Token via OAuth 2.0: {e}")
                return []
        else:
            # No API credentials configured, return empty list
            return []
    
    if not bearer_token:
        return []
    
    try:
        # Initialize Tweepy client
        client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)
        
        # Query X API
        # Search for tweets from past 3 days, exclude retweets for more diverse results
        tweets_data = []
        pagination_token = None
        
        # Calculate how many requests we need (API limit: 100 per request)
        remaining_results = min(max_results, 100)  # API max is 100 per request
        
        while len(tweets_data) < max_results:
            try:
                # Build query with date filter (past 3 days)
                from datetime import timedelta
                start_time = (datetime.now() - timedelta(days=3)).isoformat() + 'Z'
                
                # Build query string with filters
                full_query = f"{query} -is:retweet lang:en is:verified"
                print(f"Querying X API with: {full_query}")
                
                # Search recent tweets (filter: verified accounts only - 藍勾認證帳號)
                # Add timeout to prevent hanging (15 seconds per API call)
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        client.search_recent_tweets,
                        query=full_query,
                        max_results=min(remaining_results, 100),
                        tweet_fields=['created_at', 'public_metrics', 'author_id', 'text'],
                        user_fields=['username', 'name', 'verified'],
                        expansions=['author_id'],
                        start_time=start_time if len(tweets_data) == 0 else None,  # Only on first request
                        next_token=pagination_token if pagination_token else None
                    ),
                    timeout=15.0  # 15 second timeout per API call
                )
                
                if not response.data:
                    print(f"No tweets found for query: {full_query}")
                    # Check if there are any errors in response
                    if hasattr(response, 'errors'):
                        print(f"API Errors: {response.errors}")
                    break
                
                print(f"Found {len(response.data)} tweets in this batch")
                
                # Create user lookup dictionary
                users = {user.id: user for user in response.includes.get('users', [])} if response.includes else {}
                
                # Process tweets
                for tweet in response.data:
                    author = users.get(tweet.author_id) if tweet.author_id else None
                    metrics = tweet.public_metrics
                    
                    # Verify author is verified (double-check, though query already filters)
                    is_verified = author.verified if author and hasattr(author, 'verified') else False
                    
                    author_username = author.username if author else None
                    tweet_dict = {
                        "id": str(tweet.id),
                        "text": tweet.text,
                        "author": f"@{author_username}" if author_username else f"@{tweet.author_id}",
                        "author_type": author.name if author else "Unknown",
                        "verified": is_verified,  # Mark as verified account
                        "timestamp": tweet.created_at.isoformat() if tweet.created_at else datetime.now().isoformat(),
                        "likes": metrics.get('like_count', 0),
                        "retweets": metrics.get('retweet_count', 0),
                        "views": metrics.get('impression_count', 0),  # May not be available on all tiers
                        "replies": metrics.get('reply_count', 0),
                        "x_url": f"https://x.com/{author_username}/status/{tweet.id}" if author_username and tweet.id else None,  # X.com link to the tweet
                    }
                    tweets_data.append(tweet_dict)
                
                # Check for pagination
                if hasattr(response, 'meta') and response.meta.get('next_token'):
                    pagination_token = response.meta['next_token']
                    remaining_results = max_results - len(tweets_data)
                else:
                    break
                    
            except asyncio.TimeoutError:
                print(f"⚠️ X API query timed out after 15s for: {full_query}")
                print("Continuing with tweets found so far...")
                break  # Return what we have so far
            except tweepy.TooManyRequests:
                # Rate limit hit, wait and retry
                print("Rate limit reached, waiting...")
                await asyncio.sleep(60)
                continue
            except tweepy.Unauthorized:
                print("Twitter API authentication failed. Check your bearer token.")
                print(f"Query that failed: {full_query}")
                break
            except tweepy.BadRequest as e:
                print(f"Twitter API bad request: {e}")
                print(f"Query that failed: {full_query}")
                # Try without verified filter as fallback
                try:
                    print("Attempting query without verified filter...")
                    fallback_query = f"{query} -is:retweet lang:en"
                    response = client.search_recent_tweets(
                        query=fallback_query,
                        max_results=min(remaining_results, 100),
                        tweet_fields=['created_at', 'public_metrics', 'author_id', 'text'],
                        user_fields=['username', 'name', 'verified'],
                        expansions=['author_id'],
                        start_time=start_time if len(tweets_data) == 0 else None,
                    )
                    if response.data:
                        print(f"Fallback query found {len(response.data)} tweets (non-verified)")
                        # Filter verified accounts manually
                        users = {user.id: user for user in response.includes.get('users', [])} if response.includes else {}
                        for tweet in response.data:
                            author = users.get(tweet.author_id) if tweet.author_id else None
                            if author and hasattr(author, 'verified') and author.verified:
                                # Process verified tweet
                                metrics = tweet.public_metrics
                                tweet_dict = {
                                    "id": tweet.id,
                                    "text": tweet.text,
                                    "author": f"@{author.username}" if author else f"@{tweet.author_id}",
                                    "author_type": author.name if author else "Unknown",
                                    "verified": True,
                                    "timestamp": tweet.created_at.isoformat() if tweet.created_at else datetime.now().isoformat(),
                                    "likes": metrics.get('like_count', 0),
                                    "retweets": metrics.get('retweet_count', 0),
                                    "views": metrics.get('impression_count', 0),
                                    "replies": metrics.get('reply_count', 0),
                                }
                                tweets_data.append(tweet_dict)
                except Exception as fallback_error:
                    print(f"Fallback query also failed: {fallback_error}")
                break
            except Exception as e:
                print(f"Twitter API error: {e}")
                print(f"Query that failed: {full_query}")
                import traceback
                traceback.print_exc()
                break
        
        return tweets_data
        
    except ImportError:
        print("tweepy not installed. Install with: pip install tweepy")
        return []
    except Exception as e:
        print(f"Error querying X API: {e}")
        return []


async def search_tweets(keyword_variations: Dict[str, List[str]], max_tweets: int = 1000) -> tuple[List[Dict[str, Any]], List[str]]:
    """
    Query X API for tweets matching keyword variations
    
    This function queries the real X (Twitter) API v2 for tweets matching
    the provided keyword variations. Falls back to mock data if API is unavailable.
    
    Args:
        keyword_variations: Dict mapping original keyword to list of variations
                          e.g., {"AAPL": ["AAPL", "Apple", "$AAPL", "Apple Inc."]}
        max_tweets: Maximum number of tweets to return (used for initial query, 
                   actual ranking happens in stage1_scan)
    
    Returns:
        Tuple of (list of tweets, list of variations searched)
    """
    from datetime import timedelta
    import random
    
    tweets = []
    all_variations_searched = []
    
    # Determine which method to use (priority: mock if forced > snscrape if forced > API > snscrape fallback > mock)
    use_mock_forced = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'
    use_snscrape_forced = os.getenv('USE_SNSCRAPE', 'false').lower() == 'true'
    # Check if we have API credentials (Bearer Token or OAuth 2.0)
    has_bearer_token = os.getenv('TWITTER_BEARER_TOKEN') and os.getenv('TWITTER_BEARER_TOKEN') != 'your_twitter_bearer_token_here'
    has_oauth = os.getenv('X_API_CLIENT_ID') and os.getenv('X_API_CLIENT_SECRET') and \
                os.getenv('X_API_CLIENT_ID') != 'your_client_id_here'
    use_api = has_bearer_token or has_oauth
    api_failed = False
    
    # Priority order: Mock (forced) > Snscrape (forced) > API > Snscrape (fallback) > Mock (fallback)
    # If mock data is forced, skip everything and use mock directly
    if use_mock_forced:
        print("🧪 Test Mode: Using Mock Database (forced via USE_MOCK_DATA=true)")
        # Skip API and snscrape, will execute mock code in elif section below
    elif use_snscrape_forced:
        print("🔧 Test Mode: Using snscrape (forced via USE_SNSCRAPE=true)")
        print("⚠️ WARNING: snscrape violates Twitter's Terms of Service. Use at your own risk.")
        # Skip API, will go directly to snscrape section below
    elif use_api:
        # Query real X API - OPTIMIZED: Merge all variations into single query per keyword
        print("Querying X API for tweets (optimized: merged queries)...")
        
        try:
            for original_keyword, variations in keyword_variations.items():
                all_variations_searched.extend(variations)
                
                # OPTIMIZATION: Merge all variations into single query using OR operator
                # This reduces API calls from N (one per variation) to 1 (one per keyword)
                # Example: "AAPL" OR "Apple" OR "$AAPL" OR "Apple Inc."
                if len(variations) > 1:
                    # Build OR query: (AAPL) OR (Apple) OR ($AAPL) OR (Apple Inc.)
                    or_queries = [f"({v})" for v in variations]
                    merged_query = " OR ".join(or_queries)
                else:
                    merged_query = f"({variations[0]})"
                
                # Single API call for all variations of this keyword
                # Increase max_results since we're getting results for all variations
                api_tweets = await query_x_api(merged_query, max_results=max_tweets)
                
                # Add keyword context to tweets and determine which variation matched
                for tweet in api_tweets:
                    tweet_text_lower = tweet.get("text", "").lower()
                    
                    # Determine which variation(s) matched this tweet
                    matched_variations = []
                    for variation in variations:
                        variation_lower = variation.lower()
                        # Check if variation appears in tweet text
                        if variation_lower in tweet_text_lower or f"${variation_lower}" in tweet_text_lower:
                            matched_variations.append(variation)
                    
                    # Use first matched variation, or first variation if none matched
                    matched_variation = matched_variations[0] if matched_variations else variations[0]
                    
                    tweet["original_keyword"] = original_keyword
                    tweet["matched_variation"] = matched_variation
                    tweet["matched_variations"] = matched_variations  # Store all matches
                    tweet["keyword"] = matched_variation.upper().replace("$", "")
                    
                    # Ensure views field exists (may not be available on free tier)
                    if "views" not in tweet or tweet["views"] == 0:
                        # Estimate views based on other metrics if not available
                        tweet["views"] = (tweet.get("likes", 0) + tweet.get("retweets", 0)) * 10
                    
                    tweets.append(tweet)
            
            print(f"Found {len(tweets)} tweets from X API (optimized: {len(keyword_variations)} API calls instead of {sum(len(v) for v in keyword_variations.values())})")
            
            # If API returned no results, try snscrape as fallback
            if len(tweets) == 0:
                print("⚠️ X API returned no results. Falling back to snscrape...")
                api_failed = True
            else:
                # API succeeded, return results
                pass
                
        except Exception as e:
            print(f"❌ X API failed with error: {e}")
            print("⚠️ Falling back to snscrape...")
            api_failed = True
    
    # Use snscrape if: forced via env var, or API failed/returned no results
    if use_snscrape_forced or (use_api and api_failed):
        # Use snscrape as free alternative or fallback - OPTIMIZED: Merge queries
        if use_snscrape_forced:
            # Already printed test mode message above
            pass
        elif api_failed:
            print("🔄 Falling back to snscrape (X API had no results or failed)")
        else:
            print("Using snscrape to fetch tweets (free, no API key required)")
        
        if not use_snscrape_forced:
            print("⚠️ WARNING: snscrape violates Twitter's Terms of Service. Use at your own risk.")
        
        # Reset tweets list if falling back from API
        if api_failed:
            tweets = []
            all_variations_searched = []
        
        for original_keyword, variations in keyword_variations.items():
            all_variations_searched.extend(variations)
            
            # OPTIMIZATION: Merge all variations into single query
            if len(variations) > 1:
                or_queries = [f"({v})" for v in variations]
                merged_query = " OR ".join(or_queries)
            else:
                merged_query = f"({variations[0]})"
            
            # Single scrape call for all variations
            scraped_tweets = await query_x_api_snscrape(merged_query, max_results=max_tweets)
            
            # Add keyword context to tweets
            for tweet in scraped_tweets:
                tweet_text_lower = tweet.get("text", "").lower()
                
                # Determine which variation matched
                matched_variations = []
                for variation in variations:
                    variation_lower = variation.lower()
                    if variation_lower in tweet_text_lower or f"${variation_lower}" in tweet_text_lower:
                        matched_variations.append(variation)
                
                matched_variation = matched_variations[0] if matched_variations else variations[0]
                
                tweet["original_keyword"] = original_keyword
                tweet["matched_variation"] = matched_variation
                tweet["matched_variations"] = matched_variations
                tweet["keyword"] = matched_variation.upper().replace("$", "")
                if "views" not in tweet or tweet["views"] == 0:
                    tweet["views"] = (tweet.get("likes", 0) + tweet.get("retweets", 0)) * 10
                
                tweets.append(tweet)
            
            # Single delay per keyword (not per variation)
            await asyncio.sleep(2)
        
        print(f"Found {len(tweets)} tweets using snscrape (optimized)")
    elif use_mock_forced or (not use_api and not use_snscrape_forced and not (use_api and api_failed)):
        # Use mock data (forced or automatic fallback)
        if use_mock_forced:
            print("🧪 Using Mock Database for testing")
        else:
            print("📦 Fallback: Using Mock Database (no API/snscrape configured)")
        now = datetime.now()
        
        for original_keyword, variations in keyword_variations.items():
            for variation in variations:
                all_variations_searched.append(variation)
                normalized = variation.upper().replace("$", "")
                keyword_tweets = MOCK_TWEETS_DB.get(normalized, MOCK_TWEETS_DB["default"])
                
                for tweet in keyword_tweets:
                    tweet_copy = tweet.copy()
                    if "views" not in tweet_copy:
                        tweet_copy["views"] = 0
                    tweet_copy["original_keyword"] = original_keyword
                    tweet_copy["matched_variation"] = variation
                    tweet_copy["keyword"] = normalized
                    tweet_copy["id"] = f"tweet_{normalized}_{random.randint(1000, 9999)}"
                    
                    days_ago = random.randint(0, 7)
                    hours_ago = random.randint(0, 23)
                    tweet_time = now - timedelta(days=days_ago, hours=hours_ago)
                    tweet_copy["timestamp"] = tweet_time.isoformat()
                    
                    tweets.append(tweet_copy)
        
        print(f"Found {len(tweets)} tweets from Mock Database")
    
    # Remove duplicates based on tweet ID (more reliable than text)
    # This handles cases where same tweet matches multiple variations
    seen_ids = set()
    seen_texts = set()  # Fallback for tweets without IDs
    unique_tweets = []
    for tweet in tweets:
        tweet_id = tweet.get("id")
        if tweet_id and tweet_id not in seen_ids:
            seen_ids.add(tweet_id)
            unique_tweets.append(tweet)
        elif not tweet_id:
            # Fallback to text-based deduplication if no ID
            text_key = tweet.get("text", "").lower()
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_tweets.append(tweet)
    
    # Track optimization metrics
    total_variations = sum(len(v) for v in keyword_variations.values())
    api_calls_saved = max(0, total_variations - len(keyword_variations))
    if api_calls_saved > 0:
        print(f"✅ API Optimization: Saved {api_calls_saved} API calls (reduced from {total_variations} to {len(keyword_variations)} calls)")
    
    # Return all unique tweets (ranking will happen in stage1_scan)
    return unique_tweets[:max_tweets], list(set(all_variations_searched))


def extract_urls_from_text(text: str) -> List[str]:
    """
    Extract URLs from tweet text
    
    Args:
        text: Tweet text content
    
    Returns:
        List of URLs found in the text
    """
    # URL regex pattern
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    
    # Also check for shortened URLs (t.co, bit.ly, etc.)
    # and common URL patterns without protocol
    patterns_without_protocol = [
        r'(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?',
    ]
    
    for pattern in patterns_without_protocol:
        found = re.findall(pattern, text)
        for url in found:
            if url not in urls and not url.startswith('http'):
                # Try to construct full URL
                if url.startswith('www.'):
                    urls.append(f"https://{url}")
                elif '.' in url:
                    urls.append(f"https://{url}")
    
    return list(set(urls))  # Remove duplicates


def read_background() -> str:
    """
    Read the strategic background from background.md
    
    Returns:
        Content of background.md as string
    """
    background_path = os.path.join(os.path.dirname(__file__), "background.md")
    try:
        with open(background_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Our project's primary strategic focus is analyzing user thoughts on X for various keywords (including ticker symbols, company names, $)."
    except Exception as e:
        print(f"Error reading background.md: {e}")
        return "Our project's primary strategic focus is analyzing user thoughts on X for various keywords (including ticker symbols, company names, $)."


def calculate_popularity_score(tweet: Dict[str, Any]) -> float:
    """
    Calculate popularity score for ranking tweets.
    Uses weighted engagement: views (0.1), likes (0.3), retweets (0.6)
    """
    views = tweet.get("views", 0)
    likes = tweet.get("likes", 0)
    retweets = tweet.get("retweets", 0)
    
    score = (
        views * 0.1 +
        likes * 0.3 +
        retweets * 0.6
    )
    return score


def filter_tweets_by_timeframe(tweets: List[Dict[str, Any]], days: int = 3) -> List[Dict[str, Any]]:
    """
    Filter tweets to only include those from the past N days.
    
    Args:
        tweets: List of tweet dictionaries
        days: Number of days to look back (default: 3 for past 3 days)
    
    Returns:
        Filtered list of tweets from the past N days
    """
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    filtered = []
    for tweet in tweets:
        # Parse timestamp if it's a string
        tweet_time = tweet.get("timestamp")
        if isinstance(tweet_time, str):
            try:
                tweet_time = datetime.fromisoformat(tweet_time.replace('Z', '+00:00'))
            except:
                # If parsing fails, assume it's recent (within timeframe)
                filtered.append(tweet)
                continue
        
        if isinstance(tweet_time, datetime):
            if tweet_time >= cutoff_date:
                filtered.append(tweet)
        else:
            # If no timestamp, assume it's recent
            filtered.append(tweet)
    
    return filtered


async def stage1_scan(keywords: List[str], max_tweets: int = 3, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Stage 1: Broad Scan - Query X API and Rank Top 3 Most Popular Tweets
    
    Process:
    1. Query X API for keyword matches (expands keywords to all variations)
    2. Filter to verified accounts only (藍勾認證帳號 - blue checkmark accounts)
    3. Filter tweets to past 3 days
    4. Rank tweets by popularity (weighted engagement: views, likes, retweets)
    5. Return top 3 most popular tweets
    
    This ensures that searching for "AAPL", "Apple", or "$AAPL" all find tweets
    containing any of these variations from verified accounts, then ranks them by popularity.
    """
    start_time = datetime.now()
    background_text = read_background()
    
    # Set default max_tweets if not provided
    if max_tweets is None:
        max_tweets = 3  # Default to 3 popular tweets
    
    # Step 1: Query X API for keyword matches
    tweets = []
    keyword_expansions = {}
    all_variations_searched = []
    found_keywords = []
    
    if keywords:
        # Check if keyword expansion should be skipped
        # Default: skip expansion for both Mock Database and real API (user preference)
        skip_expansion_default = True  # Skip by default
        skip_expansion = options.get("skip_keyword_expansion", skip_expansion_default) if options else skip_expansion_default
        
        if skip_expansion:
            # Use keywords directly without expansion (faster)
            print(f"⚡ Skipping keyword expansion - using keywords directly: {keywords}")
            keyword_expansions = {kw: [kw] for kw in keywords}  # Each keyword maps to itself
            all_variations_searched = keywords.copy()
        else:
            # Expand each keyword to all variations (slower but more comprehensive)
            print(f"🔍 Expanding keywords to variations...")
            for keyword in keywords:
                expansion = await expand_keyword_to_variations(keyword)
                keyword_expansions[keyword] = expansion["variations"]
            all_variations_searched = []
            for variations in keyword_expansions.values():
                all_variations_searched.extend(variations)
        
        # Query X API for tweets matching keywords/variations
        # Get more tweets than needed so we can rank and filter
        search_start = datetime.now()
        print(f"🔍 [STAGE1] Querying X API for {len(keyword_expansions)} keyword(s)...")
        all_tweets, searched_variations = await search_tweets(keyword_expansions, max_tweets=1000)
        search_duration = (datetime.now() - search_start).total_seconds() * 1000
        print(f"📊 [STAGE1] Found {len(all_tweets)} tweets in {search_duration:.2f}ms")
        if not skip_expansion:
            all_variations_searched = searched_variations
        
        # Step 2: Filter to past 3 days
        tweets_from_past_3_days = filter_tweets_by_timeframe(all_tweets, days=3)
        
        # Step 3: Rank by popularity (calculate popularity score for each tweet)
        for tweet in tweets_from_past_3_days:
            tweet["popularity_score"] = calculate_popularity_score(tweet)
        
        # Sort by popularity score (descending) and take top tweets
        tweets_from_past_3_days.sort(key=lambda x: x.get("popularity_score", 0), reverse=True)
        tweets = tweets_from_past_3_days[:max_tweets]
        
        # Extract keywords found
        found_keywords = list(set(tweet.get("keyword", "") for tweet in tweets))
    else:
        # No keywords provided, return empty result
        tweets = []
    
    # Create Broad Scan Report with top ranked tweets
    broad_scan_report = {
        "tweets": tweets,
        "count": len(tweets),
        "timeframe": "past 3 days",
        "ranking_method": "popularity_score (weighted: views 0.1, likes 0.3, retweets 0.6)",
        "total_tweets_queried": len(all_tweets) if keywords else 0,
        "tweets_from_past_3_days": len(tweets_from_past_3_days) if keywords else 0,
        "query_info": {
            "keywords_searched": keywords,
            "variations_searched": all_variations_searched if keywords else [],
            "filter_applied": "verified accounts only (藍勾認證帳號)",
            "keyword_expansion_skipped": skip_expansion if keywords else False
        }
    }
    
    # Debug logging
    if len(tweets) == 0 and keywords:
        print(f"DEBUG: Broad Scan Report - No tweets found")
        print(f"  Keywords: {keywords}")
        print(f"  Variations searched: {all_variations_searched}")
        print(f"  Total tweets queried: {len(all_tweets)}")
        print(f"  Tweets from past 3 days: {len(tweets_from_past_3_days)}")
    
    result = {
        # Broad Scan Report (now contains top 5 ranked tweets)
        "broad_scan": {
            "report": broad_scan_report,
            "background_text": background_text,
            "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
            "timestamp": start_time.isoformat()
        },
        # Tweet Discovery Results
        "tweets_found": len(tweets),
        "original_keywords": keywords,
        "keyword_expansions": keyword_expansions,
        "all_variations_searched": all_variations_searched,
        "keywords_found": found_keywords,
        "tweets": tweets,
        "search_metadata": {
            "max_tweets": max_tweets,
            "search_time": datetime.now().isoformat(),
            "ranking_applied": True,
            "timeframe_filter": "past 3 days"
        }
    }
    
    if options:
        result["options_applied"] = options
    
    duration = (datetime.now() - start_time).total_seconds() * 1000
    
    return {
        "result": result,
        "duration_ms": duration
    }


async def stage2_scan(stage1_result: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Stage 2: Deep Dive Analysis
    
    Part 1: Thoughts Analysis
    - Analyzes thoughts of discovered tweets (using TextBlob)
    - Optionally enhances analysis with AI for complex cases
    
    Part 2: Deep Dive Analysis
    - Iterates through each tweet found in Stage 1
    - For each tweet, makes LLM call with:
      - Internal Context: Content of background.md
      - External Information: Full text content extracted from the tweet
      - Analytical Task: Evaluate strategic importance and return sentiment (Positive/Neutral/Negative), summary, and reasoning
    - Collects all analyses into Deep Dive Report
    """
    start_time = datetime.now()
    
    # Check if using Mock Database (affects optimization settings)
    use_mock_data = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'
    
    stage1_data = stage1_result.get("result", {})
    tweets = stage1_data.get("tweets", [])
    original_keywords = stage1_data.get("original_keywords", [])
    background_text = stage1_data.get("broad_scan", {}).get("background_text", read_background())
    
    # Part 1: Thoughts Analysis with Weighted Engagement
    analyzed_tweets = []
    thoughts_scores = []
    weighted_thoughts_scores = []  # Thoughts weighted by engagement
    
    for tweet in tweets:
        # Ensure views field exists (default to 0 if missing)
        views = tweet.get("views", 0)
        likes = tweet.get("likes", 0)
        retweets = tweet.get("retweets", 0)
        
        # Use TextBlob for initial thoughts analysis
        thoughts = analyze_thoughts(tweet["text"])
        
        # Optionally enhance with AI for ambiguous cases (low confidence)
        if thoughts["confidence"] < 0.3:
            try:
                context = tweet.get("original_keyword", "")
                ai_thoughts = await analyze_thoughts_with_ai(tweet["text"], context)
                # Use AI result if available, otherwise keep TextBlob result
                if ai_thoughts.get("thoughts_score") is not None:
                    thoughts = {
                        "score": ai_thoughts.get("thoughts_score", thoughts["score"]),
                        "label": ai_thoughts.get("thoughts_label", thoughts["label"]),
                        "confidence": ai_thoughts.get("confidence", thoughts["confidence"]),
                        "ai_enhanced": True,
                        "reasoning": ai_thoughts.get("reasoning", "")
                    }
            except Exception as e:
                # If AI fails, continue with TextBlob result
                pass
        
        # Calculate weighted engagement
        weighted_engagement = calculate_weighted_engagement(likes, retweets, views)
        
        tweet_with_thoughts = {
            **tweet,
            "views": views,  # Ensure views is included
            "thoughts_score": thoughts["score"],
            "thoughts_label": thoughts["label"],
            "thoughts_confidence": thoughts["confidence"],
            "weighted_engagement": weighted_engagement
        }
        
        if thoughts.get("ai_enhanced"):
            tweet_with_thoughts["ai_enhanced"] = True
            tweet_with_thoughts["ai_reasoning"] = thoughts.get("reasoning", "")
        
        analyzed_tweets.append(tweet_with_thoughts)
        thoughts_scores.append(thoughts["score"])
        
        # Calculate weighted thoughts (thoughts * engagement weight)
        # Higher engagement = more influence on overall thoughts
        weighted_thoughts = thoughts["score"] * weighted_engagement
        weighted_thoughts_scores.append(weighted_thoughts)
    
    # Calculate aggregate metrics (both unweighted and weighted)
    if thoughts_scores:
        # Unweighted average (simple mean)
        avg_thoughts = sum(thoughts_scores) / len(thoughts_scores)
        
        # Weighted average (engagement-weighted)
        # Will be calculated after total_weighted_engagement is computed
        
        # Counts (unweighted)
        positive_count = sum(1 for s in thoughts_scores if s > 0.1)
        negative_count = sum(1 for s in thoughts_scores if s < -0.1)
        neutral_count = len(thoughts_scores) - positive_count - negative_count
        
        # Weighted counts (considering engagement)
        weighted_positive = sum(
            tweet.get("weighted_engagement", 0) 
            for tweet in analyzed_tweets 
            if tweet.get("thoughts_score", 0) > 0.1
        )
        weighted_negative = sum(
            tweet.get("weighted_engagement", 0) 
            for tweet in analyzed_tweets 
            if tweet.get("thoughts_score", 0) < -0.1
        )
        weighted_neutral = sum(
            tweet.get("weighted_engagement", 0) 
            for tweet in analyzed_tweets 
            if -0.1 <= tweet.get("thoughts_score", 0) <= 0.1
        )
        
        # Calculate total weighted engagement
        total_weighted_engagement = sum(tweet.get("weighted_engagement", 0) for tweet in analyzed_tweets)
        
        # Calculate weighted average thoughts
        if total_weighted_engagement > 0:
            weighted_avg_thoughts = sum(weighted_thoughts_scores) / total_weighted_engagement
        else:
            weighted_avg_thoughts = avg_thoughts
    else:
        avg_thoughts = 0.0
        weighted_avg_thoughts = 0.0
        positive_count = negative_count = neutral_count = 0
        weighted_positive = weighted_negative = weighted_neutral = 0.0
        total_weighted_engagement = 0.0
    
    # Part 2: Deep Dive Analysis
    deep_dive_start = datetime.now()
    deep_dive_analyses = []
    
    # Prepare tasks for parallel LLM calls (optimization: process all tweets concurrently)
    async def analyze_single_tweet(tweet: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single tweet and return analysis result"""
        tweet_text = tweet.get("text", "")
        tweet_id = tweet.get("id", "")
        
        if not tweet_text:
            return None
        
        try:
            # Perform deep dive analysis on tweet text
            # Internal Context: background.md content
            # External Information: Full text content extracted from the tweet
            analysis = await perform_deep_dive_analysis(
                tweet_text=tweet_text,
                background_text=background_text,
                tweet_id=tweet_id
            )
            
            # Add tweet context to analysis
            analysis["tweet_id"] = tweet_id
            analysis["tweet_author"] = tweet.get("author", "")
            # Generate X.com link to the tweet itself
            author_username = tweet.get("author", "").replace("@", "")
            if tweet_id and author_username:
                analysis["tweet_x_url"] = f"https://x.com/{author_username}/status/{tweet_id}"
            else:
                analysis["tweet_x_url"] = None
            # Store external URLs found in tweet text (e.g., bloomberg.com, reuters.com) - these are links IN the tweet, not the tweet itself
            analysis["tweet_urls"] = extract_urls_from_text(tweet_text)
            
            return analysis
        except Exception as e:
            # If analysis fails, return error entry
            return {
                "tweet_id": tweet_id,
                "tweet_text": tweet_text[:200] if tweet_text else "",
                "sentiment": "Neutral",
                "summary": f"Error analyzing tweet: {str(e)}",
                "reasoning": "Unable to analyze tweet content",
                "error": str(e)
            }
    
    # Check if using Mock Database (no need for optimizations)
    use_mock_data = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'
    
    # Execute LLM calls: parallel for API (optimized) or sequential for Mock Database (no optimization needed)
    if analyzed_tweets:
        llm_start = datetime.now()
        if use_mock_data:
            # Sequential processing for Mock Database (no optimization needed, more reliable)
            print(f"🚀 [STAGE2] Processing {len(analyzed_tweets)} tweets sequentially for Deep Dive Analysis (Mock Database mode)...")
            for tweet in analyzed_tweets:
                try:
                    result = await analyze_single_tweet(tweet)
                    if result is not None:
                        deep_dive_analyses.append(result)
                except Exception as e:
                    deep_dive_analyses.append({
                        "sentiment": "Neutral",
                        "summary": f"Error analyzing tweet: {str(e)}",
                        "reasoning": "Analysis error",
                        "error": str(e)
                    })
        else:
            # Parallel processing for real API (optimized for speed)
            print(f"🚀 [STAGE2] Processing {len(analyzed_tweets)} tweets in parallel for Deep Dive Analysis...")
            analysis_tasks = [analyze_single_tweet(tweet) for tweet in analyzed_tweets]
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results and filter out None values
            for result in results:
                if isinstance(result, Exception):
                    # Handle exceptions from gather
                    deep_dive_analyses.append({
                        "sentiment": "Neutral",
                        "summary": f"Error during parallel analysis: {str(result)}",
                        "reasoning": "Parallel processing error",
                        "error": str(result)
                    })
                elif result is not None:
                    deep_dive_analyses.append(result)
        
        llm_duration = (datetime.now() - llm_start).total_seconds() * 1000
        print(f"✅ [STAGE2] Completed {len(analyzed_tweets)} LLM calls in {llm_duration:.2f}ms (avg: {llm_duration/len(analyzed_tweets):.2f}ms per tweet)")
    else:
        print("⚠️ No tweets to analyze in Deep Dive")
    
    deep_dive_duration = (datetime.now() - deep_dive_start).total_seconds() * 1000
    
    # Generate basic insights
    basic_insights = []
    if avg_thoughts > 0.3:
        basic_insights.append("Overall thoughts are strongly positive")
    elif avg_thoughts > 0.1:
        basic_insights.append("Overall thoughts are positive")
    elif avg_thoughts < -0.3:
        basic_insights.append("Overall thoughts are strongly negative")
    elif avg_thoughts < -0.1:
        basic_insights.append("Overall thoughts are negative")
    else:
        basic_insights.append("Overall thoughts are neutral")
    
    basic_insights.append(f"Found {positive_count} positive, {negative_count} negative, and {neutral_count} neutral tweets")
    
    # Generate AI-powered insights
    # For Mock Database: enable by default (no timeout concerns)
    # For real API: skip by default to prevent 504 timeout
    ai_insights = []
    skip_ai_insights = not use_mock_data  # Enable for Mock Database, skip for real API by default
    if options and options.get("skip_ai_insights") is not None:
        skip_ai_insights = options.get("skip_ai_insights", skip_ai_insights)
    
    if not skip_ai_insights:
        try:
            aggregate_thoughts = {
                "average_score": round(avg_thoughts, 3),
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "total_tweets": len(analyzed_tweets)
            }
            # Add timeout: longer for Mock Database, shorter for real API
            timeout_seconds = 20.0 if use_mock_data else 10.0
            ai_insights = await asyncio.wait_for(
                generate_insights_with_ai(
                    analyzed_tweets,
                    original_keywords,
                    aggregate_thoughts
                ),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            print("⚠️ AI insights generation timed out, skipping...")
            ai_insights = []
        except Exception as e:
            # If AI insights fail, use basic insights only
            print(f"AI insights generation failed: {e}")
    
    # Combine insights (AI insights first, then basic)
    insights = ai_insights + basic_insights if ai_insights else basic_insights
    
    # Compile final results
    final_result = {
        # Thoughts Analysis Results
        "analyzed_tweets": analyzed_tweets,
        "aggregate_thoughts": {
            "average_score": round(avg_thoughts, 3),
            "weighted_average_score": round(weighted_avg_thoughts, 3),  # Engagement-weighted
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "total_tweets": len(analyzed_tweets),
            # Weighted engagement metrics
            "weighted_positive": round(weighted_positive, 2),
            "weighted_negative": round(weighted_negative, 2),
            "weighted_neutral": round(weighted_neutral, 2),
            "total_weighted_engagement": round(total_weighted_engagement, 2),
            "engagement_weights": ENGAGEMENT_WEIGHTS
        },
        "insights": insights,
        "ai_insights_count": len(ai_insights),
        "recommendations": [
            "Monitor thoughts trends over time",
            "Track engagement metrics (likes, retweets, views)",
            "Compare thoughts across different keywords"
        ],
        # Deep Dive Report
        "deep_dive": {
            "report": deep_dive_analyses,
            "tweets_analyzed": len(deep_dive_analyses),
            "total_tweets": len(analyzed_tweets),
            "duration_ms": deep_dive_duration,
            "timestamp": deep_dive_start.isoformat()
        }
    }
    
    if options:
        final_result["options_applied"] = options
    
    duration = (datetime.now() - start_time).total_seconds() * 1000
    
    return {
        "result": final_result,
        "duration_ms": duration
    }


@app.post("/scan", response_model=ScanResponse)
async def run_thoughts_scan(request: ScanRequest):
    """
    Run a two-stage thoughts scan workflow
    
    - **Stage 1: Broad Scan**
      - Queries X API for keyword matches (expands keywords to all variations)
      - Filters tweets to past 3 days
      - Ranks tweets by popularity (weighted engagement: views, likes, retweets)
      - Returns top 3 most popular tweets as Broad Scan Report
    
    - **Stage 2: Deep Dive Analysis**
      - Iterates through each tweet found in Stage 1
      - For each tweet, makes LLM call with:
        - Internal Context: Content of background.md
        - External Information: Full text content extracted from the tweet
        - Analytical Task: Evaluate strategic importance and return sentiment (Positive/Neutral/Negative), summary, and reasoning
      - Returns Deep Dive Report with sentiment ratings for each tweet
    
    Returns a single JSON object containing both Broad Scan Report and Deep Dive Report.
    
    **Note**: Processing time is typically 15-30 seconds. If timeout occurs, reduce max_tweets.
    """
    scan_start_time = datetime.now()
    scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Check if using Mock Database (no need for strict limits)
    use_mock_data = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'
    
    # Set max_tweets: default to 3 popular tweets
    max_tweets = request.max_tweets or 3  # Default to 3 popular tweets
    max_tweets = min(max_tweets, 10)  # Cap at 10 maximum
    
    # Log scan start
    print(f"🚀 [SCAN {scan_id}] Starting scan with keywords: {request.keywords}, max_tweets: {max_tweets}")
    
    try:
        # Stage 1: Tweet Discovery
        stage1_start = datetime.now()
        print(f"⏱️  [SCAN {scan_id}] Stage 1 started at {stage1_start.isoformat()}")
        stage1_data = await stage1_scan(request.keywords, max_tweets, request.options)
        stage1_duration = stage1_data["duration_ms"]
        print(f"✅ [SCAN {scan_id}] Stage 1 completed in {stage1_duration:.2f}ms")
        
        stage1_result = ScanStageResult(
            stage=1,
            status="completed",
            result=stage1_data["result"],
            timestamp=stage1_start.isoformat(),
            duration_ms=stage1_duration
        )
        
        # Stage 2: Thoughts Analysis (uses stage 1 results)
        stage2_start = datetime.now()
        print(f"⏱️  [SCAN {scan_id}] Stage 2 started at {stage2_start.isoformat()}")
        stage2_data = await stage2_scan(stage1_data, request.options)
        stage2_duration = stage2_data["duration_ms"]
        print(f"✅ [SCAN {scan_id}] Stage 2 completed in {stage2_duration:.2f}ms")
        
        stage2_result = ScanStageResult(
            stage=2,
            status="completed",
            result=stage2_data["result"],
            timestamp=stage2_start.isoformat(),
            duration_ms=stage2_duration
        )
        
        # Calculate total duration
        total_duration = (datetime.now() - scan_start_time).total_seconds() * 1000
        
        # Log completion
        print(f"🎉 [SCAN {scan_id}] Scan completed successfully!")
        print(f"   Stage 1: {stage1_duration:.2f}ms ({stage1_duration/total_duration*100:.1f}%)")
        print(f"   Stage 2: {stage2_duration:.2f}ms ({stage2_duration/total_duration*100:.1f}%)")
        print(f"   Total: {total_duration:.2f}ms")
        
        # Include expanded keywords in response
        expanded_keywords = stage1_data["result"].get("all_variations_searched", request.keywords)
        
        return ScanResponse(
            scan_id=scan_id,
            status="completed",
            keywords=expanded_keywords,  # Return expanded keywords
            stage1=stage1_result,
            stage2=stage2_result,
            total_duration_ms=total_duration,
            timestamp=scan_start_time.isoformat()
        )
        
    except Exception as e:
        error_duration = (datetime.now() - scan_start_time).total_seconds() * 1000
        print(f"❌ [SCAN {scan_id}] Scan failed after {error_duration:.2f}ms: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Scan failed: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint - serves frontend"""
    html_path = os.path.join("static", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {
        "message": "Sentiment Alpha Radar API",
        "version": "1.0.0",
        "endpoints": {
            "scan": "/scan (POST)",
            "docs": "/docs",
            "health": "/health"
        }
    }


async def search_tickers_yfinance(query: str, limit: int = 10) -> List[TickerResult]:
    """
    Search for tickers using yfinance (Yahoo Finance)
    This is a free method that doesn't require API keys
    """
    try:
        import yfinance as yf
        
        # Try to get ticker info directly if query looks like a symbol
        query_upper = query.upper().strip()
        
        # If it's a short symbol (1-5 chars), try direct lookup
        if len(query_upper) <= 5 and query_upper.isalpha():
            try:
                ticker = yf.Ticker(query_upper)
                info = ticker.info
                if info and 'symbol' in info:
                    return [TickerResult(
                        symbol=info.get('symbol', query_upper),
                        name=info.get('longName') or info.get('shortName', query_upper),
                        exchange=info.get('exchange', ''),
                        type=info.get('quoteType', 'EQUITY')
                    )]
            except:
                pass
        
        # For company name searches, use a fallback approach
        # Note: yfinance doesn't have a direct search API, so we'll use Finnhub as fallback
        return []
    except ImportError:
        # yfinance not installed, fall back to Finnhub
        return []


async def search_tickers_finnhub(query: str, limit: int = 10, api_key: Optional[str] = None) -> List[TickerResult]:
    """
    Search for tickers using Finnhub API (free tier available)
    Requires API key - set FINNHUB_API_KEY environment variable
    """
    api_key = api_key or os.getenv('FINNHUB_API_KEY')
    
    if not api_key:
        # Return empty if no API key
        return []
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"https://finnhub.io/api/v1/search"
            params = {
                "q": query,
                "token": api_key
            }
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Finnhub returns results in 'result' field
                for item in data.get('result', [])[:limit]:
                    results.append(TickerResult(
                        symbol=item.get('symbol', ''),
                        name=item.get('description', ''),
                        exchange=item.get('displaySymbol', '').split('.')[0] if '.' in item.get('displaySymbol', '') else '',
                        type=item.get('type', 'EQUITY')
                    ))
                
                return results
    except Exception as e:
        print(f"Finnhub API error: {e}")
    
    return []


async def search_tickers_openfigi(query: str, limit: int = 10) -> List[TickerResult]:
    """
    Search for tickers using OpenFIGI API (free, no API key required)
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = "https://api.openfigi.com/v3/search"
            payload = [{
                "query": query,
                "exchCode": "US"  # Focus on US markets
            }]
            headers = {"Content-Type": "application/json"}
            
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item_list in data:
                    for item in item_list.get('data', [])[:limit]:
                        results.append(TickerResult(
                            symbol=item.get('ticker', ''),
                            name=item.get('name', ''),
                            exchange=item.get('exchCode', ''),
                            type=item.get('securityType', 'EQUITY')
                        ))
                
                return results[:limit]
    except Exception as e:
        print(f"OpenFIGI API error: {e}")
    
    return []


@app.get("/api/tickers/search", response_model=TickerSearchResponse)
async def search_tickers(
    q: str = Query(..., description="Search query (ticker symbol or company name)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """
    Search for ticker symbols and company names
    
    Uses multiple free APIs:
    1. yfinance (Yahoo Finance) - for direct ticker lookups
    2. OpenFIGI - free public API (no key required)
    3. Finnhub - free tier (requires FINNHUB_API_KEY env var)
    
    Returns matching ticker symbols and company names.
    """
    query = q.strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    results = []
    
    # Try yfinance first (best for direct symbol lookups)
    try:
        yf_results = await search_tickers_yfinance(query, limit)
        results.extend(yf_results)
    except Exception as e:
        print(f"yfinance search error: {e}")
    
    # Try OpenFIGI (free, no API key)
    try:
        figi_results = await search_tickers_openfigi(query, limit)
        # Avoid duplicates
        existing_symbols = {r.symbol for r in results}
        for r in figi_results:
            if r.symbol and r.symbol not in existing_symbols:
                results.append(r)
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"OpenFIGI search error: {e}")
    
    # Try Finnhub if API key is available
    if len(results) < limit:
        try:
            finnhub_results = await search_tickers_finnhub(query, limit - len(results))
            existing_symbols = {r.symbol for r in results}
            for r in finnhub_results:
                if r.symbol and r.symbol not in existing_symbols:
                    results.append(r)
                    if len(results) >= limit:
                        break
        except Exception as e:
            print(f"Finnhub search error: {e}")
    
    # If no results, provide some common tickers as fallback
    if not results and len(query) <= 5:
        # Common ticker symbols that might match
        common_tickers = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.',
            'NVDA': 'NVIDIA Corporation',
            'JPM': 'JPMorgan Chase & Co.',
            'V': 'Visa Inc.',
            'JNJ': 'Johnson & Johnson'
        }
        
        query_upper = query.upper()
        for symbol, name in common_tickers.items():
            if query_upper in symbol or query_upper in name.upper():
                results.append(TickerResult(
                    symbol=symbol,
                    name=name,
                    exchange='NASDAQ' if symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA'] else 'NYSE',
                    type='EQUITY'
                ))
                if len(results) >= limit:
                    break
    
    return TickerSearchResponse(
        query=query,
        results=results[:limit],
        count=len(results)
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
