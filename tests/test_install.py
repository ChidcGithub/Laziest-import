"""
Comprehensive tests for auto-install module (_install.py).

Tests cover:
- Auto-install configuration
- Package installation
- Pip index settings
"""

import pytest


class TestAutoInstallConfig:
    """Test auto-install configuration."""

    def test_get_auto_install_config(self):
        """Test getting auto-install config."""
        import laziest_import as lz

        config = lz.get_auto_install_config()
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_auto_install_disabled_by_default(self):
        """Test that auto-install is disabled by default."""
        import laziest_import as lz

        assert lz.is_auto_install_enabled() is False

    def test_enable_auto_install(self):
        """Test enabling auto-install."""
        import laziest_import as lz

        lz.enable_auto_install(interactive=False)
        assert lz.is_auto_install_enabled() is True

        # Disable for safety
        lz.disable_auto_install()

    def test_disable_auto_install(self):
        """Test disabling auto-install."""
        import laziest_import as lz

        lz.enable_auto_install(interactive=False)
        lz.disable_auto_install()
        assert lz.is_auto_install_enabled() is False


class TestPipIndex:
    """Test pip index settings."""

    def test_set_pip_index(self):
        """Test setting custom pip index."""
        import laziest_import as lz

        lz.set_pip_index("https://pypi.org/simple")
        config = lz.get_auto_install_config()
        assert config["index"] == "https://pypi.org/simple"

        # Reset
        lz.set_pip_index(None)

    def test_set_pip_index_none(self):
        """Test setting pip index to None."""
        import laziest_import as lz

        lz.set_pip_index(None)
        config = lz.get_auto_install_config()
        assert config["index"] is None


class TestPipExtraArgs:
    """Test extra pip arguments."""

    def test_set_pip_extra_args(self):
        """Test setting extra pip arguments."""
        import laziest_import as lz

        lz.set_pip_extra_args(["--no-cache-dir", "--quiet"])
        config = lz.get_auto_install_config()
        assert "--no-cache-dir" in config["extra_args"]
        assert "--quiet" in config["extra_args"]

        # Reset
        lz.set_pip_extra_args([])

    def test_set_pip_extra_args_empty(self):
        """Test setting empty extra args."""
        import laziest_import as lz

        lz.set_pip_extra_args([])
        config = lz.get_auto_install_config()
        assert config["extra_args"] == []


class TestPackageInstall:
    """Test package installation functionality."""

    def test_install_package_function_exists(self):
        """Test that install_package function exists."""
        import laziest_import as lz

        assert callable(lz.install_package)

    def test_rebuild_module_cache(self):
        """Test rebuild_module_cache function."""
        import laziest_import as lz

        # Should not raise
        lz.rebuild_module_cache()


class TestPackageRename:
    """Test package rename functionality."""

    def test_get_pip_package_name(self):
        """Test getting pip package name."""
        from laziest_import._install import _get_pip_package_name

        # sklearn -> scikit-learn
        result = _get_pip_package_name("sklearn")
        assert result == "scikit-learn"

    def test_get_pip_package_name_unchanged(self):
        """Test pip package name unchanged."""
        from laziest_import._install import _get_pip_package_name

        # numpy stays numpy
        result = _get_pip_package_name("numpy")
        assert result == "numpy"


class TestAutoInstallSafety:
    """Test auto-install safety features."""

    def test_interactive_mode(self):
        """Test interactive mode setting."""
        import laziest_import as lz

        lz.enable_auto_install(interactive=True)
        config = lz.get_auto_install_config()
        assert config["interactive"] is True

        lz.disable_auto_install()

    def test_non_interactive_mode(self):
        """Test non-interactive mode."""
        import laziest_import as lz

        lz.enable_auto_install(interactive=False)
        config = lz.get_auto_install_config()
        assert config["interactive"] is False

        lz.disable_auto_install()


class TestAutoInstallEdgeCases:
    """Test auto-install edge cases."""

    def test_enable_multiple_times(self):
        """Test enabling multiple times."""
        import laziest_import as lz

        lz.enable_auto_install(interactive=False)
        lz.enable_auto_install(interactive=False)
        assert lz.is_auto_install_enabled() is True

        lz.disable_auto_install()

    def test_disable_when_already_disabled(self):
        """Test disabling when already disabled."""
        import laziest_import as lz

        lz.disable_auto_install()
        lz.disable_auto_install()
        assert lz.is_auto_install_enabled() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
