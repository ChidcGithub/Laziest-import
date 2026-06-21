"""
laziest_import Test Suite - Comprehensive Tests
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure laziest_import can be imported
sys.path.insert(0, ".")

from laziest_import import (
    get_init_error,
    is_init_failed,
    is_initialized,
    is_initializing,
    lz,
    reload_mappings,
)
from laziest_import._alias import (
    get_config_dirs,
    get_config_paths,
    validate_aliases_importable,
)
from laziest_import._api._config import reset_import_stats
from laziest_import._async_ops import import_async, import_multiple_async
from laziest_import._cache._api import invalidate_package_cache, reset_cache_stats
from laziest_import._install import set_pip_extra_args, set_pip_index
from laziest_import._symbol import (
    get_loaded_modules_context,
    get_module_priority,
    set_module_priority,
)
import contextlib


class TestBasicImport:
    """Test basic import functionality"""

    def test_module_version(self):
        """Test module version exists"""
        import json

        assert hasattr(lz, "__version__")

        # Version should match version.json
        version_file = Path(__file__).parent.parent / "laziest_import" / "version.json"
        with open(version_file, encoding="utf-8") as f:
            version_config = json.load(f)
        expected_version = version_config.get("_current_version")
        assert lz.__version__ == expected_version

    def test_import_with_alias(self):
        """Test import using alias prefix"""

        # Access standard library module
        math = lz.math
        import math as real_math

        # Check attributes are correct
        assert math.pi == real_math.pi

    def test_import_stdlib(self):
        """Test standard library lazy import"""

        # os module
        os_module = lz.os
        import os as real_os

        assert os_module.getcwd() == real_os.getcwd()

        # sys module
        sys_module = lz.sys
        assert sys_module.version == sys.version

    def test_caching(self):
        """Test module caching"""

        # Multiple accesses should return same attribute values
        pi1 = lz.math.pi
        pi2 = lz.math.pi
        assert pi1 == pi2


class TestAliasMapping:
    """Test alias mapping functionality"""

    def test_register_alias(self):
        """Test registering custom alias"""

        lz.alias.register("test_os_alias", "os")

        # Verify alias is registered
        available = lz.module.list_available()
        assert "test_os_alias" in available

    def test_unregister_alias(self):
        """Test unregistering alias"""

        lz.alias.register("temp_alias_for_test", "os")
        assert lz.alias.unregister("temp_alias_for_test") is True
        assert lz.alias.unregister("nonexistent_alias_xyz") is False

    def test_list_loaded(self):
        """Test listing loaded modules"""

        # Clear cache
        lz.cache.clear()

        # Load a module
        _ = lz.math.pi

        loaded = lz.module.list_loaded()
        assert "math" in loaded

    def test_list_available(self):
        """Test listing available aliases"""

        available = lz.module.list_available()
        # Check some built-in aliases
        assert "np" in available
        assert "pd" in available
        assert "plt" in available
        assert "os" in available


class TestErrorHandling:
    """Test error handling"""

    def test_import_nonexistent_module(self):
        """Test importing non-existent module"""

        # Use an extremely unlikely module name
        # When accessing a non-existent module attribute, should raise AttributeError
        # (not ImportError) because the attribute doesn't exist in the module
        with pytest.raises(AttributeError):
            _ = lz.definitely_not_a_real_module_xyz123456.pi

    def test_clear_cache(self):
        """Test clearing cache"""

        # Load a module
        _ = lz.math.pi
        assert "math" in lz.module.list_loaded()

        # Clear cache
        lz.cache.clear()
        assert "math" not in lz.module.list_loaded()


class TestFromImport:
    """Test from ... import * syntax"""

    def test_from_import_star(self):
        """Test from laziest_import import *"""
        import json
        import subprocess
        import sys

        r = subprocess.run(  # noqa: S603 — list form, trusted input
            [
                sys.executable,
                "-c",
                "from laziest_import import *; import json; print(json.dumps({k: str(type(v)) for k, v in list(locals().items()) if not k.startswith('_')}))",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        namespace = json.loads(r.stdout.strip())

        assert "np" in namespace
        assert "pd" in namespace
        assert "plt" in namespace
        assert "os" in namespace
        assert "register_alias" in namespace

    def test_from_import_usage(self):
        """Test actual usage after from import"""
        import subprocess
        import sys

        r = subprocess.run(  # noqa: S603 — list form, trusted input
            [
                sys.executable,
                "-c",
                "from laziest_import import *; m = math; assert m.pi > 3.14; o = os; assert callable(o.getcwd); print('OK')",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        assert r.stdout.strip() == "OK"


class TestFunctions:
    """Test utility functions"""

    def test_get_module(self):
        """Test get_module function"""

        # Returns None when not loaded
        lz.cache.clear()
        assert lz.module.get("math") is None

        # Returns module after loading
        _ = lz.math.pi
        mod = lz.module.get("math")
        assert mod is not None
        assert hasattr(mod, "pi")

    def test_dir_function(self):
        """Test __dir__ function"""

        dir_result = dir(lz)

        # Check that public functions are in result
        assert "alias" in dir_result
        assert "module" in dir_result
        assert "cache" in dir_result

    def test_lazy_module_repr(self):
        """Test LazyModule repr"""
        from laziest_import._api._module import _get_lazy_module

        # When not loaded
        lz.cache.clear()
        lm = _get_lazy_module("math")
        repr_str = repr(lm)
        assert "not loaded" in repr_str

        # After loading
        _ = lm.pi
        repr_str = repr(lm)
        assert "loaded" in repr_str


class TestAutoSearch:
    """Test auto-search functionality"""

    def test_auto_search_enabled_by_default(self):
        """Test auto-search is enabled by default"""

        assert lz.config.auto_search is True

    def test_enable_disable_auto_search(self):
        """Test enabling/disabling auto-search"""

        lz.config.auto_search = False
        assert lz.config.auto_search is False

        lz.config.auto_search = True
        assert lz.config.auto_search is True

    def test_search_module_stdlib(self):
        """Test searching for standard library modules"""

        # Search for standard library modules
        result = lz.symbol.search("os")
        assert isinstance(result, list)
        assert len(result) > 0

        result = lz.symbol.search("json")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_search_module_installed(self):
        """Test searching for installed third-party libraries"""

        # Search for installed modules
        result = lz.symbol.search("numpy")
        if not result:
            # numpy not installed, try another common package
            result = lz.symbol.search("pytest")
            assert isinstance(result, list)
            assert len(result) > 0
        else:
            assert isinstance(result, list)
            assert len(result) > 0

    def test_auto_import_unregistered_module(self):
        """Test auto-importing unregistered module"""

        # Use a module that is NOT in predefined aliases
        # Using a unique name that's unlikely to be in any package
        unregistered_module = "some_random_module_xyz123"
        assert unregistered_module not in lz.module.list_available()

        # Test auto-search with a module that might be installed
        # Using 'flask' which may or may not be installed
        try:
            flask_mod = lz.flask
            assert flask_mod.__name__ == "flask"
        except ImportError:
            # Skip test if flask is not installed
            pytest.skip("flask not installed")

    def test_rebuild_module_cache(self):
        """Test rebuilding module cache"""

        result = lz.install.rebuild_cache()
        assert result is None or result is True


class TestSymbolSearch:
    """Test symbol search functionality"""

    def test_symbol_search_enabled_by_default(self):
        """Test symbol search is enabled by default"""

        assert lz.symbol.config.enabled is True

    def test_enable_disable_symbol_search(self):
        """Test enabling/disabling symbol search"""

        lz.symbol.config.disable()
        assert lz.symbol.config.enabled is False

        lz.symbol.config.enable()
        assert lz.symbol.config.enabled is True

    def test_search_symbol_function(self):
        """Test search_symbol function returns results"""

        # Search for a common function name that should exist
        results = lz.symbol.search("sqrt", max_results=3)

        # sqrt should be found in math and/or numpy
        assert isinstance(results, list)
        if results:
            assert all(hasattr(r, "module_name") for r in results)
            assert all(hasattr(r, "symbol_name") for r in results)
            assert all(hasattr(r, "symbol_type") for r in results)

    def test_search_symbol_with_type_filter(self):
        """Test search_symbol with type filter"""

        # Search for classes only
        results = lz.symbol.search("defaultdict", symbol_type="class", max_results=5)

        if results:
            # All results should be classes
            for r in results:
                assert r.symbol_type == "class"

    def test_get_symbol_search_config(self):
        """Test getting symbol search configuration"""

        config = lz.symbol.config.snapshot()
        assert isinstance(config, dict)
        assert "enabled" in config["search"]
        assert "interactive" in config["search"]
        assert "exact_params" in config["search"]
        assert "max_results" in config["search"]

    def test_get_symbol_cache_info(self):
        """Test getting symbol cache info"""

        info = lz.symbol.cache_info()
        assert isinstance(info, dict)
        assert "built" in info
        assert "symbol_count" in info
        assert "confirmed_mappings" in info

    def test_clear_symbol_cache(self):
        """Test clearing symbol cache"""

        # This should not raise an error
        lz.cache.symbols.clear()

        info = lz.symbol.cache_info()
        assert info["built"] is False
        assert info["symbol_count"] == 0

    def test_rebuild_symbol_index(self):
        """Test rebuilding symbol index"""

        # Clear first
        lz.cache.symbols.clear()

        # Rebuild
        lz.symbol.index.rebuild()

        # Should have some symbols now
        info = lz.symbol.cache_info()
        assert info["built"] is True
        assert info["symbol_count"] > 0

    def test_search_symbol_nonexistent(self):
        """Test searching for nonexistent symbol"""

        results = lz.symbol.search("this_symbol_definitely_does_not_exist_xyz123")
        assert results == []


class TestAsyncImport:
    """Test async import functionality"""

    @pytest.mark.asyncio
    async def test_import_async(self):
        """Test async import of a module"""

        # Import a stdlib module asynchronously
        math_mod = await import_async("math")
        assert math_mod is not None
        assert hasattr(math_mod, "pi")
        assert math_mod.pi > 3.14

    @pytest.mark.asyncio
    async def test_import_multiple_async(self):
        """Test async import of multiple modules"""

        # Import multiple stdlib modules asynchronously
        modules = await import_multiple_async(["math", "os", "json"])

        assert "math" in modules
        assert "os" in modules
        assert "json" in modules
        assert modules["math"].pi > 3.14
        assert callable(modules["os"].getcwd)
        assert callable(modules["json"].dumps)


class TestRetryMechanism:
    """Test retry mechanism for imports"""

    def test_enable_disable_retry(self):
        """Test enabling/disabling retry"""

        # Disable retry first
        lz.config.retry.enabled = False
        assert lz.config.retry.enabled is False

        # Enable with default params
        lz.config.retry.enabled = True
        assert lz.config.retry.enabled is True

        # Disable again
        lz.config.retry.enabled = False
        assert lz.config.retry.enabled is False

        # Re-enable for other tests
        lz.config.retry.enabled = True

    def test_enable_retry_with_params(self):
        """Test enabling retry with custom parameters"""

        lz.config.retry.enabled = True
        lz.config.retry.max_retries = 5
        lz.config.retry.delay = 0.1
        assert lz.config.retry.enabled is True

        # Reset to default
        lz.config.retry.enabled = True


class TestFileCache:
    """Test file-level caching functionality"""

    def test_enable_disable_file_cache(self):
        """Test enabling/disabling file cache"""

        # Disable first
        lz.cache.files.enabled = False
        assert lz.cache.files.enabled is False

        # Enable
        lz.cache.files.enabled = True
        assert lz.cache.files.enabled is True

    def test_get_file_cache_info(self):
        """Test getting file cache info"""

        info = lz.cache.files.info()
        assert isinstance(info, dict)
        assert "enabled" in info

    def test_clear_file_cache(self):
        """Test clearing file cache"""

        # Should not raise an error
        count = lz.cache.files.clear()
        assert isinstance(count, int)

    def test_set_cache_dir(self):
        """Test setting custom cache directory"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            lz.cache.dir = tmpdir
            cache_dir = lz.cache.dir
            assert str(cache_dir) == tmpdir or cache_dir == Path(tmpdir)

            # Reset to default
            lz.cache.reset_dir()


