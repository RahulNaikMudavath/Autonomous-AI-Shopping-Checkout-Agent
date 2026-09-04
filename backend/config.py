"""
AgentCart Configuration Bridge (Backward Compatibility)
Re-exports AppSettings, get_settings, and update_runtime_settings from backend.core.config.
"""
from backend.core.config import AppSettings, get_settings, update_runtime_settings

__all__ = ["AppSettings", "get_settings", "update_runtime_settings"]
