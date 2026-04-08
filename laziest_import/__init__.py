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

# Import config module for state access (avoid value copy issues)
from . import _config as _config_module

# Import config internals needed for __getattr__
from ._config import (
    _AUTO_SEARCH_ENABLED,
    _ALIAS_MAP,
    _LAZY_MODULES,
    _SYMBOL_RESOLUTION_CONFIG,
    _SYMBOL_SEARCH_CONFIG,
    _DEBUG_MODE,
    _RESERVED_NAMES,
    get_init_lock,
    # State helper functions
    is_initializing,
    is_initialized,
    is_init_failed,
    get_init_error,
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
    # Package version functions
    get_package_version,
    get_all_package_versions,
    get_laziest_import_version,
    # Incremental index functions
    enable_incremental_index,
    enable_background_build,
    enable_cache_compression,
    get_incremental_config,
    get_preheat_config,
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

# Import symbol search (lazy loaded to reduce startup time)
# Full symbol module is loaded on first use
_SYMBOL_FUNCTIONS: Dict[str, Any] = {}

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
    return [
        alias
        for alias, lm in _LAZY_MODULES.items()
        if object.__getattribute__(lm, "_cached_module") is not None
    ]


def list_available() -> List[str]:
    """Get list of all available module aliases."""
    return list(_ALIAS_MAP.keys())


def get_module(alias: str) -> Optional[Any]:
    """Get the actual module object for an alias."""
    if alias in _LAZY_MODULES:
        return _LAZY_MODULES[alias]._get_module()
    return None


def clear_cache() -> None:
    """Clear the module cache.

    This clears all cached module instances, but keeps alias mappings intact.
    Use reload_aliases() to reset aliases, or reset_all() to reset everything.
    """
    global _LAZY_MODULES
    for lm in _LAZY_MODULES.values():
        object.__setattr__(lm, "_cached_module", None)
        object.__setattr__(lm, "_submodule_cache", {})
    _LAZY_MODULES.clear()


def reset_all() -> None:
    """Reset all state including cache, aliases, and symbol index.

    This performs a complete reset:
    - Clears module cache
    - Reloads aliases from configuration files
    - Clears symbol cache

    Use this for a complete reset. Use clear_cache() for a lighter reset
    that only clears loaded modules.
    """
    global _LAZY_MODULES

    # Clear module cache
    for lm in _LAZY_MODULES.values():
        object.__setattr__(lm, "_cached_module", None)
        object.__setattr__(lm, "_submodule_cache", {})
    _LAZY_MODULES.clear()

    # Reload aliases from configuration
    from ._alias import reload_aliases

    reload_aliases()

    # Clear symbol cache
    from ._cache import clear_symbol_cache

    clear_symbol_cache()

    # Reset import stats
    reset_import_stats()

    # Clear confirmed mappings
    from ._config import _CONFIRMED_MAPPINGS

    _CONFIRMED_MAPPINGS.clear()


def get_version(alias: str) -> Optional[str]:
    """Get the version of a loaded module."""
    if alias in _LAZY_MODULES:
        module = _LAZY_MODULES[alias]._get_module()
        return getattr(module, "__version__", None)
    return None


def reload_module(alias: str) -> bool:
    """Reload a module."""
    import importlib

    if alias not in _LAZY_MODULES:
        return False

    lm = _LAZY_MODULES[alias]
    module_name = object.__getattribute__(lm, "_module_name")
    cached = object.__getattribute__(lm, "_cached_module")

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


def validate_aliases_importable(
    aliases: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, Any]]:
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


# ============== Lazy Loading Helpers ==============


