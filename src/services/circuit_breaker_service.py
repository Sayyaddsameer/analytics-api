import time
import asyncio
from enum import Enum
from src.config.settings import settings

class CircuitState(Enum):
    CLOSED = 1
    OPEN = 2
    HALF_OPEN = 3

class CircuitBreakerOpenError(Exception):
    pass

class CircuitBreaker:
    def __init__(self):
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._threshold = settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        self._reset_timeout = settings.CIRCUIT_BREAKER_RESET_TIMEOUT
        self._lock = asyncio.Lock()

    async def call(self, func, *args, **kwargs):
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() > self._last_failure_time + self._reset_timeout:
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerOpenError("Circuit is open.")
            
        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                self._failure_count = 0
                self._state = CircuitState.CLOSED
            return result
        except Exception as e:
            if isinstance(e, CircuitBreakerOpenError):
                raise e
            async with self._lock:
                self._failure_count += 1
                self._last_failure_time = time.time()
                if self._state == CircuitState.HALF_OPEN or self._failure_count >= self._threshold:
                    self._state = CircuitState.OPEN
            raise e