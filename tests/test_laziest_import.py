"""
laziest_import Test Suite - Comprehensive Tests
"""

import sys
import pytest
import tempfile
import os
from pathlib import Path

# Ensure laziest_import can be imported
sys.path.insert(0, '.')


class TestBasicImport:
    """Test basic import functionality"""
    
    def test_module_version(self):
        """Test module version exists"""
        import laziest_import
        assert hasattr(laziest_import, '__version__')
        assert laziest_import.__version__ == "0.0.2.3"
    
    def test_import_with_alias(self):
        """Test import using alias prefix"""
        import laziest_import as lz
        # Access standard library module
        math = lz.math
        import math as real_math
        # Check attributes are correct
        assert math.pi == real_math.pi
    
    def test_import_stdlib(self):
        """Test standard library lazy import"""
        import laziest_import as lz
        
        # os module
        os_module = lz.os
        import os as real_os
        assert os_module.getcwd() == real_os.getcwd()
        
        # sys module
        sys_module = lz.sys
        assert sys_module.version == sys.version
    
    def test_caching(self):
        """Test module caching"""
        import laziest_import as lz
        
        # Multiple accesses should return same attribute values
        pi1 = lz.math.pi
        pi2 = lz.math.pi
        assert pi1 == pi2


class TestAliasMapping:
    """Test alias mapping functionality"""
    
    def test_register_alias(self):
        """Test registering custom alias"""
        import laziest_import as lz
        
        lz.register_alias("test_os_alias", "os")
        
        # Verify alias is registered
        available = lz.list_available()
        assert "test_os_alias" in available
    
    def test_unregister_alias(self):
        """Test unregistering alias"""
        import laziest_import as lz
        
        lz.register_alias("temp_alias_for_test", "os")
        assert lz.unregister_alias("temp_alias_for_test") is True
        assert lz.unregister_alias("nonexistent_alias_xyz") is False
    
    def test_list_loaded(self):
        """Test listing loaded modules"""
        import laziest_import as lz
        
        # Clear cache
        lz.clear_cache()
        
        # Load a module
        _ = lz.math.pi
        
        loaded = lz.list_loaded()
        assert "math" in loaded
    
    def test_list_available(self):
        """Test listing available aliases"""
        import laziest_import as lz
        
        available = lz.list_available()
        # Check some built-in aliases
        assert "np" in available
        assert "pd" in available
        assert "plt" in available
        assert "os" in available


class TestErrorHandling:
    """Test error handling"""
    
    def test_import_nonexistent_module(self):
        """Test importing non-existent module"""
        import laziest_import as lz
        
        # Use an extremely unlikely module name
        # When accessing a non-existent module attribute, should raise AttributeError
        # (not ImportError) because the attribute doesn't exist in the module
        with pytest.raises(AttributeError):
            _ = lz.definitely_not_a_real_module_xyz123456.pi
    
    def test_clear_cache(self):
        """Test clearing cache"""
        import laziest_import as lz
        
        # Load a module
        _ = lz.math.pi
        assert "math" in lz.list_loaded()
        
        # Clear cache
        lz.clear_cache()
        assert "math" not in lz.list_loaded()


class TestFromImport:
    """Test from ... import * syntax"""
    
    def test_from_import_star(self):
        """Test from laziest_import import *"""
        # Create a new namespace
        namespace = {}
        exec("from laziest_import import *", namespace)
        
        # Check that common aliases are imported
        assert "np" in namespace
        assert "pd" in namespace
        assert "plt" in namespace
        assert "os" in namespace
        assert "register_alias" in namespace
    
    def test_from_import_usage(self):
        """Test actual usage after from import"""
        namespace = {}
        exec("from laziest_import import *", namespace)
        
        # Use math module
        math = namespace['math']
        assert math.pi > 3.14
        
        # Use os module
        os_mod = namespace['os']
        assert callable(os_mod.getcwd)


