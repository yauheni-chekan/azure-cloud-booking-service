"""Unit tests for FastAPI application."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestFastAPIApp:
    """Test suite for FastAPI application."""

    @pytest.fixture
    def mock_service_bus_receiver(self):
        """Mock the service bus receiver service.

        Yields:
            AsyncMock: Mocked service bus receiver
        """
        with patch("app.main.service_bus_receiver") as mock:
            mock.start = AsyncMock()
            mock.stop = AsyncMock()
            yield mock

    @pytest.fixture
    def client(self, mock_service_bus_receiver):  # noqa: ARG002
        """Create a test client.

        Args:
            mock_service_bus_receiver: Mocked service bus receiver fixture

        Returns:
            TestClient: FastAPI test client
        """
        from app.main import app

        with TestClient(app) as c:
            yield c

    def test_root_redirects_to_docs(self, client):
        """Test that root endpoint redirects to /docs."""
        response = client.get("/", follow_redirects=False)

        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/docs"

    def test_docs_endpoint(self, client):
        """Test that /docs endpoint is accessible."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert b"Swagger UI" in response.content or b"swagger" in response.content.lower()

    def test_openapi_endpoint(self, client):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        from app.config import settings

        assert data["info"]["title"] == settings.app_name

    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_lifespan_startup(self, mock_service_bus_receiver):
        """Test application startup lifecycle."""
        from app.main import app

        with TestClient(app):
            pass

        mock_service_bus_receiver.start.assert_called_once()

    def test_lifespan_shutdown(self, mock_service_bus_receiver):
        """Test application shutdown lifecycle."""
        from app.main import app

        with TestClient(app):
            pass

        # Service bus receiver should be stopped
        mock_service_bus_receiver.stop.assert_called_once()

    def test_lifespan_startup_failure(self):
        """Test handling of service bus startup failure."""
        with patch("app.main.service_bus_receiver") as mock_receiver:
            mock_receiver.start = AsyncMock(side_effect=Exception("Connection failed"))
            mock_receiver.stop = AsyncMock()

            from app.main import app

            # Application should raise exception on startup failure
            with pytest.raises(Exception, match="Connection failed"), TestClient(app):
                pass

    def test_lifespan_shutdown_error_handling(self, mock_service_bus_receiver):
        """Test that shutdown errors are handled gracefully."""
        mock_service_bus_receiver.stop = AsyncMock(side_effect=Exception("Stop failed"))

        from app.main import app

        # Should not raise exception even if stop fails
        with TestClient(app):
            pass

        # Stop should have been called despite the error
        mock_service_bus_receiver.stop.assert_called_once()

    def test_api_v1_router_included(self, client):
        """Test that API v1 router is properly included."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200

    def test_cors_headers_not_present_by_default(self, client):
        """Test that CORS is not enabled by default."""
        response = client.get("/api/v1/health")

        assert "access-control-allow-origin" not in response.headers

    def test_app_metadata(self, client):
        """Test application metadata in OpenAPI schema."""
        response = client.get("/openapi.json")
        data = response.json()

        from app.config import settings

        assert data["info"]["title"] == settings.app_name
        assert data["info"]["version"] == settings.app_version
        assert "Pet grooming booking service" in data["info"]["description"]

    def test_redoc_endpoint(self, client):
        """Test that ReDoc endpoint is accessible."""
        response = client.get("/redoc")

        assert response.status_code == 200
