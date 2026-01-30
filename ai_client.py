"""
AI Client for AI Builders API integration
Uses OpenAI SDK with custom base URL and model
"""
import os
import asyncio
from typing import Optional, List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
AI_BUILDER_TOKEN = os.getenv("AI_BUILDER_TOKEN")
AI_BUILDER_BASE_URL = "https://space.ai-builders.com/backend"
AI_BUILDER_MODEL = "supermind-agent-v1"

if not AI_BUILDER_TOKEN:
    raise ValueError(
        "AI_BUILDER_TOKEN not found in environment variables. "
        "Please create a .env file with AI_BUILDER_TOKEN=your_api_key"
    )

# Initialize OpenAI client with custom base URL
client = OpenAI(
    api_key=AI_BUILDER_TOKEN,
    base_url=f"{AI_BUILDER_BASE_URL}/v1"
)


async def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a chat completion using the AI Builders API
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        model: Model to use (defaults to supermind-agent-v1)
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters
    
    Returns:
        Response dict with completion data
    """
    try:
        response = client.chat.completions.create(
            model=model or AI_BUILDER_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return {
            "id": response.id,
            "model": response.model,
            "choices": [
                {
                    "index": choice.index,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content
                    },
                    "finish_reason": choice.finish_reason
                }
                for choice in response.choices
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except Exception as e:
        raise Exception(f"AI API error: {str(e)}")


async def analyze_sentiment_with_ai(
    text: str,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze sentiment using AI Builders API
    
    Args:
        text: Text to analyze
        context: Optional context (e.g., company name, ticker symbol)
    
    Returns:
        Dict with sentiment analysis results
    """
    system_prompt = """You are a sentiment analysis expert. Analyze the sentiment/opinions expressed in the given text and return a JSON response with:
- sentiment_score: A float between -1 (very negative) and 1 (very positive)
- sentiment_label: One of "positive", "negative", or "neutral"
- confidence: A float between 0 and 1 indicating confidence
- reasoning: Brief explanation of the sentiment analysis

Focus on financial and market sentiment/opinions when analyzing stock-related content."""

    user_prompt = f"Analyze the sentiment expressed in this text"
    if context:
        user_prompt += f" related to {context}"
    user_prompt += f":\n\n{text}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = await chat_completion(
            messages=messages,
            temperature=0.3,  # Lower temperature for more consistent sentiment analysis
            max_tokens=200
        )
        
        content = response["choices"][0]["message"]["content"]
        
        # Try to parse JSON from response
        import json
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            # Fallback: extract sentiment from text response
            content_lower = content.lower()
            if "positive" in content_lower:
                sentiment_label = "positive"
                sentiment_score = 0.5
            elif "negative" in content_lower:
                sentiment_label = "negative"
                sentiment_score = -0.5
            else:
                sentiment_label = "neutral"
                sentiment_score = 0.0
            
            return {
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "confidence": 0.7,
                "reasoning": content
            }
    except Exception as e:
        # Fallback to TextBlob if AI fails
        from textblob import TextBlob
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        return {
            "sentiment_score": round(polarity, 3),
            "sentiment_label": label,
            "confidence": round(abs(polarity), 3),
            "reasoning": f"Fallback analysis: {str(e)}"
        }