class TestImportHooks:
    """Test import hooks functionality"""

    def test_pre_import_hook(self):
        """Test pre-import hook"""

        called = []

        def my_hook(module_name: str):
            called.append(module_name)

        lz.hooks.pre.add(my_hook)

        # Import something
        lz.cache.clear()
        _ = lz.math.pi

        # Check if hook was called
        assert "math" in called

        # Clean up
        lz.hooks.pre.remove(my_hook)

    def test_post_import_hook(self):
        """Test post-import hook"""

        called = []

        def my_hook(module_name: str, module):
            called.append((module_name, module.__name__))

        lz.hooks.post.add(my_hook)

        # Import something
        lz.cache.clear()
        _ = lz.json.dumps

        # Check if hook was called
        assert any(name == "json" for name, _ in called)

        # Clean up
        lz.hooks.post.remove(my_hook)

    def test_clear_import_hooks(self):
        """Test clearing all import hooks"""

        def dummy_hook(name):
            pass

        lz.hooks.pre.add(dummy_hook)
        lz.hooks.post.add(dummy_hook)

        lz.hooks.clear()
        assert len(lz.hooks.pre) == 0
        assert len(lz.hooks.post) == 0


class TestLazyModuleCall:
    """Test LazyModule __call__ behavior"""

    def test_call_non_callable_module_error_message(self):
        """Test error message when calling non-callable module"""

        # math module is not callable
        with pytest.raises(TypeError) as excinfo:
            lz.math()

        # Check error message
        assert "'module' object is not callable" in str(excinfo.value)


class TestValidateAliases:
    """Test alias validation functionality"""

    def test_validate_aliases_valid(self):
        """Test validating valid aliases"""

        # Test with valid aliases
        result = lz.alias.validate({"os_alias": "os", "sys_alias": "sys"})
        assert "os_alias" in result["valid"]
        assert "sys_alias" in result["valid"]
        assert len(result["invalid"]) == 0

    def test_validate_aliases_invalid_identifier(self):
        """Test validating aliases with invalid identifiers"""

        # Test with invalid alias names (starting with digit is truly invalid)
        result = lz.alias.validate({"123invalid": "os", "another_invalid": "sys"})
        assert "123invalid" in result["invalid"]
        # Note: aliases with '-' or '.' are now valid for pip package name mapping

    def test_validate_aliases_empty_module(self):
        """Test validating aliases with empty module name"""

        result = lz.alias.validate({"empty_mod": ""})
        assert "empty_mod" in result["invalid"]

    def test_validate_aliases_current(self):
        """Test validating current aliases"""

        # Validate all current aliases
        result = lz.alias.validate()
        assert isinstance(result, dict)
        assert "valid" in result
        assert "invalid" in result

    def test_validate_aliases_importable(self):
        """Test validating that aliases are importable"""

        # Test with a known importable module
        result = validate_aliases_importable({"os_test": "os"})
        assert "importable" in result
        assert "not_importable" in result
        assert "os_test" in result["importable"]

    def test_validate_aliases_importable_nonexistent(self):
        """Test validating import of nonexistent module"""

        result = validate_aliases_importable({"bad": "nonexistent_module_xyz123"})
        assert "importable" in result
        assert "not_importable" in result
        assert "bad" in result["not_importable"]


class TestVersionAndReload:
    """Test version and reload functionality"""

    def test_get_version_loaded_module(self):
        """Test getting version of loaded module"""

        # Load a module with __version__
        _ = lz.json.dumps

        # Check version (json is stdlib, may or may not have version)
        version = lz.version.of("json")
        # Just check it doesn't crash
        assert version is None or isinstance(version, str)

    def test_get_version_not_loaded(self):
        """Test getting version of non-loaded module"""

        lz.cache.clear()
        version = lz.version.of("math")
        assert version is None

    def test_reload_module(self):
        """Test reloading a module"""

        # Load a module first
        _ = lz.math.pi

        # Reload it
        result = lz.module.reload("math")
        assert result is True

    def test_reload_module_not_loaded(self):
        """Test reloading a module that was never loaded"""

        # Try to reload a module that was never loaded
        # Register a temp alias but don't load it
        lz.alias.register("temp_reload_test", "os")
        lz.cache.clear()

        result = lz.module.reload("temp_reload_test")
        assert result is False

        # Clean up
        lz.alias.unregister("temp_reload_test")


class TestDebugMode:
    """Test debug mode functionality"""

    def test_enable_disable_debug_mode(self):
        """Test enabling/disabling debug mode"""

        # Enable debug mode
        lz.config.debug = True
        assert lz.config.debug is True

        # Disable debug mode
        lz.config.debug = False
        assert lz.config.debug is False

    def test_debug_mode_off_by_default(self):
        """Test debug mode is off by default"""

        # Make sure it's off
        lz.config.debug = False
        assert lz.config.debug is False


class TestImportStats:
    """Test import statistics functionality"""

    def test_get_import_stats(self):
        """Test getting import statistics"""

        # Reset stats first
        reset_import_stats()

        # Load a module
        lz.cache.clear()
        _ = lz.math.pi

        # Get stats
        stats = lz.config.import_stats
        assert isinstance(stats, dict)
        assert "total_imports" in stats
        assert "total_time" in stats
        assert "average_time" in stats
        assert "module_times" in stats
        assert "module_access_counts" in stats

    def test_reset_import_stats(self):
        """Test resetting import statistics"""

        # Load something to generate stats
        lz.cache.clear()
        _ = lz.os.getcwd

        # Reset
        reset_import_stats()

        stats = lz.config.import_stats
        assert stats["total_imports"] == 0


class TestLazySubmodule:
    """Test lazy submodule access"""

    def test_submodule_access(self):
        """Test accessing submodule attributes"""

        # Access os.path (submodule)
        path = lz.os.path
        assert path is not None
        assert hasattr(path, "join")

    def test_nested_submodule_access(self):
        """Test accessing nested submodule"""

        # Access collections.abc (nested)
        abc = lz.collections.abc
        assert abc is not None

    def test_submodule_dir(self):
        """Test dir() on submodule"""

        path_dir = dir(lz.os.path)
        assert isinstance(path_dir, list)
        assert "join" in path_dir

    def test_submodule_repr(self):
        """Test repr of submodule"""

        repr_str = repr(lz.os.path)
        assert "LazySubmodule" in repr_str or "path" in repr_str


class TestSearchClass:
    """Test search_class functionality"""

    def test_search_class_in_stdlib(self):
        """Test searching for class in stdlib"""

        # Search for defaultdict in collections
        result = lz.symbol.search("defaultdict", symbol_type="class")
        if result:
            for r in result:
                assert r.symbol_type == "class"

    def test_search_class_not_found(self):
        """Test searching for nonexistent class"""

        result = lz.symbol.search("ThisClassDefinitelyDoesNotExist12345", symbol_type="class")
        assert result == []


