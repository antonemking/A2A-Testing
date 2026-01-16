"""Main entry point for running the A2A server locally."""
import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"Starting A2A Protocol Server on {host}:{port}")
    print(f"Agent Card: http://{host}:{port}/.well-known/agent.json")
    print(f"API Docs: http://{host}:{port}/docs")
    print(f"API Key: {os.getenv('A2A_API_KEY', 'demo-api-key-12345')}")

    uvicorn.run(
        "a2a.server:app",
        host=host,
        port=port,
        reload=True
    )
