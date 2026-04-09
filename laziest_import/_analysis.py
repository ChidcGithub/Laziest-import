"""
Dependency analysis and profiling tools for laziest-import.

Features:
- Pre-analysis: Scan code files to predict imports
- Profiler: Record module load times and memory usage
- Conflict visualization: Show symbol conflicts
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
import ast
import sys
import os
import time
import logging
import threading
import traceback
import json
from dataclasses import dataclass, field
from collections import defaultdict

from ._config import (
    _DEBUG_MODE,
    _ALIAS_MAP,
    _SYMBOL_CACHE,
    _IMPORT_STATS,
    _CACHE_STATS,
    _SYMBOL_PREFERENCES,
    _TRACKED_PACKAGES,
)
from ._alias import _build_known_modules_cache


# ============== Pre-Analysis ==============

@dataclass
class PreAnalysisResult:
    """Result of pre-analysis scan."""
    file_path: str
    predicted_imports: Set[str]
    used_symbols: Set[str]
    confidence: Dict[str, float]  # module -> confidence score


class DependencyPreAnalyzer:
    """
    Scan code files to predict required imports.
    
    Usage:
        analyzer = DependencyPreAnalyzer()
        result = analyzer.analyze_file('my_script.py')
        print(result.predicted_imports)  # {'numpy', 'pandas', ...}
    """
    
    def __init__(self):
        self._known_modules: Optional[Set[str]] = None
        self._alias_to_module: Dict[str, str] = {}
        self._module_aliases: Dict[str, Set[str]] = defaultdict(set)
        self._build_reverse_aliases()
    
    def _build_reverse_aliases(self) -> None:
        """Build reverse alias mapping."""
        for alias, module in _ALIAS_MAP.items():
            self._alias_to_module[alias] = module
            self._module_aliases[module].add(alias)
    
    def _get_known_modules(self) -> Set[str]:
        """Get or build known modules cache."""
        if self._known_modules is None:
            self._known_modules = _build_known_modules_cache()
        return self._known_modules
    
    def analyze_file(self, file_path: str) -> PreAnalysisResult:
        """
        Analyze a Python file to predict imports.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            PreAnalysisResult with predicted imports
        """
        path = Path(file_path)
        if not path.exists():
            return PreAnalysisResult(file_path, set(), set(), {})
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
        except (OSError, UnicodeDecodeError):
            return PreAnalysisResult(file_path, set(), set(), {})
        
        return self.analyze_source(source, file_path)
    
    def analyze_source(self, source: str, file_path: str = "<string>") -> PreAnalysisResult:
        """
        Analyze source code to predict imports.
        
        Args:
            source: Python source code
            file_path: Optional file path for reference
            
        Returns:
            PreAnalysisResult with predicted imports
        """
        predicted: Set[str] = set()
        used_symbols: Set[str] = set()
        confidence: Dict[str, float] = {}
        
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return PreAnalysisResult(file_path, predicted, used_symbols, confidence)
        
        # Collect all names used in the code
        visitor = _NameVisitor()
        visitor.visit(tree)
        
        known_modules = self._get_known_modules()
        
        # Analyze each name
        for name in visitor.names:
            used_symbols.add(name)
            
            # Check if it's a known alias
            if name in self._alias_to_module:
                module = self._alias_to_module[name]
                predicted.add(module)
                confidence[module] = confidence.get(module, 0.0) + 1.0
            # Check if it's a module name
            elif name in known_modules:
                predicted.add(name)
                confidence[name] = confidence.get(name, 0.0) + 0.8
            # Check symbol cache
            elif name in _SYMBOL_CACHE:
                for loc in _SYMBOL_CACHE[name][:3]:
                    module = loc[0].split('.')[0]
                    predicted.add(module)
                    confidence[module] = confidence.get(module, 0.0) + 0.5
        
        # Analyze attribute access patterns like "np.array"
        for obj, attr in visitor.attribute_accesses:
            if obj in self._alias_to_module:
                module = self._alias_to_module[obj]
                predicted.add(module)
                confidence[module] = confidence.get(module, 0.0) + 1.0
        
        # Analyze from imports
        for module in visitor.imported_modules:
            predicted.add(module)
            confidence[module] = 1.0
        
        # Normalize confidence scores
        max_conf = max(confidence.values()) if confidence else 1.0
        for module in confidence:
            confidence[module] = min(1.0, confidence[module] / max_conf)
        
        return PreAnalysisResult(file_path, predicted, used_symbols, confidence)
    
    def analyze_directory(
        self, 
        dir_path: str,
        recursive: bool = True,
        exclude: Optional[Set[str]] = None
    ) -> List[PreAnalysisResult]:
        """
        Analyze all Python files in a directory.
        
        Args:
            dir_path: Directory path
            recursive: Include subdirectories
            exclude: Set of directory/file names to exclude
            
        Returns:
            List of PreAnalysisResult for each file
        """
        exclude = exclude or {'__pycache__', '.git', '.venv', 'venv', 'node_modules'}
        results = []
        
        path = Path(dir_path)
        if not path.exists():
            return results
        
        pattern = '**/*.py' if recursive else '*.py'
        
        for py_file in path.glob(pattern):
            # Skip excluded paths
            if any(exc in py_file.parts for exc in exclude):
                continue
            results.append(self.analyze_file(str(py_file)))
        
        return results
    
    def get_preload_order(self, results: List[PreAnalysisResult]) -> List[str]:
        """
        Get optimal preload order based on analysis results.
        
        Args:
            results: List of analysis results
            
        Returns:
            List of module names in optimal load order
        """
        # Aggregate confidence scores
        total_confidence: Dict[str, float] = defaultdict(float)
        
        for result in results:
            for module, conf in result.confidence.items():
                total_confidence[module] += conf
        
        # Sort by confidence (highest first)
        sorted_modules = sorted(
            total_confidence.items(),
            key=lambda x: (-x[1], x[0])
        )
        
        return [module for module, _ in sorted_modules]


class _NameVisitor(ast.NodeVisitor):
    """AST visitor to collect names and attribute accesses."""
    
    def __init__(self):
        self.names: Set[str] = set()
        self.attribute_accesses: Set[Tuple[str, str]] = set()
        self.imported_modules: Set[str] = set()
    
    def visit_Name(self, node: ast.Name) -> None:
        self.names.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name):
            self.attribute_accesses.add((node.value.id, node.attr))
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name
            self.names.add(name)
            self.imported_modules.add(alias.name.split('.')[0])
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imported_modules.add(node.module.split('.')[0])
        for alias in node.names:
            name = alias.asname or alias.name
            self.names.add(name)
        self.generic_visit(node)


# ============== Profiler ==============

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
                recommendations=recommendations
            )
    
    def print_report(self, top_n: int = 10) -> None:
        """Print a formatted profile report."""
        report = self.get_report(top_n)
        
        print("\n" + "=" * 60)
        print("             Import Profile Report")
        print("=" * 60)
        
        print(f"\nTotal import time: {report.total_time:.3f}s")
        print(f"Total memory delta: {report.total_memory / (1024*1024):.2f}MB")
        
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


# ============== Conflict Visualization ==============

@dataclass
class SymbolConflict:
    """Information about a symbol conflict."""
    symbol_name: str
    locations: List[Tuple[str, str]]  # (module_name, symbol_type)
    recommended: Optional[str] = None


def find_symbol_conflicts() -> Dict[str, SymbolConflict]:
    """
    Find all symbols that exist in multiple modules.
    
    Returns:
        Dictionary mapping symbol name to conflict info
    """
    conflicts: Dict[str, SymbolConflict] = {}
    
    for symbol_name, locations in _SYMBOL_CACHE.items():
        if len(locations) > 1:
            # Get unique modules
            modules = {}
            for loc in locations:
                module_name = loc[0]
                symbol_type = loc[1]
                if module_name not in modules:
                    modules[module_name] = symbol_type
            
            if len(modules) > 1:
                # Find recommended module from preferences
                recommended = _SYMBOL_PREFERENCES.get(symbol_name)
                
                conflicts[symbol_name] = SymbolConflict(
                    symbol_name=symbol_name,
                    locations=[(m, t) for m, t in modules.items()],
                    recommended=recommended
                )
    
    return conflicts


def show_conflicts(
    symbol_filter: Optional[str] = None,
    max_results: int = 20
) -> None:
    """
    Display symbol conflicts in a formatted table.
    
    Args:
        symbol_filter: Optional filter string to narrow results
        max_results: Maximum number of conflicts to show
    """
    conflicts = find_symbol_conflicts()
    
    if not conflicts:
        print("No symbol conflicts found.")
        return
    
    # Filter if requested
    if symbol_filter:
        conflicts = {
            k: v for k, v in conflicts.items()
            if symbol_filter.lower() in k.lower()
        }
    
    if not conflicts:
        print(f"No conflicts matching '{symbol_filter}' found.")
        return
    
    # Sort by number of locations (most conflicts first)
    sorted_conflicts = sorted(
        conflicts.items(),
        key=lambda x: -len(x[1].locations)
    )[:max_results]
    
    print("\n" + "=" * 70)
    print("                    Symbol Conflicts")
    print("=" * 70)
    
    for symbol, conflict in sorted_conflicts:
        print(f"\n  {symbol}:")
        for module, sym_type in conflict.locations:
            pref_marker = " *" if module == conflict.recommended else ""
            print(f"    - {module} [{sym_type}]{pref_marker}")
        
        if conflict.recommended:
            print(f"    (preferred: {conflict.recommended})")
    
    print(f"\n  Showing {len(sorted_conflicts)} of {len(conflicts)} conflicts")
    print("=" * 70)


def get_conflicts_summary() -> Dict[str, Any]:
    """
    Get a summary of all symbol conflicts.
    
    Returns:
        Summary dictionary
    """
    conflicts = find_symbol_conflicts()
    
    # Count by module
    module_counts: Dict[str, int] = defaultdict(int)
    for conflict in conflicts.values():
        for module, _ in conflict.locations:
            module_counts[module] += 1
    
    return {
        "total_conflicts": len(conflicts),
        "modules_with_conflicts": dict(sorted(
            module_counts.items(),
            key=lambda x: -x[1]
        )[:10]),
        "top_conflicts": [
            {
                "symbol": symbol,
                "modules": [m for m, _ in conflict.locations]
            }
            for symbol, conflict in sorted(
                conflicts.items(),
                key=lambda x: -len(x[1].locations)
            )[:10]
        ]
    }


# ============== Environment Detection ==============

@dataclass
class EnvironmentInfo:
    """Information about the current Python environment."""
    python_version: str
    executable: str
    virtual_env: Optional[str]
    venv_type: Optional[str]  # 'venv', 'conda', 'virtualenv', None
    site_packages: List[str]
    installed_packages: Dict[str, str]  # package -> version


def detect_environment() -> EnvironmentInfo:
    """
    Detect the current Python environment.
    
    Returns:
        EnvironmentInfo with environment details
    """
    # Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Executable
    executable = sys.executable
    
    # Detect virtual environment
    virtual_env = None
    venv_type = None
    
    # Check for venv/virtualenv
    if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
        virtual_env = sys.prefix
        # Check if it's conda
        if 'conda' in sys.prefix.lower() or 'anaconda' in sys.prefix.lower():
            venv_type = 'conda'
        elif 'VIRTUAL_ENV' in os.environ:
            venv_type = 'virtualenv' if 'virtualenv' in os.environ.get('VIRTUAL_ENV', '') else 'venv'
        else:
            venv_type = 'venv'
    
    # Check for conda
    if venv_type is None and 'CONDA_PREFIX' in os.environ:
        virtual_env = os.environ['CONDA_PREFIX']
        venv_type = 'conda'
    
    # Get site-packages
    site_packages = []
    for path in sys.path:
        if 'site-packages' in path and os.path.exists(path):
            site_packages.append(path)
    
    # Get installed packages
    installed_packages = {}
    try:
        from importlib.metadata import distributions
        for dist in distributions():
            name = dist.metadata.get('Name', '')
            version = dist.metadata.get('Version', '')
            if name:
                installed_packages[name.lower()] = version
    except Exception:
        pass
    
    return EnvironmentInfo(
        python_version=python_version,
        executable=executable,
        virtual_env=virtual_env,
        venv_type=venv_type,
        site_packages=site_packages,
        installed_packages=installed_packages
    )


def show_environment() -> None:
    """Display environment information."""
    env = detect_environment()
    
    print("\n" + "=" * 60)
    print("              Environment Information")
    print("=" * 60)
    
    print(f"\nPython: {env.python_version}")
    print(f"Executable: {env.executable}")
    
    if env.virtual_env:
        print(f"Virtual Environment: {env.virtual_env}")
        print(f"Environment Type: {env.venv_type}")
    else:
        print("Virtual Environment: None (system Python)")
    
    if env.site_packages:
        print(f"\nSite Packages ({len(env.site_packages)}):")
        for sp in env.site_packages[:5]:
            print(f"  - {sp}")
        if len(env.site_packages) > 5:
            print(f"  ... and {len(env.site_packages) - 5} more")
    
    print(f"\nInstalled Packages: {len(env.installed_packages)}")
    print("=" * 60)


# ============== Persistence ==============

_PREFERENCES_FILE = Path.home() / ".laziest_import" / "preferences.json"


def _ensure_preferences_dir() -> None:
    """Ensure preferences directory exists."""
    _PREFERENCES_FILE.parent.mkdir(parents=True, exist_ok=True)


def save_preferences() -> bool:
    """
    Save current symbol preferences to file.
    
    Returns:
        True if saved successfully
    """
    try:
        _ensure_preferences_dir()
        
        data = {
            "symbol_preferences": dict(_SYMBOL_PREFERENCES),
            "timestamp": time.time(),
            "version": "1.0"
        }
        
        with open(_PREFERENCES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        if _DEBUG_MODE:
            logging.info(f"[laziest-import] Saved preferences to {_PREFERENCES_FILE}")
        
        return True
    except Exception as e:
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Failed to save preferences: {e}")
        return False


def load_preferences() -> Dict[str, str]:
    """
    Load symbol preferences from file.
    
    Returns:
        Dictionary of symbol -> module preferences
    """
    try:
        if not _PREFERENCES_FILE.exists():
            return {}
        
        with open(_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get("symbol_preferences", {})
    except Exception as e:
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Failed to load preferences: {e}")
        return {}


def apply_preferences() -> None:
    """Apply loaded preferences to current session."""
    prefs = load_preferences()
    for symbol, module in prefs.items():
        _SYMBOL_PREFERENCES[symbol] = module


def clear_preferences() -> bool:
    """Clear saved preferences."""
    try:
        if _PREFERENCES_FILE.exists():
            _PREFERENCES_FILE.unlink()
        return True
    except Exception:
        return False


def get_preferences_path() -> Path:
    """Get the path to the preferences file."""
    return _PREFERENCES_FILE