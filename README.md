# Usage

## Features

- Event-driven architecture with familiar decorator syntax
- Automatic username detection from auth tokens
- Message and reply handling with content moderation warnings
- **Built-in user banning functionality with messageId tracking**
- **Automatic moderator permission detection**
- Built-in reconnection logic and error handling
- Lightweight with minimal logging
- Full async/await support
- Structured data models for messages, users, and rooms

## Quick Start

```python
import asyncio
from pump_self_melon import Client

async def main():
    client = Client(token="your_auth_token")
    
    @client.event
    async def on_ready():
        print("Bot is ready!")
    
    @client.event
    async def on_message(message):
        print(f"{message.author.username}: {message.content}")
        
        if message.content.lower() == "ping":
            await client.send_message("pong!")
        
        elif message.content.lower() == "hello":
            await client.send_message(f"Hello {message.author.username}!")
    
    await client.start("room_id_here")

if __name__ == "__main__":
    asyncio.run(main())
```

## Core Components

### Client

The main client class handles websocket connections and event management.

```python
from pump_self_melon import Client

client = Client(token="your_auth_token")
```

Optional parameters:
- `websocket_uri`: Custom websocket URI (defaults to pump.fun chat)

### Event Decorators

#### @client.event
Decorator for event handlers. Function name determines the event type:

```python
@client.event
async def on_message(message):
    # Handle incoming messages
    pass

@client.event
async def on_ready():
    # Called when bot connects and authenticates
    pass

@client.event
async def on_join(room, user):
    # Called when joining a room
    pass

@client.event
async def on_error(error):
    # Handle errors
    pass
```

#### @client.listen()
Alternative event listener syntax:

```python
@client.listen('message')
async def handle_message(message):
    # Handle messages
    pass
```

### Sending Messages

#### send_message()
Send a regular message to the chat:

```python
await client.send_message("Hello world!")
await client.send_message("Message", room_id="specific_room")
```

#### send_reply()
Send a reply to a specific message (includes reply context):

```python
@client.event
async def on_message(message):
    if message.content == "reply to me":
        await client.send_reply(message, "This is a reply!")
```

**Note**: Regular messages (`send_message`) are less likely to be flagged by content moderation than replies (`send_reply`).

## Data Models

### Message
Represents a chat message:

```python
message.id          # Message ID
message.content     # Message text
message.author      # User object
message.room        # Room object  
message.timestamp   # Datetime object
message.raw_data    # Original message data
```

### User
Represents a user:

```python
user.username       # Display name
user.address        # Wallet address
```

### Room
Represents a chat room:

```python
room.id             # Room identifier
```

## Banning and Moderation

### Enabling Banning

```python
@client.event
async def on_ready():
    # Enable banning functionality
    client.enable_banning()
    
    # Check if you have mod permissions
    has_perms = await client.check_mod_permissions()
    if has_perms:
        print("Moderator permissions confirmed - banning active")
    else:
        print("No moderator permissions - banning disabled")
```

### Banning Users by Message ID

Track and ban users based on their message IDs:

```python
@client.event
async def on_message(message):
    # Check for inappropriate content
    if "spam" in message.content.lower():
        # Ban the user who sent this specific message
        success = await client.ban_user_by_message_id(
            message.id, 
            "Spam detected"
        )
        
        if success:
            print(f"Banned {message.author.username}")
        else:
            print(f"Failed to ban {message.author.username}")
```

### Banning Users by Address

Directly ban users if you know their address:

```python
# Ban a user by their wallet address
success = await client.ban_user_by_address(
    "user_wallet_address_here",
    "Inappropriate behavior"
)
```

### Unbanning Users

```python
# Unban a user by their wallet address  
success = await client.unban_user("user_wallet_address_here")
```

### Ban Statistics

```python
# Get banning statistics
stats = client.get_ban_stats()
print(f"Banned users: {stats['banned_users_count']}")
print(f"Has mod permissions: {stats['has_mod_permissions']}")
```

### Automatic Moderation Example

```python
import asyncio
from pump_self_melon import Client

# Phrases that trigger automatic banning
BAN_TRIGGERS = ["spam", "scam", "inappropriate content"]

client = Client(token="your_token")

@client.event
async def on_ready():
    client.enable_banning()
    print("Auto-moderation bot ready!")

@client.event  
async def on_message(message):
    message_lower = message.content.lower()
    
    for trigger in BAN_TRIGGERS:
        if trigger in message_lower:
            success = await client.ban_user_by_message_id(
                message.id,
                f"Auto-ban: {trigger}"
            )
            
            if success:
                print(f"Auto-banned {message.author.username}")
            break

await client.start("room_id", "username")
```

**Requirements for Banning:**
- You must have moderator permissions in the room
- Banning functionality must be enabled with `client.enable_banning()`
- The library will automatically check and warn about missing permissions

## Advanced Usage

