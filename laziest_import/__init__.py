"""
laziest-import: Automatic Lazy Import Library

Usage:
    from laziest_import import *
    arr = np.array([1, 2, 3])

Or:
    import laziest_import as lz
    arr = lz.np.array([1, 2, 3])
"""
# ruff: noqa: F401  # noqa: RUF100 — legitimately suppresses 163 F401 re-export warnings
# The imports in this file intentionally re-export the public API;
# names are exposed via __all__ and __dir__.

import time
from typing import Any, Optional, Union

# Import config module for state access
from . import _config as _config_module

# Import alias functionality
from ._alias import (
    export_aliases,
    get_alias_category,
    get_config_dirs,
    get_config_paths,
    register_alias,
    register_aliases,
    reload_aliases,
    unregister_alias,
    validate_aliases,
)

# Import analysis and profiling tools
from ._analysis import (
    BenchmarkReport,
    # Benchmark
    BenchmarkResult,
    # Dependency tree
    DependencyNode,
    DependencyPreAnalyzer,
    DependencyTree,
    EnvironmentInfo,
    ImportProfiler,
    ModuleProfile,
    PreAnalysisResult,
    ProfileReport,
    apply_preferences,
    benchmark,
    benchmark_imports,
    clear_preferences,
    dependency_tree,
    detect_environment,
    find_symbol_conflicts,
    get_conflicts_summary,
    get_profile_report,
    load_preferences,
    print_benchmark_report,
    print_dependency_tree,
    print_profile_report,
    save_preferences,
    show_conflicts,
    show_environment,
    start_profiling,
    stop_profiling,
)

# ═══════════════════════════════════════════════════════════════
#  New object-oriented API (recommended)
# ═══════════════════════════════════════════════════════════════
from ._api import (
    AliasNamespace,
    AnalyzeNamespace,
    AsyncNamespace,
    # Data classes
    AutoInstallConfig,
    BackgroundNamespace,
    CacheConfig,
    CacheConfigNamespace,
    CacheFilesNamespace,
    CacheNamespace,
    CacheStatsNamespace,
    CacheSymbolsNamespace,
    ConfigContext,
    ConfigNamespace,
    ExportNamespace,
    HookList,
    HookNamespace,
    InstallNamespace,
    # Main class
    LazyImport,
    # Namespace classes (for advanced users to inherit/compose)
    ModuleNamespace,
    ModuleSkipConfig,
    ProfileNamespace,
    RCConfigNamespace,
    RetryConfig,
    SymbolConfigNamespace,
    SymbolIndexNamespace,
    SymbolNamespace,
    SymbolResolutionConfig,
    SymbolSearchConfig,
    VersionNamespace,
    lz,
)

# Import async operations
from ._async_ops import (
    disable_retry,
    enable_retry,
    import_async,
    import_multiple_async,
    is_retry_enabled,
)

# Import cache functionality
from ._cache import (
    clear_file_cache,
    clear_symbol_cache,
    disable_file_cache,
    enable_background_build,
    enable_cache_compression,
    enable_file_cache,
    enable_incremental_index,
    force_save_cache,
    get_all_package_versions,
    get_cache_config,
    get_cache_dir,
    get_cache_stats,
    get_cache_version,
    get_file_cache_info,
    get_incremental_config,
    get_laziest_import_version,
    get_package_version,
    get_preheat_config,
    invalidate_package_cache,
    is_file_cache_enabled,
    reset_cache_dir,
    reset_cache_stats,
    set_cache_config,
    set_cache_dir,
)

# Import version
# Import data classes
from ._config import (
    _ALIAS_MAP,
    _AUTO_SEARCH_ENABLED,
    _DEBUG_MODE,
    _NEGATIVE_CACHE,
    _NEGATIVE_CACHE_LOCK,
    _NEGATIVE_CACHE_TTL,
    _RESERVED_NAMES,
    _SYMBOL_PREFERENCES,
    _SYMBOL_RESOLUTION_CONFIG,
    _SYMBOL_SEARCH_CONFIG,
    ImportStats,
    SearchResult,
    SymbolMatch,
    __version__,
    get_init_error,
    get_init_lock,
    is_init_failed,
    is_initialized,
    is_initializing,
    reset_init_state,
)

