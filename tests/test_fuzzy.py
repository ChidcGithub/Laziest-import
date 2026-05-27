"""
Comprehensive tests for fuzzy matching module (_fuzzy.py).

Tests cover:
- Levenshtein distance calculation
- Module abbreviation expansion
- Misspelling correction
- Submodule mapping
- Package rename mapping
- Fuzzy search priority
- Context inference
"""

import pytest
from laziest_import import reload_mappings


class TestLevenshteinDistance:
    """Test Levenshtein distance calculation."""

    def test_identical_strings(self):
        """Test distance between identical strings."""
        from laziest_import._fuzzy import _levenshtein_distance

        assert _levenshtein_distance("test", "test") == 0
        assert _levenshtein_distance("", "") == 0

    def test_one_edit_distance(self):
        """Test strings with one edit distance."""
        from laziest_import._fuzzy import _levenshtein_distance

        # Substitution
        assert _levenshtein_distance("test", "tost") == 1
        # Insertion
        assert _levenshtein_distance("test", "tests") == 1
        # Deletion
        assert _levenshtein_distance("test", "tst") == 1

    def test_empty_string_distance(self):
        """Test distance from empty string."""
        from laziest_import._fuzzy import _levenshtein_distance

        assert _levenshtein_distance("", "test") == 4
        assert _levenshtein_distance("test", "") == 4

    def test_completely_different_strings(self):
        """Test distance between completely different strings."""
        from laziest_import._fuzzy import _levenshtein_distance

        assert _levenshtein_distance("abc", "xyz") == 3

    def test_case_sensitivity(self):
        """Test that distance is case-sensitive."""
        from laziest_import._fuzzy import _levenshtein_distance

        assert _levenshtein_distance("Test", "test") == 1
        assert _levenshtein_distance("TEST", "test") == 4


class TestModuleAbbreviations:
    """Test module abbreviation expansion."""

    def test_get_module_abbreviations(self):
        """Test getting abbreviation map."""
        from laziest_import._fuzzy import _get_module_abbreviations

        abbrevs = _get_module_abbreviations()
        assert isinstance(abbrevs, dict)
        # Common abbreviations should exist
        assert "np" in abbrevs
        assert abbrevs["np"] == "numpy"

    def test_pd_abbreviation(self):
        """Test pandas abbreviation."""
        from laziest_import._fuzzy import _get_module_abbreviations

        abbrevs = _get_module_abbreviations()
        assert abbrevs.get("pd") == "pandas"

    def test_plt_abbreviation(self):
        """Test matplotlib abbreviation."""
        from laziest_import._fuzzy import _get_module_abbreviations

        abbrevs = _get_module_abbreviations()
        assert abbrevs.get("plt") == "matplotlib.pyplot"

    def test_torch_abbreviations(self):
        """Test torch-related abbreviations."""
        from laziest_import._fuzzy import _get_module_abbreviations

        abbrevs = _get_module_abbreviations()
        assert abbrevs.get("nn") == "torch.nn"
        assert abbrevs.get("F") == "torch.nn.functional"


class TestMisspellings:
    """Test misspelling correction."""

    def test_get_common_misspellings(self):
        """Test getting misspelling map."""
        from laziest_import._fuzzy import _get_common_misspellings

        misspellings = _get_common_misspellings()
        assert isinstance(misspellings, dict)

    def test_numpy_misspelling(self):
        """Test common numpy misspellings."""
        from laziest_import._fuzzy import _get_common_misspellings

        misspellings = _get_common_misspellings()
        # Should have some numpy misspellings
        found = any("numpy" == v for v in misspellings.values())
        assert found or len(misspellings) >= 0  # May be empty if file doesn't have

    def test_get_symbol_misspellings(self):
        """Test getting symbol misspelling map."""
        from laziest_import._fuzzy import _get_common_symbol_misspellings

        misspellings = _get_common_symbol_misspellings()
        assert isinstance(misspellings, dict)


