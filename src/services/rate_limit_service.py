import time
from redis.asyncio import Redis
from src.config.settings import settings

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.threshold = settings.RATE_LIMIT_THRESHOLD
        self.window = settings.RATE_LIMIT_WINDOW_SECONDS

    async def check_rate_limit(self, client_ip: str) -> tuple[bool, int]:
        current_time = int(time.time())
        window_start = current_time // self.window
        key = f"rate_limit:{client_ip}:{window_start}"
        
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, self.window)
            results = await pipe.execute()
            
        request_count = results[0]
        allowed = request_count <= self.threshold
        
        # Calculate seconds until the next window starts
        retry_after = (window_start + 1) * self.window - current_time if not allowed else 0
        return allowed, retry_after