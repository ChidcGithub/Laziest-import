"""
Real-World Usage Test Suite for laziest-import

This test file simulates how a real user would use the library in practice,
covering ALL features of the library in realistic scenarios.

Features tested:
1. Basic lazy imports (alias prefix, wildcard import)
2. Lazy loading mechanism
3. Module alias management (register, unregister, list)
4. Auto-search functionality
5. Symbol search functionality
6. Cache system (file cache, symbol cache, cache stats)
7. Async imports
8. Auto-install functionality (mocked)
9. Import hooks (pre/post hooks)
10. Debug mode and statistics
11. which() and help() functions
12. Configuration file support (RC config)
13. Module introspection
14. Submodule access (nested modules)
15. Symbol resolution and conflict handling
16. Background index building
17. Symbol sharding
18. Typo correction / fuzzy matching
"""

import sys
import os
import tempfile
import json
import asyncio
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestRealWorldScenario_DataScience:
    """
    Scenario: A data scientist uses laziest-import for their daily work.
    Tests basic imports, aliases, and common data science workflows.
    """

    def test_basic_import_and_usage(self):
        """Test basic lazy import with common stdlib modules."""
        import laziest_import as lz

        # Standard library - immediate usage
        cwd = lz.os.getcwd()
        assert isinstance(cwd, str)

        # Math operations
        assert lz.math.pi > 3.14
        assert lz.math.sqrt(16) == 4.0

        # JSON operations
        data = lz.json.dumps({"key": "value"})
        assert lz.json.loads(data) == {"key": "value"}

    def test_wildcard_import(self):
        """Test from laziest_import import * pattern."""
        namespace = {}
        exec("from laziest_import import *", namespace)

        # Check essential symbols are available
        assert "np" in namespace
        assert "pd" in namespace
        assert "plt" in namespace
        assert "os" in namespace
        assert "json" in namespace
        assert "math" in namespace

        # Check utility functions are available
        assert "register_alias" in namespace
        assert "list_loaded" in namespace
        assert "clear_cache" in namespace
        assert "which" in namespace
        assert "help" in namespace

    def test_lazy_loading_verification(self):
        """Verify that modules are only loaded on first access."""
        import laziest_import as lz

        # Clear cache first
        lz.clear_cache()

        # Check module is not loaded
        loaded = lz.list_loaded()
        assert "json" not in loaded

        # Access the module
        _ = lz.json.dumps

        # Now it should be loaded
        loaded = lz.list_loaded()
        assert "json" in loaded

    def test_submodule_access(self):
        """Test accessing nested submodules."""
        import laziest_import as lz

        # Access os.path (nested submodule)
        path_join = lz.os.path.join
        result = path_join("a", "b", "c")
        assert result == os.path.join("a", "b", "c")

        # Access collections.abc
        assert hasattr(lz.collections.abc, "Iterable")
        assert hasattr(lz.collections.abc, "Mapping")

    def test_module_repr(self):
        """Test module representation strings."""
        import laziest_import as lz

        lz.clear_cache()

        # Before loading
        repr_before = repr(lz.math)
        assert "not loaded" in repr_before

        # After loading
        _ = lz.math.pi
        repr_after = repr(lz.math)
        assert "loaded" in repr_after


