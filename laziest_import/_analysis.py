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
    "BenchmarkReport",
    # Benchmark
    "BenchmarkResult",
    "BenchmarkRunner",
    "DependencyAnalyzer",
    # Dependency tree
    "DependencyNode",
    "DependencyPreAnalyzer",
    "DependencyTree",
    # Environment detection
    "EnvironmentInfo",
    "ImportComparison",
    "ImportProfiler",
    # Profiler
    "ModuleProfile",
    # Pre-analysis
    "PreAnalysisResult",
    "ProfileReport",
    # Conflict visualization
    "SymbolConflict",
    "_NameVisitor",
    "analyze_directory",
    "analyze_file",
    "analyze_source",
    "apply_preferences",
    "benchmark",
    "benchmark_imports",
    "clear_preferences",
    "dependency_tree",
    "detect_environment",
    "find_symbol_conflicts",
    "get_conflicts_summary",
    "get_preferences_path",
    "get_profile_report",
    "load_preferences",
    "print_benchmark_report",
    "print_dependency_tree",
    "print_profile_report",
    # Preferences persistence
    "save_preferences",
    "show_conflicts",
    "show_environment",
    "start_profiling",
    "stop_profiling",
]