# Names that should resolve to the object-oriented API namespaces on the global
# LazyImport instance, rather than being treated as aliases or auto-searched modules.
_API_NAMESPACE_NAMES: frozenset[str] = frozenset(
    {
        "module",
        "alias",
        "symbol",
        "cache",
        "config",
        "analyze",
        "profile",
        "hooks",
        "async_",
        "install",
        "export",
        "background",
        "version",
        "rc",
    }
)

# ═══════════════════════════════════════════════════════════════
#  Old API backward compatibility layer (deprecated, emits FutureWarning)
# ═══════════════════════════════════════════════════════════════
from ._deprecated import (
    analyze_directory,
    analyze_file,
    analyze_source,
    benchmark,
    benchmark_imports,
    build_symbol_index_incremental,
    clear_cache,
    clear_file_cache,
    clear_shard_cache,
    clear_symbol_cache,
    clear_symbol_preference,
    dependency_tree,
    disable_auto_install,
    disable_auto_search,
    disable_auto_symbol_resolution,
    disable_debug_mode,
    disable_file_cache,
    disable_retry,
    disable_sharding,
    disable_symbol_search,
    enable_auto_install,
    enable_auto_search,
    enable_auto_symbol_resolution,
    enable_background_build,
    enable_cache_compression,
    enable_debug_mode,
    enable_file_cache,
    enable_incremental_index,
    enable_retry,
    enable_sharding,
    enable_symbol_search,
    export_aliases,
    force_save_cache,
    get_all_package_versions,
    get_auto_install_config,
    get_cache_config,
    get_cache_stats,
    get_cache_version,
    get_config_dirs,
    get_config_paths,
    get_file_cache_info,
    get_import_stats,
    get_incremental_config,
    get_laziest_import_version,
    get_loaded_modules_context,
    get_module,
    get_module_priority,
    get_module_skip_config,
    get_package_version,
    get_preheat_config,
    get_profile_report,
    get_sharding_config,
    get_symbol_cache_info,
    get_symbol_preference,
    get_symbol_resolution_config,
    get_symbol_search_config,
    get_version,
    import_async,
    import_multiple_async,
    install_package,
    invalidate_package_cache,
    is_auto_install_enabled,
    is_auto_search_enabled,
    is_debug_mode,
    is_file_cache_enabled,
    is_retry_enabled,
    is_symbol_search_enabled,
    list_available,
    list_loaded,
    list_symbol_conflicts,
    print_benchmark_report,
    print_dependency_tree,
    print_profile_report,
    rebuild_module_cache,
    rebuild_symbol_index,
    register_alias,
    register_aliases,
    reload_aliases,
    reload_module,
    reset_all,
    reset_cache_stats,
    reset_import_stats,
    search_class,
    search_module,
    search_symbol,
    search_with_sharding,
    set_cache_config,
    set_module_priority,
    set_module_skip_config,
    set_pip_extra_args,
    set_pip_index,
    set_symbol_preference,
    start_profiling,
    stop_profiling,
    unregister_alias,
    validate_aliases,
    validate_aliases_importable,
    which,
    which_all,
)

# Import fuzzy matching
from ._fuzzy import (
    _levenshtein_distance,
    _search_class_in_modules,
    _search_module,
    reload_mappings,
)

# ═══════════════════════════════════════════════════════════════
#  Import hooks module (module-level convenience API)
# ═══════════════════════════════════════════════════════════════
from ._hooks import (
    add_post_import_hook,
    add_pre_import_hook,
    clear_import_hooks,
    remove_post_import_hook,
    remove_pre_import_hook,
)

# Import proxy classes
from ._proxy import (
    LazyModule,
    LazyProxy,
    LazySubmodule,
    LazySymbol,
    _get_lazy_module,
    lazy,
)

# ============== Module-level __getattr__ ==============


def _check_init_access(name: str) -> bool:
    """Check initialization state and raise if not ready. Returns True if initialization OK."""
    _initializing = is_initializing()
    _initialized = is_initialized()

    if _initializing and not _initialized:
        raise AttributeError(
            f"module '{__name__}' is still initializing, cannot access '{name}' yet."
        )

    if is_init_failed():
        raise AttributeError(
            f"module '{__name__}' failed to initialize: {get_init_error()}. Cannot access '{name}'."
        )

    if name in _RESERVED_NAMES:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    with _NEGATIVE_CACHE_LOCK:
        if name in _NEGATIVE_CACHE:
            _ts = _NEGATIVE_CACHE[name]
            if time.time() - _ts < _NEGATIVE_CACHE_TTL:
                raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
            del _NEGATIVE_CACHE[name]

    return _initialized


