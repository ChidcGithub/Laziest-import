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
        import laziest_import as lz

        lz.clear_cache()
        loaded = lz.list_loaded()
        assert isinstance(loaded, list)

    def test_list_loaded_after_import(self):
        """Test list_loaded after importing module."""
        import laziest_import as lz

        lz.clear_cache()
        _ = lz.math.pi

        loaded = lz.list_loaded()
        assert "math" in loaded

    def test_list_loaded_multiple(self):
        """Test list_loaded with multiple modules."""
        import laziest_import as lz

        lz.clear_cache()
        _ = lz.math.pi
        _ = lz.os.getcwd
        _ = lz.json.dumps

        loaded = lz.list_loaded()
        assert "math" in loaded
        assert "os" in loaded
        assert "json" in loaded


class TestListAvailable:
    """Test list_available function."""

    def test_list_available_returns_list(self):
        """Test that list_available returns a list."""
        import laziest_import as lz

        available = lz.list_available()
        assert isinstance(available, list)

    def test_list_available_has_common_aliases(self):
        """Test that common aliases are available."""
        import laziest_import as lz

        available = lz.list_available()
        assert "np" in available
        assert "pd" in available
        assert "plt" in available
        assert "os" in available

    def test_list_available_includes_stdlib(self):
        """Test that stdlib modules are available."""
        import laziest_import as lz

        available = lz.list_available()
        assert "math" in available
        assert "json" in available
        assert "sys" in available


class TestGetModule:
    """Test get_module function."""

    def test_get_module_not_loaded(self):
        """Test get_module when module not loaded."""
        import laziest_import as lz

        lz.clear_cache()
        mod = lz.get_module("math")
        assert mod is None

    def test_get_module_after_load(self):
        """Test get_module after loading module."""
        import laziest_import as lz

        _ = lz.math.pi
        mod = lz.get_module("math")
        assert mod is not None
        assert hasattr(mod, "pi")

    def test_get_module_nonexistent(self):
        """Test get_module for non-existent alias."""
        import laziest_import as lz

        mod = lz.get_module("nonexistent_alias_xyz")
        assert mod is None


class TestClearCache:
    """Test clear_cache function."""

    def test_clear_cache_removes_loaded(self):
        """Test that clear_cache removes loaded modules."""
        import laziest_import as lz

        _ = lz.math.pi
        assert "math" in lz.list_loaded()

        lz.clear_cache()
        assert "math" not in lz.list_loaded()

    def test_clear_cache_multiple_times(self):
        """Test calling clear_cache multiple times."""
        import laziest_import as lz

        lz.clear_cache()
        lz.clear_cache()
        lz.clear_cache()
        # Should not raise

    def test_clear_cache_then_reload(self):
        """Test reloading after clear_cache."""
        import laziest_import as lz

        _ = lz.math.pi
        lz.clear_cache()
        _ = lz.math.pi
        assert "math" in lz.list_loaded()


class TestResetAll:
    """Test reset_all function."""

    def test_reset_all(self):
        """Test reset_all function."""
        import laziest_import as lz

        # Should not raise
        lz.reset_all()

    def test_reset_all_clears_cache(self):
        """Test that reset_all clears cache."""
        import laziest_import as lz

        _ = lz.math.pi
        lz.reset_all()
        assert "math" not in lz.list_loaded()


class TestGetVersion:
    """Test get_version function."""

    def test_get_version_loaded_module(self):
        """Test get_version for loaded module."""
        import laziest_import as lz

        _ = lz.json.dumps
        version = lz.get_version("json")
        # json is stdlib, may or may not have version
        assert version is None or isinstance(version, str)

    def test_get_version_not_loaded(self):
        """Test get_version for not loaded module."""
        import laziest_import as lz

        lz.clear_cache()
        version = lz.get_version("math")
        assert version is None

    def test_get_version_laziest_import(self):
        """Test get_version for laziest-import itself."""
        import laziest_import as lz

        version = lz.get_cache_version()
        assert isinstance(version, str)


class TestReloadModule:
    """Test reload_module function."""

    def test_reload_module(self):
        """Test reload_module function."""
        import laziest_import as lz

        _ = lz.math.pi
        result = lz.reload_module("math")
        assert result is True

    def test_reload_module_not_loaded(self):
        """Test reload_module for not loaded module."""
        import laziest_import as lz

        lz.register_alias("test_reload", "os")
        lz.clear_cache()
        result = lz.reload_module("test_reload")
        assert result is False
        lz.unregister_alias("test_reload")


class TestSearchModule:
    """Test search_module function."""

    def test_search_module_stdlib(self):
        """Test searching for stdlib modules."""
        import laziest_import as lz

        lz.enable_auto_search()
        assert lz.search_module("os") == "os"
        assert lz.search_module("json") == "json"

    def test_search_module_nonexistent(self):
        """Test searching for non-existent module."""
        import laziest_import as lz

        lz.enable_auto_search()
        result = lz.search_module("nonexistent_module_xyz123")
        assert result is None


class TestSearchClass:
    """Test search_class function."""

    def test_search_class_stdlib(self):
        """Test searching for stdlib class."""
        import laziest_import as lz

        result = lz.search_class("defaultdict")
        if result:
            module_name, cls = result
            assert "collections" in module_name

    def test_search_class_not_found(self):
        """Test searching for non-existent class."""
        import laziest_import as lz

        result = lz.search_class("ThisClassDoesNotExist12345")
        assert result is None


class TestValidateAliasesImportable:
    """Test validate_aliases_importable function."""

    def test_validate_importable(self):
        """Test validating importable aliases."""
        import laziest_import as lz

        result = lz.validate_aliases_importable({"os_test": "os"})
        assert "os_test" in result["importable"]

    def test_validate_not_importable(self):
        """Test validating non-importable aliases."""
        import laziest_import as lz

        result = lz.validate_aliases_importable(
            {"bad": "nonexistent_module_xyz123"}
        )
        assert "bad" in result["not_importable"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
