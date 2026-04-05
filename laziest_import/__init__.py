"""
laziest-import: Automatic Lazy Import Library

Usage:
    from laziest_import import *
    
    # Use common libraries directly without explicit import statements
    arr = np.array([1, 2, 3])
    df = pd.DataFrame({'a': [1, 2]})
    
    # Auto-search for unregistered modules
    app = flask.Flask(__name__)
    
Or:
    import laziest_import as lz
    arr = lz.np.array([1, 2, 3])
"""

from typing import Dict, List, Optional, Set, Any, Union

# Import version
from ._config import __version__

# Import data classes
from ._config import ImportStats, SearchResult, SymbolMatch

# Import proxy classes
from ._proxy import (
    LazyModule,
    LazySymbol,
    LazySubmodule,
    LazyProxy,
    lazy,
    _get_lazy_module,
)

# Import config internals needed for __getattr__
from ._config import (
    _INITIALIZING,
    _INITIALIZED,
    _AUTO_SEARCH_ENABLED,
    _ALIAS_MAP,
    _LAZY_MODULES,
    _SYMBOL_RESOLUTION_CONFIG,
    _SYMBOL_SEARCH_CONFIG,
    _DEBUG_MODE,
    _RESERVED_NAMES,
    get_init_lock,
)

# For dynamic export with __all__
import sys as _sys

# Import cache functionality
from ._cache import (
    set_cache_dir,
    get_cache_dir,
    reset_cache_dir,
    set_cache_config,
    get_cache_config,
    get_cache_stats,
    reset_cache_stats,
    invalidate_package_cache,
    get_cache_version,
    clear_symbol_cache,
    enable_file_cache,
    disable_file_cache,
    is_file_cache_enabled,
    clear_file_cache,
    get_file_cache_info,
    force_save_cache,
)

# Import alias functionality
from ._alias import (
    get_config_paths,
    get_config_dirs,
    reload_aliases,
    export_aliases,
    validate_aliases,
    register_alias,
    register_aliases,
    unregister_alias,
)

# Import fuzzy matching
from ._fuzzy import (
    _search_module,
    _search_class_in_modules,
    reload_mappings,
)

# Import symbol search
from ._symbol import (
    search_symbol,
    enable_symbol_search,
    disable_symbol_search,
    is_symbol_search_enabled,
    rebuild_symbol_index,
    get_symbol_search_config,
    get_symbol_cache_info,
    _search_symbol_enhanced,
    _handle_symbol_not_found,
    set_symbol_preference,
    get_symbol_preference,
    clear_symbol_preference,
    list_symbol_conflicts,
    set_module_priority,
    get_module_priority,
    enable_auto_symbol_resolution,
    disable_auto_symbol_resolution,
    get_symbol_resolution_config,
    get_loaded_modules_context,
)

# Import install functionality
from ._install import (
    install_package,
    enable_auto_install,
    disable_auto_install,
    is_auto_install_enabled,
    get_auto_install_config,
    set_pip_index,
    set_pip_extra_args,
    rebuild_module_cache,
)

# Import async operations
from ._async_ops import (
    import_async,
    import_multiple_async,
    enable_retry,
    disable_retry,
    is_retry_enabled,
)

# Import hooks and stats from config
from ._config import (
    _PRE_IMPORT_HOOKS,
    _POST_IMPORT_HOOKS,
    _IMPORT_STATS,
    _CACHE_STATS,
)


# ============== Additional Public API ==============

def list_loaded() -> List[str]:
    """Get list of loaded module aliases."""
    return [alias for alias, lm in _LAZY_MODULES.items() 
            if object.__getattribute__(lm, '_cached_module') is not None]


def list_available() -> List[str]:
    """Get list of all available module aliases."""
    return list(_ALIAS_MAP.keys())


def get_module(alias: str) -> Optional[Any]:
    """Get the actual module object for an alias."""
    if alias in _LAZY_MODULES:
        return _LAZY_MODULES[alias]._get_module()
    return None


