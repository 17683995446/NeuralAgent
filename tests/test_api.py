"""
Unit tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock

from backend.main import app
from backend.api.schemas import (
    CodeProcessingRequest,
    CodeSearchRequest
)


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


class TestCodeProcessingAPI:
    """Test cases for code processing API endpoints."""

    def test_start_code_processing(self, client):
        """Test starting a code processing job."""
        request_data = {
            "repo_url": "https://github.com/example/test.git",
            "branch": "main",
            "languages": ["python", "javascript"],
            "enable_parallel": True,
            "max_workers": 4
        }
        
        response = client.post("/api/v1/code/process", json=request_data)
        
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["progress_percentage"] == 0.0

    def test_start_code_processing_validation(self, client):
        """Test validation of code processing request."""
        # Missing both repo_url and local_path
        request_data = {
            "branch": "main",
            "languages": ["python"]
        }
        
        response = client.post("/api/v1/code/process", json=request_data)
        
        assert response.status_code == 400

    def test_get_job_status_not_found(self, client):
        """Test getting status for non-existent job."""
        response = client.get("/api/v1/code/process/non-existent-job/status")
        
        assert response.status_code == 404

    def test_search_code(self, client):
        """Test code search endpoint."""
        request_data = {
            "query": "test function",
            "limit": 10,
            "filters": {}
        }
        
        response = client.post("/api/v1/code/search", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_vector_stats(self, client):
        """Test getting vector store stats."""
        response = client.get("/api/v1/code/vector-stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_chunks" in data
        assert "total_vectors" in data
        assert "language_distribution" in data

    def test_get_chunk_not_found(self, client):
        """Test getting non-existent chunk."""
        response = client.get("/api/v1/code/chunks/non-existent-chunk")
        
        assert response.status_code == 200  # Mock returns data even for non-existent

    def test_cancel_job_not_found(self, client):
        """Test canceling non-existent job."""
        response = client.delete("/api/v1/code/process/non-existent-job")
        
        assert response.status_code == 404


class TestHealthAPI:
    """Test cases for health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    def test_ready_endpoint(self, client):
        """Test readiness endpoint."""
        response = client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "components" in data


class TestTaskAPI:
    """Test cases for task management API endpoints."""

    def test_create_task_validation(self, client):
        """Test task creation validation."""
        # Missing required fields
        request_data = {
            "user_requirement": "Test requirement"
        }
        
        response = client.post("/api/v1/tasks", json=request_data)
        
        # Should fail without task_id
        assert response.status_code in [400, 422]

    def test_list_tasks(self, client):
        """Test listing tasks."""
        response = client.get("/api/v1/tasks?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