def _ensure_symbol_functions_loaded() -> None:
    """Ensure symbol-related functions are loaded (lazy loading)."""
    global _SYMBOL_FUNCTIONS

    if _SYMBOL_FUNCTIONS:
        return

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
        build_symbol_index_incremental,
        search_with_sharding,
        enable_sharding,
        disable_sharding,
        get_sharding_config,
        clear_shard_cache,
    )

    _SYMBOL_FUNCTIONS.update(
        {
            "search_symbol": search_symbol,
            "enable_symbol_search": enable_symbol_search,
            "disable_symbol_search": disable_symbol_search,
            "is_symbol_search_enabled": is_symbol_search_enabled,
            "rebuild_symbol_index": rebuild_symbol_index,
            "get_symbol_search_config": get_symbol_search_config,
            "get_symbol_cache_info": get_symbol_cache_info,
            "_search_symbol_enhanced": _search_symbol_enhanced,
            "_handle_symbol_not_found": _handle_symbol_not_found,
            "set_symbol_preference": set_symbol_preference,
            "get_symbol_preference": get_symbol_preference,
            "clear_symbol_preference": clear_symbol_preference,
            "list_symbol_conflicts": list_symbol_conflicts,
            "set_module_priority": set_module_priority,
            "get_module_priority": get_module_priority,
            "enable_auto_symbol_resolution": enable_auto_symbol_resolution,
            "disable_auto_symbol_resolution": disable_auto_symbol_resolution,
            "get_symbol_resolution_config": get_symbol_resolution_config,
            "get_loaded_modules_context": get_loaded_modules_context,
            "build_symbol_index_incremental": build_symbol_index_incremental,
            "search_with_sharding": search_with_sharding,
            "enable_sharding": enable_sharding,
            "disable_sharding": disable_sharding,
            "get_sharding_config": get_sharding_config,
            "clear_shard_cache": clear_shard_cache,
        }
    )


# ============== Module-level __getattr__ ==============