def _build_attr_error_msg(name: str) -> str:
    """Build a descriptive error message with suggestions for an unknown attribute."""
    msg = f"module '{__name__}' has no attribute '{name}'."
    best_match: Optional[tuple[str, str, int]] = None
    name_lower = name.lower()
    for alias, module in _ALIAS_MAP.items():
        alias_lower = alias.lower()
        module_lower = module.split(".", 1)[0].lower()
        if name_lower in (alias_lower, module_lower):
            best_match = (alias, module, 0)
            break
        dist_a = _levenshtein_distance(name_lower, alias_lower)
        dist_m = _levenshtein_distance(name_lower, module_lower)
        min_dist = min(dist_a, dist_m)
        if min_dist == 0:
            best_match = (alias, module, 0)
            break
        threshold = max(1, len(name_lower) // 3)
        if min_dist <= threshold and (best_match is None or min_dist < best_match[2]):
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
    return msg


def __getattr__(name: str) -> Union[LazyModule, LazySubmodule, LazyProxy, LazySymbol, Any]:
    """Module-level attribute access hook for lazy loading."""
    _initialized = _check_init_access(name)

    # 1. Check lazy function registry (symbol, which, help, config, etc.)
    from ._lazy_registry import has as _registry_has
    from ._lazy_registry import resolve as _registry_resolve

    if _registry_has(name):
        return _registry_resolve(name)

    # 2. Check API namespaces on the global LazyImport instance
    if name in _API_NAMESPACE_NAMES:
        return getattr(lz, name)

    # 3. Check alias map
    if name in _ALIAS_MAP:
        return _get_lazy_module(name)

    # 4. Try module auto-search
    if _AUTO_SEARCH_ENABLED:
        found = _search_module(name)
        if found:
            _ALIAS_MAP[name] = found
            return _get_lazy_module(name)

    # 5. Try symbol auto-resolution
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

    # 6. Fall back to interactive symbol search
    if _SYMBOL_SEARCH_CONFIG["enabled"] and _initialized:
        from ._symbol import _handle_symbol_not_found

        found_module = _handle_symbol_not_found(name)
        if found_module:
            return _get_lazy_module(name)

    # Add to negative cache so we don't search again
    with _NEGATIVE_CACHE_LOCK:
        _NEGATIVE_CACHE[name] = time.time()

    raise AttributeError(_build_attr_error_msg(name))


# ============== __dir__ for tab completion ==============

# Names available via deprecated import path (still work with FutureWarning)
_OLD_API_NAMES = [
    "list_loaded",
    "list_available",
    "get_module",
    "clear_cache",
    "get_version",
    "reload_module",
    "enable_auto_search",
    "disable_auto_search",
    "is_auto_search_enabled",
    "search_module",
    "search_class",
    "enable_debug_mode",
    "disable_debug_mode",
    "is_debug_mode",
    "get_import_stats",
    "reset_import_stats",
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
    "search_with_sharding",
    "enable_sharding",
    "disable_sharding",
    "get_sharding_config",
    "clear_shard_cache",
    "build_symbol_index_incremental",
    "enable_incremental_index",
    "enable_background_build",
    "enable_cache_compression",
    "get_incremental_config",
    "get_preheat_config",
    "set_cache_config",
    "get_cache_config",
    "get_cache_stats",
    "reset_cache_stats",
    "invalidate_package_cache",
    "enable_file_cache",
    "disable_file_cache",
    "is_file_cache_enabled",
    "clear_file_cache",
    "get_file_cache_info",
    "force_save_cache",
    "set_cache_dir",
    "get_cache_dir",
    "reset_cache_dir",
    "get_package_version",
    "get_all_package_versions",
    "get_laziest_import_version",
    "get_cache_version",
    "reload_aliases",
    "export_aliases",
    "validate_aliases",
    "install_package",
    "rebuild_module_cache",
    "enable_auto_install",
    "disable_auto_install",
    "is_auto_install_enabled",
    "get_auto_install_config",
    "set_pip_index",
    "set_pip_extra_args",
    "import_async",
    "import_multiple_async",
    "enable_retry",
    "disable_retry",
    "is_retry_enabled",
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
    "start_profiling",
    "stop_profiling",
    "get_profile_report",
    "print_profile_report",
    "analyze_file",
    "analyze_source",
    "analyze_directory",
    "save_preferences",
    "load_preferences",
    "apply_preferences",
    "clear_preferences",
    "start_background_index_build",
    "is_index_building",
    "wait_for_index",
    "set_background_timeout",
    "get_background_timeout",
]


def __dir__() -> list[str]:
    """Return list of public module attributes for tab completion."""
    result = list(_ALIAS_MAP.keys())
    result.extend(_BASE_EXPORTS)
    result.extend(_OLD_API_NAMES)
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
    # Non-deprecated utility functions
    "register_alias",
    "register_aliases",
    "unregister_alias",
    "reload_aliases",
    "export_aliases",
    "validate_aliases",
    "validate_aliases_importable",
    "get_alias_category",
    "get_config_paths",
    "get_config_dirs",
    "reset_all",
    "reload_mappings",
    "help",
    "easter_egg",
    "add_pre_import_hook",
    "add_post_import_hook",
    "remove_pre_import_hook",
    "remove_post_import_hook",
    "clear_import_hooks",
    "is_initializing",
    "is_initialized",
    "is_init_failed",
    "get_init_error",
    "get_init_lock",
    "reset_init_state",
    "find_symbol_conflicts",
    "show_conflicts",
    "get_conflicts_summary",
    "detect_environment",
    "show_environment",
    "DependencyPreAnalyzer",
    "ImportProfiler",
    "PreAnalysisResult",
    "ModuleProfile",
    "ProfileReport",
    "EnvironmentInfo",
    "DependencyNode",
    "DependencyTree",
    "dependency_tree",
    "print_dependency_tree",
    "BenchmarkResult",
    "BenchmarkReport",
    "benchmark",
    "benchmark_imports",
    "print_benchmark_report",
]

