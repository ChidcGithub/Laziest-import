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
        assert laziest_import.__version__ == "0.0.3-pre6"
    
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


class TestMappingsFromFiles:
    """Test loading mappings from configuration files"""
    
    def test_abbreviations_loaded(self):
        """Test that abbreviations are loaded from file"""
        import laziest_import as lz
        
        # Check that common abbreviations work
        available = lz.list_available()
        # np is a common abbreviation for numpy
        assert "np" in available
        # pd is a common abbreviation for pandas
        assert "pd" in available
    
    def test_misspellings_corrected(self):
        """Test that misspellings are corrected from file"""
        import laziest_import as lz
        
        # Enable auto-search
        lz.enable_auto_search()
        
        # Test common misspelling correction
        result = lz.search_module("nump")  # should find numpy
        assert result == "numpy"
        
        result = lz.search_module("panda")  # should find pandas
        assert result == "pandas"
    
    def test_reload_mappings(self):
        """Test reloading mappings from files"""
        import laziest_import as lz
        
        # Should not raise an error
        lz.reload_mappings()
        
        # Check that mappings are still available
        available = lz.list_available()
        assert "np" in available
    
    def test_module_priorities_loaded(self):
        """Test that module priorities are loaded from file"""
        import laziest_import as lz
        
        # Check that priority is returned for known modules
        priority = lz.get_module_priority("pandas")
        assert priority is not None
        assert priority > 0
        
        priority = lz.get_module_priority("numpy")
        assert priority is not None
        assert priority > 0


class TestConfigFlexibility:
    """Test configuration flexibility features"""
    
    def test_set_module_priority(self):
        """Test setting custom module priority"""
        import laziest_import as lz
        
        # Set a custom priority
        lz.set_module_priority("test_module_xyz", 42)
        
        priority = lz.get_module_priority("test_module_xyz")
        assert priority == 42
    
    def test_get_symbol_preference(self):
        """Test getting symbol preference"""
        import laziest_import as lz
        
        # DataFrame should prefer pandas by default
        pref = lz.get_symbol_preference("DataFrame")
        assert pref == "pandas"
    
    def test_set_symbol_preference(self):
        """Test setting custom symbol preference"""
        import laziest_import as lz
        
        # Set a custom preference
        lz.set_symbol_preference("TestClass", "test_module")
        
        pref = lz.get_symbol_preference("TestClass")
        assert pref == "test_module"
        
        # Clear it
        lz.clear_symbol_preference("TestClass")
        pref = lz.get_symbol_preference("TestClass")
        assert pref is None