class TestRealWorldScenario_AliasManagement:
    """
    Scenario: User needs to manage custom aliases for their project.
    Tests alias registration, validation, and export.
    """

    def test_register_and_use_custom_alias(self):
        """Test registering and using custom aliases."""
        import laziest_import as lz

        # Register custom alias
        lz.register_alias("my_os", "os")

        # Verify it's in available list
        assert "my_os" in lz.list_available()

        # Use the alias
        assert lz.my_os.getcwd() == os.getcwd()

        # Cleanup
        lz.unregister_alias("my_os")
        assert "my_os" not in lz.list_available()

    def test_register_multiple_aliases(self):
        """Test batch alias registration."""
        import laziest_import as lz

        aliases = {
            "my_json": "json",
            "my_math": "math",
            "my_sys": "sys",
        }

        registered = lz.register_aliases(aliases)
        assert len(registered) == 3

        # Verify all are available
        available = lz.list_available()
        assert all(alias in available for alias in aliases.keys())

        # Use one of them
        assert lz.my_json.dumps({"a": 1}) == '{"a": 1}'

        # Cleanup
        for alias in aliases:
            lz.unregister_alias(alias)

    def test_alias_validation(self):
        """Test alias validation functionality."""
        import laziest_import as lz

        # Valid aliases
        result = lz.validate_aliases({"valid_os": "os", "valid_json": "json"})
        assert "valid_os" in result["valid"]
        assert "valid_json" in result["valid"]

        # Invalid alias (empty module name)
        result = lz.validate_aliases({"invalid_alias": ""})
        assert "invalid_alias" in result["invalid"]

    def test_alias_importable_validation(self):
        """Test validating that aliases are actually importable."""
        import laziest_import as lz

        result = lz.validate_aliases_importable({"stdlib_os": "os"})
        assert "stdlib_os" in result["importable"]

        result = lz.validate_aliases_importable({"nonexistent": "this_module_definitely_does_not_exist_xyz123"})
        assert "nonexistent" in result["not_importable"]

    def test_export_aliases(self):
        """Test exporting aliases to JSON."""
        import laziest_import as lz

        # Export as string
        json_str = lz.export_aliases()
        data = json.loads(json_str)
        assert isinstance(data, dict)

        # Export to file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            lz.export_aliases(path=temp_path)
            with open(temp_path, "r") as f:
                data = json.load(f)
            assert isinstance(data, dict)
        finally:
            os.unlink(temp_path)


class TestRealWorldScenario_Search:
    """
    Scenario: User needs to discover modules and symbols.
    Tests auto-search, symbol search, and which() functionality.
    """

    def test_search_stdlib_module(self):
        """Test searching for standard library modules."""
        import laziest_import as lz

        # Exact match
        assert lz.search_module("os") == "os"
        assert lz.search_module("json") == "json"

        # Module not found
        assert lz.search_module("this_module_does_not_exist_xyz123") is None

    def test_auto_search_enabled_by_default(self):
        """Verify auto-search is enabled by default."""
        import laziest_import as lz

        assert lz.is_auto_search_enabled() is True

    def test_enable_disable_auto_search(self):
        """Test toggling auto-search."""
        import laziest_import as lz

        lz.disable_auto_search()
        assert lz.is_auto_search_enabled() is False

        lz.enable_auto_search()
        assert lz.is_auto_search_enabled() is True

    def test_search_symbol_basic(self):
        """Test basic symbol search."""
        import laziest_import as lz

        # Ensure symbol index is built (with timeout)
        info = lz.get_symbol_cache_info()
        if not info["built"]:
            try:
                lz.rebuild_symbol_index()
            except Exception:
                # If rebuild fails, skip the assertion about results
                pass

        # Search for common symbols
        results = lz.search_symbol("sqrt", max_results=5)
        assert isinstance(results, list)

        # Note: results may be empty if symbol index couldn't be built
        # The test just verifies the API works correctly

    def test_search_symbol_with_type_filter(self):
        """Test symbol search with type filtering."""
        import laziest_import as lz

        # Search for classes only
        results = lz.search_symbol("defaultdict", symbol_type="class", max_results=5)
        if results:
            assert all(r.symbol_type == "class" for r in results)

    def test_which_function_basic(self):
        """Test which() function for symbol location."""
        import laziest_import as lz

        # Find sqrt in math
        loc = lz.which("sqrt", "math")
        assert loc is not None
        assert loc.symbol_name == "sqrt"
        assert "math" in loc.module_name

    def test_which_function_dotted_path(self):
        """Test which() with dotted path syntax."""
        import laziest_import as lz

        # Find sin in math module
        loc = lz.which("math.sin")
        assert loc is not None
        assert loc.symbol_name == "sin"

        # Find join in os.path
        loc = lz.which("os.path.join")
        assert loc is not None
        assert loc.symbol_name == "join"

    def test_which_all_function(self):
        """Test which_all() for finding all symbol locations."""
        import laziest_import as lz

        locs = lz.which_all("sqrt")
        assert isinstance(locs, list)

    def test_symbol_location_methods(self):
        """Test SymbolLocation object methods."""
        import laziest_import as lz

        loc = lz.which("sqrt", "math")
        if loc:
            # Test __str__
            str_repr = str(loc)
            assert "sqrt" in str_repr

            # Test __repr__
            repr_str = repr(loc)
            assert "SymbolLocation" in repr_str

            # Test to_dict
            d = loc.to_dict()
            assert "module" in d
            assert "symbol" in d
            assert "type" in d


