"""
Centralized mutable state for laziest-import.

THIS MODULE IS THE SINGLE SOURCE OF TRUTH for all runtime state.
All state variables are defined here as module-level globals.
Other modules import from here: `from laziest_import._config import X`.
Because dicts/sets are shared by reference, in-place mutations are
visible to all importers automatically.

Setters (which do `mod.X = value` via sys.modules) live in _state_setters.py
to avoid circular imports.
"""

from typing import Dict, List, Optional, Set, Any, Tuple, Callable
from pathlib import Path
import json
import threading
import re
import sys
from dataclasses import dataclass, field


# ============================================================
# Version loading
# ============================================================

def _load_version_config() -> Dict[str, Any]:
    vf = Path(__file__).parent / "version.json"
    if not vf.exists():
        return {}
    try:
        with open(vf, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


_VERSION_CONFIG = _load_version_config()
__version__ = _VERSION_CONFIG.get("_current_version", "0.1.0-pre2")


def get_cache_version() -> str:
    return _VERSION_CONFIG.get("_cache_version", __version__)


def get_version_range(target: str) -> Tuple[Optional[str], Optional[str]]:
    c = _VERSION_CONFIG.get(target, {})
    return c.get("_min_version"), c.get("_max_version")


def _parse_version(v: str) -> Tuple[Tuple[int, ...], Optional[str]]:
    m = re.match(r"^(\d+(?:\.\d+)*)(?:-(.+))?$", v.strip())
    if not m:
        return ((0,), None)
    try:
        return tuple(int(x) for x in m.group(1).split(".")), m.group(2)
    except ValueError:
        return (0,), m.group(2)


def _compare_versions(v1: str, v2: str) -> int:
    n1, p1 = _parse_version(v1)
    n2, p2 = _parse_version(v2)
    ml = max(len(n1), len(n2))
    a, b = n1 + (0,) * (ml - len(n1)), n2 + (0,) * (ml - len(n2))
    if a < b:
        return -1
    elif a > b:
        return 1
    if p1 is None and p2 is None:
        return 0
    if p1 is None:
        return 1
    if p2 is None:
        return -1
    if p1 < p2:
        return -1
    elif p1 > p2:
        return 1
    return 0


def check_version_range(
    min_version: Optional[str],
    max_version: Optional[str],
    current_version: str = __version__,
    file_path: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    wl = []
    if min_version is not None and _compare_versions(current_version, min_version) < 0:
        s = f"Version {current_version} is below minimum {min_version}"
        wl.append(f"{file_path}: {s}" if file_path else s)
    if max_version is not None and _compare_versions(current_version, max_version) > 0:
        s = f"Version {current_version} is above maximum {max_version}"
        wl.append(f"{file_path}: {s}" if file_path else s)
    return (False, "; ".join(wl)) if wl else (True, None)


# ============================================================
# Dataclasses (imported widely)
# ============================================================

@dataclass
class ImportStats:
    total_imports: int = 0
    total_time: float = 0.0
    module_times: Dict[str, float] = field(default_factory=dict)
    module_access_counts: Dict[str, int] = field(default_factory=dict)


@dataclass
class SearchResult:
    module_name: str
    symbol_name: str
    symbol_type: str  # 'class', 'function', 'callable'
    signature: Optional[str]
    score: float
    obj: Optional[Any] = None


@dataclass
class SymbolMatch:
    module_name: str
    symbol_name: str
    symbol_type: str
    signature: Optional[str]
    confidence: float
    source: str  # 'exact', 'user_pref', 'context', 'priority', 'fuzzy', 'misspelling'
    obj: Optional[Any] = None


# ============================================================
# Init state
# ============================================================

_INIT_LOCK: threading.RLock = threading.RLock()
_INITIALIZING: bool = False
_INITIALIZED: bool = False
_INIT_FAILED: bool = False
_INIT_ERROR: Optional[str] = None


def get_init_lock() -> threading.RLock:
    return _INIT_LOCK


def get_init_state() -> Dict[str, Any]:
    return {
        "initializing": _INITIALIZING,
        "initialized": _INITIALIZED,
        "failed": _INIT_FAILED,
        "error": _INIT_ERROR,
    }


def is_initializing() -> bool:
    return _INITIALIZING


def is_initialized() -> bool:
    return _INITIALIZED


def is_init_failed() -> bool:
    return _INIT_FAILED


def get_init_error() -> Optional[str]:
    return _INIT_ERROR


def reset_init_state() -> None:
    global _INITIALIZING, _INITIALIZED, _INIT_FAILED, _INIT_ERROR
    _INITIALIZING = False
    _INITIALIZED = False
    _INIT_FAILED = False
    _INIT_ERROR = None


# ============================================================
# Core config
# ============================================================

_AUTO_SEARCH_ENABLED: bool = True
_DEBUG_MODE: bool = False
_FILE_CACHE_ENABLED: bool = True

# Known modules cache
_KNOWN_MODULES_CACHE: Optional[Set[str]] = None
_KNOWN_MODULES_CACHE_TIME: float = 0.0
_KNOWN_MODULES_CACHE_TTL: float = 300.0
_CLASS_TO_MODULE_CACHE: Dict[str, str] = {}

# Negative cache
_NEGATIVE_CACHE: Set[str] = set()
_NEGATIVE_CACHE_LOCK: threading.Lock = threading.Lock()

# Alias & module proxies
_ALIAS_MAP: Dict[str, str] = {}
_LAZY_MODULES: Dict[str, Any] = {}

# Thread-local import context
_IMPORT_CONTEXT = threading.local()
_IMPORT_CONTEXT_LOCK = threading.Lock()

# Stats
_IMPORT_STATS: ImportStats = ImportStats()
_CACHE_STATS: Dict[str, Any] = {
    "symbol_hits": 0, "symbol_misses": 0,
    "module_hits": 0, "module_misses": 0,
    "last_build_time": 0.0, "build_count": 0,
}

# Hooks
_PRE_IMPORT_HOOKS: List[Callable[[str], None]] = []
_POST_IMPORT_HOOKS: List[Callable[[str, Any], None]] = []

# Retry config
_RETRY_CONFIG: Dict[str, Any] = {
    "enabled": False, "max_retries": 3,
    "retry_delay": 0.5, "retry_modules": set(),
}

# Auto-install config
_AUTO_INSTALL_CONFIG: Dict[str, Any] = {
    "enabled": False, "interactive": True, "index": None,
    "extra_args": [], "prefer_uv": False, "silent": False,
}

# Symbol search config
_SYMBOL_SEARCH_CONFIG: Dict[str, Any] = {
    "enabled": True, "interactive": True, "exact_params": False,
    "max_results": 5, "search_depth": 1, "cache_enabled": True,
    "skip_private": True, "skip_stdlib": False,
}

# Symbol cache
_SYMBOL_CACHE: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}
_STDLIB_SYMBOL_CACHE: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}
_THIRD_PARTY_SYMBOL_CACHE: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}
_SYMBOL_INDEX_BUILT: bool = False
_STDLIB_CACHE_BUILT: bool = False
_THIRD_PARTY_CACHE_BUILT: bool = False

