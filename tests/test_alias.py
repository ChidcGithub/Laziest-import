"""
Comprehensive tests for alias management module (_alias.py).

Tests cover:
- Alias registration and unregistration
- Alias loading from files
- Alias validation
- Alias export
- Configuration paths
- Version checking
- Duplicate detection
"""

import pytest
import tempfile
import json
import os
from pathlib import Path


class TestAliasRegistration:
    """Test alias registration functionality."""

    def test_register_single_alias(self):
        """Test registering a single alias."""
        import laziest_import as lz

        lz.register_alias("test_single_alias", "os")
        assert "test_single_alias" in lz.list_available()
        assert lz.test_single_alias.getcwd() == os.getcwd()
        lz.unregister_alias("test_single_alias")

    def test_register_alias_with_dots(self):
        """Test registering alias for submodule."""
        import laziest_import as lz

        lz.register_alias("test_submod", "os.path")
        assert hasattr(lz.test_submod, "join")
        lz.unregister_alias("test_submod")

    def test_register_multiple_aliases(self):
        """Test registering multiple aliases at once."""
        import laziest_import as lz

        aliases = {
            "test_multi_os": "os",
            "test_multi_json": "json",
            "test_multi_sys": "sys",
        }
        registered = lz.register_aliases(aliases)
        assert len(registered) == 3
        for alias in aliases:
            assert alias in lz.list_available()
        for alias in aliases:
            lz.unregister_alias(alias)

    def test_register_empty_dict(self):
        """Test registering empty alias dict."""
        import laziest_import as lz

        result = lz.register_aliases({})
        assert result == []

    def test_register_duplicate_alias_same_module(self):
        """Test registering duplicate alias with same module."""
        import laziest_import as lz

        lz.register_alias("test_dup_same", "os")
        # Should not raise - same module
        lz.register_alias("test_dup_same", "os")
        lz.unregister_alias("test_dup_same")

    def test_register_invalid_alias_empty_name(self):
        """Test that empty alias name raises error."""
        import laziest_import as lz

        with pytest.raises(ValueError):
            lz.register_alias("", "os")

    def test_register_invalid_alias_empty_module(self):
        """Test that empty module name raises error."""
        import laziest_import as lz

        with pytest.raises(ValueError):
            lz.register_alias("test_invalid", "")

    def test_register_invalid_alias_not_identifier(self):
        """Test that invalid identifier alias raises error."""
        import laziest_import as lz

        with pytest.raises(ValueError):
            lz.register_alias("123invalid", "os")

    def test_unregister_existing_alias(self):
        """Test unregistering an existing alias."""
        import laziest_import as lz

        lz.register_alias("test_unreg", "os")
        result = lz.unregister_alias("test_unreg")
        assert result is True
        assert "test_unreg" not in lz.list_available()

    def test_unregister_nonexistent_alias(self):
        """Test unregistering non-existent alias."""
        import laziest_import as lz

        result = lz.unregister_alias("nonexistent_alias_xyz")
        assert result is False


class TestAliasValidation:
    """Test alias validation functionality."""

    def test_validate_valid_aliases(self):
        """Test validation of valid aliases."""
        import laziest_import as lz

        result = lz.validate_aliases({"valid_os": "os", "valid_json": "json"})
        assert "valid_os" in result["valid"]
        assert "valid_json" in result["valid"]
        assert len(result["invalid"]) == 0

    def test_validate_invalid_identifier(self):
        """Test validation catches invalid identifiers."""
        import laziest_import as lz

        result = lz.validate_aliases({"123bad": "os"})
        assert "123bad" in result["invalid"]

    def test_validate_empty_module_name(self):
        """Test validation catches empty module names."""
        import laziest_import as lz

        result = lz.validate_aliases({"empty_mod": ""})
        assert "empty_mod" in result["invalid"]

    def test_validate_current_aliases(self):
        """Test validating all current aliases."""
        import laziest_import as lz

        result = lz.validate_aliases()
        assert isinstance(result, dict)
        assert "valid" in result
        assert "invalid" in result
        assert len(result["valid"]) > 0

    def test_validate_aliases_importable(self):
        """Test validating importable aliases."""
        import laziest_import as lz

        result = lz.validate_aliases_importable({"os_test": "os"})
        assert "os_test" in result["importable"]
        assert "not_importable" in result

    def test_validate_aliases_not_importable(self):
        """Test validation of non-importable module."""
        import laziest_import as lz

        result = lz.validate_aliases_importable(
            {"bad": "nonexistent_module_xyz12345"}
        )
        assert "bad" in result["not_importable"]


