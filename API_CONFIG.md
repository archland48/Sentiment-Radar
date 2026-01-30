# API Configuration

## AI Builders API

### Base URL
```
https://space.ai-builders.com/backend
```

### OpenAPI Specification
```
https://space.ai-builders.com/backend/openapi.json
```

### API Key
Set in `.env` file:
```
AI_BUILDER_TOKEN=sk_abfba6d6_e0b11364c4bf41af8c2762eee5ab5509dbcd
```

### Model
- **Default Model**: `supermind-agent-v1`
- **Available Models**:
  - `deepseek` - Fast and cost-effective chat completions
  - `supermind-agent-v1` - Multi-tool agent with web search and Gemini handoff (uses grok-4-fast as base model)
  - `gemini-2.5-pro` - Direct access to Google's Gemini model
  - `gemini-3-flash-preview` - Fast Gemini reasoning model
  - `gpt-5` - Passthrough to OpenAI-compatible providers
  - `grok-4-fast` - Passthrough to X.AI's Grok API

### Endpoints Used

#### Chat Completions
- **Endpoint**: `/v1/chat/completions`
- **Method**: POST
- **Authentication**: Bearer token (API key)
- **Usage**: Used for sentiment analysis and insights generation

### Configuration in Code

The API client is configured in `ai_client.py`:
```python
AI_BUILDER_BASE_URL = "https://space.ai-builders.com/backend"
AI_BUILDER_MODEL = "supermind-agent-v1"
client = OpenAI(
    api_key=AI_BUILDER_TOKEN,
    base_url=f"{AI_BUILDER_BASE_URL}/v1"
)
```

### Testing API Connection

To test the API connection:
```python
from ai_client import client, AI_BUILDER_MODEL

response = client.chat.completions.create(
    model=AI_BUILDER_MODEL,
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)
```

### Notes

- The API uses OpenAI-compatible SDK
- Authentication is via Bearer token in the Authorization header
- The API supports streaming responses (set `stream=True`)
- Debug mode can be enabled by adding `?debug=true` query parameter
