"""A2A Protocol Server Implementation.

Implements the Google A2A protocol endpoints for agent-to-agent communication.
"""
import os
from typing import Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage

from a2a.models import (
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    Artifact,
    AuthenticationInfo,
    JSONRPCRequest,
    JSONRPCResponse,
    Message,
    Part,
    Skill,
    Task,
    TaskCancelRequest,
    TaskQueryRequest,
    TaskSendRequest,
    TaskState,
    TaskStatus,
)
from agent.graph import create_graph

# In-memory task storage (use Redis/DB in production)
tasks: dict[str, Task] = {}

# API Key for authentication (set via environment variable)
API_KEY = os.getenv("A2A_API_KEY", "demo-api-key-12345")


def verify_api_key(authorization: Optional[str] = Header(None)) -> bool:
    """Verify the API key from the Authorization header."""
    if not API_KEY:
        return True  # No auth required if no key set

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    # Support both "Bearer <token>" and just "<token>"
    token = authorization.replace("Bearer ", "").strip()
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True


def create_agent_card(base_url: str) -> AgentCard:
    """Create the Agent Card for this agent."""
    return AgentCard(
        name="ServiceNow Demo Agent",
        description="A demo LangGraph agent that supports weather queries, calculations, and knowledge base searches. Built for testing the A2A protocol with ServiceNow.",
        url=base_url,
        version="1.0.0",
        documentationUrl=f"{base_url}/docs",
        provider=AgentProvider(
            organization="Demo Organization",
            url="https://example.com"
        ),
        capabilities=AgentCapabilities(
            streaming=True,
            pushNotifications=False,
            stateTransitionHistory=True
        ),
        authentication=AuthenticationInfo(
            schemes=["apiKey"],
            credentials=None
        ),
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[
            Skill(
                id="weather",
                name="Weather Information",
                description="Get current weather information for any location",
                tags=["weather", "forecast"],
                examples=["What's the weather in San Francisco?", "Tell me the temperature in Tokyo"],
                inputModes=["text"],
                outputModes=["text"]
            ),
            Skill(
                id="calculator",
                name="Calculator",
                description="Perform mathematical calculations",
                tags=["math", "calculator"],
                examples=["Calculate 25 * 4", "What is 100 / 5?"],
                inputModes=["text"],
                outputModes=["text"]
            ),
            Skill(
                id="knowledge",
                name="Knowledge Search",
                description="Search the knowledge base for information about ServiceNow, A2A protocol, and LangGraph",
                tags=["search", "knowledge", "info"],
                examples=["What is ServiceNow?", "Tell me about the A2A protocol"],
                inputModes=["text"],
                outputModes=["text"]
            )
        ]
    )


def create_a2a_app(base_url: str = "http://localhost:8000") -> FastAPI:
    """Create the FastAPI application with A2A protocol endpoints."""

    app = FastAPI(
        title="A2A Protocol Agent",
        description="LangGraph agent with A2A protocol support",
        version="1.0.0"
    )

    # Add CORS middleware for cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create the LangGraph agent
    agent_graph = create_graph()

    # Agent Card endpoint (discovery)
    @app.get("/.well-known/agent.json")
    async def get_agent_card(request: Request):
        """Return the Agent Card for A2A discovery."""
        # Dynamically build base URL from request
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("x-forwarded-host", request.url.netloc)
        actual_base_url = f"{scheme}://{host}"
        return create_agent_card(actual_base_url).model_dump(by_alias=True, exclude_none=True)

    # JSON-RPC endpoint (main A2A endpoint)
    @app.post("/")
    async def handle_jsonrpc(
        rpc_request: JSONRPCRequest,
        _auth: bool = Depends(verify_api_key)
    ):
        """Handle JSON-RPC requests for A2A protocol."""
        method = rpc_request.method
        params = rpc_request.params or {}

        try:
            if method == "tasks/send":
                result = await handle_task_send(params, agent_graph)
            elif method == "tasks/get":
                result = handle_task_get(params)
            elif method == "tasks/cancel":
                result = handle_task_cancel(params)
            else:
                return JSONRPCResponse(
                    id=rpc_request.id,
                    error={"code": -32601, "message": f"Method not found: {method}"}
                )

            return JSONRPCResponse(id=rpc_request.id, result=result)

        except Exception as e:
            return JSONRPCResponse(
                id=rpc_request.id,
                error={"code": -32000, "message": str(e)}
            )

    # REST endpoints (alternative to JSON-RPC)
    @app.post("/tasks/send")
    async def task_send(
        request: Request,
        _auth: bool = Depends(verify_api_key)
    ):
        """Send a task to the agent (REST endpoint)."""
        try:
            body = await request.json()
            # Log incoming request for debugging
            print(f"Received task/send request: {body}")
            result = await handle_task_send(body, agent_graph)
            return result
        except Exception as e:
            print(f"Error processing request: {e}")
            return JSONResponse(
                status_code=400,
                content={"error": str(e), "detail": "Failed to process request"}
            )

    @app.get("/tasks/{task_id}")
    async def task_get(
        task_id: str,
        _auth: bool = Depends(verify_api_key)
    ):
        """Get task status (REST endpoint)."""
        return handle_task_get({"id": task_id})

    @app.post("/tasks/{task_id}/cancel")
    async def task_cancel(
        task_id: str,
        _auth: bool = Depends(verify_api_key)
    ):
        """Cancel a task (REST endpoint)."""
        return handle_task_cancel({"id": task_id})

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "1.0.0"}

    # Debug endpoint to see raw request
    @app.post("/debug")
    async def debug_request(request: Request):
        """Debug endpoint - returns exactly what was received."""
        try:
            body = await request.json()
        except:
            body = (await request.body()).decode()
        headers = dict(request.headers)

        # Print to logs so you can see in Render console
        print("=" * 50)
        print("DEBUG: Incoming request from ServiceNow")
        print(f"BODY: {body}")
        print(f"HEADERS: {headers}")
        print("=" * 50)

        return {
            "received_body": body,
            "headers": headers,
            "method": request.method,
            "url": str(request.url)
        }

    return app


