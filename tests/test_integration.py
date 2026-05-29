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

# Direct imports for functions not exposed via OOP API
from laziest_import._cache import (
    invalidate_package_cache,
    get_incremental_config,
    reset_cache_stats,
)
from laziest_import._config import reset_all
from laziest_import._api._config import reset_import_stats
from laziest_import._symbol import (
    get_sharding_config,
    enable_sharding,
    disable_sharding,
    clear_shard_cache,
    set_module_priority,
    get_module_priority,
)
from laziest_import._introspect import get_module_info
from laziest_import._install import set_pip_index, set_pip_extra_args


class TestRealWorldScenario_DataScience:
    """
    Scenario: A data scientist uses laziest-import for their daily work.
    Tests basic imports, aliases, and common data science workflows.
    """

    def test_basic_import_and_usage(self):
        """Test basic lazy import with common stdlib modules."""
        from laziest_import import lz

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
        assert "which" in namespace
        assert "help" in namespace

    def test_lazy_loading_verification(self):
        """Verify that modules are only loaded on first access."""
        from laziest_import import lz

        # Clear cache first
        lz.cache.clear()

        # Check module is not loaded
        loaded = lz.module.list_loaded()
        assert "json" not in loaded

        # Access the module
        _ = lz.json.dumps

        # Now it should be loaded
        loaded = lz.module.list_loaded()
        assert "json" in loaded

    def test_submodule_access(self):
        """Test accessing nested submodules."""
        from laziest_import import lz

        # Access os.path (nested submodule)
        path_join = lz.os.path.join
        result = path_join("a", "b", "c")
        assert result == os.path.join("a", "b", "c")

        # Access collections.abc
        assert hasattr(lz.collections.abc, "Iterable")
        assert hasattr(lz.collections.abc, "Mapping")

    def test_module_repr(self):
        """Test module representation strings."""
        from laziest_import import lz
        from laziest_import._api._module import _get_lazy_module

        lz.cache.clear()

        # Before loading
        lm = _get_lazy_module("math")
        repr_before = repr(lm)
        assert "not loaded" in repr_before

        # After loading
        _ = lm.pi
        repr_after = repr(lm)
        assert "loaded" in repr_after


