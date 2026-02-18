import json
from redis.asyncio import Redis
from typing import Callable, Any
from src.config.settings import settings

class CacheService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = settings.CACHE_DEFAULT_TTL

    async def get_or_set(self, key: str, data_fetch_func: Callable, ttl_seconds: int = None) -> Any:
        cached_data = await self.redis.get(key)
        if cached_data:
            return json.loads(cached_data)
        
        data = await data_fetch_func()
        await self.redis.setex(key, ttl_seconds or self.default_ttl, json.dumps(data))
        return data