async def perform_broad_scan(background_text: str) -> Dict[str, Any]:
    """
    Perform a broad scan to identify top 10 most popular relevant tweets within a week
    
    Args:
        background_text: The strategic background text from background.md
    
    Returns:
        Dict with broad scan results including top 10 popular tweets and their details
    """
    system_prompt = """You are a strategic research analyst specializing in social media sentiment analysis for financial markets.
Your task is to analyze strategic background information and identify the top 10 most popular relevant tweets within the past week on X (Twitter).

Based on the strategic background, identify tweets that would be highly relevant and popular (high engagement: likes, retweets, views).
Consider:
- Tweets about ticker symbols, company names, and $ mentions related to the background
- High-engagement tweets (viral or trending content)
- Tweets from influential accounts in finance/trading
- Tweets that match the strategic focus areas
- Content from the past week that gained significant traction

Return your analysis as a structured response with the top 10 most popular relevant tweets."""

    user_prompt = f"""Based on the following strategic background, survey the top 10 most popular relevant tweets within a week for a broad search on X:

{background_text}

Provide:
1. A list of exactly 10 tweets that would be most popular and relevant
2. For each tweet, include:
   - Tweet content/text (what the tweet would say)
   - Estimated engagement metrics (likes, retweets, views - use realistic numbers for popular tweets)
     * Views: Typically highest (e.g., 5K-50K for popular tweets)
     * Likes: Moderate (e.g., 100-2K for popular tweets)
     * Retweets: Lower but significant (e.g., 20-500 for popular tweets)
   - Author/account type (e.g., "Financial analyst", "Trading influencer", "Company account")
   - Relevance explanation (why this tweet is relevant to the strategic background)
   - Keywords/topics covered

Format your response as a numbered list (1-10) with clear structure for each tweet.
Focus on tweets that would realistically be popular (high engagement) and directly relevant to the strategic background."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = await chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=2000  # Increased for 10 tweets with details
        )
        
        content = response["choices"][0]["message"]["content"]
        
        # Parse the response to extract tweets
        tweets = []
        lines = content.split('\n')
        current_tweet = None
        
        import re
        
        # Try to parse structured tweet data
        tweet_patterns = [
            r'(\d+)\.\s*(?:Tweet|Content|Text)[:\s]*(.+?)(?=\d+\.|Likes|Retweets|Author|Keywords|$)',
            r'(\d+)\.\s*(.+?)(?=\d+\.|Likes|Retweets|Author|Keywords|$)',
        ]
        
        # Parse by looking for numbered entries and extracting tweet info
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Check if this is a numbered tweet (1., 2., etc.)
            match = re.match(r'^(\d+)\.', line)
            if match:
                tweet_num = int(match.group(1))
                if 1 <= tweet_num <= 10:
                    # Extract tweet content (text after number)
                    tweet_text = line.lstrip('1234567890.-').strip()
                    
                    # Look ahead for additional details
                    tweet_data = {
                        "number": tweet_num,
                        "text": tweet_text,
                        "likes": 0,
                        "retweets": 0,
                        "views": 0,
                        "author_type": "",
                        "relevance": "",
                        "keywords": []
                    }
                    
                    # Parse following lines for details
                    j = i + 1
                    while j < len(lines) and j < i + 10:  # Look ahead up to 10 lines
                        next_line = lines[j].strip()
                        if next_line and re.match(r'^\d+\.', next_line):
                            break  # Found next tweet
                        
                        # Extract likes
                        likes_match = re.search(r'(?:Likes|likes|❤️)[:\s]*(\d+[KMB]?)', next_line, re.IGNORECASE)
                        if likes_match:
                            likes_str = likes_match.group(1)
                            tweet_data["likes"] = parse_engagement_number(likes_str)
                        
                        # Extract retweets
                        retweets_match = re.search(r'(?:Retweets|retweets|🔄)[:\s]*(\d+[KMB]?)', next_line, re.IGNORECASE)
                        if retweets_match:
                            retweets_str = retweets_match.group(1)
                            tweet_data["retweets"] = parse_engagement_number(retweets_str)
                        
                        # Extract views
                        views_match = re.search(r'(?:Views|views|👁️|👁)[:\s]*(\d+[KMB]?)', next_line, re.IGNORECASE)
                        if views_match:
                            views_str = views_match.group(1)
                            tweet_data["views"] = parse_engagement_number(views_str)
                        
                        # Extract author type
                        author_match = re.search(r'(?:Author|author|Account|account)[:\s]*(.+)', next_line, re.IGNORECASE)
                        if author_match:
                            tweet_data["author_type"] = author_match.group(1).strip()
                        
                        # Extract relevance
                        relevance_match = re.search(r'(?:Relevance|relevance|Why|why)[:\s]*(.+)', next_line, re.IGNORECASE)
                        if relevance_match:
                            tweet_data["relevance"] = relevance_match.group(1).strip()
                        
                        # Extract keywords
                        keywords_match = re.search(r'(?:Keywords|keywords|Topics|topics)[:\s]*(.+)', next_line, re.IGNORECASE)
                        if keywords_match:
                            keywords_str = keywords_match.group(1).strip()
                            tweet_data["keywords"] = [k.strip() for k in keywords_str.split(',') if k.strip()]
                        
                        # If line doesn't match any pattern but is substantial, add to tweet text
                        if not any([likes_match, retweets_match, author_match, relevance_match, keywords_match]):
                            if len(next_line) > 20 and not next_line.startswith('-'):
                                tweet_data["text"] += " " + next_line
                        
                        j += 1
                    
                    tweets.append(tweet_data)
                    i = j
                    continue
            
            i += 1
        
        # If parsing didn't work well, try simpler extraction
        if len(tweets) < 5:
            # Fallback: extract numbered items as tweets
            numbered_items = re.findall(r'(\d+)\.\s*(.+?)(?=\n\d+\.|\n\n|$)', content, re.DOTALL)
            for num, text in numbered_items[:10]:
                if 1 <= int(num) <= 10:
                    clean_text = ' '.join(text.split()[:50])  # First 50 words
                    tweets.append({
                        "number": int(num),
                        "text": clean_text,
                        "likes": 0,
                        "retweets": 0,
                        "views": 0,
                        "author_type": "",
                        "relevance": "",
                        "keywords": []
                    })
        
        # Sort by number and ensure we have exactly 10
        tweets.sort(key=lambda x: x["number"])
        tweets = tweets[:10]
        
        return {
            "tweets": tweets,
            "full_response": content,
            "count": len(tweets),
            "timeframe": "within a week"
        }
    except Exception as e:
        # Fallback: return default tweets based on background
        return {
            "tweets": [
                {
                    "number": 1,
                    "text": "Popular tweet about ticker symbols and sentiment analysis",
                    "likes": 0,
                    "retweets": 0,
                    "views": 0,
                    "author_type": "Financial analyst",
                    "relevance": "Related to strategic background",
                    "keywords": []
                }
            ],
            "full_response": f"Error generating broad scan: {str(e)}",
            "count": 1,
            "timeframe": "within a week",
            "error": str(e)
        }


def parse_engagement_number(value: str) -> int:
    """
    Parse engagement numbers like "1.5K", "2M", "500" to integers
    
    Args:
        value: String like "1.5K", "2M", "500"
    
    Returns:
        Integer value
    """
    if not value:
        return 0
    
    value = value.strip().upper()
    
    try:
        if 'K' in value:
            num = float(value.replace('K', ''))
            return int(num * 1000)
        elif 'M' in value:
            num = float(value.replace('M', ''))
            return int(num * 1000000)
        elif 'B' in value:
            num = float(value.replace('B', ''))
            return int(num * 1000000000)
        else:
            return int(float(value))
    except (ValueError, AttributeError):
        return 0


async def extract_url_content(url: str) -> str:
    """
    Extract text content from a URL
    
    Args:
        url: URL to extract content from
    
    Returns:
        Extracted text content
    """
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            response.raise_for_status()
            
            # Parse HTML content
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit to reasonable length (first 5000 characters)
            return text[:5000] if len(text) > 5000 else text
    except Exception as e:
        return f"Error extracting content from URL: {str(e)}"


async def perform_deep_dive_analysis(
    tweet_text: str,
    background_text: str,
    tweet_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform deep dive analysis on a tweet using AI
    
    Args:
        tweet_text: The full text content of the tweet
        background_text: Strategic background from background.md
        tweet_id: Optional tweet ID for reference
    
    Returns:
        Dict with sentiment, summary, and reasoning
    """
    system_prompt = """You are a strategic analyst evaluating external information against internal strategic context.
Your task is to evaluate the sentiment of external information based on internal context.

Return ONLY a valid JSON object with these exact fields:
- sentiment: A string value of "Positive", "Neutral", or "Negative"
- summary: A one-sentence summary of the external information
- reasoning: A brief explanation for your sentiment rating

Do not include any markdown formatting, code blocks, or additional text. Return only the JSON object."""

    user_prompt = f"""Internal Context:
{background_text}

External Information:
{tweet_text}

Analytical Task: Based on the internal context, evaluate the strategic importance of the external information. Return a single JSON object with the following fields: sentiment (a string: 'Positive', 'Neutral', or 'Negative'), summary (a one-sentence summary), and reasoning (a brief explanation for your sentiment rating)."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        # Check if using Mock Database (no need for strict limits)
        import os
        use_mock_data = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'
        
        # Adjust timeout and tokens based on data source
        timeout_seconds = 15.0 if use_mock_data else 6.0
        max_tokens_value = 300 if use_mock_data else 200
        
        # Add timeout: longer for Mock Database, shorter for real API
        response = await asyncio.wait_for(
            chat_completion(
                messages=messages,
                temperature=0.5,  # Lower temperature for more consistent analysis
                max_tokens=max_tokens_value
            ),
            timeout=timeout_seconds
        )
        
        content = response["choices"][0]["message"]["content"].strip()
        
        # Extract JSON from response
        import json
        import re
        
        # Try to find JSON in the response
        json_match = re.search(r'\{[^{}]*"sentiment"[^{}]*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content
        
        # Parse JSON
        result = json.loads(json_str)
        
        # Validate required fields
        if "sentiment" not in result:
            result["sentiment"] = "Neutral"
        if "summary" not in result:
            result["summary"] = "Tweet analyzed for strategic importance"
        if "reasoning" not in result:
            result["reasoning"] = "Analysis completed"
        
        # Ensure sentiment is valid (handle case variations and misspellings)
        sentiment_value = result.get("sentiment", "Neutral")
        if isinstance(sentiment_value, str):
            sentiment_value = sentiment_value.capitalize()
            # Handle misspellings: "Postive" -> "Positive"
            if sentiment_value.startswith("Post") or sentiment_value.startswith("Pos"):
                sentiment_value = "Positive"
            elif sentiment_value.startswith("Neg"):
                sentiment_value = "Negative"
            elif sentiment_value not in ["Positive", "Neutral", "Negative"]:
                sentiment_value = "Neutral"
        result["sentiment"] = sentiment_value
        
        result["tweet_id"] = tweet_id
        result["tweet_text"] = tweet_text[:200]  # Store first 200 chars for reference
        result["raw_response"] = content
        
        return result
    except json.JSONDecodeError as e:
        # Fallback if JSON parsing fails
        return {
            "tweet_id": tweet_id,
            "tweet_text": tweet_text[:200] if tweet_text else "",
            "sentiment": "Neutral",
            "summary": "Unable to parse AI response",
            "reasoning": f"JSON parsing error: {str(e)}. Raw response: {content[:200] if 'content' in locals() else 'N/A'}",
            "raw_response": content if 'content' in locals() else "",
            "error": str(e)
        }
    except Exception as e:
        return {
            "tweet_id": tweet_id,
            "tweet_text": tweet_text[:200] if tweet_text else "",
            "sentiment": "Neutral",
            "summary": "Analysis unavailable",
            "reasoning": f"Error during analysis: {str(e)}",
            "raw_response": "",
            "error": str(e)
        }


async def generate_insights_with_ai(
    tweets: List[Dict[str, Any]],
    keywords: List[str],
    aggregate_sentiment: Dict[str, Any]
) -> List[str]:
    """
    Generate insights using AI Builders API based on sentiment analysis results
    
    Args:
        tweets: List of analyzed tweets
        keywords: Keywords that were searched
        aggregate_sentiment: Aggregate sentiment metrics
    
    Returns:
        List of insight strings
    """
    system_prompt = """You are a financial market analyst. Analyze sentiment data and provide actionable insights.
