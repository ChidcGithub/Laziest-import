"""
laziest-import: Automatic Lazy Import Library

Usage:
    from laziest_import import *
    
    # Use common libraries directly without explicit import statements
    arr = np.array([1, 2, 3])
    df = pd.DataFrame({'a': [1, 2]})
    
    # Auto-search for unregistered modules
    # e.g., use flask directly even if not pre-registered
    app = flask.Flask(__name__)
    
Or:
    import laziest_import as lz
    arr = lz.np.array([1, 2, 3])

Configuration:
    # Custom aliases can be defined in:
    # 1. ~/.laziest_import/aliases.json (user global)
    # 2. ./.laziest_import.json (project level)
    
    # Example config file:
    # {"mylib": "my_awesome_library", "api": "my_api_client"}
"""

from typing import Dict, List, Optional, Set, Any, Tuple, Callable, Union
import sys as _sys_module
import importlib as _importlib_module
import importlib.util as _importlib_util
import importlib.machinery as _importlib_machinery
import pkgutil as _pkgutil_module
import warnings as _warnings_module
import json as _json_module
import hashlib as _hashlib_module
import atexit as _atexit_module
import traceback as _traceback_module
import time as _time_module
import logging as _logging_module
import asyncio as _asyncio_module
import threading as _threading_module
from pathlib import Path as _Path_class
from types import ModuleType as _ModuleType
from dataclasses import dataclass as _dataclass, field as _field, asdict as _asdict

__version__ = "0.0.2.3"

# ============== Initialization State Protection ==============
# These flags prevent recursive calls during module initialization
_INITIALIZING: bool = False
_INITIALIZED: bool = False
_INIT_LOCK: Optional["threading.RLock"] = None  # Will be set lazily
_INIT_LOCK_CREATION_LOCK: "threading.Lock" = _threading_module.Lock()  # Protects _INIT_LOCK creation

def _get_init_lock() -> "threading.RLock":
    """Get or create the initialization lock (lazy initialization, thread-safe)."""
    global _INIT_LOCK
    if _INIT_LOCK is None:
        with _INIT_LOCK_CREATION_LOCK:
            # Double-check after acquiring lock
            if _INIT_LOCK is None:
                _INIT_LOCK = _threading_module.RLock()
    return _INIT_LOCK

# Auto-search feature enabled flag
_AUTO_SEARCH_ENABLED: bool = True

# Known modules cache (avoids repeated searches)
_KNOWN_MODULES_CACHE: Optional[Set[str]] = None
_KNOWN_MODULES_CACHE_TIME: float = 0.0  # Timestamp when cache was built
_KNOWN_MODULES_CACHE_TTL: float = 300.0  # Cache TTL in seconds (5 minutes)

# Class name to module mapping cache (e.g., "DataFrame" -> "pandas")
_CLASS_TO_MODULE_CACHE: Dict[str, str] = {}

# Module alias mapping: alias -> actual module name
_ALIAS_MAP: Dict[str, str] = {}

# LazyModule proxy cache
_LAZY_MODULES: Dict[str, "LazyModule"] = {}

# Thread-local storage for recursion protection during import
_IMPORT_CONTEXT = _threading_module.local()

def _get_importing_modules() -> Set[str]:
    """Get the set of modules currently being imported (thread-local)."""
    if not hasattr(_IMPORT_CONTEXT, 'importing'):
        _IMPORT_CONTEXT.importing = set()
    return _IMPORT_CONTEXT.importing

# ============== New Features ==============

# Debug mode flag
_DEBUG_MODE: bool = False

# File cache enabled flag
_FILE_CACHE_ENABLED: bool = True

# Import statistics
@_dataclass
class ImportStats:
    """Import statistics record"""
    total_imports: int = 0
    total_time: float = 0.0
    module_times: Dict[str, float] = _field(default_factory=dict)
    module_access_counts: Dict[str, int] = _field(default_factory=dict)

_IMPORT_STATS: ImportStats = ImportStats()

# Import hooks/callbacks
_PRE_IMPORT_HOOKS: List[Callable[[str], None]] = []
_POST_IMPORT_HOOKS: List[Callable[[str, Any], None]] = []

# Import retry configuration
_RETRY_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "max_retries": 3,
    "retry_delay": 0.5,
    "retry_modules": set(),  # Empty set means retry all
}

# Auto-install configuration
_AUTO_INSTALL_CONFIG: Dict[str, Any] = {
    "enabled": False,  # Auto-install disabled by default (safety)
    "interactive": True,  # Ask user for confirmation before installing
    "index": None,  # Custom PyPI mirror URL (None = default)
    "extra_args": [],  # Extra pip install arguments
    "prefer_uv": False,  # Prefer uv over pip if available
    "silent": False,  # Suppress pip output
}

# ============== Symbol Search System ==============

import inspect as _inspect_module
from functools import lru_cache as _lru_cache

# Symbol search configuration
_SYMBOL_SEARCH_CONFIG: Dict[str, Any] = {
    "enabled": True,  # Enable symbol search when module not found
    "interactive": True,  # Ask user for confirmation (set False for auto-register)
    "exact_params": False,  # Require exact parameter match
    "max_results": 5,  # Maximum search results to show
    "search_depth": 1,  # How deep to scan submodules (0 = top level only)
    "cache_enabled": True,  # Cache scanned symbols
    "skip_private": True,  # Skip private symbols (starting with _)
    "skip_stdlib": False,  # Skip standard library modules in search
}

# Symbol cache: name -> List of (module_name, symbol_type, signature_hint)
_SYMBOL_CACHE: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}

# Symbol index built flag
_SYMBOL_INDEX_BUILT: bool = False

# User confirmed mappings (persistent)
_CONFIRMED_MAPPINGS: Dict[str, str] = {}

# ============== Enhanced Cache System ==============

# Cache version for compatibility checking
_CACHE_VERSION: str = "0.0.2.3"

# Multi-level symbol caches
_STDLIB_SYMBOL_CACHE: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}
_THIRD_PARTY_SYMBOL_CACHE: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}
_STDLIB_CACHE_BUILT: bool = False
_THIRD_PARTY_CACHE_BUILT: bool = False

# Cache configuration
_CACHE_CONFIG: Dict[str, Any] = {
    "symbol_index_ttl": 86400,  # Symbol index TTL in seconds (24 hours)
    "stdlib_cache_ttl": 604800,  # Stdlib cache TTL (7 days - rarely changes)
    "third_party_cache_ttl": 86400,  # Third-party cache TTL (24 hours)
    "enable_compression": False,  # Enable cache compression for large files
    "max_cache_size_mb": 100,  # Maximum cache size in MB
}

# Cache statistics
_CACHE_STATS: Dict[str, Any] = {
    "symbol_hits": 0,
    "symbol_misses": 0,
    "module_hits": 0,
    "module_misses": 0,
    "last_build_time": 0.0,
    "build_count": 0,
}

# Tracked packages for incremental updates
_TRACKED_PACKAGES: Dict[str, Dict[str, Any]] = {}  # package_name -> {version, mtime, module_count}


@_dataclass
class SearchResult:
    """Search result for a symbol."""
    module_name: str
    symbol_name: str
    symbol_type: str  # 'class', 'function', 'callable'
    signature: Optional[str]
    score: float  # Match score (0-1)
    obj: Optional[Any] = None


def _get_signature_hint(obj: Any) -> Optional[str]:
    """
    Get a signature hint string for a callable object.
    
    Args:
        obj: The callable object
        
    Returns:
        Signature string like "(a, b, c=None)" or None
    """
    try:
        if callable(obj):
            sig = _inspect_module.signature(obj)
            return str(sig)
    except (ValueError, TypeError):
        pass
    return None


def _is_stdlib_module(module_name: str) -> bool:
    """
    Check if a module is part of the standard library.
    
    Args:
        module_name: Module name to check
        
    Returns:
        True if it's a stdlib module
    """
    # Python 3.10+ has stdlib_module_names
    if hasattr(_sys_module, 'stdlib_module_names'):
        return module_name.split('.')[0] in _sys_module.stdlib_module_names
    
    # Fallback list for older Python
    stdlib_prefixes = {
        'abc', 'argparse', 'array', 'ast', 'asyncio', 'atexit', 'base64',
        'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cmath', 'cmd',
        'code', 'codecs', 'collections', 'configparser', 'contextlib',
        'copy', 'csv', 'ctypes', 'dataclasses', 'datetime', 'dbm', 'decimal',
        'difflib', 'dis', 'email', 'enum', 'errno', 'fcntl', 'filecmp',
        'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools', 'gc',
        'getopt', 'getpass', 'gettext', 'glob', 'gzip', 'hashlib', 'heapq',
        'hmac', 'html', 'http', 'imaplib', 'importlib', 'inspect', 'io',
        'itertools', 'json', 'keyword', 'linecache', 'locale', 'logging',
        'lzma', 'mailbox', 'marshal', 'math', 'mimetypes', 'mmap',
        'multiprocessing', 'netrc', 'numbers', 'operator', 'optparse', 'os',
        'pathlib', 'pickle', 'platform', 'plistlib', 'poplib', 'pprint',
        'profile', 'queue', 'random', 're', 'reprlib', 'sched', 'secrets',
        'select', 'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtplib',
        'socket', 'socketserver', 'sqlite3', 'ssl', 'stat', 'statistics',
        'string', 'struct', 'subprocess', 'sys', 'sysconfig', 'tarfile',
        'tempfile', 'termios', 'textwrap', 'threading', 'time', 'timeit',
        'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'types',
        'typing', 'unicodedata', 'unittest', 'urllib', 'uuid', 'warnings',
        'wave', 'weakref', 'webbrowser', 'wsgiref', 'xml', 'xmlrpc',
        'zipfile', 'zipimport', 'zlib', 'zoneinfo',
    }
    return module_name.split('.')[0] in stdlib_prefixes


def _scan_module_symbols(
    module_name: str,
    depth: int = 1,
    _scanned: Optional[Set[str]] = None,
    _current_depth: int = 0
) -> Dict[str, List[Tuple[str, str, Optional[str]]]]:
    """
    Scan a module for exported symbols (classes, functions, callables).
    
    Args:
        module_name: Name of the module to scan
        depth: How deep to scan submodules (0 = top level only)
        _scanned: Set of already scanned modules (internal, for cycle detection)
        _current_depth: Current recursion depth (internal)
        
    Returns:
        Dictionary mapping symbol name to list of (module_name, symbol_type, signature)
    """
    # Initialize scanned set for cycle detection
    if _scanned is None:
        _scanned = set()
    
    # Protect against deep recursion and cycles
    MAX_DEPTH = 3
    if _current_depth > MAX_DEPTH:
        return {}
    
    if module_name in _scanned:
        return {}
    _scanned.add(module_name)
    
    symbols: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}
    
    if _SYMBOL_SEARCH_CONFIG["skip_stdlib"] and _is_stdlib_module(module_name):
        return symbols
    
    # Skip modules that are known to cause issues or are not useful for symbol search
    skip_modules = {
        'test', 'tests', 'testing', 'conftest', 'setup', 'examples',
        'docs', 'doc', 'scripts', 'tools', 'vendor', 'vendored',
        '__pycache__', '.git', '.hg', '.svn',
        # Skip testing/build tools that definitely have side effects
        'pytest', 'py.test', 'sphinx', 'mkdocs',
        # Skip ourselves to prevent recursion
        'laziest_import', 'laziest-import',
    }
    if any(skip in module_name.lower() for skip in skip_modules):
        return symbols
    
    # Skip internal/deprecated modules (e.g., numpy.core, numpy.linalg.linalg)
    internal_patterns = ['._', '.core.', '.linalg.linalg', '.internal.']
    if any(pattern in module_name for pattern in internal_patterns):
        return symbols
    
    # Skip __main__ modules
    if module_name.endswith('__main__'):
        return symbols
    
    # Suppress deprecation warnings during scanning
    with _warnings_module.catch_warnings():
        _warnings_module.simplefilter("ignore", DeprecationWarning)
        _warnings_module.simplefilter("ignore", FutureWarning)
        
        try:
            module = _importlib_module.import_module(module_name)
        except (ImportError, ModuleNotFoundError, SyntaxError, AttributeError, 
                TypeError, ValueError, OSError, RecursionError, SystemExit):
            return symbols
        
        skip_private = _SYMBOL_SEARCH_CONFIG["skip_private"]
        
        # Get module's __all__ if available, otherwise use dir()
        try:
            public_names = getattr(module, '__all__', None)
            if public_names is None:
                public_names = [name for name in dir(module) if not name.startswith('_')]
            else:
                # Filter out non-strings from __all__
                public_names = [n for n in public_names if isinstance(n, str)]
        except Exception:
            public_names = []
        
        # Limit the number of symbols to scan per module
        MAX_SYMBOLS_PER_MODULE = 100
        if len(public_names) > MAX_SYMBOLS_PER_MODULE:
            public_names = public_names[:MAX_SYMBOLS_PER_MODULE]
        
        for name in public_names:
            if skip_private and name.startswith('_'):
                continue
            
            try:
                obj = getattr(module, name)
            except (AttributeError, ImportError, TypeError, RecursionError):
                continue
            
            symbol_type = None
            signature = None
            
            try:
                if _inspect_module.isclass(obj):
                    symbol_type = 'class'
                    # Get __init__ signature for classes
                    try:
                        init = getattr(obj, '__init__', None)
                        if init and callable(init):
                            signature = _get_signature_hint(init)
                    except Exception:
                        pass
                elif _inspect_module.isfunction(obj):
                    symbol_type = 'function'
                    signature = _get_signature_hint(obj)
                elif callable(obj):
                    symbol_type = 'callable'
                    signature = _get_signature_hint(obj)
            except Exception:
                continue

            if symbol_type:
                if name not in symbols:
                    symbols[name] = []
                symbols[name].append((module_name, symbol_type, signature))
    
    # Scan submodules if depth > 0
    if depth > 0 and hasattr(module, '__path__'):
        try:
            submodule_count = 0
            MAX_SUBMODULES = 20  # Limit number of submodules to scan
            for finder, submod_name, ispkg in _pkgutil_module.iter_modules(module.__path__):
                if submodule_count >= MAX_SUBMODULES:
                    break
                full_submod_name = f"{module_name}.{submod_name}"
                try:
                    submod_symbols = _scan_module_symbols(
                        full_submod_name, depth - 1, _scanned, _current_depth + 1
                    )
                    for sym_name, locations in submod_symbols.items():
                        if sym_name not in symbols:
                            symbols[sym_name] = []
                        symbols[sym_name].extend(locations)
                    submodule_count += 1
                except Exception:
                    continue
        except Exception:
            pass
    
    return symbols


