#!/usr/bin/env python3
"""
Test script for WebSocket integration
"""
import sys
import os

sys.path.append('backend_orchestrator/src')

os.environ['GEMINI_API_KEY'] = 'test-key'
os.environ['ANTHROPIC_API_KEY'] = 'test-key'
os.environ['KAFKA_BOOTSTRAP_SERVERS'] = 'localhost:9092'
os.environ['REDIS_URL'] = 'redis://localhost:6379'

def test_websocket_imports():
    """Test that WebSocket components can be imported successfully"""
    try:
        from websocket.websocket_manager import WebSocketManager
        print("✓ WebSocketManager import successful")
        
        ws_manager = WebSocketManager()
        print(f"✓ WebSocketManager created, active connections: {ws_manager.get_active_connections_count()}")
        
        assert hasattr(ws_manager, 'connect'), "WebSocketManager missing connect method"
        assert hasattr(ws_manager, 'disconnect'), "WebSocketManager missing disconnect method"
        assert hasattr(ws_manager, 'send_message'), "WebSocketManager missing send_message method"
        assert hasattr(ws_manager, 'broadcast'), "WebSocketManager missing broadcast method"
        print("✓ WebSocketManager has all required methods")
        
        return True
    except Exception as e:
        print(f"✗ WebSocket import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_app_imports():
    """Test that the main FastAPI app can be imported with WebSocket support"""
    try:
        from main import app
        print("✓ FastAPI app import successful")
        
        routes = [route.path for route in app.routes]
        websocket_route_found = any('/ws/' in route for route in routes)
        if websocket_route_found:
            print("✓ WebSocket endpoint found in FastAPI routes")
        else:
            print("✗ WebSocket endpoint not found in FastAPI routes")
            return False
            
        return True
    except Exception as e:
        print(f"✗ FastAPI app import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_engine_websocket():
    """Test that ConversationEngine has WebSocket manager integration"""
    try:
        from workflow.conversation_engine import ConversationEngine
        from websocket.websocket_manager import WebSocketManager
        from llm_abstraction.gemini_provider import GeminiProvider
        from llm_abstraction.anthropic_provider import AnthropicProvider
        from llm_abstraction.prompt_manager import PromptManager
        from messaging.kafka_client import KafkaClient
        from session.session_manager import SessionManager
        
        print("✓ All ConversationEngine dependencies imported")
        
        llm_provider = GeminiProvider("test-key")
        fallback_provider = AnthropicProvider("test-key")
        prompt_manager = PromptManager()
        kafka_client = KafkaClient("localhost:9092")
        session_manager = SessionManager("redis://localhost:6379")
        websocket_manager = WebSocketManager()
        
        engine = ConversationEngine(
            llm_provider=llm_provider,
            fallback_provider=fallback_provider,
            prompt_manager=prompt_manager,
            kafka_client=kafka_client,
            session_manager=session_manager,
            websocket_manager=websocket_manager
        )
        
        assert hasattr(engine, 'websocket_manager'), "ConversationEngine missing websocket_manager attribute"
        assert engine.websocket_manager is websocket_manager, "ConversationEngine websocket_manager not set correctly"
        print("✓ ConversationEngine WebSocket integration successful")
        
        return True
    except Exception as e:
        print(f"✗ ConversationEngine WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all WebSocket integration tests"""
    print("Testing WebSocket Integration...")
    print("=" * 50)
    
    tests = [
        test_websocket_imports,
        test_main_app_imports,
        test_conversation_engine_websocket
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\nRunning {test.__name__}...")
        if test():
            passed += 1
        print("-" * 30)
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All WebSocket integration tests passed!")
        return 0
    else:
        print("✗ Some WebSocket integration tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())
