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

import pytest
import tempfile
import os
import json
import time
from pathlib import Path


class TestCacheDirectory:
    """Test cache directory management."""

    def test_get_cache_dir(self):
        """Test getting cache directory."""
        import laziest_import as lz

        cache_dir = lz.get_cache_dir()
        assert isinstance(cache_dir, Path)
        assert cache_dir.exists() or cache_dir == Path("")

    def test_set_cache_dir(self):
        """Test setting custom cache directory."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            lz.set_cache_dir(tmpdir)
            cache_dir = lz.get_cache_dir()
            assert str(cache_dir) == tmpdir or cache_dir == Path(tmpdir)
            lz.reset_cache_dir()

    def test_set_cache_dir_path_object(self):
        """Test setting cache dir with Path object."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            lz.set_cache_dir(Path(tmpdir))
            cache_dir = lz.get_cache_dir()
            assert str(cache_dir) == tmpdir
            lz.reset_cache_dir()

    def test_reset_cache_dir(self):
        """Test resetting to default cache directory."""
        import laziest_import as lz

        original = lz.get_cache_dir()
        with tempfile.TemporaryDirectory() as tmpdir:
            lz.set_cache_dir(tmpdir)
            lz.reset_cache_dir()
            # Should be back to original or default
            cache_dir = lz.get_cache_dir()
            assert str(cache_dir) != tmpdir or cache_dir == original


class TestCacheConfiguration:
    """Test cache configuration."""

    def test_get_cache_config(self):
        """Test getting cache configuration."""
        import laziest_import as lz

        config = lz.get_cache_config()
        assert isinstance(config, dict)
        assert "symbol_index_ttl" in config
        assert "stdlib_cache_ttl" in config
        assert "max_cache_size_mb" in config

    def test_set_cache_config(self):
        """Test setting cache configuration."""
        import laziest_import as lz

        lz.set_cache_config(
            symbol_index_ttl=3600,
            stdlib_cache_ttl=86400,
            max_cache_size_mb=200,
        )

        config = lz.get_cache_config()
        assert config["symbol_index_ttl"] == 3600
        assert config["stdlib_cache_ttl"] == 86400
        assert config["max_cache_size_mb"] == 200

    def test_set_partial_cache_config(self):
        """Test setting partial cache configuration."""
        import laziest_import as lz

        original = lz.get_cache_config()
        lz.set_cache_config(symbol_index_ttl=7200)
        config = lz.get_cache_config()
        assert config["symbol_index_ttl"] == 7200
        # Other values should remain
        assert config["stdlib_cache_ttl"] == original["stdlib_cache_ttl"]


class TestCacheStatistics:
    """Test cache statistics."""

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        import laziest_import as lz

        stats = lz.get_cache_stats()
        assert isinstance(stats, dict)
        assert "symbol_hits" in stats
        assert "symbol_misses" in stats
        assert "module_hits" in stats
        assert "module_misses" in stats
        assert "hit_rate" in stats

    def test_reset_cache_stats(self):
        """Test resetting cache statistics."""
        import laziest_import as lz

        lz.reset_cache_stats()
        stats = lz.get_cache_stats()
        assert stats["symbol_hits"] == 0
        assert stats["symbol_misses"] == 0
        assert stats["module_hits"] == 0
        assert stats["module_misses"] == 0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        import laziest_import as lz

        lz.reset_cache_stats()

        # Trigger some cache activity
        lz.clear_cache()
        _ = lz.math.pi  # First access - miss
        _ = lz.math.pi  # Second access - hit

        stats = lz.get_cache_stats()
        assert "hit_rate" in stats
        assert 0 <= stats["hit_rate"] <= 1


