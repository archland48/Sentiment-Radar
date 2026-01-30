# Sentiment Alpha Radar

A full-stack application for analyzing user sentiment on X (Twitter) for various keywords including ticker symbols, company names, and $ mentions.

## Overview

Sentiment Alpha Radar performs a two-stage workflow:
1. **Stage 1: Tweet Discovery** - Searches for tweets matching keywords (ticker symbols, company names, $)
2. **Stage 2: Sentiment Analysis** - Analyzes sentiment of discovered tweets and provides aggregate metrics

## Features

- 🔍 **Smart Keyword Expansion** - Enter "AAPL", "Apple", or "$AAPL" and the system automatically searches for ALL variations
- 🔎 **Ticker Autocomplete** - Search and autocomplete ticker symbols and company names using free APIs
- 📊 **Hybrid Sentiment Analysis** - Combines TextBlob with AI-powered analysis for enhanced accuracy
- 🤖 **AI-Powered Insights** - Uses AI Builders API (supermind-agent-v1) to generate actionable market insights
- 📈 Aggregate sentiment metrics and insights
- 🎨 Modern, responsive web interface
- ⚡ Fast two-stage processing workflow
- 📱 Mobile-friendly design

### Keyword Expansion

The system intelligently expands keywords to search for all related variations:
- **Input**: "AAPL" → **Searches**: AAPL, Apple, $AAPL, Apple Inc.
- **Input**: "Apple" → **Searches**: AAPL, Apple, $AAPL, Apple Inc.
- **Input**: "$AAPL" → **Searches**: AAPL, Apple, $AAPL, Apple Inc.

This ensures comprehensive tweet discovery since searching X with different keywords yields different results, even though they refer to the same company.

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Download TextBlob data (required for sentiment analysis):
```bash
python -m textblob.download_corpora
```

3. Set up environment variables:
```bash
# Copy the example .env file
cp .env.example .env

# Edit .env and add your AI_BUILDER_TOKEN
# The token is provided by your instructor
```

The `.env` file should contain:
```
AI_BUILDER_TOKEN=your_api_key_here
```

## Running the Application

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The application will be available at:
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## Usage

1. Open http://localhost:8000 in your browser
2. **Search for tickers**: Type in the search box to see autocomplete suggestions for ticker symbols and company names
3. **Add keywords**: Click on a suggestion or press Enter to add it to your keyword list
   - You can add ticker symbols (AAPL), company names (Apple), or $ticker format ($AAPL)
   - The system will automatically expand each keyword to search for all variations
4. Click "Run Scan" to start the analysis
5. View sentiment results, insights, and analyzed tweets
   - Results show which keyword variation matched each tweet
   - Summary displays all keyword expansions used in the search

### Ticker Search APIs

The application uses multiple free ticker APIs:
- **yfinance** (Yahoo Finance) - Direct ticker lookups, no API key required
- **OpenFIGI** - Free public API, no authentication needed
- **Finnhub** - Free tier available (set `FINNHUB_API_KEY` environment variable for enhanced results)

To use Finnhub API (optional):
```bash
export FINNHUB_API_KEY=your_api_key_here
```
Get a free API key at: https://finnhub.io/

## API Endpoints

### POST /scan

Run a two-stage sentiment scan.

**Request:**
```json
{
  "keywords": ["AAPL", "TSLA"],
  "max_tweets": 10,
  "options": {}
}
```

**Response:**
```json
{
  "scan_id": "scan_20240130_123456_789012",
  "status": "completed",
  "keywords": ["AAPL", "TSLA"],
  "stage1": {
    "stage": 1,
    "status": "completed",
    "result": {
      "tweets_found": 10,
      "keywords_searched": ["AAPL", "TSLA"],
      "tweets": [...]
    },
    "duration_ms": 200.5
  },
  "stage2": {
    "stage": 2,
    "status": "completed",
    "result": {
      "analyzed_tweets": [...],
      "aggregate_sentiment": {
        "average_score": 0.45,
        "positive_count": 6,
        "negative_count": 2,
        "neutral_count": 2
      },
      "insights": [...]
    },
    "duration_ms": 300.2
  },
  "total_duration_ms": 500.7
}
```

### GET /api/tickers/search

Search for ticker symbols and company names.

**Query Parameters:**
- `q` (required): Search query (ticker symbol or company name)
- `limit` (optional): Maximum number of results (default: 10, max: 50)

**Example:**
```
GET /api/tickers/search?q=AAPL&limit=5
```

**Response:**
```json
{
  "query": "AAPL",
  "results": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "exchange": "NASDAQ",
      "type": "EQUITY"
    }
  ],
  "count": 1
}
```

### GET /health

Health check endpoint.

## Project Structure

```
sentiment alpha/
├── main.py              # FastAPI backend application
├── requirements.txt     # Python dependencies
├── background.md        # Project background and strategy
├── README.md           # This file
└── static/
    └── index.html      # Frontend HTML/JS interface
```

## AI Integration

The application uses the AI Builders API for enhanced sentiment analysis and insights generation:

- **Base URL**: `https://space.ai-builders.com/backend`
- **Model**: `supermind-agent-v1`
- **Authentication**: Bearer token via `AI_BUILDER_TOKEN` environment variable
- **Features**:
  - AI-enhanced sentiment analysis for ambiguous tweets (low confidence cases)
  - AI-generated market insights based on sentiment data
  - Fallback to TextBlob if AI API is unavailable

The AI client (`ai_client.py`) uses the OpenAI SDK with a custom base URL to interact with the AI Builders API.

## MVP Notes

- Currently uses mock tweet data for demonstration
- Sentiment analysis combines TextBlob (rule-based) with AI enhancement
- AI insights generation for actionable market analysis
- Ready for integration with Twitter/X API
- Frontend is self-contained (no build step required)

## Next Steps for Production

1. **Twitter/X API Integration**: Replace mock data with real Twitter API calls
2. **Database**: Store scan results and historical data
3. **Authentication**: Add user authentication and API keys
4. **Advanced Sentiment**: Integrate ML-based sentiment models (BERT, RoBERTa)
5. **Real-time Updates**: WebSocket support for live sentiment tracking
6. **Export**: Add CSV/JSON export functionality
7. **Alerts**: Set up sentiment threshold alerts

## Development

The application uses:
- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Sentiment Analysis**: TextBlob
- **Server**: Uvicorn

## License

MIT
