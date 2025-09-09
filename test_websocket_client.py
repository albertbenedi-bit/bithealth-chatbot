#!/usr/bin/env python3
"""
WebSocket client test script for testing the WebSocket integration
"""
import asyncio
import websockets
import json
import requests
import time

async def test_websocket_connection():
    """Test WebSocket connection to the backend orchestrator"""
    print("Testing WebSocket integration...")
    
    print("1. Creating session via POST /chat...")
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={
                "message": "Hello, I need help with an appointment",
                "user_id": "test-user-123"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            chat_data = response.json()
            session_id = chat_data.get("session_id")
            correlation_id = chat_data.get("correlation_id")
            print(f"✓ Session created: {session_id}")
            print(f"✓ Correlation ID: {correlation_id}")
            print(f"✓ Initial response: {chat_data.get('response', '')[:100]}...")
        else:
            print(f"✗ Failed to create session: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error creating session: {e}")
        return False
    
    print(f"\n2. Testing WebSocket connection to /ws/{session_id}...")
    try:
        uri = f"ws://localhost:8000/ws/{session_id}"
        
        async with websockets.connect(uri) as websocket:
            print(f"✓ WebSocket connected to {uri}")
            
            await websocket.send(json.dumps({"type": "ping"}))
            print("✓ Ping sent to WebSocket")
            
            print("✓ Waiting for WebSocket messages (10 seconds)...")
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(message)
                print(f"✓ Received WebSocket message: {data}")
                
                if data.get("type") == "final_response":
                    print("✓ Final response received via WebSocket!")
                    print(f"  - Session ID: {data.get('data', {}).get('session_id')}")
                    print(f"  - Response: {data.get('data', {}).get('response', '')[:100]}...")
                    print(f"  - Correlation ID: {data.get('data', {}).get('correlation_id')}")
                    return True
                else:
                    print(f"✓ Other message type received: {data.get('type')}")
                    
            except asyncio.TimeoutError:
                print("⚠ No WebSocket messages received within timeout (expected if no Kafka agents running)")
                print("✓ WebSocket connection established successfully")
                return True
                
    except Exception as e:
        print(f"✗ WebSocket connection failed: {e}")
        return False

def test_backend_health():
    """Test if backend is running and healthy"""
    print("Testing backend health...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend health check passed")
            return True
        else:
            print(f"✗ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Backend not reachable: {e}")
        return False

def test_websocket_endpoint_exists():
    """Test if WebSocket endpoint is available in OpenAPI docs"""
    print("Testing WebSocket endpoint availability...")
    try:
        response = requests.get("http://localhost:8000/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            
            ws_endpoint_found = any("/ws/" in path for path in paths.keys())
            if ws_endpoint_found:
                print("✓ WebSocket endpoint found in OpenAPI specification")
                return True
            else:
                print("✗ WebSocket endpoint not found in OpenAPI specification")
                return False
        else:
            print(f"✗ Failed to get OpenAPI spec: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error checking OpenAPI spec: {e}")
        return False

async def main():
    """Run all WebSocket integration tests"""
    print("=" * 60)
    print("WebSocket Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("WebSocket Endpoint", test_websocket_endpoint_exists),
        ("WebSocket Connection", test_websocket_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} Test ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            if result:
                passed += 1
                print(f"✓ {test_name} test PASSED")
            else:
                print(f"✗ {test_name} test FAILED")
        except Exception as e:
            print(f"✗ {test_name} test ERROR: {e}")
        
        print("-" * 40)
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All WebSocket integration tests PASSED!")
        return 0
    else:
        print("✗ Some WebSocket integration tests FAILED!")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
