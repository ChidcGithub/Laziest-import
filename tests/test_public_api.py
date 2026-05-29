"""
Comprehensive tests for public API module (_public_api.py).

Tests cover:
- list_loaded
- list_available
- get_module
- clear_cache
- reset_all
- get_version
- reload_module
- search_module
- search_class
"""

import pytest


class TestListLoaded:
    """Test list_loaded function."""

    def test_list_loaded_empty(self):
        """Test list_loaded when no modules loaded."""
        from laziest_import import lz

        lz.cache.clear()
        loaded = lz.module.list_loaded()
        assert isinstance(loaded, list)

    def test_list_loaded_after_import(self):
        """Test list_loaded after importing module."""
        from laziest_import import lz

        lz.cache.clear()
        _ = lz.math.pi

        loaded = lz.module.list_loaded()
        assert "math" in loaded

    def test_list_loaded_multiple(self):
        """Test list_loaded with multiple modules."""
        from laziest_import import lz

        lz.cache.clear()
        _ = lz.math.pi
        _ = lz.os.getcwd
        _ = lz.json.dumps

        loaded = lz.module.list_loaded()
        assert "math" in loaded
        assert "os" in loaded
        assert "json" in loaded


class TestListAvailable:
    """Test list_available function."""

    def test_list_available_returns_list(self):
        """Test that list_available returns a list."""
        from laziest_import import lz

        available = lz.module.list_available()
        assert isinstance(available, list)

    def test_list_available_has_common_aliases(self):
        """Test that common aliases are available."""
        from laziest_import import lz

        available = lz.module.list_available()
        assert "np" in available
        assert "pd" in available
        assert "plt" in available
        assert "os" in available

    def test_list_available_includes_stdlib(self):
        """Test that stdlib modules are available."""
        from laziest_import import lz

        available = lz.module.list_available()
        assert "math" in available
        assert "json" in available
        assert "sys" in available


class TestGetModule:
    """Test get_module function."""

    def test_get_module_not_loaded(self):
        """Test get_module when module not loaded."""
        from laziest_import import lz

        lz.cache.clear()
        mod = lz.module.get("math")
        assert mod is None

    def test_get_module_after_load(self):
        """Test get_module after loading module."""
        from laziest_import import lz

        _ = lz.math.pi
        mod = lz.module.get("math")
        assert mod is not None
        assert hasattr(mod, "pi")

    def test_get_module_nonexistent(self):
        """Test get_module for non-existent alias."""
        from laziest_import import lz

        mod = lz.module.get("nonexistent_alias_xyz")
        assert mod is None


class TestClearCache:
    """Test clear_cache function."""

    def test_clear_cache_removes_loaded(self):
        """Test that clear_cache removes loaded modules."""
        from laziest_import import lz

        _ = lz.math.pi
        assert "math" in lz.module.list_loaded()

        lz.cache.clear()
        assert "math" not in lz.module.list_loaded()

    def test_clear_cache_multiple_times(self):
        """Test calling clear_cache multiple times."""
        from laziest_import import lz

        _ = lz.math.pi
        lz.cache.clear()
        lz.cache.clear()
        lz.cache.clear()
        assert "math" not in lz.module.list_loaded()

    def test_clear_cache_then_reload(self):
        """Test reloading after clear_cache."""
        from laziest_import import lz

        _ = lz.math.pi
        lz.cache.clear()
        _ = lz.math.pi
        assert "math" in lz.module.list_loaded()


class TestResetAll:
    """Test reset_all function."""

    def test_reset_all(self):
        """Test reset_all function."""
        from laziest_import._config import reset_all
        from laziest_import._config import _ALIAS_MAP

        reset_all()
        # Verify state was reset
        assert isinstance(_ALIAS_MAP, dict)

    def test_reset_all_clears_cache(self):
        """Test that reset_all clears cache."""
        from laziest_import import lz
        from laziest_import._config import reset_all

        _ = lz.math.pi
        reset_all()
        assert "math" not in lz.module.list_loaded()


class TestGetVersion:
    """Test get_version function."""

    def test_get_version_loaded_module(self):
        """Test get_version for loaded module."""
        from laziest_import import lz

        _ = lz.json.dumps
        version = lz.version.of("json")
        # json is stdlib, may or may not have version
        assert version is None or isinstance(version, str)

    def test_get_version_not_loaded(self):
        """Test get_version for not loaded module."""
        from laziest_import import lz

        lz.cache.clear()
        version = lz.version.of("math")
        assert version is None

    def test_get_version_laziest_import(self):
        """Test get_version for laziest-import itself."""
        from laziest_import import lz

        version = lz.version.cache()
        assert isinstance(version, str)


class TestReloadModule:
    """Test reload_module function."""

    def test_reload_module(self):
        """Test reload_module function."""
        from laziest_import import lz

        _ = lz.math.pi
        result = lz.module.reload("math")
        assert result is True

    def test_reload_module_not_loaded(self):
        """Test reload_module for not loaded module."""
        from laziest_import import lz

        lz.alias.register("test_reload", "os")
        lz.cache.clear()
        result = lz.module.reload("test_reload")
        assert result is False
        lz.alias.unregister("test_reload")


class TestSearchModule:
    """Test search_module function."""

    def test_search_module_stdlib(self):
        """Test searching for stdlib modules."""
        from laziest_import import lz

        lz.symbol.config.enable()
        lz.config.auto_search = True
        result = lz.symbol.search("os")
        assert isinstance(result, list)
        assert len(result) > 0
        result = lz.symbol.search("json")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_search_module_nonexistent(self):
        """Test searching for non-existent module."""
        from laziest_import import lz

        lz.config.auto_search = True
        result = lz.symbol.search("nonexistent_module_xyz123")
        assert result == []


class TestSearchClass:
    """Test search_class function."""

    def test_search_class_stdlib(self):
        """Test searching for stdlib class."""
        from laziest_import import lz

        result = lz.symbol.search("defaultdict", symbol_type="class")
        if result:
            assert isinstance(result[0].module_name, str)
            assert len(result[0].module_name) > 0

    def test_search_class_not_found(self):
        """Test searching for non-existent class."""
        from laziest_import import lz

        result = lz.symbol.search("ThisClassDoesNotExist12345", symbol_type="class")
        assert result == []


class TestValidateAliasesImportable:
    """Test validate_aliases_importable function."""

    def test_validate_importable(self):
        """Test validating importable aliases."""
        from laziest_import._alias import validate_aliases_importable

        result = validate_aliases_importable({"os_test": "os"})
        assert "os_test" in result["importable"]

    def test_validate_not_importable(self):
        """Test validating non-importable aliases."""
        from laziest_import._alias import validate_aliases_importable

        result = validate_aliases_importable({"bad": "nonexistent_module_xyz123"})
        assert "bad" in result["not_importable"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