def __getattr__(name: str) -> Union[LazyModule, LazySymbol, Any]:
    """
    Module-level attribute access hook for lazy loading.

    Supports:
    - Module aliases (np -> numpy)
    - Module name autocorrection (nump -> numpy)
    - Symbol auto-resolution (DataFrame -> pandas.DataFrame)
    - Lazy-loaded functions (search_symbol, which, help, etc.)
    """
    # Use helper functions to access state (avoids value copy issue)
    _initializing = is_initializing()
    _initialized = is_initialized()
    _failed = is_init_failed()
    _error = get_init_error()

    if _initializing and not _initialized:
        raise AttributeError(
            f"module '{__name__}' is still initializing, cannot access '{name}' yet."
        )

    if _failed:
        raise AttributeError(
            f"module '{__name__}' failed to initialize: {_error}. "
            f"Cannot access '{name}'."
        )

    if name in _RESERVED_NAMES:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    # 1. Check for lazy-loaded functions
    global _SYMBOL_FUNCTIONS
    if not _SYMBOL_FUNCTIONS:
        _ensure_symbol_functions_loaded()
    if name in _SYMBOL_FUNCTIONS:
        return _SYMBOL_FUNCTIONS[name]

    # 2. Check for which function
    if name == "which":
        from ._which import which, which_all

        _SYMBOL_FUNCTIONS["which"] = which
        _SYMBOL_FUNCTIONS["which_all"] = which_all
        return which

    # 3. Check for help function
    if name == "help":
        from ._help import help as help_func

        _SYMBOL_FUNCTIONS["help"] = help_func
        return help_func

    # 4. Check for background index functions
    if name in (
        "start_background_index_build",
        "is_index_building",
        "wait_for_index",
        "set_background_timeout",
        "get_background_timeout",
    ):
        import importlib

        _lazy_index_mod = importlib.import_module("laziest_import._lazy_index")
        _SYMBOL_FUNCTIONS[name] = getattr(_lazy_index_mod, name)
        return _SYMBOL_FUNCTIONS[name]

    # 5. Check for RC config functions
    if name in (
        "load_rc_config",
        "get_rc_value",
        "create_rc_file",
        "get_rc_info",
        "reload_rc_config",
    ):
        import importlib

        _rcconfig_mod = importlib.import_module("laziest_import._rcconfig")
        _SYMBOL_FUNCTIONS[name] = getattr(_rcconfig_mod, name)
        return _SYMBOL_FUNCTIONS[name]

    # 6. Check for introspect functions
    if name in ("list_module_symbols", "get_module_info", "search_in_module"):
        import importlib

        _introspect_mod = importlib.import_module("laziest_import._introspect")
        _SYMBOL_FUNCTIONS[name] = getattr(_introspect_mod, name)
        return _SYMBOL_FUNCTIONS[name]

    # 7. Check alias map
    if name in _ALIAS_MAP:
        return _get_lazy_module(name)

    # 10. Try module auto-search
    if _AUTO_SEARCH_ENABLED:
        found = _search_module(name)
        if found:
            _ALIAS_MAP[name] = found
            return _get_lazy_module(name)

    # 11. Try symbol auto-resolution
    if _SYMBOL_RESOLUTION_CONFIG["auto_symbol"] and _initialized:
        from ._config import _SYMBOL_PREFERENCES

        _ensure_symbol_functions_loaded()

        symbol_match = _SYMBOL_FUNCTIONS.get("_search_symbol_enhanced")(name, auto=True)
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
                symbol_type=symbol_match.symbol_type,
            )

    # 12. Fall back to interactive symbol search
    if _SYMBOL_SEARCH_CONFIG["enabled"] and _initialized:
        _ensure_symbol_functions_loaded()
        found_module = _SYMBOL_FUNCTIONS.get("_handle_symbol_not_found")(name)
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
    result.extend(
        [
            "__version__",
            "lazy",
            "register_alias",
            "register_aliases",
            "unregister_alias",
            "list_loaded",
            "list_available",
            "get_module",
            "clear_cache",
            "reset_all",
            "get_version",
            "reload_module",
            "enable_auto_search",
            "disable_auto_search",
            "is_auto_search_enabled",
            "search_module",
            "search_class",
            "rebuild_module_cache",
            "reload_aliases",
            "export_aliases",
            "validate_aliases",
            "get_config_paths",
            "get_config_dirs",
            "enable_debug_mode",
            "disable_debug_mode",
            "is_debug_mode",
            "get_import_stats",
            "reset_import_stats",
            "add_pre_import_hook",
            "add_post_import_hook",
            "remove_pre_import_hook",
            "remove_post_import_hook",
            "clear_import_hooks",
            "import_async",
            "import_multiple_async",
            "enable_retry",
            "disable_retry",
            "is_retry_enabled",
            "enable_file_cache",
            "disable_file_cache",
            "is_file_cache_enabled",
            "clear_file_cache",
            "get_file_cache_info",
            "force_save_cache",
            "set_cache_dir",
            "get_cache_dir",
            "reset_cache_dir",
            "enable_symbol_search",
            "disable_symbol_search",
            "is_symbol_search_enabled",
            "search_symbol",
            "rebuild_symbol_index",
            "get_symbol_search_config",
            "get_symbol_cache_info",
            "clear_symbol_cache",
            "set_symbol_preference",
            "get_symbol_preference",
            "clear_symbol_preference",
            "list_symbol_conflicts",
            "set_module_priority",
            "get_module_priority",
            "enable_auto_symbol_resolution",
            "disable_auto_symbol_resolution",
            "get_symbol_resolution_config",
            "get_loaded_modules_context",
            "build_symbol_index_incremental",
            "enable_auto_install",
            "disable_auto_install",
            "is_auto_install_enabled",
            "install_package",
            "get_auto_install_config",
            "set_pip_index",
            "set_pip_extra_args",
            "set_cache_config",
            "get_cache_config",
            "get_cache_stats",
            "reset_cache_stats",
            "invalidate_package_cache",
            "get_cache_version",
            # Package version functions
            "get_package_version",
            "get_all_package_versions",
            "get_laziest_import_version",
            # Incremental index functions
            "enable_incremental_index",
            "enable_background_build",
            "enable_cache_compression",
            "get_incremental_config",
            "get_preheat_config",
            # Symbol sharding
            "search_with_sharding",
            "enable_sharding",
            "disable_sharding",
            "get_sharding_config",
            "clear_shard_cache",
            # Background index build
            "start_background_index_build",
            "is_index_building",
            "wait_for_index",
            # Which function
            "which",
            "which_all",
            # Help
            "help",
        ]
    )
    return sorted(result)


