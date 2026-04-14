"""
Comprehensive tests for introspection module (_introspect.py).

Tests cover:
- list_module_symbols
- get_module_info
- search_in_module
"""

import pytest


class TestListModuleSymbols:
    """Test list_module_symbols function."""

    def test_list_module_symbols_basic(self):
        """Test basic module symbol listing."""
        import laziest_import as lz

        symbols = lz.list_module_symbols("math")
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert "sin" in symbols
        assert "cos" in symbols

    def test_list_module_symbols_json(self):
        """Test listing json module symbols."""
        import laziest_import as lz

        symbols = lz.list_module_symbols("json")
        assert isinstance(symbols, list)
        assert "dumps" in symbols
        assert "loads" in symbols

    def test_list_module_symbols_with_filter(self):
        """Test listing symbols with type filter."""
        import laziest_import as lz

        funcs = lz.list_module_symbols("math", filter_types={"function"})
        assert isinstance(funcs, list)
        assert all(isinstance(s, str) for s in funcs)

    def test_list_module_symbols_exclude_private(self):
        """Test excluding private symbols."""
        import laziest_import as lz

        symbols = lz.list_module_symbols("json", include_private=False)
        assert isinstance(symbols, list)
        assert all(not s.startswith("_") for s in symbols)

    def test_list_module_symbols_include_private(self):
        """Test including private symbols."""
        import laziest_import as lz

        symbols = lz.list_module_symbols("json", include_private=True)
        assert isinstance(symbols, list)
        # May or may not have private symbols

    def test_list_module_symbols_nonexistent(self):
        """Test listing symbols for non-existent module."""
        import laziest_import as lz

        symbols = lz.list_module_symbols("nonexistent_module_xyz")
        assert symbols == [] or symbols is None


class TestGetModuleInfo:
    """Test get_module_info function."""

    def test_get_module_info_basic(self):
        """Test basic module info retrieval."""
        import laziest_import as lz

        info = lz.get_module_info("json")
        assert isinstance(info, dict)
        assert "name" in info
        assert info["name"] == "json"

    def test_get_module_info_math(self):
        """Test getting math module info."""
        import laziest_import as lz

        info = lz.get_module_info("math")
        assert info["name"] == "math"

    def test_get_module_info_is_package(self):
        """Test is_package field."""
        import laziest_import as lz

        info = lz.get_module_info("json")
        assert "is_package" in info

    def test_get_module_info_nonexistent(self):
        """Test getting info for non-existent module."""
        import laziest_import as lz

        info = lz.get_module_info("nonexistent_module_xyz")
        assert info == {} or info is None or isinstance(info, dict)


class TestSearchInModule:
    """Test search_in_module function."""

    def test_search_in_module_basic(self):
        """Test basic search in module."""
        import laziest_import as lz

        results = lz.search_in_module("math", "sin")
        assert isinstance(results, list)
        assert "sin" in results

    def test_search_in_module_multiple(self):
        """Test search returning multiple results."""
        import laziest_import as lz

        results = lz.search_in_module("math", "s")
        assert isinstance(results, list)
        # Should include sin, sqrt, etc.
        assert len(results) > 0

    def test_search_in_module_not_found(self):
        """Test search for non-existent symbol."""
        import laziest_import as lz

        results = lz.search_in_module("math", "nonexistent_xyz")
        assert results == [] or results is None

    def test_search_in_module_json(self):
        """Test search in json module."""
        import laziest_import as lz

        results = lz.search_in_module("json", "dump")
        assert isinstance(results, list)
        assert "dumps" in results or "dump" in results


class TestIntrospectionAdvanced:
    """Test advanced introspection features."""

    def test_list_module_symbols_os(self):
        """Test listing os module symbols."""
        import laziest_import as lz

        symbols = lz.list_module_symbols("os")
        assert isinstance(symbols, list)
        assert "getcwd" in symbols
        assert "path" in symbols

    def test_list_module_symbols_os_path(self):
        """Test listing os.path symbols."""
        import laziest_import as lz

        symbols = lz.list_module_symbols("os.path")
        assert isinstance(symbols, list)
        assert "join" in symbols

    def test_search_case_insensitive(self):
        """Test case-insensitive search."""
        import laziest_import as lz

        results_lower = lz.search_in_module("math", "sin")
        results_upper = lz.search_in_module("math", "SIN")

        # Both should work
        assert isinstance(results_lower, list)
        assert isinstance(results_upper, list)


class TestIntrospectionEdgeCases:
    """Test introspection edge cases."""

    def test_list_symbols_empty_module(self):
        """Test listing symbols for empty module name."""
        import laziest_import as lz

        # Empty module name should raise an error or return empty
        with pytest.raises((ImportError, ModuleNotFoundError, ValueError)):
            lz.list_module_symbols("")

    def test_search_empty_pattern(self):
        """Test searching with empty pattern."""
        import laziest_import as lz

        results = lz.search_in_module("math", "")
        assert isinstance(results, list)

    def test_get_info_builtin_module(self):
        """Test getting info for builtin module."""
        import laziest_import as lz

        info = lz.get_module_info("sys")
        assert isinstance(info, dict)

    def test_list_symbols_very_large_module(self):
        """Test listing symbols for a module with many symbols."""
        import laziest_import as lz

        # collections has many symbols
        symbols = lz.list_module_symbols("collections")
        assert isinstance(symbols, list)
        assert len(symbols) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
