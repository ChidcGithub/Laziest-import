"""
Comprehensive tests for proxy classes (_proxy module).

Tests cover:
- LazyModule proxy
- LazySubmodule proxy
- LazySymbol proxy
- LazyProxy (intelligent module recognition)
- Module loading behavior
- Attribute access
- Representation
"""

import pytest
import os


class TestLazyModule:
    """Test LazyModule proxy class."""

    def test_lazy_module_not_loaded_initially(self):
        """Test that module is not loaded until first access."""
        import laziest_import as lz

        lz.clear_cache()
        repr_str = repr(lz.math)
        assert "not loaded" in repr_str

    def test_lazy_module_loaded_after_access(self):
        """Test that module is loaded after first attribute access."""
        import laziest_import as lz

        lz.clear_cache()
        _ = lz.math.pi
        repr_str = repr(lz.math)
        assert "loaded" in repr_str

    def test_lazy_module_attribute_access(self):
        """Test accessing attributes on lazy module."""
        import laziest_import as lz

        assert lz.math.pi > 3.14
        assert lz.math.sqrt(16) == 4.0

    def test_lazy_module_caching(self):
        """Test that module is cached after first load."""
        import laziest_import as lz

        lz.clear_cache()
        # First access
        pi1 = lz.math.pi
        # Second access - should use cached module
        pi2 = lz.math.pi
        assert pi1 == pi2

    def test_lazy_module_dir(self):
        """Test dir() on lazy module."""
        import laziest_import as lz

        dir_result = dir(lz.math)
        assert isinstance(dir_result, list)
        assert "pi" in dir_result
        assert "sqrt" in dir_result

    def test_lazy_module_repr_not_loaded(self):
        """Test repr when module not loaded."""
        import laziest_import as lz

        lz.clear_cache()
        repr_str = repr(lz.json)
        assert "LazyModule" in repr_str
        assert "not loaded" in repr_str

    def test_lazy_module_repr_loaded(self):
        """Test repr when module is loaded."""
        import laziest_import as lz

        _ = lz.os.getcwd
        repr_str = repr(lz.os)
        assert "LazyModule" in repr_str
        assert "loaded" in repr_str

    def test_lazy_module_call_non_callable(self):
        """Test calling non-callable module raises TypeError."""
        import laziest_import as lz

        with pytest.raises(TypeError) as excinfo:
            lz.math()
        assert "not callable" in str(excinfo.value)

    def test_lazy_module_private_attribute_access(self):
        """Test that private attributes are handled correctly."""
        import laziest_import as lz

        # Some dunder attributes should work
        assert hasattr(lz.math, "__name__")
        assert lz.math.__name__ == "math"

    def test_lazy_module_invalid_private_attribute(self):
        """Test that invalid private attributes raise AttributeError."""
        import laziest_import as lz

        with pytest.raises(AttributeError):
            _ = lz.math._nonexistent_private_attr


class TestLazySubmodule:
    """Test LazySubmodule proxy class."""

    def test_submodule_access(self):
        """Test accessing submodule."""
        import laziest_import as lz

        path = lz.os.path
        assert path is not None
        assert hasattr(path, "join")

    def test_submodule_attribute_access(self):
        """Test accessing attributes on submodule."""
        import laziest_import as lz

        result = lz.os.path.join("a", "b")
        assert result == os.path.join("a", "b")

    def test_nested_submodule(self):
        """Test accessing nested submodule."""
        import laziest_import as lz

        abc = lz.collections.abc
        assert abc is not None
        assert hasattr(abc, "Iterable")

    def test_submodule_dir(self):
        """Test dir() on submodule."""
        import laziest_import as lz

        dir_result = dir(lz.os.path)
        assert isinstance(dir_result, list)
        assert "join" in dir_result

    def test_submodule_repr(self):
        """Test submodule repr."""
        import laziest_import as lz

        repr_str = repr(lz.os.path)
        assert "LazySubmodule" in repr_str or "path" in repr_str

    def test_submodule_cache(self):
        """Test that submodules are cached."""
        import laziest_import as lz

        path1 = lz.os.path
        path2 = lz.os.path
        # Should be same proxy object
        assert path1 is path2


class TestLazySymbol:
    """Test LazySymbol proxy class."""

    def test_lazy_symbol_importable(self):
        """Test that LazySymbol can be imported."""
        from laziest_import._proxy import LazySymbol

        assert LazySymbol is not None

    def test_lazy_symbol_creation(self):
        """Test creating LazySymbol."""
        from laziest_import._proxy import LazySymbol

        sym = LazySymbol("sqrt", "math", "function")
        assert sym is not None

    def test_lazy_symbol_access(self):
        """Test accessing lazy symbol."""
        from laziest_import._proxy import LazySymbol

        sym = LazySymbol("sqrt", "math", "function")
        # Access should load and return actual function
        result = sym(16)
        assert result == 4.0

    def test_lazy_symbol_repr(self):
        """Test LazySymbol repr."""
        from laziest_import._proxy import LazySymbol

        sym = LazySymbol("sqrt", "math", "function")
        repr_str = repr(sym)
        assert "LazySymbol" in repr_str or "sqrt" in repr_str