# ============== __all__ for from import * ==============
# Base exports (without aliases - aliases are added after initialization)
_BASE_EXPORTS = [
    "__version__",
    "lazy",
    "ImportStats",
    "SearchResult",
    "SymbolMatch",
    "LazyModule",
    "LazySymbol",
    "LazySubmodule",
    "LazyProxy",
    # Alias management
    "register_alias",
    "register_aliases",
    "unregister_alias",
    "list_loaded",
    "list_available",
    "get_module",
    "clear_cache",
    "reset_all",
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
    "reload_mappings",
    "export_aliases",
    "validate_aliases",
    "validate_aliases_importable",
    "get_config_paths",
    "get_config_dirs",
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
    # Symbol resolution
    "set_symbol_preference",
    "get_symbol_preference",
    "clear_symbol_preference",
    "list_symbol_conflicts",
    "set_module_priority",
    "get_module_priority",
    "enable_auto_symbol_resolution",
    "disable_auto_symbol_resolution",
    "get_symbol_resolution_config",
    "get_loaded_modules_context",
    "build_symbol_index_incremental",
    # Auto install
    "enable_auto_install",
    "disable_auto_install",
    "is_auto_install_enabled",
    "install_package",
    "get_auto_install_config",
    "set_pip_index",
    "set_pip_extra_args",
    # Cache API
    "set_cache_config",
    "get_cache_config",
    "get_cache_stats",
    "reset_cache_stats",
    "invalidate_package_cache",
    "get_cache_version",
    # Package version
    "get_package_version",
    "get_all_package_versions",
    "get_laziest_import_version",
    # Incremental index
    "enable_incremental_index",
    "enable_background_build",
    "enable_cache_compression",
    "get_incremental_config",
    "get_preheat_config",
    # Symbol sharding
    "search_with_sharding",
    "enable_sharding",
    "disable_sharding",
    "get_sharding_config",
    "clear_shard_cache",
    # Background index build
    "start_background_index_build",
    "is_index_building",
    "wait_for_index",
    "set_background_timeout",
    "get_background_timeout",
    # Which function
    "which",
    "which_all",
    # RC config
    "load_rc_config",
    "get_rc_value",
    "create_rc_file",
    "get_rc_info",
    "reload_rc_config",
    # Module introspection
    "list_module_symbols",
    "get_module_info",
    "search_in_module",
    # Fun stuff
    "easter_egg",
    "help",
]

# __all__ will be updated after initialization
__all__ = sorted(_BASE_EXPORTS)


# ============== Initialization ==============


def _do_initialize() -> None:
    """Perform module initialization."""
    global _ALIAS_MAP, __all__

    lock = get_init_lock()

    with lock:
        # Use module to access state (avoid value copy issue)
        if _config_module._INITIALIZED:
            return

        if _config_module._INIT_FAILED:
            # Don't retry if previously failed
            raise RuntimeError(
                f"laziest-import initialization previously failed: "
                f"{_config_module._INIT_ERROR}"
            )

        _config_module._INITIALIZING = True
        _config_module._INIT_FAILED = False
        _config_module._INIT_ERROR = None

        try:
            # Load aliases
            from ._alias import _load_all_aliases

            _ALIAS_MAP.update(_load_all_aliases(check_duplicates=True))

            # Init file cache
            from ._cache import _init_file_cache

            _init_file_cache()

            _config_module._INITIALIZED = True

            # Update __all__ to include aliases
            __all__ = sorted(set(_BASE_EXPORTS) | set(_ALIAS_MAP.keys()))

        except Exception as e:
            # Record failure state
            _config_module._INIT_FAILED = True
            _config_module._INIT_ERROR = str(e)
            raise
        finally:
            _config_module._INITIALIZING = False