def clear_cache() -> None:
    """Clear the module cache."""
    global _LAZY_MODULES
    for lm in _LAZY_MODULES.values():
        object.__setattr__(lm, '_cached_module', None)
        object.__setattr__(lm, '_submodule_cache', {})
    _LAZY_MODULES.clear()


def get_version(alias: str) -> Optional[str]:
    """Get the version of a loaded module."""
    if alias in _LAZY_MODULES:
        module = _LAZY_MODULES[alias]._get_module()
        return getattr(module, '__version__', None)
    return None


def reload_module(alias: str) -> bool:
    """Reload a module."""
    import importlib
    
    if alias not in _LAZY_MODULES:
        return False
    
    lm = _LAZY_MODULES[alias]
    module_name = object.__getattribute__(lm, '_module_name')
    cached = object.__getattribute__(lm, '_cached_module')
    
    if cached is not None:
        try:
            importlib.reload(cached)
            return True
        except Exception:
            return False
    return False


def enable_auto_search() -> None:
    """Enable auto-search for unregistered modules."""
    global _AUTO_SEARCH_ENABLED
    _AUTO_SEARCH_ENABLED = True


def disable_auto_search() -> None:
    """Disable auto-search for unregistered modules."""
    global _AUTO_SEARCH_ENABLED
    _AUTO_SEARCH_ENABLED = False


def is_auto_search_enabled() -> bool:
    """Check if auto-search is enabled."""
    return _AUTO_SEARCH_ENABLED


def search_module(name: str) -> Optional[str]:
    """Search for a module by name."""
    return _search_module(name)


def search_class(class_name: str) -> Optional[tuple]:
    """Search for a class in loaded modules."""
    return _search_class_in_modules(class_name)


def enable_debug_mode() -> None:
    """Enable debug mode."""
    global _DEBUG_MODE
    _DEBUG_MODE = True


def disable_debug_mode() -> None:
    """Disable debug mode."""
    global _DEBUG_MODE
    _DEBUG_MODE = False


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return _DEBUG_MODE


def get_import_stats() -> Dict[str, Any]:
    """Get import statistics."""
    avg_time = (
        _IMPORT_STATS.total_time / _IMPORT_STATS.total_imports
        if _IMPORT_STATS.total_imports > 0
        else 0.0
    )
    return {
        "total_imports": _IMPORT_STATS.total_imports,
        "total_time": _IMPORT_STATS.total_time,
        "average_time": avg_time,
        "module_times": dict(_IMPORT_STATS.module_times),
        "module_access_counts": dict(_IMPORT_STATS.module_access_counts),
    }


def reset_import_stats() -> None:
    """Reset import statistics."""
    global _IMPORT_STATS
    from ._config import ImportStats
    _IMPORT_STATS = ImportStats()


def add_pre_import_hook(hook) -> None:
    """Add a pre-import hook."""
    _PRE_IMPORT_HOOKS.append(hook)


def add_post_import_hook(hook) -> None:
    """Add a post-import hook."""
    _POST_IMPORT_HOOKS.append(hook)


def remove_pre_import_hook(hook) -> bool:
    """Remove a pre-import hook."""
    if hook in _PRE_IMPORT_HOOKS:
        _PRE_IMPORT_HOOKS.remove(hook)
        return True
    return False


def remove_post_import_hook(hook) -> bool:
    """Remove a post-import hook."""
    if hook in _POST_IMPORT_HOOKS:
        _POST_IMPORT_HOOKS.remove(hook)
        return True
    return False


def clear_import_hooks() -> None:
    """Remove all import hooks."""
    _PRE_IMPORT_HOOKS.clear()
    _POST_IMPORT_HOOKS.clear()


def validate_aliases_importable(aliases: Optional[Dict[str, str]] = None) -> Dict[str, Dict[str, Any]]:
    """Validate that aliases can actually be imported."""
    import importlib
    
    if aliases is None:
        aliases = _ALIAS_MAP
    
    importable = {}
    not_importable = {}
    
    for alias, module_name in aliases.items():
        try:
            importlib.import_module(module_name)
            importable[alias] = {"module": module_name, "status": "ok"}
        except ImportError as e:
            not_importable[alias] = {"module": module_name, "error": str(e)}
    
    return {"importable": importable, "not_importable": not_importable}


