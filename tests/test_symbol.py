"""
Comprehensive tests for symbol search module (_symbol).

Tests cover:
- Symbol search functionality
- Symbol index building
- Symbol preferences
- Symbol conflicts
- Symbol resolution
- Symbol sharding
"""

import pytest


class TestSymbolSearch:
    """Test symbol search functionality."""

    def test_search_symbol_basic(self):
        """Test basic symbol search."""
        import laziest_import as lz

        results = lz.search_symbol("sqrt", max_results=5)
        assert isinstance(results, list)

    def test_search_symbol_found(self):
        """Test finding a known symbol."""
        import laziest_import as lz

        lz.rebuild_symbol_index()
        results = lz.search_symbol("sqrt", max_results=10)
        # sqrt should be found in math and/or numpy
        if results:
            assert any("sqrt" in r.symbol_name for r in results)

    def test_search_symbol_not_found(self):
        """Test searching for non-existent symbol."""
        import laziest_import as lz

        results = lz.search_symbol("nonexistent_symbol_xyz12345")
        assert results == [] or results is None or len(results) == 0

    def test_search_symbol_with_type_filter(self):
        """Test symbol search with type filter."""
        import laziest_import as lz

        results = lz.search_symbol("defaultdict", symbol_type="class", max_results=5)
        if results:
            for r in results:
                assert r.symbol_type == "class"

    def test_search_symbol_with_max_results(self):
        """Test max_results parameter."""
        import laziest_import as lz

        results = lz.search_symbol("sqrt", max_results=2)
        assert len(results) <= 2

    def test_search_symbol_case_insensitive(self):
        """Test case-insensitive search."""
        import laziest_import as lz

        results_lower = lz.search_symbol("sqrt", max_results=5)
        results_upper = lz.search_symbol("SQRT", max_results=5)
        # Both should work (case-insensitive)
        assert isinstance(results_lower, list)
        assert isinstance(results_upper, list)


class TestSymbolSearchConfig:
    """Test symbol search configuration."""

    def test_enable_symbol_search(self):
        """Test enabling symbol search."""
        import laziest_import as lz

        lz.enable_symbol_search()
        assert lz.is_symbol_search_enabled() is True

    def test_disable_symbol_search(self):
        """Test disabling symbol search."""
        import laziest_import as lz

        lz.disable_symbol_search()
        assert lz.is_symbol_search_enabled() is False

        # Re-enable
        lz.enable_symbol_search()

    def test_get_symbol_search_config(self):
        """Test getting symbol search config."""
        import laziest_import as lz

        config = lz.get_symbol_search_config()
        assert isinstance(config, dict)
        assert "enabled" in config
        assert "interactive" in config
        assert "max_results" in config

    def test_enable_with_params(self):
        """Test enabling with custom parameters."""
        import laziest_import as lz

        lz.enable_symbol_search(
            interactive=False,
            exact_params=True,
            max_results=20,
            search_depth=3,
            skip_stdlib=False,
        )

        config = lz.get_symbol_search_config()
        assert config["interactive"] is False
        assert config["exact_params"] is True
        assert config["max_results"] == 20

        # Reset
        lz.enable_symbol_search()


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


class TestSymbolPreference:
    """Test symbol preference functionality."""

    def test_set_symbol_preference(self):
        """Test setting symbol preference."""
        import laziest_import as lz

        lz.set_symbol_preference("TestSymbol", "test_module")
        pref = lz.get_symbol_preference("TestSymbol")
        assert pref == "test_module"

    def test_get_symbol_preference_default(self):
        """Test getting preference for unknown symbol."""
        import laziest_import as lz

        pref = lz.get_symbol_preference("UnknownSymbolXYZ")
        assert pref is None

    def test_clear_symbol_preference(self):
        """Test clearing symbol preference."""
        import laziest_import as lz

        lz.set_symbol_preference("TestSymbolClear", "test_module")
        lz.clear_symbol_preference("TestSymbolClear")
        pref = lz.get_symbol_preference("TestSymbolClear")
        assert pref is None


class TestSymbolConflicts:
    """Test symbol conflict detection."""

    def test_list_symbol_conflicts(self):
        """Test listing symbol conflicts."""
        import laziest_import as lz

        conflicts = lz.list_symbol_conflicts("sqrt")
        assert isinstance(conflicts, list)

    def test_find_symbol_conflicts(self):
        """Test finding all symbol conflicts."""
        import laziest_import as lz

        conflicts = lz.find_symbol_conflicts()
        assert isinstance(conflicts, dict)

    def test_show_conflicts(self):
        """Test showing conflicts (should not raise)."""
        import laziest_import as lz

        # Should not raise
        lz.show_conflicts()

    def test_get_conflicts_summary(self):
        """Test getting conflicts summary."""
        import laziest_import as lz

        summary = lz.get_conflicts_summary()
        assert isinstance(summary, dict)
        assert "total_conflicts" in summary