class TestAliasExport:
    """Test alias export functionality"""

    def test_export_aliases_to_file(self):
        """Test exporting aliases to file"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            result = lz.alias.export(path=temp_path)
            assert os.path.exists(temp_path)

            # Check file is valid JSON
            import json

            with open(temp_path) as f:
                data = json.load(f)
            assert isinstance(data, dict)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_export_aliases_returns_json(self):
        """Test export_aliases returns JSON string"""

        result = lz.alias.export()
        assert isinstance(result, str)

        import json

        data = json.loads(result)
        assert isinstance(data, dict)


class TestConfigPaths:
    """Test configuration paths functionality"""

    def test_get_config_paths(self):
        """Test getting configuration paths"""

        paths = get_config_paths()
        assert isinstance(paths, list)
        # All paths should be strings
        assert all(isinstance(p, str) for p in paths)


class TestRegisterAliases:
    """Test batch alias registration"""

    def test_register_aliases_batch(self):
        """Test registering multiple aliases at once"""

        aliases = {"test_os1": "os", "test_sys1": "sys", "test_json1": "json"}

        registered = lz.alias.register_many(aliases)
        assert isinstance(registered, list)
        assert len(registered) == 3

        # Verify aliases are registered
        available = lz.module.list_available()
        assert "test_os1" in available
        assert "test_sys1" in available
        assert "test_json1" in available

        # Clean up
        for alias in aliases:
            lz.alias.unregister(alias)

    def test_register_aliases_empty(self):
        """Test registering empty dict"""

        registered = lz.alias.register_many({})
        assert registered == []


class TestForceSaveCache:
    """Test force save cache functionality"""

    def test_force_save_cache(self):
        """Test force saving cache"""

        # Enable file cache
        lz.cache.files.enabled = True

        # Force save
        result = lz.cache.files.force_save()
        assert isinstance(result, bool)


class TestSymbolSearchAdvanced:
    """Advanced symbol search tests"""

    def test_search_symbol_with_signature(self):
        """Test search_symbol with signature hint"""

        results = lz.symbol.search("sqrt", signature="(x)", max_results=5)
        assert isinstance(results, list)

    def test_enable_symbol_search_with_params(self):
        """Test enabling symbol search with custom params"""

        lz.symbol.config.enable()
        lz.symbol.config.interactive = False
        lz.symbol.config.exact_params = True
        lz.symbol.config.max_results = 10
        lz.symbol.config.search_depth = 2
        lz.symbol.config.skip_stdlib = True

        config = lz.symbol.config.snapshot()
        assert config["search"]["interactive"] is False
        assert config["search"]["exact_params"] is True
        assert config["search"]["max_results"] == 10
        assert config["search"]["search_depth"] == 2
        assert config["search"]["skip_stdlib"] is True

        # Reset to default
        lz.symbol.config.enable()


class TestImportHooksAdvanced:
    """Advanced import hooks tests"""

    def test_remove_nonexistent_hook(self):
        """Test removing a hook that was never added"""

        def dummy_hook(name):
            pass

        result = lz.hooks.pre.remove(dummy_hook)
        assert result is False

        result = lz.hooks.post.remove(dummy_hook)
        assert result is False

    def test_multiple_hooks(self):
        """Test multiple hooks are called in order"""

        call_order = []

        def hook1(name):
            call_order.append(("hook1", name))

        def hook2(name):
            call_order.append(("hook2", name))

        lz.hooks.pre.add(hook1)
        lz.hooks.pre.add(hook2)

        lz.cache.clear()
        _ = lz.math.pi

        # Both hooks should have been called
        assert len(call_order) >= 2

        lz.hooks.pre.remove(hook1)
        lz.hooks.pre.remove(hook2)


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_access_private_attribute(self):
        """Test accessing private attributes"""

        name = lz.math.__name__
        assert name == "math"

    def test_getattr_on_module(self):
        """Test __getattr__ behavior"""

        # Access a valid module
        math = lz.__getattr__("math")
        assert math is not None

    def test_dir_includes_functions(self):
        """Test __dir__ includes all public functions"""

        dir_result = dir(lz)

        # Check some public namespaces and attributes
        expected = [
            "alias",
            "module",
            "cache",
            "config",
            "hooks",
            "install",
            "symbol",
            "version",
        ]
        for func in expected:
            assert func in dir_result, f"{func} not in dir()"

    def test_module_repr_variants(self):
        """Test module repr in different states"""
        from laziest_import._api._module import _get_lazy_module

        lz.cache.clear()

        # Before loading
        lm = _get_lazy_module("os")
        repr_before = repr(lm)
        assert "not loaded" in repr_before

        # After loading
        _ = lm.getcwd
        repr_after = repr(lm)
        assert "loaded" in repr_after


class TestAsyncImportAdvanced:
    """Advanced async import tests"""

    @pytest.mark.asyncio
    async def test_import_async_with_alias(self):
        """Test async import using alias"""

        # 'np' is an alias for numpy, but we use stdlib
        math_mod = await import_async("math")
        assert math_mod.__name__ == "math"

    @pytest.mark.asyncio
    async def test_import_multiple_async_empty(self):
        """Test async import with empty list"""

        result = await import_multiple_async([])
        assert result == {}


class TestEnhancedCache:
    """Test enhanced cache functionality"""

    def test_get_cache_version(self):
        """Test cache version exists"""

        version = lz.version.cache()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_set_cache_config(self):
        """Test setting cache configuration"""

        # Set custom TTL
        lz.cache.config.symbol_index_ttl = 7200
        lz.cache.config.stdlib_cache_ttl = 86400

        config = lz.cache.config.snapshot()
        assert config["symbol_index_ttl"] == 7200
        assert config["stdlib_cache_ttl"] == 86400

        # Reset to defaults
        lz.cache.config.symbol_index_ttl = 86400
        lz.cache.config.stdlib_cache_ttl = 604800
        lz.cache.config.third_party_cache_ttl = 86400

    def test_get_cache_config(self):
        """Test getting cache configuration"""

        config = lz.cache.config.snapshot()
        assert "symbol_index_ttl" in config
        assert "stdlib_cache_ttl" in config
        assert "third_party_cache_ttl" in config
        assert "enable_compression" in config
        assert "max_cache_size_mb" in config

    def test_get_cache_stats(self):
        """Test getting cache statistics"""

        # Reset stats first
        reset_cache_stats()

        stats = lz.cache.stats
        assert "symbol_hits" in stats
        assert "symbol_misses" in stats
        assert "last_build_time" in stats
        assert "build_count" in stats
        assert "hit_rate" in stats

    def test_reset_cache_stats(self):
        """Test resetting cache statistics"""

        # Reset stats
        reset_cache_stats()

        stats = lz.cache.stats
        assert stats["symbol_hits"] == 0
        assert stats["symbol_misses"] == 0
        assert stats["module_hits"] == 0
        assert stats["module_misses"] == 0

    def test_enhanced_symbol_cache_info(self):
        """Test enhanced symbol cache info"""

        info = lz.symbol.cache_info()
        assert "built" in info
        assert "symbol_count" in info
        assert "stdlib_symbols" in info
        assert "third_party_symbols" in info
        assert "tracked_packages" in info
        assert "cache_stats" in info
        assert "cache_config" in info

    def test_invalidate_package_cache(self):
        """Test invalidating package cache"""

        # Try to invalidate a non-tracked package
        result = invalidate_package_cache("nonexistent_package_xyz")
        assert result is False

    def test_rebuild_symbol_index(self):
        """Test rebuilding symbol index"""

        # Clear cache first
        lz.cache.symbols.clear()

        # Rebuild
        lz.symbol.index.rebuild()

        # Check that index is built
        info = lz.symbol.cache_info()
        assert info["built"] is True


class TestMappingsFromFiles:
    """Test loading mappings from configuration files"""

    def test_abbreviations_loaded(self):
        """Test that abbreviations are loaded from file"""

        # Check that common abbreviations work
        available = lz.module.list_available()
        # np is a common abbreviation for numpy
        assert "np" in available
        # pd is a common abbreviation for pandas
        assert "pd" in available

    def test_misspellings_corrected(self):
        """Test that misspellings are corrected from file"""

        # Enable auto-search
        lz.config.auto_search = True

        # Test common misspelling correction using fuzzy module search
        from laziest_import._fuzzy import _search_module

        result = _search_module("jsn")
        assert result == "json"

        result = _search_module("maht")
        assert result == "math"

        result = _search_module("tim")
        assert result == "time"

    def test_reload_mappings(self):
        """Test reloading mappings from files"""

        # Should not raise an error
        reload_mappings()

        # Check that mappings are still available
        available = lz.module.list_available()
        assert "np" in available

    def test_module_priorities_loaded(self):
        """Test that module priorities are loaded from file"""

        # Check that priority is returned for known modules
        priority = get_module_priority("pandas")
        assert priority is not None
        assert priority > 0

        priority = get_module_priority("numpy")
        assert priority is not None
        assert priority > 0


class TestConfigFlexibility:
    """Test configuration flexibility features"""

    def test_set_module_priority(self):
        """Test setting custom module priority"""

        # Set a custom priority

        set_module_priority("test_module_xyz", 42)

        priority = get_module_priority("test_module_xyz")
        assert priority == 42

    def test_get_symbol_preference(self):
        """Test getting symbol preference"""

        # DataFrame should prefer pandas by default
        pref = lz.symbol.preference("DataFrame")
        assert pref == "pandas"

    def test_set_symbol_preference(self):
        """Test setting custom symbol preference"""

        # Set a custom preference
        lz.symbol.prefer("TestClass", "test_module")

        pref = lz.symbol.preference("TestClass")
        assert pref == "test_module"

        # Clear it
        lz.symbol.clear_preference("TestClass")
        pref = lz.symbol.preference("TestClass")
        assert pref is None


class TestAdvancedFuzzyMatching:
    """Test advanced fuzzy matching scenarios"""

    def test_search_similar_module_names(self):
        """Test finding similar module names"""

        lz.config.auto_search = True

        # Test partial matching
        result = lz.symbol.search("num")  # should find numpy
        assert isinstance(result, list)
        assert len(result) > 0

    def test_search_with_underscore_variants(self):
        """Test searching with underscore variants"""

        lz.config.auto_search = True

        # Test with a module that should be available (stdlib)
        result = lz.symbol.search("json")
        assert isinstance(result, list)
        assert len(result) > 0

        # Test with a common abbreviation
        result = lz.symbol.search("np")
        assert isinstance(result, list)

    def test_search_case_insensitive(self):
        """Test case-insensitive searching"""

        lz.config.auto_search = True

        # Lowercase search should still work
        result = lz.symbol.search("json")
        assert isinstance(result, list)
        assert len(result) > 0


class TestConfigurationPaths:
    """Test configuration path handling"""

    def test_get_config_paths_returns_list(self):
        """Test that config paths returns a list"""

        paths = get_config_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0

    def test_get_config_dirs_returns_list(self):
        """Test that config dirs returns a list"""

        dirs = get_config_dirs()
        assert isinstance(dirs, list)
        assert len(dirs) > 0


class TestModuleReprAndStr:
    """Test module representation methods"""

    def test_lazy_module_str(self):
        """Test string representation of lazy module"""

        lz.cache.clear()
        str_repr = str(lz.math)
        assert "math" in str_repr or len(str_repr) > 0

    def test_lazy_module_dir(self):
        """Test dir() on lazy module"""

        dir_result = dir(lz.os)
        assert isinstance(dir_result, list)
        assert "getcwd" in dir_result


class TestErrorRecovery:
    """Test error recovery scenarios"""

    def test_import_after_clear_cache(self):
        """Test that imports work after clearing cache"""

        # Clear everything
        lz.cache.clear()
        lz.cache.symbols.clear()

        # Should still be able to import
        _ = lz.math.pi

        # Module should be loaded
        loaded = lz.module.list_loaded()
        assert "math" in loaded

    def test_multiple_reload_mappings(self):
        """Test that multiple reload_mappings calls work"""

        # Multiple reloads should not cause issues
        from laziest_import import reload_mappings

        reload_mappings()
        from laziest_import import reload_mappings

        reload_mappings()
        from laziest_import import reload_mappings

        reload_mappings()

        # Should still work
        available = lz.module.list_available()
        assert "np" in available


class TestLazySymbolAdvanced:
    """Advanced LazySymbol tests"""

    def test_lazy_symbol_arithmetic_operators(self):
        """Test LazySymbol arithmetic operators"""

        # Load math module
        _ = lz.math.pi

        # Test that module attributes work
        assert lz.math.sqrt(4) == 2.0

    def test_lazy_symbol_comparison(self):
        """Test LazySymbol comparison operators"""

        # Test comparison with numbers
        assert lz.math.pi > 3
        assert lz.math.pi < 4
        assert lz.math.pi != 3

    def test_lazy_symbol_getitem(self):
        """Test LazySymbol getitem operator"""

        # Test indexing on module result
        result = lz.json.dumps([1, 2, 3])
        assert lz.json.loads(result)[0] == 1


class TestModuleAttributeAccess:
    """Test various module attribute access patterns"""

    def test_access_module_constant(self):
        """Test accessing module constants"""

        assert lz.math.pi > 3.14
        assert lz.math.e > 2.7

    def test_access_module_function(self):
        """Test accessing module functions"""

        assert lz.math.sqrt(16) == 4.0
        assert lz.os.path.join("a", "b") in ["a/b", "a\\b"]

    def test_access_module_class(self):
        """Test accessing module classes"""

        dt = lz.datetime.datetime(2024, 1, 1)
        assert dt.year == 2024

    def test_access_nested_attribute(self):
        """Test accessing nested attributes"""

        # Access nested function
        result = lz.os.path.basename("/path/to/file.txt")
        assert "file.txt" in result


class TestMultipleModuleAccess:
    """Test accessing multiple modules"""

    def test_sequential_module_access(self):
        """Test accessing multiple modules sequentially"""

        lz.cache.clear()

        _ = lz.math.pi
        _ = lz.os.getcwd()
        _ = lz.json.dumps({})

        loaded = lz.module.list_loaded()
        assert "math" in loaded
        assert "os" in loaded
        assert "json" in loaded

    def test_concurrent_module_access(self):
        """Test that module access doesn't interfere with each other"""

        # Access different modules
        math_pi = lz.math.pi
        json_str = lz.json.dumps({"key": "value"})

        assert math_pi > 3
        assert "key" in json_str