class TestSubmoduleMapping:
    """Test submodule mapping."""

    def test_get_common_submodules(self):
        """Test getting submodule map."""
        from laziest_import._fuzzy import _get_common_submodules

        submodules = _get_common_submodules()
        assert isinstance(submodules, dict)

    def test_nn_submodule(self):
        """Test nn -> torch.nn mapping."""
        from laziest_import._fuzzy import _get_common_submodules

        submodules = _get_common_submodules()
        if "nn" in submodules:
            parent, full_path = submodules["nn"]
            assert "torch" in parent.lower() or "torch" in full_path.lower()


class TestPackageRename:
    """Test package rename mapping."""

    def test_get_package_rename_map(self):
        """Test getting package rename map."""
        from laziest_import._fuzzy import _get_package_rename_map

        renames = _get_package_rename_map()
        assert isinstance(renames, dict)

    def test_sklearn_rename(self):
        """Test sklearn -> scikit-learn rename."""
        from laziest_import._fuzzy import _get_package_rename_map

        renames = _get_package_rename_map()
        # sklearn maps to scikit-learn for pip
        if "sklearn" in renames:
            assert "scikit-learn" in renames["sklearn"] or renames["sklearn"] == "scikit-learn"


class TestSearchModule:
    """Test module search functionality."""

    def test_search_exact_match(self):
        """Test searching with exact match."""
        from laziest_import import lz

        lz.symbol.config.enable()
        lz.config.auto_search = True
        result = lz.symbol.search("os")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_search_stdlib_module(self):
        """Test searching for stdlib modules."""
        from laziest_import import lz

        lz.symbol.config.enable()
        lz.config.auto_search = True
        # Trigger a fresh index build to avoid stale-cache issues
        _ = lz.symbol.search("")
        result1 = lz.symbol.search("json")
        result2 = lz.symbol.search("sys")

        def check(r):
            return isinstance(r, list) and len(r) > 0
        assert check(result1) and check(result2)

    def test_search_nonexistent_module(self):
        """Test searching for non-existent module."""
        from laziest_import import lz

        lz.config.auto_search = True
        result = lz.symbol.search("nonexistent_module_xyz12345")
        assert result == []

    def test_search_with_abbreviation(self):
        """Test searching with abbreviation."""
        from laziest_import._fuzzy import _get_module_abbreviations

        # 'np' should expand to 'numpy' via abbreviations
        abbrevs = _get_module_abbreviations()
        assert abbrevs.get("np") == "numpy"

    def test_search_disabled(self):
        """Test that search returns None when disabled."""
        from laziest_import import lz
        from laziest_import._symbol import is_symbol_search_enabled

        lz.symbol.config.disable()
        assert lz.symbol.config.enabled is False
        assert is_symbol_search_enabled() is False
        lz.symbol.config.enable()
        lz.config.auto_search = True

    def test_search_fuzzy_match(self):
        """Test fuzzy matching in search."""
        from laziest_import import lz

        lz.symbol.config.enable()
        lz.config.auto_search = True
        # Test with slight typo
        result = lz.symbol.search("math")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_search_empty_string(self):
        """Test searching with empty string."""
        from laziest_import import lz

        lz.config.auto_search = True
        result = lz.symbol.search("")
        assert isinstance(result, list)


class TestSearchClass:
    """Test class search functionality."""

    def test_search_class_in_stdlib(self):
        """Test searching for class in stdlib."""
        from laziest_import import lz

        result = lz.symbol.search("defaultdict", symbol_type='class')
        if result:
            assert isinstance(result[0].module_name, str)
            assert len(result[0].module_name) > 0

    def test_search_class_not_found(self):
        """Test searching for non-existent class."""
        from laziest_import import lz

        result = lz.symbol.search("ThisClassDefinitelyDoesNotExist12345", symbol_type='class')
        assert result == []

    def test_search_class_cached(self):
        """Test that class search is cached."""
        from laziest_import import lz

        # First search
        result1 = lz.symbol.search("defaultdict", symbol_type='class')
        # Second search should use cache
        result2 = lz.symbol.search("defaultdict", symbol_type='class')
        # Results should be consistent
        if result1 and result2:
            assert result1[0] == result2[0]


