"""A2A Protocol Data Models.

Based on Google's Agent-to-Agent (A2A) Protocol specification.
https://github.com/google/A2A
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskState(str, Enum):
    """Possible states for a task."""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"


class AuthenticationType(str, Enum):
    """Supported authentication types."""
    API_KEY = "apiKey"
    OAUTH2 = "oauth2"
    NONE = "none"


class Part(BaseModel):
    """A part of a message (text, file, or data)."""
    type: str = "text"
    text: Optional[str] = None
    mimeType: Optional[str] = None
    data: Optional[str] = None  # Base64 encoded for binary data


class Message(BaseModel):
    """A message in the A2A protocol."""
    role: str  # "user" or "agent"
    parts: list[Part]


class Artifact(BaseModel):
    """An artifact produced by the agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    parts: list[Part]
    index: int = 0
    append: bool = False
    lastChunk: bool = True


class TaskStatus(BaseModel):
    """Status of a task."""
    state: TaskState
    message: Optional[Message] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class Task(BaseModel):
    """A task in the A2A protocol."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    sessionId: Optional[str] = None
    status: TaskStatus = Field(default_factory=lambda: TaskStatus(state=TaskState.SUBMITTED))
    history: list[Message] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskSendRequest(BaseModel):
    """Request to send a task to an agent."""
    id: Optional[str] = None
    sessionId: Optional[str] = None
    message: Message
    acceptedOutputModes: list[str] = Field(default=["text"])
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskQueryRequest(BaseModel):
    """Request to query task status."""
    id: str
    historyLength: Optional[int] = None


class TaskCancelRequest(BaseModel):
    """Request to cancel a task."""
    id: str


class Skill(BaseModel):
    """A skill the agent can perform."""
    id: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    inputModes: list[str] = Field(default=["text"])
    outputModes: list[str] = Field(default=["text"])


class AuthenticationInfo(BaseModel):
    """Authentication information for the agent."""
    schemes: list[str] = Field(default=["apiKey"])
    credentials: Optional[str] = None  # URL for obtaining credentials


class AgentCapabilities(BaseModel):
    """Capabilities of the agent."""
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = True


class AgentProvider(BaseModel):
    """Provider information for the agent."""
    organization: str
    url: Optional[str] = None


class AgentCard(BaseModel):
    """Agent Card - describes the agent's capabilities for A2A discovery.

    This is served at /.well-known/agent.json
    """
    name: str
    description: str
    url: str  # Base URL of the agent
    version: str = "1.0.0"
    documentationUrl: Optional[str] = None
    provider: Optional[AgentProvider] = None
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    authentication: AuthenticationInfo = Field(default_factory=AuthenticationInfo)
    defaultInputModes: list[str] = Field(default=["text"])
    defaultOutputModes: list[str] = Field(default=["text"])
    skills: list[Skill] = Field(default_factory=list)


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 Request format used by A2A."""
    jsonrpc: str = "2.0"
    method: str
    params: Optional[dict[str, Any]] = None
    id: Optional[str | int] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response format used by A2A."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[dict[str, Any]] = None
    id: Optional[str | int] = None
