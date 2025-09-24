import asyncio
from pump_self_melon import Client

async def main():
    print("Pump-Self Example Bot")
    print("Replace YOUR_TOKEN_HERE and ROOM_ID_HERE with your actual values")
    
    client = Client(token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhZGRyZXNzIjoiNzVDTXpQZWVZWjJTbzhDUXBudWd6M3RucWtMWjRRdnlqNmVFUFdvMkQ4ZHIiLCJyb2xlcyI6WyJ1c2VyIl0sImlhdCI6MTc1ODYzMjgzNywiZXhwIjoxNzYxMjI0ODM3fQ.CRlPkM4HUUcel-SaJjYk3-c1xbcrYhFAqt6oiGFSaI0")
    
    @client.event
    async def on_ready():
        print("Bot is connected and ready!")
        # await client.send_message("Bot online")  # Uncomment if you want a welcome message
    
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
    
    @client.event
    async def on_join(room, user):
        print(f"Joined room {room.id} as {user.username}")
    
    @client.event
    async def on_error(error):
        print(f"Error: {error}")
    
    await client.start("DLDayw1zKbYdwKCDgr1isTtj96GzVeCdEGxe4zvUpump")

if __name__ == "__main__":
    asyncio.run(main())