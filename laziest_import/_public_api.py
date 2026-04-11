"""
Public API functions for laziest-import.

This module contains the main public API functions.
"""

from typing import Dict, List, Optional, Any
import importlib

from ._config import (
    _LAZY_MODULES,
    _ALIAS_MAP,
    _PRE_IMPORT_HOOKS,
    _POST_IMPORT_HOOKS,
    _IMPORT_STATS,
    ImportStats,
)
# Import config module directly to modify its global variables
from . import _config
from ._proxy import _get_lazy_module
from ._fuzzy import _search_module, _search_class_in_modules


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

    This clears all cached module instances and removes them from tracking,
    but keeps alias mappings intact. Use reload_aliases() to reset aliases,
    or reset_all() to reset everything.
    """
    # Clear cached modules and submodule caches before removing from tracking
    for lm in _LAZY_MODULES.values():
        object.__setattr__(lm, "_cached_module", None)
        object.__setattr__(lm, "_submodule_cache", {})
    # Remove from tracking so list_loaded() returns empty after clear
    _LAZY_MODULES.clear()


def reset_all() -> None:
    """Reset all state including cache, aliases, and symbol index."""
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
    _config._AUTO_SEARCH_ENABLED = True


def disable_auto_search() -> None:
    """Disable auto-search for unregistered modules."""
    _config._AUTO_SEARCH_ENABLED = False


def is_auto_search_enabled() -> bool:
    """Check if auto-search is enabled."""
    return _config._AUTO_SEARCH_ENABLED


def search_module(name: str) -> Optional[str]:
    """Search for a module by name."""
    return _search_module(name)


def search_class(class_name: str) -> Optional[tuple]:
    """Search for a class in loaded modules."""
    return _search_class_in_modules(class_name)


def enable_debug_mode() -> None:
    """Enable debug mode."""
    _config._DEBUG_MODE = True


def disable_debug_mode() -> None:
    """Disable debug mode."""
    _config._DEBUG_MODE = False


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return _config._DEBUG_MODE


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
    _IMPORT_STATS.total_imports = 0
    _IMPORT_STATS.total_time = 0.0
    _IMPORT_STATS.module_times.clear()
    _IMPORT_STATS.module_access_counts.clear()


def validate_aliases_importable(
    aliases: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Validate that aliases can actually be imported."""
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
