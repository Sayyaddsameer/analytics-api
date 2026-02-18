import pytest
import asyncio
from src.services.circuit_breaker_service import CircuitBreaker, CircuitState, CircuitBreakerOpenError

async def failing_call():
    raise ValueError("Failed!")

async def successful_call():
    return "Success"

@pytest.mark.asyncio
async def test_circuit_breaker_state_transitions():
    cb = CircuitBreaker()
    cb._threshold = 2
    cb._reset_timeout = 1
    
    # Trigger failures to open circuit
    for _ in range(2):
        with pytest.raises(ValueError):
            await cb.call(failing_call)
            
    assert cb._state == CircuitState.OPEN
    
    # Verify fallback is raised immediately
    with pytest.raises(CircuitBreakerOpenError):
        await cb.call(successful_call)
        
    # Wait for reset timeout
    await asyncio.sleep(1.1)
    
    # Test half-open success
    result = await cb.call(successful_call)
    assert result == "Success"
    assert cb._state == CircuitState.CLOSED