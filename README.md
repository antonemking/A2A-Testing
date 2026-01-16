# LangGraph A2A Agent

A LangGraph agent deployed to Render with Google's A2A (Agent-to-Agent) protocol support, designed for ServiceNow agent orchestration integration.

## Architecture

```
ServiceNow Agent Orchestrator
           │
           ▼ (JSON-RPC over HTTPS)
    ┌──────────────────┐
    │  Render (Host)   │
    │  ┌────────────┐  │
    │  │  FastAPI   │  │
    │  │  A2A Server│  │
    │  └─────┬──────┘  │
    │        │         │
    │  ┌─────▼──────┐  │
    │  │ LangGraph  │  │
    │  │   Agent    │  │
    │  └─────┬──────┘  │
    │        │         │
    │  ┌─────▼──────┐  │
    │  │  OpenAI    │  │
    │  │ GPT-4o-mini│  │
    │  └────────────┘  │
    └──────────────────┘
```

## Live Deployment

- **URL**: https://{{YOUR RENDER PROJECT}}.onrender.com
- **Agent Card**: https://{{YOUR RENDER PROJECT}}.onrender.com/.well-known/agent.json
- **API Docs**: https://{{YOUR RENDER PROJECT}}.onrender.com/docs

## ServiceNow A2A Integration

### Configuration in ServiceNow

| Setting | Value |
|---------|-------|
| Agent URL | `https://{{YOUR RENDER PROJECT}}.onrender.com/` |
| Authentication | Bearer Token |
| API Key | `{{YOUR TOKEN}}` |

### Request Format (ServiceNow → Agent)

ServiceNow sends JSON-RPC requests:

```json
{
  "method": "message/send",
  "id": "unique-request-id",
  "jsonrpc": "2.0",
  "params": {
    "metadata": {},
    "message": {
      "role": "user",
      "kind": "message",
      "parts": [
        {
          "kind": "text",
          "text": "what is the weather in columbus ohio?"
        }
      ],
      "messageId": "unique-message-id"
    }
  }
}
```

### Response Format (Agent → ServiceNow)

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "id": "task-id",
    "status": {
      "state": "completed",
      "message": {
        "role": "agent",
        "parts": [{"type": "text", "text": "The weather in Columbus, Ohio is partly cloudy with a temperature of 65°F."}]
      }
    },
    "artifacts": [...],
    "metadata": {
      "actions": [{"tool": "get_weather", "args": {"location": "Columbus, Ohio"}}],
      "tools_used": ["get_weather"]
    }
  }
}
```

## Agent Skills

| Skill | Description | Example Prompts |
|-------|-------------|-----------------|
| **Weather** | Get weather for any location | "What's the weather in Tokyo?" |
| **Calculator** | Math calculations | "Calculate 100 * 5" |
| **Knowledge** | Search knowledge base | "What is ServiceNow?" |

## Local Development

### Prerequisites

- Python 3.11+
- OpenAI API key

### Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and A2A_API_KEY
```

### Run Locally

```bash
python main.py
```

Server starts at http://localhost:8000

## Testing with curl

### Health Check
```bash
curl https://a2a-testing.onrender.com/health
```

### Agent Card Discovery
```bash
curl https://a2a-testing.onrender.com/.well-known/agent.json
```

### Send Task (REST)
```bash
curl -X POST https://a2a-testing.onrender.com/tasks/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-servicenow-token-1234" \
  -d '{"message": {"role": "user", "parts": [{"type": "text", "text": "What is 25 * 4?"}]}}'
```

### Send Task (JSON-RPC - ServiceNow format)
```bash
curl -X POST https://a2a-testing.onrender.com/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-servicenow-token-1234" \
  -d '{
    "method": "message/send",
    "id": "1",
    "jsonrpc": "2.0",
    "params": {
      "message": {
        "role": "user",
        "kind": "message",
        "parts": [{"kind": "text", "text": "What is the weather in San Francisco?"}]
      }
    }
  }'
```

## Deploy to Render

1. Push code to GitHub
2. Go to https://dashboard.render.com/new/web
3. Connect your GitHub repo
4. Configure:
   - **Build Command**: `pip install -e .`
   - **Start Command**: `python main.py`
5. Add Environment Variables:
   - `OPENAI_API_KEY` - Your OpenAI key
   - `A2A_API_KEY` - Token for authenticating requests
   - `PORT` - `10000`
   - `HOST` - `0.0.0.0`
6. Deploy

## Project Structure

```
.
├── agent/
│   ├── __init__.py
│   └── graph.py          # LangGraph agent workflow
├── a2a/
│   ├── __init__.py
│   ├── models.py         # A2A protocol data models
│   └── server.py         # FastAPI A2A server
├── main.py               # Server entry point
├── pyproject.toml        # Python package config
├── render.yaml           # Render deployment config
└── requirements.txt      # Dependencies
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `A2A_API_KEY` | API key for authenticating A2A requests | `demo-api-key-12345` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
