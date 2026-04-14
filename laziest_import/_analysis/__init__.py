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

# Pre-analysis
from ._preanalyze import (
    PreAnalysisResult,
    DependencyPreAnalyzer,
    _NameVisitor,
)

# Profiler
from ._profiler import (
    ModuleProfile,
    ProfileReport,
    ImportProfiler,
    start_profiling,
    stop_profiling,
    get_profile_report,
    print_profile_report,
)

# Conflict visualization
from ._conflict import (
    SymbolConflict,
    find_symbol_conflicts,
    show_conflicts,
    get_conflicts_summary,
)

# Environment detection
from ._environment import (
    EnvironmentInfo,
    detect_environment,
    show_environment,
)

# Preferences persistence
from ._preferences import (
    save_preferences,
    load_preferences,
    apply_preferences,
    clear_preferences,
    get_preferences_path,
)

# Dependency tree analysis
from ._dependency import (
    DependencyNode,
    DependencyTree,
    DependencyAnalyzer,
    dependency_tree,
    print_dependency_tree,
)

# Benchmark
from ._benchmark import (
    BenchmarkResult,
    BenchmarkReport,
    ImportComparison,
    BenchmarkRunner,
    benchmark,
    benchmark_imports,
    print_benchmark_report,
)

# Internal profiler instance (for internal use)
from ._profiler import _profiler

__all__ = [
    # Pre-analysis
    "PreAnalysisResult",
    "DependencyPreAnalyzer",
    "_NameVisitor",
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
