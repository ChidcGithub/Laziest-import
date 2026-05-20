"""
laziest-import: Automatic Lazy Import Library

Usage:
    from laziest_import import *
    arr = np.array([1, 2, 3])

Or:
    import laziest_import as lz
    arr = lz.np.array([1, 2, 3])
"""

from typing import List, Optional, Any, Union

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
    _SYMBOL_RESOLUTION_CONFIG,
    _SYMBOL_SEARCH_CONFIG,
    _SYMBOL_PREFERENCES,
    _DEBUG_MODE,
    _RESERVED_NAMES,
    _NEGATIVE_CACHE,
    _NEGATIVE_CACHE_LOCK,
    get_init_lock,
    is_initializing,
    is_initialized,
    is_init_failed,
    get_init_error,
    reset_init_state,
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
    get_alias_category,
)

# Import fuzzy matching
from ._fuzzy import (
    _search_module,
    _search_class_in_modules,
    reload_mappings,
    _levenshtein_distance,
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
    # Dependency tree
    DependencyNode,
    DependencyTree,
    dependency_tree,
    print_dependency_tree,
    # Benchmark
    BenchmarkResult,
    BenchmarkReport,
    benchmark,
    benchmark_imports,
    print_benchmark_report,
)

# ═══════════════════════════════════════════════════════════════
#  Import hooks module (module-level convenience API)
# ═══════════════════════════════════════════════════════════════

from ._hooks import (
    add_pre_import_hook,
    add_post_import_hook,
    remove_pre_import_hook,
    remove_post_import_hook,
    clear_import_hooks,
)

# ═══════════════════════════════════════════════════════════════
#  New object-oriented API (recommended)
# ═══════════════════════════════════════════════════════════════

from ._api import (
    # Main class
    LazyImport,
    lz,
    # Namespace classes (for advanced users to inherit/compose)
    ModuleNamespace,
    AliasNamespace,
    SymbolNamespace,
    CacheNamespace,
    ConfigNamespace,
    AnalyzeNamespace,
    ProfileNamespace,
    HookNamespace,
    HookList,
    AsyncNamespace,
    InstallNamespace,
    ExportNamespace,
    BackgroundNamespace,
    VersionNamespace,
    RCConfigNamespace,
    SymbolIndexNamespace,
    SymbolConfigNamespace,
    CacheConfigNamespace,
    CacheSymbolsNamespace,
    CacheFilesNamespace,
    CacheStatsNamespace,
    ConfigContext,
    # Data classes
    AutoInstallConfig,
    RetryConfig,
    SymbolSearchConfig,
    SymbolResolutionConfig,
    CacheConfig,
    ModuleSkipConfig,
)

# ═══════════════════════════════════════════════════════════════
#  Old API backward compatibility layer (deprecated, emits FutureWarning)
# ═══════════════════════════════════════════════════════════════

