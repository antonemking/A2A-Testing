"""Simple test script for the A2A protocol endpoints."""
import asyncio
import httpx


BASE_URL = "http://localhost:8000"
API_KEY = "demo-api-key-12345"


async def test_agent_card():
    """Test the agent card discovery endpoint."""
    print("\n=== Testing Agent Card Discovery ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/.well-known/agent.json")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            card = response.json()
            print(f"Agent Name: {card['name']}")
            print(f"Description: {card['description']}")
            print(f"Skills: {[s['name'] for s in card.get('skills', [])]}")
        return response.status_code == 200


async def test_task_send_rest():
    """Test sending a task via REST endpoint."""
    print("\n=== Testing Task Send (REST) ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/tasks/send",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": "What is the weather in San Francisco?"}]
                }
            },
            timeout=60.0
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            task = response.json()
            print(f"Task ID: {task['id']}")
            print(f"State: {task['status']['state']}")
            if task.get("artifacts"):
                print(f"Response: {task['artifacts'][0]['parts'][0]['text']}")
        return response.status_code == 200


async def test_task_send_jsonrpc():
    """Test sending a task via JSON-RPC endpoint."""
    print("\n=== Testing Task Send (JSON-RPC) ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "jsonrpc": "2.0",
                "method": "tasks/send",
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [{"type": "text", "text": "Calculate 25 * 4"}]
                    }
                },
                "id": "test-1"
            },
            timeout=60.0
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            rpc_response = response.json()
            if "result" in rpc_response:
                task = rpc_response["result"]
                print(f"Task ID: {task['id']}")
                print(f"State: {task['status']['state']}")
                if task.get("artifacts"):
                    print(f"Response: {task['artifacts'][0]['parts'][0]['text']}")
            elif "error" in rpc_response:
                print(f"Error: {rpc_response['error']}")
        return response.status_code == 200


async def test_health():
    """Test the health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200


async def main():
    """Run all tests."""
    print("=" * 50)
    print("A2A Protocol Test Suite")
    print("=" * 50)
    print(f"Testing against: {BASE_URL}")
    print(f"API Key: {API_KEY}")

    results = []

    try:
        results.append(("Health Check", await test_health()))
        results.append(("Agent Card", await test_agent_card()))
        results.append(("Task Send (REST)", await test_task_send_rest()))
        results.append(("Task Send (JSON-RPC)", await test_task_send_jsonrpc()))
    except httpx.ConnectError:
        print("\nERROR: Could not connect to server. Make sure it's running:")
        print("  python main.py")
        return

    print("\n" + "=" * 50)
    print("Test Results")
    print("=" * 50)
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
