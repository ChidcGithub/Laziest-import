"""
laziest-import: Automatic Lazy Import Library

Usage:
    from laziest_import import *
    arr = np.array([1, 2, 3])

Or:
    import laziest_import as lz
    arr = lz.np.array([1, 2, 3])
"""

from typing import Dict, List, Optional, Any, Union

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

# Import config module for state access
from . import _config as _config_module
from ._config import (
    _AUTO_SEARCH_ENABLED,
    _ALIAS_MAP,
    _LAZY_MODULES,
    _SYMBOL_RESOLUTION_CONFIG,
    _SYMBOL_SEARCH_CONFIG,
    _DEBUG_MODE,
    _RESERVED_NAMES,
    get_init_lock,
    is_initializing,
    is_initialized,
    is_init_failed,
    get_init_error,
    _PRE_IMPORT_HOOKS,
    _POST_IMPORT_HOOKS,
    _IMPORT_STATS,
    _CACHE_STATS,
)

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
    get_package_version,
    get_all_package_versions,
    get_laziest_import_version,
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

# Import analysis and profiling tools
from ._analysis import (
    DependencyPreAnalyzer,
    ImportProfiler,
    PreAnalysisResult,
    ModuleProfile,
    ProfileReport,
    EnvironmentInfo,
    start_profiling,
    stop_profiling,
    get_profile_report,
    print_profile_report,
    find_symbol_conflicts,
    show_conflicts,
    get_conflicts_summary,
    detect_environment,
    show_environment,
    save_preferences,
    load_preferences,
    apply_preferences,
    clear_preferences,
)

# Import public API functions
from ._public_api import (
    list_loaded,
    list_available,
    get_module,
    clear_cache,
    reset_all,
    get_version,
    reload_module,
    enable_auto_search,
    disable_auto_search,
    is_auto_search_enabled,
    search_module,
    search_class,
    enable_debug_mode,
    disable_debug_mode,
    is_debug_mode,
    get_import_stats,
    reset_import_stats,
    validate_aliases_importable,
)


# ============== Hook API ==============


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


# ============== Analysis Convenience Functions ==============

_analyzer: Optional[DependencyPreAnalyzer] = None


