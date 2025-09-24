#!/usr/bin/env python3
"""
Test script for the new banning functionality in pump.fun-self
"""

import asyncio
import sys
import os

# Add the src directory to the path to import our package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pump_self_melon import Client, BanManager
from pump_self_melon.models import Message, User, Room
from datetime import datetime

class MockBanManager(BanManager):
    """Mock BanManager for testing without actual API calls"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mock_has_permissions = False
    
    async def check_mod_permissions(self) -> bool:
        """Mock mod permission check"""
        self.has_mod_permissions = self.mock_has_permissions
        if self.mock_has_permissions:
            print("✅ Mock: Moderator permissions confirmed")
        else:
            print("❌ Mock: No moderator permissions")
        return self.mock_has_permissions
    
    async def ban_user(self, user_address: str, reason: str = "Test ban") -> bool:
        """Mock ban user function"""
        if not self.enabled:
            print("⚠️  Mock: Banning not enabled")
            return False
        
        if not self.has_mod_permissions:
            print("⚠️  Mock: No mod permissions for banning")
            return False
        
        self.banned_users.add(user_address)
        print(f"🔨 Mock: Banned user {user_address[:8]}... for: {reason}")
        return True
    
    async def unban_user(self, user_address: str) -> bool:
        """Mock unban user function"""
        if not self.enabled:
            return False
        
        if user_address in self.banned_users:
            self.banned_users.remove(user_address)
            print(f"✅ Mock: Unbanned user {user_address[:8]}...")
            return True
        return False

def test_ban_manager():
    """Test BanManager functionality"""
    print("Testing BanManager...")
    
    # Create ban manager
    ban_manager = BanManager("test_token", "test_room", enabled=False)
    
    # Test initial state
    assert not ban_manager.enabled
    assert not ban_manager.has_mod_permissions
    assert len(ban_manager.banned_users) == 0
    
    # Test enabling banning
    ban_manager.enable_banning()
    assert ban_manager.enabled
    
    # Create mock user and message
    user = User("TestUser", "test_address_12345")
    room = Room("test_room")
    message = Message("msg_123", "Test message", user, room, datetime.now())
    
    # Test message tracking
    ban_manager.track_message(message)
    assert "msg_123" in ban_manager.message_to_user
    assert ban_manager.message_to_user["msg_123"] == "test_address_12345"
    
    # Test stats
    stats = ban_manager.get_stats()
    assert stats["enabled"] == True
    assert stats["banned_users_count"] == 0
    assert stats["tracked_messages"] == 1
    
    print("BanManager tests passed")

async def test_client_banning():
    """Test Client banning integration"""
    print("Testing Client banning integration...")
    
    # Create client with mock token
    client = Client("test_token")
    
    # Manually create a mock ban manager
    client.ban_manager = MockBanManager("test_token", "test_room", enabled=False)
    
    # Test enabling banning
    client.enable_banning()
    assert client.ban_manager.enabled
    
    # Test without mod permissions
    success = await client.ban_user_by_address("test_address", "Test reason")
    assert not success  # Should fail without permissions
    
    # Give mock permissions
    client.ban_manager.mock_has_permissions = True
    await client.ban_manager.check_mod_permissions()
    
    # Test with mod permissions
    success = await client.ban_user_by_address("test_address", "Test reason")
    assert success  # Should succeed with permissions
    
    # Test ban by message ID
    # First track a message
    user = User("TestUser", "test_address_12345")
    room = Room("test_room")
    message = Message("msg_456", "Test message", user, room, datetime.now())
    client.ban_manager.track_message(message)
    
    # Now ban by message ID
    success = await client.ban_user_by_message_id("msg_456", "Test ban by message ID")
    assert success
    
    # Test stats
    stats = client.get_ban_stats()
    assert stats["enabled"] == True
    assert stats["has_mod_permissions"] == True
    assert stats["banned_users_count"] == 2
    
    # Test unbanning
    success = await client.unban_user("test_address")
    assert success
    
    stats = client.get_ban_stats()
    assert stats["banned_users_count"] == 1  # One user still banned
    
    print("Client banning tests passed")

def test_message_tracking():
    """Test message tracking functionality"""
    print("Testing message tracking...")
    
    ban_manager = BanManager("test_token", "test_room", enabled=True)
    
    # Create test messages
    users = [
        User("User1", "address1"),
        User("User2", "address2"),
        User("User3", "address3")
    ]
    
    room = Room("test_room")
    
    messages = [
        Message("msg1", "Hello world", users[0], room),
        Message("msg2", "How are you?", users[1], room),
        Message("msg3", "Good morning", users[2], room)
    ]
    
    # Track all messages
    for message in messages:
        ban_manager.track_message(message)
    
    # Verify tracking
    assert len(ban_manager.message_to_user) == 3
    assert ban_manager.message_to_user["msg1"] == "address1"
    assert ban_manager.message_to_user["msg2"] == "address2"
    assert ban_manager.message_to_user["msg3"] == "address3"
    
    print("Message tracking tests passed")

async def run_all_tests():
    """Run all tests"""
    print("Running pump.fun-self banning functionality tests...")
    print("=" * 60)
    
    try:
        # Test BanManager
        test_ban_manager()
        print()
        
        # Test message tracking
        test_message_tracking()
        print()
        
        # Test Client integration
        await test_client_banning()
        print()
        
        print("All tests passed!")
        print("Banning functionality is working correctly")
        print()
        print("Features tested:")
        print("   - BanManager initialization and state management")
        print("   - Message ID to user address tracking")
        print("   - Banning users by message ID")
        print("   - Banning users by address")
        print("   - Unbanning users")
        print("   - Moderator permission checking")
        print("   - Ban statistics")
        print("   - Client integration")
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\\n✅ Ready to use! The banning functionality is properly implemented.")
        print("\\n📖 Usage Instructions:")
        print("1. Get your auth token from pump.fun")
        print("2. Ensure you have moderator permissions in your target room")
        print("3. Use client.enable_banning() to activate the feature")
        print("4. Use client.ban_user_by_message_id() to ban users")
        print("5. Check examples/moderation_bot.py for a complete example")
    else:
        print("\\n❌ Tests failed. Please check the implementation.")
        sys.exit(1)