def _build_symbol_index(force: bool = False, max_modules: int = 100, timeout: float = 30.0) -> None:
    """
    Build the symbol index by scanning installed packages.
    
    Uses multi-level caching:
    - Level 1: stdlib symbols (long-lived cache)
    - Level 2: third-party symbols (configurable TTL)
    - Level 3: in-memory hot cache
    
    Args:
        force: Force rebuild even if already built
        max_modules: Maximum number of modules to scan (to prevent timeout)
        timeout: Maximum time in seconds for the entire scan (default: 30s)
    """
    global _SYMBOL_INDEX_BUILT, _SYMBOL_CACHE, _STDLIB_SYMBOL_CACHE, _THIRD_PARTY_SYMBOL_CACHE
    global _STDLIB_CACHE_BUILT, _THIRD_PARTY_CACHE_BUILT, _CACHE_STATS, _TRACKED_PACKAGES
    
    # Don't build during initialization to prevent recursion
    if not _INITIALIZED:
        return
    
    if _SYMBOL_INDEX_BUILT and not force:
        return
    
    if not _SYMBOL_SEARCH_CONFIG["cache_enabled"]:
        return
    
    # Record start time for stats
    start_time = _time_module.perf_counter()
    
    # Try to load from persistent cache first
    if not force:
        # Load tracked packages for incremental updates
        _TRACKED_PACKAGES = _load_tracked_packages()
        
        # Try to load stdlib cache
        stdlib_cache = _load_symbol_index("stdlib")
        if stdlib_cache:
            _STDLIB_SYMBOL_CACHE = {
                k: [tuple(loc) for loc in v] 
                for k, v in stdlib_cache.symbols.items()
            }
            _STDLIB_CACHE_BUILT = True
            if _DEBUG_MODE:
                _logging_module.info(
                    f"[laziest-import] Loaded stdlib symbol index: "
                    f"{len(_STDLIB_SYMBOL_CACHE)} symbols"
                )
        
        # Try to load third-party cache
        third_party_cache = _load_symbol_index("third_party")
        if third_party_cache:
            _THIRD_PARTY_SYMBOL_CACHE = {
                k: [tuple(loc) for loc in v] 
                for k, v in third_party_cache.symbols.items()
            }
            _THIRD_PARTY_CACHE_BUILT = True
            if _DEBUG_MODE:
                _logging_module.info(
                    f"[laziest-import] Loaded third-party symbol index: "
                    f"{len(_THIRD_PARTY_SYMBOL_CACHE)} symbols"
                )
        
        # Merge caches
        if _STDLIB_CACHE_BUILT or _THIRD_PARTY_CACHE_BUILT:
            _SYMBOL_CACHE.clear()
            _SYMBOL_CACHE.update(_STDLIB_SYMBOL_CACHE)
            _SYMBOL_CACHE.update(_THIRD_PARTY_SYMBOL_CACHE)
            _SYMBOL_INDEX_BUILT = True
            
            # Update stats
            _CACHE_STATS["symbol_hits"] += 1
            elapsed = _time_module.perf_counter() - start_time
            _CACHE_STATS["last_build_time"] = elapsed
            
            if _DEBUG_MODE:
                _logging_module.info(
                    f"[laziest-import] Symbol index loaded from cache: "
                    f"{len(_SYMBOL_CACHE)} symbols in {elapsed:.3f}s"
                )
            return
    
    _CACHE_STATS["symbol_misses"] += 1
    
    # Need to rebuild - clear caches
    _SYMBOL_CACHE.clear()
    _STDLIB_SYMBOL_CACHE.clear()
    _THIRD_PARTY_SYMBOL_CACHE.clear()
    depth = _SYMBOL_SEARCH_CONFIG["search_depth"]
    
    # Scan all known modules
    known_modules = _build_known_modules_cache()
    
    if _DEBUG_MODE:
        _logging_module.info(f"[laziest-import] Building symbol index for {len(known_modules)} modules...")
    
    # Prioritize commonly used packages
    priority_packages = {
        'pandas', 'numpy', 'matplotlib', 'seaborn', 'scipy', 'sklearn',
        'torch', 'tensorflow', 'keras', 'xgboost', 'lightgbm',
        'requests', 'flask', 'django', 'fastapi',
        'PIL', 'cv2', 'plotly', 'bokeh',
        'json', 'os', 'sys', 're', 'datetime', 'collections', 'itertools',
        'pathlib', 'typing', 'functools', 'contextlib', 'dataclasses',
    }
    
    # Sort modules: priority packages first, then alphabetically
    sorted_modules = sorted(
        known_modules,
        key=lambda m: (0 if m.split('.')[0] in priority_packages else 1, m)
    )
    
    scanned_stdlib = 0
    scanned_third_party = 0
    timed_out = False
    
    for module_name in sorted_modules:
        # Check timeout
        if _time_module.perf_counter() - start_time > timeout:
            timed_out = True
            if _DEBUG_MODE:
                _logging_module.info(f"[laziest-import] Symbol index build timed out after {timeout}s")
            break
        
        if scanned_stdlib + scanned_third_party >= max_modules:
            break
            
        # Skip internal/test modules
        if any(x in module_name.lower() for x in ['test', 'tests', '_test', '__pycache__', 'conftest', 'setup']):
            continue
        
        try:
            symbols = _scan_module_symbols(module_name, depth)
            
            # Determine if stdlib or third-party
            is_stdlib = _is_stdlib_module(module_name)
            target_cache = _STDLIB_SYMBOL_CACHE if is_stdlib else _THIRD_PARTY_SYMBOL_CACHE
            
            for sym_name, locations in symbols.items():
                if sym_name not in _SYMBOL_CACHE:
                    _SYMBOL_CACHE[sym_name] = []
                _SYMBOL_CACHE[sym_name].extend(locations)
                
                if sym_name not in target_cache:
                    target_cache[sym_name] = []
                target_cache[sym_name].extend(locations)
            
            if is_stdlib:
                scanned_stdlib += 1
            else:
                scanned_third_party += 1
                # Track third-party package for incremental updates
                top_level = module_name.split('.')[0]
                if top_level not in _TRACKED_PACKAGES:
                    _track_package(top_level)
                    
        except Exception:
            continue
    
    _SYMBOL_INDEX_BUILT = True
    _STDLIB_CACHE_BUILT = True
    _THIRD_PARTY_CACHE_BUILT = True
    
    # Save to persistent cache
    _save_symbol_index(_STDLIB_SYMBOL_CACHE, "stdlib", scanned_stdlib)
    _save_symbol_index(_THIRD_PARTY_SYMBOL_CACHE, "third_party", scanned_third_party)
    _save_tracked_packages()
    
    # Update stats
    elapsed = _time_module.perf_counter() - start_time
    _CACHE_STATS["last_build_time"] = elapsed
    _CACHE_STATS["build_count"] += 1
    
    if _DEBUG_MODE:
        timeout_msg = " (timed out)" if timed_out else ""
        _logging_module.info(
            f"[laziest-import] Symbol index built: {len(_SYMBOL_CACHE)} symbols "
            f"(stdlib: {scanned_stdlib}, third-party: {scanned_third_party}) "
            f"in {elapsed:.2f}s{timeout_msg}"
        )


def _compare_signatures(sig1: Optional[str], sig2: Optional[str]) -> float:
    """
    Compare two signature strings and return a similarity score.
    
    Args:
        sig1: First signature string
        sig2: Second signature string
        
    Returns:
        Similarity score between 0 and 1
    """
    if sig1 is None or sig2 is None:
        return 0.5  # Unknown, neutral score
    
    # Extract parameter names
    def extract_params(sig: str) -> Set[str]:
        try:
            # Remove parentheses and split by comma
            inner = sig.strip('()')
            if not inner:
                return set()
            params = set()
            for part in inner.split(','):
                part = part.strip()
                if part:
                    # Extract param name (before = or :)
                    param_name = part.split('=')[0].split(':')[0].strip()
                    if param_name and not param_name.startswith('*'):
                        params.add(param_name)
            return params
        except Exception:
            return set()
    
    params1 = extract_params(sig1)
    params2 = extract_params(sig2)
    
    if not params1 or not params2:
        return 0.5
    
    # Jaccard similarity
    intersection = len(params1 & params2)
    union = len(params1 | params2)
    
    return intersection / union if union > 0 else 0.0


def search_symbol(
    name: str,
    symbol_type: Optional[str] = None,
    signature: Optional[str] = None,
    max_results: Optional[int] = None
) -> List[SearchResult]:
    """
    Search for a symbol (class/function) by name across installed packages.
    
    Args:
        name: Symbol name to search for
        symbol_type: Filter by type ('class', 'function', 'callable'), or None for all
        signature: Expected signature for matching (optional)
        max_results: Maximum number of results (uses config if None)
        
    Returns:
        List of SearchResult objects sorted by score
        
    Example:
        >>> results = search_symbol("DataFrame")
        >>> for r in results:
        ...     print(f"{r.module_name}.{r.symbol_name} [{r.symbol_type}]")
        pandas.DataFrame [class]
        polars.DataFrame [class]
    """
    if not _SYMBOL_SEARCH_CONFIG["enabled"]:
        return []
    
    # Build index if needed
    if not _SYMBOL_INDEX_BUILT:
        _build_symbol_index()
    
    if name not in _SYMBOL_CACHE:
        # Try fuzzy match on symbol names
        name_lower = name.lower()
        matches = []
        for cached_name in _SYMBOL_CACHE.keys():
            if cached_name.lower() == name_lower:
                matches.append(cached_name)
            elif name_lower in cached_name.lower():
                matches.append(cached_name)
            elif _levenshtein_distance(name_lower, cached_name.lower()) <= 2:
                matches.append(cached_name)
        
        if not matches:
            return []
        
        # Collect results for all matches
        all_results = []
        for match_name in matches[:3]:  # Limit fuzzy matches
            all_results.extend(_search_symbol_direct(match_name, symbol_type, signature))
        
        # Deduplicate and sort
        seen = set()
        results = []
        for r in all_results:
            key = (r.module_name, r.symbol_name)
            if key not in seen:
                seen.add(key)
                results.append(r)
        
        max_res = max_results or _SYMBOL_SEARCH_CONFIG["max_results"]
        return sorted(results, key=lambda x: -x.score)[:max_res]
    
    return _search_symbol_direct(name, symbol_type, signature, max_results)


def _search_symbol_direct(
    name: str,
    symbol_type: Optional[str] = None,
    signature: Optional[str] = None,
    max_results: Optional[int] = None
) -> List[SearchResult]:
    """
    Direct search for an exact symbol name in cache.
    """
    results = []
    
    if name not in _SYMBOL_CACHE:
        return results
    
    for module_name, sym_type, cached_sig in _SYMBOL_CACHE[name]:
        # Filter by type
        if symbol_type and sym_type != symbol_type:
            continue
        
        # Calculate score
        score = 1.0
        
        # Penalize stdlib if configured
        if _SYMBOL_SEARCH_CONFIG["skip_stdlib"] and _is_stdlib_module(module_name):
            score *= 0.5
        
        # Signature matching
        if signature and cached_sig:
            sig_score = _compare_signatures(signature, cached_sig)
            if _SYMBOL_SEARCH_CONFIG["exact_params"] and sig_score < 0.9:
                continue  # Skip if exact match required
            score *= (0.5 + 0.5 * sig_score)
        
        results.append(SearchResult(
            module_name=module_name,
            symbol_name=name,
            symbol_type=sym_type,
            signature=cached_sig,
            score=score,
        ))
    
    # Sort by score
    results.sort(key=lambda x: -x.score)
    
    max_res = max_results or _SYMBOL_SEARCH_CONFIG["max_results"]
    return results[:max_res]