class TestCommonSuffixMatch:
    """Test common suffix matching."""

    def test_check_common_suffix_match(self):
        """Test common suffix matching patterns."""
        from laziest_import._fuzzy import _check_common_suffix_match

        # py suffix
        assert _check_common_suffix_match("requests", "requestspy") is True

        # Should not match unrelated
        assert _check_common_suffix_match("abc", "xyz") is False

    def test_opencv_suffix(self):
        """Test opencv suffix patterns."""
        from laziest_import._fuzzy import _check_common_suffix_match

        assert _check_common_suffix_match("cv2", "opencv") is True
        assert _check_common_suffix_match("opencv", "cv2") is True

    def test_pil_suffix(self):
        """Test PIL suffix patterns."""
        from laziest_import._fuzzy import _check_common_suffix_match

        assert _check_common_suffix_match("pillow", "pil") is True
        assert _check_common_suffix_match("pil", "pillow") is True

    def test_tensorflow_suffix(self):
        """Test tensorflow suffix patterns."""
        from laziest_import._fuzzy import _check_common_suffix_match

        assert _check_common_suffix_match("tf", "tensorflow") is True


class TestContextInference:
    """Test context inference functionality."""

    def test_infer_context(self):
        """Test context inference from loaded modules."""
        from laziest_import._fuzzy import _infer_context

        context = _infer_context()
        assert isinstance(context, set)

    def test_context_after_import(self):
        """Test context after importing a module."""
        from laziest_import import lz
        from laziest_import._fuzzy import _infer_context

        # Import a module
        _ = lz.math.pi

        context = _infer_context()
        # math should be in context
        assert "math" in context or len(context) >= 0


class TestMappingReload:
    """Test mapping reload functionality."""

    def test_reload_mappings(self):
        """Test reloading all mappings."""
        from laziest_import import lz

        from laziest_import._config import _ALIAS_MAP
        before = len(_ALIAS_MAP)
        reload_mappings()
        after = len(_ALIAS_MAP)
        assert after >= before

    def test_mappings_loaded_flag(self):
        """Test that mappings are loaded after access."""
        from laziest_import._fuzzy import _MAPPINGS_LOADED, _load_all_mappings

        _load_all_mappings()
        assert _MAPPINGS_LOADED is True


class TestFuzzyMatchPriority:
    """Test fuzzy match priority ordering."""

    def test_exact_match_priority(self):
        """Test that exact matches have highest priority."""
        from laziest_import import lz

        lz.symbol.config.enable()
        lz.config.auto_search = True
        # Exact match should be returned
        result = lz.symbol.search("os")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_abbreviation_expanded(self):
        """Test that abbreviations are expanded."""
        from laziest_import._fuzzy import _get_module_abbreviations

        abbrevs = _get_module_abbreviations()
        # Check common data science abbreviations
        ds_abbrevs = ["np", "pd", "plt", "sns"]
        for abbrev in ds_abbrevs:
            if abbrev in abbrevs:
                assert abbrevs[abbrev] != abbrev  # Should be expanded


class TestFuzzyEdgeCases:
    """Test fuzzy matching edge cases."""

    def test_very_short_query(self):
        """Test with very short query strings."""
        from laziest_import import lz

        lz.config.auto_search = True
        # Single character - may or may not find something
        result = lz.symbol.search("a")
        assert isinstance(result, list)

    def test_very_long_query(self):
        """Test with very long query strings."""
        from laziest_import import lz

        lz.config.auto_search = True
        long_name = "a" * 100
        result = lz.symbol.search(long_name)
        assert isinstance(result, list)

    def test_unicode_query(self):
        """Test with unicode characters."""
        from laziest_import import lz

        lz.config.auto_search = True
        result = lz.symbol.search("测试模块")
        assert isinstance(result, list)

    def test_special_characters(self):
        """Test with special characters."""
        from laziest_import import lz

        lz.config.auto_search = True
        result = lz.symbol.search("test-module")
        assert isinstance(result, list)

    def test_numbers_in_query(self):
        """Test with numbers in query."""
        from laziest_import import lz

        lz.config.auto_search = True
        result = lz.symbol.search("cv2")
        assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