# Confirmed mappings
_CONFIRMED_MAPPINGS: Dict[str, str] = {}

# Symbol cache lock
_SYMBOL_CACHE_LOCK: threading.Lock = threading.Lock()

# Module priority
_MODULE_PRIORITY: Dict[str, int] = {}

# Symbol preferences
_SYMBOL_PREFERENCES: Dict[str, str] = {
    "DataFrame": "pandas", "Series": "pandas", "array": "numpy",
    "ndarray": "numpy", "Tensor": "torch", "read_csv": "pandas",
    "read_excel": "pandas", "read_json": "pandas", "concat": "pandas",
    "merge": "pandas", "figure": "matplotlib.pyplot", "subplot": "matplotlib.pyplot",
    "plot": "matplotlib.pyplot", "scatter": "matplotlib.pyplot",
    "hist": "matplotlib.pyplot", "imshow": "matplotlib.pyplot",
    "show": "matplotlib.pyplot", "savefig": "matplotlib.pyplot",
}

# Symbol resolution config
_SYMBOL_RESOLUTION_CONFIG: Dict[str, Any] = {
    "auto_symbol": True, "auto_threshold": 0.7, "conflict_threshold": 0.3,
    "symbol_misspelling": True, "context_aware": True,
    "warn_on_conflict": True, "save_preferences": True,
}