# ============== Easter Egg & Help ==============


def easter_egg(name: str = "default") -> str:
    """Get a fun Easter egg message!

    Args:
        name: The Easter egg name. Available options:
            - "default": A random fun fact about lazy imports
            - "author": Author's message
            - "quote": A programming quote
            - "tip": A lazy import tip
            - "secret": A secret message (shhh!)
            - "thanks": Special thanks

    Returns:
        A fun message string.

    """
    import random
    from ._config import __version__

    eggs = {
        "default": [
            "[*] Laziest-import: Because typing 'import numpy as np' is so 2020!",
            "[*] Lazy loading: The art of procrastination, but for code!",
            "[*] Did you know? Your imports are now 471x faster on cache load!",
            "[*] Magic? No, it's just smart caching and lazy evaluation!",
            "[*] Hot take: Real programmers don't import until they have to.",
            "[*] This is not an Easter egg...Just kidding.",
            "[*] Do you know? I'm a developer from senior high school, Writing these English sentences is almost using up all my English skills.",
            "[*] Hello world.",
            "[*] You are not using C++, definitely.",
        ],
        "author": [
            """+--------------------------------------------------------------+
|  Hello, intrepid explorer!                                    |
|                                                              |
|  I created laziest-import because I got tired of             |
|  waiting for heavy libraries to load every time I            |
|  started a script. Now, imports are instant!                 |
|                                                              |
|  Hope this little tool saves you as much time as it          |
|  saved me. Happy coding!                                     |
|                                                              |
|  -- Chidc (Author of laziest-import)                         |
+--------------------------------------------------------------+""",
        ],
        "quote": [
            '"The best code is no code at all. The second best is lazy-loaded code." -- Anonymous',
            '"Why import everything when you can import nothing... until you need it?" -- Lazy Philosophy',
            '"In the future, all imports will be lazy, and I will be their prophet." -- Probably Me',
            '"Premature optimization is the root of all evil. Lazy loading is the root of all speed." -- Wise Words',
        ],
        "tip": [
            "[Tip] Use lz.search_symbol('DataFrame') to find where a symbol comes from!",
            "[Tip] lz.get_symbol_cache_info() shows you how many symbols are cached!",
            "[Tip] Enable cache compression with lz.enable_cache_compression() to save disk space!",
            "[Tip] Use lz.clear_symbol_cache() to force a full rebuild of the symbol index!",
            "[Tip] The cache is stored in ~/.laziest_import/ - you can back it up!",
        ],
        "secret": [
            "[Secret] You found the hidden message! There's nothing more here... or is there?",
            "[Secret] The cache version is a lie. Just kidding, it's real. Or is it?",
            "[Secret] If you're reading this, you're probably procrastinating. Get back to coding!",
            "[Secret] There is no secret. But now that you're here, have a great day!",
        ],
        "thanks": [
            """Special Thanks:
            
* Python community for being awesome
* All the library developers whose code we lazily import
* You, for using this package!
* Stack Overflow (we all know why)
* Coffee, the real power behind this project""",
        ],
    }

    if name in eggs:
        messages = eggs[name]
        return random.choice(messages) if len(messages) > 1 else messages[0]
    else:
        # Unknown name, give a hint
        available = ", ".join(f'"{k}"' for k in eggs.keys())
        return f"[?] Unknown easter egg '{name}'. Try one of: {available}"