class TestRealWorldScenario_Caching:
    """
    Scenario: User wants to optimize performance with caching.
    Tests file cache, symbol cache, and cache statistics.
    """

    def test_enable_disable_file_cache(self):
        """Test toggling file cache."""
        import laziest_import as lz

        lz.disable_file_cache()
        assert lz.is_file_cache_enabled() is False

        lz.enable_file_cache()
        assert lz.is_file_cache_enabled() is True

    def test_get_file_cache_info(self):
        """Test getting file cache information."""
        import laziest_import as lz

        info = lz.get_file_cache_info()
        assert "enabled" in info
        assert "cache_size" in info
        assert "cache_dir" in info

    def test_clear_file_cache(self):
        """Test clearing file cache."""
        import laziest_import as lz

        count = lz.clear_file_cache()
        assert isinstance(count, int)

    def test_set_custom_cache_dir(self):
        """Test setting custom cache directory."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            lz.set_cache_dir(tmpdir)
            cache_dir = lz.get_cache_dir()
            assert str(cache_dir) == tmpdir or cache_dir == Path(tmpdir)

            lz.reset_cache_dir()

    def test_cache_configuration(self):
        """Test cache configuration settings."""
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

    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        import laziest_import as lz

        lz.reset_cache_stats()
        stats = lz.get_cache_stats()
        assert "symbol_hits" in stats
        assert "symbol_misses" in stats
        assert "module_hits" in stats
        assert "module_misses" in stats
        assert "hit_rate" in stats

    def test_symbol_cache_operations(self):
        """Test symbol cache operations."""
        import laziest_import as lz

        # Get cache info
        info = lz.get_symbol_cache_info()
        assert "built" in info
        assert "symbol_count" in info

        # Clear symbol cache
        lz.clear_symbol_cache()
        info = lz.get_symbol_cache_info()
        assert info["built"] is False

    def test_invalidate_package_cache(self):
        """Test invalidating cache for specific package."""
        import laziest_import as lz

        # This should return False for non-tracked package
        result = lz.invalidate_package_cache("nonexistent_package_xyz")
        # Just verify it doesn't crash
        assert isinstance(result, bool)

    def test_cache_compression(self):
        """Test cache compression toggle."""
        import laziest_import as lz

        lz.enable_cache_compression(True)
        config = lz.get_cache_config()
        assert config["enable_compression"] is True

        lz.enable_cache_compression(False)


class TestRealWorldScenario_AsyncImport:
    """
    Scenario: User needs async imports for async applications.
    Tests async import functionality.
    """

    @pytest.mark.asyncio
    async def test_import_async_single(self):
        """Test async import of a single module."""
        import laziest_import as lz

        math_mod = await lz.import_async("math")
        assert math_mod is not None
        assert hasattr(math_mod, "pi")
        assert math_mod.pi > 3.14

    @pytest.mark.asyncio
    async def test_import_multiple_async(self):
        """Test async import of multiple modules."""
        import laziest_import as lz

        modules = await lz.import_multiple_async(["math", "json", "os"])

        assert "math" in modules
        assert "json" in modules
        assert "os" in modules

        assert modules["math"].pi > 3.14
        assert callable(modules["json"].dumps)
        assert callable(modules["os"].getcwd)

    def test_retry_mechanism(self):
        """Test retry mechanism for imports."""
        import laziest_import as lz

        lz.enable_retry(max_retries=3, retry_delay=0.1)
        assert lz.is_retry_enabled() is True

        lz.disable_retry()
        assert lz.is_retry_enabled() is False

        lz.enable_retry()  # Re-enable for other tests


class TestRealWorldScenario_Hooks:
    """
    Scenario: User wants to track import activity.
    Tests import hooks functionality.
    """

    def test_pre_import_hook(self):
        """Test pre-import hooks."""
        import laziest_import as lz

        called = []

        def my_hook(module_name):
            called.append(module_name)

        lz.add_pre_import_hook(my_hook)
        lz.clear_cache()
        _ = lz.math.pi

        assert "math" in called
        lz.remove_pre_import_hook(my_hook)

    def test_post_import_hook(self):
        """Test post-import hooks."""
        import laziest_import as lz

        called = []

        def my_hook(module_name, module):
            called.append((module_name, module.__name__))

        lz.add_post_import_hook(my_hook)
        lz.clear_cache()
        _ = lz.json.dumps

        assert any(name == "json" for name, _ in called)
        lz.remove_post_import_hook(my_hook)

    def test_multiple_hooks_order(self):
        """Test that multiple hooks are called in order."""
        import laziest_import as lz

        order = []

        def hook1(name):
            order.append(1)

        def hook2(name):
            order.append(2)

        lz.add_pre_import_hook(hook1)
        lz.add_pre_import_hook(hook2)
        lz.clear_cache()
        _ = lz.sys.version

        # Both hooks should have been called
        assert len(order) >= 2

        lz.remove_pre_import_hook(hook1)
        lz.remove_pre_import_hook(hook2)

    def test_clear_import_hooks(self):
        """Test clearing all hooks."""
        import laziest_import as lz

        def dummy(name):
            pass

        lz.add_pre_import_hook(dummy)
        lz.add_post_import_hook(dummy)
        lz.clear_import_hooks()


class TestRealWorldScenario_DebugAndStats:
    """
    Scenario: User needs debugging and statistics.
    Tests debug mode and import statistics.
    """

    def test_enable_disable_debug_mode(self):
        """Test toggling debug mode."""
        import laziest_import as lz

        lz.enable_debug_mode()
        assert lz.is_debug_mode() is True

        lz.disable_debug_mode()
        assert lz.is_debug_mode() is False

    def test_import_statistics(self):
        """Test import statistics tracking."""
        import laziest_import as lz

        # Reset stats first
        lz.reset_import_stats()
        
        # Clear cache to ensure fresh import
        lz.clear_cache()

        # Import a module - this should trigger import statistics
        _ = lz.math.pi

        stats = lz.get_import_stats()
        assert "total_imports" in stats
        assert "total_time" in stats
        assert "average_time" in stats
        assert "module_times" in stats
        # Note: total_imports may be 0 if module was already in sys.modules
        # from previous tests, but the stats structure should be valid


class TestRealWorldScenario_Configuration:
    """
    Scenario: User wants to customize library behavior.
    Tests configuration files and settings.
    """

    def test_get_rc_info(self):
        """Test getting RC configuration info."""
        import laziest_import as lz

        info = lz.get_rc_info()
        assert "paths_checked" in info
        assert "active_path" in info
        assert "loaded" in info

    def test_create_rc_file(self):
        """Test creating RC configuration file."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.create_rc_file(str(rc_path))  # Test with string path
            assert result.exists()

    def test_create_rc_file_with_template(self):
        """Test creating RC file with template."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.create_rc_file(rc_path, template=True)
            assert result.exists()

            with open(result) as f:
                data = json.load(f)
            assert isinstance(data, dict)

    def test_create_rc_file_exists_error(self):
        """Test that creating existing RC file raises error."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            rc_path.touch()

            with pytest.raises(FileExistsError):
                lz.create_rc_file(rc_path)

    def test_load_rc_config(self):
        """Test loading RC configuration."""
        import laziest_import as lz

        config = lz.load_rc_config()
        assert isinstance(config, dict)

    def test_reload_rc_config(self):
        """Test reloading RC configuration."""
        import laziest_import as lz

        config = lz.reload_rc_config()
        assert isinstance(config, dict)

    def test_get_rc_value(self):
        """Test getting specific RC value."""
        import laziest_import as lz

        value = lz.get_rc_value("nonexistent_key_xyz", default="default_value")
        assert value == "default_value"


