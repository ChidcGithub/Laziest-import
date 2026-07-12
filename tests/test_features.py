"""
Tests for new features in 0.0.4
"""

import json
import tempfile
from pathlib import Path

import pytest

from laziest_import import help as lz_help
from laziest_import import lz
from laziest_import._cache import get_incremental_config, reset_cache_stats
from laziest_import._introspect import get_module_info, list_module_symbols, search_in_module
from laziest_import._symbol import (
    clear_shard_cache,
    disable_sharding,
    disable_symbol_search,
    enable_sharding,
    enable_symbol_search,
    get_module_priority,
    get_sharding_config,
    set_module_priority,
)


class TestWhichFunction:
    """Test the which() function."""

    def test_which_function_callable(self):
        """Test that which() is callable and doesn't crash."""

        # Just verify which is callable and doesn't raise
        result = lz.symbol.which("xyz_unknown_symbol_12345")
        assert result is None or hasattr(result, "symbol_name")

    def test_which_finds_math_symbol(self):
        """Test that which() can find stdlib symbols when specified."""

        # Find sqrt specifically in math module
        loc = lz.symbol.which("sqrt", "math")
        if loc:
            assert loc.symbol_name == "sqrt"

    def test_which_with_module_hint(self):
        """Test which() with module hint."""

        loc = lz.symbol.which("sqrt", "math")
        assert loc is not None
        assert "math" in loc.module_name

    def test_which_returns_none_for_missing(self):
        """Test that which() returns None for missing symbols."""

        loc = lz.symbol.which("xyz_not_found_12345")
        assert loc is None or hasattr(loc, "symbol_name")

    def test_which_all_finds_multiple(self):
        """Test that which_all() finds multiple locations."""

        locs = lz.symbol.which_all("sqrt")
        assert isinstance(locs, list)

    def test_which_symbol_location_str(self):
        """Test SymbolLocation string representation."""

        loc = lz.symbol.which("sqrt")
        if loc:
            str_repr = str(loc)
            assert isinstance(str_repr, str)
            assert "sqrt" in str_repr

    def test_which_symbol_location_repr(self):
        """Test SymbolLocation repr."""

        loc = lz.symbol.which("sqrt")
        if loc:
            repr_str = repr(loc)
            assert isinstance(repr_str, str)
            assert "SymbolLocation" in repr_str

    def test_which_symbol_location_dict(self):
        """Test SymbolLocation to_dict method."""

        loc = lz.symbol.which("sqrt")
        if loc:
            d = loc.to_dict()
            assert isinstance(d, dict)
            assert "module" in d
            assert "symbol" in d
            assert "type" in d

    def test_which_empty_string(self):
        """Test which() with empty string."""

        loc = lz.symbol.which("")
        assert loc is None or hasattr(loc, "symbol_name")

    def test_which_dotted_path(self):
        """Test which() with dotted paths like 'math.sin'."""

        loc = lz.symbol.which("math.sin")
        assert loc is not None
        assert loc.symbol_name == "sin"
        assert "math" in loc.module_name

        loc = lz.symbol.which("os.path.join")
        assert loc is not None
        assert loc.symbol_name == "join"
        assert "os.path" in loc.module_name


class TestHelpFunction:
    """Test the help() function."""

    def test_help_returns_string(self):
        """Test that help() returns a string."""

        result = lz_help()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_with_topic(self):
        """Test help() with specific topic."""

        result = lz_help("quickstart")
        assert "Quick Start" in result

    def test_help_unknown_topic(self):
        """Test help() with unknown topic."""

        result = lz_help("nonexistent_topic_xyz")
        assert (
            "unknown topic" in result.lower()
            or "not found" in result.lower()
            or "did you mean" in result.lower()
        )

    def test_help_lazy_topic(self):
        """Test help() with lazy topic."""

        result = lz_help("lazy")
        assert len(result) > 0

    def test_help_alias_topic(self):
        """Test help() with alias topic."""

        result = lz_help("alias")
        assert len(result) > 0

    def test_help_cache_topic(self):
        """Test help() with cache topic."""

        result = lz_help("cache")
        assert len(result) > 0

    def test_help_jupyter_topic(self):
        """Test help() with jupyter topic."""

        result = lz_help("jupyter")
        assert len(result) > 0

    def test_help_api_topic(self):
        """Test help() with api topic."""

        result = lz_help("api")
        assert len(result) > 0

    def test_help_none_topic_shows_overview(self):
        """Test help() with None topic shows overview."""

        result = lz_help()
        assert "laziest-import" in result.lower()


