"""
Comprehensive tests for RC config module (_rcconfig.py).

Tests cover:
- RC config loading
- RC config creation
- RC config values
"""

import pytest
import tempfile
import json
from pathlib import Path


class TestRCConfigInfo:
    """Test RC config info functionality."""

    def test_get_rc_info(self):
        """Test getting RC config info."""
        import laziest_import as lz

        info = lz.get_rc_info()
        assert isinstance(info, dict)
        assert "paths_checked" in info
        assert "active_path" in info
        assert "loaded" in info

    def test_rc_info_paths_checked(self):
        """Test paths_checked in RC info."""
        import laziest_import as lz

        info = lz.get_rc_info()
        assert isinstance(info["paths_checked"], list)

    def test_rc_info_loaded(self):
        """Test loaded flag in RC info."""
        import laziest_import as lz

        info = lz.get_rc_info()
        assert isinstance(info["loaded"], bool)


class TestRCConfigLoading:
    """Test RC config loading functionality."""

    def test_load_rc_config(self):
        """Test loading RC config."""
        import laziest_import as lz

        config = lz.load_rc_config()
        assert isinstance(config, dict)

    def test_reload_rc_config(self):
        """Test reloading RC config."""
        import laziest_import as lz

        config = lz.reload_rc_config()
        assert isinstance(config, dict)

    def test_load_rc_config_returns_dict(self):
        """Test that load_rc_config returns dict even if no file."""
        import laziest_import as lz

        config = lz.load_rc_config()
        # Should return empty dict if no config file
        assert isinstance(config, dict)


class TestRCConfigValues:
    """Test RC config value retrieval."""

    def test_get_rc_value(self):
        """Test getting RC value."""
        import laziest_import as lz

        value = lz.get_rc_value("nonexistent_key_xyz", default="default")
        assert value == "default"

    def test_get_rc_value_default(self):
        """Test getting RC value with default."""
        import laziest_import as lz

        value = lz.get_rc_value("test_key", default=None)
        assert value is None

    def test_get_rc_value_nested(self):
        """Test getting nested RC value."""
        import laziest_import as lz

        # Try getting nested value
        value = lz.get_rc_value("aliases.np", default=None)
        # May or may not exist


class TestRCConfigCreation:
    """Test RC config file creation."""

    def test_create_rc_file(self):
        """Test creating RC file."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.create_rc_file(rc_path)

            assert result.exists()
            assert result == rc_path

    def test_create_rc_file_with_template(self):
        """Test creating RC file with template."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.create_rc_file(rc_path, template=True)

            assert result.exists()
            with open(result) as f:
                data = json.load(f)
            assert isinstance(data, dict)

    def test_create_rc_file_no_template(self):
        """Test creating RC file without template."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.create_rc_file(rc_path, template=False)

            assert result.exists()

    def test_create_rc_file_exists_error(self):
        """Test that creating existing RC file raises error."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            rc_path.touch()

            with pytest.raises(FileExistsError):
                lz.create_rc_file(rc_path)

    def test_create_rc_file_string_path(self):
        """Test creating RC file with string path."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = str(Path(tmpdir) / ".laziestrc")
            result = lz.create_rc_file(rc_path)

            assert result.exists()


class TestRCConfigFormat:
    """Test RC config file format."""

    def test_rc_file_is_valid_json(self):
        """Test that created RC file is valid JSON."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            lz.create_rc_file(rc_path, template=True)

            with open(rc_path) as f:
                data = json.load(f)

            assert isinstance(data, dict)


class TestRCConfigEdgeCases:
    """Test RC config edge cases."""

    def test_get_rc_value_empty_key(self):
        """Test getting RC value with empty key."""
        import laziest_import as lz

        value = lz.get_rc_value("", default="default")
        assert value == "default"

    def test_create_rc_file_in_nonexistent_dir(self):
        """Test creating RC file in non-existent directory."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a nested path that doesn't exist
            nested_dir = Path(tmpdir) / "nested" / "path"
            rc_path = nested_dir / ".laziestrc"

            # Parent directory creation depends on implementation
            try:
                result = lz.create_rc_file(rc_path)
            except (FileNotFoundError, OSError):
                pass  # Expected if parent dir doesn't exist

    def test_reload_multiple_times(self):
        """Test reloading RC config multiple times."""
        import laziest_import as lz

        for _ in range(3):
            config = lz.reload_rc_config()
            assert isinstance(config, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