__all__ = sorted(_BASE_EXPORTS)

# Keep deprecated functional API in __all__ for backward compat (will remove in v0.2)
__all__ = sorted(set(_BASE_EXPORTS) | set(_OLD_API_NAMES))


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
                f"laziest-import initialization previously failed: {_config_module._INIT_ERROR}"
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
                "search_symbol",
                "enable_symbol_search",
                "disable_symbol_search",
                "is_symbol_search_enabled",
                "rebuild_symbol_index",
                "get_symbol_search_config",
                "get_symbol_cache_info",
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
                "search_with_sharding",
                "enable_sharding",
                "disable_sharding",
                "get_sharding_config",
                "clear_shard_cache",
            ]
            for _fn in _symbol_funcs:
                _register_lazy(_fn, "laziest_import._symbol")

            _register_lazy("which", "laziest_import._which")
            _register_lazy("which_all", "laziest_import._which")
            _register_lazy("help", "laziest_import._help")

            _bg_funcs = [
                "start_background_index_build",
                "is_index_building",
                "wait_for_index",
                "set_background_timeout",
                "get_background_timeout",
            ]
            for _fn in _bg_funcs:
                _register_lazy(_fn, "laziest_import._lazy_index")

            _rc_funcs = [
                "load_rc_config",
                "get_rc_value",
                "create_rc_file",
                "get_rc_info",
                "reload_rc_config",
            ]
            for _fn in _rc_funcs:
                _register_lazy(_fn, "laziest_import._rcconfig")

            _intro_funcs = [
                "list_module_symbols",
                "get_module_info",
                "search_in_module",
            ]
            for _fn in _intro_funcs:
                _register_lazy(_fn, "laziest_import._introspect")

            _config_module._INITIALIZED = True
            __all__ = sorted(set(_BASE_EXPORTS) | set(_OLD_API_NAMES) | set(_ALIAS_MAP.keys()))

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
        available = ", ".join(f'"{k}"' for k in eggs)
        return f"[?] Unknown easter egg '{name}'. Try one of: {available}"


def help(topic: Optional[str] = None) -> str:
    """Get help on laziest-import topics."""
    from ._help import help as _help_func

    return _help_func(topic)


# Run initialization
_do_initialize()
