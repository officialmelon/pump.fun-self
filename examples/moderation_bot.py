#!/usr/bin/env python3
"""
Example demonstrating the banning functionality in pump.fun-self

This example shows how to:
1. Connect to a pump.fun room with banning enabled
2. Automatically ban users based on message content
3. Ban users by message ID
4. Check moderator permissions
"""

import asyncio
import pump_self_melon

# Configuration
TOKEN = "your_auth_token_here"  # Replace with your actual auth token
ROOM_ID = "your_room_id_here"   # Replace with your room ID
USERNAME = "MyBot"              # Replace with your username

# List of phrases that trigger automatic banning
BAN_TRIGGERS = [
    "spam message",
    "inappropriate content", 
    "scam link",
    "hate speech"
]

class ModerationBot:
    def __init__(self):
        self.client = pump_self_melon.Client(TOKEN)
        self.banned_message_ids = set()
    
    async def setup_events(self):
        """Set up event handlers"""
        
        @self.client.event
        async def on_ready():
            print("🤖 Bot is ready and connected!")
            
            # Enable banning functionality
            self.client.enable_banning()
            
            # Check if we have mod permissions
            has_perms = await self.client.check_mod_permissions()
            if has_perms:
                print("✅ Bot has moderator permissions - auto-moderation active")
            else:
                print("⚠️  Bot does not have moderator permissions - manual actions only")
        
        @self.client.event
        async def on_message(message):
            await self.handle_message(message)
        
        @self.client.event 
        async def on_join(room, user):
            print(f"📥 {user.username} joined {room.id}")
        
        @self.client.event
        async def on_error(error):
            print(f"❌ Error: {error}")
    
    async def handle_message(self, message):
        """Handle incoming messages and check for ban triggers"""
        print(f"💬 [{message.author.username}]: {message.content}")
        
        # Skip our own messages
        if message.author.username == USERNAME:
            return
        
        # Check for ban triggers in message content
        message_lower = message.content.lower()
        
        for trigger in BAN_TRIGGERS:
            if trigger in message_lower:
                print(f"🚨 Ban trigger detected: '{trigger}' in message from {message.author.username}")
                
                # Attempt to ban the user by message ID
                success = await self.client.ban_user_by_message_id(
                    message.id, 
                    f"Auto-ban: {trigger}"
                )
                
                if success:
                    print(f"🔨 Successfully banned {message.author.username} for: {trigger}")
                    self.banned_message_ids.add(message.id)
                else:
                    print(f"❌ Failed to ban {message.author.username}")
                
                break
    
    async def run(self):
        """Run the moderation bot"""
        print("🚀 Starting moderation bot...")
        print(f"📡 Connecting to room: {ROOM_ID}")
        print(f"👤 Username: {USERNAME}")
        print(f"🎯 Ban triggers: {', '.join(BAN_TRIGGERS)}")
        print("-" * 50)
        
        # Set up event handlers
        await self.setup_events()
        
        # Start the client
        await self.client.start(ROOM_ID, USERNAME)

# Additional utility functions you can use:

async def manual_ban_example():
    """Example of manually banning a user"""
    client = pump_self_melon.Client(TOKEN)
    
    # Enable banning
    client.enable_banning() 
    
    try:
        # Connect to room
        await client.start(ROOM_ID, USERNAME)
        
        # Example: Ban a user by their address
        user_address = "user_address_here"
        success = await client.ban_user_by_address(user_address, "Manual ban")
        
        if success:
            print(f"✅ User banned: {user_address}")
        else:
            print(f"❌ Failed to ban user: {user_address}")
        
        # Example: Get ban statistics  
        stats = client.get_ban_stats()
        print(f"📊 Ban stats: {stats}")
        
    finally:
        await client.close()

async def check_permissions_example():
    """Example of checking moderator permissions"""
    client = pump_self_melon.Client(TOKEN)
    
    try:
        await client.start(ROOM_ID, USERNAME)
        
        # Check if we have mod permissions
        has_perms = await client.check_mod_permissions()
        
        if has_perms:
            print("✅ You have moderator permissions")
            
            # Enable banning since we have permissions
            client.enable_banning()
            print("🔨 Banning functionality enabled")
            
        else:
            print("❌ You do not have moderator permissions")
            print("   Banning functionality will not work")
        
    finally:
        await client.close()

if __name__ == "__main__":
    # Make sure to update TOKEN, ROOM_ID, and USERNAME before running
    if TOKEN == "your_auth_token_here":
        print("⚠️  Please update the TOKEN, ROOM_ID, and USERNAME variables before running!")
        exit(1)
    
    bot = ModerationBot()
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")