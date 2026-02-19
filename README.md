# Real-Time Analytics API

A highly resilient, fault-tolerant backend microservice designed for real-time metric ingestion and summarization. Built with Python, FastAPI, and Redis, and fully containerized using Docker. 

This project demonstrates advanced distributed system patterns, focusing on API protection, performance optimization, and graceful degradation during upstream failures.



---

## Technology Stack
* **Framework:** FastAPI (Python 3.11)
* **Datastore / Cache:** Redis 7-alpine
* **Orchestration:** Docker & Docker Compose
* **Testing:** Pytest & FastAPI TestClient

---

## Core Resilience Patterns

This service implements three critical patterns to ensure high availability:

1. **Redis-Backed Rate Limiting (Sliding Window):** Protects the `POST /api/metrics` endpoint from abuse. Uses Redis pipelines to execute atomic `INCR` and `EXPIRE` commands, preventing race conditions under high concurrent load. Returns `429 Too Many Requests` with a standardized `Retry-After` header.
2. **Read-Through Caching:** Optimizes the `GET /api/metrics/summary` endpoint. Heavy aggregations are computed once and cached in Redis with a configurable Time-To-Live (TTL), reducing computational overhead and ensuring rapid response times for dashboards.
3. **Circuit Breaker Pattern:** Protects the system from cascading failures when integrating with simulated, unreliable external data sources. Managed via an asynchronous state machine (`Closed`, `Open`, `Half-Open`) utilizing `asyncio.Lock()` to ensure thread-safe state transitions during concurrent traffic spikes.



---

## Setup and Installation

### Prerequisites
* Docker and Docker Compose installed on your machine.
* Git.

### 1. Clone the Repository
```bash
git clone [https://github.com/sayyaddsameer/analytics-api.git](https://github.com/sayyaddsameer/analytics-api.git)
cd analytics-api
```

### 2. Configure Environment

Copy the example environment file.  
The default variables are pre-configured to work seamlessly with Docker Compose.

```bash
cp .env.example .env
```

### 3. Build and Run via Docker Compose

Spin up the application and Redis containers in detached mode.  
The `docker-compose.yml` includes strict health checks to ensure Redis is fully operational before the API starts.

```bash
docker-compose up --build -d
```

The API will now be running at: `http://localhost:8000`

## API Documentation

FastAPI provides an interactive **OpenAPI (Swagger) UI** out of the box.

Once the container is running, navigate to:
`http://localhost:8000/docs`

### 1. Health Check

**Method:** `GET /health`

**Description:**  
Verifies that the API is running and successfully communicating with Redis.

### Response (200 OK)

```json
{
  "status": "ok",
  "redis": "healthy"
}
```

### 2. Ingest Metric

**Method:** `POST /api/metrics`  

**Rate Limit:**  
5 requests per 60 seconds  
(Configurable via `.env`)

---

### Request Body

```json
{
  "timestamp": "2026-02-18T12:00:00Z",
  "value": 85.5,
  "type": "cpu_usage"
}
```

### Responses

- **201 Created**  
  Metric stored successfully.

- **429 Too Many Requests**  
  Client exceeded the configured rate limit.

---

### 3. Get Metric Summary

**Method:** `GET /api/metrics/summary`

**Description:**  
Retrieves aggregated metrics.  
Uses **Redis caching** to optimize repeated identical queries within the configured TTL window.

---

### Query Parameters

- `type` (string, required)  
  Example: `cpu_usage`

- `period` (string, required)  
  Example: `daily`

---

### Response (200 OK)

```json
{
  "type": "cpu_usage",
  "period": "daily",
  "average_value": 85.5,
  "count": 1,
  "external_data": {
    "status": "success",
    "external_metric_context": 342
  }
}
```

> **Note:**  
> If the external service fails and the Circuit Breaker opens,  
> `external_data.status` will gracefully degrade to `"fallback"`.

---

## Automated Testing

This project includes a robust, asynchronous **integration and unit test suite** that validates:

- API endpoints  
- Redis caching behavior  
- Rate limiter logic  
- Circuit breaker state transitions  

The tests use **dynamic IP resolution** to avoid hardcoded network flakiness.

---

## Running Tests Locally

Ensure you have **Python 3.11+** installed.

### Activate a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

Ensure the Redis Docker container is running:

```bash
docker-compose up -d redis
```

### Execute the Test Suite

```bash
pytest -v
```

---

For a deeper dive into the engineering decisions, concurrency handling, and system trade-offs, please review the `ARCHITECTURE.md` file.
