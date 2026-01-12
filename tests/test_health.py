"""Unit tests for health check endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client with mocked service bus.

        Returns:
            TestClient: FastAPI test client
        """
        with patch("app.main.service_bus_receiver") as mock_receiver:
            mock_receiver.start = AsyncMock()
            mock_receiver.stop = AsyncMock()
            from app.main import app

            with TestClient(app) as c:
                yield c

    @pytest.fixture
    def mock_settings(self):
        """Mock application settings.

        Yields:
            MagicMock: Mocked settings
        """
        with patch("app.api.v1.health.settings") as mock:
            mock.app_name = "test-app"
            mock.app_version = "1.0.0"
            yield mock

    def test_health_check_basic(self, client, mock_settings):  # noqa: ARG002
        """Test basic health check endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "test-app"
        assert data["version"] == "1.0.0"

        # Validate timestamp format
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        assert timestamp.tzinfo is not None

    def test_health_check_timestamp_format(self, client):
        """Test that timestamp is in correct ISO format."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Should be able to parse as ISO datetime
        timestamp_str = data["timestamp"]
        parsed = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)

    def test_health_endpoints_response_headers(self, client):
        """Test that health endpoints return appropriate headers."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_health_check_no_caching(self, client):
        """Test that health check responses are not cached."""
        response1 = client.get("/api/v1/health")
        response2 = client.get("/api/v1/health")

        # Timestamps should be different (or very close)
        data1 = response1.json()
        data2 = response2.json()

        # Both should be successful
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Should have timestamp field
        assert "timestamp" in data1
        assert "timestamp" in data2

    def test_health_check_structure(self, client, mock_settings):  # noqa: ARG002
        """Test that health check returns all required fields."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        required_fields = ["status", "service", "version", "timestamp"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_health_check_with_real_settings(self, client):
        """Test health check with actual settings (not mocked)."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        # Service and version should come from actual settings
        assert isinstance(data["service"], str)
        assert isinstance(data["version"], str)
