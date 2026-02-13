"""Cache module."""

from app.core.cache.redis_cache import get_cache, cache_result, invalidate_cache

__all__ = ["get_cache", "cache_result", "invalidate_cache"]