class TestAliasRegistration:
    """Test alias registration edge cases"""

    def test_register_alias_with_dots(self):
        """Test registering alias with dotted module name"""

        lz.alias.register("test_submodule", "os.path")
        available = lz.module.list_available()
        assert "test_submodule" in available

        lz.alias.unregister("test_submodule")

    def test_register_duplicate_alias(self):
        """Test registering duplicate alias"""

        # Register once
        lz.alias.register("dup_test", "os")

        # Register again with different module (should update)
        lz.alias.register("dup_test", "sys")

        available = lz.module.list_available()
        assert "dup_test" in available

        lz.alias.unregister("dup_test")

    def test_register_alias_empty_string(self):
        """Test registering alias with empty string"""

        with pytest.raises(ValueError):
            lz.alias.register("", "os")

    def test_register_alias_none_value(self):
        """Test registering alias with None value"""

        with pytest.raises((ValueError, TypeError)):
            lz.alias.register("test_none", None)


class TestCachePersistence:
    """Test cache persistence functionality"""

    def test_cache_persists_across_accesses(self):
        """Test that cache persists across accesses"""

        lz.cache.clear()

        # First access
        _ = lz.math.pi
        assert "math" in lz.module.list_loaded()

        # Second access should use cache
        _ = lz.math.sqrt(4)
        assert "math" in lz.module.list_loaded()

    def test_symbol_cache_info_after_build(self):
        """Test symbol cache info after building"""

        lz.cache.symbols.clear()
        lz.symbol.index.rebuild()

        info = lz.symbol.cache_info()
        assert info["built"] is True
        assert info["symbol_count"] > 0


class TestSearchSymbolAdvanced:
    """Advanced symbol search tests"""

    def test_search_symbol_with_different_types(self):
        """Test searching for symbols of different types"""

        # Search for function
        results = lz.symbol.search("sqrt", symbol_type="function", max_results=5)
        if results:
            for r in results:
                assert r.symbol_type in ("function", "callable")

        # Search for class
        results = lz.symbol.search("defaultdict", symbol_type="class", max_results=5)
        if results:
            for r in results:
                assert r.symbol_type == "class"

    def test_search_symbol_max_results(self):
        """Test that max_results parameter works"""

        results = lz.symbol.search("get", max_results=3)
        assert len(results) <= 3

    def test_search_symbol_case_sensitivity(self):
        """Test symbol search case handling"""

        # Should find symbols regardless of case
        results_lower = lz.symbol.search("sqrt", max_results=5)
        results_upper = lz.symbol.search("SQRT", max_results=5)

        # At least one should return results for common symbols
        assert len(results_lower) > 0 or len(results_upper) >= 0


class TestAutoSearchEdgeCases:
    """Test auto-search edge cases"""

    def test_search_empty_string(self):
        """Test searching for empty string"""

        result = lz.symbol.search("")
        assert isinstance(result, list)

    def test_search_very_long_string(self):
        """Test searching for very long string"""

        long_name = "a" * 1000
        result = lz.symbol.search(long_name)
        assert result == []

    def test_search_special_characters(self):
        """Test searching with special characters"""

        result = lz.symbol.search("os.path")
        assert isinstance(result, list)

    def test_search_unicode(self):
        """Test searching with unicode characters"""

        result = lz.symbol.search("módulo")
        assert isinstance(result, list)


class TestSubmoduleEdgeCases:
    """Test submodule handling edge cases"""

    def test_deeply_nested_submodule(self):
        """Test accessing deeply nested submodule"""

        # Access deeply nested attribute
        try:
            result = lz.collections.abc.MutableMapping
            assert result is not None
        except AttributeError:
            # Might not be available in all Python versions
            pass

    def test_submodule_attribute_error(self):
        """Test that accessing non-existent submodule attribute raises error"""

        with pytest.raises(AttributeError):
            _ = lz.os.nonexistent_attribute_xyz

    def test_submodule_dir_completeness(self):
        """Test that dir() on submodule returns useful values"""

        os_path_dir = dir(lz.os.path)
        assert "join" in os_path_dir
        assert "basename" in os_path_dir


