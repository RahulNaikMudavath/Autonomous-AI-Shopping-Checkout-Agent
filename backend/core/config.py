"""
AgentCart Core Configuration Module
Manages application settings using Pydantic Settings v2.
Loads environment variables from .env and supports runtime updates.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class AppSettings(BaseSettings):
    """
    Centralized configuration for AgentCart.
    Organized into logical subsystems for modularity and maintainability.
    """
    # Application Metadata
    app_name: str = Field(default="AgentCart API", description="Application display name")
    app_version: str = Field(default="1.0.0", description="Semantic version of the service")
    environment: str = Field(default="development", description="Runtime environment: development | staging | production | test")
    debug: bool = Field(default=False, description="Enable debug mode and verbose logging")
    api_v1_prefix: str = Field(default="/api/v1", description="URL prefix for API v1 routes")
    
    # Server & Network
    host: str = Field(default="0.0.0.0", description="Host interface to bind")
    port: int = Field(default=8000, description="Port number to listen on")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "*"],
        description="Allowed CORS origins"
    )

    # Database Configuration (PostgreSQL)
    database_url: str = Field(
        default="postgresql://agentcart:securepass@localhost:5432/agentcart_db",
        description="PostgreSQL connection string. Falls back to SQLite if unreachable in dev."
    )
    db_pool_size: int = Field(default=10, description="Database connection pool size")
    db_max_overflow: int = Field(default=20, description="Database connection pool max overflow")
    db_timeout_seconds: int = Field(default=5, description="Database connection timeout in seconds")

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for ephemeral state and caching"
    )
    redis_ttl_seconds: int = Field(default=3600, description="Default TTL for cached session state")
    redis_timeout_seconds: int = Field(default=2, description="Redis connection timeout in seconds")

    # LLM & AI Provider Settings (Reserved for Phase 2+)
    openai_api_key: Optional[str] = Field(default="", description="OpenAI API key")
    gemini_api_key: Optional[str] = Field(default="", description="Google Gemini API key")
    anthropic_api_key: Optional[str] = Field(default="", description="Anthropic API key")
    default_llm_provider: str = Field(default="local", description="Default LLM provider")

    # Discovery & Search API Keys (Reserved for Phase 3+)
    serpapi_api_key: Optional[str] = Field(default="", description="SerpAPI search key")
    tavily_api_key: Optional[str] = Field(default="", description="Tavily search key")
    brave_api_key: Optional[str] = Field(default="", description="Brave search key")
    live_discovery_mode: str = Field(default="auto", description="Product discovery mode: auto | live | mock")

    # Payment Sandbox Keys (Reserved for Phase 5+)
    stripe_secret_key: Optional[str] = Field(default="", description="Stripe secret key")
    stripe_publishable_key: Optional[str] = Field(default="", description="Stripe publishable key")
    razorpay_key_id: Optional[str] = Field(default="", description="Razorpay key ID")
    razorpay_key_secret: Optional[str] = Field(default="", description="Razorpay key secret")

    # Observability & Tracing
    langfuse_public_key: Optional[str] = Field(default="", description="Langfuse public key")
    langfuse_secret_key: Optional[str] = Field(default="", description="Langfuse secret key")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", description="Langfuse host URL")
    otel_exporter_endpoint: Optional[str] = Field(default=None, description="OpenTelemetry OTLP endpoint")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Singleton Instance
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Retrieve or initialize the global AppSettings singleton."""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


def update_runtime_settings(new_settings: dict) -> AppSettings:
    """Dynamically update settings during runtime (e.g. from API configuration modal)."""
    global _settings
    current = get_settings()
    for key, value in new_settings.items():
        if hasattr(current, key) and value is not None:
            setattr(current, key, value)
    return current