### Multiple Event Handlers
You can register multiple handlers for the same event:

```python
@client.event
async def on_message(message):
    # First handler
    pass

@client.listen('message') 
async def another_handler(message):
    # Second handler
    pass
```

### Error Handling
Handle errors gracefully:

```python
@client.event
async def on_error(error):
    print(f"An error occurred: {error}")
    # Log to file, send notification, etc.
```

### Custom Room and Username
Override defaults when starting:

```python
await client.start("room_id", username="custom_name")
```

### Manual Connection Control
For advanced use cases:

```python
await client.connect()
await client.join_room("room_id", "username")
await client.disconnect()
```

## Content Moderation

The library automatically detects content moderation issues and logs warnings. These typically occur when:
- Messages contain flagged content
- Reply formatting triggers filters
- Rate limits are exceeded

Monitor your logs for warnings like:
```
WARNING: Content moderation issue detected - message may have been filtered
```

## Best Practices

1. **Use send_message over send_reply** - Regular messages are less likely to be flagged
2. **Handle errors gracefully** - Always implement error handlers
3. **Monitor content warnings** - Watch for moderation issues

## Examples

### Echo Bot
```python
@client.event
async def on_message(message):
    if message.content.startswith("echo "):
        text = message.content[5:]
        await client.send_message(f"Echo: {text}")
```

### Welcome Bot
```python
@client.event
async def on_join(room, user):
    await client.send_message(f"Welcome {user.username}!")
```

### Command Handler
```python
@client.event
async def on_message(message):
    if not message.content.startswith("!"):
        return
        
    command = message.content[1:].split()[0]
    
    if command == "ping":
        await client.send_message("Pong!")
    elif command == "help":
        await client.send_message("Available commands: !ping, !help")
```

## Requirements

- Python 3.9+
- websockets 11.0.0+
- aiohttp 3.8.0+

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please read our contributing guidelines and submit pull requests for any improvements.

## Support

For issues and questions:
- GitHub Issues: Report bugs and request features
- Documentation: Check this README and docstrings
- Examples: See the examples/ directory for more usage patterns

## API Reference

### Client

The main client class for connecting to pump.fun.

```python
client = Client(token="your_token")  # Uses correct websocket URI automatically
```

**Note:** The library automatically uses the correct pump.fun chat websocket URI (`wss://livechat.pump.fun/socket.io/?EIO=4&transport=websocket`).

#### Methods

- `start(room_id, username=None)` - Connect and start the client (username auto-fetched from token)
- `send_message(content, room_id=None, username=None)` - Send a message
- `reply(message, content)` - Reply to a message
- `disconnect()` - Disconnect the client

#### Event Decorators

```python
@client.event
async def on_ready():
    # Called when authenticated
    pass

@client.event
async def on_message(message):
    # Called for each message
    pass

@client.event
async def on_join(room, user):
    # Called when joining a room
    pass

@client.event
async def on_error(error):
    # Called on errors
    pass

# Alternative syntax
@client.listen('message')
async def message_handler(message):
    pass
```

### Models

#### Message
```python
message.id          # Message ID
message.content     # Message content
message.author      # User object
message.room        # Room object  
message.timestamp   # Datetime object
message.message_type # Message type
message.raw_data    # Raw message data
```

#### User
```python
user.username       # Username
user.address        # Wallet address
```

#### Room
```python
room.id            # Room/token ID
```

### Utils

```python
from pump_self_melon.utils import get_user_info, get_room_info

# Get user information
user_info = await get_user_info("auth_token")

# Get room/token information  
room_info = await get_room_info("room_id")
```

## Examples

### Basic Echo Bot
```python
@client.event
async def on_message(message):
    if message.content.startswith("echo "):
        echo_text = message.content[5:]
        await client.reply(message, f"You said: {echo_text}")
```

### Message Statistics
```python
message_count = 0
user_messages = {}

@client.event
async def on_message(message):
    global message_count
    message_count += 1
    
    username = message.author.username
    user_messages[username] = user_messages.get(username, 0) + 1
    
    if message.content == "stats":
        top_users = sorted(user_messages.items(), key=lambda x: x[1], reverse=True)[:5]
        stats_text = f"Messages: {message_count}, Top: {', '.join(f'{u}({c})' for u,c in top_users)}"
        await client.send_message(stats_text)
```

### Multiple Event Handlers
```python
@client.listen('message')
async def log_messages(message):
    with open("chat.log", "a") as f:
        f.write(f"{message.timestamp}: {message.author.username}: {message.content}\n")

@client.listen('message') 
async def auto_respond(message):
    if "help" in message.content.lower():
        await client.send_message("Available commands: ping, echo, stats")
```

## Testing

Run the manual tests:
```bash
python tests/manual_tests.py
```

Run examples:
```bash
python tests/examples.py
```

Run pytest (requires pytest installation):
```bash
pytest tests/
```

## License

MIT License