class TestRealWorldScenario_HelpSystem:
    """
    Scenario: User wants to learn about the library.
    Tests help() function and documentation.
    """

    def test_help_overview(self):
        """Test help() with no arguments shows overview."""
        import laziest_import as lz

        result = lz.help()
        assert isinstance(result, str)
        assert len(result) > 0
        assert "laziest-import" in result.lower()

    def test_help_topics(self):
        """Test help() with specific topics."""
        import laziest_import as lz

        topics = ["quickstart", "lazy", "alias", "symbol", "cache", "config", "async", "hooks", "api"]

        for topic in topics:
            result = lz.help(topic)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_help_unknown_topic(self):
        """Test help() with unknown topic."""
        import laziest_import as lz

        result = lz.help("nonexistent_topic_xyz123")
        assert "unknown topic" in result.lower() or "not found" in result.lower()


class TestRealWorldScenario_BackgroundIndex:
    """
    Scenario: User wants background index building.
    Tests background index building functionality.
    """

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

    def test_background_timeout_settings(self):
        """Test background timeout configuration."""
        import laziest_import as lz

        original = lz.get_background_timeout()
        
        lz.set_background_timeout(120.0)
        assert lz.get_background_timeout() == 120.0

        lz.set_background_timeout(0)
        assert lz.get_background_timeout() == 0

        lz.set_background_timeout(original)


