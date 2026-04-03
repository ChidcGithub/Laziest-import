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

from typing import Dict, List, Optional, Set, Any, Tuple
import sys
import importlib
import importlib.util
import importlib.machinery
import pkgutil
import warnings
import json
from pathlib import Path

__version__ = "0.0.1"

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


def _get_config_paths() -> List[Path]:
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
        Path(__file__).parent / "aliases.json",  # Package default
        Path.home() / ".laziest_import" / "aliases.json",  # User global
        Path.cwd() / ".laziest_import.json",  # Project level
    ]
    return paths


def _load_aliases_from_file(path: Path) -> Dict[str, str]:
    """
    Load aliases from a JSON configuration file.
    
    Supports two formats:
    1. Flat: {"alias": "module_name", ...}
    2. Categorized: {"category": {"alias": "module_name", ...}, ...}
    
    Args:
        path: Path to the configuration file
        
    Returns:
        Dictionary of alias -> module_name mappings
    """
    if not path.exists():
        return {}
    
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        
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
        warnings.warn(f"Failed to load config from {path}: {e}")
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
        warnings.warn(f"Alias '{alias}' is not a valid Python identifier")
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
    modules.update(sys.modules.keys())
    
    # Iterate through all modules in search paths
    for path in sys.path:
        try:
            for finder, name, ispkg in pkgutil.iter_modules([path]):
                modules.add(name)
                if ispkg:
                    modules.add(name)
        except (OSError, ImportError):
            continue
    
    # Add standard library modules
    try:
        import stdlib_modules
        if hasattr(stdlib_modules, 'STDLIB_MODULES'):
            modules.update(stdlib_modules.STDLIB_MODULES)
    except ImportError:
        # Manually add common standard library modules
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


def _search_module(name: str) -> Optional[str]:
    """
    Search for a matching module name.
    
    Args:
        name: Name to search for
        
    Returns:
        Found module name, or None if not found
    """
    if not _AUTO_SEARCH_ENABLED:
        return None
    
    known_modules = _build_known_modules_cache()
    
    # 1. Exact match
    if name in known_modules:
        return name
    
    # 2. Try direct import
    try:
        spec = importlib.util.find_spec(name)
        if spec is not None:
            return name
    except (ImportError, ModuleNotFoundError, ValueError):
        pass
    
    # 3. Fuzzy matching: find similar module names (stricter matching)
    name_lower = name.lower()
    candidates: List[Tuple[int, str]] = []
    
    for mod_name in known_modules:
        mod_lower = mod_name.lower()
        
        # Case-insensitive exact match
        if mod_lower == name_lower:
            candidates.append((0, mod_name))
        # Underscore variant match (e.g., my_lib vs mylib)
        elif mod_lower.replace('_', '') == name_lower.replace('_', ''):
            candidates.append((1, mod_name))
        # Hyphen variant match (e.g., my-lib vs mylib)
        elif mod_lower.replace('-', '') == name_lower.replace('-', ''):
            candidates.append((1, mod_name))
        # Module name is prefix of search name (e.g., pillow vs PIL)
        # Only allow this match when module name is long enough
        elif name_lower.startswith(mod_lower) and len(mod_lower) >= 4:
            candidates.append((2, mod_name))
        # Search name is prefix of module name (only when search name is long enough)
        elif mod_lower.startswith(name_lower) and len(name_lower) >= 4:
            candidates.append((3, mod_name))
    
    if candidates:
        # Sort by priority and return best match
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]
    
    return None


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
            mod = sys.modules.get(mod_name) or importlib.import_module(mod_name)
            if hasattr(mod, class_name):
                return (mod_name, getattr(mod, class_name))
        except (ImportError, ModuleNotFoundError):
            pass
    
    # Search in loaded modules
    for mod_name, mod in list(sys.modules.items()):
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
    Supports auto-search for unregistered modules.
    """
    
    __slots__ = ('_alias', '_module_name', '_cached_module', '_auto_searched')
    
    def __init__(self, alias: str, module_name: str, auto_searched: bool = False):
        object.__setattr__(self, '_alias', alias)
        object.__setattr__(self, '_module_name', module_name)
        object.__setattr__(self, '_cached_module', None)
        object.__setattr__(self, '_auto_searched', auto_searched)
    
    def _get_module(self) -> Any:
        """Get the actual module (lazy load)"""
        cached = object.__getattribute__(self, '_cached_module')
        if cached is not None:
            return cached
        
        module_name = object.__getattribute__(self, '_module_name')
        alias = object.__getattribute__(self, '_alias')
        
        try:
            module = importlib.import_module(module_name)
            object.__setattr__(self, '_cached_module', module)
            return module
        except ImportError as e:
            # If auto-search is enabled and not yet searched, try searching for the module
            auto_searched = object.__getattribute__(self, '_auto_searched')
            if _AUTO_SEARCH_ENABLED and not auto_searched:
                found_name = _search_module(alias)
                if found_name and found_name != module_name:
                    try:
                        module = importlib.import_module(found_name)
                        object.__setattr__(self, '_module_name', found_name)
                        object.__setattr__(self, '_cached_module', module)
                        object.__setattr__(self, '_auto_searched', True)
                        # Update global mapping
                        _ALIAS_MAP[alias] = found_name
                        return module
                    except ImportError:
                        pass
            
            raise ImportError(
                f"Cannot import module '{module_name}' (alias '{alias}'). "
                f"Please ensure the module is installed: pip install {module_name.split('.')[0]}"
            ) from e
    
    def __getattr__(self, name: str) -> Any:
        module = self._get_module()
        return getattr(module, name)
    
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
        default_path = Path(__file__).parent / "aliases.json"
        if default_path.exists():
            with open(default_path, encoding="utf-8") as f:
                data = json.load(f)
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
    
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    
    if path:
        output_path = Path(path)
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


def __getattr__(name: str) -> LazyModule:
    """
    Module-level attribute access hook for lazy loading.
    
    Called when accessing laziest_import.xxx or from laziest_import import xxx
    where xxx is not defined.
    """
    return _get_lazy_module(name)


def __dir__() -> List[str]:
    """
    Return list of public module attributes for tab completion.
    """
    result = list(_ALIAS_MAP.keys())
    result.extend([
        "__version__",
        "register_alias",
        "unregister_alias", 
        "list_loaded",
        "list_available",
        "get_module",
        "clear_cache",
        "enable_auto_search",
        "disable_auto_search",
        "is_auto_search_enabled",
        "search_module",
        "rebuild_module_cache",
        "reload_aliases",
        "export_aliases",
        "validate_aliases",
        "get_config_paths",
    ])
    return sorted(result)


# ============== Initialization ==============

# Load aliases from config files
_ALIAS_MAP = _load_all_aliases()

# Create LazyModule proxies for all aliases and inject into global namespace
_rebuild_global_namespace()

# Dynamically generate __all__, including all registered aliases and public API
__all__: List[str] = list(_ALIAS_MAP.keys()) + [
    "__version__",
    "register_alias",
    "unregister_alias",
    "list_loaded", 
    "list_available",
    "get_module",
    "clear_cache",
    "enable_auto_search",
    "disable_auto_search",
    "is_auto_search_enabled",
    "search_module",
    "rebuild_module_cache",
    "reload_aliases",
    "export_aliases",
    "validate_aliases",
    "get_config_paths",
]
