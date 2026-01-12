"""Configuration management using Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service Bus Configuration
    service_bus_connection_string: str = Field(
        ..., description="Azure Service Bus connection string"
    )
    service_bus_queue_name: str = Field(
        ..., description="Azure Service Bus queue name to receive messages from"
    )

    service_bus_debug: bool = Field(default=False, description="Enable Service Bus debug logging")

    # Database Configuration
    db_connection_string: str = Field(..., description="Database connection string for Azure SQL")

    # Application Configuration
    app_name: str = Field(default="azure-cloud-booking-service", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")


settings = Settings()