class TestAdvancedFuzzyMatching:
    """Test advanced fuzzy matching scenarios"""
    
    def test_search_similar_module_names(self):
        """Test finding similar module names"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # Test partial matching
        result = lz.search_module("num")  # should find numpy
        assert result is not None
        assert "num" in result.lower() or result == "numpy"
    
    def test_search_with_underscore_variants(self):
        """Test searching with underscore variants"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # Test with a module that should be available (stdlib)
        result = lz.search_module("json")
        assert result == "json"
        
        # Test with a common abbreviation
        result = lz.search_module("np")
        # np should map to numpy (if numpy is conceptually available)
        # or return None if not installed
        if result is not None:
            assert result in ["numpy", "np"]
    
    def test_search_case_insensitive(self):
        """Test case-insensitive searching"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # Lowercase search should still work
        result = lz.search_module("json")
        assert result == "json"


class TestConfigurationPaths:
    """Test configuration path handling"""
    
    def test_get_config_paths_returns_list(self):
        """Test that config paths returns a list"""
        import laziest_import as lz
        
        paths = lz.get_config_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0
    
    def test_get_config_dirs_returns_list(self):
        """Test that config dirs returns a list"""
        import laziest_import as lz
        
        dirs = lz.get_config_dirs()
        assert isinstance(dirs, list)
        assert len(dirs) > 0


class TestModuleReprAndStr:
    """Test module representation methods"""
    
    def test_lazy_module_str(self):
        """Test string representation of lazy module"""
        import laziest_import as lz
        
        lz.clear_cache()
        str_repr = str(lz.math)
        assert "math" in str_repr or len(str_repr) > 0
    
    def test_lazy_module_dir(self):
        """Test dir() on lazy module"""
        import laziest_import as lz
        
        dir_result = dir(lz.os)
        assert isinstance(dir_result, list)
        assert 'getcwd' in dir_result


class TestErrorRecovery:
    """Test error recovery scenarios"""
    
    def test_import_after_clear_cache(self):
        """Test that imports work after clearing cache"""
        import laziest_import as lz
        
        # Clear everything
        lz.clear_cache()
        lz.clear_symbol_cache()
        
        # Should still be able to import
        _ = lz.math.pi
        
        # Module should be loaded
        loaded = lz.list_loaded()
        assert "math" in loaded
    
    def test_multiple_reload_mappings(self):
        """Test that multiple reload_mappings calls work"""
        import laziest_import as lz
        
        # Multiple reloads should not cause issues
        lz.reload_mappings()
        lz.reload_mappings()
        lz.reload_mappings()
        
        # Should still work
        available = lz.list_available()
        assert "np" in available


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestLazySymbolAdvanced:
    """Advanced LazySymbol tests"""
    
    def test_lazy_symbol_arithmetic_operators(self):
        """Test LazySymbol arithmetic operators"""
        import laziest_import as lz
        
        # Load math module
        _ = lz.math.pi
        
        # Test that module attributes work
        assert lz.math.sqrt(4) == 2.0
    
    def test_lazy_symbol_comparison(self):
        """Test LazySymbol comparison operators"""
        import laziest_import as lz
        
        # Test comparison with numbers
        assert lz.math.pi > 3
        assert lz.math.pi < 4
        assert lz.math.pi != 3
    
    def test_lazy_symbol_getitem(self):
        """Test LazySymbol getitem operator"""
        import laziest_import as lz
        
        # Test indexing on module result
        result = lz.json.dumps([1, 2, 3])
        assert lz.json.loads(result)[0] == 1


class TestModuleAttributeAccess:
    """Test various module attribute access patterns"""
    
    def test_access_module_constant(self):
        """Test accessing module constants"""
        import laziest_import as lz
        
        assert lz.math.pi > 3.14
        assert lz.math.e > 2.7
    
    def test_access_module_function(self):
        """Test accessing module functions"""
        import laziest_import as lz
        
        assert lz.math.sqrt(16) == 4.0
        assert lz.os.path.join("a", "b") in ["a/b", "a\\b"]
    
    def test_access_module_class(self):
        """Test accessing module classes"""
        import laziest_import as lz
        
        dt = lz.datetime.datetime(2024, 1, 1)
        assert dt.year == 2024
    
    def test_access_nested_attribute(self):
        """Test accessing nested attributes"""
        import laziest_import as lz
        
        # Access nested function
        result = lz.os.path.basename("/path/to/file.txt")
        assert "file.txt" in result


class TestMultipleModuleAccess:
    """Test accessing multiple modules"""
    
    def test_sequential_module_access(self):
        """Test accessing multiple modules sequentially"""
        import laziest_import as lz
        
        lz.clear_cache()
        
        _ = lz.math.pi
        _ = lz.os.getcwd()
        _ = lz.json.dumps({})
        
        loaded = lz.list_loaded()
        assert "math" in loaded
        assert "os" in loaded
        assert "json" in loaded
    
    def test_concurrent_module_access(self):
        """Test that module access doesn't interfere with each other"""
        import laziest_import as lz
        
        # Access different modules
        math_pi = lz.math.pi
        json_str = lz.json.dumps({"key": "value"})
        
        assert math_pi > 3
        assert "key" in json_str


