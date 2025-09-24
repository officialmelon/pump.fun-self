import aiohttp
import asyncio
from typing import Dict, Any, Optional

async def get_user_info(user_token: str) -> Dict[str, Any]:
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site"
    }
    
    cookies = {"auth_token": user_token}
    
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get("https://frontend-api-v3.pump.fun/auth/my-profile", headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Failed to get profile: {response.status}")
            profile_data = await response.json()
        
        address = profile_data.get("address")
        if not address:
            raise Exception("No address returned from profile endpoint")
        
        async with session.get(f"https://frontend-api-v3.pump.fun/users/{address}", headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Failed to get user info: {response.status}")
            user_data = await response.json()
    
    return {**profile_data, **user_data}

async def get_room_info(room_id: str) -> Optional[Dict[str, Any]]:
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://frontend-api-v3.pump.fun/coins/{room_id}", headers=headers) as response:
            if response.status == 200:
                return await response.json()
    return None

__all__ = ['get_user_info', 'get_room_info']