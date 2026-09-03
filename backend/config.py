"""
Application Configuration & Dynamic Settings Manager
Loads environment variables from .env and supports runtime API key updates.
"""
import os
from typing import Optional
from pydantic import BaseModel, Field

class AppSettings(BaseModel):
    # LLM Keys
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY", "")
    default_llm_provider: str = os.getenv("DEFAULT_LLM_PROVIDER", "local")

    # Search & Discovery Keys
    serpapi_api_key: Optional[str] = os.getenv("SERPAPI_API_KEY", "")
    tavily_api_key: Optional[str] = os.getenv("TAVILY_API_KEY", "")
    brave_api_key: Optional[str] = os.getenv("BRAVE_API_KEY", "")
    live_discovery_mode: str = os.getenv("LIVE_DISCOVERY_MODE", "auto")

    # Payment Keys
    stripe_secret_key: Optional[str] = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_publishable_key: Optional[str] = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    razorpay_key_id: Optional[str] = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_key_secret: Optional[str] = os.getenv("RAZORPAY_KEY_SECRET", "")

    # DB & Observability
    database_url: str = os.getenv("DATABASE_URL", "postgresql://agentcart:securepass@localhost:5432/agentcart_db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    langfuse_public_key: Optional[str] = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key: Optional[str] = os.getenv("LANGFUSE_SECRET_KEY", "")
    langfuse_host: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

_GLOBAL_SETTINGS = AppSettings()

def get_settings() -> AppSettings:
    global _GLOBAL_SETTINGS
    return _GLOBAL_SETTINGS

def update_runtime_settings(new_settings: dict) -> AppSettings:
    global _GLOBAL_SETTINGS
    for k, v in new_settings.items():
        if hasattr(_GLOBAL_SETTINGS, k) and v is not None:
            setattr(_GLOBAL_SETTINGS, k, v)
    return _GLOBAL_SETTINGS