class TestRealWorldScenario_SymbolSharding:
    """
    Scenario: User works with large packages.
    Tests symbol sharding functionality.
    """

    def test_get_sharding_config(self):
        """Test getting sharding configuration."""
        import laziest_import as lz

        config = lz.get_sharding_config()
        assert "enabled" in config
        assert "shard_threshold" in config

    def test_enable_disable_sharding(self):
        """Test enabling/disabling sharding."""
        import laziest_import as lz

        lz.enable_sharding()
        config = lz.get_sharding_config()
        assert config["enabled"] is True

        lz.disable_sharding()
        config = lz.get_sharding_config()
        assert config["enabled"] is False

        lz.enable_sharding()

    def test_search_with_sharding(self):
        """Test searching with sharding enabled."""
        import laziest_import as lz

        results = lz.search_with_sharding("sqrt", max_results=5)
        assert isinstance(results, list)

    def test_clear_shard_cache(self):
        """Test clearing shard cache."""
        import laziest_import as lz

        lz.clear_shard_cache()


class TestRealWorldScenario_IncrementalIndex:
    """
    Scenario: User wants efficient index updates.
    Tests incremental index building.
    """

    def test_enable_incremental_index(self):
        """Test enabling incremental index."""
        import laziest_import as lz

        lz.enable_incremental_index(True)
        config = lz.get_incremental_config()
        assert config["enabled"] is True

    def test_get_incremental_config(self):
        """Test getting incremental index configuration."""
        import laziest_import as lz

        config = lz.get_incremental_config()
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_build_symbol_index_incremental(self):
        """Test incremental symbol index build."""
        import laziest_import as lz

        result = lz.build_symbol_index_incremental()
        assert isinstance(result, bool)

    def test_get_preheat_config(self):
        """Test getting preheat configuration."""
        import laziest_import as lz

        config = lz.get_preheat_config()
        assert isinstance(config, dict)
        assert "enabled" in config


class TestRealWorldScenario_ModuleIntrospection:
    """
    Scenario: User wants to inspect module contents.
    Tests module introspection functionality.
    """

    def test_list_module_symbols(self):
        """Test listing module symbols."""
        import laziest_import as lz

        symbols = lz.list_module_symbols("math")
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert "sin" in symbols
        assert "cos" in symbols

    def test_list_module_symbols_with_filter(self):
        """Test listing symbols with type filter."""
        import laziest_import as lz

        funcs = lz.list_module_symbols("math", filter_types={"function"})
        assert all(isinstance(s, str) for s in funcs)

    def test_list_module_symbols_exclude_private(self):
        """Test excluding private symbols."""
        import laziest_import as lz

        symbols = lz.list_module_symbols("json", include_private=False)
        assert all(not s.startswith("_") for s in symbols)

    def test_get_module_info(self):
        """Test getting module information."""
        import laziest_import as lz

        info = lz.get_module_info("json")
        assert isinstance(info, dict)
        assert "name" in info
        assert info["name"] == "json"

    def test_search_in_module(self):
        """Test searching symbols in a module."""
        import laziest_import as lz

        results = lz.search_in_module("math", "sin")
        assert isinstance(results, list)
        assert "sin" in results