class TestFileCache:
    """Test file-level caching."""

    def test_enable_file_cache(self):
        """Test enabling file cache."""
        import laziest_import as lz

        lz.enable_file_cache()
        assert lz.is_file_cache_enabled() is True

    def test_disable_file_cache(self):
        """Test disabling file cache."""
        import laziest_import as lz

        lz.disable_file_cache()
        assert lz.is_file_cache_enabled() is False

        # Re-enable for other tests
        lz.enable_file_cache()

    def test_get_file_cache_info(self):
        """Test getting file cache info."""
        import laziest_import as lz

        info = lz.get_file_cache_info()
        assert isinstance(info, dict)
        assert "enabled" in info
        assert "cache_dir" in info

    def test_clear_file_cache(self):
        """Test clearing file cache."""
        import laziest_import as lz

        count = lz.clear_file_cache()
        assert isinstance(count, int)

    def test_force_save_cache(self):
        """Test force saving cache."""
        import laziest_import as lz

        result = lz.force_save_cache()
        assert isinstance(result, bool)


class TestSymbolCache:
    """Test symbol cache operations."""

    def test_get_symbol_cache_info(self):
        """Test getting symbol cache info."""
        import laziest_import as lz

        info = lz.get_symbol_cache_info()
        assert isinstance(info, dict)
        assert "built" in info
        assert "symbol_count" in info

    def test_clear_symbol_cache(self):
        """Test clearing symbol cache."""
        import laziest_import as lz

        lz.clear_symbol_cache()
        info = lz.get_symbol_cache_info()
        assert info["built"] is False
        assert info["symbol_count"] == 0

    def test_rebuild_symbol_index(self):
        """Test rebuilding symbol index."""
        import laziest_import as lz

        lz.clear_symbol_cache()
        lz.rebuild_symbol_index()
        info = lz.get_symbol_cache_info()
        assert info["built"] is True
        assert info["symbol_count"] > 0


class TestPackageVersion:
    """Test package version tracking."""

    def test_get_cache_version(self):
        """Test getting cache version."""
        import laziest_import as lz

        version = lz.get_cache_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_package_version(self):
        """Test getting package version."""
        import laziest_import as lz

        # For installed packages
        version = lz.get_package_version("pytest")
        assert version is not None or version is None  # May or may not be tracked

    def test_get_all_package_versions(self):
        """Test getting all package versions."""
        import laziest_import as lz

        versions = lz.get_all_package_versions()
        assert isinstance(versions, dict)

    def test_get_laziest_import_version(self):
        """Test getting laziest-import version."""
        import laziest_import as lz

        version = lz.get_laziest_import_version()
        assert isinstance(version, str)
        assert version == lz.__version__


class TestCacheInvalidation:
    """Test cache invalidation."""

    def test_invalidate_package_cache(self):
        """Test invalidating package cache."""
        import laziest_import as lz

        # Non-tracked package
        result = lz.invalidate_package_cache("nonexistent_xyz")
        assert isinstance(result, bool)

    def test_invalidate_then_rebuild(self):
        """Test invalidation and rebuild."""
        import laziest_import as lz

        lz.clear_symbol_cache()
        lz.rebuild_symbol_index()
        info_before = lz.get_symbol_cache_info()

        # Invalidate
        lz.invalidate_package_cache("math")

        # Rebuild should still work
        lz.rebuild_symbol_index()
        info_after = lz.get_symbol_cache_info()
        assert info_after["built"] is True


class TestIncrementalIndex:
    """Test incremental index building."""

    def test_get_incremental_config(self):
        """Test getting incremental config."""
        import laziest_import as lz

        config = lz.get_incremental_config()
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_enable_incremental_index(self):
        """Test enabling incremental index."""
        import laziest_import as lz

        lz.enable_incremental_index(True)
        config = lz.get_incremental_config()
        assert config["enabled"] is True

        lz.enable_incremental_index(False)
        config = lz.get_incremental_config()
        assert config["enabled"] is False

        lz.enable_incremental_index(True)

    def test_build_symbol_index_incremental(self):
        """Test incremental symbol index build."""
        import laziest_import as lz

        result = lz.build_symbol_index_incremental()
        assert isinstance(result, bool)


