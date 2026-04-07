"""
Configuration constants and dataclasses for laziest-import.
"""

from typing import Dict, List, Optional, Set, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import threading


# ============== Version Loading ==============
def _load_version_config() -> Dict[str, Any]:
    """Load version configuration from version.json."""
    version_file = Path(__file__).parent / "version.json"
    if not version_file.exists():
        return {}

    try:
        with open(version_file, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


_VERSION_CONFIG = _load_version_config()
__version__ = _VERSION_CONFIG.get("_current_version", "0.0.3-pre6")


def get_version_range(target: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Get version range for a specific target (aliases or mappings).

    Args:
        target: "aliases" or "mappings"

    Returns:
        Tuple of (min_version, max_version)
    """
    target_config = _VERSION_CONFIG.get(target, {})
    min_ver = target_config.get("_min_version")
    max_ver = target_config.get("_max_version")
    return (min_ver, max_ver)


def get_cache_version() -> str:
    """Get cache version from version.json."""
    return _VERSION_CONFIG.get("_cache_version", __version__)


# ============== Priority Loading ==============
def _load_priorities_from_file() -> Dict[str, int]:
    """Load module priorities from JSON file."""
    priorities_file = Path(__file__).parent / "mappings" / "priorities.json"
    if not priorities_file.exists():
        return {}

    try:
        with open(priorities_file, encoding="utf-8") as f:
            data = json.load(f)

        # Flatten the categorized structure
        result: Dict[str, int] = {}
        for key, value in data.items():
            if key.startswith("_"):
                continue
            if isinstance(value, dict):
                result.update(value)
        return result
    except (json.JSONDecodeError, OSError):
        return {}


# ============== Initialization State ==============
_INITIALIZING: bool = False
_INITIALIZED: bool = False
_INIT_FAILED: bool = False
_INIT_ERROR: Optional[str] = None
_INIT_LOCK: Optional[threading.RLock] = None
_INIT_LOCK_CREATION_LOCK: threading.Lock = threading.Lock()


def get_init_state() -> Dict[str, Any]:
    """Get current initialization state (thread-safe read)."""
    return {
        "initializing": _INITIALIZING,
        "initialized": _INITIALIZED,
        "failed": _INIT_FAILED,
        "error": _INIT_ERROR,
    }


def is_initializing() -> bool:
    """Check if currently initializing."""
    return _INITIALIZING


def is_initialized() -> bool:
    """Check if initialization completed successfully."""
    return _INITIALIZED


def is_init_failed() -> bool:
    """Check if initialization failed."""
    return _INIT_FAILED


def get_init_error() -> Optional[str]:
    """Get initialization error message if any."""
    return _INIT_ERROR


# ============== Core Configuration ==============
_AUTO_SEARCH_ENABLED: bool = True

# Known modules cache
_KNOWN_MODULES_CACHE: Optional[Set[str]] = None
_KNOWN_MODULES_CACHE_TIME: float = 0.0
_KNOWN_MODULES_CACHE_TTL: float = 300.0  # 5 minutes

# Class name to module mapping
_CLASS_TO_MODULE_CACHE: Dict[str, str] = {}

# Module alias mapping
_ALIAS_MAP: Dict[str, str] = {}

# LazyModule proxy cache
_LAZY_MODULES: Dict[str, "LazyModule"] = {}  # type: ignore

# Thread-local storage for import context
_IMPORT_CONTEXT = threading.local()

# ============== Debug & Stats ==============
_DEBUG_MODE: bool = False
_FILE_CACHE_ENABLED: bool = True


@dataclass
class ImportStats:
    """Import statistics record."""

    total_imports: int = 0
    total_time: float = 0.0
    module_times: Dict[str, float] = field(default_factory=dict)
    module_access_counts: Dict[str, int] = field(default_factory=dict)


_IMPORT_STATS: ImportStats = ImportStats()

# ============== Import Hooks ==============
_PRE_IMPORT_HOOKS: List[Callable[[str], None]] = []
_POST_IMPORT_HOOKS: List[Callable[[str, Any], None]] = []

# ============== Retry Configuration ==============
_RETRY_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "max_retries": 3,
    "retry_delay": 0.5,
    "retry_modules": set(),
}

# ============== Auto-Install Configuration ==============
_AUTO_INSTALL_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "interactive": True,
    "index": None,
    "extra_args": [],
    "prefer_uv": False,
    "silent": False,
}

# ============== Symbol Search Configuration ==============
_SYMBOL_SEARCH_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "interactive": True,
    "exact_params": False,
    "max_results": 5,
    "search_depth": 1,
    "cache_enabled": True,
    "skip_private": True,
    "skip_stdlib": False,
}

# Symbol cache
_SYMBOL_CACHE: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}
_STDLIB_SYMBOL_CACHE: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}
_THIRD_PARTY_SYMBOL_CACHE: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}
_SYMBOL_INDEX_BUILT: bool = False
_STDLIB_CACHE_BUILT: bool = False
_THIRD_PARTY_CACHE_BUILT: bool = False

# User confirmed mappings
_CONFIRMED_MAPPINGS: Dict[str, str] = {}

# ============== Module Priority Configuration ==============
# Loaded from mappings/priorities.json
_MODULE_PRIORITY: Dict[str, int] = _load_priorities_from_file()

# ============== Symbol Preferences ==============
_SYMBOL_PREFERENCES: Dict[str, str] = {
    "DataFrame": "pandas",
    "Series": "pandas",
    "array": "numpy",
    "ndarray": "numpy",
    "Tensor": "torch",
    "read_csv": "pandas",
    "read_excel": "pandas",
    "read_json": "pandas",
    "concat": "pandas",
    "merge": "pandas",
    "figure": "matplotlib.pyplot",
    "subplot": "matplotlib.pyplot",
    "plot": "matplotlib.pyplot",
    "scatter": "matplotlib.pyplot",
    "hist": "matplotlib.pyplot",
    "imshow": "matplotlib.pyplot",
    "show": "matplotlib.pyplot",
    "savefig": "matplotlib.pyplot",
}

# ============== Symbol Resolution Configuration ==============
_SYMBOL_RESOLUTION_CONFIG: Dict[str, Any] = {
    "auto_symbol": True,
    "auto_threshold": 0.7,
    "conflict_threshold": 0.3,
    "symbol_misspelling": True,
    "context_aware": True,
    "warn_on_conflict": True,
    "save_preferences": True,
}

# ============== Cache Configuration ==============
_CACHE_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "max_size_mb": 100,
    "cleanup_threshold": 0.8,
    "file_cache_enabled": True,
    "symbol_index_enabled": True,
    "persist_across_sessions": True,
    "symbol_index_ttl": 86400,
    "stdlib_cache_ttl": 604800,
    "third_party_cache_ttl": 86400,
    "enable_compression": False,
    "max_cache_size_mb": 100,
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
_TRACKED_PACKAGES: Dict[str, Dict[str, Any]] = {}

# Incremental index update configuration
_INCREMENTAL_INDEX_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "check_version": True,  # Check package version changes
    "check_mtime": False,  # Check file modification time (slower)
    "background_build": True,  # Build index in background on startup
    "background_timeout": 60.0,  # Timeout for background index build
}

# Module skip configuration for faster scanning
_MODULE_SKIP_CONFIG: Dict[str, Any] = {
    "skip_test_modules": True,
    "skip_internal_modules": True,
    "skip_large_modules": True,
    "large_module_threshold": 100,  # Skip modules with more than this many public names
    "skip_modules_file": None,  # Path to custom skip modules JSON file
}

# Background preheat configuration
_PREHEAT_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "async_index_build": True,
    "preload_common_modules": True,
    "max_preload_threads": 4,
}

# Background index build state
_BACKGROUND_INDEX_BUILDING: bool = False
_BACKGROUND_INDEX_THREAD: Optional[threading.Thread] = None

# Reserved names that shouldn't be proxied
_RESERVED_NAMES: Set[str] = {
    "__name__",
    "__doc__",
    "__package__",
    "__loader__",
    "__spec__",
    "__path__",
    "__file__",
    "__cached__",
    "__builtins__",
    "__import__",
    "__all__",
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__copyright__",
    "__credits__",
    "__maintainer__",
    "__status__",
}


# ============== Dataclasses ==============
@dataclass
class SearchResult:
    """Search result for a symbol."""

    module_name: str
    symbol_name: str
    symbol_type: str  # 'class', 'function', 'callable'
    signature: Optional[str]
    score: float
    obj: Optional[Any] = None


@dataclass
class SymbolMatch:
    """Scored symbol match with confidence and source information."""

    module_name: str
    symbol_name: str
    symbol_type: str
    signature: Optional[str]
    confidence: float
    source: str  # 'exact', 'user_pref', 'context', 'priority', 'fuzzy', 'misspelling'
    obj: Optional[Any] = None


# ============== Helper Functions ==============
_IMPORT_CONTEXT_LOCK = threading.Lock()


def get_importing_modules() -> Set[str]:
    """Get the set of modules currently being imported (thread-local)."""
    if not hasattr(_IMPORT_CONTEXT, "importing"):
        with _IMPORT_CONTEXT_LOCK:
            if not hasattr(_IMPORT_CONTEXT, "importing"):
                _IMPORT_CONTEXT.importing = set()
    return _IMPORT_CONTEXT.importing


def get_init_lock() -> threading.RLock:
    """Get or create the initialization lock (lazy initialization, thread-safe)."""
    global _INIT_LOCK
    if _INIT_LOCK is None:
        with _INIT_LOCK_CREATION_LOCK:
            if _INIT_LOCK is None:
                _INIT_LOCK = threading.RLock()
    return _INIT_LOCK


# ============== Version Utilities ==============
def _parse_version(version_str: str) -> Tuple[Tuple[int, ...], Optional[str]]:
    """
    Parse a version string into comparable components.

    Supports formats like:
    - "0.0.3-pre6" -> ((0, 0, 3), "pre6")
    - "1.2.3" -> ((1, 2, 3), None)
    - "0.0.3" -> ((0, 0, 3), None)

    Returns:
        Tuple of (numeric_tuple, prerelease_suffix)
    """
    import re

    # Split into main version and prerelease suffix
    match = re.match(r"^(\d+(?:\.\d+)*)(?:-(.+))?$", version_str.strip())
    if not match:
        return ((0,), None)

    numeric_part = match.group(1)
    prerelease = match.group(2)

    # Parse numeric components
    try:
        numeric_tuple = tuple(int(x) for x in numeric_part.split("."))
    except ValueError:
        numeric_tuple = (0,)

    return (numeric_tuple, prerelease)


def _compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings.

    Returns:
        -1 if v1 < v2
        0 if v1 == v2
        1 if v1 > v2
    """
    n1, p1 = _parse_version(v1)
    n2, p2 = _parse_version(v2)

    # Compare numeric parts
    max_len = max(len(n1), len(n2))
    n1_padded = n1 + (0,) * (max_len - len(n1))
    n2_padded = n2 + (0,) * (max_len - len(n2))

    if n1_padded < n2_padded:
        return -1
    elif n1_padded > n2_padded:
        return 1

    # Numeric parts equal, compare prerelease
    # No prerelease > prerelease (e.g., 1.0 > 1.0-alpha)
    if p1 is None and p2 is None:
        return 0
    if p1 is None:
        return 1  # v1 is release, v2 is prerelease
    if p2 is None:
        return -1  # v1 is prerelease, v2 is release

    # Both have prerelease, compare lexicographically
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
    """
    Check if current version is within the specified range.

    Args:
        min_version: Minimum version (inclusive), None means no lower bound
        max_version: Maximum version (inclusive), None means no upper bound
        current_version: Current version to check
        file_path: Optional file path for warning message

    Returns:
        Tuple of (is_valid, warning_message)
    """
    warnings_list = []

    if min_version is not None:
        if _compare_versions(current_version, min_version) < 0:
            msg = f"Version {current_version} is below minimum {min_version}"
            if file_path:
                msg = f"{file_path}: {msg}"
            warnings_list.append(msg)

    if max_version is not None:
        if _compare_versions(current_version, max_version) > 0:
            msg = f"Version {current_version} is above maximum {max_version}"
            if file_path:
                msg = f"{file_path}: {msg}"
            warnings_list.append(msg)

    if warnings_list:
        return (False, "; ".join(warnings_list))
    return (True, None)


# ============== Symbol Index State Setters ==============
# These functions provide a clean way to modify symbol index state from other modules


def _set_symbol_index_built(value: bool) -> None:
    """Set the symbol index built state."""
    global _SYMBOL_INDEX_BUILT
    _SYMBOL_INDEX_BUILT = value


def _set_stdlib_cache_built(value: bool) -> None:
    """Set the stdlib cache built state."""
    global _STDLIB_CACHE_BUILT
    _STDLIB_CACHE_BUILT = value


def _set_third_party_cache_built(value: bool) -> None:
    """Set the third-party cache built state."""
    global _THIRD_PARTY_CACHE_BUILT
    _THIRD_PARTY_CACHE_BUILT = value


def _set_background_index_building(value: bool) -> None:
    """Set the background index building state."""
    global _BACKGROUND_INDEX_BUILDING
    _BACKGROUND_INDEX_BUILDING = value