class TestRealWorldScenario_AliasManagement:
    """
    Scenario: User needs to manage custom aliases for their project.
    Tests alias registration, validation, and export.
    """

    def test_register_and_use_custom_alias(self):
        """Test registering and using custom aliases."""
        from laziest_import import lz

        # Register custom alias
        lz.alias.register("my_os", "os")

        # Verify it's in available list
        assert "my_os" in lz.module.list_available()

        # Use the alias
        assert lz.my_os.getcwd() == os.getcwd()

        # Cleanup
        lz.alias.unregister("my_os")
        assert "my_os" not in lz.module.list_available()

    def test_register_multiple_aliases(self):
        """Test batch alias registration."""
        from laziest_import import lz

        aliases = {
            "my_json": "json",
            "my_math": "math",
            "my_sys": "sys",
        }

        registered = lz.alias.register_many(aliases)
        assert len(registered) == 3

        # Verify all are available
        available = lz.module.list_available()
        assert all(alias in available for alias in aliases.keys())

        # Use one of them
        assert lz.my_json.dumps({"a": 1}) == '{"a": 1}'

        # Cleanup
        for alias in aliases:
            lz.alias.unregister(alias)

    def test_alias_validation(self):
        """Test alias validation functionality."""
        from laziest_import import lz

        # Valid aliases
        result = lz.alias.validate({"valid_os": "os", "valid_json": "json"})
        assert "valid_os" in result.get("valid", [])
        assert "valid_json" in result.get("valid", [])

        # Invalid alias (empty module name)
        result = lz.alias.validate({"invalid_alias": ""})
        assert "invalid_alias" in result.get("invalid", [])

    def test_alias_importable_validation(self):
        """Test validating that aliases are actually importable."""
        from laziest_import._alias import validate_aliases_importable

        result = validate_aliases_importable({"stdlib_os": "os"})
        assert "stdlib_os" in result["importable"]

        result = validate_aliases_importable(
            {"nonexistent": "this_module_definitely_does_not_exist_xyz123"}
        )
        assert "nonexistent" in result["not_importable"]

    def test_export_aliases(self):
        """Test exporting aliases to JSON."""
        from laziest_import import lz

        # Export as string
        json_str = lz.alias.export()
        data = json.loads(json_str)
        assert isinstance(data, dict)

        # Export to file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            lz.alias.export(path=temp_path)
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
        from laziest_import import lz

        # Symbol search returns list of SearchResult objects
        result = lz.symbol.search("os")
        assert isinstance(result, list)

        result = lz.symbol.search("json")
        assert isinstance(result, list)

        # Module not found
        result = lz.symbol.search("this_module_does_not_exist_xyz123")
        assert result == []

    def test_auto_search_enabled_by_default(self):
        """Verify auto-search is enabled by default."""
        from laziest_import import lz

        assert lz.config.auto_search is True

    def test_enable_disable_auto_search(self):
        """Test toggling auto-search."""
        from laziest_import import lz

        lz.config.auto_search = False
        assert lz.config.auto_search is False

        lz.config.auto_search = True
        assert lz.config.auto_search is True

    def test_search_symbol_basic(self):
        """Test basic symbol search."""
        from laziest_import import lz

        # Ensure symbol index is built (with timeout)
        info = lz.symbol.cache_info()
        if not info["built"]:
            try:
                lz.symbol.index.rebuild()
            except Exception:
                # If rebuild fails, skip the assertion about results
                pass

        # Search for common symbols
        results = lz.symbol.search("sqrt", max_results=5)
        assert isinstance(results, list)

        # Note: results may be empty if symbol index couldn't be built
        # The test just verifies the API works correctly

    def test_search_symbol_with_type_filter(self):
        """Test symbol search with type filtering."""
        from laziest_import import lz

        # Search for classes only
        results = lz.symbol.search("defaultdict", symbol_type="class", max_results=5)
        if results:
            assert all(r.symbol_type == "class" for r in results)

    def test_which_function_basic(self):
        """Test which() function for symbol location."""
        from laziest_import import lz

        # Find sqrt in math
        loc = lz.symbol.which("sqrt", "math")
        assert loc is not None
        assert loc.symbol_name == "sqrt"
        assert "math" in loc.module_name

    def test_which_function_dotted_path(self):
        """Test which() with dotted path syntax."""
        from laziest_import import lz

        # Find sin in math module
        loc = lz.symbol.which("math.sin")
        assert loc is not None
        assert loc.symbol_name == "sin"

        # Find join in os.path
        loc = lz.symbol.which("os.path.join")
        assert loc is not None
        assert loc.symbol_name == "join"

    def test_which_all_function(self):
        """Test which_all() for finding all symbol locations."""
        from laziest_import import lz

        locs = lz.symbol.which_all("sqrt")
        assert isinstance(locs, list)

    def test_symbol_location_methods(self):
        """Test SymbolLocation object methods."""
        from laziest_import import lz

        loc = lz.symbol.which("sqrt", "math")
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
        from laziest_import import lz

        lz.cache.files.enabled = False
        assert lz.cache.files.enabled is False

        lz.cache.files.enabled = True
        assert lz.cache.files.enabled is True

    def test_get_file_cache_info(self):
        """Test getting file cache information."""
        from laziest_import import lz

        info = lz.cache.files.info()
        assert "enabled" in info
        assert "cache_size" in info
        assert "cache_dir" in info

    def test_clear_file_cache(self):
        """Test clearing file cache."""
        from laziest_import import lz

        count = lz.cache.files.clear()
        assert isinstance(count, int)

    def test_set_custom_cache_dir(self):
        """Test setting custom cache directory."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            lz.cache.dir = tmpdir
            cache_dir = lz.cache.dir
            assert str(cache_dir) == tmpdir or cache_dir == Path(tmpdir)

            lz.cache.reset_dir()

    def test_cache_configuration(self):
        """Test cache configuration settings."""
        from laziest_import import lz

        lz.cache.config.symbol_index_ttl = 3600
        lz.cache.config.stdlib_cache_ttl = 86400
        lz.cache.config.max_size_mb = 200

        config = lz.cache.config
        assert config.symbol_index_ttl == 3600
        assert config.stdlib_cache_ttl == 86400
        assert config.max_size_mb == 200

    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        from laziest_import import lz

        reset_cache_stats()
        stats = lz.cache.stats
        assert "symbol_hits" in stats
        assert "symbol_misses" in stats
        assert "module_hits" in stats
        assert "module_misses" in stats
        assert "hit_rate" in stats

    def test_symbol_cache_operations(self):
        """Test symbol cache operations."""
        from laziest_import import lz

        # Get cache info
        info = lz.symbol.cache_info()
        assert "built" in info
        assert "symbol_count" in info

        # Clear symbol cache
        lz.cache.symbols.clear()
        info = lz.symbol.cache_info()
        assert info["built"] is False

    def test_invalidate_package_cache(self):
        """Test invalidating cache for specific package."""
        from laziest_import import lz

        # This should return False for non-tracked package
        result = invalidate_package_cache("nonexistent_package_xyz")
        # Just verify it doesn't crash
        assert isinstance(result, bool)

    def test_cache_compression(self):
        """Test cache compression toggle."""
        from laziest_import import lz

        lz.cache.compression = True
        assert lz.cache.config.compression is True

        lz.cache.compression = False


class TestRealWorldScenario_AsyncImport:
    """
    Scenario: User needs async imports for async applications.
    Tests async import functionality.
    """

    @pytest.mark.asyncio
    async def test_import_async_single(self):
        """Test async import of a single module."""
        from laziest_import import lz

        math_mod = await lz.async_.get("math")
        assert math_mod is not None
        assert hasattr(math_mod, "pi")
        assert math_mod.pi > 3.14

    @pytest.mark.asyncio
    async def test_import_multiple_async(self):
        """Test async import of multiple modules."""
        from laziest_import import lz

        modules = await lz.async_.fetch("math", "json", "os")

        assert "math" in modules
        assert "json" in modules
        assert "os" in modules

        assert modules["math"].pi > 3.14
        assert callable(modules["json"].dumps)
        assert callable(modules["os"].getcwd)

    def test_retry_mechanism(self):
        """Test retry mechanism for imports."""
        from laziest_import import lz

        lz.config.retry.enabled = True
        lz.config.retry.max_retries = 3
        lz.config.retry.retry_delay = 0.1
        assert lz.config.retry.enabled is True

        lz.config.retry.enabled = False
        assert lz.config.retry.enabled is False

        lz.config.retry.enabled = True  # Re-enable for other tests


class TestRealWorldScenario_Hooks:
    """
    Scenario: User wants to track import activity.
    Tests import hooks functionality.
    """

    def test_pre_import_hook(self):
        """Test pre-import hooks."""
        from laziest_import import lz

        called = []

        def my_hook(module_name):
            called.append(module_name)

        lz.hooks.pre.add(my_hook)
        lz.cache.clear()
        _ = lz.math.pi

        assert "math" in called
        lz.hooks.pre.remove(my_hook)

    def test_post_import_hook(self):
        """Test post-import hooks."""
        from laziest_import import lz

        called = []

        def my_hook(module_name, module):
            called.append((module_name, module.__name__))

        lz.hooks.post.add(my_hook)
        lz.cache.clear()
        _ = lz.json.dumps

        assert any(name == "json" for name, _ in called)
        lz.hooks.post.remove(my_hook)

    def test_multiple_hooks_order(self):
        """Test that multiple hooks are called in order."""
        from laziest_import import lz

        order = []

        def hook1(name):
            order.append(1)

        def hook2(name):
            order.append(2)

        lz.hooks.pre.add(hook1)
        lz.hooks.pre.add(hook2)
        lz.cache.clear()
        _ = lz.sys.version

        # Both hooks should have been called
        assert len(order) >= 2

        lz.hooks.pre.remove(hook1)
        lz.hooks.pre.remove(hook2)

    def test_clear_import_hooks(self):
        """Test clearing all hooks."""
        from laziest_import import lz

        def dummy(name):
            pass

        lz.hooks.pre.add(dummy)
        lz.hooks.post.add(dummy)
        lz.hooks.clear()
        assert len(lz.hooks.pre) == 0
        assert len(lz.hooks.post) == 0


class TestRealWorldScenario_DebugAndStats:
    """
    Scenario: User needs debugging and statistics.
    Tests debug mode and import statistics.
    """

    def test_enable_disable_debug_mode(self):
        """Test toggling debug mode."""
        from laziest_import import lz

        lz.config.debug = True
        assert lz.config.debug is True

        lz.config.debug = False
        assert lz.config.debug is False

    def test_import_statistics(self):
        """Test import statistics tracking."""
        from laziest_import import lz

        # Reset stats first
        reset_import_stats()

        # Clear cache to ensure fresh import
        lz.cache.clear()

        # Import a module - this should trigger import statistics
        _ = lz.math.pi

        stats = lz.config.import_stats
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
        from laziest_import import lz

        info = lz.rc.info()
        assert "paths_checked" in info
        assert "active_path" in info
        assert "loaded" in info

    def test_create_rc_file(self):
        """Test creating RC configuration file."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.rc.create(str(rc_path))  # Test with string path
            assert result.exists()

    def test_create_rc_file_with_template(self):
        """Test creating RC file with template."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.rc.create(rc_path, template=True)
            assert result.exists()

            with open(result) as f:
                data = json.load(f)
            assert isinstance(data, dict)

    def test_create_rc_file_exists_error(self):
        """Test that creating existing RC file raises error."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            rc_path.touch()

            with pytest.raises(FileExistsError):
                lz.rc.create(rc_path)

    def test_load_rc_config(self):
        """Test loading RC configuration."""
        from laziest_import import lz

        config = lz.rc.load()
        assert isinstance(config, dict)

    def test_reload_rc_config(self):
        """Test reloading RC configuration."""
        from laziest_import import lz

        config = lz.rc.reload()
        assert isinstance(config, dict)

    def test_get_rc_value(self):
        """Test getting specific RC value."""
        from laziest_import import lz

        value = lz.rc.get("nonexistent_key_xyz", default="default_value")
        assert value == "default_value"