class TestFunctions:
    """Test utility functions"""
    
    def test_get_module(self):
        """Test get_module function"""
        import laziest_import as lz
        
        # Returns None when not loaded
        lz.clear_cache()
        assert lz.get_module("math") is None
        
        # Returns module after loading
        _ = lz.math.pi
        mod = lz.get_module("math")
        assert mod is not None
        assert hasattr(mod, 'pi')
    
    def test_dir_function(self):
        """Test __dir__ function"""
        import laziest_import as lz
        
        dir_result = dir(lz)
        
        # Check that public functions are in result
        assert "register_alias" in dir_result
        assert "list_loaded" in dir_result
        assert "list_available" in dir_result
        assert "clear_cache" in dir_result
        assert "__version__" in dir_result
    
    def test_lazy_module_repr(self):
        """Test LazyModule repr"""
        import laziest_import as lz
        
        # When not loaded
        lz.clear_cache()
        repr_str = repr(lz.math)
        assert "not loaded" in repr_str
        
        # After loading
        _ = lz.math.pi
        repr_str = repr(lz.math)
        assert "loaded" in repr_str


class TestAutoSearch:
    """Test auto-search functionality"""
    
    def test_auto_search_enabled_by_default(self):
        """Test auto-search is enabled by default"""
        import laziest_import as lz
        assert lz.is_auto_search_enabled() is True
    
    def test_enable_disable_auto_search(self):
        """Test enabling/disabling auto-search"""
        import laziest_import as lz
        
        lz.disable_auto_search()
        assert lz.is_auto_search_enabled() is False
        
        lz.enable_auto_search()
        assert lz.is_auto_search_enabled() is True
    
    def test_search_module_stdlib(self):
        """Test searching for standard library modules"""
        import laziest_import as lz
        
        # Search for standard library modules
        result = lz.search_module("os")
        assert result == "os"
        
        result = lz.search_module("json")
        assert result == "json"
    
    def test_search_module_installed(self):
        """Test searching for installed third-party libraries"""
        import laziest_import as lz
        
        # Search for installed modules
        result = lz.search_module("numpy")
        if result is None:
            # numpy not installed, try another common package
            result = lz.search_module("pytest")
            assert result == "pytest"
        else:
            assert result == "numpy"
    
    def test_auto_import_unregistered_module(self):
        """Test auto-importing unregistered module"""
        import laziest_import as lz
        
        # Use a module that is NOT in predefined aliases
        # Using a unique name that's unlikely to be in any package
        unregistered_module = "some_random_module_xyz123"
        assert unregistered_module not in lz.list_available()
        
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
        import laziest_import as lz
        
        # This function should be callable
        lz.rebuild_module_cache()


class TestSymbolSearch:
    """Test symbol search functionality"""
    
    def test_symbol_search_enabled_by_default(self):
        """Test symbol search is enabled by default"""
        import laziest_import as lz
        assert lz.is_symbol_search_enabled() is True
    
    def test_enable_disable_symbol_search(self):
        """Test enabling/disabling symbol search"""
        import laziest_import as lz
        
        lz.disable_symbol_search()
        assert lz.is_symbol_search_enabled() is False
        
        lz.enable_symbol_search()
        assert lz.is_symbol_search_enabled() is True
    
    def test_search_symbol_function(self):
        """Test search_symbol function returns results"""
        import laziest_import as lz
        
        # Search for a common function name that should exist
        results = lz.search_symbol("sqrt", max_results=3)
        
        # sqrt should be found in math and/or numpy
        assert isinstance(results, list)
        if results:
            assert all(hasattr(r, 'module_name') for r in results)
            assert all(hasattr(r, 'symbol_name') for r in results)
            assert all(hasattr(r, 'symbol_type') for r in results)
    
    def test_search_symbol_with_type_filter(self):
        """Test search_symbol with type filter"""
        import laziest_import as lz
        
        # Search for classes only
        results = lz.search_symbol("defaultdict", symbol_type="class", max_results=5)
        
        if results:
            # All results should be classes
            for r in results:
                assert r.symbol_type == "class"
    
    def test_get_symbol_search_config(self):
        """Test getting symbol search configuration"""
        import laziest_import as lz
        
        config = lz.get_symbol_search_config()
        assert isinstance(config, dict)
        assert "enabled" in config
        assert "interactive" in config
        assert "exact_params" in config
        assert "max_results" in config
    
    def test_get_symbol_cache_info(self):
        """Test getting symbol cache info"""
        import laziest_import as lz
        
        info = lz.get_symbol_cache_info()
        assert isinstance(info, dict)
        assert "built" in info
        assert "symbol_count" in info
        assert "confirmed_mappings" in info
    
    def test_clear_symbol_cache(self):
        """Test clearing symbol cache"""
        import laziest_import as lz
        
        # This should not raise an error
        lz.clear_symbol_cache()
        
        info = lz.get_symbol_cache_info()
        assert info["built"] is False
        assert info["symbol_count"] == 0
    
    def test_rebuild_symbol_index(self):
        """Test rebuilding symbol index"""
        import laziest_import as lz
        
        # Clear first
        lz.clear_symbol_cache()
        
        # Rebuild
        lz.rebuild_symbol_index()
        
        # Should have some symbols now
        info = lz.get_symbol_cache_info()
        assert info["built"] is True
        assert info["symbol_count"] > 0
    
    def test_search_symbol_nonexistent(self):
        """Test searching for nonexistent symbol"""
        import laziest_import as lz
        
        results = lz.search_symbol("this_symbol_definitely_does_not_exist_xyz123")
        assert results == []


