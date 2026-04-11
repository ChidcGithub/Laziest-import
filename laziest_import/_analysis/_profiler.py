"""Import profiling module for performance analysis."""

from typing import Dict, List, Optional, Any
import time
import threading
from dataclasses import dataclass, field


@dataclass
class ModuleProfile:
    """Profile data for a single module."""
    module_name: str
    load_time: float = 0.0
    memory_before: int = 0
    memory_after: int = 0
    memory_delta: int = 0
    access_count: int = 0
    first_access: Optional[float] = None
    last_access: Optional[float] = None


@dataclass
class ProfileReport:
    """Complete profile report."""
    total_time: float = 0.0
    total_memory: int = 0
    modules: Dict[str, ModuleProfile] = field(default_factory=dict)
    heavy_modules: List[str] = field(default_factory=list)
    slow_modules: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    tracemalloc_enabled: bool = False  # Whether memory tracking was active


class ImportProfiler:
    """
    Profile module imports to identify performance bottlenecks.
    
    Usage:
        profiler = ImportProfiler()
        profiler.start()
        # ... your imports ...
        profiler.stop()
        report = profiler.get_report()
    """
    
    _instance: Optional["ImportProfiler"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "ImportProfiler":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._profiles: Dict[str, ModuleProfile] = {}
        self._start_time: Optional[float] = None
        self._active = False
        self._lock = threading.Lock()
        self._initialized = True
    
    def start(self) -> None:
        """Start profiling."""
        with self._lock:
            self._active = True
            self._start_time = time.perf_counter()
            self._profiles.clear()
    
    def stop(self) -> None:
        """Stop profiling."""
        with self._lock:
            self._active = False
    
    def is_active(self) -> bool:
        """Check if profiling is active."""
        return self._active
    
    def record_load(
        self,
        module_name: str,
        load_time: float,
        memory_delta: int = 0
    ) -> None:
        """Record a module load event."""
        if not self._active:
            return
        
        with self._lock:
            now = time.time()
            
            if module_name not in self._profiles:
                self._profiles[module_name] = ModuleProfile(
                    module_name=module_name,
                    load_time=load_time,
                    memory_delta=memory_delta,
                    access_count=1,
                    first_access=now,
                    last_access=now
                )
            else:
                profile = self._profiles[module_name]
                profile.load_time += load_time
                profile.memory_delta += memory_delta
                profile.access_count += 1
                profile.last_access = now
    
    def get_report(self, top_n: int = 10) -> ProfileReport:
        """
        Generate a profile report.
        
        Args:
            top_n: Number of top modules to include
            
        Returns:
            ProfileReport with analysis
        """
        with self._lock:
            total_time = sum(p.load_time for p in self._profiles.values())
            total_memory = sum(p.memory_delta for p in self._profiles.values())
            
            # Find heavy modules (by memory)
            sorted_by_memory = sorted(
                self._profiles.items(),
                key=lambda x: -x[1].memory_delta
            )
            heavy_modules = [m for m, _ in sorted_by_memory[:top_n]]
            
            # Find slow modules (by time)
            sorted_by_time = sorted(
                self._profiles.items(),
                key=lambda x: -x[1].load_time
            )
            slow_modules = [m for m, _ in sorted_by_time[:top_n]]
            
            # Generate recommendations
            recommendations = []
            
            # Check if tracemalloc is running
            try:
                import tracemalloc
                tracemalloc_running = tracemalloc.is_tracing()
            except Exception:
                tracemalloc_running = False
            
            if not tracemalloc_running:
                recommendations.append(
                    "Memory tracking is disabled. Start tracemalloc before imports "
                    "to measure memory usage: 'import tracemalloc; tracemalloc.start()'"
                )
            
            for module, profile in sorted_by_time[:3]:
                if profile.load_time > 1.0:
                    recommendations.append(
                        f"Consider lazy-loading '{module}' (takes {profile.load_time:.2f}s)"
                    )
            for module, profile in sorted_by_memory[:3]:
                if profile.memory_delta > 10 * 1024 * 1024:  # > 10MB
                    mb = profile.memory_delta / (1024 * 1024)
                    recommendations.append(
                        f"'{module}' uses {mb:.1f}MB - consider alternatives or lazy loading"
                    )
            
            return ProfileReport(
                total_time=total_time,
                total_memory=total_memory,
                modules=dict(self._profiles),
                heavy_modules=heavy_modules,
                slow_modules=slow_modules,
                recommendations=recommendations,
                tracemalloc_enabled=tracemalloc_running,
            )
    
    def print_report(self, top_n: int = 10) -> None:
        """Print a formatted profile report."""
        report = self.get_report(top_n)
        
        print("\n" + "=" * 60)
        print("             Import Profile Report")
        print("=" * 60)
        
        print(f"\nTotal import time: {report.total_time:.3f}s")
        
        # Check if tracemalloc is running to explain memory stats
        try:
            import tracemalloc
            tracemalloc_running = tracemalloc.is_tracing()
        except Exception:
            tracemalloc_running = False
        
        if tracemalloc_running:
            print(f"Total memory delta: {report.total_memory / (1024*1024):.2f}MB")
        else:
            print(f"Total memory delta: {report.total_memory / (1024*1024):.2f}MB (tracemalloc not enabled)")
            if report.total_memory == 0:
                print("  Note: Memory tracking requires tracemalloc.")
                print("  To enable: import tracemalloc; tracemalloc.start()")
                print("  Or start profiling before any imports for automatic tracking.")
        
        if report.slow_modules:
            print(f"\nTop {len(report.slow_modules)} slowest modules:")
            for i, mod in enumerate(report.slow_modules, 1):
                p = report.modules[mod]
                print(f"  {i}. {mod}: {p.load_time:.3f}s ({p.access_count} accesses)")
        
        if report.heavy_modules:
            print(f"\nTop {len(report.heavy_modules)} heaviest modules (memory):")
            for i, mod in enumerate(report.heavy_modules, 1):
                p = report.modules[mod]
                mb = p.memory_delta / (1024 * 1024)
                print(f"  {i}. {mod}: {mb:.2f}MB")
        
        if report.recommendations:
            print("\nRecommendations:")
            for rec in report.recommendations:
                print(f"  - {rec}")
        
        print("\n" + "=" * 60)


# Global profiler instance
_profiler = ImportProfiler()


def start_profiling() -> None:
    """Start import profiling."""
    _profiler.start()


def stop_profiling() -> None:
    """Stop import profiling."""
    _profiler.stop()


def get_profile_report(top_n: int = 10) -> ProfileReport:
    """Get profile report."""
    return _profiler.get_report(top_n)


def print_profile_report(top_n: int = 10) -> None:
    """Print profile report."""
    _profiler.print_report(top_n)