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

__version__ = "0.0.2-pre1"

# Auto-search feature enabled flag
_AUTO_SEARCH_ENABLED: bool = True

# Known modules cache (avoids repeated searches)
_KNOWN_MODULES_CACHE: Optional[Set[str]] = None

# Class name to module mapping cache (e.g., "DataFrame" -> "pandas")
_CLASS_TO_MODULE_CACHE: Dict[str, str] = {}

# Module alias mapping: alias -> actual module name
_ALIAS_MAP: Dict[str, str] = {}

# LazyModule proxy cache
_LAZY_MODULES: Dict[str, "LazyModule"] = {}

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


def _get_caller_file__Path_class() -> Optional[str]:
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


def _get_cache_file__Path_class(file_path: str) -> _Path_class:
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
    cache_file = _get_cache_file__Path_class(file_path)
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = _json_module.load(f)
        return FileCache.from_dict(data)
    except (json.JSONDecodeError, KeyError, OSError):
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
        cache = FileCache(
            file_path=file_path,
            file_sha=file_sha,
            loaded_modules=list(modules),
            timestamp=_time_module.time()
        )
        
        cache_file = _get_cache_file__Path_class(file_path)
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
    
    caller_path = _get_caller_file__Path_class()
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
    Start background thread to preload modules.
    
    Args:
        modules: List of module names to preload
    """
    def _preload():
        for module_name in modules:
            try:
                # Only preload if module is in _sys_module.modules (already imported before)
                # or if it's a standard library module
                if module_name in _sys_module.modules:
                    continue
                
                # Check if module is available
                spec = _importlib_module.util.find_spec(module_name)
                if spec:
                    # Import in background
                    _importlib_module.import_module(module_name)
                    if _DEBUG_MODE:
                        _logging_module.debug(f"[laziest-import] Preloaded {module_name}")
            except Exception as e:
                if _DEBUG_MODE:
                    _logging_module.debug(f"[laziest-import] Failed to preload {module_name}: {e}")
    
    # Start preload in daemon thread
    thread = _threading_module.Thread(target=_preload, daemon=True)
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
    except (json.JSONDecodeError, OSError) as e:
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
    if not alias.isidentifier():
        _warnings_module.warn(f"Alias '{alias}' is not a valid Python identifier")
        return False
    return True


def _rebuild_global_namespace() -> None:
    """
    Rebuild the global namespace with current aliases.
    
    Creates LazyModule proxies for all aliases and injects into globals.
    """
    global _LAZY_MODULES
    
    # Clear old lazy modules that are no longer in alias map
    for alias in list(_LAZY_MODULES.keys()):
        if alias not in _ALIAS_MAP:
            del _LAZY_MODULES[alias]
            if alias in globals():
                del globals()[alias]
    
    # Create LazyModule proxies for all current aliases
    for alias, module_name in _ALIAS_MAP.items():
        if alias not in _LAZY_MODULES:
            _LAZY_MODULES[alias] = LazyModule(alias, module_name)
        globals()[alias] = _LAZY_MODULES[alias]


def _build_known_modules_cache() -> Set[str]:
    """
    Build cache of all known importable modules.
    
    Returns:
        Set of installed module names
    """
    global _KNOWN_MODULES_CACHE
    if _KNOWN_MODULES_CACHE is not None:
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
    if hasattr(sys, 'stdlib_module_names'):
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
            # Update access count
            alias = object.__getattribute__(self, '_alias')
            _IMPORT_STATS.module_access_counts[alias] = _IMPORT_STATS.module_access_counts.get(alias, 0) + 1
            return cached
        
        module_name = object.__getattribute__(self, '_module_name')
        alias = object.__getattribute__(self, '_alias')
        
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
            
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return _importlib_module.import_module(name)
                except ImportError as e:
                    last_error = e
                    if attempt < max_retries:
                        if _DEBUG_MODE:
                            _logging_module.info(f"Retry {attempt + 1}/{max_retries} for {name}")
                        _time_module.sleep(retry_delay)
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
            
            raise ImportError(
                f"Cannot import module '{module_name}' (alias '{alias}'). "
                f"Please ensure the module is installed: pip install {module_name.split('.')[0]}"
            ) from e
    
    def __getattr__(self, name: str) -> Any:
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
        raise TypeError(f"'{type(module).__name__}' object is not callable")


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
            return cached
        
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
    global _KNOWN_MODULES_CACHE
    _KNOWN_MODULES_CACHE = None
    _build_known_modules_cache()


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
    # Create new LazyModule proxy
    _LAZY_MODULES[alias] = LazyModule(alias, module_name)
    globals()[alias] = _LAZY_MODULES[alias]


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
        if alias in globals():
            del globals()[alias]
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
        cache_file = _get_cache_file__Path_class(file_path)
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
        
    Example:
        >>> info = get_file_cache_info()
        >>> print(info['cached_modules'])
        ['os', 'sys', 'json']
    """
    cache_dir = _get_cache_dir()
    cache_files = list(cache_dir.glob("*.json"))
    
    return {
        "enabled": _FILE_CACHE_ENABLED,
        "caller_file": _CALLER_FILE_PATH,
        "cached_modules": list(_CALLER_LOADED_MODULES),
        "cache_dir": str(cache_dir),
        "cache_size": len(cache_files),
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
}


def __getattr__(name: str) -> LazyModule:
    """
    Module-level attribute access hook for lazy loading.
    
    Called when accessing laziest_import.xxx or from laziest_import import xxx
    where xxx is not defined.
    """
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
    
    # Not found, raise AttributeError
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'. "
                        f"Available modules: {list(_ALIAS_MAP.keys())[:10]}... (use list_available() to see all)")


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
    ])
    return sorted(result)


# ============== Initialization ==============

# Load aliases from config files
_ALIAS_MAP = _load_all_aliases()

# Create LazyModule proxies for all aliases and inject into global namespace
_rebuild_global_namespace()

# Initialize file cache for the caller
_init_file_cache()

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
]




