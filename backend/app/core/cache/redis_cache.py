"""Redis caching layer for query results."""

from typing import Optional, Any, Callable
import json
import logging
from functools import wraps
import redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache client wrapper."""

    def __init__(self):
        """Initialize Redis cache client."""
        self._client: Optional[redis.Redis] = None

    def get_client(self) -> redis.Redis:
        """
        Get Redis client instance.

        Returns:
            Redis client

        Raises:
            ConnectionError: If Redis connection fails
        """
        if self._client is None:
            try:
                self._client = redis.from_url(
                    settings.redis_url,
                    password=settings.redis_password if settings.redis_password else None,
                    decode_responses=True,
                    socket_connect_timeout=5,
                )
                # Test connection
                self._client.ping()
                logger.info("Redis connection established")
            except redis.ConnectionError as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise ConnectionError(f"Redis connection failed: {e}")

        return self._client

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            client = self.get_client()
            value = client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 60,
    ) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self.get_client()
            serialized = json.dumps(value)
            client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self.get_client()
            client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "queries:*")

        Returns:
            Number of keys deleted
        """
        try:
            client = self.get_client()
            keys = client.keys(pattern)
            if keys:
                deleted = client.delete(*keys)
                logger.info(f"Cache CLEAR: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Redis clear pattern error for {pattern}: {e}")
            return 0


# Global cache instance
_cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get global Redis cache instance."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache


def cache_result(
    key_prefix: str,
    ttl: int = 60,
    key_builder: Optional[Callable] = None,
):
    """
    Decorator to cache function results in Redis.

    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds
        key_builder: Optional function to build cache key from args/kwargs

    Example:
        @cache_result("queries:list", ttl=30)
        def get_queries(filters):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Default: use function args as key
                args_str = "_".join(str(arg) for arg in args if arg)
                kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
                key_parts = [p for p in [args_str, kwargs_str] if p]
                cache_key = f"{key_prefix}:{'_'.join(key_parts)}" if key_parts else key_prefix

            # Try to get from cache
            cache = get_cache()
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            if result is not None:
                cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Invalidate cache entries matching pattern.

    Args:
        pattern: Key pattern to invalidate

    Example:
        invalidate_cache("queries:*")
    """
    cache = get_cache()
    cache.clear_pattern(pattern)
