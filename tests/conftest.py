"""Pytest configuration and shared fixtures."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from azure.servicebus import ServiceBusReceivedMessage
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver

# Ensure required settings exist before importing app modules.
# `app.config` creates `settings = Settings()` at import time.
os.environ.setdefault(
    "SERVICE_BUS_CONNECTION_STRING",
    "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test123",
)
os.environ.setdefault("SERVICE_BUS_QUEUE_NAME", "test-queue")
os.environ.setdefault(
    "DB_CONNECTION_STRING",
    "Driver={ODBC Driver 18 for SQL Server};Server=tcp:test.database.windows.net,1433;Database=test;",  # noqa: E501
)


@pytest.fixture
def mock_service_bus_client() -> MagicMock:
    """Create a mock ServiceBusClient.

    Returns:
        MagicMock: Mocked ServiceBusClient with async context manager support
    """
    mock_client = MagicMock(spec=ServiceBusClient)
    mock_client.close = AsyncMock()
    return mock_client


@pytest.fixture
def mock_service_bus_receiver() -> AsyncMock:
    """Create a mock ServiceBusReceiver.

    Returns:
        AsyncMock: Mocked ServiceBusReceiver with async iteration support
    """
    mock_receiver = AsyncMock(spec=ServiceBusReceiver)
    mock_receiver.__aenter__ = AsyncMock(return_value=mock_receiver)
    mock_receiver.__aexit__ = AsyncMock(return_value=None)
    # Make async iteration configurable per-test via `mock_receiver.__aiter__.return_value = ...`
    mock_receiver.__aiter__ = MagicMock()
    mock_receiver.complete_message = AsyncMock()
    return mock_receiver


@pytest.fixture
def mock_service_bus_message() -> ServiceBusReceivedMessage:
    """Create a mock ServiceBusReceivedMessage.

    Returns:
        MagicMock: Mocked ServiceBusReceivedMessage
    """
    mock_message = MagicMock(spec=ServiceBusReceivedMessage)
    mock_message.application_properties = {"event_type": "booking_created", "source": "api"}
    mock_message.__str__ = MagicMock(return_value='{"event": "booking_created", "id": "123"}')
    return mock_message


@pytest.fixture
async def mock_messages(
    mock_service_bus_message: ServiceBusReceivedMessage,  # noqa: ARG001
) -> list[ServiceBusReceivedMessage]:
    """Create a list of mock messages.

    Args:
        mock_service_bus_message: Fixture providing a mock message

    Returns:
        list[ServiceBusReceivedMessage]: List of mock messages
    """
    messages = []
    for i in range(3):
        msg = MagicMock(spec=ServiceBusReceivedMessage)
        msg.application_properties = {"event_type": f"event_{i}", "source": "test"}
        msg.__str__ = MagicMock(return_value=f'{{"event": "test_{i}", "id": "{i}"}}')
        messages.append(msg)
    return messages


@pytest.fixture
def event_loop_policy():
    """Configure event loop policy for Windows compatibility."""
    if asyncio.get_event_loop_policy().__class__.__name__ == "WindowsProactorEventLoopPolicy":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
