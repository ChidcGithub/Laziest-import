"""
Performance benchmark module.

Benchmark import performance and compare with regular imports.
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
import time
import sys
import gc
import importlib
from pathlib import Path


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    memory_before: int = 0
    memory_after: int = 0
    memory_delta: int = 0


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""
    results: List[BenchmarkResult] = field(default_factory=list)
    comparison: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "results": [
                {
                    "name": r.name,
                    "iterations": r.iterations,
                    "total_time": r.total_time,
                    "avg_time": r.avg_time,
                    "min_time": r.min_time,
                    "max_time": r.max_time,
                    "std_dev": r.std_dev,
                    "memory_delta": r.memory_delta,
                }
                for r in self.results
            ],
            "comparison": self.comparison,
            "recommendations": self.recommendations,
        }


@dataclass
class ImportComparison:
    """Comparison between lazy and regular import."""
    module_name: str
    regular_import_time: float
    lazy_import_time: float
    speedup_factor: float
    regular_memory: int = 0
    lazy_memory: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "module_name": self.module_name,
            "regular_import_time": self.regular_import_time,
            "lazy_import_time": self.lazy_import_time,
            "speedup_factor": self.speedup_factor,
            "regular_memory": self.regular_memory,
            "lazy_memory": self.lazy_memory,
        }


class BenchmarkRunner:
    """Run performance benchmarks."""
    
    def __init__(
        self,
        warmup_iterations: int = 3,
        default_iterations: int = 10,
        use_gc: bool = True,
    ):
        """
        Initialize benchmark runner.
        
        Args:
            warmup_iterations: Number of warmup iterations
            default_iterations: Default number of benchmark iterations
            use_gc: Whether to run garbage collection between runs
        """
        self.warmup_iterations = warmup_iterations
        self.default_iterations = default_iterations
        self.use_gc = use_gc
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            import tracemalloc
            if tracemalloc.is_tracing():
                return tracemalloc.get_traced_memory()[0]
        except ImportError:
            pass
        return 0
    
    def _measure_time(
        self,
        func: Callable,
        iterations: int,
    ) -> List[float]:
        """Measure execution time over multiple iterations."""
        times = []
        
        # Warmup
        for _ in range(self.warmup_iterations):
            try:
                func()
            except Exception:
                pass
        
        # Actual measurements
        for _ in range(iterations):
            if self.use_gc:
                gc.collect()
            
            start = time.perf_counter()
            try:
                func()
            except Exception:
                pass
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        return times
    
    def _calculate_stats(self, times: List[float]) -> Tuple[float, float, float, float]:
        """Calculate statistics from timing data."""
        if not times:
            return 0.0, 0.0, 0.0, 0.0
        
        avg = sum(times) / len(times)
        min_t = min(times)
        max_t = max(times)
        
        # Standard deviation
        if len(times) > 1:
            variance = sum((t - avg) ** 2 for t in times) / len(times)
            std_dev = variance ** 0.5
        else:
            std_dev = 0.0
        
        return avg, min_t, max_t, std_dev
    
    def benchmark_function(
        self,
        name: str,
        func: Callable,
        iterations: Optional[int] = None,
    ) -> BenchmarkResult:
        """
        Benchmark a function.
        
        Args:
            name: Name for the benchmark
            func: Function to benchmark
            iterations: Number of iterations (default: self.default_iterations)
            
        Returns:
            BenchmarkResult with timing data
        """
        iterations = iterations or self.default_iterations
        
        memory_before = self._get_memory_usage()
        times = self._measure_time(func, iterations)
        memory_after = self._get_memory_usage()
        
        avg, min_t, max_t, std_dev = self._calculate_stats(times)
        total_time = sum(times)
        
        return BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg,
            min_time=min_t,
            max_time=max_t,
            std_dev=std_dev,
            memory_before=memory_before,
            memory_after=memory_after,
            memory_delta=memory_after - memory_before,
        )
    
    def benchmark_import(
        self,
        module_name: str,
        iterations: Optional[int] = None,
    ) -> BenchmarkResult:
        """
        Benchmark importing a module.
        
        Args:
            module_name: Name of module to import
            iterations: Number of iterations
            
        Returns:
            BenchmarkResult with timing data
        """
        # Remove module from cache if present
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        def do_import():
            if module_name in sys.modules:
                del sys.modules[module_name]
            importlib.import_module(module_name)
        
        return self.benchmark_function(
            f"import {module_name}",
            do_import,
            iterations,
        )
    
    def benchmark_lazy_import(
        self,
        module_name: str,
        iterations: Optional[int] = None,
    ) -> BenchmarkResult:
        """
        Benchmark lazy importing a module.
        
        Args:
            module_name: Name of module to import lazily
            iterations: Number of iterations
            
        Returns:
            BenchmarkResult with timing data
        """
        import laziest_import as lz
        
        # Clear cache
        lz.clear_cache()
        
        def do_lazy_import():
            lz.clear_cache()
            mod = getattr(lz, module_name.split('.')[0])
            # Force actual import by accessing an attribute
            _ = dir(mod)
        
        return self.benchmark_function(
            f"lazy import {module_name}",
            do_lazy_import,
            iterations,
        )
    
    def compare_import_methods(
        self,
        module_name: str,
        iterations: Optional[int] = None,
    ) -> ImportComparison:
        """
        Compare regular import vs lazy import.
        
        Args:
            module_name: Name of module to compare
            iterations: Number of iterations
            
        Returns:
            ImportComparison with comparison data
        """
        regular_result = self.benchmark_import(module_name, iterations)
        lazy_result = self.benchmark_lazy_import(module_name, iterations)
        
        speedup = (
            regular_result.avg_time / lazy_result.avg_time
            if lazy_result.avg_time > 0
            else 1.0
        )
        
        return ImportComparison(
            module_name=module_name,
            regular_import_time=regular_result.avg_time,
            lazy_import_time=lazy_result.avg_time,
            speedup_factor=speedup,
            regular_memory=regular_result.memory_delta,
            lazy_memory=lazy_result.memory_delta,
        )
    
    def run_suite(
        self,
        benchmarks: List[Dict[str, Any]],
    ) -> BenchmarkReport:
        """
        Run a suite of benchmarks.
        
        Args:
            benchmarks: List of benchmark configurations
                Each dict should have 'name' and 'func' keys
                Optional: 'iterations' key
                
        Returns:
            BenchmarkReport with all results
        """
        results = []
        
        for bench in benchmarks:
            name = bench.get("name", "unnamed")
            func = bench.get("func")
            iterations = bench.get("iterations")
            
            if func is None:
                continue
            
            result = self.benchmark_function(name, func, iterations)
            results.append(result)
        
        # Generate comparison and recommendations
        comparison = {}
        recommendations = []
        
        if len(results) >= 2:
            # Compare first two results
            r1, r2 = results[0], results[1]
            if r2.avg_time > 0:
                speedup = r1.avg_time / r2.avg_time
                comparison[f"{r1.name} vs {r2.name}"] = speedup
                
                if speedup < 0.9:
                    recommendations.append(
                        f"{r2.name} is {1/speedup:.2f}x faster than {r1.name}"
                    )
        
        # Check for slow benchmarks
        for r in results:
            if r.avg_time > 1.0:
                recommendations.append(
                    f"'{r.name}' is slow ({r.avg_time:.3f}s avg), consider optimization"
                )
        
        return BenchmarkReport(
            results=results,
            comparison=comparison,
            recommendations=recommendations,
        )


def benchmark(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    iterations: int = 10,
    warmup: int = 3,
) -> BenchmarkResult:
    """
    Benchmark a function.
    
    Args:
        func: Function to benchmark (if None, returns a decorator)
        name: Name for the benchmark (default: function name)
        iterations: Number of benchmark iterations
        warmup: Number of warmup iterations
        
    Returns:
        BenchmarkResult with timing data
        
    Example:
        >>> import laziest_import as lz
        >>> 
        >>> # Direct call
        >>> result = lz.benchmark(lambda: sum(range(1000)), name="sum_test")
        >>> print(result.avg_time)
        >>> 
        >>> # As decorator
        >>> @lz.benchmark(iterations=20)
        ... def my_function():
        ...     return sum(range(1000))
    """
    runner = BenchmarkRunner(
        warmup_iterations=warmup,
        default_iterations=iterations,
    )
    
    if func is None:
        # Return a decorator
        def decorator(f: Callable) -> BenchmarkResult:
            bench_name = name or f.__name__
            return runner.benchmark_function(bench_name, f, iterations)
        return decorator
    
    # Direct call
    bench_name = name or getattr(func, "__name__", "unnamed")
    return runner.benchmark_function(bench_name, func, iterations)


def benchmark_imports(
    modules: List[str],
    iterations: int = 5,
    compare_lazy: bool = True,
) -> BenchmarkReport:
    """
    Benchmark importing multiple modules.
    
    Args:
        modules: List of module names to benchmark
        iterations: Number of iterations per module
        compare_lazy: Also benchmark lazy import for comparison
        
    Returns:
        BenchmarkReport with all results
        
    Example:
        >>> import laziest_import as lz
        >>> report = lz.benchmark_imports(['numpy', 'pandas', 'matplotlib'])
        >>> print(report.to_dict())
    """
    runner = BenchmarkRunner(default_iterations=iterations)
    results = []
    comparisons = []
    
    for module_name in modules:
        # Regular import benchmark
        regular = runner.benchmark_import(module_name, iterations)
        results.append(regular)
        
        if compare_lazy:
            lazy = runner.benchmark_lazy_import(module_name, iterations)
            results.append(lazy)
            
            comparison = runner.compare_import_methods(module_name, iterations)
            comparisons.append(comparison)
    
    # Generate recommendations
    recommendations = []
    
    for comp in comparisons:
        if comp.speedup_factor > 1.5:
            recommendations.append(
                f"Lazy import for '{comp.module_name}' is {comp.speedup_factor:.1f}x faster"
            )
    
    return BenchmarkReport(
        results=results,
        comparison={
            c.module_name: c.speedup_factor
            for c in comparisons
        },
        recommendations=recommendations,
    )


def print_benchmark_report(report: BenchmarkReport) -> None:
    """
    Print a formatted benchmark report.
    
    Args:
        report: BenchmarkReport to print
    """
    print("\n" + "=" * 60)
    print("             Benchmark Report")
    print("=" * 60)
    
    if report.results:
        print(f"\n{'Name':<30} {'Avg (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12}")
        print("-" * 66)
        
        for r in report.results:
            avg_ms = r.avg_time * 1000
            min_ms = r.min_time * 1000
            max_ms = r.max_time * 1000
            print(f"{r.name:<30} {avg_ms:<12.4f} {min_ms:<12.4f} {max_ms:<12.4f}")
    
    if report.comparison:
        print(f"\n{'Comparison':<40} {'Speedup':<10}")
        print("-" * 50)
        for name, speedup in report.comparison.items():
            print(f"{name:<40} {speedup:<10.2f}x")
    
    if report.recommendations:
        print("\nRecommendations:")
        for rec in report.recommendations:
            print(f"  - {rec}")
    
    print("\n" + "=" * 60)