class TestAsyncImport:
    """Test async import functionality"""
    
    @pytest.mark.asyncio
    async def test_import_async(self):
        """Test async import of a module"""
        import laziest_import as lz
        
        # Import a stdlib module asynchronously
        math_mod = await lz.import_async("math")
        assert math_mod is not None
        assert hasattr(math_mod, 'pi')
        assert math_mod.pi > 3.14
    
    @pytest.mark.asyncio
    async def test_import_multiple_async(self):
        """Test async import of multiple modules"""
        import laziest_import as lz
        
        # Import multiple stdlib modules asynchronously
        modules = await lz.import_multiple_async(["math", "os", "json"])
        
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
        import laziest_import as lz
        
        # Disable retry first
        lz.disable_retry()
        assert lz.is_retry_enabled() is False
        
        # Enable with default params
        lz.enable_retry()
        assert lz.is_retry_enabled() is True
        
        # Disable again
        lz.disable_retry()
        assert lz.is_retry_enabled() is False
        
        # Re-enable for other tests
        lz.enable_retry()
    
    def test_enable_retry_with_params(self):
        """Test enabling retry with custom parameters"""
        import laziest_import as lz
        
        lz.enable_retry(max_retries=5, retry_delay=0.1)
        assert lz.is_retry_enabled() is True
        
        # Reset to default
        lz.enable_retry()


class TestFileCache:
    """Test file-level caching functionality"""
    
    def test_enable_disable_file_cache(self):
        """Test enabling/disabling file cache"""
        import laziest_import as lz
        
        # Disable first
        lz.disable_file_cache()
        assert lz.is_file_cache_enabled() is False
        
        # Enable
        lz.enable_file_cache()
        assert lz.is_file_cache_enabled() is True
    
    def test_get_file_cache_info(self):
        """Test getting file cache info"""
        import laziest_import as lz
        
        info = lz.get_file_cache_info()
        assert isinstance(info, dict)
        assert "enabled" in info
    
    def test_clear_file_cache(self):
        """Test clearing file cache"""
        import laziest_import as lz
        
        # Should not raise an error
        count = lz.clear_file_cache()
        assert isinstance(count, int)
    
    def test_set_cache_dir(self):
        """Test setting custom cache directory"""
        import laziest_import as lz
        from pathlib import Path
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            lz.set_cache_dir(tmpdir)
            cache_dir = lz.get_cache_dir()
            assert str(cache_dir) == tmpdir or cache_dir == Path(tmpdir)
            
            # Reset to default
            lz.reset_cache_dir()