# ============== Module-level __getattr__ ==============

def __getattr__(name: str) -> Union[LazyModule, LazySymbol]:
    """
    Module-level attribute access hook for lazy loading.
    
    Supports:
    - Module aliases (np -> numpy)
    - Module name auto-correction (nump -> numpy)
    - Symbol auto-resolution (DataFrame -> pandas.DataFrame)
    """
    global _INITIALIZING, _INITIALIZED
    
    if _INITIALIZING and not _INITIALIZED:
        raise AttributeError(
            f"module '{__name__}' is still initializing, cannot access '{name}' yet."
        )
    
    if name in _RESERVED_NAMES:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    # 1. Check alias map
    if name in _ALIAS_MAP:
        return _get_lazy_module(name)
    
    # 2. Try module auto-search
    if _AUTO_SEARCH_ENABLED:
        found = _search_module(name)
        if found:
            _ALIAS_MAP[name] = found
            return _get_lazy_module(name)
    
    # 3. Try symbol auto-resolution
    if _SYMBOL_RESOLUTION_CONFIG["auto_symbol"] and _INITIALIZED:
        from ._config import _SYMBOL_PREFERENCES
        symbol_match = _search_symbol_enhanced(name, auto=True)
        if symbol_match:
            _SYMBOL_PREFERENCES[name] = symbol_match.module_name
            
            if _DEBUG_MODE:
                import logging
                logging.info(
                    f"[laziest-import] Auto-resolved symbol '{name}' -> "
                    f"{symbol_match.module_name}.{symbol_match.symbol_name}"
                )
            
            return LazySymbol(
                symbol_name=symbol_match.symbol_name,
                module_name=symbol_match.module_name,
                symbol_type=symbol_match.symbol_type
            )
    
    # 4. Fall back to interactive symbol search
    if _SYMBOL_SEARCH_CONFIG["enabled"] and _INITIALIZED:
        found_module = _handle_symbol_not_found(name)
        if found_module:
            return _get_lazy_module(name)
    
    # Not found
    available = list(_ALIAS_MAP.keys())[:10]
    msg = f"module '{__name__}' has no attribute '{name}'."
    if available:
        msg += f" Available modules: {available}..."
    raise AttributeError(msg)


def __dir__() -> List[str]:
    """Return list of public module attributes for tab completion."""
    result = list(_ALIAS_MAP.keys())
    result.extend([
        "__version__", "lazy",
        "register_alias", "register_aliases", "unregister_alias",
        "list_loaded", "list_available", "get_module", "clear_cache",
        "get_version", "reload_module",
        "enable_auto_search", "disable_auto_search", "is_auto_search_enabled",
        "search_module", "search_class", "rebuild_module_cache",
        "reload_aliases", "export_aliases", "validate_aliases",
        "get_config_paths", "get_config_dirs",
        "enable_debug_mode", "disable_debug_mode", "is_debug_mode",
        "get_import_stats", "reset_import_stats",
        "add_pre_import_hook", "add_post_import_hook",
        "remove_pre_import_hook", "remove_post_import_hook", "clear_import_hooks",
        "import_async", "import_multiple_async",
        "enable_retry", "disable_retry", "is_retry_enabled",
        "enable_file_cache", "disable_file_cache", "is_file_cache_enabled",
        "clear_file_cache", "get_file_cache_info", "force_save_cache",
        "set_cache_dir", "get_cache_dir", "reset_cache_dir",
        "enable_symbol_search", "disable_symbol_search", "is_symbol_search_enabled",
        "search_symbol", "rebuild_symbol_index", "get_symbol_search_config",
        "get_symbol_cache_info", "clear_symbol_cache",
        "set_symbol_preference", "get_symbol_preference", "clear_symbol_preference",
        "list_symbol_conflicts", "set_module_priority", "get_module_priority",
        "enable_auto_symbol_resolution", "disable_auto_symbol_resolution",
        "get_symbol_resolution_config", "get_loaded_modules_context",
        "enable_auto_install", "disable_auto_install", "is_auto_install_enabled",
        "install_package", "get_auto_install_config", "set_pip_index", "set_pip_extra_args",
        "set_cache_config", "get_cache_config", "get_cache_stats", "reset_cache_stats",
        "invalidate_package_cache", "get_cache_version",
    ])
    return sorted(result)


