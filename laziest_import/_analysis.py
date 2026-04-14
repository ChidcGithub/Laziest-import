"""
Dependency analysis and profiling tools for laziest-import.

Features:
- Pre-analysis: Scan code files to predict imports
- Profiler: Record module load times and memory usage
- Conflict visualization: Show symbol conflicts
- Dependency tree: Analyze module dependencies
- Benchmark: Performance benchmarking

This module re-exports all public API from the _analysis subpackage for backward compatibility.
"""

# Re-export all public API from the subpackage
from ._analysis import (
    # Pre-analysis
    PreAnalysisResult,
    DependencyPreAnalyzer,
    _NameVisitor,
    # Profiler
    ModuleProfile,
    ProfileReport,
    ImportProfiler,
    start_profiling,
    stop_profiling,
    get_profile_report,
    print_profile_report,
    # Conflict visualization
    SymbolConflict,
    find_symbol_conflicts,
    show_conflicts,
    get_conflicts_summary,
    # Environment detection
    EnvironmentInfo,
    detect_environment,
    show_environment,
    # Preferences persistence
    save_preferences,
    load_preferences,
    apply_preferences,
    clear_preferences,
    get_preferences_path,
    # Dependency tree
    DependencyNode,
    DependencyTree,
    DependencyAnalyzer,
    dependency_tree,
    print_dependency_tree,
    # Benchmark
    BenchmarkResult,
    BenchmarkReport,
    ImportComparison,
    BenchmarkRunner,
    benchmark,
    benchmark_imports,
    print_benchmark_report,
    # Internal
    _profiler,
)

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