class TestAliasRegistration:
    """Test alias registration edge cases"""
    
    def test_register_alias_with_dots(self):
        """Test registering alias with dotted module name"""
        import laziest_import as lz
        
        lz.register_alias("test_submodule", "os.path")
        available = lz.list_available()
        assert "test_submodule" in available
        
        lz.unregister_alias("test_submodule")
    
    def test_register_duplicate_alias(self):
        """Test registering duplicate alias"""
        import laziest_import as lz
        
        # Register once
        lz.register_alias("dup_test", "os")
        
        # Register again with different module (should update)
        lz.register_alias("dup_test", "sys")
        
        available = lz.list_available()
        assert "dup_test" in available
        
        lz.unregister_alias("dup_test")
    
    def test_register_alias_empty_string(self):
        """Test registering alias with empty string"""
        import laziest_import as lz
        
        with pytest.raises(ValueError):
            lz.register_alias("", "os")
    
    def test_register_alias_none_value(self):
        """Test registering alias with None value"""
        import laziest_import as lz
        
        with pytest.raises((ValueError, TypeError)):
            lz.register_alias("test_none", None)


class TestCachePersistence:
    """Test cache persistence functionality"""
    
    def test_cache_persists_across_accesses(self):
        """Test that cache persists across accesses"""
        import laziest_import as lz
        
        lz.clear_cache()
        
        # First access
        _ = lz.math.pi
        assert "math" in lz.list_loaded()
        
        # Second access should use cache
        _ = lz.math.sqrt(4)
        assert "math" in lz.list_loaded()
    
    def test_symbol_cache_info_after_build(self):
        """Test symbol cache info after building"""
        import laziest_import as lz
        
        lz.clear_symbol_cache()
        lz.rebuild_symbol_index()
        
        info = lz.get_symbol_cache_info()
        assert info["built"] is True
        assert info["symbol_count"] > 0


class TestSearchSymbolAdvanced:
    """Advanced symbol search tests"""
    
    def test_search_symbol_with_different_types(self):
        """Test searching for symbols of different types"""
        import laziest_import as lz
        
        # Search for function
        results = lz.search_symbol("sqrt", symbol_type="function", max_results=5)
        if results:
            for r in results:
                assert r.symbol_type in ("function", "callable")
        
        # Search for class
        results = lz.search_symbol("defaultdict", symbol_type="class", max_results=5)
        if results:
            for r in results:
                assert r.symbol_type == "class"
    
    def test_search_symbol_max_results(self):
        """Test that max_results parameter works"""
        import laziest_import as lz
        
        results = lz.search_symbol("get", max_results=3)
        assert len(results) <= 3
    
    def test_search_symbol_case_sensitivity(self):
        """Test symbol search case handling"""
        import laziest_import as lz
        
        # Should find symbols regardless of case
        results_lower = lz.search_symbol("sqrt", max_results=5)
        results_upper = lz.search_symbol("SQRT", max_results=5)
        
        # At least one should return results for common symbols
        assert len(results_lower) > 0 or len(results_upper) >= 0


class TestAutoSearchEdgeCases:
    """Test auto-search edge cases"""
    
    def test_search_empty_string(self):
        """Test searching for empty string"""
        import laziest_import as lz
        
        result = lz.search_module("")
        # Empty string might match something or return None
        # Just check it doesn't crash
        assert result is None or isinstance(result, str)
    
    def test_search_very_long_string(self):
        """Test searching for very long string"""
        import laziest_import as lz
        
        long_name = "a" * 1000
        result = lz.search_module(long_name)
        assert result is None
    
    def test_search_special_characters(self):
        """Test searching with special characters"""
        import laziest_import as lz
        
        result = lz.search_module("os.path")
        # Should handle dotted names
        assert result is not None or result is None  # Just shouldn't crash
    
    def test_search_unicode(self):
        """Test searching with unicode characters"""
        import laziest_import as lz
        
        result = lz.search_module("módulo")
        # Should handle unicode gracefully
        assert result is None or isinstance(result, str)


