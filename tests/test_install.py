"""
Comprehensive tests for auto-install module (_install.py).

Tests cover:
- Auto-install configuration
- Package installation
- Pip index settings
"""

import pytest

from laziest_import._install import (
    rebuild_module_cache,
    set_pip_extra_args,
    set_pip_index,
)


class TestAutoInstallConfig:
    """Test auto-install configuration."""

    def test_get_auto_install_config(self):
        """Test getting auto-install config."""
        from laziest_import import lz

        config = lz.install.auto
        assert isinstance(config, dict)
        assert "enabled" in config

    def test_auto_install_disabled_by_default(self):
        """Test that auto-install is disabled by default."""
        from laziest_import import lz

        assert lz.install.enabled is False

    def test_enable_auto_install(self):
        """Test enabling auto-install."""
        from laziest_import import lz

        lz.install.enable(interactive=False, allow_non_interactive=True)
        assert lz.install.enabled is True

        # Disable for safety
        lz.install.disable()

    def test_disable_auto_install(self):
        """Test disabling auto-install."""
        from laziest_import import lz

        lz.install.enable(interactive=False, allow_non_interactive=True)
        lz.install.disable()
        assert lz.install.enabled is False


class TestPipIndex:
    """Test pip index settings."""

    def test_set_pip_index(self):
        """Test setting custom pip index."""
        from laziest_import import lz

        set_pip_index("https://pypi.org/simple")
        config = lz.install.auto
        assert config["index"] == "https://pypi.org/simple"

        # Reset
        set_pip_index(None)

    def test_set_pip_index_none(self):
        """Test setting pip index to None."""
        from laziest_import._config import _AUTO_INSTALL_CONFIG

        set_pip_index(None)
        assert _AUTO_INSTALL_CONFIG["index"] is None


class TestPipExtraArgs:
    """Test extra pip arguments."""

    def test_set_pip_extra_args(self):
        """Test setting extra pip arguments."""
        from laziest_import import lz

        set_pip_extra_args(["--no-cache-dir", "--quiet"])
        config = lz.install.auto
        assert "--no-cache-dir" in config["extra_args"]
        assert "--quiet" in config["extra_args"]

        # Reset
        set_pip_extra_args([])

    def test_set_pip_extra_args_empty(self):
        """Test setting empty extra args."""
        from laziest_import import lz

        set_pip_extra_args([])
        config = lz.install.auto
        assert config["extra_args"] == []


class TestPackageInstall:
    """Test package installation functionality."""

    def test_install_package_function_exists(self):
        """Test that install_package function exists."""
        from laziest_import import lz

        assert callable(lz.install.package)

    def test_rebuild_module_cache(self):
        """Test rebuild_module_cache function."""

        result = rebuild_module_cache()
        assert result is None or result is True


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
        from laziest_import import lz

        lz.install.enable(interactive=True)
        config = lz.install.auto
        assert config["interactive"] is True

        lz.install.disable()

    def test_non_interactive_mode(self):
        """Test non-interactive mode."""
        from laziest_import import lz

        lz.install.enable(interactive=False, allow_non_interactive=True)
        config = lz.install.auto
        assert config["interactive"] is False

        lz.install.disable()


class TestAutoInstallEdgeCases:
    """Test auto-install edge cases."""

    def test_enable_multiple_times(self):
        """Test enabling multiple times."""
        from laziest_import import lz

        lz.install.enable(interactive=False, allow_non_interactive=True)
        lz.install.enable(interactive=False, allow_non_interactive=True)
        assert lz.install.enabled is True

        lz.install.disable()

    def test_disable_when_already_disabled(self):
        """Test disabling when already disabled."""
        from laziest_import import lz

        lz.install.disable()
        lz.install.disable()
        assert lz.install.enabled is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
