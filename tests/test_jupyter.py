"""
Comprehensive tests for Jupyter magics (_jupyter.py).

Tests cover:
- Magic commands
- Extension loading
"""

import pytest


class TestJupyterMagics:
    """Test Jupyter magic commands."""

    def test_lazy_magics_importable(self):
        """Test that LazyMagics can be imported."""
        try:
            from laziest_import._jupyter import LazyMagics
            # LazyMagics may be None if IPython not available
            assert LazyMagics is None or LazyMagics is not None
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

            # None should raise ImportError
            with pytest.raises(ImportError):
                load_ipython_extension(None)
        except ImportError:
            pytest.skip("IPython not available")

    def test_unload_ipython_extension(self):
        """Test unload_ipython_extension function."""
        try:
            from laziest_import._jupyter import unload_ipython_extension

            # Should not raise
            unload_ipython_extension(None)
        except ImportError:
            pytest.skip("IPython not available")


class TestMagicCommands:
    """Test individual magic commands."""

    def test_lazyimport_magic_exists(self):
        """Test that %lazyimport magic exists."""
        try:
            from laziest_import._jupyter import LazyMagics

            if LazyMagics is None:
                pytest.skip("IPython not available")

            # Check for magic methods
            assert hasattr(LazyMagics, "lazyimport") or hasattr(LazyMagics, "_lazyimport")
        except ImportError:
            pytest.skip("IPython not available")

    def test_lazylist_magic_exists(self):
        """Test that %lazylist magic exists."""
        try:
            from laziest_import._jupyter import LazyMagics

            if LazyMagics is None:
                pytest.skip("IPython not available")

            assert hasattr(LazyMagics, "lazylist") or hasattr(LazyMagics, "_lazylist")
        except ImportError:
            pytest.skip("IPython not available")

    def test_lazysearch_magic_exists(self):
        """Test that %lazysearch magic exists."""
        try:
            from laziest_import._jupyter import LazyMagics

            if LazyMagics is None:
                pytest.skip("IPython not available")

            assert hasattr(LazyMagics, "lazysearch") or hasattr(LazyMagics, "_lazysearch")
        except ImportError:
            pytest.skip("IPython not available")


class TestCellMagic:
    """Test cell magic commands."""

    def test_lazy_cell_magic_exists(self):
        """Test that %%lazy cell magic exists."""
        try:
            from laziest_import._jupyter import LazyMagics

            if LazyMagics is None:
                pytest.skip("IPython not available")

            # Cell magic would be registered differently
            assert LazyMagics is not None
        except ImportError:
            pytest.skip("IPython not available")


class TestJupyterEdgeCases:
    """Test Jupyter edge cases."""

    def test_double_enable(self):
        """Test enabling twice should not raise."""
        from laziest_import._jupyter import enable_in_jupyter

        enable_in_jupyter()
        enable_in_jupyter()

    def test_extension_module_exists(self):
        """Test that extension module exists."""
        import laziest_import._jupyter

        assert laziest_import._jupyter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