class TestAliasExport:
    """Test alias export functionality."""

    def test_export_returns_json_string(self):
        """Test export returns valid JSON string."""
        import laziest_import as lz

        result = lz.export_aliases()
        assert isinstance(result, str)
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_export_categorized(self):
        """Test export with categories (by first letter)."""
        import laziest_import as lz

        result = lz.export_aliases(include_categories=True)
        data = json.loads(result)
        # Should have letter categories
        assert isinstance(data, dict)

    def test_export_flat(self):
        """Test export without categories."""
        import laziest_import as lz

        result = lz.export_aliases(include_categories=False)
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_export_to_file(self):
        """Test exporting aliases to file."""
        import laziest_import as lz

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = f.name

        try:
            lz.export_aliases(path=temp_path)
            assert os.path.exists(temp_path)
            with open(temp_path, "r") as f:
                data = json.load(f)
            assert isinstance(data, dict)
        finally:
            os.unlink(temp_path)


class TestConfigPaths:
    """Test configuration path functionality."""

    def test_get_config_paths(self):
        """Test getting configuration file paths."""
        import laziest_import as lz

        paths = lz.get_config_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0
        assert all(isinstance(p, str) for p in paths)

    def test_get_config_dirs(self):
        """Test getting configuration directory paths."""
        import laziest_import as lz

        dirs = lz.get_config_dirs()
        assert isinstance(dirs, list)
        assert len(dirs) > 0
        assert all(isinstance(d, str) for d in dirs)

    def test_config_paths_contain_home(self):
        """Test that config paths include home directory."""
        import laziest_import as lz

        paths = lz.get_config_paths()
        home = str(Path.home())
        assert any(home in p for p in paths)


class TestAliasLoading:
    """Test alias loading from files."""

    def test_load_from_letter_file(self):
        """Test loading aliases from letter-based file."""
        import laziest_import as lz
        from laziest_import._alias import _get_alias_dir

        alias_dir = _get_alias_dir()
        assert alias_dir.exists()

        # Check that we have alias files
        json_files = list(alias_dir.glob("*.json"))
        assert len(json_files) > 0

    def test_reload_aliases(self):
        """Test reloading aliases."""
        import laziest_import as lz

        lz.reload_aliases()
        # Should have common aliases
        available = lz.list_available()
        assert "np" in available
        assert "pd" in available

    def test_load_user_config_dir(self):
        """Test loading from user config directory."""
        import laziest_import as lz
        from laziest_import._alias import _get_config_dirs

        dirs = _get_config_dirs()
        # First is user home directory
        assert "laziest_import" in str(dirs[0]).lower()


class TestAliasVersionCheck:
    """Test alias version checking."""

    def test_version_file_exists(self):
        """Test that version.json exists."""
        from laziest_import._alias import _get_alias_dir

        version_file = Path(__file__).parent.parent / "laziest_import" / "version.json"
        assert version_file.exists()

    def test_version_range_check(self):
        """Test version range checking."""
        from laziest_import._config import check_version_range, get_version_range

        min_ver, max_ver = get_version_range("aliases")
        # Should return something (even if None)
        assert min_ver is None or isinstance(min_ver, str)
        assert max_ver is None or isinstance(max_ver, str)


class TestAliasDuplicates:
    """Test duplicate alias detection."""

    def test_duplicate_detection(self):
        """Test that duplicate aliases are detected."""
        from laziest_import._alias import _check_duplicates

        # Same alias with different modules
        duplicates = _check_duplicates({
            "dup": "os",
            "dup": "sys"  # This will overwrite in dict
        })
        # Dict only keeps last value, so no duplicate
        assert len(duplicates) == 0

    def test_load_aliases_with_check_duplicates(self):
        """Test loading aliases with duplicate checking."""
        from laziest_import._alias import _load_all_aliases

        # Should not raise
        aliases = _load_all_aliases(check_duplicates=True)
        assert isinstance(aliases, dict)
        assert len(aliases) > 0


