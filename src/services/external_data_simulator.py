import random
import asyncio
from src.config.settings import settings

async def fetch_risky_external_data() -> dict:
    # Simulate network latency
    await asyncio.sleep(0.05)
    
    if random.random() < settings.EXTERNAL_SERVICE_FAILURE_RATE:
        raise RuntimeError("Simulated external service failure due to high load.")
    
    return {"status": "success", "external_metric_context": random.randint(100, 500)}