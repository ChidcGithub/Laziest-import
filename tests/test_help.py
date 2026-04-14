"""
Comprehensive tests for help system (_help.py).

Tests cover:
- Help function
- Help topics
- Help output format
"""

import pytest


class TestHelpFunction:
    """Test the help() function."""

    def test_help_returns_string(self):
        """Test that help() returns a string."""
        import laziest_import as lz

        result = lz.help()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_contains_library_name(self):
        """Test that help output contains library name."""
        import laziest_import as lz

        result = lz.help()
        assert "laziest-import" in result.lower()

    def test_help_none_shows_overview(self):
        """Test help(None) shows overview."""
        import laziest_import as lz

        result = lz.help(None)
        assert isinstance(result, str)
        assert len(result) > 0


class TestHelpTopics:
    """Test help with specific topics."""

    def test_help_quickstart(self):
        """Test help('quickstart')."""
        import laziest_import as lz

        result = lz.help("quickstart")
        assert isinstance(result, str)
        assert "Quick Start" in result or "quick" in result.lower()

    def test_help_lazy(self):
        """Test help('lazy')."""
        import laziest_import as lz

        result = lz.help("lazy")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_alias(self):
        """Test help('alias')."""
        import laziest_import as lz

        result = lz.help("alias")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_symbol(self):
        """Test help('symbol')."""
        import laziest_import as lz

        result = lz.help("symbol")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_cache(self):
        """Test help('cache')."""
        import laziest_import as lz

        result = lz.help("cache")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_config(self):
        """Test help('config')."""
        import laziest_import as lz

        result = lz.help("config")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_async(self):
        """Test help('async')."""
        import laziest_import as lz

        result = lz.help("async")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_hooks(self):
        """Test help('hooks')."""
        import laziest_import as lz

        result = lz.help("hooks")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_api(self):
        """Test help('api')."""
        import laziest_import as lz

        result = lz.help("api")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_jupyter(self):
        """Test help('jupyter')."""
        import laziest_import as lz

        result = lz.help("jupyter")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_help_which(self):
        """Test help('which')."""
        import laziest_import as lz

        result = lz.help("which")
        assert isinstance(result, str)
        assert len(result) > 0


class TestHelpUnknownTopic:
    """Test help with unknown topics."""

    def test_help_unknown_topic(self):
        """Test help() with unknown topic."""
        import laziest_import as lz

        result = lz.help("nonexistent_topic_xyz123")
        assert "unknown topic" in result.lower() or "not found" in result.lower() or "did you mean" in result.lower()

    def test_help_gibberish(self):
        """Test help() with gibberish input."""
        import laziest_import as lz

        result = lz.help("asdfghjkl")
        assert isinstance(result, str)


class TestHelpFormat:
    """Test help output format."""

    def test_help_is_multiline(self):
        """Test that help output is multiline."""
        import laziest_import as lz

        result = lz.help()
        assert "\n" in result

    def test_help_quickstart_has_examples(self):
        """Test that quickstart has code examples."""
        import laziest_import as lz

        result = lz.help("quickstart")
        # Should contain some Python code or examples
        assert "import" in result.lower() or "from" in result.lower() or "usage" in result.lower()


class TestHelpEdgeCases:
    """Test help edge cases."""

    def test_help_empty_string(self):
        """Test help('') with empty string."""
        import laziest_import as lz

        result = lz.help("")
        assert isinstance(result, str)

    def test_help_very_long_topic(self):
        """Test help() with very long topic name."""
        import laziest_import as lz

        long_topic = "a" * 100
        result = lz.help(long_topic)
        assert isinstance(result, str)

    def test_help_unicode_topic(self):
        """Test help() with unicode topic."""
        import laziest_import as lz

        result = lz.help("帮助")
        assert isinstance(result, str)

    def test_help_special_chars(self):
        """Test help() with special characters."""
        import laziest_import as lz

        result = lz.help("test-topic")
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
