import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from pump_self_melon import Client, Message, User, Room
from pump_self_melon.utils import get_user_info, get_room_info
from pump_self_melon.core import EventEmitter, RateLimiter
import asyncio

def test_basic_functionality():
    print("Testing basic functionality...")
    
    client = Client("test_token")
    assert client.token == "test_token"
    assert not client.is_authenticated
    print("✓ Client initialization")
    
    user = User("testuser", "0x123")
    assert user.username == "testuser"
    assert user.address == "0x123"
    print("✓ User model")
    
    room = Room("test_room")
    assert room.id == "test_room"
    print("✓ Room model")
    
    message = Message("1", "Hello", user, room)
    assert message.content == "Hello"
    assert message.author == user
    assert message.room == room
    print("✓ Message model")
    
    emitter = EventEmitter()
    called = False
    def handler():
        nonlocal called
        called = True
    
    emitter.on('test', handler)
    asyncio.run(emitter.emit('test'))
    assert called
    print("✓ EventEmitter")
    
    rate_limiter = RateLimiter(max_calls=1, time_window=1)
    result = asyncio.run(rate_limiter.acquire())
    assert result is True
    print("✓ RateLimiter")
    
    print("All basic functionality tests passed!")

def test_event_system():
    print("\\nTesting event system...")
    
    client = Client("test_token")
    
    event_called = False
    
    @client.event
    async def on_message(message):
        nonlocal event_called
        event_called = True
    
    assert on_message in client._event_handlers['message']
    print("✓ Event decorator registration")
    
    listen_called = False
    
    @client.listen('custom')
    async def custom_handler():
        nonlocal listen_called
        listen_called = True
    
    assert custom_handler in client._event_handlers['custom']
    print("✓ Listen decorator registration")
    
    user = User("testuser")
    room = Room("testroom")
    message = Message("1", "test", user, room)
    
    asyncio.run(client._dispatch('message', message))
    assert event_called
    print("✓ Event dispatch")
    
    asyncio.run(client._dispatch('custom'))
    assert listen_called
    print("✓ Custom event dispatch")
    
    print("Event system tests passed!")

def test_message_parsing():
    print("\\nTesting message parsing...")
    
    client = Client("test_token")
    
    valid_message = '42["newMessage",{"id":"123","message":"Hello","username":"user1","userAddress":"0x123","timestamp":1234567890000,"messageType":"regular","roomId":"room1"}]'
    
    parsed = client._parse_message(valid_message)
    assert parsed is not None
    assert parsed.id == "123"
    assert parsed.content == "Hello"
    assert parsed.author.username == "user1"
    assert parsed.author.address == "0x123"
    assert parsed.room.id == "room1"
    print("✓ Valid message parsing")
    
    invalid_message = '43["otherEvent","data"]'
    parsed = client._parse_message(invalid_message)
    assert parsed is None
    print("✓ Invalid message handling")
    
    print("Message parsing tests passed!")

def test_authentication():
    print("\\nTesting authentication...")
    
    client = Client("test_token")
    
    success_auth = '430[{"authenticated":true,"userId":"123"}]'
    result = client._check_authentication(success_auth)
    assert result is True
    assert client.is_authenticated is True
    print("✓ Successful authentication")
    
    client.is_authenticated = False
    
    try:
        fail_auth = '430[{"authenticated":false}]'
        client._check_authentication(fail_auth)
        assert False, "Should have raised exception"
    except Exception as e:
        assert "Authentication failed" in str(e)
        print("✓ Failed authentication handling")
    
    invalid_auth = '42["message","data"]'
    result = client._check_authentication(invalid_auth)
    assert result is False
    print("✓ Invalid authentication message")
    
    print("Authentication tests passed!")

async def test_async_functionality():
    print("\\nTesting async functionality...")
    
    client = Client("test_token")
    
    events = []
    
    @client.event
    async def on_ready():
        events.append("ready")
    
    @client.event
    async def on_message(message):
        events.append(f"message: {message.content}")
    
    await client._dispatch('ready')
    assert "ready" in events
    print("✓ Async event dispatch")
    
    user = User("testuser")
    room = Room("testroom") 
    message = Message("1", "test content", user, room)
    await client._dispatch('message', message)
    assert "message: test content" in events
    print("✓ Async message handling")
    
    print("Async functionality tests passed!")

def run_all_tests():
    print("=== Pump-Self Library Tests ===\\n")
    
    try:
        test_basic_functionality()
        test_event_system()
        test_message_parsing()
        test_authentication()
        asyncio.run(test_async_functionality())
        
        print("\\n🎉 All tests passed! The library is working correctly.")
        
    except Exception as e:
        print(f"\\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()