def help(topic: Optional[str] = None) -> str:
    """Get help on laziest-import topics.

    Args:
        topic: Optional topic to get help on. Available topics:
            - None: General overview
            - "quickstart": Quick start guide
            - "lazy": How lazy imports work
            - "alias": Alias system
            - "symbol": Symbol search
            - "cache": Caching system
            - "config": Configuration options
            - "async": Async imports
            - "hooks": Import hooks
            - "api": Full API reference

    Returns:
        Help text for the requested topic.

    Examples:
        >>> import laziest_import as lz
        >>> print(lz.help())
        >>> print(lz.help("quickstart"))
        >>> print(lz.help("cache"))
    """
    from ._config import __version__

    help_texts = {
        None: f"""+------------------------------------------------------------------+
|              laziest-import v{__version__} - Help Center               |
+------------------------------------------------------------------+
|  The laziest way to import Python modules!                        |
|                                                                   |
|  Quick Start:                                                     |
|    import laziest_import as lz                                    |
|    np = lz.numpy      # Lazy import!                              |
|    pd = lz.pandas     # So lazy!                                  |
|    df = pd.DataFrame() # Now it actually imports                  |
|                                                                   |
|  Available Topics:                                                |
|    help("quickstart") - Quick start guide                         |
|    help("lazy")      - How lazy imports work                      |
|    help("alias")     - Alias system                               |
|    help("symbol")    - Symbol search                              |
|    help("cache")     - Caching system                             |
|    help("config")    - Configuration options                      |
|    help("async")     - Async imports                              |
|    help("hooks")     - Import hooks                               |
|    help("api")       - Full API reference                         |
+-------------------------------------------------------------------+""",
        "quickstart": """Quick Start Guide

Basic Usage:
  import laziest_import as lz
  
  # Lazy import - doesn't actually import until used
  np = lz.numpy
  pd = lz.pandas
  
  # Now numpy is imported (only when you use it)
  arr = np.array([1, 2, 3])
  
Common Patterns:
  # Standard library
  os = lz.os
  json = lz.json
  
  # Third-party
  tf = lz.tensorflow    # tensorflow
  plt = lz.matplotlib.pyplot  # submodules work too!
  
  # Using search
  lz.search_symbol("DataFrame")  # Find where DataFrame lives
  
Tips:
  * Use lz.list_loaded() to see what's imported
  * Use lz.search_symbol() to find symbols
  * First run builds cache (~2s), subsequent runs are instant!
""",
        "lazy": """How Lazy Imports Work

The Magic:
  When you write 'np = lz.numpy', nothing is imported yet!
  The import only happens when you actually USE it:
  
  np = lz.numpy       # No import yet!
  arr = np.array([1]) # NOW numpy is imported
  
How It Works:
  1. Creates a proxy object that looks like the module
  2. Intercepts all attribute access
  3. On first access, performs the real import
  4. Replaces itself with the real module
  
Benefits:
  * Faster startup time
  * Lower memory usage
  * Only import what you need
  * Great for notebooks and scripts
""",
        "alias": """Alias System

Built-in Aliases:
  lz.np    → numpy
  lz.pd    → pandas
  lz.plt   → matplotlib.pyplot
  lz.tf    → tensorflow
  lz.torch → torch
  
Custom Aliases:
  # Register your own
  lz.register_alias("my_np", "numpy")
  my_np = lz.my_np
  
  # Register multiple
  lz.register_aliases({
      "np": "numpy",
      "pd": "pandas"
  })
  
  # Remove alias
  lz.unregister_alias("my_np")
  
List Aliases:
  lz.list_loaded()     # Loaded modules
  lz.list_available()  # All known aliases
""",
        "symbol": """Symbol Search

Find where symbols come from:
  # Find DataFrame
  lz.search_symbol("DataFrame")
  # → Found: pandas.DataFrame
  
  # Find with details
  lz.search_symbol("array", show_all=True)
  
Symbol Resolution:
  # Set preference when multiple modules have same symbol
  lz.set_symbol_preference("array", "numpy")
  
  # List conflicts
  lz.list_symbol_conflicts()
  
Cache Info:
  lz.get_symbol_cache_info()  # See cache stats
  lz.clear_symbol_cache()     # Force rebuild
""",
        "cache": """Caching System

Cache Location:
  ~/.laziest_import/
    ├── stdlib_cache.json.gz
    ├── third_party_cache.json.gz
    └── tracked_packages.json
  
Cache Management:
  lz.enable_file_cache()    # Enable caching
  lz.disable_file_cache()   # Disable caching
  lz.clear_file_cache()     # Clear all caches
  lz.get_file_cache_info()  # Cache info
  
Incremental Updates:
  lz.enable_incremental_index()     # Enable
  lz.get_incremental_config()       # Get config
  
Compression:
  lz.enable_cache_compression()     # Save space
  
Performance:
  * First run: ~2s (builds index)
  * Cached run: ~0.003s (700x faster!)
""",
        "config": """Configuration Options

Debug Mode:
  lz.enable_debug_mode()   # Enable logging
  lz.disable_debug_mode()  # Disable logging
  
Auto Search:
  lz.enable_auto_search()  # Search unknown modules
  lz.disable_auto_search()
  
Retry on Failure:
  lz.enable_retry()        # Retry failed imports
  lz.disable_retry()
  
Cache Settings:
  lz.set_cache_dir(path)   # Custom cache location
  lz.get_cache_dir()       # Get current location
  
Symbol Search:
  lz.enable_symbol_search()
  lz.disable_symbol_search()
  
Auto Install:
  lz.enable_auto_install()  # Auto-install missing
""",
        "async": """Async Imports

Async Import:
  import asyncio
  import laziest_import as lz
  
  async def main():
      # Import asynchronously
      np = await lz.import_async("numpy")
      arr = np.array([1, 2, 3])
  
  asyncio.run(main())
  
Multiple Async:
  async def main():
      modules = await lz.import_multiple_async([
          "numpy",
          "pandas", 
          "matplotlib"
      ])
      np = modules["numpy"]
  
Benefits:
  * Non-blocking imports
  * Concurrent loading
  * Great for web apps
""",
        "hooks": """Import Hooks

Pre-Import Hooks:
  def before_import(module_name):
      print(f"About to import {module_name}")
  
  lz.add_pre_import_hook(before_import)
  
Post-Import Hooks:
  def after_import(module_name, module):
      print(f"Imported {module_name}")
  
  lz.add_post_import_hook(after_import)
  
Remove Hooks:
  lz.remove_pre_import_hook(func)
  lz.remove_post_import_hook(func)
  lz.clear_import_hooks()  # Remove all
  
Use Cases:
  * Logging
  * Profiling
  * Dependency tracking
""",
        "api": """Full API Reference

Basic Imports:
  lz.<module>              # Lazy import
  lz.get_module(name)      # Get loaded module
  
Version Info:
  lz.__version__           # Library version
  lz.get_cache_version()   # Cache version
  lz.get_package_version(name)  # Package version
  
Search:
  lz.search_module(name)   # Search for module
  lz.search_class(name)    # Search for class
  lz.search_symbol(name)   # Search for symbol
  
Cache:
  lz.clear_cache()         # Clear memory cache
  lz.clear_file_cache()    # Clear file cache
  lz.get_file_cache_info() # Cache info
  
Aliases:
  lz.register_alias(a, m)  # Register alias
  lz.unregister_alias(a)   # Remove alias
  lz.list_loaded()         # Loaded modules
  lz.list_available()      # Available aliases
  
Config:
  lz.enable_*() / lz.disable_*()  # Toggle features
  lz.is_*_enabled()               # Check status
""",
    }

    return help_texts.get(
        topic, f"Unknown topic: '{topic}'. Try help() for available topics."
    )


# Run initialization
_do_initialize()
