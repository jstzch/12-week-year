"""Unit tests for 12-Week Year API"""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_root_message(client):
    """Test root endpoint returns correct message"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello from 12-Week Year API!"
    assert data["status"] == "ok"


def test_hello_endpoint(client):
    """Test hello endpoint returns correct message"""
    response = client.get("/api/hello")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello, World!"
