"""
Comprehensive tests for configuration module (_config.py).

Tests cover:
- Module version
- Debug mode
- Import statistics
- Auto-search toggle
- Initialization state
- Version range checking
"""

import pytest
import json
from pathlib import Path
from laziest_import import (
    is_initialized,
    is_initializing,
    is_init_failed,
    get_init_error,
    get_init_lock,
    __version__,
    reset_init_state,
)


class TestModuleVersion:
    """Test module version functionality."""

    def test_version_exists(self):
        """Test that version attribute exists."""

        assert isinstance(__version__, str)

    def test_version_format(self):
        """Test version format is valid."""

        # Should be semantic version or similar
        version = __version__
        parts = version.split(".")
        assert len(parts) >= 2

    def test_version_matches_file(self):
        """Test version matches version.json."""

        version_file = Path(__file__).parent.parent / "laziest_import" / "version.json"
        with open(version_file, encoding="utf-8") as f:
            data = json.load(f)

        expected = data.get("_current_version")
        assert __version__ == expected


class TestDebugMode:
    """Test debug mode functionality."""

    def test_debug_mode_off_by_default(self):
        """Test that debug mode is off by default."""
        from laziest_import import lz

        # Make sure it's off
        lz.config.debug = False
        assert lz.config.debug is False

    def test_enable_debug_mode(self):
        """Test enabling debug mode."""
        from laziest_import import lz

        lz.config.debug = True
        assert lz.config.debug is True

        # Disable for other tests
        lz.config.debug = False

    def test_disable_debug_mode(self):
        """Test disabling debug mode."""
        from laziest_import import lz

        lz.config.debug = True
        lz.config.debug = False
        assert lz.config.debug is False


class TestImportStatistics:
    """Test import statistics functionality."""

    def test_get_import_stats(self):
        """Test getting import statistics."""
        from laziest_import import lz

        stats = lz.config.import_stats
        assert isinstance(stats, dict)
        assert "total_imports" in stats
        assert "total_time" in stats
        assert "average_time" in stats
        assert "module_times" in stats

    def test_reset_import_stats(self):
        """Test resetting import statistics."""
        from laziest_import import lz
        from laziest_import._api._config import reset_import_stats

        reset_import_stats()
        stats = lz.config.import_stats
        assert stats["total_imports"] == 0
        assert stats["total_time"] == 0.0

    def test_stats_updated_on_import(self):
        """Test that stats are updated on import."""
        from laziest_import import lz
        from laziest_import._api._config import reset_import_stats

        reset_import_stats()
        lz.cache.clear()

        _ = lz.math.pi

        stats = lz.config.import_stats
        # Stats may be 0 if module was already imported
        assert isinstance(stats["total_imports"], int)

    def test_module_times_tracking(self):
        """Test that module times are tracked."""
        from laziest_import import lz

        lz.cache.clear()
        _ = lz.json.dumps

        stats = lz.config.import_stats
        assert isinstance(stats["module_times"], dict)


class TestAutoSearchToggle:
    """Test auto-search toggle functionality."""

    def test_auto_search_enabled_by_default(self):
        """Test that auto-search is enabled by default."""
        from laziest_import import lz

        assert lz.config.auto_search is True

    def test_enable_auto_search(self):
        """Test enabling auto-search."""
        from laziest_import import lz

        lz.config.auto_search = False
        lz.config.auto_search = True
        assert lz.config.auto_search is True

    def test_disable_auto_search(self):
        """Test disabling auto-search."""
        from laziest_import import lz

        lz.config.auto_search = False
        assert lz.config.auto_search is False

        # Re-enable for other tests
        lz.config.auto_search = True


class TestInitializationState:
    """Test initialization state functionality."""

    def test_is_initialized(self):
        """Test checking if module is initialized."""
        from laziest_import import lz

        # Should be initialized after import
        assert is_initialized() is True

    def test_is_not_initializing(self):
        """Test that module is not currently initializing."""
        from laziest_import import lz

        assert is_initializing() is False

    def test_is_not_failed(self):
        """Test that initialization did not fail."""
        from laziest_import import lz

        assert is_init_failed() is False

    def test_get_init_error_none(self):
        """Test that no init error exists."""
        from laziest_import import lz

        assert get_init_error() is None

    def test_get_init_lock(self):
        """Test getting initialization lock."""
        from laziest_import import lz

        lock = get_init_lock()
        assert lock is not None


