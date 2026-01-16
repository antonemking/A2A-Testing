"""LangGraph agent workflow definition."""
import os
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode


# Define the agent state
class AgentState(TypedDict):
    """State for the agent workflow."""
    messages: Annotated[list, add_messages]


# Define tools the agent can use
@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location.

    Args:
        location: The city or location to get weather for.
    """
    # Simulated weather data for demo purposes
    weather_data = {
        "san francisco": "Foggy, 58°F",
        "new york": "Sunny, 72°F",
        "london": "Rainy, 55°F",
        "tokyo": "Cloudy, 68°F",
        "default": "Partly cloudy, 65°F"
    }
    return weather_data.get(location.lower(), weather_data["default"])


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A mathematical expression to evaluate (e.g., '2 + 2', '10 * 5').
    """
    try:
        # Safe evaluation of mathematical expressions
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def search_knowledge(query: str) -> str:
    """Search the knowledge base for information.

    Args:
        query: The search query.
    """
    # Simulated knowledge base for demo
    knowledge = {
        "servicenow": "ServiceNow is a cloud computing platform that provides IT service management (ITSM) and automates IT business management.",
        "a2a protocol": "The Agent-to-Agent (A2A) protocol is Google's open protocol for enabling AI agents to communicate and collaborate with each other.",
        "langgraph": "LangGraph is a library for building stateful, multi-actor applications with LLMs, built on top of LangChain.",
        "default": "I found some general information related to your query. Please be more specific for detailed results."
    }
    query_lower = query.lower()
    for key, value in knowledge.items():
        if key in query_lower:
            return value
    return knowledge["default"]


# List of tools available to the agent
tools = [get_weather, calculate, search_knowledge]


def create_graph(model_name: str = "gpt-4o-mini"):
    """Create the LangGraph agent workflow.

    Args:
        model_name: The LLM model to use.

    Returns:
        Compiled LangGraph workflow.
    """
    # Initialize the LLM with tools
    llm = ChatOpenAI(model=model_name, temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    # Define the agent node
    def agent_node(state: AgentState) -> dict:
        """The main agent node that decides what to do."""
        system_message = SystemMessage(content="""You are a helpful AI assistant that can:
1. Get weather information for locations
2. Perform mathematical calculations
3. Search a knowledge base for information

Be concise and helpful in your responses. When you have the information needed,
provide a clear answer to the user.""")

        messages = [system_message] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # Define the routing function
    def should_continue(state: AgentState) -> Literal["tools", END]:
        """Determine if we should continue to tools or end."""
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        return END

    # Build the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    # Set entry point
    workflow.set_entry_point("agent")

    # Add edges
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    return workflow.compile()


# Create the default graph instance for LangGraph Cloud
graph = create_graph()