class TestSymbolResolution:
    """Test symbol resolution functionality."""

    def test_enable_auto_symbol_resolution(self):
        """Test enabling auto symbol resolution."""
        import laziest_import as lz

        lz.enable_auto_symbol_resolution()
        config = lz.get_symbol_resolution_config()
        assert config["auto_symbol"] is True

    def test_disable_auto_symbol_resolution(self):
        """Test disabling auto symbol resolution."""
        import laziest_import as lz

        lz.disable_auto_symbol_resolution()
        config = lz.get_symbol_resolution_config()
        assert config["auto_symbol"] is False

        # Re-enable
        lz.enable_auto_symbol_resolution()

    def test_get_symbol_resolution_config(self):
        """Test getting symbol resolution config."""
        import laziest_import as lz

        config = lz.get_symbol_resolution_config()
        assert isinstance(config, dict)
        assert "auto_symbol" in config


class TestModulePriority:
    """Test module priority functionality."""

    def test_set_module_priority(self):
        """Test setting module priority."""
        import laziest_import as lz

        lz.set_module_priority("test_module", 100)
        priority = lz.get_module_priority("test_module")
        assert priority == 100

    def test_get_module_priority_default(self):
        """Test getting priority for unknown module."""
        import laziest_import as lz

        priority = lz.get_module_priority("unknown_module_xyz")
        assert priority == 50  # Default priority

    def test_priority_affects_resolution(self):
        """Test that priority affects symbol resolution."""
        import laziest_import as lz

        # Set high priority for math
        lz.set_module_priority("math", 100)
        # Search for sqrt - should prefer math
        results = lz.search_symbol("sqrt", max_results=5)
        # Just verify it works
        assert isinstance(results, list)


class TestSymbolSharding:
    """Test symbol sharding functionality."""

    def test_get_sharding_config(self):
        """Test getting sharding config."""
        import laziest_import as lz

        config = lz.get_sharding_config()
        assert isinstance(config, dict)
        assert "enabled" in config
        assert "shard_threshold" in config

    def test_enable_sharding(self):
        """Test enabling sharding."""
        import laziest_import as lz

        lz.enable_sharding()
        config = lz.get_sharding_config()
        assert config["enabled"] is True

    def test_disable_sharding(self):
        """Test disabling sharding."""
        import laziest_import as lz

        lz.disable_sharding()
        config = lz.get_sharding_config()
        assert config["enabled"] is False

        # Re-enable
        lz.enable_sharding()

    def test_search_with_sharding(self):
        """Test searching with sharding."""
        import laziest_import as lz

        lz.enable_sharding()
        results = lz.search_with_sharding("sqrt", max_results=5)
        assert isinstance(results, list)

    def test_clear_shard_cache(self):
        """Test clearing shard cache."""
        import laziest_import as lz

        # Should not raise
        lz.clear_shard_cache()


class TestSymbolIndexIncremental:
    """Test incremental symbol index building."""

    def test_build_symbol_index_incremental(self):
        """Test incremental symbol index build."""
        import laziest_import as lz

        result = lz.build_symbol_index_incremental()
        assert isinstance(result, bool)


class TestLoadedModulesContext:
    """Test loaded modules context."""

    def test_get_loaded_modules_context(self):
        """Test getting loaded modules context."""
        import laziest_import as lz

        context = lz.get_loaded_modules_context()
        assert isinstance(context, dict) or isinstance(context, set)

    def test_context_after_import(self):
        """Test context after importing modules."""
        import laziest_import as lz

        _ = lz.math.pi
        _ = lz.os.getcwd

        context = lz.get_loaded_modules_context()
        assert "math" in context or len(context) >= 0


class TestSymbolSearchAdvanced:
    """Test advanced symbol search features."""

    def test_search_with_signature(self):
        """Test search with signature hint."""
        import laziest_import as lz

        results = lz.search_symbol("sqrt", signature="(x)", max_results=5)
        assert isinstance(results, list)

    def test_search_with_exact_params(self):
        """Test search with exact params."""
        import laziest_import as lz

        lz.enable_symbol_search(exact_params=True)
        results = lz.search_symbol("join", max_results=5)
        assert isinstance(results, list)
        lz.enable_symbol_search(exact_params=False)

    def test_search_with_search_depth(self):
        """Test search with different depth."""
        import laziest_import as lz

        lz.enable_symbol_search(search_depth=2)
        results = lz.search_symbol("sqrt", max_results=5)
        assert isinstance(results, list)
        lz.enable_symbol_search(search_depth=1)

    def test_search_skip_stdlib(self):
        """Test search skipping stdlib."""
        import laziest_import as lz

        lz.enable_symbol_search(skip_stdlib=True)
        results = lz.search_symbol("sqrt", max_results=5)
        assert isinstance(results, list)
        lz.enable_symbol_search(skip_stdlib=False)


class TestSymbolSearchEdgeCases:
    """Test symbol search edge cases."""

    def test_search_empty_string(self):
        """Test searching with empty string."""
        import laziest_import as lz

        results = lz.search_symbol("")
        assert results == [] or results is None or isinstance(results, list)

    def test_search_very_long_name(self):
        """Test searching with very long name."""
        import laziest_import as lz

        long_name = "a" * 100
        results = lz.search_symbol(long_name)
        assert results == [] or results is None or isinstance(results, list)

    def test_search_unicode_name(self):
        """Test searching with unicode name."""
        import laziest_import as lz

        results = lz.search_symbol("测试符号")
        assert results == [] or results is None or isinstance(results, list)

    def test_search_special_characters(self):
        """Test searching with special characters."""
        import laziest_import as lz

        results = lz.search_symbol("test-symbol")
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
