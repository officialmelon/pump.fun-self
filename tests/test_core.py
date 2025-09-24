import pytest
import asyncio
from pump_self_melon.core import EventEmitter, RateLimiter

class TestEventEmitter:
    @pytest.fixture
    def emitter(self):
        return EventEmitter()
    
    def test_on_event_registration(self, emitter):
        def test_handler():
            pass
        
        emitter.on('test_event', test_handler)
        
        assert 'test_event' in emitter._events
        assert test_handler in emitter._events['test_event']
    
    def test_off_event_removal(self, emitter):
        def test_handler():
            pass
        
        emitter.on('test_event', test_handler)
        emitter.off('test_event', test_handler)
        
        assert test_handler not in emitter._events.get('test_event', [])
    
    def test_off_nonexistent_handler(self, emitter):
        def test_handler():
            pass
        
        emitter.off('test_event', test_handler)
    
    @pytest.mark.asyncio
    async def test_emit_async_handler(self, emitter):
        called = False
        
        async def async_handler():
            nonlocal called
            called = True
        
        emitter.on('test_event', async_handler)
        await emitter.emit('test_event')
        
        assert called
    
    @pytest.mark.asyncio
    async def test_emit_sync_handler(self, emitter):
        called = False
        
        def sync_handler():
            nonlocal called
            called = True
        
        emitter.on('test_event', sync_handler)
        await emitter.emit('test_event')
        
        assert called
    
    @pytest.mark.asyncio
    async def test_emit_with_args(self, emitter):
        received_args = []
        
        async def handler(*args, **kwargs):
            received_args.extend(args)
        
        emitter.on('test_event', handler)
        await emitter.emit('test_event', 'arg1', 'arg2', key='value')
        
        assert 'arg1' in received_args
        assert 'arg2' in received_args

class TestRateLimiter:
    @pytest.fixture
    def rate_limiter(self):
        return RateLimiter(max_calls=3, time_window=1)
    
    @pytest.mark.asyncio
    async def test_under_limit(self, rate_limiter):
        for _ in range(3):
            result = await rate_limiter.acquire()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_over_limit_blocks(self, rate_limiter):
        for _ in range(3):
            await rate_limiter.acquire()
        
        import time
        start_time = time.time()
        await rate_limiter.acquire()
        end_time = time.time()
        
        assert (end_time - start_time) >= 0.9
    
    @pytest.mark.asyncio
    async def test_calls_expire(self, rate_limiter):
        await rate_limiter.acquire()
        
        await asyncio.sleep(1.1)
        
        for _ in range(3):
            result = await rate_limiter.acquire()
            assert result is True