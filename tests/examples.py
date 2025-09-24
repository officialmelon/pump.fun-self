import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from pump_self_melon import Client

async def example_basic_bot():
    client = Client(token="your_auth_token_here")
    
    @client.event
    async def on_ready():
        print("Bot connected and authenticated!")
    
    @client.event
    async def on_message(message):
        print(f"[{message.room.id[:8]}] {message.author.username}: {message.content}")
        
        if message.content.lower() == "ping":
            await client.send_message("pong!")
        
        elif message.content.lower().startswith("echo "):
            echo_text = message.content[5:]
            await client.reply(message, f"You said: {echo_text}")
        
        elif message.content.lower() == "hello":
            await client.send_message(f"Hello {message.author.username}!")
    
    @client.event
    async def on_join(room, user):
        print(f"Joined room {room.id} as {user.username}")
    
    @client.event
    async def on_error(error):
        print(f"Error occurred: {error}")
    
    await client.start("your_room_id_here")

async def example_advanced_bot():
    client = Client(token="your_auth_token_here")
    
    message_count = 0
    user_messages = {}
    
    @client.event
    async def on_ready():
        print("Advanced bot ready!")
    
    @client.event
    async def on_message(message):
        nonlocal message_count
        message_count += 1
        
        username = message.author.username
        if username not in user_messages:
            user_messages[username] = 0
        user_messages[username] += 1
        
        print(f"Message #{message_count} from {username}: {message.content}")
        
        if message.content.lower() == "stats":
            top_users = sorted(user_messages.items(), key=lambda x: x[1], reverse=True)[:5]
            stats_text = f"Total messages: {message_count}\\nTop users: "
            stats_text += ", ".join(f"{user}({count})" for user, count in top_users)
            await client.send_message(stats_text)
        
        elif message.content.lower().startswith("respond "):
            response = message.content[8:]
            await client.reply(message, response)
        
        elif "@everyone" in message.content.lower():
            await client.send_message("Hello everyone! 👋")
    
    await client.start("your_room_id_here")

async def example_event_listener():
    client = Client(token="your_auth_token_here")
    
    @client.listen('message')
    async def log_message(message):
        with open("messages.log", "a") as f:
            f.write(f"{message.timestamp}: {message.author.username}: {message.content}\\n")
    
    @client.listen('message')
    async def auto_respond(message):
        if "help" in message.content.lower():
            await client.send_message("Available commands: ping, echo <text>, hello, stats")
    
    @client.event
    async def on_ready():
        print("Event listener bot ready!")
    
    await client.start("your_room_id_here")

if __name__ == "__main__":
    print("Pump-Self Examples")
    print("1. Basic Bot")
    print("2. Advanced Bot")
    print("3. Event Listener Bot")
    
    choice = input("Choose an example (1-3): ").strip()
    
    try:
        if choice == "1":
            asyncio.run(example_basic_bot())
        elif choice == "2":
            asyncio.run(example_advanced_bot())
        elif choice == "3":
            asyncio.run(example_event_listener())
        else:
            print("Invalid choice")
    except KeyboardInterrupt:
        print("\\nBot stopped by user")
    except Exception as e:
        print(f"Error: {e}")