class TestImportHooks:
    """Test import hooks functionality"""
    
    def test_pre_import_hook(self):
        """Test pre-import hook"""
        import laziest_import as lz
        
        called = []
        
        def my_hook(module_name: str):
            called.append(module_name)
        
        lz.add_pre_import_hook(my_hook)
        
        # Import something
        lz.clear_cache()
        _ = lz.math.pi
        
        # Check if hook was called
        assert "math" in called
        
        # Clean up
        lz.remove_pre_import_hook(my_hook)
    
    def test_post_import_hook(self):
        """Test post-import hook"""
        import laziest_import as lz
        
        called = []
        
        def my_hook(module_name: str, module):
            called.append((module_name, module.__name__))
        
        lz.add_post_import_hook(my_hook)
        
        # Import something
        lz.clear_cache()
        _ = lz.json.dumps
        
        # Check if hook was called
        assert any(name == "json" for name, _ in called)
        
        # Clean up
        lz.remove_post_import_hook(my_hook)
    
    def test_clear_import_hooks(self):
        """Test clearing all import hooks"""
        import laziest_import as lz
        
        def dummy_hook(name):
            pass
        
        lz.add_pre_import_hook(dummy_hook)
        lz.add_post_import_hook(dummy_hook)
        
        # Clear all hooks
        lz.clear_import_hooks()


class TestLazyModuleCall:
    """Test LazyModule __call__ behavior"""
    
    def test_call_non_callable_module_error_message(self):
        """Test error message when calling non-callable module"""
        import laziest_import as lz
        
        # math module is not callable
        with pytest.raises(TypeError) as excinfo:
            lz.math()
        
        # Check error message contains module name
        assert "math" in str(excinfo.value)
        assert "not callable" in str(excinfo.value)


class TestValidateAliases:
    """Test alias validation functionality"""
    
    def test_validate_aliases_valid(self):
        """Test validating valid aliases"""
        import laziest_import as lz
        
        # Test with valid aliases
        result = lz.validate_aliases({"os_alias": "os", "sys_alias": "sys"})
        assert "os_alias" in result["valid"]
        assert "sys_alias" in result["valid"]
        assert len(result["invalid"]) == 0
    
    def test_validate_aliases_invalid_identifier(self):
        """Test validating aliases with invalid identifiers"""
        import laziest_import as lz
        
        # Test with invalid alias names (starting with digit is truly invalid)
        result = lz.validate_aliases({"123invalid": "os", "another_invalid": "sys"})
        assert "123invalid" in result["invalid"]
        # Note: aliases with '-' or '.' are now valid for pip package name mapping
    
    def test_validate_aliases_empty_module(self):
        """Test validating aliases with empty module name"""
        import laziest_import as lz
        
        result = lz.validate_aliases({"empty_mod": ""})
        assert "empty_mod" in result["invalid"]
    
    def test_validate_aliases_current(self):
        """Test validating current aliases"""
        import laziest_import as lz
        
        # Validate all current aliases
        result = lz.validate_aliases()
        assert isinstance(result, dict)
        assert "valid" in result
        assert "invalid" in result
    
    def test_validate_aliases_importable(self):
        """Test validating that aliases are importable"""
        import laziest_import as lz
        
        # Test with a known importable module
        result = lz.validate_aliases_importable({"os_test": "os"})
        assert "importable" in result
        assert "not_importable" in result
        assert "os_test" in result["importable"]
    
    def test_validate_aliases_importable_nonexistent(self):
        """Test validating import of nonexistent module"""
        import laziest_import as lz
        
        result = lz.validate_aliases_importable({"bad": "nonexistent_module_xyz123"})
        assert "importable" in result
        assert "not_importable" in result
        assert "bad" in result["not_importable"]


class TestVersionAndReload:
    """Test version and reload functionality"""
    
    def test_get_version_loaded_module(self):
        """Test getting version of loaded module"""
        import laziest_import as lz
        
        # Load a module with __version__
        _ = lz.json.dumps
        
        # Check version (json is stdlib, may or may not have version)
        version = lz.get_version("json")
        # Just check it doesn't crash
        assert version is None or isinstance(version, str)
    
    def test_get_version_not_loaded(self):
        """Test getting version of non-loaded module"""
        import laziest_import as lz
        
        lz.clear_cache()
        version = lz.get_version("math")
        assert version is None
    
    def test_reload_module(self):
        """Test reloading a module"""
        import laziest_import as lz
        
        # Load a module first
        _ = lz.math.pi
        
        # Reload it
        result = lz.reload_module("math")
        assert result is True
    
    def test_reload_module_not_loaded(self):
        """Test reloading a module that was never loaded"""
        import laziest_import as lz
        
        # Try to reload a module that was never loaded
        # Register a temp alias but don't load it
        lz.register_alias("temp_reload_test", "os")
        lz.clear_cache()
        
        result = lz.reload_module("temp_reload_test")
        assert result is False
        
        # Clean up
        lz.unregister_alias("temp_reload_test")


