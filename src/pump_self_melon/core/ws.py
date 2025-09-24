import asyncio
from typing import Callable, Any, Dict, List

class EventEmitter:
    def __init__(self):
        self._events: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, handler: Callable):
        if event not in self._events:
            self._events[event] = []
        self._events[event].append(handler)
    
    def off(self, event: str, handler: Callable):
        if event in self._events:
            try:
                self._events[event].remove(handler)
            except ValueError:
                pass
    
    async def emit(self, event: str, *args, **kwargs):
        if event in self._events:
            tasks = []
            for handler in self._events[event]:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(*args, **kwargs))
                else:
                    tasks.append(asyncio.create_task(asyncio.coroutine(lambda: handler(*args, **kwargs))()))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

class RateLimiter:
    def __init__(self, max_calls: int = 5, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self):
        now = asyncio.get_event_loop().time()
        
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                return await self.acquire()
        
        self.calls.append(now)
        return True
            logger.info("Connecting to %s", self.url)
            self.websocket = await websockets.connect(self.url)
            logger.info("Connection established")
            return True
        except Exception as exc:
            logger.error("Connection failed: %s", exc)
            return False

    async def send_initial_message(self):
        timestamp = int(time.time() * 1000)
        payload = {"origin": "https://pump.fun", "timestamp": timestamp, "token": self.bot_token}
        message = f'40{json.dumps(payload)}'
        logger.info("Sending authentication message")
        await self.websocket.send(message)

    async def join_room(self, room_id: Optional[str] = None, username: Optional[str] = None):
        room = room_id or self.room_id
        user = username or self.default_username
        payload = {"roomId": room, "username": user}
        message = f'420{json.dumps(["joinRoom", payload])}'
        logger.info("Joining room %s as %s", room, user)
        await self.websocket.send(message)

    async def send_message(self, message_text: str):
        try:
            payload = {"roomId": self.room_id, "message": message_text, "username": self.bot_username}
            message = f'423{json.dumps(["sendMessage", payload])}'
            logger.info("Sending message to room %s", self.room_id)
            await self.websocket.send(message)
        except Exception as exc:
            logger.error("Failed to send message: %s", exc)

    async def send_reply(self, message_text: str, reply_to_id: Optional[str] = None, reply_preview: Optional[str] = None):
        try:
            payload = {"roomId": self.room_id, "message": message_text, "username": self.bot_username}
            if reply_to_id:
                payload["replyToId"] = reply_to_id
            if reply_preview:
                payload["replyPreview"] = reply_preview
            message = f'423{json.dumps(["sendMessage", payload])}'
            logger.info("Sending reply in room %s", self.room_id)
            await self.websocket.send(message)
        except Exception as exc:
            logger.error("Failed to send reply: %s", exc)

    def check_authentication(self, message: str) -> bool:
        try:
            if message.startswith("430"):
                json_part = message[3:]
                parsed = json.loads(json_part)
                if isinstance(parsed, list) and parsed:
                    first = parsed[0]
                    if isinstance(first, dict) and "authenticated" in first:
                        if first["authenticated"]:
                            logger.info("Authentication successful")
                            self.is_authenticated = True
                            return True
                        logger.error("Authentication failed")
                        raise SystemExit("Authentication failed")
        except json.JSONDecodeError:
            logger.debug("Received non-JSON authentication payload")
        except Exception as exc:
            logger.error("Authentication check error: %s", exc)
        return False

    async def listen_for_messages(self):
        logger.info("Listening for incoming messages")
        try:
            async for message in self.websocket:
                if self.check_authentication(message):
                    continue
                if self.message_handler:
                    try:
                        await self.message_handler(message)
                    except Exception as exc:
                        logger.error("Message handler error: %s", exc)
                else:
                    logger.debug("Received message: %s", message)
        except websockets.exceptions.ConnectionClosed as exc:
            logger.info("WebSocket connection closed: %s", exc)
            raise
        except Exception as exc:
            logger.error("Error while listening for messages: %s", exc)
            raise

    async def disconnect(self):
        if self.websocket is not None:
            try:
                if not getattr(self.websocket, "closed", False):
                    await self.websocket.close()
                    logger.info("WebSocket connection closed")
            except Exception as exc:
                logger.error("Error closing WebSocket: %s", exc)
        self.websocket = None
        self.is_authenticated = False

    async def run(self):
        max_reconnect_attempts = 10
        reconnect_delay = 5
        attempt = 0

        while attempt < max_reconnect_attempts:
            try:
                if attempt > 0:
                    logger.info("Reconnection attempt %d/%d", attempt, max_reconnect_attempts)
                    await asyncio.sleep(reconnect_delay)

                if not await self.connect():
                    attempt += 1
                    continue

                attempt = 0

                try:
                    await self.send_initial_message()
                    await asyncio.sleep(1)
                    await self.join_room()
                    await self.listen_for_messages()
                except (websockets.exceptions.ConnectionClosed, websockets.exceptions.WebSocketException) as exc:
                    logger.warning("Connection lost: %s", exc)
                    await self.disconnect()
                    attempt += 1
                    continue
                except Exception as exc:
                    logger.error("Runtime error: %s", exc)
                    await self.disconnect()
                    attempt += 1
                    continue

            except KeyboardInterrupt:
                logger.info("Termination requested by user")
                break
            except Exception as exc:
                logger.error("Unexpected error: %s", exc)
                attempt += 1
                await asyncio.sleep(reconnect_delay)

        if attempt >= max_reconnect_attempts:
            logger.error("Exceeded maximum reconnection attempts (%d)", max_reconnect_attempts)

        await self.disconnect()
