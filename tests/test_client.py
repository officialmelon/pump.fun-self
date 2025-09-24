import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pump_self_melon import Client, Message, User, Room
from datetime import datetime

class TestClient:
    @pytest.fixture
    def client(self):
        return Client(token="test_token", websocket_uri="ws://test.example.com")
    
    def test_client_initialization(self, client):
        assert client.token == "test_token"
        assert client.websocket_uri == "ws://test.example.com"
        assert not client.is_authenticated
        assert client.current_room is None
        assert client.current_username is None
        assert len(client._event_handlers) == 5
    
    def test_event_decorator(self, client):
        @client.event
        async def on_message(message):
            pass
        
        assert on_message in client._event_handlers['message']
    
    def test_listen_decorator(self, client):
        @client.listen('custom_event')
        async def custom_handler():
            pass
        
        assert custom_handler in client._event_handlers['custom_event']
    
    def test_invalid_event_handler_sync(self, client):
        with pytest.raises(TypeError):
            @client.event
            def sync_handler():
                pass
    
    @pytest.mark.asyncio
    async def test_dispatch_event(self, client):
        handler_called = False
        
        @client.event
        async def on_message(message):
            nonlocal handler_called
            handler_called = True
        
        user = User("test_user")
        room = Room("test_room")
        message = Message("1", "test", user, room)
        
        await client._dispatch('message', message)
        assert handler_called
    
    @pytest.mark.asyncio
    async def test_connect_success(self, client):
        with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            result = await client.connect()
            
            assert result is True
            assert client.websocket == mock_websocket
            mock_connect.assert_called_once_with("ws://test.example.com")
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, client):
        with patch('websockets.connect', side_effect=Exception("Connection failed")):
            result = await client.connect()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_auth(self, client):
        mock_websocket = AsyncMock()
        client.websocket = mock_websocket
        
        with patch('time.time', return_value=1234567890):
            await client._send_auth()
            
            expected_message = '40{"origin":"https://pump.fun","timestamp":1234567890000,"token":"test_token"}'
            mock_websocket.send.assert_called_once_with(expected_message)
    
    @pytest.mark.asyncio
    async def test_join_room(self, client):
        mock_websocket = AsyncMock()
        client.websocket = mock_websocket
        
        await client.join_room("test_room", "test_user")
        
        assert client.current_room.id == "test_room"
        assert client.current_username == "test_user"
        
        expected_message = '420["joinRoom",{"roomId":"test_room","username":"test_user"}]'
        mock_websocket.send.assert_called_once_with(expected_message)
    
    @pytest.mark.asyncio
    async def test_send_message(self, client):
        mock_websocket = AsyncMock()
        client.websocket = mock_websocket
        client.current_room = Room("test_room")
        client.current_username = "test_user"
        
        await client.send_message("Hello world!")
        
        expected_message = '423["sendMessage",{"roomId":"test_room","message":"Hello world!","username":"test_user"}]'
        mock_websocket.send.assert_called_once_with(expected_message)
    
    @pytest.mark.asyncio
    async def test_send_message_no_room(self, client):
        with pytest.raises(ValueError, match="Room ID and username required"):
            await client.send_message("Hello")
    
    @pytest.mark.asyncio
    async def test_reply_message(self, client):
        mock_websocket = AsyncMock()
        client.websocket = mock_websocket
        client.current_username = "test_user"
        
        user = User("original_user")
        room = Room("test_room")
        original_message = Message("msg_123", "Original message content", user, room)
        
        await client.reply(original_message, "This is a reply")
        
        expected_data = {
            "roomId": "test_room",
            "message": "This is a reply",
            "username": "test_user",
            "replyToId": "msg_123",
            "replyPreview": "Original message content"
        }
        expected_message = f'423["sendMessage",{{"roomId":"test_room","message":"This is a reply","username":"test_user","replyToId":"msg_123","replyPreview":"Original message content"}}]'
        mock_websocket.send.assert_called_once()
    
    def test_check_authentication_success(self, client):
        auth_message = '430[{"authenticated":true,"userId":"123"}]'
        result = client._check_authentication(auth_message)
        
        assert result is True
        assert client.is_authenticated is True
    
    def test_check_authentication_failure(self, client):
        auth_message = '430[{"authenticated":false}]'
        
        with pytest.raises(Exception, match="Authentication failed"):
            client._check_authentication(auth_message)
    
    def test_check_authentication_invalid(self, client):
        auth_message = '42["message","data"]'
        result = client._check_authentication(auth_message)
        
        assert result is False
        assert client.is_authenticated is False
    
    def test_parse_message_valid(self, client):
        raw_message = '42["newMessage",{"id":"msg_123","message":"Hello world","username":"test_user","userAddress":"0x123","timestamp":1234567890000,"messageType":"regular","roomId":"room_123"}]'
        
        message = client._parse_message(raw_message)
        
        assert message is not None
        assert message.id == "msg_123"
        assert message.content == "Hello world"
        assert message.author.username == "test_user"
        assert message.author.address == "0x123"
        assert message.room.id == "room_123"
        assert message.message_type == "regular"
    
    def test_parse_message_invalid(self, client):
        raw_message = '43["otherEvent","data"]'
        
        message = client._parse_message(raw_message)
        
        assert message is None
    
    @pytest.mark.asyncio
    async def test_disconnect(self, client):
        mock_websocket = AsyncMock()
        client.websocket = mock_websocket
        client._running = True
        client.is_authenticated = True
        
        await client.disconnect()
        
        assert client._running is False
        assert client.websocket is None
        assert client.is_authenticated is False
        mock_websocket.close.assert_called_once()

class TestModels:
    def test_user_creation(self):
        user = User("testuser", "0x123")
        
        assert user.username == "testuser"
        assert user.address == "0x123"
        assert str(user) == "testuser"
        assert "testuser" in repr(user)
    
    def test_room_creation(self):
        room = Room("room_123")
        
        assert room.id == "room_123"
        assert str(room) == "room_123"
        assert "room_123" in repr(room)
    
    def test_message_creation(self):
        user = User("testuser")
        room = Room("test_room")
        timestamp = datetime.now()
        
        message = Message("msg_123", "Hello world", user, room, timestamp, "regular")
        
        assert message.id == "msg_123"
        assert message.content == "Hello world"
        assert message.author == user
        assert message.room == room
        assert message.timestamp == timestamp
        assert message.message_type == "regular"
        assert str(message) == "Hello world"
        assert "msg_123" in repr(message)
        assert "testuser" in repr(message)

class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_message_flow(self):
        client = Client("test_token")
        
        events_received = []
        
        @client.event
        async def on_ready():
            events_received.append("ready")
        
        @client.event
        async def on_message(message):
            events_received.append(("message", message.content, message.author.username))
        
        @client.event
        async def on_join(room, user):
            events_received.append(("join", room.id, user.username))
        
        mock_websocket = AsyncMock()
        client.websocket = mock_websocket
        
        await client._handle_message('430[{"authenticated":true}]')
        await client._handle_message('42["newMessage",{"id":"1","message":"test","username":"user1","roomId":"room1","timestamp":1234567890000}]')
        
        assert ("ready",) in events_received or "ready" in events_received
        assert any(event[0] == "message" and event[1] == "test" and event[2] == "user1" for event in events_received if isinstance(event, tuple))
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        client = Client("test_token")
        
        errors_received = []
        
        @client.event
        async def on_error(error):
            errors_received.append(error)
        
        test_error = Exception("Test error")
        await client._dispatch('error', test_error)
        
        assert test_error in errors_received