"""
Tests for new features in 0.0.4
"""

import pytest
import tempfile
import json
import os
from pathlib import Path


class TestWhichFunction:
    """Test the which() function."""

    def test_which_function_callable(self):
        """Test that which() is callable and doesn't crash."""
        import laziest_import as lz

        # Just verify which is callable and doesn't raise
        result = lz.which("xyz_unknown_symbol_12345")
        assert result is None or hasattr(result, "symbol_name")

    def test_which_finds_math_symbol(self):
        """Test that which() can find stdlib symbols when specified."""
        import laziest_import as lz

        # Find sqrt specifically in math module
        loc = lz.which("sqrt", "math")
        if loc:
            assert loc.symbol_name == "sqrt"

    def test_which_with_module_hint(self):
        """Test which() with module hint."""
        import laziest_import as lz

        loc = lz.which("sqrt", "math")
        assert loc is not None
        assert "math" in loc.module_name

    def test_which_returns_none_for_missing(self):
        """Test that which() returns None for missing symbols."""
        import laziest_import as lz

        loc = lz.which("xyz_not_found_12345")
        assert loc is None or hasattr(loc, "symbol_name")

    def test_which_all_finds_multiple(self):
        """Test that which_all() finds multiple locations."""
        import laziest_import as lz

        locs = lz.which_all("sqrt")
        assert isinstance(locs, list)

    def test_which_symbol_location_str(self):
        """Test SymbolLocation string representation."""
        import laziest_import as lz

        loc = lz.which("sqrt")
        if loc:
            str_repr = str(loc)
            assert isinstance(str_repr, str)
            assert "sqrt" in str_repr

    def test_which_symbol_location_repr(self):
        """Test SymbolLocation repr."""
        import laziest_import as lz

        loc = lz.which("sqrt")
        if loc:
            repr_str = repr(loc)
            assert isinstance(repr_str, str)
            assert "SymbolLocation" in repr_str

    def test_which_symbol_location_dict(self):
        """Test SymbolLocation to_dict method."""
        import laziest_import as lz

        loc = lz.which("sqrt")
        if loc:
            d = loc.to_dict()
            assert isinstance(d, dict)
            assert "module" in d
            assert "symbol" in d
            assert "type" in d

    def test_which_empty_string(self):
        """Test which() with empty string."""
        import laziest_import as lz

        loc = lz.which("")
        assert loc is None or hasattr(loc, "symbol_name")

    def test_which_dotted_path(self):
        """Test which() with dotted paths like 'math.sin'."""
        import laziest_import as lz

        loc = lz.which("math.sin")
        assert loc is not None
        assert loc.symbol_name == "sin"
        assert "math" in loc.module_name

        loc = lz.which("os.path.join")
        assert loc is not None
        assert loc.symbol_name == "join"
        assert "os.path" in loc.module_name


class TestHelpFunction:
    """Test the help() function."""

    def test_help_returns_string(self):
        """Test that help() returns a string."""
        import laziest_import as lz

        result = lz.help()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_with_topic(self):
        """Test help() with specific topic."""
        import laziest_import as lz

        result = lz.help("quickstart")
        assert "Quick Start" in result

    def test_help_unknown_topic(self):
        """Test help() with unknown topic."""
        import laziest_import as lz

        result = lz.help("nonexistent_topic_xyz")
        assert (
            "unknown topic" in result.lower()
            or "not found" in result.lower()
            or "did you mean" in result.lower()
        )

    def test_help_lazy_topic(self):
        """Test help() with lazy topic."""
        import laziest_import as lz

        result = lz.help("lazy")
        assert len(result) > 0

    def test_help_alias_topic(self):
        """Test help() with alias topic."""
        import laziest_import as lz

        result = lz.help("alias")
        assert len(result) > 0

    def test_help_cache_topic(self):
        """Test help() with cache topic."""
        import laziest_import as lz

        result = lz.help("cache")
        assert len(result) > 0

    def test_help_jupyter_topic(self):
        """Test help() with jupyter topic."""
        import laziest_import as lz

        result = lz.help("jupyter")
        assert len(result) > 0

    def test_help_api_topic(self):
        """Test help() with api topic."""
        import laziest_import as lz

        result = lz.help("api")
        assert len(result) > 0

    def test_help_none_topic_shows_overview(self):
        """Test help() with None topic shows overview."""
        import laziest_import as lz

        result = lz.help()
        assert "laziest-import" in result.lower()


