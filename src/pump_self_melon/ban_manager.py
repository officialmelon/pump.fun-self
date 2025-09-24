"""
Ban management system for pump.fun-self
"""
import aiohttp
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from .models import Message, User

logger = logging.getLogger(__name__)

class BanManager:
    """Manages banning users based on message IDs and user addresses"""
    
    def __init__(self, auth_token: str, room_id: str, enabled: bool = False):
        """
        Initialize the ban manager
        
        Args:
            auth_token: Authentication token for API requests
            room_id: The room ID where banning will occur
            enabled: Whether banning functionality is enabled
        """
        self.auth_token = auth_token
        self.room_id = room_id
        self.enabled = enabled
        self.has_mod_permissions = False
        
        # Track message ID to user address mapping
        self.message_to_user: Dict[str, str] = {}
        
        # Track banned users and messages
        self.banned_users: Set[str] = set()
        self.banned_messages: Set[str] = set()
        
        # Session for HTTP requests
        self._session = None
    
    def enable_banning(self):
        """Enable the banning functionality"""
        self.enabled = True
        if not self.has_mod_permissions:
            print("⚠️  WARNING: Banning enabled but no moderator permissions detected!")
            print("   You will need moderator permissions to ban users effectively.")
    
    def disable_banning(self):
        """Disable the banning functionality"""
        self.enabled = False
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            cookies = {"auth_token": self.auth_token}
            self._session = aiohttp.ClientSession(cookies=cookies)
        return self._session
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def track_message(self, message: Message):
        """Track a message for potential banning"""
        if not self.enabled:
            return
        
        if message.id and message.author.address:
            self.message_to_user[message.id] = message.author.address
            logger.debug(f"Tracking message {message.id} from user {message.author.address}")
    
    async def check_mod_permissions(self) -> bool:
        """Check if the user has moderator permissions in the room"""
        try:
            session = await self._get_session()
            headers = {
                "accept": "application/json",
                "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors", 
                "sec-fetch-site": "same-site"
            }
            
            # Try to access the moderation endpoint
            url = f"https://livechat.pump.fun/chat/moderation/rooms/{self.room_id}/participants"
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    self.has_mod_permissions = True
                    logger.info("✅ Moderator permissions confirmed")
                    return True
                elif response.status == 403:
                    self.has_mod_permissions = False
                    logger.warning("❌ No moderator permissions detected")
                    return False
                else:
                    logger.warning(f"Unknown response when checking mod permissions: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking mod permissions: {e}")
            return False
    
    async def ban_by_message_id(self, message_id: str, reason: str = "Inappropriate content") -> bool:
        """
        Ban a user based on their message ID
        
        Args:
            message_id: The ID of the message from the user to ban
            reason: Reason for the ban
            
        Returns:
            True if ban was successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Banning is not enabled")
            return False
        
        if not self.has_mod_permissions:
            logger.warning("Cannot ban user: no moderator permissions")
            return False
        
        # Find user address from message ID
        user_address = self.message_to_user.get(message_id)
        if not user_address:
            logger.error(f"No user address found for message ID: {message_id}")
            return False
        
        return await self.ban_user(user_address, reason)
    
    async def ban_user(self, user_address: str, reason: str = "Inappropriate content") -> bool:
        """
        Ban a user by their address
        
        Args:
            user_address: The address of the user to ban
            reason: Reason for the ban
            
        Returns:
            True if ban was successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Banning is not enabled")
            return False
        
        if not self.has_mod_permissions:
            logger.warning("Cannot ban user: no moderator permissions")
            return False
        
        if user_address in self.banned_users:
            logger.info(f"User {user_address[:8]}... is already banned")
            return True
        
        try:
            session = await self._get_session()
            url = f"https://livechat.pump.fun/chat/moderation/rooms/{self.room_id}/bans"
            
            headers = {
                "accept": "*/*",
                "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                "cache-control": "no-cache",
                "content-type": "application/json",
                "pragma": "no-cache",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site"
            }
            
            data = {
                "userAddress": user_address,
                "reason": reason
            }
            
            async with session.post(url, headers=headers, json=data) as response:
                if response.status in [200, 201, 204]:
                    self.banned_users.add(user_address)
                    logger.info(f"✅ Successfully banned user {user_address[:8]}... for: {reason}")
                    print(f"🔨 BANNED USER: {user_address[:8]}... | Reason: {reason}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to ban user {user_address[:8]}...: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error banning user {user_address[:8]}...: {e}")
            return False
    
    async def unban_user(self, user_address: str) -> bool:
        """
        Unban a user by their address
        
        Args:
            user_address: The address of the user to unban
            
        Returns:
            True if unban was successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Banning is not enabled")
            return False
        
        if not self.has_mod_permissions:
            logger.warning("Cannot unban user: no moderator permissions")
            return False
        
        try:
            session = await self._get_session()
            url = f"https://livechat.pump.fun/chat/moderation/rooms/{self.room_id}/bans/{user_address}"
            
            headers = {
                "accept": "*/*",
                "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site"
            }
            
            async with session.delete(url, headers=headers) as response:
                if response.status in [200, 204]:
                    self.banned_users.discard(user_address)
                    logger.info(f"✅ Successfully unbanned user {user_address[:8]}...")
                    print(f"✅ UNBANNED USER: {user_address[:8]}...")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to unban user {user_address[:8]}...: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error unbanning user {user_address[:8]}...: {e}")
            return False
    
    def is_user_banned(self, user_address: str) -> bool:
        """Check if a user is currently banned"""
        return user_address in self.banned_users
    
    def get_banned_users(self) -> List[str]:
        """Get list of all banned user addresses"""
        return list(self.banned_users)
    
    def get_stats(self) -> Dict:
        """Get banning statistics"""
        return {
            "enabled": self.enabled,
            "has_mod_permissions": self.has_mod_permissions,
            "banned_users_count": len(self.banned_users),
            "tracked_messages": len(self.message_to_user),
            "banned_users": list(self.banned_users)
        }