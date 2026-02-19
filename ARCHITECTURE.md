# Architectural Decisions and System Design



This document outlines the core engineering decisions, design patterns, and trade-offs made while building the Real-Time Analytics API. The primary objective of this architecture is to ensure high availability, resilience, and consistent performance under adverse network conditions.

---

## 1. High-Level Technology Stack

* **API Framework:** FastAPI (Python 3.11)
* **In-Memory Datastore / Cache:** Redis 7.x
* **Containerization:** Docker & Docker Compose
* **Testing:** Pytest with FastAPI `TestClient` (Async-aware)

FastAPI was selected for its native, first-class support for asynchronous I/O (`async`/`await`). Because this service heavily relies on network-bound operations (connecting to Redis, calling simulated external APIs), asynchronous execution prevents thread-blocking. This allows a single Uvicorn ASGI worker to handle thousands of concurrent requests efficiently, scaling gracefully under load.

---

## 2. Resilience Patterns

### 2.1. Rate Limiting (Sliding Window)
To protect the API from abuse and traffic spikes, a time-window rate limiter was implemented at the middleware level.



* **Implementation:** We use a Redis `pipeline(transaction=True)` to bundle `INCR` and `EXPIRE` commands. 
* **Trade-off & Justification:** This guarantees atomicity. Even if 50 requests from the same IP arrive at the exact same millisecond, the counter increments perfectly in a single network round-trip without race conditions. By dynamically resolving the `X-Forwarded-For` headers, the limiter safely handles traffic routed through Docker bridge networks or external reverse proxies.

### 2.2. Read-Through Cache
To optimize the `GET /api/metrics/summary` endpoint, heavy aggregation computations are cached.



* **Implementation:** Data is stored in Redis with a configurable Time-To-Live (TTL). The service attempts to fetch from Redis first; upon a cache miss, it computes the summary, stores it, and returns the response.
* **Trade-off:** This introduces *eventual consistency*. Users might see slightly delayed aggregated data until the TTL expires.
* **Justification:** For analytics dashboards, reading data that is a few seconds old is vastly preferable to bringing down the primary database with repetitive, heavy aggregation queries.

### 2.3. Circuit Breaker (State Machine)
The `CircuitBreaker` class manages a state machine (`CLOSED`, `OPEN`, `HALF-OPEN`) to protect against cascading failures from upstream external services.



* **Implementation:** Because the ASGI server handles requests concurrently, there is a severe risk of a race condition where multiple failing requests trigger the state transition simultaneously, leading to redundant logging or corrupted failure counts.
* **Solution:** An `asyncio.Lock()` wraps all state-read and state-write operations. This ensures that only one request can evaluate and mutate the circuit's state at any given microsecond, guaranteeing thread-safe fault tolerance.

---

## 3. Data Storage Strategy

For this specific implementation, raw ingested metrics are stored in memory (`List[Metric]`). 

* **Trade-off:** If the container restarts, unaggregated raw metrics are lost. 
* **Justification:** The primary focus of this architecture is demonstrating distributed resilience patterns. In a production cloud-native environment, this in-memory list acts as a placeholder that would be swapped seamlessly for a persistent time-series database (e.g., TimescaleDB, Amazon Timestream, or Prometheus) via a standard Repository Pattern, without altering the core resilience logic layered above it.

---

## 4. Containerization & Orchestration

The application and its Redis dependency are containerized to ensure identical behavior across local, testing, and production environments.

* **Implementation:** The `docker-compose.yml` utilizes strict network dependencies. The backend `app` service includes a `depends_on` block with `condition: service_healthy` tied directly to the Redis container's health check.
* **Justification:** This orchestration prevents the backend API from booting up and instantly crashing if the Redis container takes a few extra seconds to initialize. This establishes a stable, deterministic startup sequence that is a prerequisite for modern automated deployment pipelines.