#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from pump_self_melon import Client

async def main():
    print("Pump-Self Integration Demo")
    print("=========================")
    
    token = input("Enter your auth token (or 'demo' for demo mode): ").strip()
    
    if token.lower() == 'demo':
        print("\\nRunning in demo mode with mock client...")
        print("This will simulate bot behavior without connecting.")
        await demo_mode()
        return
    
    room_id = input("Enter room ID: ").strip()
    
    if not token or not room_id:
        print("Token and room ID are required!")
        return
    
    client = Client(token=token)
    
    message_count = 0
    bot_username = None
    
    @client.event
    async def on_ready():
        nonlocal bot_username
        bot_username = client.current_username
        print(f"✅ Bot connected as {bot_username}!")
        await client.send_message("Hello! I'm now online. Type 'help' for commands.")
    
    @client.event
    async def on_message(message):
        nonlocal message_count
        message_count += 1
        
        print(f"[{message_count}] {message.author.username}: {message.content}")
        
        if message.author.username == bot_username:
            return
        
        content = message.content.lower().strip()
        
        if content == "ping":
            await client.send_message("pong! 🏓")
        
        elif content == "help":
            help_text = "Available commands: ping, echo <text>, stats, time, hello"
            await client.reply(message, help_text)
        
        elif content.startswith("echo "):
            echo_text = message.content[5:]
            await client.reply(message, f"📢 {echo_text}")
        
        elif content == "stats":
            await client.send_message(f"📊 Total messages processed: {message_count}")
        
        elif content == "time":
            import datetime
            now = datetime.datetime.now().strftime("%H:%M:%S")
            await client.send_message(f"🕐 Current time: {now}")
        
        elif content == "hello":
            await client.send_message(f"👋 Hello {message.author.username}!")
    
    @client.event
    async def on_join(room, user):
        print(f"🚀 Joined room {room.id[:12]}... as {user.username}")
    
    @client.event
    async def on_error(error):
        print(f"❌ Error: {error}")
    
    print(f"\\n🤖 Starting bot...")
    print("Press Ctrl+C to stop")
    
    try:
        await client.start(room_id)
    except KeyboardInterrupt:
        print("\\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\\n❌ Error: {e}")
    finally:
        await client.disconnect()

async def demo_mode():
    print("\\n🎭 Demo Mode Active")
    print("Simulating bot responses...")
    
    demo_messages = [
        ("user1", "ping"),
        ("user2", "hello"),
        ("user3", "echo Hello World!"),
        ("user4", "stats"),
        ("user5", "help")
    ]
    
    message_count = 0
    
    for username, content in demo_messages:
        message_count += 1
        print(f"\\n[{message_count}] {username}: {content}")
        
        if content == "ping":
            print("🤖 Bot: pong! 🏓")
        elif content == "hello":
            print(f"🤖 Bot: 👋 Hello {username}!")
        elif content.startswith("echo "):
            echo_text = content[5:]
            print(f"🤖 Bot: 📢 {echo_text}")
        elif content == "stats":
            print(f"🤖 Bot: 📊 Total messages processed: {message_count}")
        elif content == "help":
            print("🤖 Bot: Available commands: ping, echo <text>, stats, time, hello")
        
        await asyncio.sleep(0.5)
    
    print("\\n✅ Demo completed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nExiting...")