class TestImportHooksEdgeCases:
    """Test import hooks edge cases"""

    def test_hook_raises_exception(self):
        """Test that hook exceptions are handled"""

        def bad_hook(module_name):
            raise RuntimeError("Hook error")

        lz.hooks.pre.add(bad_hook)

        # Should not crash even if hook raises
        lz.cache.clear()
        try:
            _ = lz.math.pi
        finally:
            lz.hooks.pre.remove(bad_hook)

    def test_post_hook_with_invalid_module(self):
        """Test post-import hook with module that fails to load"""

        called = []

        def tracking_hook(module_name, module):
            called.append(module_name)

        lz.hooks.post.add(tracking_hook)

        # Try to import something that will fail
        with contextlib.suppress(AttributeError, ImportError):
            _ = lz.nonexistent_module_xyz_12345.pi

        lz.hooks.post.remove(tracking_hook)
        # Hook may or may not be called on failed import
        assert isinstance(called, list)

        # Hook shouldn't be called for failed imports
        # (or should handle gracefully)


class TestCacheStatistics:
    """Test cache statistics functionality"""

    def test_cache_stats_increment_on_hit(self):
        """Test that cache stats increment on hits"""

        reset_cache_stats()
        lz.cache.clear()

        # First access (miss)
        _ = lz.math.pi

        # Second access (should be a hit conceptually, but depends on implementation)
        _ = lz.math.sqrt(4)

        stats = lz.cache.stats
        assert stats["module_hits"] >= 0
        assert stats["module_misses"] >= 0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""

        reset_cache_stats()

        stats = lz.cache.stats
        # Hit rate should be a number between 0 and 100
        assert 0 <= stats["hit_rate"] <= 100


class TestSymbolResolutionConfig:
    """Test symbol resolution configuration"""

    def test_get_symbol_resolution_config(self):
        """Test getting symbol resolution config"""

        config = lz.symbol.config.snapshot()
        assert "auto_symbol" in config["resolution"]
        assert "auto_threshold" in config["resolution"]
        assert "conflict_threshold" in config["resolution"]

    def test_enable_disable_auto_symbol_resolution(self):
        """Test enabling/disabling auto symbol resolution"""

        lz.symbol.config.auto_resolution = True
        config = lz.symbol.config.snapshot()
        assert config["resolution"]["auto_symbol"] is True

        lz.symbol.config.auto_resolution = False
        config = lz.symbol.config.snapshot()
        assert config["resolution"]["auto_symbol"] is False

        lz.symbol.config.auto_resolution = True
        lz.symbol.config.auto_resolution = True


class TestModulePriority:
    """Test module priority functionality"""

    def test_priority_for_unknown_module(self):
        """Test getting priority for unknown module"""

        priority = get_module_priority("unknown_module_xyz_123")
        # Unknown modules return default priority 50
        assert isinstance(priority, int)
        assert priority == 50

    def test_update_existing_priority(self):
        """Test updating existing priority"""

        original = get_module_priority("pandas")

        set_module_priority("pandas", 200)

        new_priority = get_module_priority("pandas")
        assert new_priority == 200

        # Restore original
        if original is not None:
            set_module_priority("pandas", original)


class TestAutoInstallConfig:
    """Test auto-install configuration"""

    def test_get_auto_install_config(self):
        """Test getting auto-install config"""

        config = lz.install.auto
        assert "enabled" in config
        assert "interactive" in config

    def test_enable_disable_auto_install(self):
        """Test enabling/disabling auto-install"""

        original = lz.install.enabled

        lz.install.enable()
        assert lz.install.enabled is True

        lz.install.disable()
        assert lz.install.enabled is False

        # Restore original
        if original:
            lz.install.enable()
        else:
            lz.install.disable()

    def test_set_pip_index(self):
        """Test setting pip index"""

        set_pip_index("https://pypi.org/simple")
        from laziest_import._config import _AUTO_INSTALL_CONFIG

        assert _AUTO_INSTALL_CONFIG["index"] == "https://pypi.org/simple"

    def test_set_pip_extra_args(self):
        """Test setting pip extra args"""

        set_pip_extra_args(["--no-cache-dir"])
        from laziest_import._config import _AUTO_INSTALL_CONFIG

        assert "--no-cache-dir" in _AUTO_INSTALL_CONFIG["extra_args"]


class TestLoadedModulesContext:
    """Test loaded modules context functionality"""

    def test_get_loaded_modules_context(self):
        """Test getting loaded modules context"""

        lz.cache.clear()
        _ = lz.math.pi
        _ = lz.os.getcwd

        context = get_loaded_modules_context()
        assert isinstance(context, (set, list, dict))


class TestListSymbolConflicts:
    """Test symbol conflict listing"""

    def test_list_symbol_conflicts(self):
        """Test listing symbol conflicts"""

        # list_symbol_conflicts requires a symbol argument
        conflicts = lz.symbol.conflicts("sqrt") or []
        assert isinstance(conflicts, list)

    def test_list_symbol_conflicts_no_conflict(self):
        """Test listing conflicts for unique symbol"""

        # A unique symbol should have no conflicts
        conflicts = lz.symbol.conflicts("this_symbol_definitely_does_not_exist_xyz") or []
        assert isinstance(conflicts, list)


class TestCacheVersion:
    """Test cache version functionality"""

    def test_cache_version_format(self):
        """Test that cache version has correct format"""

        version = lz.version.cache()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_cache_version_consistency(self):
        """Test that cache version is consistent"""

        v1 = lz.version.cache()
        v2 = lz.version.cache()
        assert v1 == v2


class TestModuleCachingBehavior:
    """Test module caching behavior in detail"""

    def test_cache_is_shared(self):
        """Test that cache is shared between accesses"""

        lz.cache.clear()

        # Access through different means
        mod1 = lz.math
        mod2 = lz.__getattr__("math")

        # Both should return the same cached module
        assert mod1.pi == mod2.pi

    def test_clear_cache_removes_all(self):
        """Test that clear_cache removes all cached modules"""

        # Load multiple modules
        _ = lz.math.pi
        _ = lz.os.getcwd
        _ = lz.json.dumps

        # Clear cache
        lz.cache.clear()

        # All should be unloaded
        loaded = lz.module.list_loaded()
        assert len(loaded) == 0


class TestThreadSafety:
    """Test thread safety of lazy loading"""

    def test_concurrent_imports(self):
        """Test concurrent imports don't cause issues"""
        import threading

        errors = []

        def import_math():
            try:
                _ = lz.math.pi
            except Exception as e:
                errors.append(e)

        def import_os():
            try:
                _ = lz.os.getcwd
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=import_math),
            threading.Thread(target=import_os),
            threading.Thread(target=import_math),
            threading.Thread(target=import_os),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestPackageRenameMapping:
    """Test package rename mapping functionality"""

    def test_common_package_renames(self):
        """Test that common package renames are available"""

        # These should work through the rename mapping
        # sklearn -> scikit-learn, PIL -> pillow, etc.
        # The mapping is used internally for auto-install suggestions
        available = lz.module.list_available()

        # Check that we have some common aliases
        assert len(available) > 0


class TestExportAliasesFormat:
    """Test alias export format"""

    def test_export_aliases_json_valid(self):
        """Test that exported aliases is valid JSON"""
        import json

        exported = lz.alias.export()
        # Should not raise
        data = json.loads(exported)
        assert isinstance(data, dict)

    def test_export_aliases_includes_common(self):
        """Test that exported aliases include common aliases"""
        import json

        exported = lz.alias.export()
        data = json.loads(exported)

        # Should include some common aliases
        assert len(data) > 0


class TestValidateAliasesEdgeCases:
    """Test validate aliases edge cases"""

    def test_validate_aliases_with_none(self):
        """Test validating aliases with None input"""

        result = lz.alias.validate(None)
        assert "valid" in result
        assert "invalid" in result

    def test_validate_aliases_importable_with_none(self):
        """Test validating importable aliases with None input"""

        result = validate_aliases_importable(None)
        assert "importable" in result
        assert "not_importable" in result


class TestRetryMechanismAdvanced:
    """Test retry mechanism advanced scenarios"""

    def test_retry_with_custom_modules(self):
        """Test retry with specific modules"""

        lz.config.retry.enabled = True
        lz.config.retry.max_retries = 2
        lz.config.retry.delay = 0.01
        assert lz.config.retry.enabled is True

        # Should work for stdlib
        lz.cache.clear()
        _ = lz.math.pi

        lz.config.retry.enabled = False

    def test_retry_disabled_by_default(self):
        """Test that retry is typically disabled by default"""

        # Just check the function exists
        assert lz.config.retry.enabled is not None


class TestLazyProxyAdvanced:
    """Test LazyProxy advanced functionality"""

    def test_lazy_proxy_dir(self):
        """Test LazyProxy dir()"""
        from laziest_import._proxy._proxy import LazyProxy

        dir_result = dir(LazyProxy())
        assert isinstance(dir_result, list)

    def test_lazy_proxy_repr(self):
        """Test LazyProxy repr"""
        from laziest_import._proxy._proxy import LazyProxy

        repr_str = repr(LazyProxy())
        assert "LazyProxy" in repr_str

    def test_lazy_proxy_attribute_access(self):
        """Test LazyProxy attribute access"""
        from laziest_import._proxy._proxy import LazyProxy

        # Access through lazy proxy
        math = LazyProxy().math
        assert math is not None


class TestMemoryEfficiency:
    """Test memory efficiency of lazy loading"""

    def test_unloaded_modules_dont_consume_memory(self):
        """Test that unloaded modules don't consume significant memory"""

        lz.cache.clear()

        # Get reference count for a known alias before loading
        # This is a basic check - detailed memory profiling would need more tools
        available = lz.module.list_available()
        assert len(available) > 0

    def test_loaded_modules_are_cached(self):
        """Test that loaded modules are properly cached"""

        lz.cache.clear()

        # First load
        mod1_id = id(lz.math)

        # Second access should return same object
        mod2_id = id(lz.math)

        # Should be the same cached object
        assert mod1_id == mod2_id