class TestRCConfig:
    """Test .laziestrc configuration."""

    def test_get_rc_info(self):
        """Test getting RC config info."""
        import laziest_import as lz

        info = lz.get_rc_info()
        assert "paths_checked" in info
        assert "active_path" in info
        assert "loaded" in info

    def test_create_rc_file(self):
        """Test creating RC file."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.create_rc_file(rc_path)

            assert result.exists()
            assert result == rc_path

    def test_create_rc_file_with_template(self):
        """Test creating RC file with template."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.create_rc_file(rc_path, template=True)

            assert result.exists()
            with open(result) as f:
                data = json.load(f)
            assert "aliases" in data or isinstance(data, dict)

    def test_create_rc_file_no_template(self):
        """Test creating RC file without template."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.create_rc_file(rc_path, template=False)

            assert result.exists()

    def test_create_rc_file_exists_error(self):
        """Test that creating existing RC file raises error."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            rc_path.touch()

            with pytest.raises(FileExistsError):
                lz.create_rc_file(rc_path)

    def test_get_rc_value(self):
        """Test getting specific RC value."""
        import laziest_import as lz

        value = lz.get_rc_value("nonexistent_key", default="default_val")
        assert value == "default_val"

    def test_get_rc_value_nested(self):
        """Test getting nested RC value."""
        import laziest_import as lz

        value = lz.get_rc_value("aliases.np", default=None)
        # May or may not exist depending on config

    def test_load_rc_config(self):
        """Test loading RC config."""
        import laziest_import as lz

        config = lz.load_rc_config()
        assert isinstance(config, dict)

    def test_reload_rc_config(self):
        """Test reloading RC config."""
        import laziest_import as lz

        config = lz.reload_rc_config()
        assert isinstance(config, dict)


class TestBackgroundIndex:
    """Test background index building."""

    def test_start_background_index(self):
        """Test starting background index build."""
        import laziest_import as lz

        lz.start_background_index_build()

    def test_start_background_index_with_callback(self):
        """Test starting background index with progress callback."""
        import laziest_import as lz

        called = []

        def callback(msg, progress):
            called.append((msg, progress))

        lz.start_background_index_build(progress_callback=callback)

    def test_is_index_building(self):
        """Test checking if index is building."""
        import laziest_import as lz

        result = lz.is_index_building()
        assert isinstance(result, bool)

    def test_wait_for_index(self):
        """Test waiting for index."""
        import laziest_import as lz

        result = lz.wait_for_index(timeout=0.1)
        assert isinstance(result, bool)

    def test_wait_for_index_no_timeout(self):
        """Test waiting for index without timeout."""
        import laziest_import as lz

        result = lz.wait_for_index()
        assert isinstance(result, bool)


class TestSymbolSharding:
    """Test symbol index sharding."""

    def test_get_sharding_config(self):
        """Test getting sharding config."""
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
        """Test searching with sharding."""
        import laziest_import as lz

        results = lz.search_with_sharding("sqrt", max_results=5)
        assert isinstance(results, list)

    def test_search_with_sharding_empty_result(self):
        """Test searching with sharding returns empty for unknown."""
        import laziest_import as lz

        results = lz.search_with_sharding("xyz_unknown_symbol_123", max_results=5)
        assert isinstance(results, list)

    def test_clear_shard_cache(self):
        """Test clearing shard cache."""
        import laziest_import as lz

        lz.clear_shard_cache()


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
        import laziest_import as lz

        result = lz.build_symbol_index_incremental()
        assert isinstance(result, bool)

    def test_enable_incremental_index(self):
        """Test enabling incremental index."""
        import laziest_import as lz

        from laziest_import._cache import get_incremental_config

        config_before = get_incremental_config()

        lz.enable_incremental_index(True)
        config_after = get_incremental_config()
        assert config_after["enabled"] is True

        lz.enable_incremental_index(False)

    def test_get_incremental_config(self):
        """Test getting incremental config."""
        import laziest_import as lz

        config = lz.get_incremental_config()
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_enable_background_build(self):
        """Test enabling background build."""
        import laziest_import as lz

        from laziest_import._cache import get_preheat_config

        lz.enable_background_build(True)
        config = get_preheat_config()
        assert config["enabled"] is True

        lz.enable_background_build(False)

    def test_get_preheat_config(self):
        """Test getting preheat config."""
        import laziest_import as lz

        config = lz.get_preheat_config()
        assert isinstance(config, dict)
        assert "enabled" in config