async def handle_task_send(params: dict, agent_graph) -> dict:
    """Handle a task/send request."""
    # Create or retrieve task
    task_id = params.get("id") or str(uuid4())
    session_id = params.get("sessionId") or params.get("session_id") or str(uuid4())

    # Extract the message - handle multiple formats
    user_text = ""

    # Format 1: Standard A2A format {"message": {"role": "user", "parts": [{"text": "..."}]}}
    message_data = params.get("message", {})
    if message_data:
        parts = message_data.get("parts", [])
        for part in parts:
            if isinstance(part, dict):
                if part.get("type") == "text" or "text" in part:
                    user_text = part.get("text", "")
                    break
            elif isinstance(part, str):
                user_text = part
                break
        # Also check for direct text in message
        if not user_text and isinstance(message_data, dict):
            user_text = message_data.get("text", "") or message_data.get("content", "")

    # Format 2: Simple format {"text": "..."} or {"content": "..."}
    if not user_text:
        user_text = params.get("text", "") or params.get("content", "") or params.get("query", "")

    # Format 3: Prompt format {"prompt": "..."}
    if not user_text:
        user_text = params.get("prompt", "")

    # Format 4: Input format {"input": "..."}
    if not user_text:
        user_text = params.get("input", "")

    if not user_text:
        raise ValueError(f"No text content found in request. Received params: {params}")

    # Create or update task
    if task_id in tasks:
        task = tasks[task_id]
    else:
        task = Task(id=task_id, sessionId=session_id)
        tasks[task_id] = task

    # Add user message to history
    user_message = Message(role="user", parts=[Part(type="text", text=user_text)])
    task.history.append(user_message)
    task.status = TaskStatus(state=TaskState.WORKING)

    try:
        # Build conversation history for the agent
        langchain_messages = []
        for msg in task.history:
            for part in msg.parts:
                if part.text:
                    if msg.role == "user":
                        langchain_messages.append(HumanMessage(content=part.text))
                    else:
                        langchain_messages.append(AIMessage(content=part.text))

        # Run the agent
        result = await agent_graph.ainvoke({"messages": langchain_messages})

        # Extract the response
        response_text = ""
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                response_text = msg.content
                break

        # Update task with response
        agent_message = Message(role="agent", parts=[Part(type="text", text=response_text)])
        task.history.append(agent_message)
        task.status = TaskStatus(state=TaskState.COMPLETED, message=agent_message)

        # Add artifact
        task.artifacts.append(Artifact(
            name="response",
            parts=[Part(type="text", text=response_text)],
            index=0,
            lastChunk=True
        ))

    except Exception as e:
        task.status = TaskStatus(state=TaskState.FAILED)
        task.status.message = Message(role="agent", parts=[Part(type="text", text=f"Error: {str(e)}")])

    return task.model_dump(by_alias=True, exclude_none=True)


def handle_task_get(params: dict) -> dict:
    """Handle a task/get request."""
    task_id = params.get("id")
    if not task_id or task_id not in tasks:
        raise ValueError(f"Task not found: {task_id}")

    task = tasks[task_id]
    return task.model_dump(by_alias=True, exclude_none=True)


def handle_task_cancel(params: dict) -> dict:
    """Handle a task/cancel request."""
    task_id = params.get("id")
    if not task_id or task_id not in tasks:
        raise ValueError(f"Task not found: {task_id}")

    task = tasks[task_id]
    task.status = TaskStatus(state=TaskState.CANCELED)
    return task.model_dump(by_alias=True, exclude_none=True)


# Create default app instance
app = create_a2a_app()