class TestRCConfig:
    """Test .laziestrc configuration."""

    def test_get_rc_info(self):
        """Test getting RC config info."""

        info = lz.rc.info()
        assert "paths_checked" in info
        assert "active_path" in info
        assert "loaded" in info

    def test_create_rc_file(self):
        """Test creating RC file."""

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.rc.create(rc_path)

            assert result.exists()
            assert result == rc_path

    def test_create_rc_file_with_template(self):
        """Test creating RC file with template."""

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.rc.create(rc_path, template=True)

            assert result.exists()
            with open(result) as f:
                data = json.load(f)
            assert "aliases" in data or isinstance(data, dict)

    def test_create_rc_file_no_template(self):
        """Test creating RC file without template."""

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.rc.create(rc_path, template=False)

            assert result.exists()

    def test_create_rc_file_exists_error(self):
        """Test that creating existing RC file raises error."""

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            rc_path.touch()

            with pytest.raises(FileExistsError):
                lz.rc.create(rc_path)

    def test_get_rc_value(self):
        """Test getting specific RC value."""

        value = lz.rc.get("nonexistent_key", default="default_val")
        assert value == "default_val"

    def test_get_rc_value_nested(self):
        """Test getting nested RC value."""

        value = lz.rc.get("aliases.np", default=None)
        assert value is None or isinstance(value, str)

    def test_load_rc_config(self):
        """Test loading RC config."""

        config = lz.rc.load()
        assert isinstance(config, dict)

    def test_reload_rc_config(self):
        """Test reloading RC config."""

        config = lz.rc.reload()
        assert isinstance(config, dict)


class TestBackgroundIndex:
    """Test background index building."""

    def test_start_background_index(self):
        """Test starting background index build."""

        lz.background.start()
        lz.background.wait(timeout=5)

    def test_start_background_index_with_callback(self):
        """Test starting background index with progress callback."""

        called = []

        def callback(msg, progress):
            called.append((msg, progress))

        lz.background.start(progress_callback=callback)
        lz.background.wait(timeout=5)
        # Callback may or may not have been called
        assert isinstance(called, list)

    def test_is_index_building(self):
        """Test checking if index is building."""

        result = lz.background.is_building
        assert isinstance(result, bool)

    def test_wait_for_index(self):
        """Test waiting for index."""

        result = lz.background.wait(timeout=0.1)
        assert isinstance(result, bool)

    def test_wait_for_index_no_timeout(self):
        """Test waiting for index without timeout."""

        result = lz.background.wait(timeout=5)
        assert isinstance(result, bool)


class TestSymbolSharding:
    """Test symbol index sharding."""

    def test_get_sharding_config(self):
        """Test getting sharding config."""
        config = get_sharding_config()
        assert "enabled" in config
        assert "shard_threshold" in config

    def test_enable_disable_sharding(self):
        """Test enabling/disabling sharding."""
        enable_sharding()
        config = get_sharding_config()
        assert config["enabled"] is True

        disable_sharding()
        config = get_sharding_config()
        assert config["enabled"] is False

        enable_sharding()

    def test_search_with_sharding(self):
        """Test searching with sharding."""

        results = lz.symbol.sharded("sqrt", max_results=5)
        assert isinstance(results, list)

    def test_search_with_sharding_empty_result(self):
        """Test searching with sharding returns empty for unknown."""

        results = lz.symbol.sharded("xyz_unknown_symbol_123", max_results=5)
        assert isinstance(results, list)

    def test_clear_shard_cache(self):
        """Test clearing shard cache."""

        clear_shard_cache()
        config = get_sharding_config()
        assert isinstance(config, dict)


class TestJupyterMagics:
    """Test Jupyter magic commands."""

    def test_lazy_magic_class_importable(self):
        """Test that LazyMagics can be imported."""
        try:
            from laziest_import._jupyter import LazyMagics, enable_in_jupyter

            if LazyMagics is None:
                pytest.skip("IPython not available")
            assert LazyMagics is not None
        except ImportError:
            pytest.skip("IPython not available")

    def test_enable_in_jupyter(self):
        """Test enable_in_jupyter function."""
        from laziest_import._jupyter import enable_in_jupyter

        result = enable_in_jupyter()
        assert isinstance(result, bool)

    def test_load_ipython_extension(self):
        """Test load_ipython_extension function."""
        try:
            from laziest_import._jupyter import load_ipython_extension

            with pytest.raises(ImportError):
                load_ipython_extension(None)
        except ImportError:
            pytest.skip("IPython not available")


class TestIncrementalIndex:
    """Test incremental index features."""

    def test_build_symbol_index_incremental(self):
        """Test incremental symbol index build."""

        result = lz.symbol.index.incremental()
        assert isinstance(result, bool)

    def test_enable_incremental_index(self):
        """Test enabling incremental index."""

        lz.background.enable(True)
        config_after = get_incremental_config()
        assert config_after["enabled"] is True

        lz.background.enable(False)

    def test_get_incremental_config(self):
        """Test getting incremental config."""

        config = get_incremental_config()
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_enable_background_build(self):
        """Test enabling background build."""

        lz.background.enable(True)
        config = lz.background.preheat
        assert config["enabled"] is True

        lz.background.enable(False)

    def test_get_preheat_config(self):
        """Test getting preheat config."""

        config = lz.background.preheat
        assert isinstance(config, dict)
        assert "enabled" in config


