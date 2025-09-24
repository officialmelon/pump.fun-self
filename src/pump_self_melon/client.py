import asyncio
import websockets
import json
import time
import logging
from typing import Optional, Callable, Dict, Any, List
from functools import wraps
from datetime import datetime

from .models import Message, User, Room
from .utils import get_user_info
from .ban_manager import BanManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

class Client:
    def __init__(self, token: str, websocket_uri: str = "wss://livechat.pump.fun/socket.io/?EIO=4&transport=websocket"):
        self.token = token
        self.websocket_uri = websocket_uri
        self.websocket = None
        self.is_authenticated = False
        self.current_room = None
        self.current_username = None
        self.ban_manager = None
        
        self._event_handlers = {
            'message': [],
            'ready': [],
            'join': [],
            'leave': [],
            'error': []
        }
        
        self._running = False
    
    def event(self, func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Event handler must be a coroutine function')
        
        event_name = func.__name__
        if event_name.startswith('on_'):
            event_name = event_name[3:]
        
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        
        self._event_handlers[event_name].append(func)
        return func
    
    def listen(self, event_name: str):
        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('Event handler must be a coroutine function')
            
            if event_name not in self._event_handlers:
                self._event_handlers[event_name] = []
            
            self._event_handlers[event_name].append(func)
            return func
        return decorator
    
    async def _dispatch(self, event_name: str, *args, **kwargs):
        handlers = self._event_handlers.get(event_name, [])
        if handlers:
            tasks = [handler(*args, **kwargs) for handler in handlers]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def connect(self) -> bool:
        try:
            self.websocket = await websockets.connect(self.websocket_uri)
            return True
        except Exception as e:
            await self._dispatch('error', e)
            return False
    
    async def _send_auth(self):
        timestamp = int(time.time() * 1000)
        auth_message = f'40{{"origin":"https://pump.fun","timestamp":{timestamp},"token":"{self.token}"}}'
        await self.websocket.send(auth_message)
    
    async def join_room(self, room_id: str, username: str = "anonymous"):
        self.current_room = Room(room_id)
        self.current_username = username
        
        # Initialize ban manager for this room
        if self.ban_manager is None:
            self.ban_manager = BanManager(self.token, room_id, enabled=False)
        
        join_message = f'420["joinRoom",{{"roomId":"{room_id}","username":"{username}"}}]'
        await self.websocket.send(join_message)
        
        # Check mod permissions if banning is enabled
        if self.ban_manager and self.ban_manager.enabled:
            print("🔍 Checking moderator permissions...")
            await self.ban_manager.check_mod_permissions()
            if not self.ban_manager.has_mod_permissions:
                print("⚠️  WARNING: Banning is enabled but you don't have moderator permissions!")
                print("   You will need moderator permissions to ban users effectively.")
            else:
                print("✅ Moderator permissions confirmed - banning functionality active")
        
        await self._dispatch('join', self.current_room, User(username))
    
    async def send_message(self, content: str, room_id: Optional[str] = None, username: Optional[str] = None):
        room_id = room_id or (self.current_room.id if self.current_room else None)
        username = username or self.current_username
        
        if not room_id or not username:
            raise ValueError("Room ID and username required")
        
        message_data = {
            "roomId": room_id,
            "message": content,
            "username": username
        }
        
        chat_message = f'423["sendMessage",{json.dumps(message_data)}]'
        await self.websocket.send(chat_message)

    async def send_reply(self, message: Message, content: str):
        reply_data = {
            "roomId": message.room.id,
            "message": content,
            "username": self.current_username,
            "replyToId": message.id,
            "replyPreview": message.content[:50] if message.content else ""
        }
        
        reply_message = f'423["sendMessage",{json.dumps(reply_data)}]'
        await self.websocket.send(reply_message)
    
    async def reply(self, message: Message, content: str):
        # Deprecated alias for send_reply
        await self.send_reply(message, content)
    
    def _check_authentication(self, raw_message: str) -> bool:
        try:
            if len(raw_message) > 2 and raw_message[:3] == "430":
                json_part = raw_message[3:]
                if json_part.startswith('['):
                    parsed = json.loads(json_part)
                    
                    if isinstance(parsed, list) and len(parsed) > 0:
                        if isinstance(parsed[0], dict) and 'authenticated' in parsed[0]:
                            auth_status = parsed[0]['authenticated']
                            if auth_status:
                                self.is_authenticated = True
                                return True
                            else:
                                raise Exception("Authentication failed")
        except json.JSONDecodeError:
            pass
        except Exception as e:
            raise e
        
        return False
    
    def _parse_message(self, raw_message: str) -> Optional[Message]:
        try:
            if len(raw_message) > 2 and raw_message[:2] == "42":
                json_part = raw_message[2:]
                if json_part.startswith('['):
                    parsed = json.loads(json_part)
                    
                    if (isinstance(parsed, list) and len(parsed) >= 2 and 
                        parsed[0] == "newMessage" and isinstance(parsed[1], dict)):
                        
                        msg_data = parsed[1]
                        
                        user = User(
                            username=msg_data.get('username', 'unknown'),
                            address=msg_data.get('userAddress')
                        )
                        
                        room = Room(msg_data.get('roomId', ''))
                        
                        timestamp = None
                        if msg_data.get('timestamp'):
                            try:
                                timestamp = datetime.fromtimestamp(msg_data['timestamp'] / 1000)
                            except:
                                pass
                        
                        message = Message(
                            id=msg_data.get('id', ''),
                            content=msg_data.get('message', ''),
                            author=user,
                            room=room,
                            timestamp=timestamp,
                            message_type=msg_data.get('messageType', 'regular'),
                            raw_data=msg_data
                        )
                        
                        return message
        except json.JSONDecodeError:
            pass
        except Exception:
            pass
        
        return None
    
    async def _handle_message(self, raw_message: str):
        if self._check_authentication(raw_message):
            await self._dispatch('ready')
            return
            
        # Check for content moderation issues
        if "Invalid message" in raw_message and "Failed to subscribe" in raw_message:
            logger.warning("Content moderation issue detected - message may have been filtered")
        
        message = self._parse_message(raw_message)
        if message:
            # Track message for potential banning
            if self.ban_manager:
                self.ban_manager.track_message(message)
            
            await self._dispatch('message', message)
    
    async def _listen(self):
        try:
            async for raw_message in self.websocket:
                await self._handle_message(raw_message)
        except websockets.exceptions.ConnectionClosed:
            if self._running:
                raise
        except Exception as e:
            await self._dispatch('error', e)
            if self._running:
                raise
    
    async def start(self, room_id: str, username: Optional[str] = None):
        self._running = True
        max_reconnect_attempts = 10
        reconnect_delay = 5
        attempt = 0
        
        # Auto-fetch username from user info if not provided
        if username is None:
            try:
                user_info = await get_user_info(self.token)
                username = user_info.get("username")
                if not username:
                    raise Exception("No username found in user info")
            except Exception as e:
                await self._dispatch('error', f"Failed to get username from user info: {e}")
                return
        
        while attempt < max_reconnect_attempts and self._running:
            try:
                if attempt > 0:
                    await asyncio.sleep(reconnect_delay)
                
                if await self.connect():
                    attempt = 0
                    
                    try:
                        await self._send_auth()
                        await asyncio.sleep(1)
                        await self.join_room(room_id, username)
                        await self._listen()
                    except (websockets.exceptions.ConnectionClosed, 
                           websockets.exceptions.WebSocketException):
                        if self._running:
                            attempt += 1
                            continue
                        else:
                            break
                    except Exception as e:
                        await self._dispatch('error', e)
                        if self._running:
                            attempt += 1
                            continue
                        else:
                            break
                else:
                    attempt += 1
                    continue
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                await self._dispatch('error', e)
                attempt += 1
                await asyncio.sleep(reconnect_delay)
        
        await self.disconnect()
    
    async def disconnect(self):
        self._running = False
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.close()
            except Exception:
                pass
        self.websocket = None
        self.is_authenticated = False
    
    async def close(self):
        if self.ban_manager:
            await self.ban_manager.close()
        await self.disconnect()
    
    def enable_banning(self):
        """Enable automatic user banning functionality"""
        if self.ban_manager:
            self.ban_manager.enable_banning()
        else:
            print("⚠️  Cannot enable banning: not connected to a room yet")
    
    def disable_banning(self):
        """Disable automatic user banning functionality"""
        if self.ban_manager:
            self.ban_manager.disable_banning()
    
    async def ban_user_by_message_id(self, message_id: str, reason: str = "Inappropriate content") -> bool:
        """
        Ban a user based on their message ID
        
        Args:
            message_id: The ID of the message from the user to ban
            reason: Reason for the ban
            
        Returns:
            True if ban was successful, False otherwise
        """
        if not self.ban_manager:
            print("⚠️  Banning not available: not connected to a room")
            return False
        
        return await self.ban_manager.ban_by_message_id(message_id, reason)
    
    async def ban_user_by_address(self, user_address: str, reason: str = "Inappropriate content") -> bool:
        """
        Ban a user by their address
        
        Args:
            user_address: The address of the user to ban
            reason: Reason for the ban
            
        Returns:
            True if ban was successful, False otherwise
        """
        if not self.ban_manager:
            print("⚠️  Banning not available: not connected to a room")
            return False
        
        return await self.ban_manager.ban_user(user_address, reason)
    
    async def unban_user(self, user_address: str) -> bool:
        """
        Unban a user by their address
        
        Args:
            user_address: The address of the user to unban
            
        Returns:
            True if unban was successful, False otherwise
        """
        if not self.ban_manager:
            print("⚠️  Banning not available: not connected to a room")
            return False
        
        return await self.ban_manager.unban_user(user_address)
    
    def get_ban_stats(self) -> dict:
        """Get banning statistics"""
        if not self.ban_manager:
            return {"error": "Banning not available: not connected to a room"}
        
        return self.ban_manager.get_stats()
    
    async def check_mod_permissions(self) -> bool:
        """Check if the current user has moderator permissions"""
        if not self.ban_manager:
            return False
        
        return await self.ban_manager.check_mod_permissions()

def on_message(func):
    return func

def on_ready(func):
    return func

def on_join(func):
    return func

def on_leave(func):
    return func

def on_error(func):
    return func