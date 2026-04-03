"""
laziest_import Test Suite
"""

import sys
import pytest

# Ensure laziest_import can be imported
sys.path.insert(0, '.')


class TestBasicImport:
    """Test basic import functionality"""
    
    def test_module_version(self):
        """Test module version exists"""
        import laziest_import
        assert hasattr(laziest_import, '__version__')
        assert laziest_import.__version__ == "0.0.2-pre6"
    
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
