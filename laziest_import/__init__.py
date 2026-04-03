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
"""

from typing import Dict, List, Optional, Set, Any, Tuple
import sys
import importlib
import importlib.util
import importlib.machinery
import pkgutil
import warnings

__version__ = "0.0.1-pre"

# Auto-search feature enabled flag
_AUTO_SEARCH_ENABLED: bool = True

# Known modules cache (avoids repeated searches)
_KNOWN_MODULES_CACHE: Optional[Set[str]] = None

# Class name to module mapping cache (e.g., "DataFrame" -> "pandas")
_CLASS_TO_MODULE_CACHE: Dict[str, str] = {}


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


# Module alias mapping: alias -> actual module name
_ALIAS_MAP: Dict[str, str] = {
    # Data Science
    "np": "numpy",
    "pd": "pandas",
    "plt": "matplotlib.pyplot",
    "mpl": "matplotlib",
    "sns": "seaborn",
    
    # Machine Learning
    "sklearn": "sklearn",
    "torch": "torch",
    "tf": "tensorflow",
    "keras": "keras",
    
    # Standard Library
    "os": "os",
    "sys": "sys",
    "re": "re",
    "json": "json",
    "csv": "csv",
    "datetime": "datetime",
    "collections": "collections",
    "itertools": "itertools",
    "functools": "functools",
    "pathlib": "pathlib",
    "typing": "typing",
    "math": "math",
    "random": "random",
    "time": "time",
    "logging": "logging",
    "argparse": "argparse",
    "subprocess": "subprocess",
    "threading": "threading",
    "multiprocessing": "multiprocessing",
    "pickle": "pickle",
    "shutil": "shutil",
    "glob": "glob",
    "io": "io",
    "copy": "copy",
    
    # HTTP Requests
    "requests": "requests",
    "httpx": "httpx",
    "aiohttp": "aiohttp",
    "urllib": "urllib",
    
    # Web Parsing
    "bs4": "bs4",
    "BeautifulSoup": "bs4",
    "lxml": "lxml",
    "html": "html",
    
    # Image Processing
    "Image": "PIL.Image",
    "PIL": "PIL",
    "cv2": "cv2",
    "cv": "cv2",
    
    # Database
    "sqlite3": "sqlite3",
    "sqlalchemy": "sqlalchemy",
    
    # Testing
    "pytest": "pytest",
    "unittest": "unittest",
    
    # Common Libraries
    "tqdm": "tqdm",
    "rich": "rich",
    "click": "click",
    "yaml": "yaml",
    "toml": "toml",
    "dotenv": "dotenv",
    
    # Async
    "asyncio": "asyncio",
    
    # Cryptography
    "hashlib": "hashlib",
    "hmac": "hmac",
    "secrets": "secrets",
    
    # Compression
    "zipfile": "zipfile",
    "tarfile": "tarfile",
    "gzip": "gzip",
    
    # Data Formats
    "pprint": "pprint",
    "dataclasses": "dataclasses",
    "enum": "enum",
}

# LazyModule proxy cache
_LAZY_MODULES: Dict[str, LazyModule] = {}


def _get_lazy_module(alias: str) -> LazyModule:
    """Get or create a LazyModule proxy"""
    if alias not in _LAZY_MODULES:
        module_name = _ALIAS_MAP.get(alias, alias)
        _LAZY_MODULES[alias] = LazyModule(alias, module_name)
    return _LAZY_MODULES[alias]


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
    _ALIAS_MAP[alias] = module_name
    # Create new LazyModule proxy
    _LAZY_MODULES[alias] = LazyModule(alias, module_name)
    globals()[alias] = _LAZY_MODULES[alias]
    # Update __all__
    if alias not in __all__:
        __all__.append(alias)


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
        if alias in __all__:
            __all__.remove(alias)
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
    ])
    return sorted(result)


# Initialization: create LazyModule proxies for all aliases and inject into global namespace
# This allows `from laziest_import import *` to get these proxy objects
for _alias, _mod_name in _ALIAS_MAP.items():
    _LAZY_MODULES[_alias] = LazyModule(_alias, _mod_name)
    globals()[_alias] = _LAZY_MODULES[_alias]


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
]