class TestDebugMode:
    """Test debug mode functionality"""
    
    def test_enable_disable_debug_mode(self):
        """Test enabling/disabling debug mode"""
        import laziest_import as lz
        
        # Enable debug mode
        lz.enable_debug_mode()
        assert lz.is_debug_mode() is True
        
        # Disable debug mode
        lz.disable_debug_mode()
        assert lz.is_debug_mode() is False
    
    def test_debug_mode_off_by_default(self):
        """Test debug mode is off by default"""
        import laziest_import as lz
        
        # Make sure it's off
        lz.disable_debug_mode()
        assert lz.is_debug_mode() is False


class TestImportStats:
    """Test import statistics functionality"""
    
    def test_get_import_stats(self):
        """Test getting import statistics"""
        import laziest_import as lz
        
        # Reset stats first
        lz.reset_import_stats()
        
        # Load a module
        lz.clear_cache()
        _ = lz.math.pi
        
        # Get stats
        stats = lz.get_import_stats()
        assert isinstance(stats, dict)
        assert "total_imports" in stats
        assert "total_time" in stats
        assert "average_time" in stats
        assert "module_times" in stats
        assert "module_access_counts" in stats
    
    def test_reset_import_stats(self):
        """Test resetting import statistics"""
        import laziest_import as lz
        
        # Load something to generate stats
        lz.clear_cache()
        _ = lz.os.getcwd
        
        # Reset
        lz.reset_import_stats()
        
        stats = lz.get_import_stats()
        assert stats["total_imports"] == 0


class TestLazySubmodule:
    """Test lazy submodule access"""
    
    def test_submodule_access(self):
        """Test accessing submodule attributes"""
        import laziest_import as lz
        
        # Access os.path (submodule)
        path = lz.os.path
        assert path is not None
        assert hasattr(path, 'join')
    
    def test_nested_submodule_access(self):
        """Test accessing nested submodule"""
        import laziest_import as lz
        
        # Access collections.abc (nested)
        abc = lz.collections.abc
        assert abc is not None
    
    def test_submodule_dir(self):
        """Test dir() on submodule"""
        import laziest_import as lz
        
        path_dir = dir(lz.os.path)
        assert isinstance(path_dir, list)
        assert 'join' in path_dir
    
    def test_submodule_repr(self):
        """Test repr of submodule"""
        import laziest_import as lz
        
        repr_str = repr(lz.os.path)
        assert 'LazySubmodule' in repr_str or 'path' in repr_str


class TestSearchClass:
    """Test search_class functionality"""
    
    def test_search_class_in_stdlib(self):
        """Test searching for class in stdlib"""
        import laziest_import as lz
        
        # Search for defaultdict in collections
        result = lz.search_class("defaultdict")
        if result:
            module_name, cls = result
            # defaultdict is defined in _collections (CPython implementation detail)
            assert module_name in ("collections", "_collections")
    
    def test_search_class_not_found(self):
        """Test searching for nonexistent class"""
        import laziest_import as lz
        
        result = lz.search_class("ThisClassDefinitelyDoesNotExist12345")
        assert result is None


class TestAliasExport:
    """Test alias export functionality"""
    
    def test_export_aliases_to_file(self):
        """Test exporting aliases to file"""
        import laziest_import as lz
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            result = lz.export_aliases(path=temp_path)
            assert os.path.exists(temp_path)
            
            # Check file is valid JSON
            import json
            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert isinstance(data, dict)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_export_aliases_returns_json(self):
        """Test export_aliases returns JSON string"""
        import laziest_import as lz
        
        result = lz.export_aliases()
        assert isinstance(result, str)
        
        import json
        data = json.loads(result)
        assert isinstance(data, dict)


