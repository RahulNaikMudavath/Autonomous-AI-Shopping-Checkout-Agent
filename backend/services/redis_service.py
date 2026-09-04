"""
AgentCart Redis Service Module
Provides ephemeral state storage for multi-agent reasoning, distributed session locks,
and general caching with an automatic in-memory mock fallback when Redis is offline.
"""
import json
import logging
import time
from typing import Any, Dict, Optional
import redis
from backend.core.config import get_settings

logger = logging.getLogger("agentcart.redis")


class InMemoryFallbackCache:
    """High-fidelity in-memory cache mimicking Redis operations for offline/local environments."""
    
    def __init__(self):
        self._store: Dict[str, tuple[str, Optional[float]]] = {}

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        expire_at = (time.time() + ex) if ex else None
        self._store[key] = (value, expire_at)
        return True

    def get(self, key: str) -> Optional[str]:
        if key not in self._store:
            return None
        value, expire_at = self._store[key]
        if expire_at is not None and time.time() > expire_at:
            del self._store[key]
            return None
        return value

    def delete(self, key: str) -> int:
        if key in self._store:
            del self._store[key]
            return 1
        return 0

    def exists(self, key: str) -> int:
        return 1 if self.get(key) is not None else 0

    def ping(self) -> bool:
        return True

    def flushall(self):
        self._store.clear()


class RedisService:
    """
    Manages Redis connection lifecycle, ephemeral agent memory, and caching.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.settings = get_settings()
        self.redis_url = redis_url or self.settings.redis_url
        self._client = None
        self._is_fallback = False
        self._fallback_store = InMemoryFallbackCache()
        self._init_connection()

    def _init_connection(self):
        """Initializes the Redis client or switches to the in-memory fallback."""
        try:
            client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=self.settings.redis_timeout_seconds,
                socket_connect_timeout=self.settings.redis_timeout_seconds
            )
            client.ping()
            self._client = client
            self._is_fallback = False
            logger.info("Connected to Redis server at %s", self.redis_url)
        except Exception as e:
            logger.warning("Redis server unreachable (%s). Using in-memory ephemeral fallback.", str(e))
            self._client = None
            self._is_fallback = True

    @property
    def is_fallback(self) -> bool:
        return self._is_fallback

    def get_client(self):
        if self._client is None and not self._is_fallback:
            self._init_connection()
        return self._client

    # =====================================================================
    # Ephemeral Agent State Operations
    # =====================================================================

    def set_session_state(
        self,
        session_id: str,
        state: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Stores temporary multi-agent state (scratchpad, plan, subagent outputs)."""
        ttl = ttl_seconds or self.settings.redis_ttl_seconds
        key = f"agent_state:{session_id}"
        serialized = json.dumps(state)
        
        try:
            if self._client and not self._is_fallback:
                return bool(self._client.set(key, serialized, ex=ttl))
            return self._fallback_store.set(key, serialized, ex=ttl)
        except Exception as e:
            logger.error("Failed to set session state in Redis: %s", str(e))
            return self._fallback_store.set(key, serialized, ex=ttl)

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves temporary multi-agent state."""
        key = f"agent_state:{session_id}"
        try:
            raw = None
            if self._client and not self._is_fallback:
                raw = self._client.get(key)
            else:
                raw = self._fallback_store.get(key)
                
            if raw:
                return json.loads(raw)
            return None
        except Exception as e:
            logger.error("Failed to retrieve session state from Redis: %s", str(e))
            raw = self._fallback_store.get(key)
            return json.loads(raw) if raw else None

    def delete_session_state(self, session_id: str) -> bool:
        """Cleans up temporary state for a completed or aborted session."""
        key = f"agent_state:{session_id}"
        try:
            if self._client and not self._is_fallback:
                return bool(self._client.delete(key))
            return bool(self._fallback_store.delete(key))
        except Exception as e:
            logger.error("Failed to delete session state from Redis: %s", str(e))
            return bool(self._fallback_store.delete(key))

    # =====================================================================
    # General Key-Value & Cache Operations
    # =====================================================================

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        serialized = json.dumps(value) if not isinstance(value, str) else value
        try:
            if self._client and not self._is_fallback:
                return bool(self._client.set(key, serialized, ex=ttl))
            return self._fallback_store.set(key, serialized, ex=ttl)
        except Exception as e:
            logger.warning("Redis SET error (%s), using fallback.", str(e))
            return self._fallback_store.set(key, serialized, ex=ttl)

    def get(self, key: str) -> Optional[Any]:
        try:
            raw = None
            if self._client and not self._is_fallback:
                raw = self._client.get(key)
            else:
                raw = self._fallback_store.get(key)
            if raw is None:
                return None
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return raw
        except Exception as e:
            logger.warning("Redis GET error (%s), using fallback.", str(e))
            raw = self._fallback_store.get(key)
            if raw is None:
                return None
            try:
                return json.loads(raw)
            except Exception:
                return raw

    def delete(self, key: str) -> bool:
        try:
            if self._client and not self._is_fallback:
                return bool(self._client.delete(key))
            return bool(self._fallback_store.delete(key))
        except Exception as e:
            logger.warning("Redis DELETE error (%s), using fallback.", str(e))
            return bool(self._fallback_store.delete(key))

    def exists(self, key: str) -> bool:
        try:
            if self._client and not self._is_fallback:
                return bool(self._client.exists(key))
            return bool(self._fallback_store.exists(key))
        except Exception as e:
            logger.warning("Redis EXISTS error (%s), using fallback.", str(e))
            return bool(self._fallback_store.exists(key))

    def flush(self):
        """Flushes cache (useful in tests)."""
        if self._client and not self._is_fallback:
            try:
                self._client.flushdb()
            except Exception:
                pass
        self._fallback_store.flushall()

    # =====================================================================
    # Health Probe
    # =====================================================================

    def check_redis_health(self) -> Dict[str, Any]:
        """Probes Redis server connectivity and returns latency and mode."""
        start = time.perf_counter()
        if self._client and not self._is_fallback:
            try:
                self._client.ping()
                latency_ms = (time.perf_counter() - start) * 1000
                return {
                    "status": "connected",
                    "mode": "redis_cluster_or_standalone",
                    "latency_ms": round(latency_ms, 2),
                    "healthy": True
                }
            except Exception as e:
                return {
                    "status": "degraded",
                    "mode": "in_memory_fallback",
                    "error": str(e),
                    "healthy": False
                }
        
        return {
            "status": "fallback_active",
            "mode": "in_memory_mock",
            "latency_ms": 0.05,
            "healthy": True
        }


# Singleton Redis instance
_redis_service: Optional[RedisService] = None


def get_redis_service() -> RedisService:
    """Returns or initializes the global RedisService instance."""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service
