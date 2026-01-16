# LangGraph A2A Agent

A simple LangGraph agent with Google's A2A (Agent-to-Agent) protocol support, designed for testing agent interoperability with ServiceNow.

## Features

- **LangGraph Agent**: Stateful agent workflow with tools for weather, calculations, and knowledge search
- **A2A Protocol**: Full implementation of Google's Agent-to-Agent protocol
- **API Key Authentication**: Secure token-based access
- **LangGraph Cloud Ready**: Configuration for deployment to LangGraph Cloud

## Quick Start

### 1. Install Dependencies

```bash
pip install -e .
# or
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key for the LLM
- `A2A_API_KEY`: API key for authenticating A2A requests (default: `demo-api-key-12345`)

### 3. Run Locally

```bash
python main.py
```

The server will start at `http://localhost:8000`

## A2A Protocol Endpoints

### Agent Discovery

```bash
# Get Agent Card (no auth required)
curl http://localhost:8000/.well-known/agent.json
```

### Send a Task (JSON-RPC)

```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-api-key-12345" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tasks/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "What is the weather in San Francisco?"}]
      }
    },
    "id": "1"
  }'
```

### Send a Task (REST)

```bash
curl -X POST http://localhost:8000/tasks/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-api-key-12345" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{"type": "text", "text": "Calculate 25 * 4"}]
    }
  }'
```

### Get Task Status

```bash
curl http://localhost:8000/tasks/{task_id} \
  -H "Authorization: Bearer demo-api-key-12345"
```

## Deploy to LangGraph Cloud

### 1. Install LangGraph CLI

```bash
pip install langgraph-cli
```

### 2. Deploy

```bash
# Login to LangGraph Cloud
langgraph auth login

# Deploy the agent
langgraph deploy
```

### 3. Access Your Deployed Agent

After deployment, you'll receive a URL like:
```
https://your-deployment.langgraph.cloud
```

The A2A endpoints will be available at:
- Agent Card: `https://your-deployment.langgraph.cloud/.well-known/agent.json`
- Tasks: `https://your-deployment.langgraph.cloud/tasks/send`

## Alternative Deployment Options

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8000
CMD ["python", "main.py"]
```

```bash
docker build -t a2a-agent .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key -e A2A_API_KEY=your-api-key a2a-agent
```

### Cloud Run / Render / Railway

1. Push to GitHub
2. Connect your repo to the cloud provider
3. Set environment variables
4. Deploy

## Testing with ServiceNow A2A

1. Deploy your agent and note the public URL
2. In ServiceNow, configure the A2A connector with:
   - **Agent URL**: `https://your-deployment-url.com`
   - **API Key**: Your `A2A_API_KEY` value
3. ServiceNow will discover your agent via `/.well-known/agent.json`
4. Use the skills defined in the Agent Card to send tasks

## Agent Skills

| Skill | Description | Example |
|-------|-------------|---------|
| Weather | Get weather for locations | "What's the weather in Tokyo?" |
| Calculator | Math calculations | "Calculate 100 / 5" |
| Knowledge | Search knowledge base | "What is ServiceNow?" |

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
├── langgraph.json        # LangGraph Cloud config
├── main.py               # Local server entry point
├── pyproject.toml        # Python package config
└── requirements.txt      # Dependencies
```

## API Documentation

When running locally, access the interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