def _get_analyzer() -> DependencyPreAnalyzer:
    """Get or create the global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = DependencyPreAnalyzer()
    return _analyzer


def analyze_file(file_path: str) -> PreAnalysisResult:
    """Analyze a Python file to predict required imports."""
    return _get_analyzer().analyze_file(file_path)


def analyze_source(source: str, file_path: str = "<string>") -> PreAnalysisResult:
    """Analyze source code to predict required imports."""
    return _get_analyzer().analyze_source(source, file_path)


def analyze_directory(
    dir_path: str, 
    recursive: bool = True,
    exclude: Optional[set] = None
) -> List[PreAnalysisResult]:
    """Analyze all Python files in a directory."""
    return _get_analyzer().analyze_directory(dir_path, recursive, exclude)


# ============== Lazy Loading Helpers ==============

_SYMBOL_FUNCTIONS: Dict[str, Any] = {}


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

    _SYMBOL_FUNCTIONS.update({
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
    })


# ============== Module-level __getattr__ ==============


def __getattr__(name: str) -> Union[LazyModule, LazySymbol, Any]:
    """Module-level attribute access hook for lazy loading."""
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

    # 8. Try module auto-search
    if _AUTO_SEARCH_ENABLED:
        found = _search_module(name)
        if found:
            _ALIAS_MAP[name] = found
            return _get_lazy_module(name)

    # 9. Try symbol auto-resolution
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

    # 10. Fall back to interactive symbol search
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


# ============== __dir__ for tab completion ==============

_DIR_NAMES = [
    "__version__", "lazy", "register_alias", "register_aliases", "unregister_alias",
    "list_loaded", "list_available", "get_module", "clear_cache", "reset_all",
    "get_version", "reload_module", "enable_auto_search", "disable_auto_search",
    "is_auto_search_enabled", "search_module", "search_class", "rebuild_module_cache",
    "reload_aliases", "export_aliases", "validate_aliases", "get_config_paths",
    "get_config_dirs", "enable_debug_mode", "disable_debug_mode", "is_debug_mode",
    "get_import_stats", "reset_import_stats", "add_pre_import_hook", "add_post_import_hook",
    "remove_pre_import_hook", "remove_post_import_hook", "clear_import_hooks",
    "import_async", "import_multiple_async", "enable_retry", "disable_retry",
    "is_retry_enabled", "enable_file_cache", "disable_file_cache", "is_file_cache_enabled",
    "clear_file_cache", "get_file_cache_info", "force_save_cache", "set_cache_dir",
    "get_cache_dir", "reset_cache_dir", "enable_symbol_search", "disable_symbol_search",
    "is_symbol_search_enabled", "search_symbol", "rebuild_symbol_index",
    "get_symbol_search_config", "get_symbol_cache_info", "clear_symbol_cache",
    "set_symbol_preference", "get_symbol_preference", "clear_symbol_preference",
    "list_symbol_conflicts", "set_module_priority", "get_module_priority",
    "enable_auto_symbol_resolution", "disable_auto_symbol_resolution",
    "get_symbol_resolution_config", "get_loaded_modules_context",
    "build_symbol_index_incremental", "enable_auto_install", "disable_auto_install",
    "is_auto_install_enabled", "install_package", "get_auto_install_config",
    "set_pip_index", "set_pip_extra_args", "set_cache_config", "get_cache_config",
    "get_cache_stats", "reset_cache_stats", "invalidate_package_cache", "get_cache_version",
    "get_package_version", "get_all_package_versions", "get_laziest_import_version",
    "enable_incremental_index", "enable_background_build", "enable_cache_compression",
    "get_incremental_config", "get_preheat_config", "search_with_sharding",
    "enable_sharding", "disable_sharding", "get_sharding_config", "clear_shard_cache",
    "start_background_index_build", "is_index_building", "wait_for_index",
    "which", "which_all", "help", "DependencyPreAnalyzer", "ImportProfiler",
    "analyze_file", "analyze_source", "analyze_directory", "start_profiling",
    "stop_profiling", "get_profile_report", "print_profile_report", "show_conflicts",
    "get_conflicts_summary", "show_environment", "detect_environment",
    "save_preferences", "load_preferences", "apply_preferences", "clear_preferences",
]


def __dir__() -> List[str]:
    """Return list of public module attributes for tab completion."""
    result = list(_ALIAS_MAP.keys())
    result.extend(_DIR_NAMES)
    return sorted(result)


# ============== __all__ for from import * ==============

_BASE_EXPORTS = [
    "__version__", "lazy", "ImportStats", "SearchResult", "SymbolMatch",
    "LazyModule", "LazySymbol", "LazySubmodule", "LazyProxy",
    "register_alias", "register_aliases", "unregister_alias",
    "list_loaded", "list_available", "get_module", "clear_cache", "reset_all",
    "get_version", "reload_module", "enable_auto_search", "disable_auto_search",
    "is_auto_search_enabled", "search_module", "search_class", "rebuild_module_cache",
    "reload_aliases", "reload_mappings", "export_aliases", "validate_aliases",
    "validate_aliases_importable", "get_config_paths", "get_config_dirs",
    "enable_debug_mode", "disable_debug_mode", "is_debug_mode",
    "get_import_stats", "reset_import_stats",
    "add_pre_import_hook", "add_post_import_hook",
    "remove_pre_import_hook", "remove_post_import_hook", "clear_import_hooks",
    "import_async", "import_multiple_async", "enable_retry", "disable_retry",
    "is_retry_enabled", "enable_file_cache", "disable_file_cache",
    "is_file_cache_enabled", "clear_file_cache", "get_file_cache_info",
    "force_save_cache", "set_cache_dir", "get_cache_dir", "reset_cache_dir",
    "enable_symbol_search", "disable_symbol_search", "is_symbol_search_enabled",
    "search_symbol", "rebuild_symbol_index", "get_symbol_search_config",
    "get_symbol_cache_info", "clear_symbol_cache",
    "set_symbol_preference", "get_symbol_preference", "clear_symbol_preference",
    "list_symbol_conflicts", "set_module_priority", "get_module_priority",
    "enable_auto_symbol_resolution", "disable_auto_symbol_resolution",
    "get_symbol_resolution_config", "get_loaded_modules_context",
    "build_symbol_index_incremental",
    "enable_auto_install", "disable_auto_install", "is_auto_install_enabled",
    "install_package", "get_auto_install_config", "set_pip_index", "set_pip_extra_args",
    "set_cache_config", "get_cache_config", "get_cache_stats", "reset_cache_stats",
    "invalidate_package_cache", "get_cache_version",
    "get_package_version", "get_all_package_versions", "get_laziest_import_version",
    "enable_incremental_index", "enable_background_build", "enable_cache_compression",
    "get_incremental_config", "get_preheat_config",
    "search_with_sharding", "enable_sharding", "disable_sharding",
    "get_sharding_config", "clear_shard_cache",
    "start_background_index_build", "is_index_building", "wait_for_index",
    "set_background_timeout", "get_background_timeout",
    "which", "which_all",
    "load_rc_config", "get_rc_value", "create_rc_file", "get_rc_info", "reload_rc_config",
    "list_module_symbols", "get_module_info", "search_in_module",
    "easter_egg", "help",
    "DependencyPreAnalyzer", "ImportProfiler", "PreAnalysisResult",
    "ModuleProfile", "ProfileReport", "EnvironmentInfo",
    "start_profiling", "stop_profiling", "get_profile_report", "print_profile_report",
    "show_conflicts", "get_conflicts_summary", "show_environment", "detect_environment",
    "save_preferences", "load_preferences", "apply_preferences", "clear_preferences",
]

__all__ = sorted(_BASE_EXPORTS)


# ============== Initialization ==============


def _do_initialize() -> None:
    """Perform module initialization."""
    global _ALIAS_MAP, __all__

    lock = get_init_lock()

    with lock:
        if _config_module._INITIALIZED:
            return

        if _config_module._INIT_FAILED:
            raise RuntimeError(
                f"laziest-import initialization previously failed: "
                f"{_config_module._INIT_ERROR}"
            )

        _config_module._INITIALIZING = True
        _config_module._INIT_FAILED = False
        _config_module._INIT_ERROR = None

        try:
            from ._alias import _load_all_aliases
            _ALIAS_MAP.update(_load_all_aliases(check_duplicates=True))

            from ._cache import _init_file_cache
            _init_file_cache()

            _config_module._INITIALIZED = True
            __all__ = sorted(set(_BASE_EXPORTS) | set(_ALIAS_MAP.keys()))

        except Exception as e:
            _config_module._INIT_FAILED = True
            _config_module._INIT_ERROR = str(e)
            raise
        finally:
            _config_module._INITIALIZING = False


# ============== Easter Egg & Help ==============


def easter_egg(name: str = "default") -> str:
    """Get a fun Easter egg message!"""
    import random

    eggs = {
        "default": [
            "[*] Laziest-import: Because typing 'import numpy as np' is so 2020!",
            "[*] Lazy loading: The art of procrastination, but for code!",
            "[*] Did you know? Your imports are now 471x faster on cache load!",
            "[*] Magic? No, it's just smart caching and lazy evaluation!",
            "[*] Hot take: Real programmers don't import until they have to.",
        ],
        "author": ["Hello from the author of laziest-import! -- Chidc"],
        "quote": [
            '"The best code is no code at all." -- Anonymous',
            '"Why import everything when you can import nothing?" -- Lazy Philosophy',
        ],
        "tip": [
            "[Tip] Use lz.search_symbol('DataFrame') to find where a symbol comes from!",
            "[Tip] lz.get_symbol_cache_info() shows you how many symbols are cached!",
        ],
        "secret": ["[Secret] You found the hidden message!"],
        "thanks": ["Special thanks to the Python community!"],
    }

    if name in eggs:
        messages = eggs[name]
        return random.choice(messages) if len(messages) > 1 else messages[0]
    else:
        available = ", ".join(f'"{k}"' for k in eggs.keys())
        return f"[?] Unknown easter egg '{name}'. Try one of: {available}"


def help(topic: Optional[str] = None) -> str:
    """Get help on laziest-import topics."""
    from ._help import help as _help_func
    return _help_func(topic)


# Run initialization
_do_initialize()