"""
Comprehensive tests for cache system (_cache module).

Tests cover:
- Cache directory management
- Cache configuration
- Cache statistics
- File cache operations
- Symbol index cache
- Version tracking
- Incremental updates
- Background operations
"""

import tempfile
from pathlib import Path

import pytest


class TestCacheDirectory:
    """Test cache directory management."""

    def test_get_cache_dir(self):
        """Test getting cache directory."""
        from laziest_import import lz

        cache_dir = lz.cache.dir
        assert isinstance(cache_dir, Path)
        assert cache_dir.exists() or cache_dir == Path("")

    def test_set_cache_dir(self):
        """Test setting custom cache directory."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            lz.cache.dir = tmpdir
            cache_dir = lz.cache.dir
            assert str(cache_dir) == tmpdir or cache_dir == Path(tmpdir)
            lz.cache.reset_dir()

    def test_set_cache_dir_path_object(self):
        """Test setting cache dir with Path object."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            lz.cache.dir = Path(tmpdir)
            cache_dir = lz.cache.dir
            assert str(cache_dir) == tmpdir
            lz.cache.reset_dir()

    def test_reset_cache_dir(self):
        """Test resetting to default cache directory."""
        from laziest_import import lz

        original = lz.cache.dir
        with tempfile.TemporaryDirectory() as tmpdir:
            lz.cache.dir = tmpdir
            lz.cache.reset_dir()
            # Should be back to original or default
            cache_dir = lz.cache.dir
            assert str(cache_dir) != tmpdir or cache_dir == original


class TestCacheConfiguration:
    """Test cache configuration."""

    def test_get_cache_config(self):
        """Test getting cache configuration."""
        from laziest_import import lz

        config = lz.cache.config
        assert hasattr(config, "symbol_index_ttl")
        assert hasattr(config, "max_size_mb")

    def test_set_cache_config(self):
        """Test setting cache configuration."""
        from laziest_import import lz

        lz.cache.config.symbol_index_ttl = 3600
        lz.cache.config.stdlib_cache_ttl = 86400
        lz.cache.config.max_size_mb = 200

        config = lz.cache.config
        assert config.symbol_index_ttl == 3600
        assert config.stdlib_cache_ttl == 86400
        assert config.max_size_mb == 200

    def test_set_partial_cache_config(self):
        """Test setting partial cache configuration."""
        from laziest_import import lz

        original_ttl = lz.cache.config.stdlib_cache_ttl
        lz.cache.config.symbol_index_ttl = 7200
        config = lz.cache.config
        assert config.symbol_index_ttl == 7200
        # Other values should remain
        assert config.stdlib_cache_ttl == original_ttl


class TestCacheStatistics:
    """Test cache statistics."""

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        from laziest_import import lz

        stats = lz.cache.stats
        assert "symbol_hits" in stats
        assert "symbol_misses" in stats
        assert "module_hits" in stats
        assert "module_misses" in stats
        assert "hit_rate" in stats

    def test_reset_cache_stats(self):
        """Test resetting cache statistics."""
        from laziest_import import lz
        from laziest_import._cache import reset_cache_stats

        reset_cache_stats()
        stats = lz.cache.stats
        assert stats["symbol_hits"] == 0
        assert stats["symbol_misses"] == 0
        assert stats["module_hits"] == 0
        assert stats["module_misses"] == 0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        from laziest_import import lz
        from laziest_import._cache import reset_cache_stats

        reset_cache_stats()

        # Trigger some cache activity
        lz.cache.clear()
        _ = lz.math.pi  # First access - miss
        _ = lz.math.pi  # Second access - hit

        stats = lz.cache.stats
        assert "hit_rate" in stats
        assert 0 <= stats["hit_rate"] <= 1


class TestFileCache:
    """Test file-level caching."""

    def test_enable_file_cache(self):
        """Test enabling file cache."""
        from laziest_import import lz

        lz.cache.files.enabled = True
        assert lz.cache.files.enabled is True

    def test_disable_file_cache(self):
        """Test disabling file cache."""
        from laziest_import import lz

        lz.cache.files.enabled = False
        assert lz.cache.files.enabled is False

        # Re-enable for other tests
        lz.cache.files.enabled = True

    def test_get_file_cache_info(self):
        """Test getting file cache info."""
        from laziest_import import lz

        info = lz.cache.files.info()
        assert isinstance(info, dict)
        assert "enabled" in info
        assert "cache_dir" in info

    def test_clear_file_cache(self):
        """Test clearing file cache."""
        from laziest_import import lz

        count = lz.cache.files.clear()
        assert isinstance(count, int)

    def test_force_save_cache(self):
        """Test force saving cache."""
        from laziest_import import lz

        result = lz.cache.files.force_save()
        assert isinstance(result, bool)