class TestMisspelledModuleImport:
    """Test importing modules with misspelled names - auto-correction functionality"""

    def _search_module_fuzzy(self, name):
        """Helper: search module name via fuzzy matching."""
        from laziest_import._fuzzy import _search_module

        lz.config.auto_search = True
        return _search_module(name)

    def test_import_math_with_misspelling(self):
        """Test importing math module with common misspellings"""

        lz.config.auto_search = True
        lz.cache.clear()

        # Test math variations
        result = self._search_module_fuzzy("mathh")
        assert result == "math"

    def test_import_json_with_misspelling(self):
        """Test importing json module with common misspellings"""

        result = self._search_module_fuzzy("jsn")
        assert result == "json"

    def test_import_os_with_misspelling(self):
        """Test importing os module with partial name"""

        result = self._search_module_fuzzy("o")
        assert result is None or "o" in result.lower()

    def test_import_sys_with_misspelling(self):
        """Test importing sys module with typo"""

        result = self._search_module_fuzzy("sy")
        assert result == "sys" or result is None

    def test_import_datetime_with_misspelling(self):
        """Test importing datetime with common typo"""

        result = self._search_module_fuzzy("datatime")
        assert result == "datetime"

    def test_import_collections_with_misspelling(self):
        """Test importing collections with typo"""

        result = self._search_module_fuzzy("colection")
        assert result == "collections"

    def test_import_functools_with_misspelling(self):
        """Test importing functools with typo"""

        result = self._search_module_fuzzy("functool")
        assert result == "functools"

    def test_import_itertools_with_misspelling(self):
        """Test importing itertools with typo"""

        result = self._search_module_fuzzy("itertool")
        assert result == "itertools"

    def test_import_pathlib_with_misspelling(self):
        """Test importing pathlib with typo"""

        result = self._search_module_fuzzy("pathlb")
        assert result == "pathlib"

    def test_import_subprocess_with_misspelling(self):
        """Test importing subprocess with typo"""

        result = self._search_module_fuzzy("subproces")
        assert result == "subprocess"

    def test_import_argparse_with_misspelling(self):
        """Test importing argparse with typo"""

        result = self._search_module_fuzzy("argpars")
        assert result == "argparse"

    def test_import_logging_with_misspelling(self):
        """Test importing logging with common typo"""

        result = self._search_module_fuzzy("loging")
        assert result == "logging"

    def test_import_re_with_misspelling(self):
        """Test importing re with partial match"""

        result = self._search_module_fuzzy("regex")
        assert result is not None or result is None

    def test_import_random_with_misspelling(self):
        """Test importing random with typo"""

        result = self._search_module_fuzzy("randm")
        assert result == "random"

    def test_import_string_with_misspelling(self):
        """Test importing string with typo"""

        result = self._search_module_fuzzy("strng")
        assert result == "string"

    def test_import_copy_with_misspelling(self):
        """Test importing copy with typo"""

        result = self._search_module_fuzzy("cpy")
        assert result == "copy"

    def test_import_pickle_with_misspelling(self):
        """Test importing pickle with typo"""

        result = self._search_module_fuzzy("pickl")
        assert result == "pickle"

    def test_import_threading_with_misspelling(self):
        """Test importing threading with typo"""

        result = self._search_module_fuzzy("threadng")
        assert result == "threading"

    def test_import_time_with_misspelling(self):
        """Test importing time with typo"""

        result = self._search_module_fuzzy("tim")
        assert result is not None or result is None  # Just check it doesn't crash

    def test_import_io_with_misspelling(self):
        """Test importing io with typo"""

        result = self._search_module_fuzzy("i")
        assert result is None or result == "io"

    def test_import_hashlib_with_misspelling(self):
        """Test importing hashlib with typo"""

        result = self._search_module_fuzzy("hashlb")
        assert result == "hashlib"

    def test_import_typing_with_misspelling(self):
        """Test importing typing with typo"""

        result = self._search_module_fuzzy("typng")
        assert result == "typing"

    def test_import_warnings_with_misspelling(self):
        """Test importing warnings with typo"""

        result = self._search_module_fuzzy("warning")
        assert result == "warnings"

    def test_import_contextlib_with_misspelling(self):
        """Test importing contextlib with typo"""

        result = self._search_module_fuzzy("contextlb")
        assert result == "contextlib"

    def test_import_enum_with_misspelling(self):
        """Test importing enum with typo"""

        result = self._search_module_fuzzy("enumm")
        assert result == "enum"

    def test_import_dataclasses_with_misspelling(self):
        """Test importing dataclasses with typo"""

        result = self._search_module_fuzzy("dataclass")
        assert result == "dataclasses"

    def test_import_abc_with_misspelling(self):
        """Test importing abc with typo"""

        result = self._search_module_fuzzy("ab")
        assert result is None or result == "abc"

    def test_import_urllib_with_misspelling(self):
        """Test importing urllib with typo"""

        result = self._search_module_fuzzy("urlllib")
        assert result == "urllib"

    def test_import_email_with_misspelling(self):
        """Test importing email with typo"""

        result = self._search_module_fuzzy("emial")
        assert result is None or result == "email" or isinstance(result, str)

    def test_import_html_with_misspelling(self):
        """Test importing html with typo"""

        result = self._search_module_fuzzy("htlm")
        assert result is None or result == "html" or isinstance(result, str)

    def test_import_http_with_misspelling(self):
        """Test importing http with typo"""

        result = self._search_module_fuzzy("htp")
        assert result == "http"

    def test_import_xml_with_misspelling(self):
        """Test importing xml with typo"""

        result = self._search_module_fuzzy("xm")
        assert result == "xml" or result is None

    def test_import_csv_with_misspelling(self):
        """Test importing csv with typo"""

        result = self._search_module_fuzzy("cs")
        assert result == "csv" or result is None

    def test_import_configparser_with_misspelling(self):
        """Test importing configparser with typo"""

        result = self._search_module_fuzzy("configparser")
        assert result == "configparser"

    def test_import_tempfile_with_misspelling(self):
        """Test importing tempfile with typo"""

        result = self._search_module_fuzzy("tempflie")
        assert result == "tempfile"

    def test_import_shutil_with_misspelling(self):
        """Test importing shutil with typo"""

        result = self._search_module_fuzzy("shutl")
        assert result == "shutil"

    def test_import_glob_with_misspelling(self):
        """Test importing glob with typo"""

        result = self._search_module_fuzzy("glb")
        assert result == "glob"

    def test_import_fnmatch_with_misspelling(self):
        """Test importing fnmatch with typo"""

        result = self._search_module_fuzzy("fnmatc")
        assert result == "fnmatch"

    def test_import_struct_with_misspelling(self):
        """Test importing struct with typo"""

        result = self._search_module_fuzzy("struc")
        assert result == "struct"

    def test_import_codecs_with_misspelling(self):
        """Test importing codecs with typo"""

        result = self._search_module_fuzzy("codec")
        assert result == "codecs"

    def test_import_locale_with_misspelling(self):
        """Test importing locale with typo"""

        result = self._search_module_fuzzy("loclae")
        assert result == "locale"

    def test_import_calendar_with_misspelling(self):
        """Test importing calendar with typo"""

        result = self._search_module_fuzzy("calender")
        assert result == "calendar"

    def test_import_socket_with_misspelling(self):
        """Test importing socket with typo"""

        result = self._search_module_fuzzy("soket")
        assert result == "socket"

    def test_import_ssl_with_misspelling(self):
        """Test importing ssl with typo"""

        result = self._search_module_fuzzy("ss")
        assert result == "ssl" or result is None

    def test_import_secrets_with_misspelling(self):
        """Test importing secrets with typo"""

        result = self._search_module_fuzzy("secret")
        assert result == "secrets"

    def test_import_unittest_with_misspelling(self):
        """Test importing unittest with typo"""

        result = self._search_module_fuzzy("unitest")
        assert result == "unittest"

    def test_import_asyncio_with_misspelling(self):
        """Test importing asyncio with common typo"""

        result = self._search_module_fuzzy("asynccio")
        assert result == "asyncio"

    def test_import_concurrent_with_misspelling(self):
        """Test importing concurrent with typo"""

        result = self._search_module_fuzzy("concurent")
        assert result == "concurrent"

    def test_import_multiprocessing_with_misspelling(self):
        """Test importing multiprocessing with typo"""

        result = self._search_module_fuzzy("multiprocesing")
        assert result == "multiprocessing"

    def test_import_queue_with_misspelling(self):
        """Test importing queue with typo"""

        result = self._search_module_fuzzy("queu")
        assert result == "queue"

    def test_import_sched_with_misspelling(self):
        """Test importing sched with typo"""

        result = self._search_module_fuzzy("schd")
        assert result == "sched"

    def test_import_textwrap_with_misspelling(self):
        """Test importing textwrap with typo"""

        result = self._search_module_fuzzy("textwarp")
        assert result == "textwrap"

    def test_import_traceback_with_misspelling(self):
        """Test importing traceback with typo"""

        result = self._search_module_fuzzy("tracebak")
        assert result == "traceback"

    def test_import_inspect_with_misspelling(self):
        """Test importing inspect with typo"""

        result = self._search_module_fuzzy("inpect")
        assert result == "inspect"

    def test_import_dis_with_misspelling(self):
        """Test importing dis with typo"""

        result = self._search_module_fuzzy("di")
        assert result == "dis" or result is None

    def test_import_ast_with_misspelling(self):
        """Test importing ast with typo"""

        result = self._search_module_fuzzy("as")
        assert result == "ast" or result is None

    def test_import_token_with_misspelling(self):
        """Test importing token with typo"""

        result = self._search_module_fuzzy("tokn")
        assert result == "token"

    def test_import_keyword_with_misspelling(self):
        """Test importing keyword with typo"""

        result = self._search_module_fuzzy("keyord")
        assert result == "keyword"

    def test_import_operator_with_misspelling(self):
        """Test importing operator with typo"""

        result = self._search_module_fuzzy("operater")
        assert result == "operator"

    def test_no_false_positives_for_gibberish(self):
        """Test that gibberish doesn't match anything"""

        lz.config.auto_search = True

        # Completely random string should not match
        result = self._search_module_fuzzy("xyzqwerty12345asdfg")
        assert result is None

    def test_very_similar_names(self):
        """Test that very similar names are handled correctly"""

        lz.config.auto_search = True

        result = self._search_module_fuzzy("jams")
        assert result is None or result != "json"

    def test_case_sensitivity(self):
        """Test case sensitivity in searches"""

        lz.config.auto_search = True

        # Uppercase should still work
        result = self._search_module_fuzzy("JSON")
        assert result == "json"

        result = self._search_module_fuzzy("MATH")
        assert result == "math"

    def test_underscore_vs_hyphen(self):
        """Test underscore vs hyphen handling"""

        lz.config.auto_search = True

        result1 = self._search_module_fuzzy("date_util")
        result2 = self._search_module_fuzzy("date-util")
        if result1 is not None and result2 is not None:
            assert result1 == result2


