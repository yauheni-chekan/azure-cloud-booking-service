"""Unit tests for configuration module."""

import importlib
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config import Settings


class TestSettings:
    """Test suite for Settings configuration."""

    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(
            os.environ,
            {
                "SERVICE_BUS_CONNECTION_STRING": "Endpoint=sb://test.servicebus.windows.net/",
                "SERVICE_BUS_QUEUE_NAME": "test-queue",
                "DB_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=test.database.windows.net;",  # noqa: E501
            },
            clear=True,
        ):
            settings = Settings()

            assert settings.app_name == "azure-cloud-booking-service"
            assert settings.app_version == "0.1.0"
            assert settings.debug is False
            assert settings.service_bus_queue_name == "test-queue"

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(
            os.environ,
            {
                "APP_NAME": "custom-app",
                "APP_VERSION": "1.2.3",
                "DEBUG": "true",
                "SERVICE_BUS_CONNECTION_STRING": "Endpoint=sb://custom.servicebus.windows.net/",
                "SERVICE_BUS_QUEUE_NAME": "custom-queue",
                "DB_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=custom.database.windows.net;",  # noqa: E501
            },
            clear=True,
        ):
            settings = Settings()

            assert settings.app_name == "custom-app"
            assert settings.app_version == "1.2.3"
            assert settings.debug is True
            assert settings.service_bus_queue_name == "custom-queue"
            assert "custom.servicebus.windows.net" in settings.service_bus_connection_string

    def test_missing_required_service_bus_connection_string(self):
        """Test that missing SERVICE_BUS_CONNECTION_STRING raises validation error."""
        with patch.dict(
            os.environ,
            {
                "SERVICE_BUS_QUEUE_NAME": "test-queue",
                "DB_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=test.database.windows.net;",  # noqa: E501
            },
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings(_env_file=None)

            assert "service_bus_connection_string" in str(exc_info.value)

    def test_missing_required_queue_name(self):
        """Test that missing SERVICE_BUS_QUEUE_NAME raises validation error."""
        with patch.dict(
            os.environ,
            {
                "SERVICE_BUS_CONNECTION_STRING": "Endpoint=sb://test.servicebus.windows.net/",
                "DB_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=test.database.windows.net;",  # noqa: E501
            },
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings(_env_file=None)

            assert "service_bus_queue_name" in str(exc_info.value)

    def test_missing_required_db_connection_string(self):
        """Test that missing DB_CONNECTION_STRING raises validation error."""
        with patch.dict(
            os.environ,
            {
                "SERVICE_BUS_CONNECTION_STRING": "Endpoint=sb://test.servicebus.windows.net/",
                "SERVICE_BUS_QUEUE_NAME": "test-queue",
            },
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings(_env_file=None)

            assert "db_connection_string" in str(exc_info.value)

    def test_debug_mode_boolean_parsing(self):
        """Test that DEBUG env var is properly parsed as boolean."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
        ]

        for env_value, expected in test_cases:
            with patch.dict(
                os.environ,
                {
                    "DEBUG": env_value,
                    "SERVICE_BUS_CONNECTION_STRING": "Endpoint=sb://test.servicebus.windows.net/",
                    "SERVICE_BUS_QUEUE_NAME": "test-queue",
                    "DB_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=test.database.windows.net;",  # noqa: E501
                },
                clear=True,
            ):
                settings = Settings()
                assert settings.debug == expected, f"Failed for DEBUG={env_value}"

    def test_settings_case_insensitive(self):
        """Test that settings are case-insensitive."""
        with patch.dict(
            os.environ,
            {
                "app_name": "lowercase-app",  # lowercase
                "SERVICE_BUS_CONNECTION_STRING": "Endpoint=sb://test.servicebus.windows.net/",
                "SERVICE_BUS_QUEUE_NAME": "test-queue",
                "DB_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=test.database.windows.net;",  # noqa: E501
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.app_name == "lowercase-app"

    def test_connection_string_validation(self):
        """Test that connection string is validated."""
        with patch.dict(
            os.environ,
            {
                "SERVICE_BUS_CONNECTION_STRING": "invalid-connection-string",
                "SERVICE_BUS_QUEUE_NAME": "test-queue",
                "DB_CONNECTION_STRING": "invalid-db-connection-string",
            },
            clear=True,
        ):
            # Should still create settings (validation happens at Azure SDK level)
            settings = Settings()
            assert settings.service_bus_connection_string == "invalid-connection-string"

    def test_settings_are_mutable_by_default(self):
        """Test that settings allow assignment by default."""
        with patch.dict(
            os.environ,
            {
                "SERVICE_BUS_CONNECTION_STRING": "Endpoint=sb://test.servicebus.windows.net/",
                "SERVICE_BUS_QUEUE_NAME": "test-queue",
                "DB_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=test.database.windows.net;",  # noqa: E501
            },
            clear=True,
        ):
            settings = Settings()

            settings.app_name = "new-name"
            assert settings.app_name == "new-name"

    def test_settings_singleton_behavior(self):
        """Test that module-level settings is created from environment at import time."""
        with patch.dict(
            os.environ,
            {
                "SERVICE_BUS_CONNECTION_STRING": "Endpoint=sb://test.servicebus.windows.net/",
                "SERVICE_BUS_QUEUE_NAME": "test-queue",
                "DB_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=test.database.windows.net;",  # noqa: E501
            },
            clear=True,
        ):
            import app.config as config_module

            importlib.reload(config_module)

            # Settings should be importable and accessible
            assert config_module.settings.app_name == "azure-cloud-booking-service"
            assert config_module.settings.service_bus_queue_name == "test-queue"