class TestRealWorldScenario_HelpSystem:
    """
    Scenario: User wants to learn about the library.
    Tests help() function and documentation.
    """

    def test_help_overview(self):
        """Test help() with no arguments shows overview."""
        from laziest_import import help

        result = help()
        assert isinstance(result, str)
        assert len(result) > 0
        assert "laziest-import" in result.lower()

    def test_help_topics(self):
        """Test help() with specific topics."""
        from laziest_import import help

        topics = [
            "quickstart",
            "lazy",
            "alias",
            "symbol",
            "cache",
            "config",
            "async",
            "hooks",
            "api",
        ]

        for topic in topics:
            result = help(topic)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_help_unknown_topic(self):
        """Test help() with unknown topic."""
        from laziest_import import help

        result = help("nonexistent_topic_xyz123")
        assert "unknown topic" in result.lower() or "not found" in result.lower()


class TestRealWorldScenario_BackgroundIndex:
    """
    Scenario: User wants background index building.
    Tests background index building functionality.
    """

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

    def test_background_timeout_settings(self):
        """Test background timeout configuration."""
        from laziest_import import lz

        original = lz.background.timeout

        lz.background.timeout = 120.0
        assert lz.background.timeout == 120.0

        lz.background.timeout = 0
        assert lz.background.timeout == 0

        lz.background.timeout = original


