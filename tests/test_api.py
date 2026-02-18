import pytest
import socket
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_metric_ingestion(client):
    current_time = datetime.now(timezone.utc).isoformat()
    
    payload = {
        "timestamp": current_time,
        "value": 85.5,
        "type": "cpu_usage"
    }
    
    # Dynamically resolve local IP to simulate proxy routing without hardcoded strings
    local_ip = socket.gethostbyname(socket.gethostname())
    headers = {"X-Forwarded-For": local_ip}
    
    response = client.post("/api/metrics", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["message"] == "Metric received successfully"