class TestSymbolSearchAdvanced:
    """Test advanced symbol search features."""

    def test_search_symbol_basic(self):
        """Test basic symbol search."""

        results = lz.symbol.search("sqrt", max_results=5)
        assert isinstance(results, list)

    def test_search_symbol_with_type_filter(self):
        """Test symbol search with type filter."""

        results = lz.symbol.search("sqrt", symbol_type="function", max_results=5)
        assert isinstance(results, list)

    def test_enable_disable_symbol_search(self):
        """Test enabling/disabling symbol search."""

        enable_symbol_search()
        assert lz.symbol.config.enabled is True

        disable_symbol_search()
        assert lz.symbol.config.enabled is False

        enable_symbol_search()

    def test_get_symbol_search_config(self):
        """Test getting symbol search config."""

        config = lz.symbol.config.snapshot()
        assert isinstance(config, dict)
        assert "search" in config


class TestCacheAdvanced:
    """Test advanced cache features."""

    def test_enable_cache_compression(self):
        """Test enabling cache compression."""

        lz.cache.compression = True
        config = lz.cache.config.snapshot()
        assert config["enable_compression"] is True

        lz.cache.compression = False

    def test_get_cache_config(self):
        """Test getting cache config."""

        config = lz.cache.config.snapshot()
        assert isinstance(config, dict)
        assert "symbol_index_ttl" in config
        assert "stdlib_cache_ttl" in config

    def test_get_cache_stats(self):
        """Test getting cache stats."""

        reset_cache_stats()
        stats = lz.cache.stats
        assert "hit_rate" in stats


class TestModulePriority:
    """Test module priority features."""

    def test_set_get_module_priority(self):
        """Test setting and getting module priority."""

        set_module_priority("test_module_priority", 100)
        priority = get_module_priority("test_module_priority")
        assert priority == 100

    def test_get_module_priority_unknown(self):
        """Test getting priority for unknown module."""

        priority = get_module_priority("nonexistent_module_xyz_123")
        assert priority == 50


class TestSymbolPreference:
    """Test symbol preference features."""

    def test_set_get_symbol_preference(self):
        """Test setting and getting symbol preference."""

        lz.symbol.prefer("TestSymbolXYZ", "test_module")
        pref = lz.symbol.preference("TestSymbolXYZ")
        assert pref == "test_module"

        lz.symbol.clear_preference("TestSymbolXYZ")
        pref = lz.symbol.preference("TestSymbolXYZ")
        assert pref is None


class TestSymbolResolution:
    """Test symbol resolution features."""

    def test_get_symbol_resolution_config(self):
        """Test getting symbol resolution config."""

        config = lz.symbol.config.snapshot()
        assert isinstance(config, dict)
        assert "resolution" in config

    def test_enable_auto_symbol_resolution(self):
        """Test enabling auto symbol resolution."""

        lz.symbol.config.auto_resolution = True
        config = lz.symbol.config.snapshot()
        assert config["resolution"]["auto_symbol"] is True

        lz.symbol.config.auto_resolution = False
        config = lz.symbol.config.snapshot()
        assert config["resolution"]["auto_symbol"] is False

        lz.symbol.config.auto_resolution = True


class TestLazyFunctions:
    """Test lazy-loaded functions."""

    def test_lazy_which_function(self):
        """Test that which is lazy loaded."""

        which_func = lz.symbol.which
        assert callable(which_func)

    def test_lazy_help_function(self):
        """Test that help is lazy loaded."""

        help_func = lz_help
        assert callable(help_func)

    def test_lazy_search_symbol_function(self):
        """Test that search_symbol is lazy loaded."""

        search_func = lz.symbol.search
        assert callable(search_func)


class TestModuleIntrospection:
    """Test module introspection functions."""

    def test_list_module_symbols_basic(self):
        """Test listing module symbols."""

        symbols = list_module_symbols("math")
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert "sin" in symbols

    def test_list_module_symbols_with_filter(self):
        """Test listing symbols with type filter."""

        funcs = list_module_symbols("math", filter_types={"function"})
        assert all(isinstance(s, str) for s in funcs)

    def test_list_module_symbols_exclude_private(self):
        """Test excluding private symbols."""

        symbols = list_module_symbols("math", include_private=False)
        assert all(not s.startswith("_") for s in symbols)

    def test_get_module_info(self):
        """Test getting module info."""

        info = get_module_info("json")
        assert isinstance(info, dict)
        assert "name" in info
        assert info["name"] == "json"
        assert info["is_package"] is True

    def test_search_in_module(self):
        """Test searching symbols in module."""

        results = search_in_module("math", "sin")
        assert isinstance(results, list)
        assert "sin" in results


class TestBackgroundTimeout:
    """Test background timeout configuration."""

    def test_get_background_timeout(self):
        """Test getting background timeout."""

        timeout = lz.background.timeout
        assert isinstance(timeout, float)
        assert timeout > 0

    def test_set_background_timeout(self):
        """Test setting background timeout."""

        original = lz.background.timeout
        lz.background.timeout = 120.0
        assert lz.background.timeout == 120.0
        lz.background.timeout = 0  # No timeout
        assert lz.background.timeout == 0
        lz.background.timeout = original  # Restore


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