def _interactive_confirm(results: List[SearchResult], symbol_name: str) -> Optional[str]:
    """
    Interactively ask user to confirm which module to use.
    
    Args:
        results: List of search results
        symbol_name: The symbol name being searched
        
    Returns:
        Selected module name, or None if cancelled
    """
    if not results:
        return None
    
    if not _SYMBOL_SEARCH_CONFIG["interactive"]:
        # Auto-select best match
        return results[0].module_name
    
    # Format results for display
    print(f"\n[laziest-import] Found {len(results)} match(es) for '{symbol_name}':")
    print("-" * 60)
    
    for i, r in enumerate(results, 1):
        sig_str = f" {r.signature}" if r.signature else ""
        type_str = f"[{r.symbol_type}]"
        print(f"  {i}. {r.module_name}.{r.symbol_name} {type_str}{sig_str}")
    
    print(f"  0. Skip (do not register)")
    print("-" * 60)
    
    try:
        choice = input(f"Select [1-{len(results)}, 0 to skip] (default=1): ").strip()
        
        if not choice:
            choice = "1"
        
        if choice == "0":
            return None
        
        idx = int(choice) - 1
        if 0 <= idx < len(results):
            return results[idx].module_name
        
        print(f"Invalid choice: {choice}")
        return None
    except (ValueError, EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return None


def _handle_symbol_not_found(name: str) -> Optional[str]:
    """
    Handle a symbol not found error by searching and prompting user.
    
    This is called when a name is not found in aliases or modules.
    
    Args:
        name: The symbol name that was not found
        
    Returns:
        Module name if found and confirmed, None otherwise
    """
    # Don't do symbol search during initialization
    if not _INITIALIZED:
        return None
    
    # Check if already confirmed before
    if name in _CONFIRMED_MAPPINGS:
        return _CONFIRMED_MAPPINGS[name]
    
    # Search for the symbol
    results = search_symbol(name)
    
    if not results:
        return None
    
    # Interactive confirmation
    selected_module = _interactive_confirm(results, name)
    
    if selected_module:
        # Save the mapping
        _CONFIRMED_MAPPINGS[name] = selected_module
        
        # Register the alias
        register_alias(name, selected_module)
        
        print(f"[laziest-import] Registered alias: {name} -> {selected_module}")
        
        return selected_module
    
    return None


# ============== Symbol Search API ==============

def enable_symbol_search(
    interactive: bool = True,
    exact_params: bool = False,
    max_results: int = 5,
    search_depth: int = 1,
    skip_stdlib: bool = False
) -> None:
    """
    Enable symbol search functionality.
    
    When enabled, accessing an unknown name will search for matching
    classes/functions in installed packages.
    
    Args:
        interactive: Ask user for confirmation (False = auto-select best match)
        exact_params: Require exact parameter signature match
        max_results: Maximum number of results to show
        search_depth: How deep to scan submodules (0 = top level only)
        skip_stdlib: Skip standard library modules in search
        
    Example:
        >>> enable_symbol_search(interactive=True, max_results=3)
    """
    _SYMBOL_SEARCH_CONFIG["enabled"] = True
    _SYMBOL_SEARCH_CONFIG["interactive"] = interactive
    _SYMBOL_SEARCH_CONFIG["exact_params"] = exact_params
    _SYMBOL_SEARCH_CONFIG["max_results"] = max_results
    _SYMBOL_SEARCH_CONFIG["search_depth"] = search_depth
    _SYMBOL_SEARCH_CONFIG["skip_stdlib"] = skip_stdlib


def disable_symbol_search() -> None:
    """
    Disable symbol search functionality.
    """
    _SYMBOL_SEARCH_CONFIG["enabled"] = False


def is_symbol_search_enabled() -> bool:
    """
    Check if symbol search is enabled.
    
    Returns:
        True if symbol search is enabled
    """
    return _SYMBOL_SEARCH_CONFIG["enabled"]


def rebuild_symbol_index() -> None:
    """
    Rebuild the symbol index.
    
    Call this after installing new packages to update the symbol cache.
    Clears both memory and persistent cache, then rebuilds from scratch.
    """
    global _SYMBOL_INDEX_BUILT, _STDLIB_CACHE_BUILT, _THIRD_PARTY_CACHE_BUILT
    
    # Clear memory cache
    _SYMBOL_CACHE.clear()
    _STDLIB_SYMBOL_CACHE.clear()
    _THIRD_PARTY_SYMBOL_CACHE.clear()
    _SYMBOL_INDEX_BUILT = False
    _STDLIB_CACHE_BUILT = False
    _THIRD_PARTY_CACHE_BUILT = False
    
    # Clear persistent cache
    for cache_type in ["stdlib", "third_party", "all"]:
        cache_path = _get_symbol_index_path(cache_type)
        if cache_path.exists():
            cache_path.unlink()
    
    # Rebuild
    _build_symbol_index(force=True)


def get_symbol_search_config() -> Dict[str, Any]:
    """
    Get current symbol search configuration.
    
    Returns:
        Dictionary of configuration options
    """
    return dict(_SYMBOL_SEARCH_CONFIG)


def get_symbol_cache_info() -> Dict[str, Any]:
    """
    Get information about the symbol cache.
    
    Returns:
        Dictionary with cache statistics including:
        - built: Whether index is built
        - symbol_count: Total symbols in cache
        - stdlib_symbols: Number of stdlib symbols
        - third_party_symbols: Number of third-party symbols
        - cache_stats: Hit/miss statistics
        - cache_config: Current cache configuration
    """
    return {
        "built": _SYMBOL_INDEX_BUILT,
        "symbol_count": len(_SYMBOL_CACHE),
        "stdlib_symbols": len(_STDLIB_SYMBOL_CACHE),
        "third_party_symbols": len(_THIRD_PARTY_SYMBOL_CACHE),
        "confirmed_mappings": len(_CONFIRMED_MAPPINGS),
        "tracked_packages": len(_TRACKED_PACKAGES),
        "cache_stats": dict(_CACHE_STATS),
        "cache_config": dict(_CACHE_CONFIG),
    }


def clear_symbol_cache() -> None:
    """
    Clear the symbol cache (memory only).
    
    For full reset including persistent cache, use rebuild_symbol_index().
    """
    global _SYMBOL_INDEX_BUILT, _STDLIB_CACHE_BUILT, _THIRD_PARTY_CACHE_BUILT
    _SYMBOL_CACHE.clear()
    _STDLIB_SYMBOL_CACHE.clear()
    _THIRD_PARTY_SYMBOL_CACHE.clear()
    _CONFIRMED_MAPPINGS.clear()
    _TRACKED_PACKAGES.clear()
    _SYMBOL_INDEX_BUILT = False
    _STDLIB_CACHE_BUILT = False
    _THIRD_PARTY_CACHE_BUILT = False


# ============== Cache Configuration API ==============

def set_cache_config(
    symbol_index_ttl: Optional[int] = None,
    stdlib_cache_ttl: Optional[int] = None,
    third_party_cache_ttl: Optional[int] = None,
    enable_compression: Optional[bool] = None,
    max_cache_size_mb: Optional[int] = None,
) -> None:
    """
    Configure cache settings.
    
    Args:
        symbol_index_ttl: TTL for symbol index in seconds (default: 86400 = 24h)
        stdlib_cache_ttl: TTL for stdlib cache in seconds (default: 604800 = 7 days)
        third_party_cache_ttl: TTL for third-party cache in seconds (default: 86400 = 24h)
        enable_compression: Enable cache compression for large files (default: False)
        max_cache_size_mb: Maximum cache size in MB (default: 100)
        
    Example:
        set_cache_config(symbol_index_ttl=3600)  # 1 hour TTL
        set_cache_config(stdlib_cache_ttl=2592000)  # 30 days for stdlib
    """
    if symbol_index_ttl is not None:
        _CACHE_CONFIG["symbol_index_ttl"] = symbol_index_ttl
    if stdlib_cache_ttl is not None:
        _CACHE_CONFIG["stdlib_cache_ttl"] = stdlib_cache_ttl
    if third_party_cache_ttl is not None:
        _CACHE_CONFIG["third_party_cache_ttl"] = third_party_cache_ttl
    if enable_compression is not None:
        _CACHE_CONFIG["enable_compression"] = enable_compression
    if max_cache_size_mb is not None:
        _CACHE_CONFIG["max_cache_size_mb"] = max_cache_size_mb


def get_cache_config() -> Dict[str, Any]:
    """
    Get current cache configuration.
    
    Returns:
        Dictionary with cache configuration options
    """
    return dict(_CACHE_CONFIG)


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with:
        - symbol_hits: Number of cache hits for symbol lookups
        - symbol_misses: Number of cache misses
        - module_hits: Module cache hits
        - module_misses: Module cache misses
        - last_build_time: Time taken for last index build
        - build_count: Number of times index was built
        - hit_rate: Overall cache hit rate
    """
    total_hits = _CACHE_STATS["symbol_hits"] + _CACHE_STATS["module_hits"]
    total_misses = _CACHE_STATS["symbol_misses"] + _CACHE_STATS["module_misses"]
    total_requests = total_hits + total_misses
    hit_rate = total_hits / total_requests if total_requests > 0 else 0.0
    
    return {
        **_CACHE_STATS,
        "hit_rate": hit_rate,
        "total_requests": total_requests,
    }


def reset_cache_stats() -> None:
    """Reset cache statistics."""
    global _CACHE_STATS
    _CACHE_STATS = {
        "symbol_hits": 0,
        "symbol_misses": 0,
        "module_hits": 0,
        "module_misses": 0,
        "last_build_time": 0.0,
        "build_count": 0,
    }


def invalidate_package_cache(package_name: str) -> bool:
    """
    Invalidate cache for a specific package.
    
    Useful after upgrading a package to force re-scanning.
    
    Args:
        package_name: Name of the package to invalidate
        
    Returns:
        True if package was in cache and invalidated
    """
    global _TRACKED_PACKAGES, _THIRD_PARTY_CACHE_BUILT
    
    if package_name in _TRACKED_PACKAGES:
        del _TRACKED_PACKAGES[package_name]
        _THIRD_PARTY_CACHE_BUILT = False
        _save_tracked_packages()
        return True
    return False


def get_cache_version() -> str:
    """
    Get current cache version.
    
    Returns:
        Cache version string
    """
    return _CACHE_VERSION


# ============== File Cache System ==============

# Current caller file info
_CALLER_FILE_PATH: Optional[str] = None
_CALLER_FILE_SHA: Optional[str] = None
_CALLER_LOADED_MODULES: Set[str] = set()  # Modules loaded for current file

# Cache directory (can be customized)
_CACHE_DIR: Optional[_Path_class] = None  # None means use default


def _get_default_cache_dir() -> _Path_class:
    """Get default cache directory path."""
    return _Path_class.home() / ".laziest_import" / "cache"


def _get_cache_dir() -> _Path_class:
    """Get or create cache directory."""
    cache_dir = _CACHE_DIR if _CACHE_DIR is not None else _get_default_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_cache_size() -> int:
    """
    Get total cache size in bytes.
    
    Returns:
        Total size of all cache files in bytes
    """
    cache_dir = _get_cache_dir()
    total_size = 0
    try:
        for cache_file in cache_dir.glob("*.json"):
            total_size += cache_file.stat().st_size
    except (OSError, IOError):
        pass
    return total_size


def _cleanup_cache_if_needed() -> None:
    """
    Clean up old cache files if cache size exceeds limit.
    
    Removes oldest cache files until size is under limit.
    """
    max_size_bytes = _CACHE_CONFIG.get("max_cache_size_mb", 100) * 1024 * 1024
    current_size = _get_cache_size()
    
    if current_size <= max_size_bytes:
        return
    
    cache_dir = _get_cache_dir()
    
    # Get all cache files with their modification times
    cache_files = []
    try:
        for cache_file in cache_dir.glob("*.json"):
            cache_files.append((cache_file, cache_file.stat().st_mtime))
    except (OSError, IOError):
        return
    
    # Sort by modification time (oldest first)
    cache_files.sort(key=lambda x: x[1])
    
    # Remove oldest files until size is under limit
    for cache_file, _ in cache_files:
        if current_size <= max_size_bytes:
            break
        try:
            file_size = cache_file.stat().st_size
            cache_file.unlink()
            current_size -= file_size
            if _DEBUG_MODE:
                _logging_module.debug(f"[laziest-import] Removed old cache file: {cache_file.name}")
        except (OSError, IOError):
            continue


def _check_cache_size_before_save() -> bool:
    """
    Check if we should save cache based on size limit.
    
    Returns:
        True if saving is allowed, False if cache is full
    """
    max_size_bytes = _CACHE_CONFIG.get("max_cache_size_mb", 100) * 1024 * 1024
    current_size = _get_cache_size()
    
    # Allow save if under 90% of limit
    return current_size < max_size_bytes * 0.9


def set_cache_dir(path: Union[str, _Path_class]) -> None:
    """
    Set custom cache directory.
    
    Args:
        path: _Path_class to the cache directory. Can be a string or Path object.
        
    Example:
        set_cache_dir("./my_cache")  # Use project-local cache
        set_cache_dir("/tmp/laziest_cache")  # Use temp directory
    """
    global _CACHE_DIR
    _CACHE_DIR = _Path_class(path).resolve()


def get_cache_dir() -> _Path_class:
    """
    Get current cache directory path.
    
    Returns:
        Path object pointing to the cache directory
    """
    return _get_cache_dir()


def reset_cache_dir() -> None:
    """
    Reset cache directory to default location (~/.laziest_import/cache).
    """
    global _CACHE_DIR
    _CACHE_DIR = None


# ============== Symbol Index Persistence ==============

def _get_symbol_index_path(cache_type: str = "all") -> _Path_class:
    """
    Get symbol index cache file path.
    
    Args:
        cache_type: 'all', 'stdlib', or 'third_party'
        
    Returns:
        Path to the symbol index cache file
    """
    cache_dir = _get_cache_dir()
    if cache_type == "stdlib":
        return cache_dir / "symbol_index_stdlib.json"
    elif cache_type == "third_party":
        return cache_dir / "symbol_index_third_party.json"
    else:
        return cache_dir / "symbol_index.json"


def _get_tracked_packages_path() -> _Path_class:
    """Get tracked packages file path."""
    return _get_cache_dir() / "tracked_packages.json"


@_dataclass
class SymbolIndexCache:
    """Symbol index cache with metadata."""
    version: str
    cache_type: str  # 'all', 'stdlib', 'third_party'
    timestamp: float
    symbol_count: int
    module_count: int
    symbols: Dict[str, List[Tuple[str, str, Optional[str]]]]
    python_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "cache_type": self.cache_type,
            "timestamp": self.timestamp,
            "symbol_count": self.symbol_count,
            "module_count": self.module_count,
            "python_version": self.python_version,
            "symbols": self.symbols,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SymbolIndexCache":
        return cls(
            version=data.get("version", "0.0"),
            cache_type=data.get("cache_type", "all"),
            timestamp=data.get("timestamp", 0.0),
            symbol_count=data.get("symbol_count", 0),
            module_count=data.get("module_count", 0),
            symbols=data.get("symbols", {}),
            python_version=data.get("python_version", ""),
        )


def _save_symbol_index(
    symbols: Dict[str, List[Tuple[str, str, Optional[str]]]],
    cache_type: str = "all",
    module_count: int = 0
) -> bool:
    """
    Save symbol index to cache file.
    
    Args:
        symbols: Symbol cache dictionary
        cache_type: 'all', 'stdlib', or 'third_party'
        module_count: Number of modules scanned
        
    Returns:
        True if saved successfully
    """
    try:
        # Check cache size and cleanup if needed
        _cleanup_cache_if_needed()
        
        # Convert tuples to lists for JSON serialization
        serializable_symbols = {}
        for name, locations in symbols.items():
            serializable_symbols[name] = [list(loc) for loc in locations]
        
        cache = SymbolIndexCache(
            version=_CACHE_VERSION,
            cache_type=cache_type,
            timestamp=_time_module.time(),
            symbol_count=len(symbols),
            module_count=module_count,
            symbols=serializable_symbols,
            python_version=f"{_sys_module.version_info.major}.{_sys_module.version_info.minor}.{_sys_module.version_info.micro}",
        )
        
        cache_path = _get_symbol_index_path(cache_type)
        with open(cache_path, 'w', encoding='utf-8') as f:
            _json_module.dump(cache.to_dict(), f, indent=2)
        
        if _DEBUG_MODE:
            _logging_module.info(
                f"[laziest-import] Saved {cache_type} symbol index: "
                f"{len(symbols)} symbols from {module_count} modules"
            )
        return True
    except Exception as e:
        if _DEBUG_MODE:
            _logging_module.warning(f"[laziest-import] Failed to save symbol index: {e}")
        return False


def _load_symbol_index(cache_type: str = "all") -> Optional[SymbolIndexCache]:
    """
    Load symbol index from cache file.
    
    Args:
        cache_type: 'all', 'stdlib', or 'third_party'
        
    Returns:
        SymbolIndexCache object, or None if not found/invalid
    """
    try:
        cache_path = _get_symbol_index_path(cache_type)
        if not cache_path.exists():
            return None
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = _json_module.load(f)
        
        cache = SymbolIndexCache.from_dict(data)
        
        # Check version compatibility
        if cache.version != _CACHE_VERSION:
            if _DEBUG_MODE:
                _logging_module.info(
                    f"[laziest-import] Symbol index version mismatch: "
                    f"{cache.version} != {_CACHE_VERSION}, will rebuild"
                )
            return None
        
        # Check Python version compatibility (major.minor should match)
        current_py = f"{_sys_module.version_info.major}.{_sys_module.version_info.minor}"
        if cache.python_version and not cache.python_version.startswith(current_py):
            if _DEBUG_MODE:
                _logging_module.info(
                    f"[laziest-import] Python version changed: "
                    f"{cache.python_version} -> {current_py}, will rebuild"
                )
            return None
        
        # Check TTL
        ttl = _CACHE_CONFIG.get("symbol_index_ttl", 86400)
        if cache_type == "stdlib":
            ttl = _CACHE_CONFIG.get("stdlib_cache_ttl", 604800)
        elif cache_type == "third_party":
            ttl = _CACHE_CONFIG.get("third_party_cache_ttl", 86400)
        
        if _time_module.time() - cache.timestamp > ttl:
            if _DEBUG_MODE:
                _logging_module.info(
                    f"[laziest-import] {cache_type} symbol index expired (TTL: {ttl}s)"
                )
            return None
        
        return cache
    except Exception as e:
        if _DEBUG_MODE:
            _logging_module.warning(f"[laziest-import] Failed to load symbol index: {e}")
        return None


def _save_tracked_packages() -> bool:
    """Save tracked packages information."""
    try:
        path = _get_tracked_packages_path()
        with open(path, 'w', encoding='utf-8') as f:
            _json_module.dump(_TRACKED_PACKAGES, f, indent=2)
        return True
    except Exception as e:
        if _DEBUG_MODE:
            _logging_module.warning(f"[laziest-import] Failed to save tracked packages: {e}")
        return False


def _load_tracked_packages() -> Dict[str, Dict[str, Any]]:
    """Load tracked packages information."""
    try:
        path = _get_tracked_packages_path()
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return _json_module.load(f)
    except Exception:
        pass
    return {}


def _get_package_version(package_name: str) -> Optional[str]:
    """Get installed version of a package."""
    try:
        # Try importlib.metadata first (Python 3.8+)
        from importlib.metadata import version as get_version
        return get_version(package_name)
    except Exception:
        return None


def _track_package(package_name: str, module_count: int = 0) -> None:
    """
    Track a package for incremental updates.
    
    Args:
        package_name: Name of the package
        module_count: Number of modules in the package
    """
    global _TRACKED_PACKAGES
    version = _get_package_version(package_name)
    _TRACKED_PACKAGES[package_name] = {
        "version": version,
        "mtime": _time_module.time(),
        "module_count": module_count,
    }


def _check_package_changed(package_name: str) -> bool:
    """
    Check if a package has changed since last scan.
    
    Args:
        package_name: Name of the package
        
    Returns:
        True if package changed or not tracked
    """
    if package_name not in _TRACKED_PACKAGES:
        return True
    
    tracked = _TRACKED_PACKAGES[package_name]
    current_version = _get_package_version(package_name)
    
    # Version changed
    if current_version and tracked.get("version") != current_version:
        return True
    
    return False


def _calculate_file_sha(file_path: str) -> Optional[str]:
    """
    Calculate SHA256 hash of a file.
    
    Args:
        file_path: _Path_class to the file
        
    Returns:
        SHA256 hash string, or None if file not found
    """
    try:
        path = _Path_class(file_path)
        if not path.exists():
            return None
        
        sha256 = _hashlib_module.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (OSError, IOError):
        return None


def _get_caller_file_path() -> Optional[str]:
    """
    Get the path of the file that imported laziest_import.
    
    Returns:
        File path string, or None if not found
    """
    try:
        # Walk up the stack to find the first file outside this package
        for frame_info in _traceback_module.extract_stack():
            # Skip files within laziest_import package
            if 'laziest_import' not in frame_info.filename:
                # Also skip internal Python files
                if not frame_info.filename.startswith('<'):
                    return str(_Path_class(frame_info.filename).resolve())
    except Exception:
        pass
    return None


def _get_cache_file_path(file_path: str) -> _Path_class:
    """
    Get cache file path for a given source file.
    
    Args:
        file_path: Source file path
        
    Returns:
        Cache file path
    """
    # Use SHA256 of file path as cache filename
    path_hash = _hashlib_module.sha256(file_path.encode()).hexdigest()
    return _get_cache_dir() / f"{path_hash}.json"


@_dataclass
class FileCache:
    """Cache data for a single file."""
    file_path: str
    file_sha: str
    loaded_modules: List[str]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return _asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileCache":
        return cls(**data)


def _load_file_cache(file_path: str) -> Optional[FileCache]:
    """
    Load cache for a file.
    
    Args:
        file_path: Source file path
        
    Returns:
        FileCache object, or None if not found/invalid
    """
    cache_file = _get_cache_file_path(file_path)
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = _json_module.load(f)
        return FileCache.from_dict(data)
    except (_json_module.JSONDecodeError, KeyError, OSError):
        return None


def _save_file_cache(file_path: str, file_sha: str, modules: Set[str]) -> bool:
    """
    Save cache for a file.
    
    Args:
        file_path: Source file path
        file_sha: SHA256 hash of the file
        modules: Set of loaded module names
        
    Returns:
        True if saved successfully
    """
    try:
        # Check cache size and cleanup if needed
        _cleanup_cache_if_needed()
        
        cache = FileCache(
            file_path=file_path,
            file_sha=file_sha,
            loaded_modules=list(modules),
            timestamp=_time_module.time()
        )
        
        cache_file = _get_cache_file_path(file_path)
        with open(cache_file, 'w', encoding='utf-8') as f:
            _json_module.dump(cache.to_dict(), f, indent=2)
        
        if _DEBUG_MODE:
            _logging_module.info(f"[laziest-import] Saved cache for {file_path}: {len(modules)} modules")
        
        return True
    except (OSError, IOError) as e:
        if _DEBUG_MODE:
            _logging_module.warning(f"Failed to save cache: {e}")
        return False


def _init_file_cache() -> None:
    """
    Initialize file cache for the current caller file.
    
    Detects the caller file, loads existing cache if valid,
    and sets up module tracking.
    """
    global _CALLER_FILE_PATH, _CALLER_FILE_SHA, _CALLER_LOADED_MODULES
    
    if not _FILE_CACHE_ENABLED:
        return
    
    caller_path = _get_caller_file_path()
    if not caller_path:
        return
    
    _CALLER_FILE_PATH = caller_path
    caller_sha = _calculate_file_sha(caller_path)
    _CALLER_FILE_SHA = caller_sha
    
    if not caller_sha:
        return
    
    # Try to load existing cache
    cache = _load_file_cache(caller_path)
    
    if cache and cache.file_sha == caller_sha:
        # Cache is valid, preload modules in background
        if _DEBUG_MODE:
            _logging_module.info(
                f"[laziest-import] Found valid cache for {caller_path}: "
                f"{len(cache.loaded_modules)} modules"
            )
        
        # Store for preloading
        _CALLER_LOADED_MODULES = set(cache.loaded_modules)
        
        # Start background preloading (non-blocking)
        _start_background_preload(cache.loaded_modules)
    else:
        if _DEBUG_MODE:
            if cache:
                _logging_module.info(
                    f"[laziest-import] Cache outdated for {caller_path}, will rebuild"
                )
            else:
                _logging_module.info(
                    f"[laziest-import] No cache found for {caller_path}"
                )


def _start_background_preload(modules: List[str]) -> None:
    """
    Start background thread to preload modules in parallel.
    
    Uses ThreadPoolExecutor for parallel loading to improve speed.
    
    Args:
        modules: List of module names to preload
    """
    # Don't start background preload during initialization
    if not _INITIALIZED:
        return
    
    # Skip if no modules to preload
    if not modules:
        return
    
    # Filter out already loaded modules
    modules_to_load = [m for m in modules if m not in _sys_module.modules]
    if not modules_to_load:
        return
    
    def _preload_single(module_name: str) -> bool:
        """Preload a single module."""
        try:
            spec = _importlib_module.util.find_spec(module_name)
            if spec:
                _importlib_module.import_module(module_name)
                if _DEBUG_MODE:
                    _logging_module.debug(f"[laziest-import] Preloaded {module_name}")
                return True
        except Exception as e:
            if _DEBUG_MODE:
                _logging_module.debug(f"[laziest-import] Failed to preload {module_name}: {e}")
        return False
    
    def _preload_parallel():
        """Parallel preload worker."""
        if not _INITIALIZED:
            return
        
        # Use ThreadPoolExecutor for parallel loading
        # Limit workers to avoid overwhelming the system
        max_workers = min(4, len(modules_to_load))
        
        try:
            from concurrent.futures import ThreadPoolExecutor
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(_preload_single, modules_to_load))
        except ImportError:
            # Fallback to sequential loading if ThreadPoolExecutor not available
            for module_name in modules_to_load:
                _preload_single(module_name)
    
    # Start preload in daemon thread
    thread = _threading_module.Thread(target=_preload_parallel, daemon=True)
    thread.start()


def _record_module_load(module_name: str) -> None:
    """
    Record a module load for the current caller file.
    
    Args:
        module_name: Name of the loaded module
    """
    global _CALLER_LOADED_MODULES
    _CALLER_LOADED_MODULES.add(module_name)


def _save_current_cache() -> None:
    """Save cache for the current caller file (called at exit)."""
    if not _FILE_CACHE_ENABLED:
        return
    
    if _CALLER_FILE_PATH and _CALLER_FILE_SHA and _CALLER_LOADED_MODULES:
        _save_file_cache(
            _CALLER_FILE_PATH,
            _CALLER_FILE_SHA,
            _CALLER_LOADED_MODULES
        )


# Register exit handler
_atexit_module.register(_save_current_cache)


def _get_config_paths() -> List[_Path_class]:
    """
    Get configuration file paths in priority order (lowest to highest).
    
    Priority:
        1. Package default: laziest_import/aliases.json
        2. User global: ~/.laziest_import/aliases.json
        3. Project level: ./.laziest_import.json
    
    Returns:
        List of configuration file paths
    """
    paths = [
        _Path_class(__file__).parent / "aliases.json",  # Package default
        _Path_class.home() / ".laziest_import" / "aliases.json",  # User global
        _Path_class.cwd() / ".laziest_import.json",  # Project level
    ]
    return paths


def _load_aliases_from_file(path: _Path_class) -> Dict[str, str]:
    """
    Load aliases from a JSON configuration file.
    
    Supports two formats:
    1. Flat: {"alias": "module_name", ...}
    2. Categorized: {"category": {"alias": "module_name", ...}, ...}
    
    Args:
        path: _Path_class to the configuration file
        
    Returns:
        Dictionary of alias -> module_name mappings
    """
    if not path.exists():
        return {}
    
    try:
        with open(path, encoding="utf-8") as f:
            data = _json_module.load(f)
        
        # Flatten categorized structure
        aliases: Dict[str, str] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                # Categorized format
                aliases.update(value)
            elif isinstance(value, str):
                # Flat format
                aliases[key] = value
        
        return aliases
    except (_json_module.JSONDecodeError, OSError) as e:
        _warnings_module.warn(f"Failed to load config from {path}: {e}")
        return {}


def _load_all_aliases() -> Dict[str, str]:
    """
    Load aliases from all configuration files.
    
    Later files override earlier ones (project > user > default).
    
    Returns:
        Combined dictionary of all aliases
    """
    aliases: Dict[str, str] = {}
    
    for path in _get_config_paths():
        file_aliases = _load_aliases_from_file(path)
        if file_aliases:
            aliases.update(file_aliases)
    
    return aliases


def _validate_alias(alias: str, module_name: str) -> bool:
    """
    Validate an alias entry.
    
    Args:
        alias: The alias name
        module_name: The target module name
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(alias, str) or not isinstance(module_name, str):
        return False
    if not alias or not module_name:
        return False
    # Allow non-identifier aliases for pip package name mappings
    # (e.g., "scikit-learn", "xml.etree") - these are used for installation lookup
    # Only warn for truly invalid identifiers (like starting with digit)
    if not alias.isidentifier():
        # Skip warning for pip package names (contain -) or module paths (contain .)
        if '-' in alias or '.' in alias:
            return True  # Valid for pip package mapping
        # Warn for other invalid identifiers (e.g., "123invalid")
        _warnings_module.warn(f"Alias '{alias}' is not a valid Python identifier")
        return False
    return True


def _rebuild_global_namespace() -> None:
    """
    Rebuild the global namespace with current aliases.
    
    Creates LazyModule proxies for all aliases.
    Note: We no longer inject into globals() to avoid recursion issues.
    The __getattr__ hook handles attribute access instead.
    """
    global _LAZY_MODULES
    
    # Clear old lazy modules that are no longer in alias map
    for alias in list(_LAZY_MODULES.keys()):
        if alias not in _ALIAS_MAP:
            del _LAZY_MODULES[alias]
    
    # Create LazyModule proxies for all current aliases
    # Don't inject into globals() - let __getattr__ handle it
    for alias, module_name in _ALIAS_MAP.items():
        if alias not in _LAZY_MODULES:
            _LAZY_MODULES[alias] = LazyModule(alias, module_name)


def _build_known_modules_cache(force: bool = False) -> Set[str]:
    """
    Build cache of all known importable modules.
    
    Args:
        force: Force rebuild even if cache is still valid
        
    Returns:
        Set of installed module names
    """
    global _KNOWN_MODULES_CACHE, _KNOWN_MODULES_CACHE_TIME
    
    # Check if cache is still valid (not expired)
    current_time = _time_module.time()
    if _KNOWN_MODULES_CACHE is not None and not force:
        if current_time - _KNOWN_MODULES_CACHE_TIME < _KNOWN_MODULES_CACHE_TTL:
            return _KNOWN_MODULES_CACHE
    
    modules: Set[str] = set()
    
    # Add already loaded modules
    modules.update(_sys_module.modules.keys())
    
    # Iterate through all modules in search paths
    for path in _sys_module.path:
        # Skip empty strings and non-existent paths
        if not path:
            path = '.'
        if not _Path_class(path).exists():
            continue
        try:
            for finder, name, ispkg in _pkgutil_module.iter_modules([path]):
                modules.add(name)
        except (OSError, ImportError):
            continue
    
    # Add standard library modules (prefer _sys_module.stdlib_module_names for Python 3.10+)
    if hasattr(_sys_module, 'stdlib_module_names'):
        modules.update(_sys_module.stdlib_module_names)
    else:
        # Fallback for Python 3.8-3.9: manually add common standard library modules
        stdlib = {
            'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio',
            'asyncore', 'atexit', 'audioop', 'base64', 'bdb', 'binascii',
            'binhex', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb',
            'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
            'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib',
            'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
            'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal',
            'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings',
            'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
            'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt',
            'getpass', 'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib',
            'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib', 'imghdr',
            'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
            'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging',
            'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes',
            'mmap', 'modulefinder', 'multiprocessing', 'netrc', 'nis',
            'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev',
            'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
            'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
            'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc',
            'queue', 'quopri', 'random', 're', 'readline', 'reprlib', 'resource',
            'rlcompleter', 'runpy', 'sched', 'secrets', 'select', 'selectors',
            'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib',
            'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3', 'ssl',
            'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess',
            'sunau', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
            'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
            'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize',
            'trace', 'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo',
            'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uu',
            'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser',
            'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc',
            'zipapp', 'zipfile', 'zipimport', 'zlib', 'zoneinfo',
        }
        modules.update(stdlib)
    
    _KNOWN_MODULES_CACHE = modules
    _KNOWN_MODULES_CACHE_TIME = current_time
    return modules


def _levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Edit distance
    """
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def _get_module_abbreviations() -> Dict[str, str]:
    """
    Get common module abbreviations mapping.
    
    Returns:
        Dictionary mapping abbreviation to full module name
    """
    return {
        # Data Science
        "np": "numpy", "numpy": "numpy",
        "pd": "pandas", "pandas": "pandas",
        "plt": "matplotlib.pyplot", "mpl": "matplotlib",
        "sns": "seaborn", "seaborn": "seaborn",
        "sp": "scipy", "scipy": "scipy",
        "sk": "sklearn", "sklearn": "sklearn",
        # Machine Learning
        "tf": "tensorflow", "tensorflow": "tensorflow",
        "torch": "torch", "pytorch": "torch",
        "keras": "keras",
        "xgb": "xgboost", "xgboost": "xgboost",
        "lgb": "lightgbm", "lightgbm": "lightgbm",
        "cat": "catboost", "catboost": "catboost",
        # Web
        "flask": "flask", "django": "django",
        "fastapi": "fastapi", "api": "fastapi",
        "bs4": "bs4", "beautifulsoup": "bs4",
        "requests": "requests", "http": "httpx",
        # Database
        "db": "sqlite3", "sql": "sqlalchemy",
        "sa": "sqlalchemy", "orm": "sqlalchemy.orm",
        "mongo": "pymongo", "redis": "redis",
        # Utils
        "tqdm": "tqdm", "log": "logging",
        "yaml": "yaml", "toml": "toml",
        # Crypto
        "web3": "web3", "eth": "web3",
        # GUI
        "qt": "PyQt6", "tk": "tkinter",
        "gui": "tkinter",
        # Cloud
        "aws": "boto3", "s3": "boto3",
        "gcs": "google.cloud.storage",
        # NLP
        "nlp": "spacy", "spacy": "spacy",
        "nltk": "nltk",
        "hf": "transformers",
        # Visualization
        "px": "plotly.express", "go": "plotly.graph_objects",
        "alt": "altair",
        # Async
        "aio": "asyncio", "async": "asyncio",
        # Others
        "cv": "cv2", "opencv": "cv2",
        "pil": "PIL", "pillow": "PIL",
        "image": "PIL.Image",
        "crypto": "cryptography",
        "test": "pytest", "pytest": "pytest",
    }


def _get_package_rename_map() -> Dict[str, str]:
    """
    Get mapping of package import names to pip install names.
    
    Returns:
        Dictionary mapping import name to pip package name
    """
    return {
        "sklearn": "scikit-learn",
        "PIL": "pillow",
        "cv2": "opencv-python",
        "bs4": "beautifulsoup4",
        "yaml": "pyyaml",
        "dotenv": "python-dotenv",
        "jwt": "pyjwt",
        "dateutil": "python-dateutil",
        "leetcode": "leetcode-api",
        "crypto": "pycryptodome",
        "Crypto": "pycryptodome",
        "Image": "pillow",
        "Bio": "biopython",
        "OpenGL": "pyopengl",
        "fitz": "pymupdf",
        "docx": "python-docx",
        "pptx": "python-pptx",
        "win32com": "pywin32",
        "kafka": "kafka-python",
        "mqtt": "paho-mqtt",
        "zmq": "pyzmq",
        "web3": "web3",
        "eth": "web3",
        "selenium": "selenium",
        "webdriver": "selenium",
        "dash": "dash",
        "dcc": "dash-core-components",
        "st": "streamlit",
        "streamlit": "streamlit",
        "gradio": "gradio",
        "wandb": "wandb",
        "mlflow": "mlflow",
        "dvc": "dvc",
    }


def _search_module(name: str) -> Optional[str]:
    """
    Search for a matching module name with enhanced fuzzy matching.
    
    Matching priority:
    1. Exact match in known modules
    2. Direct import test
    3. Abbreviation expansion
    4. Package rename mapping
    5. Case-insensitive match
    6. Underscore/hyphen variants
    7. Prefix/suffix match
    8. Levenshtein distance fuzzy match
    9. Phonetic/common misspelling match
    
    Args:
        name: Name to search for
        
    Returns:
        Found module name, or None if not found
    """
    if not _AUTO_SEARCH_ENABLED:
        return None
    
    known_modules = _build_known_modules_cache()
    name_lower = name.lower()
    name_stripped = name_lower.replace('_', '').replace('-', '')
    
    # 1. Exact match
    if name in known_modules:
        return name
    
    # 2. Try direct import
    try:
        spec = _importlib_module.util.find_spec(name)
        if spec is not None:
            return name
    except (ImportError, ModuleNotFoundError, ValueError):
        pass
    
    # 3. Check abbreviations
    abbrev_map = _get_module_abbreviations()
    if name_lower in abbrev_map:
        target = abbrev_map[name_lower]
        if target in known_modules:
            return target
        # Try importing the expanded abbreviation
        try:
            spec = _importlib_module.util.find_spec(target)
            if spec is not None:
                return target
        except (ImportError, ModuleNotFoundError, ValueError):
            pass
    
    # 4. Check package rename map (e.g., sklearn -> scikit-learn)
    rename_map = _get_package_rename_map()
    if name in rename_map:
        pip_name = rename_map[name]
        # This might not be importable, but we can suggest installation
    
    # Collect candidates with priority scores
    candidates: List[Tuple[int, int, str]] = []  # (priority, distance, module_name)
    
    for mod_name in known_modules:
        mod_lower = mod_name.lower()
        mod_stripped = mod_lower.replace('_', '').replace('-', '')
        
        # Priority 0: Case-insensitive exact match
        if mod_lower == name_lower:
            candidates.append((0, 0, mod_name))
        
        # Priority 1: Abbreviation match (e.g., np -> numpy)
        elif mod_lower == name_stripped or mod_stripped == name_lower:
            candidates.append((1, 0, mod_name))
        
        # Priority 2: Underscore/hyphon variant match (e.g., my_lib vs mylib)
        elif mod_stripped == name_stripped and mod_stripped != mod_lower:
            candidates.append((2, 0, mod_name))
        
        # Priority 3: Common suffix patterns
        elif _check_common_suffix_match(name_lower, mod_lower):
            candidates.append((3, 0, mod_name))
        
        # Priority 4: Prefix match (search name is prefix of module)
        elif mod_lower.startswith(name_lower) and len(name_lower) >= 3:
            distance = len(mod_lower) - len(name_lower)
            candidates.append((4, distance, mod_name))
        
        # Priority 5: Suffix match (search name is suffix of module)
        elif mod_lower.endswith(name_lower) and len(name_lower) >= 3:
            distance = len(mod_lower) - len(name_lower)
            candidates.append((5, distance, mod_name))
        
        # Priority 6: Contains match (search name contained in module)
        elif name_lower in mod_lower and len(name_lower) >= 4:
            distance = mod_lower.index(name_lower)
            candidates.append((6, distance, mod_name))
        
        # Priority 7: Fuzzy match using Levenshtein distance
        elif len(name_lower) >= 3 and len(mod_lower) >= 3:
            # Only compute for similar lengths
            length_ratio = len(name_lower) / len(mod_lower) if len(mod_lower) > 0 else 0
            if 0.5 <= length_ratio <= 2.0:
                distance = _levenshtein_distance(name_lower, mod_lower)
                max_distance = min(3, max(len(name_lower), len(mod_lower)) // 3)
                if distance <= max_distance:
                    candidates.append((7, distance, mod_name))
    
    if candidates:
        # Sort by priority, then by distance
        candidates.sort(key=lambda x: (x[0], x[1]))
        best = candidates[0]
        
        if _DEBUG_MODE:
            _logging_module.debug(
                f"[laziest-import] Fuzzy match: '{name}' -> '{best[2]}' "
                f"(priority={best[0]}, distance={best[1]})"
            )
        
        return best[2]
    
    return None


def _check_common_suffix_match(name: str, module: str) -> bool:
    """
    Check if name matches module with common suffix patterns.
    
    Args:
        name: Search name (lowercase)
        module: Module name (lowercase)
        
    Returns:
        True if matches common pattern
    """
    # Common module suffixes
    suffixes = [
        'py', 'python', 'lib', 'library', 'api', 'client', 'sdk',
        'core', 'utils', 'tools', 'helper', 'wrapper', 'handler',
        'db', 'sql', 'io', 'cli', 'gui', 'ui', 'web', 'http',
        'async', 'sync', 'multi', 'base', 'simple', 'easy', 'fast',
        'ml', 'ai', 'dl', 'nn', 'cv', 'nlp', 'data', 'geo', 'sci',
    ]
    
    # Check if module is name + suffix
    for suffix in suffixes:
        if module == f"{name}{suffix}" or module == f"{name}_{suffix}":
            return True
        if name == f"{module}{suffix}" or name == f"{module}_{suffix}":
            return True
    
    # Check special patterns
    patterns = [
        # scikit-learn -> sklearn
        (lambda n, m: m == n.replace('-', '').replace('_', '')),
        # Pillow -> PIL
        (lambda n, m: n == 'pillow' and m == 'pil'),
        (lambda n, m: n == 'pil' and m == 'pillow'),
        # OpenCV -> cv2
        (lambda n, m: n == 'opencv' and m.startswith('cv')),
        (lambda n, m: m == 'opencv' and n.startswith('cv')),
        # BeautifulSoup -> bs4
        (lambda n, m: 'beautiful' in n and m == 'bs4'),
        (lambda n, m: n == 'bs4' and 'beautiful' in m),
        # PyTorch -> torch
        (lambda n, m: n == 'pytorch' and m == 'torch'),
        (lambda n, m: m == 'pytorch' and n == 'torch'),
        # TensorFlow -> tensorflow
        (lambda n, m: n == 'tf' and m == 'tensorflow'),
        (lambda n, m: m == 'tf' and n == 'tensorflow'),
        # scikit-learn patterns
        (lambda n, m: n.startswith('sk') and m.startswith('scikit')),
        (lambda n, m: m.startswith('sk') and n.startswith('scikit')),
    ]
    
    for pattern in patterns:
        try:
            if pattern(name, module):
                return True
        except Exception:
            continue
    
    return False


def _search_class_in_modules(class_name: str) -> Optional[Tuple[str, Any]]:
    """
    Search for a class in loaded modules.
    
    Args:
        class_name: Class name
        
    Returns:
        Tuple of (module_name, class_object), or None if not found
    """
    # Check cache
    if class_name in _CLASS_TO_MODULE_CACHE:
        mod_name = _CLASS_TO_MODULE_CACHE[class_name]
        try:
            mod = _sys_module.modules.get(mod_name) or _importlib_module.import_module(mod_name)
            if hasattr(mod, class_name):
                return (mod_name, getattr(mod, class_name))
        except (ImportError, ModuleNotFoundError):
            pass
    
    # Search in loaded modules
    for mod_name, mod in list(_sys_module.modules.items()):
        if mod is None:
            continue
        try:
            obj = getattr(mod, class_name, None)
            if obj is not None and isinstance(obj, type):
                _CLASS_TO_MODULE_CACHE[class_name] = mod_name
                return (mod_name, obj)
        except Exception:
            continue
    
    return None


class LazyModule:
    """
    Lazy loading module proxy class.
    
    Imports the actual module only when attributes are accessed.
    Supports auto-search for unregistered modules and submodule lazy loading.
    """
    
    __slots__ = ('_alias', '_module_name', '_cached_module', '_auto_searched', '_submodule_cache')
    
    def __init__(self, alias: str, module_name: str, auto_searched: bool = False):
        object.__setattr__(self, '_alias', alias)
        object.__setattr__(self, '_module_name', module_name)
        object.__setattr__(self, '_cached_module', None)
        object.__setattr__(self, '_auto_searched', auto_searched)
        object.__setattr__(self, '_submodule_cache', {})
    
    def _get_module(self) -> Any:
        """Get the actual module (lazy load)"""
        cached = object.__getattribute__(self, '_cached_module')
        if cached is not None:
            # Update access count and cache hit
            alias = object.__getattribute__(self, '_alias')
            _IMPORT_STATS.module_access_counts[alias] = _IMPORT_STATS.module_access_counts.get(alias, 0) + 1
            _CACHE_STATS["module_hits"] += 1
            return cached
        
        # Cache miss - will need to load
        _CACHE_STATS["module_misses"] += 1
        
        module_name = object.__getattribute__(self, '_module_name')
        alias = object.__getattribute__(self, '_alias')
        
        # Recursion protection: check if we're already importing this module
        importing_modules = _get_importing_modules()
        if module_name in importing_modules:
            # Direct import to avoid recursion
            return _importlib_module.import_module(module_name)
        
        # Mark this module as being imported
        importing_modules.add(module_name)
        
        try:
            # Execute pre-import hooks
            for hook in _PRE_IMPORT_HOOKS:
                try:
                    hook(module_name)
                except Exception as e:
                    if _DEBUG_MODE:
                        _logging_module.warning(f"Pre-import hook failed for {module_name}: {e}")
            
            # Import with optional retry
            start_time = _time_module.perf_counter()
            
            def _do_import(name: str) -> Any:
                """Internal import function with retry support"""
                if not _RETRY_CONFIG["enabled"]:
                    return _importlib_module.import_module(name)
                
                max_retries = _RETRY_CONFIG["max_retries"]
                retry_delay = _RETRY_CONFIG["retry_delay"]
                retry_modules = _RETRY_CONFIG["retry_modules"]
                
                # Check if this module should be retried
                if retry_modules and name.split('.')[0] not in retry_modules:
                    return _importlib_module.import_module(name)
                
                # Check if we're in an async context (to avoid blocking the event loop)
                in_async_context = False
                try:
                    loop = _asyncio_module.get_running_loop()
                    in_async_context = loop is not None
                except RuntimeError:
                    pass  # No running loop
                
                last_error = None
                for attempt in range(max_retries + 1):
                    try:
                        return _importlib_module.import_module(name)
                    except ImportError as e:
                        last_error = e
                        if attempt < max_retries:
                            if _DEBUG_MODE:
                                _logging_module.info(f"Retry {attempt + 1}/{max_retries} for {name}")
                            # Skip sleep in async context to avoid blocking event loop
                            if not in_async_context:
                                _time_module.sleep(retry_delay)
                            elif _DEBUG_MODE:
                                _logging_module.debug(f"Skipping retry sleep in async context for {name}")
                raise last_error
            
            try:
                module = _do_import(module_name)
                
                # Update statistics
                elapsed = _time_module.perf_counter() - start_time
                _IMPORT_STATS.total_imports += 1
                _IMPORT_STATS.total_time += elapsed
                _IMPORT_STATS.module_times[module_name] = elapsed
                _IMPORT_STATS.module_access_counts[alias] = 1
                
                # Record for file cache
                _record_module_load(module_name)
                
                object.__setattr__(self, '_cached_module', module)
                
                # Execute post-import hooks
                for hook in _POST_IMPORT_HOOKS:
                    try:
                        hook(module_name, module)
                    except Exception as e:
                        if _DEBUG_MODE:
                            _logging_module.warning(f"Post-import hook failed for {module_name}: {e}")
                
                if _DEBUG_MODE:
                    _logging_module.info(f"[laziest-import] Loaded module '{module_name}' in {elapsed*1000:.2f}ms")
                
                return module
            except ImportError as e:
                # If auto-search is enabled and not yet searched, try searching for the module
                auto_searched = object.__getattribute__(self, '_auto_searched')
                if _AUTO_SEARCH_ENABLED and not auto_searched:
                    found_name = _search_module(alias)
                    if found_name and found_name != module_name:
                        try:
                            module = _do_import(found_name)
                            object.__setattr__(self, '_module_name', found_name)
                            object.__setattr__(self, '_cached_module', module)
                            object.__setattr__(self, '_auto_searched', True)
                            # Update global mapping
                            _ALIAS_MAP[alias] = found_name
                            
                            # Update statistics
                            elapsed = _time_module.perf_counter() - start_time
                            _IMPORT_STATS.total_imports += 1
                            _IMPORT_STATS.total_time += elapsed
                            _IMPORT_STATS.module_times[found_name] = elapsed
                            
                            return module
                        except ImportError:
                            pass
                
                # Try auto-install if enabled
                if _AUTO_INSTALL_CONFIG["enabled"]:
                    pip_package = _get_pip_package_name(module_name)
                    
                    # Confirm installation if interactive
                    should_install = True
                    if _AUTO_INSTALL_CONFIG["interactive"]:
                        should_install = _interactive_install_confirm(module_name, pip_package)
                    
                    if should_install:
                        success, message = _install_package_sync(
                            pip_package,
                            index=_AUTO_INSTALL_CONFIG["index"],
                            extra_args=_AUTO_INSTALL_CONFIG["extra_args"],
                            prefer_uv=_AUTO_INSTALL_CONFIG["prefer_uv"],
                            silent=_AUTO_INSTALL_CONFIG["silent"]
                        )
                        
                        if success:
                            if _DEBUG_MODE:
                                _logging_module.info(f"[laziest-import] {message}")
                            
                            # Rebuild module cache
                            rebuild_module_cache()
                            
                            # Try importing again
                            try:
                                module = _do_import(module_name)
                                
                                # Update statistics
                                elapsed = _time_module.perf_counter() - start_time
                                _IMPORT_STATS.total_imports += 1
                                _IMPORT_STATS.total_time += elapsed
                                _IMPORT_STATS.module_times[module_name] = elapsed
                                _IMPORT_STATS.module_access_counts[alias] = 1
                                
                                # Record for file cache
                                _record_module_load(module_name)
                                
                                object.__setattr__(self, '_cached_module', module)
                                
                                return module
                            except ImportError as import_error:
                                raise ImportError(
                                    f"Module '{module_name}' was installed but still cannot be imported. "
                                    f"Error: {import_error}"
                                ) from import_error
                        else:
                            if _DEBUG_MODE:
                                _logging_module.warning(f"[laziest-import] Auto-install failed: {message}")
                
                raise ImportError(
                    f"Cannot import module '{module_name}' (alias '{alias}'). "
                    f"Please ensure the module is installed: pip install {module_name.split('.')[0]}"
                ) from e
        finally:
            # Always clean up the importing mark
            importing_modules.discard(module_name)
    
    def __getattr__(self, name: str) -> Any:
        # Protect access to private attributes (prevents recursion issues)
        # But allow common dunder attributes that modules typically have
        if name.startswith('_'):
            allowed_dunder = {'__name__', '__file__', '__path__', '__package__',
                             '__loader__', '__spec__', '__doc__', '__version__'}
            if name not in allowed_dunder:
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        module = self._get_module()
        attr = getattr(module, name)
        
        # If the attribute is a module, return a LazySubmodule for recursive lazy loading
        if isinstance(attr, _ModuleType):
            submodule_cache = object.__getattribute__(self, '_submodule_cache')
            if name not in submodule_cache:
                full_name = f"{object.__getattribute__(self, '_module_name')}.{name}"
                submodule_cache[name] = LazySubmodule(full_name, self, name)
            return submodule_cache[name]
        
        return attr
    
    def __dir__(self) -> List[str]:
        module = self._get_module()
        return dir(module)
    
    def __repr__(self) -> str:
        module_name = object.__getattribute__(self, '_module_name')
        cached = object.__getattribute__(self, '_cached_module')
        if cached is not None:
            return f"<LazyModule '{module_name}' (loaded)>"
        return f"<LazyModule '{module_name}' (not loaded)>"
    
    # Support calling module directly (if module itself is callable)
    def __call__(self, *args, **kwargs) -> Any:
        module = self._get_module()
        if callable(module):
            return module(*args, **kwargs)
        module_name = object.__getattribute__(self, '_module_name')
        raise TypeError(f"Module '{module_name}' ({type(module).__name__}) is not callable")


class LazySubmodule:
    """
    Lazy loading submodule proxy class.
    
    Supports recursive lazy loading for nested module access like np.linalg.svd.
    """
    
    __slots__ = ('_full_name', '_parent', '_attr_name', '_cached_module', '_submodule_cache')
    
    def __init__(self, full_name: str, parent: Union[LazyModule, 'LazySubmodule'], attr_name: str):
        object.__setattr__(self, '_full_name', full_name)
        object.__setattr__(self, '_parent', parent)
        object.__setattr__(self, '_attr_name', attr_name)
        object.__setattr__(self, '_cached_module', None)
        object.__setattr__(self, '_submodule_cache', {})
    
    def _get_module(self) -> Any:
        """Get the actual submodule (lazy load)"""
        cached = object.__getattribute__(self, '_cached_module')
        if cached is not None:
            _CACHE_STATS["module_hits"] += 1
            return cached
        
        # Cache miss - will need to load
        _CACHE_STATS["module_misses"] += 1
        
        full_name = object.__getattribute__(self, '_full_name')
        
        start_time = _time_module.perf_counter()
        
        try:
            module = _importlib_module.import_module(full_name)
            
            # Update statistics
            elapsed = _time_module.perf_counter() - start_time
            _IMPORT_STATS.total_imports += 1
            _IMPORT_STATS.total_time += elapsed
            _IMPORT_STATS.module_times[full_name] = elapsed
            
            # Record for file cache
            _record_module_load(full_name)
            
            object.__setattr__(self, '_cached_module', module)
            
            if _DEBUG_MODE:
                _logging_module.info(f"[laziest-import] Loaded submodule '{full_name}' in {elapsed*1000:.2f}ms")
            
            return module
        except ImportError:
            # Fallback: get attribute from parent module
            parent = object.__getattribute__(self, '_parent')
            attr_name = object.__getattribute__(self, '_attr_name')
            parent_module = parent._get_module()
            attr = getattr(parent_module, attr_name)
            
            if isinstance(attr, _ModuleType):
                object.__setattr__(self, '_cached_module', attr)
                return attr
            
            # If it's not a module, return the attribute directly
            return attr
    
    def __getattr__(self, name: str) -> Any:
        # Protect access to private attributes (prevents recursion issues)
        # But allow common dunder attributes that modules typically have
        if name.startswith('_'):
            allowed_dunder = {'__name__', '__file__', '__path__', '__package__',
                             '__loader__', '__spec__', '__doc__', '__version__'}
            if name not in allowed_dunder:
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        module = self._get_module()
        attr = getattr(module, name)
        
        # If the attribute is a module, return a LazySubmodule for recursive lazy loading
        if isinstance(attr, _ModuleType):
            submodule_cache = object.__getattribute__(self, '_submodule_cache')
            if name not in submodule_cache:
                full_name = f"{object.__getattribute__(self, '_full_name')}.{name}"
                submodule_cache[name] = LazySubmodule(full_name, self, name)
            return submodule_cache[name]
        
        return attr
    
    def __dir__(self) -> List[str]:
        module = self._get_module()
        return dir(module)
    
    def __repr__(self) -> str:
        full_name = object.__getattribute__(self, '_full_name')
        cached = object.__getattribute__(self, '_cached_module')
        if cached is not None:
            return f"<LazySubmodule '{full_name}' (loaded)>"
        return f"<LazySubmodule '{full_name}' (not loaded)>"
    
    def __call__(self, *args, **kwargs) -> Any:
        module = self._get_module()
        if callable(module):
            return module(*args, **kwargs)
        raise TypeError(f"'{type(module).__name__}' object is not callable")


def _get_lazy_module(alias: str) -> LazyModule:
    """Get or create a LazyModule proxy"""
    if alias not in _LAZY_MODULES:
        module_name = _ALIAS_MAP.get(alias, alias)
        _LAZY_MODULES[alias] = LazyModule(alias, module_name)
    return _LAZY_MODULES[alias]


# ============== Configuration API ==============

def get_config_paths() -> List[str]:
    """
    Get all configuration file paths in priority order.
    
    Returns:
        List of configuration file paths as strings
    """
    return [str(p) for p in _get_config_paths()]


def reload_aliases() -> None:
    """
    Reload aliases from all configuration files.
    
    This will:
    1. Reload all config files
    2. Rebuild the alias map
    3. Update the global namespace
    
    Call this after modifying config files to apply changes.
    """
    global _ALIAS_MAP
    
    _ALIAS_MAP = _load_all_aliases()
    _rebuild_global_namespace()


def export_aliases(path: Optional[str] = None, include_categories: bool = True) -> str:
    """
    Export current aliases to a JSON file.
    
    Args:
        path: Output file path. If None, returns JSON string.
        include_categories: If True, organize aliases by category.
        
    Returns:
        Path to exported file, or JSON string if path is None
        
    Example:
        >>> export_aliases("my_aliases.json")
        'my_aliases.json'
        >>> export_aliases()
        '{"data_science": {"np": "numpy", ...}}'
    """
    if include_categories:
        # Load default config to get category structure
        default_path = _Path_class(__file__).parent / "aliases.json"
        if default_path.exists():
            with open(default_path, encoding="utf-8") as f:
                data = _json_module.load(f)
            # Update with current aliases
            for category in data:
                for alias in list(data[category].keys()):
                    if alias in _ALIAS_MAP:
                        data[category][alias] = _ALIAS_MAP[alias]
                    else:
                        del data[category][alias]
            # Add any new aliases to a "custom" category
            known_aliases = set()
            for cat in data.values():
                known_aliases.update(cat.keys())
            new_aliases = {k: v for k, v in _ALIAS_MAP.items() if k not in known_aliases}
            if new_aliases:
                data["custom"] = new_aliases
        else:
            data = {"aliases": dict(_ALIAS_MAP)}
    else:
        data = dict(_ALIAS_MAP)
    
    json_str = _json_module.dumps(data, indent=2, ensure_ascii=False)
    
    if path:
        output_path = _Path_class(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        return str(output_path)
    
    return json_str


def validate_aliases(aliases: Optional[Dict[str, str]] = None) -> Dict[str, List[str]]:
    """
    Validate alias entries.
    
    Args:
        aliases: Aliases to validate. If None, validates current aliases.
        
    Returns:
        Dictionary with 'valid' and 'invalid' lists of alias names
        
    Example:
        >>> result = validate_aliases()
        >>> print(result['invalid'])
        ['bad-alias']  # Not a valid identifier
    """
    to_validate = aliases if aliases is not None else _ALIAS_MAP
    
    valid: List[str] = []
    invalid: List[str] = []
    
    for alias, module_name in to_validate.items():
        if _validate_alias(alias, module_name):
            valid.append(alias)
        else:
            invalid.append(alias)
    
    return {"valid": valid, "invalid": invalid}


# ============== Auto-search API ==============

def enable_auto_search() -> None:
    """
    Enable auto-search functionality.
    
    When enabled, accessing unregistered names will automatically search for matching modules.
    """
    global _AUTO_SEARCH_ENABLED
    _AUTO_SEARCH_ENABLED = True


def disable_auto_search() -> None:
    """
    Disable auto-search functionality.
    
    When disabled, only predefined alias mappings will be used.
    """
    global _AUTO_SEARCH_ENABLED
    _AUTO_SEARCH_ENABLED = False


def is_auto_search_enabled() -> bool:
    """
    Check if auto-search is enabled.
    
    Returns:
        True if auto-search is enabled
    """
    return _AUTO_SEARCH_ENABLED


def search_module(name: str) -> Optional[str]:
    """
    Search for a matching module name.
    
    Args:
        name: Name to search for
        
    Returns:
        Found module name, or None if not found
        
    Example:
        >>> search_module("flask")
        'flask'
        >>> search_module("DataFrame")
        None
    """
    return _search_module(name)


def search_class(class_name: str) -> Optional[Tuple[str, Any]]:
    """
    Search for a class in loaded modules.
    
    Args:
        class_name: Class name to search for
        
    Returns:
        Tuple of (module_name, class_object), or None if not found
        
    Example:
        >>> result = search_class("DataFrame")
        >>> if result:
        ...     mod_name, cls = result
        ...     print(f"Found in {mod_name}")
        Found in pandas
    """
    return _search_class_in_modules(class_name)


def rebuild_module_cache() -> None:
    """
    Rebuild the module cache.
    
    Call this function after installing new packages to update the module list.
    """
    global _KNOWN_MODULES_CACHE, _KNOWN_MODULES_CACHE_TIME
    _KNOWN_MODULES_CACHE = None
    _KNOWN_MODULES_CACHE_TIME = 0.0
    _build_known_modules_cache(force=True)


# ============== Alias Management API ==============

def register_alias(alias: str, module_name: str) -> None:
    """
    Register a custom module alias.
    
    Args:
        alias: Alias name (e.g., "mylib")
        module_name: Actual module name (e.g., "my_awesome_library")
    
    Example:
        register_alias("mylib", "my_awesome_library")
        # Now you can use mylib.xxx directly
    """
    if not _validate_alias(alias, module_name):
        raise ValueError(f"Invalid alias: '{alias}' -> '{module_name}'")
    
    _ALIAS_MAP[alias] = module_name
    # Create new LazyModule proxy (access via __getattr__ instead of globals())
    _LAZY_MODULES[alias] = LazyModule(alias, module_name)


def register_aliases(aliases: Dict[str, str]) -> List[str]:
    """
    Register multiple module aliases at once.
    
    Args:
        aliases: Dictionary mapping alias names to module names
        
    Returns:
        List of successfully registered aliases
        
    Example:
        register_aliases({"np": "numpy", "pd": "pandas", "plt": "matplotlib.pyplot"})
    """
    registered = []
    for alias, module_name in aliases.items():
        try:
            register_alias(alias, module_name)
            registered.append(alias)
        except ValueError as e:
            if _DEBUG_MODE:
                _logging_module.warning(f"Failed to register alias '{alias}': {e}")
    return registered


def unregister_alias(alias: str) -> bool:
    """
    Remove a registered alias.
    
    Args:
        alias: Alias to remove
        
    Returns:
        True if alias existed and was removed, False otherwise
    """
    if alias in _ALIAS_MAP:
        del _ALIAS_MAP[alias]
        if alias in _LAZY_MODULES:
            del _LAZY_MODULES[alias]
        return True
    return False


def list_loaded() -> List[str]:
    """
    Return list of loaded module aliases.
    
    Returns:
        List of aliases for loaded modules
    """
    loaded = []
    for alias, lazy_mod in _LAZY_MODULES.items():
        # Check if actually loaded
        if object.__getattribute__(lazy_mod, '_cached_module') is not None:
            loaded.append(alias)
    return loaded


def list_available() -> List[str]:
    """
    Return list of all available module aliases (registered but not necessarily loaded).
    
    Returns:
        List of all registered aliases
    """
    return list(_ALIAS_MAP.keys())


def get_module(alias: str) -> Optional[Any]:
    """
    Get a loaded module object.
    
    Args:
        alias: Module alias
        
    Returns:
        Module object, or None if not loaded
    """
    if alias in _LAZY_MODULES:
        lazy_mod = _LAZY_MODULES[alias]
        cached = object.__getattribute__(lazy_mod, '_cached_module')
        if cached is not None:
            return cached
    return None


def clear_cache() -> None:
    """
    Clear the loaded module cache.
    
    Note: This does not actually unload modules, only clears cache references.
    Next access will re-import (but Python's module cache still applies).
    """
    for lazy_mod in _LAZY_MODULES.values():
        object.__setattr__(lazy_mod, '_cached_module', None)


# ============== Version & Reload API ==============

def get_version(alias: str) -> Optional[str]:
    """
    Get the version of a loaded module.
    
    Args:
        alias: Module alias
        
    Returns:
        Version string, or None if not loaded or no version info
        
    Example:
        >>> get_version("np")
        '1.24.0'
    """
    module = get_module(alias)
    if module is None:
        return None
    
    # Try common version attributes
    for attr in ('__version__', 'VERSION', 'version'):
        if hasattr(module, attr):
            ver = getattr(module, attr)
            if isinstance(ver, str):
                return ver
            elif isinstance(ver, tuple):
                return '.'.join(map(str, ver))
    return None


def reload_module(alias: str) -> bool:
    """
    Reload a loaded module.
    
    Args:
        alias: Module alias to reload
        
    Returns:
        True if reload was successful, False otherwise
        
    Example:
        >>> reload_module("np")
        True
    """
    if alias not in _LAZY_MODULES:
        return False
    
    lazy_mod = _LAZY_MODULES[alias]
    cached = object.__getattribute__(lazy_mod, '_cached_module')
    
    if cached is None:
        return False
    
    module_name = object.__getattribute__(lazy_mod, '_module_name')
    
    try:
        # Reload the module
        reloaded = _importlib_module.reload(cached)
        object.__setattr__(lazy_mod, '_cached_module', reloaded)
        
        if _DEBUG_MODE:
            _logging_module.info(f"[laziest-import] Reloaded module '{module_name}'")
        
        return True
    except Exception as e:
        if _DEBUG_MODE:
            _logging_module.warning(f"Failed to reload module '{module_name}': {e}")
        return False


# ============== Debug & Statistics API ==============

def enable_debug_mode() -> None:
    """
    Enable debug mode for detailed logging of import operations.
    """
    global _DEBUG_MODE
    _DEBUG_MODE = True
    _logging_module.basicConfig(level=_logging_module.DEBUG)


def disable_debug_mode() -> None:
    """
    Disable debug mode.
    """
    global _DEBUG_MODE
    _DEBUG_MODE = False


def is_debug_mode() -> bool:
    """
    Check if debug mode is enabled.
    
    Returns:
        True if debug mode is enabled
    """
    return _DEBUG_MODE


def get_import_stats() -> Dict[str, Any]:
    """
    Get import statistics.
    
    Returns:
        Dictionary containing:
        - total_imports: Total number of imports
        - total_time: Total time spent importing (seconds)
        - average_time: Average time per import
        - module_times: Time spent per module
        - module_access_counts: Number of times each module was accessed
        
    Example:
        >>> stats = get_import_stats()
        >>> print(stats['total_imports'])
        5
    """
    avg_time = (_IMPORT_STATS.total_time / _IMPORT_STATS.total_imports 
                if _IMPORT_STATS.total_imports > 0 else 0)
    return {
        "total_imports": _IMPORT_STATS.total_imports,
        "total_time": _IMPORT_STATS.total_time,
        "average_time": avg_time,
        "module_times": dict(_IMPORT_STATS.module_times),
        "module_access_counts": dict(_IMPORT_STATS.module_access_counts),
    }


def reset_import_stats() -> None:
    """
    Reset import statistics.
    """
    global _IMPORT_STATS
    _IMPORT_STATS = ImportStats()


# ============== Import Hooks API ==============

def add_pre_import_hook(hook: Callable[[str], None]) -> None:
    """
    Add a hook to be called before a module is imported.
    
    Args:
        hook: Callable that takes the module name as argument
        
    Example:
        def my_hook(module_name):
            print(f"About to import {module_name}")
        add_pre_import_hook(my_hook)
    """
    _PRE_IMPORT_HOOKS.append(hook)


def add_post_import_hook(hook: Callable[[str, Any], None]) -> None:
    """
    Add a hook to be called after a module is imported.
    
    Args:
        hook: Callable that takes (module_name, module_object) as arguments
        
    Example:
        def my_hook(module_name, module):
            print(f"Imported {module_name} v{getattr(module, '__version__', 'unknown')}")
        add_post_import_hook(my_hook)
    """
    _POST_IMPORT_HOOKS.append(hook)


def remove_pre_import_hook(hook: Callable[[str], None]) -> bool:
    """
    Remove a pre-import hook.
    
    Args:
        hook: The hook to remove
        
    Returns:
        True if hook was found and removed
    """
    if hook in _PRE_IMPORT_HOOKS:
        _PRE_IMPORT_HOOKS.remove(hook)
        return True
    return False


def remove_post_import_hook(hook: Callable[[str, Any], None]) -> bool:
    """
    Remove a post-import hook.
    
    Args:
        hook: The hook to remove
        
    Returns:
        True if hook was found and removed
    """
    if hook in _POST_IMPORT_HOOKS:
        _POST_IMPORT_HOOKS.remove(hook)
        return True
    return False


def clear_import_hooks() -> None:
    """
    Remove all import hooks.
    """
    _PRE_IMPORT_HOOKS.clear()
    _POST_IMPORT_HOOKS.clear()


# ============== Async Import API ==============

async def import_async(alias: str) -> Any:
    """
    Asynchronously import a module.
    
    Useful for importing large modules without blocking the event loop.
    
    Args:
        alias: Module alias to import
        
    Returns:
        The imported module object
        
    Example:
        module = await import_async("torch")
    """
    loop = _asyncio_module.get_event_loop()
    
    def _sync_import():
        if alias in _LAZY_MODULES:
            return _LAZY_MODULES[alias]._get_module()
        
        module_name = _ALIAS_MAP.get(alias, alias)
        try:
            return _importlib_module.import_module(module_name)
        except ImportError:
            found = _search_module(alias)
            if found:
                return _importlib_module.import_module(found)
            raise
    
    return await loop.run_in_executor(None, _sync_import)


async def import_multiple_async(aliases: List[str]) -> Dict[str, Any]:
    """
    Asynchronously import multiple modules in parallel.
    
    Args:
        aliases: List of module aliases to import
        
    Returns:
        Dictionary mapping alias to module object
        
    Example:
        modules = await import_multiple_async(["numpy", "pandas", "matplotlib"])
    """
    tasks = [import_async(alias) for alias in aliases]
    results = await _asyncio_module.gather(*tasks, return_exceptions=True)
    
    modules = {}
    for alias, result in zip(aliases, results):
        if isinstance(result, Exception):
            if _DEBUG_MODE:
                _logging_module.warning(f"Failed to import {alias}: {result}")
        else:
            modules[alias] = result
    
    return modules


# ============== Retry Configuration API ==============

def enable_retry(max_retries: int = 3, retry_delay: float = 0.5, 
                 modules: Optional[Set[str]] = None) -> None:
    """
    Enable automatic retry for module imports.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        modules: Set of module names to retry. If None, retry all modules.
        
    Example:
        enable_retry(max_retries=3, retry_delay=1.0)
    """
    _RETRY_CONFIG["enabled"] = True
    _RETRY_CONFIG["max_retries"] = max_retries
    _RETRY_CONFIG["retry_delay"] = retry_delay
    _RETRY_CONFIG["retry_modules"] = modules if modules else set()


def disable_retry() -> None:
    """
    Disable automatic retry for module imports.
    """
    _RETRY_CONFIG["enabled"] = False


def is_retry_enabled() -> bool:
    """
    Check if retry is enabled.
    
    Returns:
        True if retry is enabled
    """
    return _RETRY_CONFIG["enabled"]


# ============== Auto Install API ==============

def _get_pip_package_name(module_name: str) -> str:
    """
    Get the pip package name for a module name.
    
    Many Python packages have different import names vs pip names.
    This function maps common cases.
    
    Args:
        module_name: The import module name
        
    Returns:
        The pip package name
    """
    # Common mappings: import name -> pip package name
    rename_map = _get_package_rename_map()
    
    # Check direct mapping
    if module_name in rename_map:
        return rename_map[module_name]
    
    # Check without submodule path
    base_module = module_name.split('.')[0]
    if base_module in rename_map:
        return rename_map[base_module]
    
    # Default: assume module name = package name
    return base_module


def _check_uv_available() -> bool:
    """
    Check if uv is available in the system.
    
    Returns:
        True if uv is installed and available
    """
    import shutil as _shutil
    return _shutil.which('uv') is not None


def _install_package_sync(package_name: str, index: Optional[str] = None, 
                          extra_args: Optional[List[str]] = None,
                          prefer_uv: bool = False, silent: bool = False) -> Tuple[bool, str]:
    """
    Install a package using pip or uv.
    
    Args:
        package_name: Name of the package to install
        index: Optional custom PyPI mirror URL
        extra_args: Additional arguments for pip/uv
        prefer_uv: Prefer uv over pip if available
        silent: Suppress output
        
    Returns:
        Tuple of (success, message)
    """
    import subprocess as _subprocess_module
    import shutil as _shutil_module
    
    # Build command
    use_uv = prefer_uv and _check_uv_available()
    
    if use_uv:
        uv_path = _shutil_module.which('uv')
        if uv_path is None:
            # Fallback to pip if uv not found (shouldn't happen if _check_uv_available returned True)
            use_uv = False
            cmd = [_sys_module.executable, '-m', 'pip', 'install', package_name]
        else:
            cmd = [uv_path, 'pip', 'install', package_name]
    else:
        cmd = [_sys_module.executable, '-m', 'pip', 'install', package_name]
    
    # Add index URL if specified
    if index:
        cmd.extend(['--index-url', index])
    
    # Add extra arguments
    if extra_args:
        cmd.extend(extra_args)
    
    # Add quiet flag if silent
    if silent:
        cmd.append('-q')
    
    try:
        result = _subprocess_module.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return True, result.stdout or f"Successfully installed {package_name}"
        else:
            return False, result.stderr or f"Failed to install {package_name}"
            
    except _subprocess_module.TimeoutExpired:
        return False, f"Installation of {package_name} timed out"
    except FileNotFoundError as e:
        return False, f"Package manager not found: {e}"
    except Exception as e:
        return False, f"Installation failed: {e}"


def _interactive_install_confirm(module_name: str, package_name: str) -> bool:
    """
    Ask user for confirmation before installing a package.
    
    Args:
        module_name: The module name that was requested
        package_name: The package that will be installed
        
    Returns:
        True if user confirms, False otherwise
    """
    if not _AUTO_INSTALL_CONFIG["interactive"]:
        return True
    
    print(f"\n[laziest-import] Module '{module_name}' is not installed.")
    print(f"  Package to install: {package_name}")
    print("-" * 50)
    
    try:
        response = input("Install now? [Y/n]: ").strip().lower()
        return response in ('', 'y', 'yes')
    except (EOFError, KeyboardInterrupt):
        print("\nInstallation cancelled.")
        return False


def install_package(package_name: str, index: Optional[str] = None,
                    extra_args: Optional[List[str]] = None,
                    interactive: Optional[bool] = None) -> bool:
    """
    Install a package manually.
    
    Args:
        package_name: Name of the package to install (pip name)
        index: Optional custom PyPI mirror URL
        extra_args: Additional arguments for pip
        interactive: Override interactive setting. None = use config.
        
    Returns:
        True if installation succeeded
        
    Example:
        >>> install_package("pandas")
        >>> install_package("torch", index="https://download.pytorch.org/whl/cpu")
    """
    # Use config values for unspecified parameters
    if index is None:
        index = _AUTO_INSTALL_CONFIG["index"]
    if extra_args is None:
        extra_args = _AUTO_INSTALL_CONFIG["extra_args"]
    if interactive is None:
        interactive = _AUTO_INSTALL_CONFIG["interactive"]
    
    # Confirm if interactive
    if interactive:
        if not _interactive_install_confirm(package_name, package_name):
            return False
    
    # Install
    success, message = _install_package_sync(
        package_name,
        index=index,
        extra_args=extra_args,
        prefer_uv=_AUTO_INSTALL_CONFIG["prefer_uv"],
        silent=_AUTO_INSTALL_CONFIG["silent"]
    )
    
    if success:
        if _DEBUG_MODE:
            _logging_module.info(f"[laziest-import] {message}")
        # Rebuild module cache to include newly installed package
        rebuild_module_cache()
        return True
    else:
        _logging_module.warning(f"[laziest-import] {message}")
        return False


def enable_auto_install(
    interactive: bool = True,
    index: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    prefer_uv: bool = False,
    silent: bool = False
) -> None:
    """
    Enable automatic installation of missing packages.
    
    When enabled, attempting to use a module that is not installed
    will automatically install it (with optional confirmation).
    
    WARNING: This feature installs packages automatically. Use with caution
    in production environments.
    
    Args:
        interactive: Ask for confirmation before installing (default: True)
        index: Custom PyPI mirror URL (e.g., Tsinghua mirror for China)
        extra_args: Additional arguments for pip install
        prefer_uv: Prefer uv over pip if available (faster)
        silent: Suppress pip output
        
    Example:
        >>> enable_auto_install()  # Interactive mode (asks before installing)
        >>> enable_auto_install(interactive=False)  # Auto-install without asking
        >>> enable_auto_install(index="https://pypi.tuna.tsinghua.edu.cn/simple")  # China mirror
    """
    global _AUTO_INSTALL_CONFIG
    
    _AUTO_INSTALL_CONFIG["enabled"] = True
    _AUTO_INSTALL_CONFIG["interactive"] = interactive
    _AUTO_INSTALL_CONFIG["index"] = index
    _AUTO_INSTALL_CONFIG["extra_args"] = extra_args or []
    _AUTO_INSTALL_CONFIG["prefer_uv"] = prefer_uv
    _AUTO_INSTALL_CONFIG["silent"] = silent


def disable_auto_install() -> None:
    """
    Disable automatic installation of missing packages.
    """
    _AUTO_INSTALL_CONFIG["enabled"] = False


def is_auto_install_enabled() -> bool:
    """
    Check if automatic installation is enabled.
    
    Returns:
        True if auto-install is enabled
    """
    return _AUTO_INSTALL_CONFIG["enabled"]


def get_auto_install_config() -> Dict[str, Any]:
    """
    Get current auto-install configuration.
    
    Returns:
        Dictionary of configuration options
    """
    return dict(_AUTO_INSTALL_CONFIG)


def set_pip_index(url: Optional[str]) -> None:
    """
    Set custom PyPI mirror index URL.
    
    Args:
        url: PyPI mirror URL, or None to use default
        
    Example:
        >>> set_pip_index("https://pypi.tuna.tsinghua.edu.cn/simple")  # Tsinghua (China)
        >>> set_pip_index("https://mirrors.aliyun.com/pypi/simple")  # Aliyun (China)
        >>> set_pip_index(None)  # Reset to default
    """
    _AUTO_INSTALL_CONFIG["index"] = url


def set_pip_extra_args(args: List[str]) -> None:
    """
    Set extra arguments for pip install.
    
    Args:
        args: List of extra arguments
        
    Example:
        >>> set_pip_extra_args(["--no-cache-dir", "--force-reinstall"])
    """
    _AUTO_INSTALL_CONFIG["extra_args"] = args


# ============== Enhanced Validation API ==============

def validate_aliases_importable(aliases: Optional[Dict[str, str]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Validate that aliases can actually be imported.
    
    Args:
        aliases: Aliases to validate. If None, validates current aliases.
        
    Returns:
        Dictionary with 'importable' and 'not_importable' results
        
    Example:
        >>> result = validate_aliases_importable()
        >>> print(result['not_importable'])
        {'bad_alias': {'module': 'nonexistent', 'error': 'No module named ...'}}
    """
    to_validate = aliases if aliases is not None else _ALIAS_MAP
    
    importable: Dict[str, Dict[str, Any]] = {}
    not_importable: Dict[str, Dict[str, Any]] = {}
    
    for alias, module_name in to_validate.items():
        try:
            spec = _importlib_module.util.find_spec(module_name)
            if spec is not None:
                importable[alias] = {"module": module_name, "spec": spec}
            else:
                not_importable[alias] = {"module": module_name, "error": "Module not found"}
        except (ImportError, ModuleNotFoundError, ValueError) as e:
            not_importable[alias] = {"module": module_name, "error": str(e)}
    
    return {"importable": importable, "not_importable": not_importable}


# ============== File Cache API ==============

def enable_file_cache() -> None:
    """
    Enable file-level caching for faster subsequent imports.
    
    When enabled, the library caches which modules were loaded for each
    Python file, and preloads them in the background on subsequent runs.
    """
    global _FILE_CACHE_ENABLED
    _FILE_CACHE_ENABLED = True


def disable_file_cache() -> None:
    """
    Disable file-level caching.
    """
    global _FILE_CACHE_ENABLED
    _FILE_CACHE_ENABLED = False


def is_file_cache_enabled() -> bool:
    """
    Check if file-level caching is enabled.
    
    Returns:
        True if file cache is enabled
    """
    return _FILE_CACHE_ENABLED


def clear_file_cache(file_path: Optional[str] = None) -> int:
    """
    Clear file cache(s).
    
    Args:
        file_path: Specific file to clear cache for. If None, clears all caches.
        
    Returns:
        Number of cache files removed
        
    Example:
        >>> clear_file_cache()  # Clear all caches
        5
        >>> clear_file_cache("my_script.py")  # Clear specific file cache
        1
    """
    removed = 0
    
    if file_path:
        cache_file = _get_cache_file_path(file_path)
        if cache_file.exists():
            cache_file.unlink()
            removed = 1
    else:
        # Clear all caches
        cache_dir = _get_cache_dir()
        for cache_file in cache_dir.glob("*.json"):
            cache_file.unlink()
            removed += 1
    
    return removed


def get_file_cache_info() -> Dict[str, Any]:
    """
    Get information about the current file cache.
    
    Returns:
        Dictionary containing:
        - enabled: Whether file cache is enabled
        - caller_file: Current caller file path (if detected)
        - cached_modules: List of modules loaded for current file
        - cache_dir: Cache directory path
        - cache_size: Total number of cached files
        - cache_size_bytes: Total size of cache in bytes
        - max_cache_size_mb: Maximum allowed cache size in MB
        
    Example:
        >>> info = get_file_cache_info()
        >>> print(info['cached_modules'])
        ['os', 'sys', 'json']
    """
    cache_dir = _get_cache_dir()
    cache_files = list(cache_dir.glob("*.json"))
    cache_size_bytes = _get_cache_size()
    
    return {
        "enabled": _FILE_CACHE_ENABLED,
        "caller_file": _CALLER_FILE_PATH,
        "cached_modules": list(_CALLER_LOADED_MODULES),
        "cache_dir": str(cache_dir),
        "cache_size": len(cache_files),
        "cache_size_bytes": cache_size_bytes,
        "cache_size_mb": round(cache_size_bytes / (1024 * 1024), 2),
        "max_cache_size_mb": _CACHE_CONFIG.get("max_cache_size_mb", 100),
    }


def force_save_cache() -> bool:
    """
    Force save the current file cache immediately.
    
    Normally, cache is saved automatically at program exit.
    Use this to save manually if needed.
    
    Returns:
        True if saved successfully
    """
    _save_current_cache()
    return True


# List of reserved public API names that should not be treated as modules
_RESERVED_NAMES: Set[str] = {
    "__version__",
    "register_alias", "register_aliases", "unregister_alias",
    "list_loaded", "list_available", "get_module", "clear_cache",
    "get_version", "reload_module",
    "enable_auto_search", "disable_auto_search", "is_auto_search_enabled",
    "search_module", "search_class", "rebuild_module_cache",
    "reload_aliases", "export_aliases", "validate_aliases", "validate_aliases_importable",
    "get_config_paths",
    "enable_debug_mode", "disable_debug_mode", "is_debug_mode",
    "get_import_stats", "reset_import_stats",
    "add_pre_import_hook", "add_post_import_hook",
    "remove_pre_import_hook", "remove_post_import_hook", "clear_import_hooks",
    "import_async", "import_multiple_async",
    "enable_retry", "disable_retry", "is_retry_enabled",
    "enable_file_cache", "disable_file_cache", "is_file_cache_enabled",
    "clear_file_cache", "get_file_cache_info", "force_save_cache",
    "set_cache_dir", "get_cache_dir", "reset_cache_dir",
    # Symbol search
    "enable_symbol_search", "disable_symbol_search", "is_symbol_search_enabled",
    "search_symbol", "rebuild_symbol_index", "get_symbol_search_config",
    "get_symbol_cache_info", "clear_symbol_cache",
    # Auto install
    "enable_auto_install", "disable_auto_install", "is_auto_install_enabled",
    "install_package", "get_auto_install_config",
    "set_pip_index", "set_pip_extra_args",
    # Enhanced cache API
    "set_cache_config", "get_cache_config", "get_cache_stats", "reset_cache_stats",
    "invalidate_package_cache", "get_cache_version",
}


def __getattr__(name: str) -> LazyModule:
    """
    Module-level attribute access hook for lazy loading.
    
    Called when accessing laziest_import.xxx or from laziest_import import xxx
    where xxx is not defined.
    """
    global _INITIALIZING, _INITIALIZED
    
    # Prevent recursion during initialization
    if _INITIALIZING and not _INITIALIZED:
        raise AttributeError(
            f"module '{__name__}' is still initializing, cannot access '{name}' yet. "
            f"This is likely caused by a circular import."
        )
    
    # If it's a reserved name, raise AttributeError (shouldn't happen if defined correctly)
    if name in _RESERVED_NAMES:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    # If it's in the alias map, return LazyModule
    if name in _ALIAS_MAP:
        return _get_lazy_module(name)
    
    # If auto-search is enabled, try to find the module
    if _AUTO_SEARCH_ENABLED:
        found = _search_module(name)
        if found:
            # Add to alias map for future use
            _ALIAS_MAP[name] = found
            return _get_lazy_module(name)
    
    # Symbol search: try to find class/function in installed packages
    # Skip symbol search during initialization to prevent recursion
    if _SYMBOL_SEARCH_CONFIG["enabled"] and _INITIALIZED:
        found_module = _handle_symbol_not_found(name)
        if found_module:
            # _handle_symbol_not_found already registered the alias
            return _get_lazy_module(name)
    
    # Not found, raise AttributeError with helpful message
    available = list(_ALIAS_MAP.keys())[:10]
    msg = f"module '{__name__}' has no attribute '{name}'."
    if available:
        msg += f" Available modules: {available}... (use list_available() to see all)"
    if _SYMBOL_SEARCH_CONFIG["enabled"] and _INITIALIZED:
        msg += f"\nTip: Use search_symbol('{name}') to search for classes/functions in installed packages."
    raise AttributeError(msg)


def __dir__() -> List[str]:
    """
    Return list of public module attributes for tab completion.
    """
    result = list(_ALIAS_MAP.keys())
    result.extend([
        "__version__",
        # Alias management
        "register_alias",
        "register_aliases",
        "unregister_alias", 
        "list_loaded",
        "list_available",
        "get_module",
        "clear_cache",
        # Version & reload
        "get_version",
        "reload_module",
        # Auto-search
        "enable_auto_search",
        "disable_auto_search",
        "is_auto_search_enabled",
        "search_module",
        "search_class",
        "rebuild_module_cache",
        "reload_aliases",
        "export_aliases",
        "validate_aliases",
        "validate_aliases_importable",
        "get_config_paths",
        # Debug & statistics
        "enable_debug_mode",
        "disable_debug_mode",
        "is_debug_mode",
        "get_import_stats",
        "reset_import_stats",
        # Import hooks
        "add_pre_import_hook",
        "add_post_import_hook",
        "remove_pre_import_hook",
        "remove_post_import_hook",
        "clear_import_hooks",
        # Async import
        "import_async",
        "import_multiple_async",
        # Retry configuration
        "enable_retry",
        "disable_retry",
        "is_retry_enabled",
        # File cache
        "enable_file_cache",
        "disable_file_cache",
        "is_file_cache_enabled",
        "clear_file_cache",
        "get_file_cache_info",
        "force_save_cache",
        "set_cache_dir",
        "get_cache_dir",
        "reset_cache_dir",
        # Symbol search
        "enable_symbol_search",
        "disable_symbol_search",
        "is_symbol_search_enabled",
        "search_symbol",
        "rebuild_symbol_index",
        "get_symbol_search_config",
        "get_symbol_cache_info",
        "clear_symbol_cache",
        # Auto install
        "enable_auto_install",
        "disable_auto_install",
        "is_auto_install_enabled",
        "install_package",
        "get_auto_install_config",
        "set_pip_index",
        "set_pip_extra_args",
        # Enhanced cache API
        "set_cache_config",
        "get_cache_config",
        "get_cache_stats",
        "reset_cache_stats",
        "invalidate_package_cache",
        "get_cache_version",
    ])
    return sorted(result)


# ============== Initialization ==============

def _do_initialize() -> None:
    """
    Perform module initialization with protection against recursion.
    """
    global _INITIALIZING, _INITIALIZED, _ALIAS_MAP
    
    # Use lock for thread safety
    lock = _get_init_lock()
    with lock:
        # Double-check pattern after acquiring lock
        # Check _INITIALIZING first, then _INITIALIZED (more logical order)
        if _INITIALIZING:
            return
        if _INITIALIZED:
            return
        
        _INITIALIZING = True
        
        try:
            # Load aliases from config files FIRST, before any other operation
            _ALIAS_MAP.update(_load_all_aliases())
            
            # Create LazyModule proxies for all aliases
            _rebuild_global_namespace()
            
            # Mark as initialized BEFORE file cache init
            # (file cache init might trigger module access)
            _INITIALIZED = True
            
            # Initialize file cache for the caller (safe now that we're initialized)
            _init_file_cache()
            
        finally:
            _INITIALIZING = False


# Initialize _ALIAS_MAP as empty dict first
_ALIAS_MAP: Dict[str, str] = {}

# Perform initialization
_do_initialize()

# Dynamically generate __all__, including all registered aliases and public API
__all__: List[str] = list(_ALIAS_MAP.keys()) + [
    "__version__",
    # Alias management
    "register_alias",
    "register_aliases",
    "unregister_alias",
    "list_loaded", 
    "list_available",
    "get_module",
    "clear_cache",
    # Version & reload
    "get_version",
    "reload_module",
    # Auto-search
    "enable_auto_search",
    "disable_auto_search",
    "is_auto_search_enabled",
    "search_module",
    "search_class",
    "rebuild_module_cache",
    "reload_aliases",
    "export_aliases",
    "validate_aliases",
    "validate_aliases_importable",
    "get_config_paths",
    # Debug & statistics
    "enable_debug_mode",
    "disable_debug_mode",
    "is_debug_mode",
    "get_import_stats",
    "reset_import_stats",
    # Import hooks
    "add_pre_import_hook",
    "add_post_import_hook",
    "remove_pre_import_hook",
    "remove_post_import_hook",
    "clear_import_hooks",
    # Async import
    "import_async",
    "import_multiple_async",
    # Retry configuration
    "enable_retry",
    "disable_retry",
    "is_retry_enabled",
    # File cache
    "enable_file_cache",
    "disable_file_cache",
    "is_file_cache_enabled",
    "clear_file_cache",
    "get_file_cache_info",
    "force_save_cache",
    "set_cache_dir",
    "get_cache_dir",
    "reset_cache_dir",
    # Symbol search
    "enable_symbol_search",
    "disable_symbol_search",
    "is_symbol_search_enabled",
    "search_symbol",
    "rebuild_symbol_index",
    "get_symbol_search_config",
    "get_symbol_cache_info",
    "clear_symbol_cache",
    # Auto install
    "enable_auto_install",
    "disable_auto_install",
    "is_auto_install_enabled",
    "install_package",
    "get_auto_install_config",
    "set_pip_index",
    "set_pip_extra_args",
    # Enhanced cache API
    "set_cache_config",
    "get_cache_config",
    "get_cache_stats",
    "reset_cache_stats",
    "invalidate_package_cache",
    "get_cache_version",
]