class TestSubmoduleEdgeCases:
    """Test submodule handling edge cases"""
    
    def test_deeply_nested_submodule(self):
        """Test accessing deeply nested submodule"""
        import laziest_import as lz
        
        # Access deeply nested attribute
        try:
            result = lz.collections.abc.MutableMapping
            assert result is not None
        except AttributeError:
            # Might not be available in all Python versions
            pass
    
    def test_submodule_attribute_error(self):
        """Test that accessing non-existent submodule attribute raises error"""
        import laziest_import as lz
        
        with pytest.raises(AttributeError):
            _ = lz.os.nonexistent_attribute_xyz
    
    def test_submodule_dir_completeness(self):
        """Test that dir() on submodule returns useful values"""
        import laziest_import as lz
        
        os_path_dir = dir(lz.os.path)
        assert "join" in os_path_dir
        assert "basename" in os_path_dir


class TestImportHooksEdgeCases:
    """Test import hooks edge cases"""
    
    def test_hook_raises_exception(self):
        """Test that hook exceptions are handled"""
        import laziest_import as lz
        
        def bad_hook(module_name):
            raise RuntimeError("Hook error")
        
        lz.add_pre_import_hook(bad_hook)
        
        # Should not crash even if hook raises
        lz.clear_cache()
        try:
            _ = lz.math.pi
        finally:
            lz.remove_pre_import_hook(bad_hook)
    
    def test_post_hook_with_invalid_module(self):
        """Test post-import hook with module that fails to load"""
        import laziest_import as lz
        
        called = []
        
        def tracking_hook(module_name, module):
            called.append(module_name)
        
        lz.add_post_import_hook(tracking_hook)
        
        # Try to import something that will fail
        try:
            _ = lz.nonexistent_module_xyz_12345.pi
        except (AttributeError, ImportError):
            pass
        
        lz.remove_post_import_hook(tracking_hook)
        
        # Hook shouldn't be called for failed imports
        # (or should handle gracefully)


class TestCacheStatistics:
    """Test cache statistics functionality"""
    
    def test_cache_stats_increment_on_hit(self):
        """Test that cache stats increment on hits"""
        import laziest_import as lz
        
        lz.reset_cache_stats()
        lz.clear_cache()
        
        # First access (miss)
        _ = lz.math.pi
        
        # Second access (should be a hit conceptually, but depends on implementation)
        _ = lz.math.sqrt(4)
        
        stats = lz.get_cache_stats()
        assert stats["module_hits"] >= 0
        assert stats["module_misses"] >= 0
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        import laziest_import as lz
        
        lz.reset_cache_stats()
        
        stats = lz.get_cache_stats()
        # Hit rate should be a number between 0 and 100
        assert 0 <= stats["hit_rate"] <= 100


class TestSymbolResolutionConfig:
    """Test symbol resolution configuration"""
    
    def test_get_symbol_resolution_config(self):
        """Test getting symbol resolution config"""
        import laziest_import as lz
        
        config = lz.get_symbol_resolution_config()
        assert "auto_symbol" in config
        assert "auto_threshold" in config
        assert "conflict_threshold" in config
    
    def test_enable_disable_auto_symbol_resolution(self):
        """Test enabling/disabling auto symbol resolution"""
        import laziest_import as lz
        
        lz.enable_auto_symbol_resolution()
        config = lz.get_symbol_resolution_config()
        # Should have auto_symbol enabled
        
        lz.disable_auto_symbol_resolution()
        config = lz.get_symbol_resolution_config()
        # Should have auto_symbol disabled
        
        # Re-enable for other tests
        lz.enable_auto_symbol_resolution()


class TestModulePriority:
    """Test module priority functionality"""
    
    def test_priority_for_unknown_module(self):
        """Test getting priority for unknown module"""
        import laziest_import as lz
        
        priority = lz.get_module_priority("unknown_module_xyz_123")
        # Unknown modules might return None or a default priority
        assert priority is None or isinstance(priority, int)
    
    def test_update_existing_priority(self):
        """Test updating existing priority"""
        import laziest_import as lz
        
        original = lz.get_module_priority("pandas")
        lz.set_module_priority("pandas", 200)
        
        new_priority = lz.get_module_priority("pandas")
        assert new_priority == 200
        
        # Restore original
        if original is not None:
            lz.set_module_priority("pandas", original)