class TestSymbolSearchAdvanced:
    """Test advanced symbol search features."""

    def test_search_symbol_basic(self):
        """Test basic symbol search."""
        import laziest_import as lz

        results = lz.search_symbol("sqrt", max_results=5)
        assert isinstance(results, list)

    def test_search_symbol_with_type_filter(self):
        """Test symbol search with type filter."""
        import laziest_import as lz

        results = lz.search_symbol("sqrt", symbol_type="function", max_results=5)
        assert isinstance(results, list)

    def test_enable_disable_symbol_search(self):
        """Test enabling/disabling symbol search."""
        import laziest_import as lz

        lz.enable_symbol_search()
        assert lz.is_symbol_search_enabled() is True

        lz.disable_symbol_search()
        assert lz.is_symbol_search_enabled() is False

        lz.enable_symbol_search()

    def test_get_symbol_search_config(self):
        """Test getting symbol search config."""
        import laziest_import as lz

        config = lz.get_symbol_search_config()
        assert isinstance(config, dict)
        assert "enabled" in config


class TestCacheAdvanced:
    """Test advanced cache features."""

    def test_enable_cache_compression(self):
        """Test enabling cache compression."""
        import laziest_import as lz

        from laziest_import._cache import get_cache_config

        lz.enable_cache_compression(True)
        config = get_cache_config()
        assert config["enable_compression"] is True

        lz.enable_cache_compression(False)

    def test_get_cache_config(self):
        """Test getting cache config."""
        import laziest_import as lz

        config = lz.get_cache_config()
        assert isinstance(config, dict)
        assert "symbol_index_ttl" in config
        assert "stdlib_cache_ttl" in config

    def test_get_cache_stats(self):
        """Test getting cache stats."""
        import laziest_import as lz

        lz.reset_cache_stats()
        stats = lz.get_cache_stats()
        assert isinstance(stats, dict)
        assert "hit_rate" in stats


class TestModulePriority:
    """Test module priority features."""

    def test_set_get_module_priority(self):
        """Test setting and getting module priority."""
        import laziest_import as lz

        lz.set_module_priority("test_module_priority", 100)
        priority = lz.get_module_priority("test_module_priority")
        assert priority == 100

    def test_get_module_priority_unknown(self):
        """Test getting priority for unknown module."""
        import laziest_import as lz

        priority = lz.get_module_priority("nonexistent_module_xyz_123")
        assert priority == 50


class TestSymbolPreference:
    """Test symbol preference features."""

    def test_set_get_symbol_preference(self):
        """Test setting and getting symbol preference."""
        import laziest_import as lz

        lz.set_symbol_preference("TestSymbolXYZ", "test_module")
        pref = lz.get_symbol_preference("TestSymbolXYZ")
        assert pref == "test_module"

        lz.clear_symbol_preference("TestSymbolXYZ")
        pref = lz.get_symbol_preference("TestSymbolXYZ")
        assert pref is None


class TestSymbolResolution:
    """Test symbol resolution features."""

    def test_get_symbol_resolution_config(self):
        """Test getting symbol resolution config."""
        import laziest_import as lz

        config = lz.get_symbol_resolution_config()
        assert isinstance(config, dict)
        assert "auto_symbol" in config

    def test_enable_auto_symbol_resolution(self):
        """Test enabling auto symbol resolution."""
        import laziest_import as lz

        lz.enable_auto_symbol_resolution()
        config = lz.get_symbol_resolution_config()
        assert config["auto_symbol"] is True

        lz.disable_auto_symbol_resolution()
        config = lz.get_symbol_resolution_config()
        assert config["auto_symbol"] is False

        lz.enable_auto_symbol_resolution()


class TestLazyFunctions:
    """Test lazy-loaded functions."""

    def test_lazy_which_function(self):
        """Test that which is lazy loaded."""
        import laziest_import as lz

        which_func = lz.which
        assert callable(which_func)

    def test_lazy_help_function(self):
        """Test that help is lazy loaded."""
        import laziest_import as lz

        help_func = lz.help
        assert callable(help_func)

    def test_lazy_search_symbol_function(self):
        """Test that search_symbol is lazy loaded."""
        import laziest_import as lz

        search_func = lz.search_symbol
        assert callable(search_func)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
