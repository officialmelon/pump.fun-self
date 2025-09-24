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
                    try:
                        result = handler(*args, **kwargs)
                        if asyncio.iscoroutine(result):
                            tasks.append(result)
                    except Exception:
                        pass
            
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