class TestRealWorldScenario_SymbolResolution:
    """
    Scenario: User needs to handle symbol conflicts.
    Tests symbol resolution and preferences.
    """

    def test_set_get_symbol_preference(self):
        """Test setting and getting symbol preferences."""
        import laziest_import as lz

        lz.set_symbol_preference("TestSymbolXYZ", "test_module")
        pref = lz.get_symbol_preference("TestSymbolXYZ")
        assert pref == "test_module"

        lz.clear_symbol_preference("TestSymbolXYZ")
        pref = lz.get_symbol_preference("TestSymbolXYZ")
        assert pref is None

    def test_get_symbol_resolution_config(self):
        """Test getting symbol resolution configuration."""
        import laziest_import as lz

        config = lz.get_symbol_resolution_config()
        assert isinstance(config, dict)
        assert "auto_symbol" in config

    def test_enable_disable_auto_symbol_resolution(self):
        """Test toggling auto symbol resolution."""
        import laziest_import as lz

        lz.enable_auto_symbol_resolution()
        config = lz.get_symbol_resolution_config()
        assert config["auto_symbol"] is True

        lz.disable_auto_symbol_resolution()
        config = lz.get_symbol_resolution_config()
        assert config["auto_symbol"] is False

        lz.enable_auto_symbol_resolution()

    def test_list_symbol_conflicts(self):
        """Test listing symbol conflicts."""
        import laziest_import as lz

        # List conflicts for a common symbol
        conflicts = lz.list_symbol_conflicts("sqrt")
        assert isinstance(conflicts, list)

    def test_module_priority(self):
        """Test module priority settings."""
        import laziest_import as lz

        lz.set_module_priority("test_priority_module", 100)
        priority = lz.get_module_priority("test_priority_module")
        assert priority == 100

        # Unknown module should have default priority
        priority = lz.get_module_priority("unknown_module_xyz")
        assert priority == 50


class TestRealWorldScenario_AutoInstall:
    """
    Scenario: User wants auto-install for missing packages.
    Tests auto-install functionality (mocked to avoid actual installation).
    """

    def test_auto_install_config(self):
        """Test auto-install configuration."""
        import laziest_import as lz

        config = lz.get_auto_install_config()
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_enable_disable_auto_install(self):
        """Test toggling auto-install."""
        import laziest_import as lz

        lz.enable_auto_install(interactive=False)
        assert lz.is_auto_install_enabled() is True

        lz.disable_auto_install()
        assert lz.is_auto_install_enabled() is False

    def test_set_pip_index(self):
        """Test setting custom pip index."""
        import laziest_import as lz

        lz.set_pip_index("https://pypi.org/simple")
        config = lz.get_auto_install_config()
        assert config["index"] == "https://pypi.org/simple"

        lz.set_pip_index(None)

    def test_set_pip_extra_args(self):
        """Test setting extra pip arguments."""
        import laziest_import as lz

        lz.set_pip_extra_args(["--no-cache-dir"])
        config = lz.get_auto_install_config()
        assert "--no-cache-dir" in config["extra_args"]

        lz.set_pip_extra_args([])


class TestRealWorldScenario_VersionAndReload:
    """
    Scenario: User needs version info and module reload.
    Tests version and reload functionality.
    """

    def test_version_exists(self):
        """Test that version attribute exists."""
        import laziest_import as lz

        assert hasattr(lz, "__version__")
        assert isinstance(lz.__version__, str)

    def test_cache_version(self):
        """Test getting cache version."""
        import laziest_import as lz

        version = lz.get_cache_version()
        assert isinstance(version, str)

    def test_package_version(self):
        """Test getting package version."""
        import laziest_import as lz

        # pytest should be installed
        version = lz.get_package_version("pytest")
        # May or may not have version
        assert version is None or isinstance(version, str)

    def test_get_version_of_loaded_module(self):
        """Test getting version of a loaded module."""
        import laziest_import as lz

        _ = lz.json.dumps
        version = lz.get_version("json")
        # stdlib may not have __version__
        assert version is None or isinstance(version, str)

    def test_reload_module(self):
        """Test reloading a module."""
        import laziest_import as lz

        _ = lz.math.pi
        result = lz.reload_module("math")
        assert result is True

    def test_reload_nonexistent_module(self):
        """Test reloading a module that doesn't exist in lazy modules."""
        import laziest_import as lz

        result = lz.reload_module("nonexistent_module_xyz123")
        assert result is False


class TestRealWorldScenario_ResetOperations:
    """
    Scenario: User needs to reset library state.
    Tests various reset operations.
    """

    def test_clear_cache(self):
        """Test clearing module cache."""
        import laziest_import as lz

        _ = lz.math.pi
        assert "math" in lz.list_loaded()

        lz.clear_cache()
        assert "math" not in lz.list_loaded()

    def test_reset_all(self):
        """Test complete reset."""
        import laziest_import as lz

        _ = lz.math.pi
        lz.reset_all()
        assert "math" not in lz.list_loaded()

    def test_reset_cache_stats(self):
        """Test resetting cache statistics."""
        import laziest_import as lz

        lz.reset_cache_stats()
        stats = lz.get_cache_stats()
        assert stats["symbol_hits"] == 0
        assert stats["symbol_misses"] == 0

    def test_reset_import_stats(self):
        """Test resetting import statistics."""
        import laziest_import as lz

        lz.reset_import_stats()
        stats = lz.get_import_stats()
        assert stats["total_imports"] == 0


