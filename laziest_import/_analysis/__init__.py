"""
Analysis subpackage for laziest-import.

Provides:
- Pre-analysis: Scan code files to predict imports
- Profiler: Record module load times and memory usage
- Conflict visualization: Show symbol conflicts
- Environment detection: Detect Python environment
- Preferences persistence: Save/load user preferences
- Dependency tree: Analyze module dependencies
- Benchmark: Performance benchmarking
"""

from typing import List, Optional

# Pre-analysis
from ._preanalyze import (
    DependencyPreAnalyzer,
    PreAnalysisResult,
    _NameVisitor,
)

_analyzer_instance: Optional[DependencyPreAnalyzer] = None


def _get_analyzer() -> DependencyPreAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = DependencyPreAnalyzer()
    return _analyzer_instance


def analyze_file(file_path: str) -> PreAnalysisResult:
    return _get_analyzer().analyze_file(file_path)


def analyze_source(source: str, file_path: str = "<string>") -> PreAnalysisResult:
    return _get_analyzer().analyze_source(source, file_path)


def analyze_directory(
    dir_path: str, recursive: bool = True, exclude: Optional[set] = None
) -> list[PreAnalysisResult]:
    return _get_analyzer().analyze_directory(dir_path, recursive, exclude)


# Profiler
# Benchmark
from ._benchmark import (
    BenchmarkReport,
    BenchmarkResult,
    BenchmarkRunner,
    ImportComparison,
    benchmark,
    benchmark_imports,
    print_benchmark_report,
)

# Conflict visualization
from ._conflict import (
    SymbolConflict,
    find_symbol_conflicts,
    get_conflicts_summary,
    show_conflicts,
)

# Dependency tree analysis
from ._dependency import (
    DependencyAnalyzer,
    DependencyNode,
    DependencyTree,
    dependency_tree,
    print_dependency_tree,
)

# Environment detection
from ._environment import (
    EnvironmentInfo,
    detect_environment,
    show_environment,
)

# Preferences persistence
from ._preferences import (
    apply_preferences,
    clear_preferences,
    get_preferences_path,
    load_preferences,
    save_preferences,
)

# Internal profiler instance (for internal use)
from ._profiler import (
    ImportProfiler,
    ModuleProfile,
    ProfileReport,
    _profiler,
    get_profile_report,
    print_profile_report,
    start_profiling,
    stop_profiling,
)

__all__ = [
    # Pre-analysis
    "PreAnalysisResult",
    "DependencyPreAnalyzer",
    "_NameVisitor",
    "analyze_file",
    "analyze_source",
    "analyze_directory",
    # Profiler
    "ModuleProfile",
    "ProfileReport",
    "ImportProfiler",
    "start_profiling",
    "stop_profiling",
    "get_profile_report",
    "print_profile_report",
    # Conflict visualization
    "SymbolConflict",
    "find_symbol_conflicts",
    "show_conflicts",
    "get_conflicts_summary",
    # Environment detection
    "EnvironmentInfo",
    "detect_environment",
    "show_environment",
    # Preferences persistence
    "save_preferences",
    "load_preferences",
    "apply_preferences",
    "clear_preferences",
    "get_preferences_path",
    # Dependency tree
    "DependencyNode",
    "DependencyTree",
    "DependencyAnalyzer",
    "dependency_tree",
    "print_dependency_tree",
    # Benchmark
    "BenchmarkResult",
    "BenchmarkReport",
    "ImportComparison",
    "BenchmarkRunner",
    "benchmark",
    "benchmark_imports",
    "print_benchmark_report",
]