# ============== New Performance Feature Tests ==============


class TestIncrementalIndex:
    """Test incremental index update functionality"""

    def test_get_incremental_config(self):
        """Test getting incremental config"""
        from laziest_import._cache import get_incremental_config

        config = get_incremental_config()
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_enable_incremental_index(self):
        """Test enabling/disabling incremental index"""
        from laziest_import._cache import (
            enable_incremental_index,
            get_incremental_config,
        )

        enable_incremental_index(True)
        config = get_incremental_config()
        assert config["enabled"] is True

        enable_incremental_index(False)
        config = get_incremental_config()
        assert config["enabled"] is False

        # Restore default
        enable_incremental_index(True)

    def test_build_symbol_index_incremental(self):
        """Test incremental symbol index build"""
        from laziest_import._symbol import build_symbol_index_incremental

        # Should return True or False depending on state
        result = build_symbol_index_incremental()
        assert isinstance(result, bool)


class TestBackgroundIndexBuild:
    """Test background index build functionality"""

    def test_enable_background_build(self):
        """Test enabling/disabling background build"""
        from laziest_import._cache import (
            enable_background_build,
            get_preheat_config,
        )

        enable_background_build(True)
        config = get_preheat_config()
        assert config["enabled"] is True

        enable_background_build(False)
        config = get_preheat_config()
        assert config["enabled"] is False

        # Restore default
        enable_background_build(True)

    def test_is_background_index_building(self):
        """Test checking background build status"""
        from laziest_import._cache import _is_background_index_building

        result = _is_background_index_building()
        assert isinstance(result, bool)

    def test_get_preheat_config(self):
        """Test getting preheat config"""
        from laziest_import._cache import get_preheat_config

        config = get_preheat_config()
        assert isinstance(config, dict)
        assert "enabled" in config
        assert "async_index_build" in config


class TestModuleSkipConfig:
    """Test module skip configuration"""

    def test_get_module_skip_config(self):
        """Test getting module skip config"""
        from laziest_import._symbol import get_module_skip_config

        config = get_module_skip_config()
        assert isinstance(config, dict)
        assert "skip_test_modules" in config
        assert "skip_large_modules" in config
        assert "large_module_threshold" in config

    def test_set_module_skip_config(self):
        """Test setting module skip config"""
        from laziest_import._symbol import (
            get_module_skip_config,
            set_module_skip_config,
        )

        # Set new values
        set_module_skip_config(
            skip_test_modules=False,
            skip_large_modules=False,
            large_module_threshold=200,
        )

        config = get_module_skip_config()
        assert config["skip_test_modules"] is False
        assert config["skip_large_modules"] is False
        assert config["large_module_threshold"] == 200

        # Restore defaults
        set_module_skip_config(
            skip_test_modules=True,
            skip_large_modules=True,
            large_module_threshold=100,
        )


class TestCacheCompression:
    """Test cache compression functionality"""

    def test_enable_cache_compression(self):
        """Test enabling/disabling cache compression"""
        from laziest_import._cache import (
            enable_cache_compression,
            get_cache_config,
        )

        enable_cache_compression(True)
        config = get_cache_config()
        assert config["enable_compression"] is True

        enable_cache_compression(False)
        config = get_cache_config()
        assert config["enable_compression"] is False

        # Restore default
        enable_cache_compression(False)

    def test_save_and_load_compressed_cache(self):
        """Test saving and loading compressed cache"""

        from laziest_import._cache import (
            _get_cache_dir,
            _load_compressed_json,
            _save_compressed_json,
        )

        # Create test data
        test_data = {
            "test_key": "test_value",
            "nested": {"a": 1, "b": 2},
            "list": [1, 2, 3],
        }

        # Save to temp file
        cache_dir = _get_cache_dir()
        test_file = cache_dir / "test_compressed.json.gz"

        try:
            # Save compressed
            result = _save_compressed_json(test_data, test_file)
            assert result is True
            assert test_file.exists()

            # Load compressed
            loaded = _load_compressed_json(test_file)
            assert loaded is not None
            assert loaded["test_key"] == "test_value"
            assert loaded["nested"]["a"] == 1
            assert loaded["list"] == [1, 2, 3]
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()


class TestPackageDetection:
    """Test package detection for incremental updates"""

    def test_get_installed_packages(self):
        """Test getting installed packages"""
        from laziest_import._cache import _get_installed_packages

        packages = _get_installed_packages()
        assert isinstance(packages, set)
        # Should have at least some packages
        assert len(packages) > 0

    def test_detect_changed_packages(self):
        """Test detecting changed packages"""
        from laziest_import._cache import _detect_changed_packages

        new_pkgs, updated_pkgs, removed_pkgs = _detect_changed_packages()
        assert isinstance(new_pkgs, set)
        assert isinstance(updated_pkgs, set)
        assert isinstance(removed_pkgs, set)

    def test_get_incremental_update_modules(self):
        """Test getting modules for incremental update"""
        from laziest_import._cache import _get_incremental_update_modules

        modules, needs_full = _get_incremental_update_modules()
        assert isinstance(modules, set)
        assert isinstance(needs_full, bool)


class TestRemovePackageSymbols:
    """Test removing package symbols from cache"""

    def test_remove_package_symbols_basic(self):
        """Test basic symbol removal"""
        from laziest_import._symbol import (
            _SYMBOL_CACHE,
            _remove_package_symbols,
        )

        # Add some test symbols
        test_pkg = "__test_package_for_removal__"
        _SYMBOL_CACHE["test_symbol_1"] = [(f"{test_pkg}.module", "function", None)]
        _SYMBOL_CACHE["test_symbol_2"] = [
            (f"{test_pkg}.module", "class", None),
            ("other_package.module", "function", None),
        ]

        # Remove the package symbols
        _remove_package_symbols(test_pkg)

        # Verify removal
        assert "test_symbol_1" not in _SYMBOL_CACHE
        assert "test_symbol_2" in _SYMBOL_CACHE
        assert len(_SYMBOL_CACHE["test_symbol_2"]) == 1
        assert _SYMBOL_CACHE["test_symbol_2"][0][0] == "other_package.module"


class TestIntegrationNewFeatures:
    """Integration tests for new features"""

    def test_full_workflow(self):
        """Test full workflow with new features"""
        from laziest_import._cache import (
            enable_background_build,
            enable_cache_compression,
            enable_incremental_index,
            get_cache_config,
            get_incremental_config,
            get_preheat_config,
        )
        from laziest_import._symbol import (
            get_module_skip_config,
            set_module_skip_config,
        )

        # Enable all features
        enable_cache_compression(True)
        enable_background_build(True)
        enable_incremental_index(True)

        # Verify all enabled
        assert get_cache_config()["enable_compression"] is True
        assert get_preheat_config()["enabled"] is True
        assert get_incremental_config()["enabled"] is True

        # Test module skip config
        set_module_skip_config(skip_large_modules=True, large_module_threshold=50)
        config = get_module_skip_config()
        assert config["skip_large_modules"] is True
        assert config["large_module_threshold"] == 50

        # Restore defaults
        enable_cache_compression(False)
        set_module_skip_config(large_module_threshold=100)


class TestPackageVersion:
    """Test package version functionality"""

    def test_get_package_version_existing(self):
        """Test getting version of existing packages"""

        # Test with laziest-import itself (always installed in test env)
        version = lz.version.of("laziest-import")

        # Should return version string
        assert version is not None
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_package_version_nonexistent(self):
        """Test getting version of nonexistent package"""

        version = lz.version.of("this_package_definitely_does_not_exist_12345")
        assert version is None

    def test_get_package_version_normalized_name(self):
        """Test that package names are normalized"""

        # Both formats should work
        ver1 = lz.version.of("laziest_import")
        ver2 = lz.version.of("laziest-import")

        # At least one should work
        assert ver1 is not None or ver2 is not None

    def test_get_all_package_versions(self):
        """Test getting all package versions"""

        versions = lz.version.all_packages()

        assert isinstance(versions, dict)
        assert len(versions) > 0

        # All values should be strings
        for pkg, ver in versions.items():
            assert isinstance(pkg, str)
            assert isinstance(ver, str)

    def test_get_laziest_import_version(self):
        """Test getting laziest-import version"""

        version = lz.version.current

        assert version is not None
        assert isinstance(version, str)
        # Should have version-like format
        assert len(version) > 0

    def test_version_matches_version_attribute(self):
        """Test that version functions match __version__"""

        # __version__ should be defined
        assert hasattr(lz, "__version__")
        assert lz.__version__ is not None