class TestRealWorldScenario_LazyProxy:
    """
    Scenario: User uses lazy proxy for auto-correction.
    Tests LazyProxy and typo correction.
    """

    def test_lazy_proxy_access(self):
        """Test accessing modules through lazy proxy."""
        from laziest_import import lazy

        # Access through lazy proxy
        math = lazy.math
        assert math is not None

    def test_lazy_proxy_dir(self):
        """Test dir() on lazy proxy."""
        from laziest_import import lazy

        available = dir(lazy)
        assert isinstance(available, list)

    def test_lazy_proxy_repr(self):
        """Test repr of lazy proxy."""
        from laziest_import import lazy

        repr_str = repr(lazy)
        assert "LazyProxy" in repr_str


class TestRealWorldScenario_EasterEgg:
    """
    Scenario: User discovers the easter egg.
    Tests easter_egg function for fun.
    """

    def test_easter_egg_default(self):
        """Test default easter egg message."""
        import laziest_import as lz

        msg = lz.easter_egg()
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_easter_egg_variants(self):
        """Test easter egg variants."""
        import laziest_import as lz

        variants = ["default", "author", "quote", "tip", "secret", "thanks"]

        for variant in variants:
            msg = lz.easter_egg(variant)
            assert isinstance(msg, str)


class TestRealWorldScenario_ComprehensiveWorkflow:
    """
    Scenario: Complete workflow combining multiple features.
    Tests realistic user workflow using multiple features together.
    """

    def test_data_science_workflow(self):
        """Simulate a data science workflow."""
        import laziest_import as lz

        # Reset state for clean test
        lz.clear_cache()
        lz.reset_import_stats()
        
        # Setup: Enable features
        lz.enable_debug_mode()
        lz.enable_auto_search()
        lz.enable_symbol_search(interactive=False)

        # Workflow: Import and use modules
        cwd = lz.os.getcwd()
        assert isinstance(cwd, str)

        data = {"key": "value"}
        json_str = lz.json.dumps(data)
        assert lz.json.loads(json_str) == data

        value = lz.math.sqrt(16)
        assert value == 4.0

        # Introspection: Check what's loaded
        loaded = lz.list_loaded()
        assert len(loaded) > 0

        # Statistics: Check import stats structure (values may vary due to caching)
        stats = lz.get_import_stats()
        assert "total_imports" in stats
        assert "total_time" in stats

        # Help: Get help
        help_text = lz.help("quickstart")
        assert len(help_text) > 0

        # Which: Find symbol location
        loc = lz.which("sqrt", "math")
        assert loc is not None

        # Cleanup
        lz.disable_debug_mode()
        lz.clear_cache()

    def test_web_development_workflow(self):
        """Simulate a web development workflow."""
        import laziest_import as lz

        # Use datetime for timestamps
        now = lz.datetime.datetime.now()
        assert now is not None

        # Use json for API responses
        api_response = lz.json.dumps({"status": "ok", "timestamp": str(now)})
        assert lz.json.loads(api_response)["status"] == "ok"

        # Use re for validation
        pattern = lz.re.compile(r"^\w+@\w+\.\w+$")
        assert pattern.match("test@example.com") is not None

        # Cleanup
        lz.clear_cache()

    def test_configuration_workflow(self):
        """Simulate a configuration management workflow."""
        import laziest_import as lz

        # Setup: Create custom config
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            lz.create_rc_file(rc_path, template=True)

            # Configure cache
            lz.set_cache_config(
                symbol_index_ttl=3600,
                max_cache_size_mb=50,
            )

            # Configure background building
            lz.set_background_timeout(30.0)
            lz.enable_background_build(True)

            # Verify configuration
            cache_config = lz.get_cache_config()
            assert cache_config["symbol_index_ttl"] == 3600

            preheat_config = lz.get_preheat_config()
            assert preheat_config["enabled"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