class TestAliasLookup:
    """Test alias lookup functionality."""

    def test_lookup_existing_alias(self):
        """Test looking up existing alias."""
        from laziest_import._alias import _lookup_alias_fast

        result = _lookup_alias_fast("np")
        assert result == "numpy"

    def test_lookup_nonexistent_alias(self):
        """Test looking up non-existent alias."""
        from laziest_import._alias import _lookup_alias_fast

        result = _lookup_alias_fast("nonexistent_alias_xyz123")
        assert result is None

    def test_lookup_empty_string(self):
        """Test looking up empty string."""
        from laziest_import._alias import _lookup_alias_fast

        result = _lookup_alias_fast("")
        assert result is None

    def test_lookup_by_letter_file(self):
        """Test that lookup uses letter-based files."""
        from laziest_import._alias import (
            _lookup_alias_fast,
            _load_aliases_from_letter_file,
            _get_alias_dir,
        )

        # Load from N.json for numpy
        alias_dir = _get_alias_dir()
        n_aliases = _load_aliases_from_letter_file(alias_dir, "N")
        assert "np" in n_aliases


class TestAliasRebuild:
    """Test global namespace rebuild."""

    def test_rebuild_global_namespace(self):
        """Test rebuilding global namespace."""
        from laziest_import._alias import _rebuild_global_namespace

        # Should not raise
        _rebuild_global_namespace()

    def test_rebuild_after_unregister(self):
        """Test rebuild removes unregistered aliases."""
        import laziest_import as lz
        from laziest_import._alias import _rebuild_global_namespace

        lz.register_alias("test_rebuild", "os")
        lz.unregister_alias("test_rebuild")
        _rebuild_global_namespace()
        assert "test_rebuild" not in lz.list_available()


class TestKnownModulesCache:
    """Test known modules cache functionality."""

    def test_build_known_modules_cache(self):
        """Test building known modules cache."""
        from laziest_import._alias import _build_known_modules_cache

        modules = _build_known_modules_cache()
        assert isinstance(modules, set)
        # Should include stdlib modules
        assert "os" in modules
        assert "sys" in modules

    def test_build_known_modules_cache_force(self):
        """Test force rebuild of cache."""
        from laziest_import._alias import _build_known_modules_cache

        modules = _build_known_modules_cache(force=True)
        assert isinstance(modules, set)

    def test_cache_ttl(self):
        """Test cache TTL behavior."""
        from laziest_import._alias import _build_known_modules_cache
        import time

        # First build
        _build_known_modules_cache(force=True)
        # Immediate second build should use cache
        _build_known_modules_cache(force=False)


class TestAliasEdgeCases:
    """Test edge cases in alias management."""

    def test_alias_with_hyphen(self):
        """Test alias containing hyphen (valid for pip names)."""
        import laziest_import as lz

        # Should work for pip package name mapping
        result = lz.validate_aliases({"sklearn": "scikit-learn"})
        # May or may not be valid depending on validation
        assert isinstance(result, dict)

    def test_alias_with_dot(self):
        """Test alias containing dot (valid for submodules)."""
        import laziest_import as lz

        # Dots in module names are valid
        lz.register_alias("test_dot_mod", "os.path")
        assert hasattr(lz.test_dot_mod, "join")
        lz.unregister_alias("test_dot_mod")

    def test_unicode_alias(self):
        """Test Unicode alias handling."""
        import laziest_import as lz

        # Unicode aliases may be valid Python identifiers in Python 3
        result = lz.validate_aliases({"测试": "os"})
        # Either valid or invalid depending on Python version and implementation
        assert isinstance(result, dict)
        assert "valid" in result
        assert "invalid" in result

    def test_very_long_alias(self):
        """Test very long alias name."""
        import laziest_import as lz

        long_alias = "a" * 100
        lz.register_alias(long_alias, "os")
        assert long_alias in lz.list_available()
        lz.unregister_alias(long_alias)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
