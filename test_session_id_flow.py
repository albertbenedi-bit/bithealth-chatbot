#!/usr/bin/env python3
"""
Test script to verify WebSocket session_id flow through Kafka pipeline.
This script tests the complete flow:
Frontend WebSocket → Backend Orchestrator → Kafka → RAG Service → Kafka Response → WebSocket Delivery
"""

import asyncio
import websockets
import json
import requests
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def test_websocket_session_flow():
    """Test complete WebSocket session_id flow with multiple concurrent sessions"""
    print("🧪 Testing WebSocket Session ID Flow")
    print("=" * 50)
    
    test_sessions = [
        {"session_id": f"test-session-{uuid.uuid4()}", "message": "What are your opening hours?"},
        {"session_id": f"test-session-{uuid.uuid4()}", "message": "How do I book an appointment?"},
        {"session_id": f"test-session-{uuid.uuid4()}", "message": "What services do you provide?"}
    ]
    
    print(f"📋 Testing {len(test_sessions)} concurrent sessions:")
    for i, session in enumerate(test_sessions, 1):
        print(f"  {i}. Session: {session['session_id'][:20]}... Message: {session['message'][:30]}...")
    
    results = []
    for session_data in test_sessions:
        result = await test_single_session(session_data["session_id"], session_data["message"])
        results.append(result)
        await asyncio.sleep(1)  # Small delay between sessions
    
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    success_count = sum(1 for r in results if r["success"])
    print(f"✅ Successful sessions: {success_count}/{len(results)}")
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"  Session {i}: {status}")
        if not result["success"]:
            print(f"    Error: {result.get('error', 'Unknown error')}")
    
    return success_count == len(results)

async def test_single_session(session_id: str, message: str):
    """Test a single WebSocket session"""
    try:
        print(f"\n🔄 Testing session: {session_id[:20]}...")
        
        ws_uri = f"{WS_URL}/ws/{session_id}"
        print(f"  📡 Connecting to WebSocket: {ws_uri}")
        
        async with websockets.connect(ws_uri) as websocket:
            print(f"  ✅ WebSocket connected for session: {session_id[:20]}...")
            
            chat_payload = {
                "user_id": f"test-user-{session_id[:8]}",
                "message": message,
                "session_id": session_id,
                "context": {"test": True}
            }
            
            print(f"  📤 Sending chat request: {message[:30]}...")
            response = requests.post(f"{BASE_URL}/chat", json=chat_payload, timeout=10)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP request failed: {response.status_code}"}
            
            http_response = response.json()
            print(f"  ✅ HTTP response received: {http_response.get('response', '')[:50]}...")
            
            print(f"  ⏳ Waiting for WebSocket response...")
            
            try:
                ws_message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                ws_data = json.loads(ws_message)
                
                print(f"  📨 WebSocket message received!")
                print(f"    Type: {ws_data.get('type')}")
                print(f"    Session ID: {ws_data.get('data', {}).get('session_id', 'N/A')}")
                print(f"    Response: {ws_data.get('data', {}).get('response', '')[:50]}...")
                
                received_session_id = ws_data.get('data', {}).get('session_id')
                if received_session_id == session_id:
                    print(f"  ✅ Session ID matches: {session_id[:20]}...")
                    return {"success": True, "ws_data": ws_data, "http_data": http_response}
                else:
                    return {"success": False, "error": f"Session ID mismatch. Expected: {session_id}, Got: {received_session_id}"}
                    
            except asyncio.TimeoutError:
                return {"success": False, "error": "WebSocket response timeout (30s)"}
                
    except Exception as e:
        return {"success": False, "error": f"Exception: {str(e)}"}

def test_health_check():
    """Test that the backend is running"""
    try:
        print("🏥 Checking backend health...")
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"  ✅ Backend is healthy: {health_data.get('status')}")
            print(f"  📊 Checks: {health_data.get('checks', {})}")
            return True
        else:
            print(f"  ❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Backend health check error: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 WebSocket Session ID Flow Test")
    print("=" * 40)
    print(f"⏰ Test started at: {datetime.now().isoformat()}")
    
    if not test_health_check():
        print("\n❌ Backend is not healthy. Please start the backend services first.")
        print("   Run: cd backend_orchestrator && python -m src.main")
        return False
    
    try:
        success = await test_websocket_session_flow()
        
        print(f"\n🏁 Test completed at: {datetime.now().isoformat()}")
        if success:
            print("🎉 All tests PASSED! Session ID flow is working correctly.")
        else:
            print("💥 Some tests FAILED! Check the output above for details.")
        
        return success
        
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