# Cache config
_CACHE_CONFIG: Dict[str, Any] = {
    "enabled": True, "max_size_mb": 100, "cleanup_threshold": 0.8,
    "file_cache_enabled": True, "symbol_index_enabled": True,
    "persist_across_sessions": True, "symbol_index_ttl": 86400,
    "stdlib_cache_ttl": 604800, "third_party_cache_ttl": 86400,
    "enable_compression": False, "max_cache_size_mb": 100,
}

# Incremental & background config
_INCREMENTAL_INDEX_CONFIG: Dict[str, Any] = {
    "enabled": True, "check_version": True, "check_mtime": False,
    "background_build": True, "background_timeout": 60.0,
}
_MODULE_SKIP_CONFIG: Dict[str, Any] = {
    "skip_test_modules": True, "skip_internal_modules": True,
    "skip_large_modules": True, "large_module_threshold": 100,
    "skip_modules_file": None,
}
_PREHEAT_CONFIG: Dict[str, Any] = {
    "enabled": True, "async_index_build": True,
    "preload_common_modules": True, "max_preload_threads": 4,
}

# Background index state
_BACKGROUND_INDEX_BUILDING: bool = False
_BACKGROUND_INDEX_THREAD: Optional[Any] = None

# Tracked packages
_TRACKED_PACKAGES: Dict[str, Dict[str, Any]] = {}

# Reserved names
_RESERVED_NAMES: Set[str] = {
    "__name__", "__doc__", "__package__", "__loader__",
    "__spec__", "__path__", "__file__", "__cached__",
    "__builtins__", "__import__", "__all__", "__version__",
    "__author__", "__email__", "__license__", "__copyright__",
    "__credits__", "__maintainer__", "__status__",
}


# ============================================================
# Delegated state setters (defined in _state_setters.py)
# ============================================================

# These are imported at the end of this module to avoid circular deps.
# They are declared here for documentation/IDE support.

def _set_symbol_index_built(value: bool) -> None: ...
def _set_stdlib_cache_built(value: bool) -> None: ...
def _set_third_party_cache_built(value: bool) -> None: ...
def _set_background_index_building(value: bool) -> None: ...
def reset_all() -> None: ...
def _load_priorities_from_file() -> Dict[str, int]: ...
def get_importing_modules() -> Set[str]: ...


# ── Dynamically replace stubs with real implementations ──────────────

def _activate_state_setters() -> None:
    """Replace stub functions with real implementations."""
    from ._state_setters import (
        _set_symbol_index_built as _s1,
        _set_stdlib_cache_built as _s2,
        _set_third_party_cache_built as _s3,
        _set_background_index_building as _s4,
        reset_all as _r,
        _load_priorities_from_file as _lpf,
        get_importing_modules as _gim,
    )
    import laziest_import._config as _self
    _self._set_symbol_index_built = _s1
    _self._set_stdlib_cache_built = _s2
    _self._set_third_party_cache_built = _s3
    _self._set_background_index_building = _s4
    _self.reset_all = _r
    _self._load_priorities_from_file = _lpf
    _self.get_importing_modules = _gim


try:
    _activate_state_setters()
except ImportError:
    pass  # deferred activation in build/editable install environments