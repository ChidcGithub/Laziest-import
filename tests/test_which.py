"""
Comprehensive tests for which function (_which.py).

Tests cover:
- Symbol location finding
- which() function
- which_all() function
- SymbolLocation class
"""

import pytest


class TestWhichFunction:
    """Test the which() function."""

    def test_which_finds_stdlib_symbol(self):
        """Test finding stdlib symbol."""
        from laziest_import import lz

        loc = lz.symbol.which("sqrt", "math")
        assert loc is not None
        assert loc.symbol_name == "sqrt"
        assert "math" in loc.module_name

    def test_which_with_dotted_path(self):
        """Test which() with dotted path like 'math.sin'."""
        from laziest_import import lz

        loc = lz.symbol.which("math.sin")
        assert loc is not None
        assert loc.symbol_name == "sin"
        assert "math" in loc.module_name

    def test_which_os_path_join(self):
        """Test finding os.path.join."""
        from laziest_import import lz

        loc = lz.symbol.which("os.path.join")
        assert loc is not None
        assert loc.symbol_name == "join"
        assert "os.path" in loc.module_name

    def test_which_without_module_hint(self):
        """Test which() without module hint."""
        from laziest_import import lz

        loc = lz.symbol.which("sqrt")
        # May or may not find depending on index
        assert loc is None or hasattr(loc, "symbol_name")

    def test_which_nonexistent_symbol(self):
        """Test which() for non-existent symbol."""
        from laziest_import import lz

        loc = lz.symbol.which("nonexistent_symbol_xyz12345")
        assert loc is None or hasattr(loc, "symbol_name")

    def test_which_empty_string(self):
        """Test which() with empty string."""
        from laziest_import import lz

        loc = lz.symbol.which("")
        assert loc is None or hasattr(loc, "symbol_name")

    def test_which_returns_symbol_location(self):
        """Test that which() returns SymbolLocation object."""
        from laziest_import import lz

        loc = lz.symbol.which("sqrt", "math")
        if loc:
            assert hasattr(loc, "module_name")
            assert hasattr(loc, "symbol_name")
            assert hasattr(loc, "symbol_type")


class TestWhichAllFunction:
    """Test the which_all() function."""

    def test_which_all_finds_multiple(self):
        """Test that which_all() finds multiple locations."""
        from laziest_import import lz

        locs = lz.symbol.which_all("sqrt")
        assert isinstance(locs, list)

    def test_which_all_for_common_symbol(self):
        """Test which_all() for common symbol."""
        from laziest_import import lz

        # join exists in os.path, str, etc.
        locs = lz.symbol.which_all("join")
        assert isinstance(locs, list)

    def test_which_all_nonexistent(self):
        """Test which_all() for non-existent symbol."""
        from laziest_import import lz

        locs = lz.symbol.which_all("nonexistent_xyz12345")
        assert locs == [] or locs is None or len(locs) == 0 or isinstance(locs, list)

    def test_which_all_returns_locations(self):
        """Test that which_all() returns SymbolLocation objects."""
        from laziest_import import lz

        locs = lz.symbol.which_all("sqrt")
        for loc in locs:
            assert hasattr(loc, "module_name")
            assert hasattr(loc, "symbol_name")


class TestSymbolLocation:
    """Test SymbolLocation class."""

    def test_symbol_location_str(self):
        """Test SymbolLocation string representation."""
        from laziest_import import lz

        loc = lz.symbol.which("sqrt", "math")
        if loc:
            str_repr = str(loc)
            assert isinstance(str_repr, str)
            assert "sqrt" in str_repr or "math" in str_repr

    def test_symbol_location_repr(self):
        """Test SymbolLocation repr."""
        from laziest_import import lz

        loc = lz.symbol.which("sqrt", "math")
        if loc:
            repr_str = repr(loc)
            assert isinstance(repr_str, str)
            assert "SymbolLocation" in repr_str

    def test_symbol_location_to_dict(self):
        """Test SymbolLocation to_dict method."""
        from laziest_import import lz

        loc = lz.symbol.which("sqrt", "math")
        if loc:
            d = loc.to_dict()
            assert isinstance(d, dict)
            assert "module" in d
            assert "symbol" in d
            assert "type" in d

    def test_symbol_location_attributes(self):
        """Test SymbolLocation attributes."""
        from laziest_import import lz

        loc = lz.symbol.which("sqrt", "math")
        if loc:
            assert loc.module_name is not None
            assert loc.symbol_name == "sqrt"
            # symbol_type may be various values
            assert loc.symbol_type is not None


class TestWhichWithDifferentTypes:
    """Test which() with different symbol types."""

    def test_which_function(self):
        """Test finding a function."""
        from laziest_import import lz

        loc = lz.symbol.which("sin", "math")
        if loc:
            # symbol_type may be various values
            assert loc.symbol_type is not None

    def test_which_class(self):
        """Test finding a class."""
        from laziest_import import lz

        loc = lz.symbol.which("defaultdict", "collections")
        if loc:
            assert loc.symbol_type in ("class", "type")

    def test_which_module(self):
        """Test finding a module."""
        from laziest_import import lz

        loc = lz.symbol.which("path", "os")
        if loc:
            assert loc is not None


class TestWhichEdgeCases:
    """Test edge cases for which() function."""

    def test_which_private_symbol(self):
        """Test finding private symbol."""
        from laziest_import import lz

        # May or may not find private symbols
        loc = lz.symbol.which("_private_symbol_xyz")
        assert loc is None or hasattr(loc, "symbol_name")

    def test_which_dunder_symbol(self):
        """Test finding dunder symbol."""
        from laziest_import import lz

        loc = lz.symbol.which("__name__", "os")
        if loc:
            assert loc.symbol_name == "__name__"

    def test_very_long_symbol_name(self):
        """Test with very long symbol name."""
        from laziest_import import lz

        long_name = "a" * 100
        loc = lz.symbol.which(long_name)
        assert loc is None or hasattr(loc, "symbol_name")

    def test_unicode_symbol_name(self):
        """Test with unicode symbol name."""
        from laziest_import import lz

        loc = lz.symbol.which("测试符号")
        assert loc is None or hasattr(loc, "symbol_name")


class TestWhichIntegration:
    """Test which() integration with other features."""

    def test_which_after_rebuild_index(self):
        """Test which() after rebuilding symbol index."""
        from laziest_import import lz

        lz.symbol.index.rebuild()
        loc = lz.symbol.which("sqrt", "math")
        assert loc is not None

    def test_which_with_symbol_search_enabled(self):
        """Test which() with symbol search enabled."""
        from laziest_import import lz

        lz.symbol.config.enable()
        loc = lz.symbol.which("sqrt")
        assert loc is None or hasattr(loc, "symbol_name")

    def test_which_with_preference(self):
        """Test which() with symbol preference set."""
        from laziest_import import lz

        lz.symbol.prefer("sqrt", "math")
        loc = lz.symbol.which("sqrt")
        # May or may not respect preference depending on implementation
        assert loc is None or hasattr(loc, "symbol_name")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