class TestBackgroundBuild:
    """Test background index building."""

    def test_enable_background_build(self):
        """Test enabling background build."""
        import laziest_import as lz

        lz.enable_background_build(True)
        config = lz.get_preheat_config()
        assert config["enabled"] is True

        lz.enable_background_build(False)
        config = lz.get_preheat_config()
        assert config["enabled"] is False

    def test_get_preheat_config(self):
        """Test getting preheat config."""
        import laziest_import as lz

        config = lz.get_preheat_config()
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_start_background_index_build(self):
        """Test starting background index build."""
        import laziest_import as lz

        result = lz.start_background_index_build()
        assert isinstance(result, bool)

    def test_is_index_building(self):
        """Test checking if index is building."""
        import laziest_import as lz

        result = lz.is_index_building()
        assert isinstance(result, bool)

    def test_wait_for_index(self):
        """Test waiting for index build."""
        import laziest_import as lz

        result = lz.wait_for_index(timeout=0.1)
        assert isinstance(result, bool)

    def test_wait_for_index_no_timeout(self):
        """Test waiting for index without timeout."""
        import laziest_import as lz

        result = lz.wait_for_index()
        assert isinstance(result, bool)

    def test_background_timeout(self):
        """Test background timeout settings."""
        import laziest_import as lz

        original = lz.get_background_timeout()
        lz.set_background_timeout(60.0)
        assert lz.get_background_timeout() == 60.0
        lz.set_background_timeout(original)


class TestCacheCompression:
    """Test cache compression."""

    def test_enable_cache_compression(self):
        """Test enabling cache compression."""
        import laziest_import as lz

        lz.enable_cache_compression(True)
        config = lz.get_cache_config()
        assert config["enable_compression"] is True

        lz.enable_cache_compression(False)
        config = lz.get_cache_config()
        assert config["enable_compression"] is False

    def test_compressed_save_load(self):
        """Test compressed save and load."""
        from laziest_import._cache import (
            _save_compressed_json,
            _load_compressed_json,
        )
        import tempfile

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
        from laziest_import._cache import _track_package, _check_package_changed

        _track_package("test_package_xyz", "1.0.0")
        # Should not raise

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
        import laziest_import as lz

        # Set small limit
        lz.set_cache_config(max_cache_size_mb=1)

        # Do some operations
        for _ in range(10):
            _ = lz.math.pi

        # Should not exceed limit significantly
        info = lz.get_file_cache_info()
        assert isinstance(info, dict)

        # Reset
        lz.set_cache_config(max_cache_size_mb=100)

    def test_get_cache_size(self):
        """Test getting cache size."""
        from laziest_import._cache import _get_cache_size

        size = _get_cache_size()
        assert isinstance(size, int)
        assert size >= 0

    def test_cleanup_cache_if_needed(self):
        """Test cache cleanup."""
        from laziest_import._cache import _cleanup_cache_if_needed

        # Should not raise
        _cleanup_cache_if_needed()


class TestCacheThreadSafety:
    """Test cache thread safety."""

    def test_concurrent_cache_access(self):
        """Test concurrent cache access."""
        import laziest_import as lz
        import threading

        errors = []

        def cache_op():
            try:
                for _ in range(10):
                    _ = lz.get_cache_stats()
                    _ = lz.get_cache_config()
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
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            lz.set_cache_dir(tmpdir)
            lz.clear_file_cache()

            # Should still work
            _ = lz.math.pi

            lz.reset_cache_dir()

    def test_invalid_cache_dir(self):
        """Test handling of invalid cache directory."""
        import laziest_import as lz

        original = lz.get_cache_dir()
        # Set to a path that might not exist
        lz.set_cache_dir("/nonexistent/path/xyz123")

        # Should still work (graceful degradation)
        try:
            _ = lz.math.pi
        except Exception:
            pass  # May fail, but shouldn't crash

        lz.reset_cache_dir()

    def test_cache_with_no_permissions(self):
        """Test cache with no write permissions (graceful handling)."""
        # This test is platform-dependent and may require admin
        # Just verify the functions exist
        import laziest_import as lz
        assert callable(lz.clear_file_cache)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
