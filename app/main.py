"""FastAPI application for Azure Cloud Booking Service."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.v1 import router as api_v1_router
from app.config import settings
from app.services import service_bus_receiver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress verbose Azure SDK logs (only show warnings and errors)
logging.getLogger("azure").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan events.

    Handles startup and shutdown of the Service Bus receiver.
    """
    # Startup
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    logger.info("Debug mode: %s", settings.debug)

    try:
        await service_bus_receiver.start()
        logger.info("Service Bus receiver started successfully")
    except Exception:
        logger.exception("Failed to start Service Bus receiver")
        raise

    yield
    logger.info("Shutting down application...")

    try:
        await service_bus_receiver.stop()
        logger.info("Service Bus receiver stopped successfully")
    except Exception:
        logger.exception("Error stopping Service Bus receiver")

    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Pet grooming booking service with Azure Service Bus integration",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Include API v1 router
app.include_router(api_v1_router, prefix="/api/v1", tags=["v1"])


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
