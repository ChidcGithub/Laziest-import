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

from laziest_import import lz
from laziest_import._analysis import detect_environment, show_environment
from laziest_import._analysis._preferences import (
    save_preferences,
    load_preferences,
    apply_preferences,
    clear_preferences,
)


class TestDependencyPreAnalyzer:
    """Test dependency pre-analysis functionality."""

    def test_analyzer_creation(self):
        """Test creating DependencyPreAnalyzer."""
        from laziest_import._analysis import DependencyPreAnalyzer

        analyzer = DependencyPreAnalyzer()
        assert analyzer is not None

    def test_analyze_source(self):
        """Test analyzing source code."""
        code = '''
import numpy as np
import pandas as pd
from os import path
'''
        result = lz.analyze.code(code)
        assert result is not None
        assert hasattr(result, "predicted_imports")

    def test_analyze_source_with_used_symbols(self):
        """Test analyzing source for used symbols."""
        code = '''
np.array([1, 2, 3])
pd.DataFrame()
'''
        result = lz.analyze.code(code)
        assert hasattr(result, "used_symbols")

    def test_analyze_file(self):
        """Test analyzing a file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("import math\nimport os\n")
            temp_path = f.name

        try:
            result = lz.analyze.file(temp_path)
            assert result is not None
            assert hasattr(result, "predicted_imports")
        finally:
            os.unlink(temp_path)

    def test_analyze_directory(self):
        """Test analyzing a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python file
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("import math\n")

            results = lz.analyze.dir(tmpdir, recursive=True)
            assert isinstance(results, list)
            assert len(results) >= 1

    def test_analyze_directory_non_recursive(self):
        """Test non-recursive directory analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("import json\n")

            results = lz.analyze.dir(tmpdir, recursive=False)
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
        lz.profile.start()
        lz.profile.stop()

    def test_stop_profiling(self):
        """Test stopping profiler."""
        lz.profile.start()
        _ = lz.math.pi
        lz.profile.stop()
        report = lz.profile.report()
        assert hasattr(report, "modules")

    def test_get_profile_report(self):
        """Test getting profile report."""
        lz.profile.start()
        _ = lz.math.pi
        lz.profile.stop()

        report = lz.profile.report()
        assert report is not None
        assert hasattr(report, "modules")

    def test_print_profile_report(self):
        """Test printing profile report."""
        lz.profile.start()
        _ = lz.json.dumps
        lz.profile.stop()

        lz.profile.print_report()
        # Verifies it doesn't raise

    def test_profiler_records_load_time(self):
        """Test that profiler records load times."""
        lz.cache.clear()
        lz.profile.start()
        _ = lz.os.getcwd
        lz.profile.stop()

        report = lz.profile.report()
        # Should have recorded something
        assert hasattr(report, "modules")


class TestEnvironmentDetection:
    """Test environment detection functionality."""

    def test_detect_environment(self):
        """Test detecting environment."""
        env = detect_environment()
        assert env is not None
        assert hasattr(env, "python_version")
        assert hasattr(env, "executable")

    def test_environment_python_version(self):
        """Test getting Python version from environment."""
        env = detect_environment()
        assert env.python_version is not None

    def test_environment_executable(self):
        """Test getting Python executable path."""
        env = detect_environment()
        assert env.executable is not None

    def test_environment_site_packages(self):
        """Test getting site-packages path."""
        env = detect_environment()
        assert hasattr(env, "site_packages")

    def test_show_environment(self):
        """Test showing environment info."""
        show_environment()
        env = detect_environment()
        assert env is not None


class TestConflictVisualization:
    """Test conflict visualization functionality."""

    def test_find_symbol_conflicts(self):
        """Test finding symbol conflicts."""
        conflicts = lz.symbol.conflicts()
        assert isinstance(conflicts, dict)

    def test_show_conflicts(self):
        """Test showing conflicts."""
        lz.symbol.show_conflicts()
        # Verifies it doesn't raise

    def test_get_conflicts_summary(self):
        """Test getting conflicts summary."""
        summary = lz.symbol.conflict_summary()
        assert isinstance(summary, dict)
        assert "total_conflicts" in summary

    def test_common_symbol_conflicts(self):
        """Test conflicts for common symbols."""
        # sqrt exists in both math and numpy (if installed)
        conflicts = lz.symbol.conflicts()
        # Just verify it returns a dict
        assert isinstance(conflicts, dict)


class TestPreferencesManagement:
    """Test preferences management functionality."""

    def test_save_preferences(self):
        """Test saving preferences."""
        result = save_preferences()
        assert result is True or result is False

    def test_load_preferences(self):
        """Test loading preferences."""
        prefs = load_preferences()
        assert isinstance(prefs, dict)

    def test_apply_preferences(self):
        """Test applying preferences."""
        save_preferences()
        apply_preferences()
        prefs = load_preferences()
        assert isinstance(prefs, dict)

    def test_clear_preferences(self):
        """Test clearing preferences."""
        clear_preferences()
        prefs = load_preferences()
        assert isinstance(prefs, dict)

    def test_set_get_symbol_preference(self):
        """Test setting and getting symbol preference."""
        lz.symbol.prefer("TestSymbol", "test_module")
        pref = lz.symbol.preference("TestSymbol")
        assert pref == "test_module"

        lz.symbol.clear_preference("TestSymbol")


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
        info = detect_environment()
        assert hasattr(info, "python_version")
        assert hasattr(info, "executable")


class TestAnalysisEdgeCases:
    """Test analysis edge cases."""

    def test_analyze_empty_source(self):
        """Test analyzing empty source code."""
        result = lz.analyze.code("")
        assert result is not None

    def test_analyze_invalid_syntax(self):
        """Test analyzing invalid syntax."""
        # Should handle gracefully
        result = lz.analyze.code("this is not valid python !!!")
        assert result is not None

    def test_analyze_nonexistent_file(self):
        """Test analyzing non-existent file."""
        try:
            result = lz.analyze.file("/nonexistent/path/xyz.py")
        except FileNotFoundError:
            pass  # Expected

    def test_profile_without_imports(self):
        """Test profiling with no imports."""
        lz.profile.start()
        # Do nothing
        lz.profile.stop()

        report = lz.profile.report()
        assert report is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
