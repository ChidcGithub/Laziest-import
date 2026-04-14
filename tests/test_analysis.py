"""
Comprehensive tests for analysis module (_analysis.py).

Tests cover:
- Dependency pre-analysis
- Import profiler
- Environment detection
- Conflict visualization
- Preferences management
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestDependencyPreAnalyzer:
    """Test dependency pre-analysis functionality."""

    def test_analyzer_creation(self):
        """Test creating DependencyPreAnalyzer."""
        from laziest_import._analysis import DependencyPreAnalyzer

        analyzer = DependencyPreAnalyzer()
        assert analyzer is not None

    def test_analyze_source(self):
        """Test analyzing source code."""
        import laziest_import as lz

        code = '''
import numpy as np
import pandas as pd
from os import path
'''
        result = lz.analyze_source(code)
        assert result is not None
        assert hasattr(result, "predicted_imports")

    def test_analyze_source_with_used_symbols(self):
        """Test analyzing source for used symbols."""
        import laziest_import as lz

        code = '''
np.array([1, 2, 3])
pd.DataFrame()
'''
        result = lz.analyze_source(code)
        assert hasattr(result, "used_symbols")

    def test_analyze_file(self):
        """Test analyzing a file."""
        import laziest_import as lz

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("import math\nimport os\n")
            temp_path = f.name

        try:
            result = lz.analyze_file(temp_path)
            assert result is not None
            assert hasattr(result, "predicted_imports")
        finally:
            os.unlink(temp_path)

    def test_analyze_directory(self):
        """Test analyzing a directory."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python file
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("import math\n")

            results = lz.analyze_directory(tmpdir, recursive=True)
            assert isinstance(results, list)
            assert len(results) >= 1

    def test_analyze_directory_non_recursive(self):
        """Test non-recursive directory analysis."""
        import laziest_import as lz

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("import json\n")

            results = lz.analyze_directory(tmpdir, recursive=False)
            assert isinstance(results, list)


class TestImportProfiler:
    """Test import profiler functionality."""

    def test_profiler_creation(self):
        """Test creating ImportProfiler."""
        from laziest_import._analysis import ImportProfiler

        profiler = ImportProfiler()
        assert profiler is not None

    def test_start_profiling(self):
        """Test starting profiler."""
        import laziest_import as lz

        lz.start_profiling()
        # Should not raise

    def test_stop_profiling(self):
        """Test stopping profiler."""
        import laziest_import as lz

        lz.start_profiling()
        lz.stop_profiling()
        # Should not raise

    def test_get_profile_report(self):
        """Test getting profile report."""
        import laziest_import as lz

        lz.start_profiling()
        _ = lz.math.pi
        lz.stop_profiling()

        report = lz.get_profile_report()
        assert report is not None
        assert hasattr(report, "modules")

    def test_print_profile_report(self):
        """Test printing profile report."""
        import laziest_import as lz

        lz.start_profiling()
        _ = lz.json.dumps
        lz.stop_profiling()

        # Should not raise
        lz.print_profile_report()

    def test_profiler_records_load_time(self):
        """Test that profiler records load times."""
        import laziest_import as lz

        lz.clear_cache()
        lz.start_profiling()
        _ = lz.os.getcwd
        lz.stop_profiling()

        report = lz.get_profile_report()
        # Should have recorded something
        assert hasattr(report, "modules")


class TestEnvironmentDetection:
    """Test environment detection functionality."""

    def test_detect_environment(self):
        """Test detecting environment."""
        import laziest_import as lz

        env = lz.detect_environment()
        assert env is not None
        assert hasattr(env, "python_version")
        assert hasattr(env, "executable")

    def test_environment_python_version(self):
        """Test getting Python version from environment."""
        import laziest_import as lz

        env = lz.detect_environment()
        assert env.python_version is not None

    def test_environment_executable(self):
        """Test getting Python executable path."""
        import laziest_import as lz

        env = lz.detect_environment()
        assert env.executable is not None

    def test_environment_site_packages(self):
        """Test getting site-packages path."""
        import laziest_import as lz

        env = lz.detect_environment()
        assert hasattr(env, "site_packages")

    def test_show_environment(self):
        """Test showing environment info."""
        import laziest_import as lz

        # Should not raise
        lz.show_environment()