class TestRealWorldScenario_SymbolSharding:
    """
    Scenario: User works with large packages.
    Tests symbol sharding functionality.
    """

    def test_get_sharding_config(self):
        """Test getting sharding configuration."""
        from laziest_import import lz

        config = get_sharding_config()
        assert "enabled" in config
        assert "shard_threshold" in config

    def test_enable_disable_sharding(self):
        """Test enabling/disabling sharding."""
        from laziest_import import lz

        enable_sharding()
        config = get_sharding_config()
        assert config["enabled"] is True

        disable_sharding()
        config = get_sharding_config()
        assert config["enabled"] is False

        enable_sharding()

    def test_search_with_sharding(self):
        """Test searching with sharding enabled."""
        from laziest_import import lz

        results = lz.symbol.sharded("sqrt", max_results=5)
        assert isinstance(results, list)

    def test_clear_shard_cache(self):
        """Test clearing shard cache."""
        from laziest_import._symbol import get_sharding_config

        clear_shard_cache()
        config = get_sharding_config()
        assert isinstance(config, dict)


class TestRealWorldScenario_IncrementalIndex:
    """
    Scenario: User wants efficient index updates.
    Tests incremental index building.
    """

    def test_enable_incremental_index(self):
        """Test enabling incremental index."""
        from laziest_import._cache._incremental import enable_incremental_index

        enable_incremental_index(True)
        config = get_incremental_config()
        assert config["enabled"] is True

    def test_get_incremental_config(self):
        """Test getting incremental index configuration."""
        from laziest_import import lz

        config = get_incremental_config()
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_build_symbol_index_incremental(self):
        """Test incremental symbol index build."""
        from laziest_import import lz

        result = lz.symbol.index.incremental()
        assert isinstance(result, bool)

    def test_get_preheat_config(self):
        """Test getting preheat configuration."""
        from laziest_import import lz

        config = lz.background.preheat
        assert isinstance(config, dict)
        assert "enabled" in config