Focus on:
- Overall market sentiment trends
- Notable patterns in the data
- Potential implications for investors
- Key takeaways

Keep insights concise (1-2 sentences each) and professional."""

    user_prompt = f"""Analyze this sentiment data and provide 3-5 key insights:

Keywords analyzed: {', '.join(keywords)}
Total tweets: {aggregate_sentiment.get('total_tweets', 0)}
Average sentiment score: {aggregate_sentiment.get('average_score', 0)}
Positive tweets: {aggregate_sentiment.get('positive_count', 0)}
Negative tweets: {aggregate_sentiment.get('negative_count', 0)}
Neutral tweets: {aggregate_sentiment.get('neutral_count', 0)}

Sample tweets analyzed:
{chr(10).join([f"- {tweet.get('text', '')[:100]}..." for tweet in tweets[:5]])}

Provide insights as a bulleted list."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = await chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        content = response["choices"][0]["message"]["content"]
        
        # Extract bullet points
        insights = []
        for line in content.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                insight = line.lstrip('-•*').strip()
                if insight:
                    insights.append(insight)
            elif line and len(line) > 20:  # Also capture non-bulleted insights
                insights.append(line)
        
        return insights[:5]  # Limit to 5 insights
    except Exception as e:
        # Fallback insights
        return [
            f"Analyzed {aggregate_sentiment.get('total_tweets', 0)} tweets across {len(keywords)} keywords",
            f"Overall sentiment score is {aggregate_sentiment.get('average_score', 0):.2f}",
            f"AI insight generation unavailable: {str(e)}"
        ]