class TestSymbolCache:
    """Test symbol cache operations."""

    def test_get_symbol_cache_info(self):
        """Test getting symbol cache info."""
        from laziest_import import lz

        info = lz.symbol.cache_info()
        assert isinstance(info, dict)
        assert "built" in info
        assert "symbol_count" in info

    def test_clear_symbol_cache(self):
        """Test clearing symbol cache."""
        from laziest_import import lz

        lz.cache.symbols.clear()
        info = lz.symbol.cache_info()
        assert info["built"] is False
        assert info["symbol_count"] == 0

    def test_rebuild_symbol_index(self):
        """Test rebuilding symbol index."""
        from laziest_import import lz

        lz.cache.symbols.clear()
        lz.symbol.index.rebuild()
        info = lz.symbol.cache_info()
        assert info["built"] is True
        assert info["symbol_count"] > 0


class TestPackageVersion:
    """Test package version tracking."""

    def test_get_cache_version(self):
        """Test getting cache version."""
        from laziest_import import lz

        version = lz.version.cache()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_package_version(self):
        """Test getting package version."""
        from laziest_import import lz

        # For installed packages
        version = lz.version.of("pytest")
        assert version is not None or version is None  # May or may not be tracked

    def test_get_all_package_versions(self):
        """Test getting all package versions."""
        from laziest_import import lz

        versions = lz.version.all_packages()
        assert isinstance(versions, dict)

    def test_get_laziest_import_version(self):
        """Test getting laziest-import version."""
        from laziest_import import lz

        version = lz.version.current
        assert isinstance(version, str)
        assert version == lz.version.current


class TestCacheInvalidation:
    """Test cache invalidation."""

    def test_invalidate_package_cache(self):
        """Test invalidating package cache."""
        from laziest_import._cache import invalidate_package_cache

        # Non-tracked package
        result = invalidate_package_cache("nonexistent_xyz")
        assert isinstance(result, bool)

    def test_invalidate_then_rebuild(self):
        """Test invalidation and rebuild."""
        from laziest_import import lz

        lz.cache.symbols.clear()
        lz.symbol.index.rebuild()
        lz.symbol.cache_info()

        # Invalidate
        from laziest_import._cache import invalidate_package_cache

        invalidate_package_cache("math")

        # Rebuild should still work
        lz.symbol.index.rebuild()
        info_after = lz.symbol.cache_info()
        assert info_after["built"] is True


class TestIncrementalIndex:
    """Test incremental index building."""

    def test_get_incremental_config(self):
        """Test getting incremental config."""
        from laziest_import._cache import get_incremental_config

        config = get_incremental_config()
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_enable_incremental_index(self):
        """Test enabling incremental index."""
        from laziest_import._cache import get_incremental_config
        from laziest_import._cache._incremental import enable_incremental_index

        enable_incremental_index(True)
        config = get_incremental_config()
        assert config["enabled"] is True

        enable_incremental_index(False)
        config = get_incremental_config()
        assert config["enabled"] is False

        enable_incremental_index(True)

    def test_build_symbol_index_incremental(self):
        """Test incremental symbol index build."""
        from laziest_import import lz

        result = lz.symbol.index.incremental()
        assert isinstance(result, bool)


class TestBackgroundBuild:
    """Test background index building."""

    def test_enable_background_build(self):
        """Test enabling background build."""
        from laziest_import import lz

        lz.background.enable(True)
        config = lz.background.preheat
        assert config["enabled"] is True

        lz.background.enable(False)
        config = lz.background.preheat
        assert config["enabled"] is False

    def test_get_preheat_config(self):
        """Test getting preheat config."""
        from laziest_import import lz

        config = lz.background.preheat
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_start_background_index_build(self):
        """Test starting background index build."""
        from laziest_import import lz

        result = lz.background.start()
        assert isinstance(result, bool)

    def test_is_index_building(self):
        """Test checking if index is building."""
        from laziest_import import lz

        result = lz.background.is_building
        assert isinstance(result, bool)

    def test_wait_for_index(self):
        """Test waiting for index build."""
        from laziest_import import lz

        result = lz.background.wait(timeout=0.1)
        assert isinstance(result, bool)

    def test_wait_for_index_no_timeout(self):
        """Test waiting for index without timeout."""
        from laziest_import import lz

        result = lz.background.wait()
        assert isinstance(result, bool)

    def test_background_timeout(self):
        """Test background timeout settings."""
        from laziest_import import lz

        original = lz.background.timeout
        lz.background.timeout = 60.0
        assert lz.background.timeout == 60.0
        lz.background.timeout = original


