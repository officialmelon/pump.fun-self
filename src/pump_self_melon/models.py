from typing import Optional, Dict, Any
from datetime import datetime

class User:
    def __init__(self, username: str, address: Optional[str] = None):
        self.username = username
        self.address = address
    
    def __str__(self):
        return self.username
    
    def __repr__(self):
        return f"<User username={self.username} address={self.address}>"

class Room:
    def __init__(self, room_id: str):
        self.id = room_id
    
    def __str__(self):
        return self.id
    
    def __repr__(self):
        return f"<Room id={self.id}>"

class Message:
    def __init__(self, id: str, content: str, author: User, room: Room, 
                 timestamp: Optional[datetime] = None, message_type: str = "regular",
                 raw_data: Optional[Dict[str, Any]] = None):
        self.id = id
        self.content = content
        self.author = author
        self.room = room
        self.timestamp = timestamp or datetime.now()
        self.message_type = message_type
        self.raw_data = raw_data or {}
    
    def __str__(self):
        return self.content
    
    def __repr__(self):
        return f"<Message id={self.id} author={self.author.username} content='{self.content[:30]}...'>"