# ============== __all__ for from import * ==============
# Base exports (without aliases - aliases are added after initialization)
_BASE_EXPORTS = [
    "__version__", "lazy",
    "ImportStats", "SearchResult", "SymbolMatch",
    "LazyModule", "LazySymbol", "LazySubmodule", "LazyProxy",
    # Alias management
    "register_alias", "register_aliases", "unregister_alias",
    "list_loaded", "list_available", "get_module", "clear_cache",
    "get_version", "reload_module",
    # Auto-search
    "enable_auto_search", "disable_auto_search", "is_auto_search_enabled",
    "search_module", "search_class", "rebuild_module_cache",
    "reload_aliases", "reload_mappings", "export_aliases", "validate_aliases", "validate_aliases_importable",
    "get_config_paths", "get_config_dirs",
    # Debug & statistics
    "enable_debug_mode", "disable_debug_mode", "is_debug_mode",
    "get_import_stats", "reset_import_stats",
    # Import hooks
    "add_pre_import_hook", "add_post_import_hook",
    "remove_pre_import_hook", "remove_post_import_hook", "clear_import_hooks",
    # Async import
    "import_async", "import_multiple_async",
    # Retry configuration
    "enable_retry", "disable_retry", "is_retry_enabled",
    # File cache
    "enable_file_cache", "disable_file_cache", "is_file_cache_enabled",
    "clear_file_cache", "get_file_cache_info", "force_save_cache",
    "set_cache_dir", "get_cache_dir", "reset_cache_dir",
    # Symbol search
    "enable_symbol_search", "disable_symbol_search", "is_symbol_search_enabled",
    "search_symbol", "rebuild_symbol_index", "get_symbol_search_config",
    "get_symbol_cache_info", "clear_symbol_cache",
    # Symbol resolution
    "set_symbol_preference", "get_symbol_preference", "clear_symbol_preference",
    "list_symbol_conflicts", "set_module_priority", "get_module_priority",
    "enable_auto_symbol_resolution", "disable_auto_symbol_resolution",
    "get_symbol_resolution_config", "get_loaded_modules_context",
    # Auto install
    "enable_auto_install", "disable_auto_install", "is_auto_install_enabled",
    "install_package", "get_auto_install_config", "set_pip_index", "set_pip_extra_args",
    # Cache API
    "set_cache_config", "get_cache_config", "get_cache_stats", "reset_cache_stats",
    "invalidate_package_cache", "get_cache_version",
]

# __all__ will be updated after initialization
__all__ = sorted(_BASE_EXPORTS)


# ============== Initialization ==============

def _do_initialize() -> None:
    """Perform module initialization."""
    global _INITIALIZING, _INITIALIZED, _ALIAS_MAP, __all__
    
    lock = get_init_lock()
    
    with lock:
        if _INITIALIZED:
            return
        
        _INITIALIZING = True
        
        try:
            # Load aliases
            from ._alias import _load_all_aliases
            _ALIAS_MAP.update(_load_all_aliases(check_duplicates=True))
            
            # Init file cache
            from ._cache import _init_file_cache
            _init_file_cache()
            
            _INITIALIZED = True
            
            # Update __all__ to include aliases
            __all__ = sorted(set(_BASE_EXPORTS) | set(_ALIAS_MAP.keys()))
        finally:
            _INITIALIZING = False


# Run initialization
_do_initialize()