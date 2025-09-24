import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from pump_self_melon.utils import get_user_info, get_room_info

class TestUtils:
    @pytest.mark.asyncio
    async def test_get_user_info_success(self):
        mock_response_data = {
            "address": "0x123",
            "username": "testuser",
            "created": "2024-01-01"
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_context_manager = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_context_manager
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            mock_context_manager.get.return_value.__aenter__.return_value = mock_response
            
            result = await get_user_info("test_token")
            
            assert result == {**mock_response_data, **mock_response_data}
    
    @pytest.mark.asyncio
    async def test_get_user_info_profile_failure(self):
        with patch('aiohttp.ClientSession') as mock_session:
            mock_context_manager = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_context_manager
            
            mock_response = AsyncMock()
            mock_response.status = 401
            
            mock_context_manager.get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to get profile: 401"):
                await get_user_info("invalid_token")
    
    @pytest.mark.asyncio
    async def test_get_user_info_no_address(self):
        mock_response_data = {"username": "testuser"}
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_context_manager = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_context_manager
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            mock_context_manager.get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(Exception, match="No address returned from profile endpoint"):
                await get_user_info("test_token")
    
    @pytest.mark.asyncio
    async def test_get_room_info_success(self):
        mock_room_data = {
            "mint": "room_123",
            "name": "Test Coin",
            "symbol": "TEST"
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_context_manager = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_context_manager
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_room_data
            
            mock_context_manager.get.return_value.__aenter__.return_value = mock_response
            
            result = await get_room_info("room_123")
            
            assert result == mock_room_data
    
    @pytest.mark.asyncio
    async def test_get_room_info_not_found(self):
        with patch('aiohttp.ClientSession') as mock_session:
            mock_context_manager = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_context_manager
            
            mock_response = AsyncMock()
            mock_response.status = 404
            
            mock_context_manager.get.return_value.__aenter__.return_value = mock_response
            
            result = await get_room_info("nonexistent_room")
            
            assert result is None