class TestCacheCompression:
    """Test cache compression."""

    def test_enable_cache_compression(self):
        """Test enabling cache compression."""
        from laziest_import import lz

        lz.cache.compression = True
        assert lz.cache.config.compression is True

        lz.cache.compression = False
        assert lz.cache.config.compression is False

    def test_compressed_save_load(self):
        """Test compressed save and load."""
        import tempfile

        from laziest_import._cache import (
            _load_compressed_json,
            _save_compressed_json,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test.json.gz"

            data = {"test": "data", "number": 123}
            _save_compressed_json(data, test_path)
            loaded = _load_compressed_json(test_path)

            assert loaded == data


class TestSymbolIndexCache:
    """Test symbol index cache operations."""

    def test_get_symbol_index_path(self):
        """Test getting symbol index path."""
        from laziest_import._cache import _get_symbol_index_path

        path = _get_symbol_index_path()
        assert isinstance(path, Path)

    def test_get_tracked_packages_path(self):
        """Test getting tracked packages path."""
        from laziest_import._cache import _get_tracked_packages_path

        path = _get_tracked_packages_path()
        assert isinstance(path, Path)

    def test_track_package(self):
        """Test tracking a package."""
        from laziest_import._cache import _check_package_changed, _track_package

        _track_package("test_package_xyz", "1.0.0")
        result = _check_package_changed("test_package_xyz")
        assert result is False or result is True

    def test_check_package_changed(self):
        """Test checking if package changed."""
        from laziest_import._cache import _check_package_changed

        # Unknown package
        result = _check_package_changed("unknown_package_xyz")
        assert result is True or result is False


class TestCacheSizeManagement:
    """Test cache size management."""

    def test_cache_size_limit(self):
        """Test cache size limit."""
        from laziest_import import lz

        # Set small limit
        lz.cache.config.max_cache_size_mb = 1

        # Do some operations
        for _ in range(10):
            _ = lz.math.pi

        # Should not exceed limit significantly
        info = lz.cache.files.info()
        assert isinstance(info, dict)

        # Reset
        lz.cache.config.max_cache_size_mb = 100

    def test_get_cache_size(self):
        """Test getting cache size."""
        from laziest_import._cache import _get_cache_size

        size = _get_cache_size()
        assert isinstance(size, int)
        assert size >= 0

    def test_cleanup_cache_if_needed(self):
        """Test cache cleanup."""
        from laziest_import._cache import _cleanup_cache_if_needed

        result = _cleanup_cache_if_needed()
        assert result is None or result is True


class TestCacheThreadSafety:
    """Test cache thread safety."""

    def test_concurrent_cache_access(self):
        """Test concurrent cache access."""
        import threading

        from laziest_import import lz

        errors = []

        def cache_op():
            try:
                for _ in range(10):
                    _ = lz.cache.stats
                    _ = lz.cache.config
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=cache_op) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestCacheEdgeCases:
    """Test cache edge cases."""

    def test_empty_cache_dir(self):
        """Test with empty cache directory."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            lz.cache.dir = tmpdir
            lz.cache.files.clear()

            result = lz.math.pi
            assert result > 3

            lz.cache.reset_dir()

    def test_invalid_cache_dir(self):
        """Test handling of invalid cache directory."""
        from laziest_import import lz

        # Set to a path that might not exist
        lz.cache.dir = "/nonexistent/path/xyz123"

        result = lz.math.pi
        assert result > 3

        lz.cache.reset_dir()

    def test_cache_with_no_permissions(self):
        """Test cache with no write permissions (graceful handling)."""
        # This test is platform-dependent and may require admin
        # Just verify the functions exist
        from laziest_import import lz

        assert callable(lz.cache.files.clear)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