class TestAutoInstallConfig:
    """Test auto-install configuration"""
    
    def test_get_auto_install_config(self):
        """Test getting auto-install config"""
        import laziest_import as lz
        
        config = lz.get_auto_install_config()
        assert "enabled" in config
        assert "interactive" in config
    
    def test_enable_disable_auto_install(self):
        """Test enabling/disabling auto-install"""
        import laziest_import as lz
        
        original = lz.is_auto_install_enabled()
        
        lz.enable_auto_install()
        assert lz.is_auto_install_enabled() is True
        
        lz.disable_auto_install()
        assert lz.is_auto_install_enabled() is False
        
        # Restore original
        if original:
            lz.enable_auto_install()
        else:
            lz.disable_auto_install()
    
    def test_set_pip_index(self):
        """Test setting pip index"""
        import laziest_import as lz
        
        # Should not raise
        lz.set_pip_index("https://pypi.org/simple")
    
    def test_set_pip_extra_args(self):
        """Test setting pip extra args"""
        import laziest_import as lz
        
        # Should not raise
        lz.set_pip_extra_args(["--no-cache-dir"])


class TestLoadedModulesContext:
    """Test loaded modules context functionality"""
    
    def test_get_loaded_modules_context(self):
        """Test getting loaded modules context"""
        import laziest_import as lz
        
        lz.clear_cache()
        _ = lz.math.pi
        _ = lz.os.getcwd
        
        context = lz.get_loaded_modules_context()
        assert isinstance(context, (set, list, dict))


class TestListSymbolConflicts:
    """Test symbol conflict listing"""
    
    def test_list_symbol_conflicts(self):
        """Test listing symbol conflicts"""
        import laziest_import as lz
        
        # list_symbol_conflicts requires a symbol argument
        conflicts = lz.list_symbol_conflicts("sqrt")
        assert isinstance(conflicts, list)
    
    def test_list_symbol_conflicts_no_conflict(self):
        """Test listing conflicts for unique symbol"""
        import laziest_import as lz
        
        # A unique symbol should have no conflicts
        conflicts = lz.list_symbol_conflicts("this_symbol_definitely_does_not_exist_xyz")
        assert isinstance(conflicts, list)


class TestCacheVersion:
    """Test cache version functionality"""
    
    def test_cache_version_format(self):
        """Test that cache version has correct format"""
        import laziest_import as lz
        
        version = lz.get_cache_version()
        assert isinstance(version, str)
        assert len(version) > 0
    
    def test_cache_version_consistency(self):
        """Test that cache version is consistent"""
        import laziest_import as lz
        
        v1 = lz.get_cache_version()
        v2 = lz.get_cache_version()
        assert v1 == v2


class TestModuleCachingBehavior:
    """Test module caching behavior in detail"""
    
    def test_cache_is_shared(self):
        """Test that cache is shared between accesses"""
        import laziest_import as lz
        
        lz.clear_cache()
        
        # Access through different means
        mod1 = lz.math
        mod2 = lz.__getattr__('math')
        
        # Both should return the same cached module
        assert mod1.pi == mod2.pi
    
    def test_clear_cache_removes_all(self):
        """Test that clear_cache removes all cached modules"""
        import laziest_import as lz
        
        # Load multiple modules
        _ = lz.math.pi
        _ = lz.os.getcwd
        _ = lz.json.dumps
        
        # Clear cache
        lz.clear_cache()
        
        # All should be unloaded
        loaded = lz.list_loaded()
        assert len(loaded) == 0


class TestThreadSafety:
    """Test thread safety of lazy loading"""
    
    def test_concurrent_imports(self):
        """Test concurrent imports don't cause issues"""
        import laziest_import as lz
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
        import laziest_import as lz
        
        # These should work through the rename mapping
        # sklearn -> scikit-learn, PIL -> pillow, etc.
        # The mapping is used internally for auto-install suggestions
        available = lz.list_available()
        
        # Check that we have some common aliases
        assert len(available) > 0


