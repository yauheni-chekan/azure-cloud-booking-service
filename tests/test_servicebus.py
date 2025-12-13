"""Unit tests for Service Bus receiver service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.servicebus import ServiceBusReceiverService


class TestServiceBusReceiverService:
    @pytest.fixture
    def service(self) -> ServiceBusReceiverService:
        return ServiceBusReceiverService()

    @pytest.fixture
    def mock_settings(self):
        # `app.services.servicebus` reads `settings.*` at runtime.
        with patch("app.services.servicebus.settings") as mock:
            mock.service_bus_connection_string = "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test123"
            mock.service_bus_queue_name = "test-queue"
            yield mock

    async def test_init(self, service: ServiceBusReceiverService) -> None:
        assert service.client is None
        assert service.receiver is None
        assert service._running is False
        assert service._task is None

    async def test_start_creates_client_and_task(
        self, service: ServiceBusReceiverService, mock_service_bus_client, mock_settings  # noqa: ARG002
    ) -> None:
        with (
            patch(
                "app.services.servicebus.ServiceBusClient.from_connection_string",
                return_value=mock_service_bus_client,
            ),
            patch.object(service, "_receive_messages", new=AsyncMock(return_value=None)) as recv,
        ):
            await service.start()

            assert service._running is True
            assert service.client is mock_service_bus_client
            assert service._task is not None

            # Background task runs the receive loop coroutine
            await service._task
            recv.assert_awaited()

    async def test_start_is_idempotent(
        self, service: ServiceBusReceiverService, mock_settings  # noqa: ARG002
    ) -> None:
        service._running = True
        service._task = MagicMock()

        with patch("app.services.servicebus.ServiceBusClient.from_connection_string") as from_conn:
            await service.start()
            from_conn.assert_not_called()

    async def test_stop_closes_client(
        self, service: ServiceBusReceiverService, mock_service_bus_client
    ) -> None:
        service._running = True
        service.client = mock_service_bus_client
        service._task = asyncio.create_task(asyncio.sleep(0))
        await service._task

        await service.stop()

        assert service._running is False
        assert service.client is None
        mock_service_bus_client.close.assert_awaited_once()

    async def test_stop_cancels_task_on_timeout(
        self, service: ServiceBusReceiverService, mock_service_bus_client
    ) -> None:
        service._running = True
        service.client = mock_service_bus_client
        blocker = asyncio.Event()
        service._task = asyncio.create_task(blocker.wait())

        # Avoid waiting 10 seconds in tests: force immediate timeout.
        with patch(
            "app.services.servicebus.asyncio.wait_for",
            new=AsyncMock(side_effect=asyncio.TimeoutError),
        ):
            await service.stop()

        assert service._task.cancelled()
        assert service.client is None
        mock_service_bus_client.close.assert_awaited_once()

    async def test_receive_messages_processes_and_completes(
        self,
        service: ServiceBusReceiverService,
        mock_service_bus_client,
        mock_service_bus_receiver,
        mock_messages,
        mock_settings,  # noqa: ARG002
    ) -> None:
        # Stop after yielding the batch to avoid an infinite receive loop.
        async def message_stream():
            for msg in mock_messages:
                yield msg
            service._running = False

        mock_service_bus_receiver.__aiter__.return_value = message_stream()
        mock_service_bus_client.get_queue_receiver = MagicMock(
            return_value=mock_service_bus_receiver
        )
        service.client = mock_service_bus_client
        service._running = True

        with patch("app.services.servicebus.asyncio.sleep", new=AsyncMock(return_value=None)):
            service._process_message = AsyncMock(return_value=None)  # type: ignore[method-assign]
            await service._receive_messages()

        assert service._process_message.await_count == len(mock_messages)
        assert mock_service_bus_receiver.complete_message.await_count == len(mock_messages)

    async def test_receive_messages_sleeps_on_error_and_retries(
        self, service: ServiceBusReceiverService, mock_service_bus_client, mock_settings  # noqa: ARG002
    ) -> None:
        service.client = mock_service_bus_client
        service._running = True
        mock_service_bus_client.get_queue_receiver = MagicMock(side_effect=Exception("boom"))

        async def sleep_and_stop(_seconds: float):
            service._running = False

        with patch(
            "app.services.servicebus.asyncio.sleep", new=AsyncMock(side_effect=sleep_and_stop)
        ) as slp:
            await service._receive_messages()

        slp.assert_awaited()
        mock_service_bus_client.get_queue_receiver.assert_called()

    async def test_receive_messages_cancellation_is_swallowed(
        self,
        service: ServiceBusReceiverService,
        mock_service_bus_client,
        mock_service_bus_receiver,
        mock_settings,  # noqa: ARG002
    ) -> None:
        # Block inside receiver enter so we can cancel the task.
        blocker = asyncio.Event()

        async def enter_block():
            await blocker.wait()

        mock_service_bus_receiver.__aenter__ = AsyncMock(side_effect=enter_block)
        mock_service_bus_client.get_queue_receiver = MagicMock(
            return_value=mock_service_bus_receiver
        )
        service.client = mock_service_bus_client
        service._running = True

        task = asyncio.create_task(service._receive_messages())
        await asyncio.sleep(0)  # let it start
        task.cancel()
        await task  # should not raise (CancelledError is handled inside)

        assert task.done()
        assert not task.cancelled()
