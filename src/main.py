from fastapi import FastAPI, HTTPException, Request, Depends, Response
from fastapi.responses import JSONResponse
from typing import List
from redis.asyncio import Redis

from src.models import Metric, SummaryResponse
from src.config.settings import settings
from src.services.rate_limit_service import RateLimiter
from src.services.cache_service import CacheService
from src.services.circuit_breaker_service import CircuitBreaker, CircuitBreakerOpenError
from src.services.external_data_simulator import fetch_risky_external_data

app = FastAPI(title="Real-time Analytics API")

# In-memory database
metrics_db: List[Metric] = []

# Service instances
redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
rate_limiter = RateLimiter(redis_client)
cache_service = CacheService(redis_client)
circuit_breaker = CircuitBreaker()

@app.on_event("shutdown")
async def shutdown_event():
    await redis_client.close()

@app.get("/health")
async def health_check():
    try:
        await redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    return {"status": "ok", "redis": redis_status}

async def rate_limit_dependency(request: Request):
    # 1. Attempt to resolve via proxy headers (standard for Docker environments)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    # 2. Fall back to the direct client connection
    elif request.client and getattr(request.client, "host", None):
        client_ip = request.client.host
    # 3. Reject securely if no IP can be determined
    else:
        raise HTTPException(status_code=400, detail="Unable to determine client IP for rate limiting")

    allowed, retry_after = await rate_limiter.check_rate_limit(client_ip)
    if not allowed:
        headers = {"Retry-After": str(retry_after)}
        raise HTTPException(status_code=429, detail="Too Many Requests", headers=headers)
    return True

@app.post("/api/metrics", status_code=201)
async def create_metric(metric: Metric, allowed: bool = Depends(rate_limit_dependency)):
    metrics_db.append(metric)
    return {"message": "Metric received successfully"}

@app.get("/api/metrics/summary", response_model=SummaryResponse)
async def get_summary(type: str, period: str):
    cache_key = f"summary:{type}:{period}"

    async def compute_summary():
        # Filter metrics
        filtered = [m for m in metrics_db if m.type == type]
        count = len(filtered)
        avg = sum(m.value for m in filtered) / count if count > 0 else 0.0

        # Try to get external context via Circuit Breaker
        external_data = None
        try:
            external_data = await circuit_breaker.call(fetch_risky_external_data)
        except CircuitBreakerOpenError:
            external_data = {"status": "fallback", "message": "External service temporarily unavailable"}
        except Exception:
            external_data = {"status": "error", "message": "External service failed"}

        return {
            "type": type,
            "period": period,
            "average_value": round(avg, 2),
            "count": count,
            "external_data": external_data
        }

    data = await cache_service.get_or_set(cache_key, compute_summary)
    return data