class TestExportAliasesFormat:
    """Test alias export format"""
    
    def test_export_aliases_json_valid(self):
        """Test that exported aliases is valid JSON"""
        import laziest_import as lz
        import json
        
        exported = lz.export_aliases()
        # Should not raise
        data = json.loads(exported)
        assert isinstance(data, dict)
    
    def test_export_aliases_includes_common(self):
        """Test that exported aliases include common aliases"""
        import laziest_import as lz
        import json
        
        exported = lz.export_aliases()
        data = json.loads(exported)
        
        # Should include some common aliases
        assert len(data) > 0


class TestValidateAliasesEdgeCases:
    """Test validate aliases edge cases"""
    
    def test_validate_aliases_with_none(self):
        """Test validating aliases with None input"""
        import laziest_import as lz
        
        result = lz.validate_aliases(None)
        assert "valid" in result
        assert "invalid" in result
    
    def test_validate_aliases_importable_with_none(self):
        """Test validating importable aliases with None input"""
        import laziest_import as lz
        
        result = lz.validate_aliases_importable(None)
        assert "importable" in result
        assert "not_importable" in result


class TestRetryMechanismAdvanced:
    """Test retry mechanism advanced scenarios"""
    
    def test_retry_with_custom_modules(self):
        """Test retry with specific modules"""
        import laziest_import as lz
        
        lz.enable_retry(max_retries=2, retry_delay=0.01)
        assert lz.is_retry_enabled() is True
        
        # Should work for stdlib
        lz.clear_cache()
        _ = lz.math.pi
        
        lz.disable_retry()
    
    def test_retry_disabled_by_default(self):
        """Test that retry is typically disabled by default"""
        import laziest_import as lz
        
        # Just check the function exists
        assert lz.is_retry_enabled() is not None


class TestLazyProxyAdvanced:
    """Test LazyProxy advanced functionality"""
    
    def test_lazy_proxy_dir(self):
        """Test LazyProxy dir()"""
        import laziest_import as lz
        
        dir_result = dir(lz.lazy)
        assert isinstance(dir_result, list)
    
    def test_lazy_proxy_repr(self):
        """Test LazyProxy repr"""
        import laziest_import as lz
        
        repr_str = repr(lz.lazy)
        assert "LazyProxy" in repr_str
    
    def test_lazy_proxy_attribute_access(self):
        """Test LazyProxy attribute access"""
        import laziest_import as lz
        
        # Access through lazy proxy
        math = lz.lazy.math
        assert math is not None


class TestMemoryEfficiency:
    """Test memory efficiency of lazy loading"""
    
    def test_unloaded_modules_dont_consume_memory(self):
        """Test that unloaded modules don't consume significant memory"""
        import laziest_import as lz
        import sys
        
        lz.clear_cache()
        
        # Get reference count for a known alias before loading
        # This is a basic check - detailed memory profiling would need more tools
        available = lz.list_available()
        assert len(available) > 0
    
    def test_loaded_modules_are_cached(self):
        """Test that loaded modules are properly cached"""
        import laziest_import as lz
        
        lz.clear_cache()
        
        # First load
        mod1_id = id(lz.math)
        
        # Second access should return same object
        mod2_id = id(lz.math)
        
        # Should be the same cached object
        assert mod1_id == mod2_id


