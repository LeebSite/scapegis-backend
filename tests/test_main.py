"""
Test untuk main application
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "environment" in data
    assert "ScapeGIS Backend" in data["message"]


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "database" in data


def test_api_v1_test():
    """Test API v1 test endpoint"""
    response = client.get("/api/v1/test")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "API v1 is working!"


def test_docs_endpoint():
    """Test that docs endpoint is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_endpoint():
    """Test OpenAPI schema endpoint"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
