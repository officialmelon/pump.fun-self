import asyncio
from pump_self_melon import Client

async def main():
    print("Pump-Self Example Bot")
    print("Replace YOUR_TOKEN_HERE and ROOM_ID_HERE with your actual values")
    
    client = Client(token="YOUR_TOKEN_HERE")
    
    @client.event
    async def on_ready():
        print("Bot is connected and ready!")
        
        # Optional: Enable banning functionality
        # client.enable_banning()
        # print("Banning functionality enabled")
    
    @client.event
    async def on_message(message):
        print(f"[{message.room.id[:8]}] {message.author.username}: {message.content}")
        
        if message.content.lower() == "ping":
            await client.send_message("pong!")
        
        elif message.content.lower().startswith("echo "):
            text = message.content[5:]
            await client.send_message(f"Echo: {text}")
        
        elif message.content.lower() == "hello":
            await client.send_message(f"Hello {message.author.username}!")
        
        # Example: Ban user if they send inappropriate content
        # (Uncomment to enable - requires moderator permissions)
        # elif "spam" in message.content.lower():
        #     success = await client.ban_user_by_message_id(message.id, "Spam detected")
        #     if success:
        #         print(f"Banned user {message.author.username} for spam")
    
    @client.event
    async def on_join(room, user):
        print(f"Joined room {room.id} as {user.username}")
    
    @client.event
    async def on_error(error):
        print(f"Error: {error}")
    
    await client.start("ROOM_ID_HERE")

if __name__ == "__main__":
    asyncio.run(main())