"""Tests for Cache Manager Module."""

import pytest
from backend.core.infrastructure.cache.cache_manager import (
    CacheManager,
    get_cache_manager,
    cache_result,
    invalidate_cache
)


class TestCacheManager:
    """Tests for CacheManager class."""

    def test_cache_manager_initialization(self):
        """Test creating a cache manager."""
        cache = CacheManager(
            redis_url="redis://localhost:6379/0",
            default_ttl=3600,
            key_prefix="test:"
        )
        assert cache.redis_url == "redis://localhost:6379/0"
        assert cache.default_ttl == 3600
        assert cache.key_prefix == "test:"

    def test_cache_set_and_get(self):
        """Test setting and getting values."""
        cache = CacheManager()
        cache.set("test_key", "test_value")
        result = cache.get("test_key")
        assert result == "test_value"

    def test_cache_get_nonexistent(self):
        """Test getting non-existent value."""
        cache = CacheManager()
        result = cache.get("nonexistent_key", default="default_value")
        assert result == "default_value"

    def test_cache_delete(self):
        """Test deleting values."""
        cache = CacheManager()
        cache.set("test_key", "test_value")
        cache.delete("test_key")
        result = cache.get("test_key")
        assert result is None

    def test_cache_exists(self):
        """Test checking if key exists."""
        cache = CacheManager()
        cache.set("test_key", "test_value")
        assert cache.exists("test_key") is True
        assert cache.exists("nonexistent_key") is False

    def test_cache_clear(self):
        """Test clearing all cache."""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.exists("key1") is False
        assert cache.exists("key2") is False

    def test_cache_get_many(self):
        """Test getting multiple values."""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        result = cache.get_many(["key1", "key2", "key4"])
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
        assert "key3" not in result

    def test_cache_set_many(self):
        """Test setting multiple values."""
        cache = CacheManager()
        items = {
            "key1": "value1",
            "key2": "value2"
        }
        cache.set_many(items)
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

    def test_cache_increment(self):
        """Test incrementing counter."""
        cache = CacheManager()
        cache.set("counter", 10)
        result = cache.increment("counter")
        assert result == 11

    def test_cache_get_stats(self):
        """Test getting cache statistics."""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        stats = cache.get_stats()
        assert "backend" in stats
        assert "total_keys" in stats or "memory_keys" in stats


class TestGlobalCacheManager:
    """Tests for global cache manager."""

    def test_get_cache_manager(self):
        """Test getting global cache manager."""
        cache = get_cache_manager()
        assert cache is not None
        assert isinstance(cache, CacheManager)


class TestCacheDecorator:
    """Tests for cache decorator."""

    def test_cache_result_decorator(self):
        """Test caching function results."""
        call_count = 0

        @cache_result(key_prefix="test", ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Second call should use cache