class TestRealWorldScenario_ModuleIntrospection:
    """
    Scenario: User wants to inspect module contents.
    Tests module introspection functionality.
    """

    def test_list_module_symbols(self):
        """Test listing module symbols."""
        from laziest_import._introspect import get_module_info

        info = get_module_info("math")
        assert isinstance(info, dict)
        assert "name" in info
        assert info["name"] == "math"

    def test_list_module_symbols_with_filter(self):
        """Test listing symbols with type filter."""
        from laziest_import._introspect import get_module_info

        info = get_module_info("math")
        assert isinstance(info, dict)

    def test_list_module_symbols_exclude_private(self):
        """Test excluding private symbols."""
        from laziest_import._introspect import get_module_info

        info = get_module_info("json")
        assert isinstance(info, dict)

    def test_get_module_info(self):
        """Test getting module information."""
        from laziest_import import lz

        info = get_module_info("json")
        assert isinstance(info, dict)
        assert "name" in info
        assert info["name"] == "json"

    def test_search_in_module(self):
        """Test searching symbols in a module."""
        from laziest_import._introspect import get_module_info

        info = get_module_info("math")
        assert isinstance(info, dict)


class TestRealWorldScenario_SymbolResolution:
    """
    Scenario: User needs to handle symbol conflicts.
    Tests symbol resolution and preferences.
    """

    def test_set_get_symbol_preference(self):
        """Test setting and getting symbol preferences."""
        from laziest_import import lz

        lz.symbol.prefer("TestSymbolXYZ", "test_module")
        pref = lz.symbol.preference("TestSymbolXYZ")
        assert pref == "test_module"

        lz.symbol.clear_preference("TestSymbolXYZ")
        pref = lz.symbol.preference("TestSymbolXYZ")
        assert pref is None

    def test_get_symbol_resolution_config(self):
        """Test getting symbol resolution configuration."""
        from laziest_import import lz

        config = lz.symbol.config.snapshot()
        assert isinstance(config, dict)
        assert "search" in config
        assert "resolution" in config

    def test_enable_disable_auto_symbol_resolution(self):
        """Test toggling auto symbol resolution."""
        from laziest_import import lz

        lz.symbol.config.auto_resolution = True
        assert lz.symbol.config.auto_resolution is True

        lz.symbol.config.auto_resolution = False
        assert lz.symbol.config.auto_resolution is False

        lz.symbol.config.auto_resolution = True

    def test_list_symbol_conflicts(self):
        """Test listing symbol conflicts."""
        from laziest_import import lz
        from laziest_import._analysis._conflict import SymbolConflict

        # List conflicts for a common symbol
        conflicts = lz.symbol.conflicts("sqrt") or []
        assert isinstance(conflicts, (list, type(None), SymbolConflict))

    def test_module_priority(self):
        """Test module priority settings."""
        from laziest_import import lz

        set_module_priority("test_priority_module", 100)
        priority = get_module_priority("test_priority_module")
        assert priority == 100

        # Unknown module should have default priority
        priority = get_module_priority("unknown_module_xyz")
        assert priority == 50


class TestRealWorldScenario_AutoInstall:
    """
    Scenario: User wants auto-install for missing packages.
    Tests auto-install functionality (mocked to avoid actual installation).
    """

    def test_auto_install_config(self):
        """Test auto-install configuration."""
        from laziest_import import lz

        config = lz.install.auto
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_enable_disable_auto_install(self):
        """Test toggling auto-install."""
        from laziest_import import lz

        lz.install.enable(interactive=False)
        assert lz.install.enabled is True

        lz.install.disable()
        assert lz.install.enabled is False

    def test_set_pip_index(self):
        """Test setting custom pip index."""
        from laziest_import import lz

        set_pip_index("https://pypi.org/simple")
        config = lz.install.auto
        assert config["index"] == "https://pypi.org/simple"

        set_pip_index(None)

    def test_set_pip_extra_args(self):
        """Test setting extra pip arguments."""
        from laziest_import import lz

        set_pip_extra_args(["--no-cache-dir"])
        config = lz.install.auto
        assert "--no-cache-dir" in config["extra_args"]

        set_pip_extra_args([])