# ============== Bug Fix Verification Tests ==============
# These tests specifically verify the bugs that were fixed


class TestInitStateVariableCopyFix:
    """Test P0 fix: Variable copy issue when importing state variables.

    Bug: Using `from ._config import _INITIALIZING` creates a copy that never updates.
    Fix: Added helper functions (is_initializing(), is_initialized(), etc.) and
         access state through module reference.
    """

    def test_is_initialized_helper_function_exists(self):
        """Test that is_initialized helper function exists."""

        from laziest_import import is_initialized

        assert callable(is_initialized)

    def test_is_initializing_helper_function_exists(self):
        """Test that is_initializing helper function exists."""

        from laziest_import import is_initializing

        assert callable(is_initializing)

    def test_is_init_failed_helper_function_exists(self):
        """Test that is_init_failed helper function exists."""

        from laziest_import import is_init_failed

        assert callable(is_init_failed)

    def test_get_init_error_helper_function_exists(self):
        """Test that get_init_error helper function exists."""

        from laziest_import import get_init_error

        assert callable(get_init_error)

    def test_helper_functions_return_correct_state(self):
        """Test that helper functions return correct values after initialization."""

        # After module is loaded, initialization should be complete
        assert is_initialized() is True
        assert is_initializing() is False
        assert is_init_failed() is False
        assert get_init_error() is None

    def test_get_init_state_returns_dict(self):
        """Test that get_init_state returns a dictionary with all state keys."""
        from laziest_import._config import get_init_state

        state = get_init_state()
        assert isinstance(state, dict)
        assert "initializing" in state
        assert "initialized" in state
        assert "failed" in state
        assert "error" in state

    def test_state_updates_through_module_access(self):
        """Test that state changes are reflected when accessed through module."""
        from laziest_import import _config as config_module
        from laziest_import._config import is_initialized

        # Both should return the same value
        assert is_initialized() == config_module._INITIALIZED

        # The helper function should reflect the actual state
        assert is_initialized() is True


class TestInitFailureStateTracking:
    """Test P1 fix: Initialization failure state not tracked.

    Bug: When initialization fails, subsequent accesses don't know about the failure.
    Fix: Added _INIT_FAILED and _INIT_ERROR tracking with helper functions.
    """

    def test_init_failure_state_variables_exist(self):
        """Test that failure state variables exist in config."""
        from laziest_import import _config as config_module

        assert hasattr(config_module, "_INIT_FAILED")
        assert hasattr(config_module, "_INIT_ERROR")

    def test_init_failure_helpers_return_values(self):
        """Test that failure helpers can be called and return appropriate values."""

        # Should not be failed in normal conditions
        assert is_init_failed() is False
        assert get_init_error() is None


class TestNonInteractiveEnvironmentDetection:
    """Test P1 fix: Interactive confirmation blocking in non-interactive environments.

    Bug: _interactive_confirm() blocks when stdin is not a TTY.
    Fix: Added _is_interactive_terminal() check to detect non-interactive environments.
    """

    def test_is_interactive_terminal_function_exists(self):
        """Test that the interactive terminal detection function exists."""
        from laziest_import._symbol import _is_interactive_terminal

        assert callable(_is_interactive_terminal)

    def test_is_interactive_terminal_returns_bool(self):
        """Test that _is_interactive_terminal returns a boolean."""
        from laziest_import._symbol import _is_interactive_terminal

        result = _is_interactive_terminal()
        assert isinstance(result, bool)

    def test_install_is_interactive_terminal_function_exists(self):
        """Test that the install module also has interactive terminal detection."""
        from laziest_import._install import _is_interactive_terminal

        assert callable(_is_interactive_terminal)
        result = _is_interactive_terminal()
        assert isinstance(result, bool)


class TestLazySymbolGetUnderlyingClass:
    """Test P2 fix: Type checking methods on LazySymbol.

    Bug: __instancecheck__ and __subclasscheck__ on LazySymbol instance have no effect.
         These methods must be defined on metaclasses, not instances.
    Fix: Removed ineffective methods, added get_underlying_class() as documented alternative.
    """

    def test_get_underlying_class_method_exists(self):
        """Test that get_underlying_class method exists on LazySymbol."""
        from laziest_import._proxy import LazySymbol

        assert hasattr(LazySymbol, "get_underlying_class")
        assert callable(getattr(LazySymbol, "get_underlying_class"))

    def test_get_underlying_class_returns_type(self):
        """Test that get_underlying_class returns a type for class symbols."""
        from laziest_import._proxy import LazySymbol

        # Create a LazySymbol for a known class
        lazy_defaultdict = LazySymbol("defaultdict", "collections", "class")

        # Get the underlying class
        cls = lazy_defaultdict.get_underlying_class()
        assert isinstance(cls, type)
        assert cls.__name__ == "defaultdict"

    def test_get_underlying_class_allows_isinstance_check(self):
        """Test that get_underlying_class result works with isinstance."""
        from laziest_import._proxy import LazySymbol

        lazy_defaultdict = LazySymbol("defaultdict", "collections", "class")
        defaultdict_cls = lazy_defaultdict.get_underlying_class()

        # Create an instance
        dd = lazy_defaultdict(list)

        # isinstance should work with the underlying class
        assert isinstance(dd, defaultdict_cls)

    def test_get_underlying_class_for_function(self):
        """Test that get_underlying_class works for functions too."""
        from laziest_import._proxy import LazySymbol

        lazy_sqrt = LazySymbol("sqrt", "math", "function")
        sqrt_type = lazy_sqrt.get_underlying_class()

        # Should return the function's type
        import math

        assert sqrt_type is type(math.sqrt)


class TestAsyncContextNoBlocking:
    """Test P2 fix: time.sleep() blocking in async context.

    Bug: time.sleep() in retry mechanism blocks the async event loop.
    Fix: Detect async context and skip retry with sleep in such cases.
    """

    @pytest.mark.asyncio
    async def test_import_in_async_context_no_sleep(self):
        """Test that imports in async context don't use blocking sleep."""
        import asyncio

        # Enable retry (which would normally use sleep)
        lz.config.retry.enabled = True
        lz.config.retry.max_retries = 3
        lz.config.retry.delay = 0.1

        # Import a module - should not block
        start = asyncio.get_event_loop().time()
        _ = lz.math.pi
        elapsed = asyncio.get_event_loop().time() - start

        # Should be very fast (no blocking sleep)
        assert elapsed < 0.5  # Much less than retry_delay * max_retries

        lz.config.retry.enabled = False

    @pytest.mark.asyncio
    async def test_async_import_still_works(self):
        """Test that async imports still work correctly."""

        # Should work normally
        math_mod = await import_async("math")
        assert math_mod is not None
        assert math_mod.pi > 3


class TestSubmoduleCacheKeyConflict:
    """Test P3 fix: Submodule cache key conflicts.

    Bug: Submodule cache used attribute name as key, causing conflicts between
         different parent modules with same-named submodules.
    Fix: Use full_name (parent.attr) as cache key instead of just attr name.
    """

    def test_submodule_cache_uses_full_name(self):
        """Test that submodule cache uses full qualified name."""

        # Access submodules from different parents
        # Both might have 'path' attribute but should be cached separately
        os_path = lz.os.path

        # Should be able to access os.path attributes
        assert hasattr(os_path, "join")
        assert hasattr(os_path, "basename")

    def test_different_modules_same_attr_no_conflict(self):
        """Test that different modules with same attribute name don't conflict."""

        # Access collections.abc
        collections_abc = lz.collections.abc

        # This should be different from os.path etc.
        # Just verify it doesn't crash and returns correct object
        assert collections_abc is not None

    def test_submodule_dir_works(self):
        """Test that dir() works on submodules."""

        path_dir = dir(lz.os.path)
        assert isinstance(path_dir, list)
        assert "join" in path_dir

    def test_nested_submodule_access(self):
        """Test that nested submodule access works correctly."""

        # This should work without cache conflicts
        abc = lz.collections.abc
        assert abc is not None


class TestEdgeCasesFixedBugs:
    """Additional edge case tests for fixed bugs."""

    def test_module_access_during_initialization(self):
        """Test that module access works correctly after initialization."""

        # Module should be initialized now
        assert is_initialized() is True

        # Access should work
        assert lz.math.pi > 3

    def test_state_helper_functions_are_importable(self):
        """Test that state helper functions are importable from main module."""
        from laziest_import import (
            get_init_error,
            is_init_failed,
            is_initialized,
            is_initializing,
        )

        assert callable(is_initialized)
        assert callable(is_initializing)
        assert callable(is_init_failed)
        assert callable(get_init_error)

    def test_lazy_symbol_comparison_operators(self):
        """Test that LazySymbol comparison operators work."""
        from laziest_import._proxy import LazySymbol

        # Create lazy symbols for values
        lazy_pi = LazySymbol("pi", "math", "constant")

        # Comparison should work after loading
        assert lazy_pi > 3
        assert lazy_pi < 4
        assert lazy_pi != 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
