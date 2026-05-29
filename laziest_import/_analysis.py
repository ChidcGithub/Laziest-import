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
    BenchmarkReport,
    # Benchmark
    BenchmarkResult,
    BenchmarkRunner,
    DependencyAnalyzer,
    # Dependency tree
    DependencyNode,
    DependencyPreAnalyzer,
    DependencyTree,
    # Environment detection
    EnvironmentInfo,
    ImportComparison,
    ImportProfiler,
    # Profiler
    ModuleProfile,
    # Pre-analysis
    PreAnalysisResult,
    ProfileReport,
    # Conflict visualization
    SymbolConflict,
    _NameVisitor,
    analyze_directory,
    analyze_file,
    analyze_source,
    apply_preferences,
    benchmark,
    benchmark_imports,
    clear_preferences,
    dependency_tree,
    detect_environment,
    find_symbol_conflicts,
    get_conflicts_summary,
    get_preferences_path,
    get_profile_report,
    load_preferences,
    print_benchmark_report,
    print_dependency_tree,
    print_profile_report,
    # Preferences persistence
    save_preferences,
    show_conflicts,
    show_environment,
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
