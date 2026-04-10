"""
Public API for symbol search functionality.

This module contains all public-facing API functions for symbol search.
"""

from typing import Dict, List, Optional, Any, Set

from .._config import (
    _DEBUG_MODE,
    _SYMBOL_SEARCH_CONFIG,
    _SYMBOL_CACHE,
    _STDLIB_SYMBOL_CACHE,
    _THIRD_PARTY_SYMBOL_CACHE,
    _CACHE_STATS,
    _CACHE_CONFIG,
    _TRACKED_PACKAGES,
    _CONFIRMED_MAPPINGS,
    _SYMBOL_PREFERENCES,
    _MODULE_PRIORITY,
    _SYMBOL_RESOLUTION_CONFIG,
    _MODULE_SKIP_CONFIG,
    _set_symbol_index_built,
    _set_stdlib_cache_built,
    _set_third_party_cache_built,
)
from .._cache import _get_symbol_index_path
from ._scan import _is_stdlib_module
from ._index import _build_symbol_index
from ._search import (
    search_symbol,
    _search_symbol_enhanced,
    _handle_symbol_not_found,
    _infer_context,
)


# ============== Symbol Search API ==============


def enable_symbol_search(
    interactive: bool = True,
    exact_params: bool = False,
    max_results: int = 5,
    search_depth: int = 1,
    skip_stdlib: bool = False,
) -> None:
    """Enable symbol search functionality."""
    _SYMBOL_SEARCH_CONFIG["enabled"] = True
    _SYMBOL_SEARCH_CONFIG["interactive"] = interactive
    _SYMBOL_SEARCH_CONFIG["exact_params"] = exact_params
    _SYMBOL_SEARCH_CONFIG["max_results"] = max_results
    _SYMBOL_SEARCH_CONFIG["search_depth"] = search_depth
    _SYMBOL_SEARCH_CONFIG["skip_stdlib"] = skip_stdlib


def disable_symbol_search() -> None:
    """Disable symbol search functionality."""
    _SYMBOL_SEARCH_CONFIG["enabled"] = False


def is_symbol_search_enabled() -> bool:
    """Check if symbol search is enabled."""
    return _SYMBOL_SEARCH_CONFIG["enabled"]


def rebuild_symbol_index() -> None:
    """Rebuild the symbol index."""
    import laziest_import._config as config
    
    _SYMBOL_CACHE.clear()
    _STDLIB_SYMBOL_CACHE.clear()
    _THIRD_PARTY_SYMBOL_CACHE.clear()
    _set_symbol_index_built(False)
    _set_stdlib_cache_built(False)
    _set_third_party_cache_built(False)

    for cache_type in ["stdlib", "third_party", "all"]:
        cache_path = _get_symbol_index_path(cache_type)
        if cache_path.exists():
            cache_path.unlink()

    _build_symbol_index(force=True)


def get_symbol_search_config() -> Dict[str, Any]:
    """Get current symbol search configuration."""
    return dict(_SYMBOL_SEARCH_CONFIG)


def get_symbol_cache_info() -> Dict[str, Any]:
    """Get information about the symbol cache."""
    import laziest_import._config as config

    return {
        "built": config._SYMBOL_INDEX_BUILT,
        "symbol_count": len(_SYMBOL_CACHE),
        "stdlib_symbols": len(_STDLIB_SYMBOL_CACHE),
        "third_party_symbols": len(_THIRD_PARTY_SYMBOL_CACHE),
        "stdlib_built": config._STDLIB_CACHE_BUILT,
        "third_party_built": config._THIRD_PARTY_CACHE_BUILT,
        "confirmed_mappings": len(_CONFIRMED_MAPPINGS),
        "tracked_packages": len(_TRACKED_PACKAGES),
        "cache_stats": dict(_CACHE_STATS),
        "cache_config": dict(_CACHE_CONFIG),
    }


# ============== Symbol Resolution API ==============


def set_symbol_preference(symbol: str, module: str) -> None:
    """Set a preference for symbol resolution."""
    _SYMBOL_PREFERENCES[symbol] = module
    if _DEBUG_MODE:
        import logging
        logging.debug(f"[laziest-import] Set symbol preference: {symbol} -> {module}")


def get_symbol_preference(symbol: str) -> Optional[str]:
    """Get the preferred module for a symbol."""
    return _SYMBOL_PREFERENCES.get(symbol)


def clear_symbol_preference(symbol: str) -> bool:
    """Clear a symbol preference."""
    if symbol in _SYMBOL_PREFERENCES:
        del _SYMBOL_PREFERENCES[symbol]
        return True
    return False


def list_symbol_conflicts(symbol: str) -> List[Dict[str, Any]]:
    """List all modules that export a symbol."""
    import laziest_import._config as config
    
    if not config._SYMBOL_INDEX_BUILT:
        _build_symbol_index()

    if symbol not in _SYMBOL_CACHE:
        return []

    return [
        {
            "module": loc[0],
            "type": loc[1],
            "signature": loc[2],
            "priority": _MODULE_PRIORITY.get(loc[0].split(".")[0], 50),
        }
        for loc in _SYMBOL_CACHE[symbol]
    ]


def set_module_priority(module: str, priority: int) -> None:
    """Set priority for a module (higher = more preferred)."""
    _MODULE_PRIORITY[module] = priority


def get_module_priority(module: str) -> int:
    """Get the priority for a module."""
    return _MODULE_PRIORITY.get(module, 50)


def enable_auto_symbol_resolution(
    auto_threshold: float = 0.7,
    conflict_threshold: float = 0.3,
    warn_on_conflict: bool = True,
) -> None:
    """Enable automatic symbol resolution."""
    _SYMBOL_RESOLUTION_CONFIG["auto_symbol"] = True
    _SYMBOL_RESOLUTION_CONFIG["auto_threshold"] = auto_threshold
    _SYMBOL_RESOLUTION_CONFIG["conflict_threshold"] = conflict_threshold
    _SYMBOL_RESOLUTION_CONFIG["warn_on_conflict"] = warn_on_conflict


def disable_auto_symbol_resolution() -> None:
    """Disable automatic symbol resolution."""
    _SYMBOL_RESOLUTION_CONFIG["auto_symbol"] = False


def get_symbol_resolution_config() -> Dict[str, Any]:
    """Get symbol resolution configuration."""
    return dict(_SYMBOL_RESOLUTION_CONFIG)


def get_loaded_modules_context() -> Set[str]:
    """Get the set of currently loaded module names."""
    return _infer_context()


# ============== Module Skip Configuration API ==============


def get_module_skip_config() -> Dict[str, Any]:
    """Get current module skip configuration."""
    return dict(_MODULE_SKIP_CONFIG)


def set_module_skip_config(
    skip_test_modules: Optional[bool] = None,
    skip_internal_modules: Optional[bool] = None,
    skip_large_modules: Optional[bool] = None,
    large_module_threshold: Optional[int] = None,
) -> None:
    """Configure module skip settings."""
    if skip_test_modules is not None:
        _MODULE_SKIP_CONFIG["skip_test_modules"] = skip_test_modules
    if skip_internal_modules is not None:
        _MODULE_SKIP_CONFIG["skip_internal_modules"] = skip_internal_modules
    if skip_large_modules is not None:
        _MODULE_SKIP_CONFIG["skip_large_modules"] = skip_large_modules
    if large_module_threshold is not None:
        _MODULE_SKIP_CONFIG["large_module_threshold"] = large_module_threshold