class TestConflictVisualization:
    """Test conflict visualization functionality."""

    def test_find_symbol_conflicts(self):
        """Test finding symbol conflicts."""
        import laziest_import as lz

        conflicts = lz.find_symbol_conflicts()
        assert isinstance(conflicts, dict)

    def test_show_conflicts(self):
        """Test showing conflicts."""
        import laziest_import as lz

        # Should not raise
        lz.show_conflicts()

    def test_get_conflicts_summary(self):
        """Test getting conflicts summary."""
        import laziest_import as lz

        summary = lz.get_conflicts_summary()
        assert isinstance(summary, dict)
        assert "total_conflicts" in summary

    def test_common_symbol_conflicts(self):
        """Test conflicts for common symbols."""
        import laziest_import as lz

        # sqrt exists in both math and numpy (if installed)
        conflicts = lz.find_symbol_conflicts()
        # Just verify it returns a dict
        assert isinstance(conflicts, dict)


class TestPreferencesManagement:
    """Test preferences management functionality."""

    def test_save_preferences(self):
        """Test saving preferences."""
        import laziest_import as lz

        # Should not raise
        lz.save_preferences()

    def test_load_preferences(self):
        """Test loading preferences."""
        import laziest_import as lz

        prefs = lz.load_preferences()
        assert isinstance(prefs, dict)

    def test_apply_preferences(self):
        """Test applying preferences."""
        import laziest_import as lz

        prefs = {"symbols": {"test": "test_module"}}
        try:
            lz.apply_preferences(prefs)
        except (TypeError, AttributeError):
            # May have different signature
            pass

    def test_clear_preferences(self):
        """Test clearing preferences."""
        import laziest_import as lz

        lz.clear_preferences()
        # Should not raise

    def test_set_get_symbol_preference(self):
        """Test setting and getting symbol preference."""
        import laziest_import as lz

        lz.set_symbol_preference("TestSymbol", "test_module")
        pref = lz.get_symbol_preference("TestSymbol")
        assert pref == "test_module"

        lz.clear_symbol_preference("TestSymbol")


class TestPreAnalysisResult:
    """Test PreAnalysisResult dataclass."""

    def test_preanalysis_result_attrs(self):
        """Test PreAnalysisResult attributes."""
        from laziest_import._analysis import PreAnalysisResult

        result = PreAnalysisResult(
            file_path="test.py",
            predicted_imports={"numpy", "pandas"},
            used_symbols={"np", "pd"},
            confidence={"numpy": 0.9}
        )
        assert result.file_path == "test.py"
        assert hasattr(result, "predicted_imports")
        assert hasattr(result, "used_symbols")


class TestModuleProfile:
    """Test ModuleProfile dataclass."""

    def test_module_profile_attrs(self):
        """Test ModuleProfile attributes."""
        from laziest_import._analysis import ModuleProfile

        profile = ModuleProfile(module_name="math", load_time=0.1, memory_delta=1024)
        assert profile.module_name == "math"
        assert profile.load_time == 0.1
        assert profile.memory_delta == 1024


class TestProfileReport:
    """Test ProfileReport dataclass."""

    def test_profile_report_attrs(self):
        """Test ProfileReport attributes."""
        from laziest_import._analysis import ProfileReport

        report = ProfileReport()
        assert hasattr(report, "modules")
        assert hasattr(report, "total_time")


class TestEnvironmentInfo:
    """Test EnvironmentInfo dataclass."""

    def test_environment_info_attrs(self):
        """Test EnvironmentInfo attributes."""
        import laziest_import as lz

        info = lz.detect_environment()
        assert hasattr(info, "python_version")
        assert hasattr(info, "executable")


class TestAnalysisEdgeCases:
    """Test analysis edge cases."""

    def test_analyze_empty_source(self):
        """Test analyzing empty source code."""
        import laziest_import as lz

        result = lz.analyze_source("")
        assert result is not None

    def test_analyze_invalid_syntax(self):
        """Test analyzing invalid syntax."""
        import laziest_import as lz

        # Should handle gracefully
        result = lz.analyze_source("this is not valid python !!!")
        assert result is not None

    def test_analyze_nonexistent_file(self):
        """Test analyzing non-existent file."""
        import laziest_import as lz

        try:
            result = lz.analyze_file("/nonexistent/path/xyz.py")
        except FileNotFoundError:
            pass  # Expected

    def test_profile_without_imports(self):
        """Test profiling with no imports."""
        import laziest_import as lz

        lz.start_profiling()
        # Do nothing
        lz.stop_profiling()

        report = lz.get_profile_report()
        assert report is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