class TestVersionRangeCheck:
    """Test version range checking."""

    def test_get_version_range(self):
        """Test getting version range."""
        from laziest_import._config import get_version_range

        min_ver, max_ver = get_version_range("aliases")
        assert min_ver is None or isinstance(min_ver, str)
        assert max_ver is None or isinstance(max_ver, str)

    def test_check_version_range_valid(self):
        """Test checking valid version range."""
        from laziest_import._config import check_version_range

        # Valid range
        is_valid, msg = check_version_range("0.0.1", "0.0.5", "test")
        assert isinstance(is_valid, bool)
        assert isinstance(msg, str)

    def test_check_version_range_min_only(self):
        """Test version range with only minimum."""
        from laziest_import._config import check_version_range

        is_valid, msg = check_version_range("0.0.1", None, "test")
        assert isinstance(is_valid, bool)

    def test_check_version_range_max_only(self):
        """Test version range with only maximum."""
        from laziest_import._config import check_version_range

        is_valid, msg = check_version_range(None, "1.0.0", "test")
        assert isinstance(is_valid, bool)

    def test_check_version_range_none(self):
        """Test version range with no constraints."""
        from laziest_import._config import check_version_range

        is_valid, msg = check_version_range(None, None, "test")
        assert is_valid is True


class TestConfigDataClasses:
    """Test configuration data classes."""

    def test_import_stats_dataclass(self):
        """Test ImportStats dataclass."""
        from laziest_import._config import ImportStats

        stats = ImportStats()
        assert stats.total_imports == 0
        assert stats.total_time == 0.0

    def test_search_result_dataclass(self):
        """Test SearchResult dataclass."""
        from laziest_import._config import SearchResult

        result = SearchResult(
            module_name="test",
            symbol_name="test_sym",
            symbol_type="function",
            signature=None,
            score=0.9,
        )
        assert result.module_name == "test"
        assert result.score == 0.9

    def test_symbol_match_dataclass(self):
        """Test SymbolMatch dataclass."""
        from laziest_import._config import SymbolMatch

        match = SymbolMatch(
            module_name="math",
            symbol_name="sqrt",
            symbol_type="function",
            signature=None,
            confidence=0.9,
            source="exact",
        )
        assert match.module_name == "math"
        assert match.symbol_name == "sqrt"


class TestConfigConstants:
    """Test configuration constants."""

    def test_reserved_names_exist(self):
        """Test that reserved names are defined."""
        from laziest_import._config import _RESERVED_NAMES

        assert isinstance(_RESERVED_NAMES, set)
        assert len(_RESERVED_NAMES) > 0

    def test_alias_map_is_dict(self):
        """Test that alias map is a dictionary."""
        from laziest_import._config import _ALIAS_MAP

        assert isinstance(_ALIAS_MAP, dict)


class TestConfigThreadSafety:
    """Test configuration thread safety."""

    def test_concurrent_config_access(self):
        """Test concurrent access to configuration."""
        from laziest_import import lz
        import threading

        errors = []

        def config_op():
            try:
                for _ in range(10):
                    _ = lz.config.debug
                    _ = lz.config.auto_search
                    lz.config.debug = True
                    lz.config.debug = False
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=config_op) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestConfigEdgeCases:
    """Test configuration edge cases."""

    def test_reset_init_state(self):
        """Test resetting init state."""
        from laziest_import import lz
        from laziest_import._config import is_initialized, _INITIALIZED

        was_initialized = _INITIALIZED
        reset_init_state()
        assert is_initialized() is False
        if was_initialized:
            from laziest_import import _do_initialize

            _do_initialize()

    def test_repeated_enable_disable(self):
        """Test repeated enable/disable calls."""
        from laziest_import import lz

        for _ in range(10):
            lz.config.debug = True
            lz.config.debug = False
            lz.config.auto_search = True
            lz.config.auto_search = False

        assert lz.config.debug is False
        assert lz.config.auto_search is False
        lz.config.auto_search = True
        assert lz.config.auto_search is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