from ._deprecated import (  # noqa: F401, F403
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
    search_symbol,
    enable_symbol_search,
    disable_symbol_search,
    is_symbol_search_enabled,
    rebuild_symbol_index,
    get_symbol_search_config,
    get_symbol_cache_info,
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
    get_module_skip_config,
    set_module_skip_config,
    search_with_sharding,
    enable_sharding,
    disable_sharding,
    get_sharding_config,
    clear_shard_cache,
    build_symbol_index_incremental,
    set_cache_config,
    get_cache_config,
    get_cache_stats,
    reset_cache_stats,
    invalidate_package_cache,
    clear_symbol_cache,
    enable_cache_compression,
    enable_file_cache,
    disable_file_cache,
    is_file_cache_enabled,
    clear_file_cache,
    get_file_cache_info,
    force_save_cache,
    enable_background_build,
    get_preheat_config,
    enable_incremental_index,
    get_incremental_config,
    get_package_version,
    get_all_package_versions,
    get_laziest_import_version,
    get_cache_version,
    get_config_paths,
    get_config_dirs,
    reload_aliases,
    export_aliases,
    validate_aliases,
    register_alias,
    register_aliases,
    unregister_alias,
    install_package,
    enable_auto_install,
    disable_auto_install,
    is_auto_install_enabled,
    get_auto_install_config,
    set_pip_index,
    set_pip_extra_args,
    rebuild_module_cache,
    import_async,
    import_multiple_async,
    enable_retry,
    disable_retry,
    is_retry_enabled,
    which,
    which_all,
    validate_aliases_importable,
    analyze_file,
    analyze_source,
    analyze_directory,
    dependency_tree,
    print_dependency_tree,
    start_profiling,
    stop_profiling,
    get_profile_report,
    print_profile_report,
    benchmark,
    benchmark_imports,
    print_benchmark_report,
    help,
)


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

    if name in _NEGATIVE_CACHE:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    # 1. Check lazy function registry (symbol, which, help, config, etc.)
    from ._lazy_registry import has as _registry_has, resolve as _registry_resolve

    if _registry_has(name):
        return _registry_resolve(name)

    # 2. Check alias map
    if name in _ALIAS_MAP:
        return _get_lazy_module(name)

    # 3. Try module auto-search
    if _AUTO_SEARCH_ENABLED:
        found = _search_module(name)
        if found:
            _ALIAS_MAP[name] = found
            return _get_lazy_module(name)

    # 4. Try symbol auto-resolution
    if _SYMBOL_RESOLUTION_CONFIG["auto_symbol"] and _initialized:
        from ._symbol import _search_symbol_enhanced

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
                symbol_type=symbol_match.symbol_type,
            )

    # 5. Fall back to interactive symbol search
    if _SYMBOL_SEARCH_CONFIG["enabled"] and _initialized:
        from ._symbol import _handle_symbol_not_found

        found_module = _handle_symbol_not_found(name)
        if found_module:
            return _get_lazy_module(name)

    # Add to negative cache so we don't search again
    with _NEGATIVE_CACHE_LOCK:
        _NEGATIVE_CACHE.add(name)

    # Not found - generate smart suggestion
    msg = f"module '{__name__}' has no attribute '{name}'."

    # Find closest alias by Levenshtein distance
    best_match: Optional[Tuple[str, str, int]] = None
    name_lower = name.lower()
    for alias, module in _ALIAS_MAP.items():
        alias_lower = alias.lower()
        module_lower = module.split(".")[0].lower()
        if alias_lower == name_lower or module_lower == name_lower:
            best_match = (alias, module, 0)
            break
        dist_a = _levenshtein_distance(name_lower, alias_lower)
        dist_m = _levenshtein_distance(name_lower, module_lower)
        min_dist = min(dist_a, dist_m)
        if min_dist == 0:
            best_match = (alias, module, 0)
            break
        threshold = max(1, len(name_lower) // 3)
        if min_dist <= threshold:
            if best_match is None or min_dist < best_match[2]:
                best_match = (alias, module, min_dist)

    if best_match and best_match[2] == 0:
        msg += f" Did you mean `{best_match[1]}`? (alias: `{best_match[0]}`)"
        cat = get_alias_category(best_match[0])
        if cat:
            msg += f", category: {cat}"
    elif best_match:
        msg += f" Did you mean `{best_match[0]}` (→ {best_match[1]})?"
    else:
        popular = [k for k in _ALIAS_MAP if len(k) > 1][:15]
        if popular:
            msg += f" Available: {popular}..."
    raise AttributeError(msg)


# ============== __dir__ for tab completion ==============

# Only names that should appear in __dir__ but NOT in __all__
_DIR_EXTRAS = [
    "set_background_timeout",
    "get_background_timeout",
]


def __dir__() -> List[str]:
    """Return list of public module attributes for tab completion."""
    result = list(_ALIAS_MAP.keys())
    result.extend(_BASE_EXPORTS)
    result.extend(_DIR_EXTRAS)
    return sorted(set(result))


# ============== __all__ for from import * ==============

_BASE_EXPORTS = [
    "__version__",
    "lazy",
    # New API
    "LazyImport",
    "lz",
    "ModuleNamespace",
    "AliasNamespace",
    "SymbolNamespace",
    "CacheNamespace",
    "ConfigNamespace",
    "AnalyzeNamespace",
    "ProfileNamespace",
    "HookNamespace",
    "HookList",
    "AsyncNamespace",
    "InstallNamespace",
    "ExportNamespace",
    "BackgroundNamespace",
    "VersionNamespace",
    "RCConfigNamespace",
    "SymbolIndexNamespace",
    "SymbolConfigNamespace",
    "CacheConfigNamespace",
    "CacheSymbolsNamespace",
    "CacheFilesNamespace",
    "CacheStatsNamespace",
    "ConfigContext",
    "AutoInstallConfig",
    "RetryConfig",
    "SymbolSearchConfig",
    "SymbolResolutionConfig",
    "CacheConfig",
    "ModuleSkipConfig",
    # Data classes
    "ImportStats",
    "SearchResult",
    "SymbolMatch",
    "LazyModule",
    "LazySymbol",
    "LazySubmodule",
    "LazyProxy",
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
    "reload_mappings",
    "export_aliases",
    "validate_aliases",
    "validate_aliases_importable",
    "get_config_paths",
    "get_config_dirs",
    "enable_debug_mode",
    "disable_debug_mode",
    "is_debug_mode",
    "get_import_stats",
    "reset_import_stats",
    "get_init_lock",
    "is_initializing",
    "is_initialized",
    "is_init_failed",
    "get_init_error",
    "reset_init_state",
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
    "get_package_version",
    "get_all_package_versions",
    "get_laziest_import_version",
    "enable_incremental_index",
    "enable_background_build",
    "enable_cache_compression",
    "get_incremental_config",
    "get_preheat_config",
    "search_with_sharding",
    "enable_sharding",
    "disable_sharding",
    "get_sharding_config",
    "clear_shard_cache",
    "start_background_index_build",
    "is_index_building",
    "wait_for_index",
    "set_background_timeout",
    "get_background_timeout",
"which",
     "which_all",
     "load_rc_config",
     "get_rc_value",
     "create_rc_file",
     "get_rc_info",
     "reload_rc_config",
     "list_module_symbols",
     "get_module_info",
     "search_in_module",
     "easter_egg",
     "help",
    "DependencyPreAnalyzer",
    "ImportProfiler",
    "PreAnalysisResult",
    "ModuleProfile",
    "ProfileReport",
    "EnvironmentInfo",
    "start_profiling",
    "stop_profiling",
    "get_profile_report",
    "print_profile_report",
    "show_conflicts",
    "get_conflicts_summary",
    "show_environment",
    "detect_environment",
    "save_preferences",
    "load_preferences",
    "apply_preferences",
    "clear_preferences",
    "analyze_file",
    "analyze_source",
    "analyze_directory",
    # Dependency tree
    "dependency_tree",
    "print_dependency_tree",
    "DependencyNode",
    "DependencyTree",
    # Benchmark
    "benchmark",
    "benchmark_imports",
    "print_benchmark_report",
    "BenchmarkResult",
    "BenchmarkReport",
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

            # Register lazy-loaded functions
            from ._lazy_registry import register as _register_lazy

            _symbol_funcs = [
                "search_symbol", "enable_symbol_search", "disable_symbol_search",
                "is_symbol_search_enabled", "rebuild_symbol_index",
                "get_symbol_search_config", "get_symbol_cache_info",
                "set_symbol_preference", "get_symbol_preference",
                "clear_symbol_preference", "list_symbol_conflicts",
                "set_module_priority", "get_module_priority",
                "enable_auto_symbol_resolution", "disable_auto_symbol_resolution",
                "get_symbol_resolution_config", "get_loaded_modules_context",
                "build_symbol_index_incremental", "search_with_sharding",
                "enable_sharding", "disable_sharding", "get_sharding_config",
                "clear_shard_cache",
            ]
            for _fn in _symbol_funcs:
                _register_lazy(_fn, "laziest_import._symbol")

            _register_lazy("which", "laziest_import._which")
            _register_lazy("which_all", "laziest_import._which")
            _register_lazy("help", "laziest_import._help")

            _bg_funcs = [
                "start_background_index_build", "is_index_building",
                "wait_for_index", "set_background_timeout", "get_background_timeout",
            ]
            for _fn in _bg_funcs:
                _register_lazy(_fn, "laziest_import._lazy_index")

            _rc_funcs = [
                "load_rc_config", "get_rc_value", "create_rc_file",
                "get_rc_info", "reload_rc_config",
            ]
            for _fn in _rc_funcs:
                _register_lazy(_fn, "laziest_import._rcconfig")

            _intro_funcs = [
                "list_module_symbols", "get_module_info", "search_in_module",
            ]
            for _fn in _intro_funcs:
                _register_lazy(_fn, "laziest_import._introspect")

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
