"""
Unit tests for health check endpoint.

Validates: Requirement 10.7 - Health check endpoints for monitoring service status
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create test client for API testing"""
    return TestClient(app)


def test_health_endpoint_returns_200(client):
    """
    Test that /health endpoint returns 200 status code.
    
    Validates: Requirement 10.7
    """
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_returns_healthy_status(client):
    """
    Test that /health endpoint returns correct status in response body.
    
    Validates: Requirement 10.7
    """
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_health_endpoint_returns_json(client):
    """
    Test that /health endpoint returns JSON content type.
    
    Validates: Requirement 10.7
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