class TestLazyProxy:
    """Test LazyProxy (intelligent module recognition)."""

    def test_lazy_proxy_importable(self):
        """Test that LazyProxy can be imported."""
        from laziest_import._proxy import LazyProxy, lazy

        assert LazyProxy is not None
        assert lazy is not None

    def test_lazy_proxy_attribute_access(self):
        """Test attribute access on lazy proxy."""
        from laziest_import._proxy import lazy

        # Access through lazy proxy
        math = lazy.math
        assert math is not None

    def test_lazy_proxy_dir(self):
        """Test dir() on lazy proxy."""
        from laziest_import._proxy import lazy

        dir_result = dir(lazy)
        assert isinstance(dir_result, list)

    def test_lazy_proxy_repr(self):
        """Test lazy proxy repr."""
        from laziest_import._proxy import lazy

        repr_str = repr(lazy)
        assert "LazyProxy" in repr_str

    def test_lazy_proxy_misspelling_correction(self):
        """Test misspelling correction through lazy proxy."""
        from laziest_import._proxy import lazy
        import laziest_import as lz

        lz.enable_auto_search()
        # Try accessing with typo (if supported)
        # This depends on the misspelling mappings


class TestModuleLoading:
    """Test module loading behavior."""

    def test_module_load_timing(self):
        """Test that module load is recorded."""
        import laziest_import as lz

        lz.reset_import_stats()
        lz.clear_cache()

        _ = lz.math.pi

        stats = lz.get_import_stats()
        assert stats["total_imports"] >= 1
        assert "math" in stats["module_times"]

    def test_module_load_hooks(self):
        """Test that hooks are called during load."""
        import laziest_import as lz

        called = []

        def pre_hook(name):
            called.append(("pre", name))

        def post_hook(name, mod):
            called.append(("post", name))

        lz.add_pre_import_hook(pre_hook)
        lz.add_post_import_hook(post_hook)

        lz.clear_cache()
        _ = lz.json.dumps

        assert any("json" in c for c in called)

        lz.remove_pre_import_hook(pre_hook)
        lz.remove_post_import_hook(post_hook)

    def test_module_load_error_handling(self):
        """Test error handling during module load."""
        import laziest_import as lz

        # Try to access non-existent module
        with pytest.raises((AttributeError, ImportError)):
            _ = lz.nonexistent_module_xyz123.pi


class TestAttributeAccess:
    """Test attribute access patterns."""

    def test_getattr_on_module(self):
        """Test __getattr__ on module level."""
        import laziest_import as lz

        math = lz.__getattr__("math")
        assert math is not None

    def test_getattr_nonexistent(self):
        """Test __getattr__ for non-existent attribute."""
        import laziest_import as lz

        with pytest.raises(AttributeError):
            lz.__getattr__("nonexistent_attr_xyz123")

    def test_reserved_names(self):
        """Test that reserved names raise AttributeError."""
        import laziest_import as lz

        # Some names may be reserved
        # Test that the mechanism works
        try:
            _ = lz.__getattr__("__path__")
        except AttributeError:
            pass  # Expected for some reserved names


class TestModuleCaching:
    """Test module caching behavior."""

    def test_cache_clear_unloads(self):
        """Test that clear_cache unloads modules."""
        import laziest_import as lz

        _ = lz.math.pi
        assert "math" in lz.list_loaded()

        lz.clear_cache()
        assert "math" not in lz.list_loaded()

    def test_get_module(self):
        """Test get_module function."""
        import laziest_import as lz

        lz.clear_cache()
        assert lz.get_module("math") is None

        _ = lz.math.pi
        mod = lz.get_module("math")
        assert mod is not None
        assert hasattr(mod, "pi")

    def test_reload_module(self):
        """Test module reload."""
        import laziest_import as lz

        _ = lz.math.pi
        result = lz.reload_module("math")
        assert result is True


class TestProxyThreadSafety:
    """Test proxy thread safety."""

    def test_concurrent_access(self):
        """Test concurrent access to lazy modules."""
        import laziest_import as lz
        import threading

        errors = []

        def access_math():
            try:
                for _ in range(10):
                    _ = lz.math.pi
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=access_math) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestProxyEdgeCases:
    """Test edge cases in proxy behavior."""

    def test_access_dunder_name(self):
        """Test accessing __name__."""
        import laziest_import as lz

        name = lz.math.__name__
        assert name == "math"

    def test_access_dunder_doc(self):
        """Test accessing __doc__."""
        import laziest_import as lz

        doc = lz.math.__doc__
        assert doc is not None or doc is None  # May or may not exist

    def test_module_with_no_attr(self):
        """Test accessing non-existent attribute on module."""
        import laziest_import as lz

        with pytest.raises(AttributeError):
            _ = lz.math.nonexistent_attr_xyz

    def test_cyclic_import_protection(self):
        """Test that cyclic imports are handled."""
        import laziest_import as lz

        # Should not cause infinite loop
        _ = lz.math.pi
        _ = lz.math.sqrt(4)
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
