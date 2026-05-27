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
        from laziest_import import lz

        info = lz.rc.info()
        assert isinstance(info, dict)
        assert "paths_checked" in info
        assert "active_path" in info
        assert "loaded" in info

    def test_rc_info_paths_checked(self):
        """Test paths_checked in RC info."""
        from laziest_import import lz

        info = lz.rc.info()
        assert isinstance(info["paths_checked"], list)

    def test_rc_info_loaded(self):
        """Test loaded flag in RC info."""
        from laziest_import import lz

        info = lz.rc.info()
        assert isinstance(info["loaded"], bool)


class TestRCConfigLoading:
    """Test RC config loading functionality."""

    def test_load_rc_config(self):
        """Test loading RC config."""
        from laziest_import import lz

        config = lz.rc.load()
        assert isinstance(config, dict)

    def test_reload_rc_config(self):
        """Test reloading RC config."""
        from laziest_import import lz

        config = lz.rc.reload()
        assert isinstance(config, dict)

    def test_load_rc_config_returns_dict(self):
        """Test that load_rc_config returns dict even if no file."""
        from laziest_import import lz

        config = lz.rc.load()
        # Should return empty dict if no config file
        assert isinstance(config, dict)


class TestRCConfigValues:
    """Test RC config value retrieval."""

    def test_get_rc_value(self):
        """Test getting RC value."""
        from laziest_import import lz

        value = lz.rc.get("nonexistent_key_xyz", default="default")
        assert value == "default"

    def test_get_rc_value_default(self):
        """Test getting RC value with default."""
        from laziest_import import lz

        value = lz.rc.get("test_key", default=None)
        assert value is None

    def test_get_rc_value_nested(self):
        """Test getting nested RC value."""
        from laziest_import import lz

        value = lz.rc.get("aliases.np", default=None)
        assert value is None or isinstance(value, str)


class TestRCConfigCreation:
    """Test RC config file creation."""

    def test_create_rc_file(self):
        """Test creating RC file."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.rc.create(rc_path)

            assert result.exists()
            assert result == rc_path

    def test_create_rc_file_with_template(self):
        """Test creating RC file with template."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.rc.create(rc_path, template=True)

            assert result.exists()
            with open(result) as f:
                data = json.load(f)
            assert isinstance(data, dict)

    def test_create_rc_file_no_template(self):
        """Test creating RC file without template."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            result = lz.rc.create(rc_path, template=False)

            assert result.exists()

    def test_create_rc_file_exists_error(self):
        """Test that creating existing RC file raises error."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            rc_path.touch()

            with pytest.raises(FileExistsError):
                lz.rc.create(rc_path)

    def test_create_rc_file_string_path(self):
        """Test creating RC file with string path."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = str(Path(tmpdir) / ".laziestrc")
            result = lz.rc.create(rc_path)

            assert result.exists()


class TestRCConfigFormat:
    """Test RC config file format."""

    def test_rc_file_is_valid_json(self):
        """Test that created RC file is valid JSON."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            rc_path = Path(tmpdir) / ".laziestrc"
            lz.rc.create(rc_path, template=True)

            with open(rc_path) as f:
                data = json.load(f)

            assert isinstance(data, dict)


class TestRCConfigEdgeCases:
    """Test RC config edge cases."""

    def test_get_rc_value_empty_key(self):
        """Test getting RC value with empty key."""
        from laziest_import import lz

        value = lz.rc.get("", default="default")
        assert value == "default"

    def test_create_rc_file_in_nonexistent_dir(self):
        """Test creating RC file in non-existent directory."""
        from laziest_import import lz

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "path"
            rc_path = nested_dir / ".laziestrc"

            result = lz.rc.create(rc_path)
            assert result.exists()

    def test_reload_multiple_times(self):
        """Test reloading RC config multiple times."""
        from laziest_import import lz

        for _ in range(3):
            config = lz.rc.reload()
            assert isinstance(config, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
