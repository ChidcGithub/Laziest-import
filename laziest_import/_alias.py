"""
Alias management for laziest-import.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
import sys
import json
import time
import warnings
import logging
import pkgutil

from ._config import (
    _DEBUG_MODE,
    _ALIAS_MAP,
    _LAZY_MODULES,
    _KNOWN_MODULES_CACHE,
    _KNOWN_MODULES_CACHE_TIME,
    _KNOWN_MODULES_CACHE_TTL,
    check_version_range,
    get_version_range,
)


def _get_alias_dir() -> Path:
    """Get the package aliases directory."""
    return Path(__file__).parent / "aliases"


def _lookup_alias_fast(alias: str) -> Optional[str]:
    """
    Fast lookup of a single alias by loading only the relevant letter file.
    
    Args:
        alias: The alias to look up
        
    Returns:
        The module name if found, None otherwise
    """
    if not alias:
        return None
    
    first_char = alias[0].upper()
    if first_char.isalpha():
        letter = first_char
    else:
        letter = '_'
    
    alias_dir = _get_alias_dir()
    letter_aliases = _load_aliases_from_letter_file(alias_dir, letter)
    
    if alias in letter_aliases:
        return letter_aliases[alias]
    
    for dir_path in _get_config_dirs():
        if dir_path.exists() and dir_path.is_dir():
            dir_aliases = _load_aliases_from_letter_file(dir_path, letter)
            if alias in dir_aliases:
                return dir_aliases[alias]
    
    for path in _get_config_paths():
        file_aliases = _load_aliases_from_file(path)
        if alias in file_aliases:
            return file_aliases[alias]
    
    return None


def _get_config_paths() -> List[Path]:
    """Get configuration file paths in priority order."""
    paths = [
        Path.home() / ".laziest_import" / "aliases.json",
        Path.cwd() / ".laziest_import.json",
    ]
    return paths


def _get_config_dirs() -> List[Path]:
    """Get configuration directory paths for letter-based alias files."""
    dirs = [
        Path.home() / ".laziest_import" / "aliases",
        Path.cwd() / ".laziest_import",
    ]
    return dirs


def _load_aliases_from_letter_file(dir_path: Path, letter: str) -> Dict[str, str]:
    """
    Load aliases from a specific letter file (e.g., A.json, B.json).
    
    Args:
        dir_path: Path to the aliases directory
        letter: The letter (A-Z) or '_' for non-alphabetic aliases
        
    Returns:
        Dictionary of alias -> module_name mappings
    """
    aliases: Dict[str, str] = {}
    
    letter = letter.upper()
    if letter not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_':
        return aliases
    
    file_path = dir_path / f"{letter}.json"
    if not file_path.exists():
        return aliases
    
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    aliases[key] = value
    except (json.JSONDecodeError, OSError) as e:
        if _DEBUG_MODE:
            logging.warning(f"Failed to load aliases from {file_path}: {e}")
    
    return aliases


# Track if aliases version has been checked
_ALIASES_VERSION_CHECKED: bool = False


def _check_aliases_version_range() -> None:
    """Check aliases version range from version.json (only once)."""
    global _ALIASES_VERSION_CHECKED
    if _ALIASES_VERSION_CHECKED:
        return
    
    _ALIASES_VERSION_CHECKED = True
    min_version, max_version = get_version_range("aliases")
    if min_version is not None or max_version is not None:
        is_valid, warning_msg = check_version_range(
            min_version, max_version, file_path="aliases"
        )
        if not is_valid:
            warnings.warn(
                f"[laziest-import] {warning_msg}. Some alias features may not work correctly.",
                UserWarning,
                stacklevel=3
            )


def _check_duplicates(aliases: Dict[str, str], source: str = "") -> List[Tuple[str, str, str]]:
    """
    Check for duplicate aliases with different module mappings.
    
    Args:
        aliases: Dictionary of alias -> module_name mappings
        source: Source description for error messages
        
    Returns:
        List of (alias, module1, module2) tuples for conflicts
    """
    alias_sources: Dict[str, List[str]] = {}
    for alias, module in aliases.items():
        if alias not in alias_sources:
            alias_sources[alias] = []
        if module not in alias_sources[alias]:
            alias_sources[alias].append(module)
    
    duplicates = []
    for alias, modules in alias_sources.items():
        if len(modules) > 1:
            duplicates.append((alias, modules[0], modules[1]))
    
    return duplicates


def _load_aliases_from_dir(dir_path: Path, check_duplicates: bool = True) -> Dict[str, str]:
    """
    Load aliases from A-Z letter files in a directory.
    
    Args:
        dir_path: Path to the directory containing alias JSON files
        check_duplicates: If True, raise error on duplicate aliases with different modules
        
    Returns:
        Dictionary of alias -> module_name mappings
    """
    aliases: Dict[str, str] = {}
    
    if not dir_path.exists() or not dir_path.is_dir():
        return aliases
    
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_':
        letter_aliases = _load_aliases_from_letter_file(dir_path, letter)
        if letter_aliases:
            for alias, module in letter_aliases.items():
                if alias in aliases and aliases[alias] != module:
                    if check_duplicates:
                        raise ValueError(
                            f"[laziest-import] Duplicate alias '{alias}' with different modules: "
                            f"'{aliases[alias]}' vs '{module}'"
                        )
                aliases[alias] = module
    
    return aliases


def _load_aliases_from_file(path: Path) -> Dict[str, str]:
    """
    Load aliases from a JSON configuration file.
    
    Supports two formats:
    1. Flat: {"alias": "module_name", ...}
    2. Categorized: {"category": {"alias": "module_name", ...}, ...}
    """
    if not path.exists():
        return {}
    
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        
        aliases: Dict[str, str] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                aliases.update(value)
            elif isinstance(value, str):
                aliases[key] = value
        
        return aliases
    except (json.JSONDecodeError, OSError) as e:
        warnings.warn(f"Failed to load config from {path}: {e}")
        return {}


def _load_all_aliases(check_duplicates: bool = True) -> Dict[str, str]:
    """
    Load aliases from all sources.
    
    Loading order (later overrides earlier):
        1. Package aliases directory (laziest_import/aliases/A-Z.json)
        2. User global directory (~/.laziest_import/aliases/A-Z.json)
        3. User global file (~/.laziest_import/aliases.json)
        4. Project level directory (./.laziest_import/A-Z.json)
        5. Project level file (./.laziest_import.json)
    """
    # Check aliases version range from version.json
    _check_aliases_version_range()
    
    aliases: Dict[str, str] = {}
    
    # 1. Load from package aliases directory
    alias_dir = _get_alias_dir()
    dir_aliases = _load_aliases_from_dir(alias_dir, check_duplicates=False)
    if dir_aliases:
        aliases.update(dir_aliases)
    
    # 2. Load from user/project config directories
    for dir_path in _get_config_dirs():
        if dir_path.exists() and dir_path.is_dir():
            dir_aliases = _load_aliases_from_dir(dir_path, check_duplicates=False)
            if dir_aliases:
                for alias, module in dir_aliases.items():
                    if alias in aliases and aliases[alias] != module:
                        if check_duplicates:
                            raise ValueError(
                                f"[laziest-import] Duplicate alias '{alias}' with different modules: "
                                f"'{aliases[alias]}' vs '{module}' (from {dir_path})"
                            )
                    aliases[alias] = module
    
    # 3. Load from user/project config files
    for path in _get_config_paths():
        file_aliases = _load_aliases_from_file(path)
        if file_aliases:
            for alias, module in file_aliases.items():
                if alias in aliases and aliases[alias] != module:
                    if check_duplicates:
                        raise ValueError(
                            f"[laziest-import] Duplicate alias '{alias}' with different modules: "
                            f"'{aliases[alias]}' (from package) vs '{module}' (from {path})"
                        )
                aliases[alias] = module
    
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
        if '-' in alias or '.' in alias:
            return True
        warnings.warn(f"Alias '{alias}' is not a valid Python identifier")
        return False
    return True


def _rebuild_global_namespace() -> None:
    """
    Rebuild the global namespace with current aliases.
    
    Creates LazyModule proxies for all aliases.
    """
    global _LAZY_MODULES
    
    for alias in list(_LAZY_MODULES.keys()):
        if alias not in _ALIAS_MAP:
            del _LAZY_MODULES[alias]
    
    # Import here to avoid circular import
    from ._proxy import LazyModule
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
    
    current_time = time.time()
    if _KNOWN_MODULES_CACHE is not None and not force:
        if current_time - _KNOWN_MODULES_CACHE_TIME < _KNOWN_MODULES_CACHE_TTL:
            return _KNOWN_MODULES_CACHE
    
    modules: Set[str] = set()
    
    # Add already loaded modules
    modules.update(sys.modules.keys())
    
    # Iterate through all modules in search paths
    for path in sys.path:
        if not path:
            path = '.'
        if not Path(path).exists():
            continue
        try:
            for finder, name, ispkg in pkgutil.iter_modules([path]):
                modules.add(name)
        except (OSError, ImportError):
            continue
    
    # Add standard library modules
    if hasattr(sys, 'stdlib_module_names'):
        modules.update(sys.stdlib_module_names)
    else:
        stdlib_modules = {
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
        modules.update(stdlib_modules)
    
    _KNOWN_MODULES_CACHE = modules
    _KNOWN_MODULES_CACHE_TIME = current_time
    
    return modules


# ============== Alias API ==============

def get_config_paths() -> List[str]:
    """Get configuration file paths as strings."""
    return [str(p) for p in _get_config_paths()]


def get_config_dirs() -> List[str]:
    """Get configuration directory paths as strings."""
    return [str(p) for p in _get_config_dirs()]


def reload_aliases() -> None:
    """Reload aliases from all configuration sources."""
    global _ALIAS_MAP
    _ALIAS_MAP.clear()
    _ALIAS_MAP.update(_load_all_aliases(check_duplicates=True))
    _rebuild_global_namespace()


def export_aliases(path: Optional[str] = None, include_categories: bool = True) -> str:
    """
    Export current aliases to a JSON file.
    
    Args:
        path: Output file path (optional, returns string if None)
        include_categories: Include category information
        
    Returns:
        JSON string of aliases
    """
    if include_categories:
        # Group by first letter
        categorized: Dict[str, Dict[str, str]] = {}
        for alias, module in sorted(_ALIAS_MAP.items()):
            category = alias[0].upper() if alias else '_'
            if category not in categorized:
                categorized[category] = {}
            categorized[category][alias] = module
        output = json.dumps(categorized, indent=2, ensure_ascii=False)
    else:
        output = json.dumps(_ALIAS_MAP, indent=2, ensure_ascii=False)
    
    if path:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(output)
    
    return output


def validate_aliases(aliases: Optional[Dict[str, str]] = None) -> Dict[str, List[str]]:
    """
    Validate alias entries.
    
    Args:
        aliases: Aliases to validate (uses _ALIAS_MAP if None)
        
    Returns:
        Dictionary with 'valid', 'invalid', and 'warnings' lists
    """
    if aliases is None:
        aliases = _ALIAS_MAP
    
    result: Dict[str, List[str]] = {
        "valid": [],
        "invalid": [],
        "warnings": [],
    }
    
    for alias, module in aliases.items():
        if _validate_alias(alias, module):
            result["valid"].append(alias)
        else:
            result["invalid"].append(alias)
    
    return result


def register_alias(alias: str, module_name: str) -> None:
    """
    Register a new alias.
    
    Args:
        alias: The alias name
        module_name: The actual module name
    """
    if not _validate_alias(alias, module_name):
        raise ValueError(f"Invalid alias: {alias} -> {module_name}")
    
    _ALIAS_MAP[alias] = module_name
    
    # Create lazy module proxy
    from ._proxy import LazyModule
    if alias not in _LAZY_MODULES:
        _LAZY_MODULES[alias] = LazyModule(alias, module_name)


def register_aliases(aliases: Dict[str, str]) -> List[str]:
    """
    Register multiple aliases.
    
    Args:
        aliases: Dictionary of alias -> module_name
        
    Returns:
        List of successfully registered aliases
    """
    registered = []
    for alias, module in aliases.items():
        try:
            register_alias(alias, module)
            registered.append(alias)
        except ValueError:
            pass
    return registered


def unregister_alias(alias: str) -> bool:
    """
    Unregister an alias.
    
    Args:
        alias: The alias to remove
        
    Returns:
        True if alias was removed, False if not found
    """
    if alias in _ALIAS_MAP:
        del _ALIAS_MAP[alias]
        if alias in _LAZY_MODULES:
            del _LAZY_MODULES[alias]
        return True
    return False