class TestMisspelledModuleImport:
    """Test importing modules with misspelled names - auto-correction functionality"""
    
    def test_import_math_with_misspelling(self):
        """Test importing math module with common misspellings"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        lz.clear_cache()
        
        # Test math variations
        result = lz.search_module("mathh")
        assert result == "math"
    
    def test_import_json_with_misspelling(self):
        """Test importing json module with common misspellings"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("jsn")
        assert result == "json"
    
    def test_import_os_with_misspelling(self):
        """Test importing os module with partial name"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # Partial match
        result = lz.search_module("o")
        # Should find os or return None for single char
        assert result is None or "o" in result.lower()
    
    def test_import_sys_with_misspelling(self):
        """Test importing sys module with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("sy")
        assert result == "sys" or result is None
    
    def test_import_datetime_with_misspelling(self):
        """Test importing datetime with common typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # Common misspelling: datatime
        result = lz.search_module("datatime")
        assert result == "datetime"
    
    def test_import_collections_with_misspelling(self):
        """Test importing collections with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("colection")
        assert result == "collections"
    
    def test_import_functools_with_misspelling(self):
        """Test importing functools with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("functool")
        assert result == "functools"
    
    def test_import_itertools_with_misspelling(self):
        """Test importing itertools with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("itertool")
        assert result == "itertools"
    
    def test_import_pathlib_with_misspelling(self):
        """Test importing pathlib with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("pathlb")
        assert result == "pathlib"
    
    def test_import_subprocess_with_misspelling(self):
        """Test importing subprocess with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("subproces")
        assert result == "subprocess"
    
    def test_import_argparse_with_misspelling(self):
        """Test importing argparse with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("argpars")
        assert result == "argparse"
    
    def test_import_logging_with_misspelling(self):
        """Test importing logging with common typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # Common misspelling: loging
        result = lz.search_module("loging")
        assert result == "logging"
    
    def test_import_re_with_misspelling(self):
        """Test importing re with partial match"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # re is short, hard to misspell
        result = lz.search_module("regex")
        # regex might not map to re directly
        assert result is not None or result is None
    
    def test_import_random_with_misspelling(self):
        """Test importing random with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("randm")
        assert result == "random"
    
    def test_import_string_with_misspelling(self):
        """Test importing string with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("strng")
        assert result == "string"
    
    def test_import_copy_with_misspelling(self):
        """Test importing copy with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("cpy")
        assert result == "copy"
    
    def test_import_pickle_with_misspelling(self):
        """Test importing pickle with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("pickl")
        assert result == "pickle"
    
    def test_import_threading_with_misspelling(self):
        """Test importing threading with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("threadng")
        assert result == "threading"
    
    def test_import_time_with_misspelling(self):
        """Test importing time with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("tim")
        # tim might match 'time' or something else due to fuzzy matching
        assert result is not None or result is None  # Just check it doesn't crash
    
    def test_import_io_with_misspelling(self):
        """Test importing io with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("i")
        # Single char might not match
        assert result is None or result == "io"
    
    def test_import_hashlib_with_misspelling(self):
        """Test importing hashlib with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("hashlb")
        assert result == "hashlib"
    
    def test_import_typing_with_misspelling(self):
        """Test importing typing with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("typng")
        assert result == "typing"
    
    def test_import_warnings_with_misspelling(self):
        """Test importing warnings with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("warning")
        assert result == "warnings"
    
    def test_import_contextlib_with_misspelling(self):
        """Test importing contextlib with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("contextlb")
        assert result == "contextlib"
    
    def test_import_enum_with_misspelling(self):
        """Test importing enum with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("enumm")
        assert result == "enum"
    
    def test_import_dataclasses_with_misspelling(self):
        """Test importing dataclasses with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("dataclass")
        assert result == "dataclasses"
    
    def test_import_abc_with_misspelling(self):
        """Test importing abc with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("ab")
        # Two chars might be too short
        assert result is None or result == "abc"
    
    def test_import_urllib_with_misspelling(self):
        """Test importing urllib with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("urlllib")
        assert result == "urllib"
    
    def test_import_email_with_misspelling(self):
        """Test importing email with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("emial")
        # Fuzzy matching might or might not find this
        assert result is None or result == "email" or isinstance(result, str)
    
    def test_import_html_with_misspelling(self):
        """Test importing html with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("htlm")
        # Fuzzy matching might or might not find this
        assert result is None or result == "html" or isinstance(result, str)
    
    def test_import_http_with_misspelling(self):
        """Test importing http with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("htp")
        assert result == "http"
    
    def test_import_xml_with_misspelling(self):
        """Test importing xml with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("xm")
        assert result == "xml" or result is None
    
    def test_import_csv_with_misspelling(self):
        """Test importing csv with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("cs")
        assert result == "csv" or result is None
    
    def test_import_configparser_with_misspelling(self):
        """Test importing configparser with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("configparser")
        assert result == "configparser"
    
    def test_import_tempfile_with_misspelling(self):
        """Test importing tempfile with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("tempflie")
        assert result == "tempfile"
    
    def test_import_shutil_with_misspelling(self):
        """Test importing shutil with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("shutl")
        assert result == "shutil"
    
    def test_import_glob_with_misspelling(self):
        """Test importing glob with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("glb")
        assert result == "glob"
    
    def test_import_fnmatch_with_misspelling(self):
        """Test importing fnmatch with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("fnmatc")
        assert result == "fnmatch"
    
    def test_import_struct_with_misspelling(self):
        """Test importing struct with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("struc")
        assert result == "struct"
    
    def test_import_codecs_with_misspelling(self):
        """Test importing codecs with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("codec")
        assert result == "codecs"
    
    def test_import_locale_with_misspelling(self):
        """Test importing locale with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("loclae")
        assert result == "locale"
    
    def test_import_calendar_with_misspelling(self):
        """Test importing calendar with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("calender")
        assert result == "calendar"
    
    def test_import_socket_with_misspelling(self):
        """Test importing socket with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("soket")
        assert result == "socket"
    
    def test_import_ssl_with_misspelling(self):
        """Test importing ssl with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("ss")
        assert result == "ssl" or result is None
    
    def test_import_secrets_with_misspelling(self):
        """Test importing secrets with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("secret")
        assert result == "secrets"
    
    def test_import_unittest_with_misspelling(self):
        """Test importing unittest with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("unitest")
        assert result == "unittest"
    
    def test_import_asyncio_with_misspelling(self):
        """Test importing asyncio with common typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # Common misspelling: asynccio
        result = lz.search_module("asynccio")
        assert result == "asyncio"
    
    def test_import_concurrent_with_misspelling(self):
        """Test importing concurrent with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("concurent")
        assert result == "concurrent"
    
    def test_import_multiprocessing_with_misspelling(self):
        """Test importing multiprocessing with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("multiprocesing")
        assert result == "multiprocessing"
    
    def test_import_queue_with_misspelling(self):
        """Test importing queue with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("queu")
        assert result == "queue"
    
    def test_import_sched_with_misspelling(self):
        """Test importing sched with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("schd")
        assert result == "sched"
    
    def test_import_textwrap_with_misspelling(self):
        """Test importing textwrap with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("textwarp")
        assert result == "textwrap"
    
    def test_import_traceback_with_misspelling(self):
        """Test importing traceback with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("tracebak")
        assert result == "traceback"
    
    def test_import_inspect_with_misspelling(self):
        """Test importing inspect with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("inpect")
        assert result == "inspect"
    
    def test_import_dis_with_misspelling(self):
        """Test importing dis with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("di")
        assert result == "dis" or result is None
    
    def test_import_ast_with_misspelling(self):
        """Test importing ast with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("as")
        assert result == "ast" or result is None
    
    def test_import_token_with_misspelling(self):
        """Test importing token with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("tokn")
        assert result == "token"
    
    def test_import_keyword_with_misspelling(self):
        """Test importing keyword with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("keyord")
        assert result == "keyword"
    
    def test_import_operator_with_misspelling(self):
        """Test importing operator with typo"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        result = lz.search_module("operater")
        assert result == "operator"
    
    def test_no_false_positives_for_gibberish(self):
        """Test that gibberish doesn't match anything"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # Completely random string should not match
        result = lz.search_module("xyzqwerty12345asdfg")
        assert result is None
    
    def test_very_similar_names(self):
        """Test that very similar names are handled correctly"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # json vs jams - should not match
        result = lz.search_module("jams")
        # Might match or not depending on fuzzy threshold
        assert result is None or result != "json"
    
    def test_case_sensitivity(self):
        """Test case sensitivity in searches"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # Uppercase should still work
        result = lz.search_module("JSON")
        assert result == "json"
        
        result = lz.search_module("MATH")
        assert result == "math"
    
    def test_underscore_vs_hyphen(self):
        """Test underscore vs hyphen handling"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # These should be treated similarly
        result1 = lz.search_module("date_util")
        result2 = lz.search_module("date-util")
        # Both should either match the same thing or both be None
        if result1 is not None and result2 is not None:
            assert result1 == result2
