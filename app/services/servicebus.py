"""Azure Service Bus message receiver service."""

import asyncio
import contextlib
import logging
from typing import Any

from azure.servicebus import ServiceBusReceivedMessage
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver

from app.config import settings

logger = logging.getLogger(__name__)


class ServiceBusReceiverService:
    """Service for receiving messages from Azure Service Bus Queue."""

    def __init__(self) -> None:
        """Initialize the Service Bus receiver service."""
        self.client: ServiceBusClient | None = None
        self.receiver: ServiceBusReceiver | None = None
        self._running = False
        self._task: asyncio.Task[Any] | None = None

    async def start(self) -> None:
        """Start the Service Bus receiver background task."""
        if self._running:
            logger.warning("Service Bus receiver is already running")
            return

        logger.info("Starting Service Bus receiver service...")
        self._running = True
        self.client = ServiceBusClient.from_connection_string(
            conn_str=settings.service_bus_connection_string,
        )

        self._task = asyncio.create_task(self._receive_messages())
        logger.info("Service Bus receiver service started successfully")

    async def stop(self) -> None:
        """Stop the Service Bus receiver and cleanup resources."""
        logger.info("Stopping Service Bus receiver service...")
        self._running = False

        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except TimeoutError:
                logger.warning("Timeout waiting for receiver task to complete")
                self._task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._task

        if self.client:
            await self.client.close()
            self.client = None

        logger.info("Service Bus receiver service stopped")

    async def _receive_messages(self) -> None:
        """Background task to continuously receive and process messages."""
        logger.info("Starting to receive messages from queue: %s", settings.service_bus_queue_name)

        try:
            while self._running:
                try:
                    # Get a receiver with max_wait_time to prevent blocking indefinitely
                    async with self.client.get_queue_receiver(
                        queue_name=settings.service_bus_queue_name,
                        max_wait_time=5,
                    ) as receiver:
                        # Iterate over messages
                        async for msg in receiver:
                            if not self._running:
                                break

                            await self._process_message(msg)
                            await receiver.complete_message(msg)

                except Exception:
                    logger.exception("Error receiving messages")
                    await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info("Message receiving task cancelled")
        except Exception:
            logger.exception("Fatal error in message receiver")
        finally:
            logger.info("Message receiving task completed")

    async def _process_message(self, message: ServiceBusReceivedMessage) -> None:
        """Process a received message.

        For now, this just prints the message. In the future, this can be
        extended to process events and create bookings, etc.

        :param message: The received Service Bus message
        """
        try:
            message_body = str(message)
            logger.info("📨 Service Bus Event Received: %s", message_body)
            if message.application_properties:
                logger.info("Message properties: %s", message.application_properties)

        except Exception:
            logger.exception("Error processing message")
            raise


service_bus_receiver = ServiceBusReceiverService()