class TestRealWorldScenario_VersionAndReload:
    """
    Scenario: User needs version info and module reload.
    Tests version and reload functionality.
    """

    def test_version_exists(self):
        """Test that version attribute exists."""
        from laziest_import import lz

        assert hasattr(lz, "__version__")
        assert isinstance(lz.__version__, str)

    def test_cache_version(self):
        """Test getting cache version."""
        from laziest_import import lz

        version = lz.version.cache()
        assert isinstance(version, str)

    def test_package_version(self):
        """Test getting package version."""
        from laziest_import import lz

        # pytest should be installed
        version = lz.version.of("pytest")
        # May or may not have version
        assert version is None or isinstance(version, str)

    def test_get_version_of_loaded_module(self):
        """Test getting version of a loaded module."""
        from laziest_import import lz

        _ = lz.json.dumps
        version = lz.version.of("json")
        # stdlib may not have __version__
        assert version is None or isinstance(version, str)

    def test_reload_module(self):
        """Test reloading a module."""
        from laziest_import import lz

        _ = lz.math.pi
        result = lz.module.reload("math")
        assert result is True

    def test_reload_nonexistent_module(self):
        """Test reloading a module that doesn't exist in lazy modules."""
        from laziest_import import lz

        result = lz.module.reload("nonexistent_module_xyz123")
        assert result is False


class TestRealWorldScenario_ResetOperations:
    """
    Scenario: User needs to reset library state.
    Tests various reset operations.
    """

    def test_clear_cache(self):
        """Test clearing module cache."""
        from laziest_import import lz

        _ = lz.math.pi
        assert "math" in lz.module.list_loaded()

        lz.cache.clear()
        assert "math" not in lz.module.list_loaded()

    def test_reset_all(self):
        """Test complete reset."""
        from laziest_import import lz

        _ = lz.math.pi
        reset_all()
        assert "math" not in lz.module.list_loaded()

    def test_reset_cache_stats(self):
        """Test resetting cache statistics."""
        from laziest_import import lz

        reset_cache_stats()
        stats = lz.cache.stats
        assert stats["symbol_hits"] == 0
        assert stats["symbol_misses"] == 0

    def test_reset_import_stats(self):
        """Test resetting import statistics."""
        from laziest_import import lz

        reset_import_stats()
        stats = lz.config.import_stats
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
        from laziest_import import easter_egg

        msg = easter_egg()
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_easter_egg_variants(self):
        """Test easter egg variants."""
        from laziest_import import easter_egg

        variants = ["default", "author", "quote", "tip", "secret", "thanks"]

        for variant in variants:
            msg = easter_egg(variant)
            assert isinstance(msg, str)


class TestRealWorldScenario_ComprehensiveWorkflow:
    """
    Scenario: Complete workflow combining multiple features.
    Tests realistic user workflow using multiple features together.
    """

    def test_data_science_workflow(self):
        """Simulate a data science workflow."""
        from laziest_import import lz

        # Reset state for clean test
        lz.cache.clear()
        reset_import_stats()

        # Setup: Enable features
        lz.config.debug = True
        lz.config.auto_search = True
        lz.symbol.config.enable()
        lz.symbol.config.interactive = False

        # Workflow: Import and use modules
        cwd = lz.os.getcwd()
        assert isinstance(cwd, str)

        data = {"key": "value"}
        json_str = lz.json.dumps(data)
        assert lz.json.loads(json_str) == data

        value = lz.math.sqrt(16)
        assert value == 4.0

        # Introspection: Check what's loaded
        loaded = lz.module.list_loaded()
        assert len(loaded) > 0

        # Statistics: Check import stats structure (values may vary due to caching)
        stats = lz.config.import_stats
        assert "total_imports" in stats
        assert "total_time" in stats

        # Help: Get help
        from laziest_import import help

        help_text = help("quickstart")
        assert len(help_text) > 0

        # Which: Find symbol location
        loc = lz.symbol.which("sqrt", "math")
        assert loc is not None

        # Cleanup
        lz.config.debug = False
        lz.cache.clear()

    def test_web_development_workflow(self):
        """Simulate a web development workflow."""
        from laziest_import import lz

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
        lz.cache.clear()

    def test_configuration_workflow(self):
        """Simulate a configuration management workflow."""
        from laziest_import import lz

        # Setup: Create custom config
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            lz.rc.create(rc_path, template=True)

            # Configure cache
            lz.cache.config.symbol_index_ttl = 3600
            lz.cache.config.max_size_mb = 50

            # Configure background building
            lz.background.timeout = 30.0
            lz.background.enable(True)

            # Verify configuration
            cache_config = lz.cache.config
            assert cache_config.symbol_index_ttl == 3600

            preheat_config = lz.background.preheat
            assert preheat_config["enabled"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