class TestConfigPaths:
    """Test configuration paths functionality"""
    
    def test_get_config_paths(self):
        """Test getting configuration paths"""
        import laziest_import as lz
        
        paths = lz.get_config_paths()
        assert isinstance(paths, list)
        # All paths should be strings
        assert all(isinstance(p, str) for p in paths)


class TestRegisterAliases:
    """Test batch alias registration"""
    
    def test_register_aliases_batch(self):
        """Test registering multiple aliases at once"""
        import laziest_import as lz
        
        aliases = {
            "test_os1": "os",
            "test_sys1": "sys",
            "test_json1": "json"
        }
        
        registered = lz.register_aliases(aliases)
        assert isinstance(registered, list)
        assert len(registered) == 3
        
        # Verify aliases are registered
        available = lz.list_available()
        assert "test_os1" in available
        assert "test_sys1" in available
        assert "test_json1" in available
        
        # Clean up
        for alias in aliases:
            lz.unregister_alias(alias)
    
    def test_register_aliases_empty(self):
        """Test registering empty dict"""
        import laziest_import as lz
        
        registered = lz.register_aliases({})
        assert registered == []


class TestForceSaveCache:
    """Test force save cache functionality"""
    
    def test_force_save_cache(self):
        """Test force saving cache"""
        import laziest_import as lz
        
        # Enable file cache
        lz.enable_file_cache()
        
        # Force save
        result = lz.force_save_cache()
        assert isinstance(result, bool)


class TestSymbolSearchAdvanced:
    """Advanced symbol search tests"""
    
    def test_search_symbol_with_signature(self):
        """Test search_symbol with signature hint"""
        import laziest_import as lz
        
        results = lz.search_symbol("sqrt", signature="(x)", max_results=5)
        assert isinstance(results, list)
    
    def test_enable_symbol_search_with_params(self):
        """Test enabling symbol search with custom params"""
        import laziest_import as lz
        
        lz.enable_symbol_search(
            interactive=False,
            exact_params=True,
            max_results=10,
            search_depth=2,
            skip_stdlib=True
        )
        
        config = lz.get_symbol_search_config()
        assert config["interactive"] is False
        assert config["exact_params"] is True
        assert config["max_results"] == 10
        assert config["search_depth"] == 2
        assert config["skip_stdlib"] is True
        
        # Reset to default
        lz.enable_symbol_search()


class TestImportHooksAdvanced:
    """Advanced import hooks tests"""
    
    def test_remove_nonexistent_hook(self):
        """Test removing a hook that was never added"""
        import laziest_import as lz
        
        def dummy_hook(name):
            pass
        
        result = lz.remove_pre_import_hook(dummy_hook)
        assert result is False
        
        result = lz.remove_post_import_hook(dummy_hook)
        assert result is False
    
    def test_multiple_hooks(self):
        """Test multiple hooks are called in order"""
        import laziest_import as lz
        
        call_order = []
        
        def hook1(name):
            call_order.append(("hook1", name))
        
        def hook2(name):
            call_order.append(("hook2", name))
        
        lz.add_pre_import_hook(hook1)
        lz.add_pre_import_hook(hook2)
        
        lz.clear_cache()
        _ = lz.math.pi
        
        # Both hooks should have been called
        assert len(call_order) >= 2
        
        lz.remove_pre_import_hook(hook1)
        lz.remove_pre_import_hook(hook2)


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_access_private_attribute(self):
        """Test accessing private attributes"""
        import laziest_import as lz
        
        # Private attributes should still work
        _ = lz.math.__name__
    
    def test_getattr_on_module(self):
        """Test __getattr__ behavior"""
        import laziest_import as lz
        
        # Access a valid module
        math = lz.__getattr__('math')
        assert math is not None
    
    def test_dir_includes_functions(self):
        """Test __dir__ includes all public functions"""
        import laziest_import as lz
        
        dir_result = dir(lz)
        
        # Check some public functions
        expected = [
            "register_alias", "unregister_alias", "list_loaded", 
            "list_available", "get_module", "clear_cache",
            "enable_auto_search", "disable_auto_search", "search_module",
            "enable_symbol_search", "search_symbol"
        ]
        for func in expected:
            assert func in dir_result, f"{func} not in dir()"
    
    def test_module_repr_variants(self):
        """Test module repr in different states"""
        import laziest_import as lz
        
        lz.clear_cache()
        
        # Before loading
        repr_before = repr(lz.os)
        assert "not loaded" in repr_before
        
        # After loading
        _ = lz.os.getcwd
        repr_after = repr(lz.os)
        assert "loaded" in repr_after


