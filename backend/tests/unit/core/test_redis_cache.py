"""Unit tests for Redis cache module."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import redis

from app.core.cache.redis_cache import RedisCache, get_cache, cache_result, invalidate_cache


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = Mock(spec=redis.Redis)
    client.ping.return_value = True
    client.get.return_value = None
    client.setex.return_value = True
    client.delete.return_value = 1
    client.keys.return_value = []
    return client


@pytest.fixture
def redis_cache(mock_redis_client):
    """Create RedisCache instance with mocked client."""
    cache = RedisCache()
    cache._client = mock_redis_client
    return cache


class TestRedisCache:
    """Tests for RedisCache class."""

    def test_get_client_creates_new_client(self):
        """Test get_client creates a new client if none exists."""
        cache = RedisCache()

        with patch("app.core.cache.redis_cache.redis.from_url") as mock_from_url:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_from_url.return_value = mock_client

            client = cache.get_client()

            assert client == mock_client
            mock_from_url.assert_called_once()
            mock_client.ping.assert_called_once()

    def test_get_client_returns_existing_client(self, redis_cache, mock_redis_client):
        """Test get_client returns existing client if already created."""
        client1 = redis_cache.get_client()
        client2 = redis_cache.get_client()

        assert client1 == client2
        assert client1 == mock_redis_client

    def test_get_client_connection_error(self):
        """Test get_client raises ConnectionError on Redis failure."""
        cache = RedisCache()

        with patch("app.core.cache.redis_cache.redis.from_url") as mock_from_url:
            mock_from_url.side_effect = redis.ConnectionError("Connection failed")

            with pytest.raises(ConnectionError, match="Redis connection failed"):
                cache.get_client()

    def test_get_cache_hit(self, redis_cache, mock_redis_client):
        """Test get returns cached value on cache hit."""
        test_data = {"key": "value", "number": 123}
        mock_redis_client.get.return_value = json.dumps(test_data)

        result = redis_cache.get("test_key")

        assert result == test_data
        mock_redis_client.get.assert_called_once_with("test_key")

    def test_get_cache_miss(self, redis_cache, mock_redis_client):
        """Test get returns None on cache miss."""
        mock_redis_client.get.return_value = None

        result = redis_cache.get("test_key")

        assert result is None
        mock_redis_client.get.assert_called_once_with("test_key")

    def test_get_handles_exception(self, redis_cache, mock_redis_client):
        """Test get handles exceptions gracefully."""
        mock_redis_client.get.side_effect = Exception("Redis error")

        result = redis_cache.get("test_key")

        assert result is None

    def test_set_success(self, redis_cache, mock_redis_client):
        """Test set successfully stores value."""
        test_data = {"key": "value"}

        result = redis_cache.set("test_key", test_data, ttl=60)

        assert result is True
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == 60
        assert json.loads(call_args[0][2]) == test_data

    def test_set_with_custom_ttl(self, redis_cache, mock_redis_client):
        """Test set with custom TTL."""
        test_data = {"key": "value"}

        redis_cache.set("test_key", test_data, ttl=300)

        call_args = mock_redis_client.setex.call_args
        assert call_args[0][1] == 300

    def test_set_handles_exception(self, redis_cache, mock_redis_client):
        """Test set handles exceptions gracefully."""
        mock_redis_client.setex.side_effect = Exception("Redis error")

        result = redis_cache.set("test_key", {"data": "value"})

        assert result is False

    def test_delete_success(self, redis_cache, mock_redis_client):
        """Test delete successfully removes key."""
        mock_redis_client.delete.return_value = 1

        result = redis_cache.delete("test_key")

        assert result is True
        mock_redis_client.delete.assert_called_once_with("test_key")

    def test_delete_handles_exception(self, redis_cache, mock_redis_client):
        """Test delete handles exceptions gracefully."""
        mock_redis_client.delete.side_effect = Exception("Redis error")

        result = redis_cache.delete("test_key")

        assert result is False

    def test_clear_pattern_with_keys(self, redis_cache, mock_redis_client):
        """Test clear_pattern deletes matching keys."""
        mock_redis_client.keys.return_value = ["key1", "key2", "key3"]
        mock_redis_client.delete.return_value = 3

        result = redis_cache.clear_pattern("test:*")

        assert result == 3
        mock_redis_client.keys.assert_called_once_with("test:*")
        mock_redis_client.delete.assert_called_once_with("key1", "key2", "key3")

    def test_clear_pattern_no_keys(self, redis_cache, mock_redis_client):
        """Test clear_pattern with no matching keys."""
        mock_redis_client.keys.return_value = []

        result = redis_cache.clear_pattern("test:*")

        assert result == 0
        mock_redis_client.delete.assert_not_called()

    def test_clear_pattern_handles_exception(self, redis_cache, mock_redis_client):
        """Test clear_pattern handles exceptions gracefully."""
        mock_redis_client.keys.side_effect = Exception("Redis error")

        result = redis_cache.clear_pattern("test:*")

        assert result == 0


class TestCacheDecorator:
    """Tests for cache_result decorator."""

    def test_cache_result_miss_and_store(self, mock_redis_client):
        """Test cache_result decorator on cache miss."""
        with patch("app.core.cache.redis_cache.get_cache") as mock_get_cache:
            mock_cache = Mock()
            mock_cache.get.return_value = None
            mock_get_cache.return_value = mock_cache

            @cache_result("test", ttl=30)
            def test_func(arg1, arg2):
                return {"result": arg1 + arg2}

            result = test_func(1, 2)

            assert result == {"result": 3}
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()

    def test_cache_result_hit(self, mock_redis_client):
        """Test cache_result decorator on cache hit."""
        cached_data = {"result": "cached"}

        with patch("app.core.cache.redis_cache.get_cache") as mock_get_cache:
            mock_cache = Mock()
            mock_cache.get.return_value = cached_data
            mock_get_cache.return_value = mock_cache

            function_called = False

            @cache_result("test", ttl=30)
            def test_func(arg1):
                nonlocal function_called
                function_called = True
                return {"result": "new"}

            result = test_func(1)

            assert result == cached_data
            assert not function_called  # Function should not be called
            mock_cache.set.assert_not_called()

    def test_cache_result_with_key_builder(self):
        """Test cache_result decorator with custom key builder."""
        with patch("app.core.cache.redis_cache.get_cache") as mock_get_cache:
            mock_cache = Mock()
            mock_cache.get.return_value = None
            mock_get_cache.return_value = mock_cache

            def custom_key_builder(user_id):
                return f"user_{user_id}"

            @cache_result("users", ttl=60, key_builder=custom_key_builder)
            def get_user(user_id):
                return {"id": user_id, "name": "Test"}

            result = get_user(123)

            assert result == {"id": 123, "name": "Test"}
            # Check that cache key was built correctly
            cache_key_call = mock_cache.get.call_args[0][0]
            assert cache_key_call == "users:user_123"

    def test_cache_result_none_value_not_cached(self):
        """Test cache_result decorator doesn't cache None values."""
        with patch("app.core.cache.redis_cache.get_cache") as mock_get_cache:
            mock_cache = Mock()
            mock_cache.get.return_value = None
            mock_get_cache.return_value = mock_cache

            @cache_result("test", ttl=30)
            def test_func():
                return None

            result = test_func()

            assert result is None
            mock_cache.set.assert_not_called()


class TestGlobalCache:
    """Tests for global cache instance functions."""

    def test_get_cache_singleton(self):
        """Test get_cache returns singleton instance."""
        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2
        assert isinstance(cache1, RedisCache)

    def test_invalidate_cache(self):
        """Test invalidate_cache function."""
        with patch("app.core.cache.redis_cache.get_cache") as mock_get_cache:
            mock_cache = Mock()
            mock_cache.clear_pattern.return_value = 5
            mock_get_cache.return_value = mock_cache

            invalidate_cache("queries:*")

            mock_cache.clear_pattern.assert_called_once_with("queries:*")