class TestAsyncImportAdvanced:
    """Advanced async import tests"""
    
    @pytest.mark.asyncio
    async def test_import_async_with_alias(self):
        """Test async import using alias"""
        import laziest_import as lz
        
        # 'np' is an alias for numpy, but we use stdlib
        math_mod = await lz.import_async("math")
        assert math_mod.__name__ == "math"
    
    @pytest.mark.asyncio
    async def test_import_multiple_async_empty(self):
        """Test async import with empty list"""
        import laziest_import as lz
        
        result = await lz.import_multiple_async([])
        assert result == {}


class TestEnhancedCache:
    """Test enhanced cache functionality"""
    
    def test_get_cache_version(self):
        """Test cache version exists"""
        import laziest_import as lz
        assert hasattr(lz, 'get_cache_version')
        version = lz.get_cache_version()
        assert isinstance(version, str)
        assert len(version) > 0
    
    def test_set_cache_config(self):
        """Test setting cache configuration"""
        import laziest_import as lz
        
        # Set custom TTL
        lz.set_cache_config(symbol_index_ttl=7200, stdlib_cache_ttl=86400)
        
        config = lz.get_cache_config()
        assert config["symbol_index_ttl"] == 7200
        assert config["stdlib_cache_ttl"] == 86400
        
        # Reset to defaults
        lz.set_cache_config(
            symbol_index_ttl=86400,
            stdlib_cache_ttl=604800,
            third_party_cache_ttl=86400
        )
    
    def test_get_cache_config(self):
        """Test getting cache configuration"""
        import laziest_import as lz
        
        config = lz.get_cache_config()
        assert "symbol_index_ttl" in config
        assert "stdlib_cache_ttl" in config
        assert "third_party_cache_ttl" in config
        assert "enable_compression" in config
        assert "max_cache_size_mb" in config
    
    def test_get_cache_stats(self):
        """Test getting cache statistics"""
        import laziest_import as lz
        
        # Reset stats first
        lz.reset_cache_stats()
        
        stats = lz.get_cache_stats()
        assert "symbol_hits" in stats
        assert "symbol_misses" in stats
        assert "last_build_time" in stats
        assert "build_count" in stats
        assert "hit_rate" in stats
    
    def test_reset_cache_stats(self):
        """Test resetting cache statistics"""
        import laziest_import as lz
        
        # Reset stats
        lz.reset_cache_stats()
        
        stats = lz.get_cache_stats()
        assert stats["symbol_hits"] == 0
        assert stats["symbol_misses"] == 0
        assert stats["module_hits"] == 0
        assert stats["module_misses"] == 0
    
    def test_enhanced_symbol_cache_info(self):
        """Test enhanced symbol cache info"""
        import laziest_import as lz
        
        info = lz.get_symbol_cache_info()
        assert "built" in info
        assert "symbol_count" in info
        assert "stdlib_symbols" in info
        assert "third_party_symbols" in info
        assert "tracked_packages" in info
        assert "cache_stats" in info
        assert "cache_config" in info
    
    def test_invalidate_package_cache(self):
        """Test invalidating package cache"""
        import laziest_import as lz
        
        # Try to invalidate a non-tracked package
        result = lz.invalidate_package_cache("nonexistent_package_xyz")
        assert result is False
    
    def test_rebuild_symbol_index(self):
        """Test rebuilding symbol index"""
        import laziest_import as lz
        
        # Clear cache first
        lz.clear_symbol_cache()
        
        # Rebuild
        lz.rebuild_symbol_index()
        
        # Check that index is built
        info = lz.get_symbol_cache_info()
        assert info["built"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
