"""
Public cache API for laziest-import.
"""

from typing import Dict, Any, Optional

from .. import _config

from ._dir import (
    set_cache_dir,
    get_cache_dir,
    reset_cache_dir,
    _get_cache_size,
)

from ._file_cache import (
    enable_file_cache,
    disable_file_cache,
    is_file_cache_enabled,
    clear_file_cache,
    get_file_cache_info,
    force_save_cache,
)

from ._background import (
    enable_background_build,
    get_preheat_config,
)

from ._incremental import (
    enable_incremental_index,
    get_incremental_config,
)

from ._version import (
    get_package_version,
    get_all_package_versions,
    get_laziest_import_version,
    get_cache_version,
)

from ._symbol_index import _save_tracked_packages


# ============== Cache Configuration API ==============


def set_cache_config(
    symbol_index_ttl: Optional[int] = None,
    stdlib_cache_ttl: Optional[int] = None,
    third_party_cache_ttl: Optional[int] = None,
    enable_compression: Optional[bool] = None,
    max_cache_size_mb: Optional[int] = None,
) -> None:
    """Configure cache settings."""
    c = _config
    if symbol_index_ttl is not None:
        c._CACHE_CONFIG["symbol_index_ttl"] = symbol_index_ttl
    if stdlib_cache_ttl is not None:
        c._CACHE_CONFIG["stdlib_cache_ttl"] = stdlib_cache_ttl
    if third_party_cache_ttl is not None:
        c._CACHE_CONFIG["third_party_cache_ttl"] = third_party_cache_ttl
    if enable_compression is not None:
        c._CACHE_CONFIG["enable_compression"] = enable_compression
    if max_cache_size_mb is not None:
        c._CACHE_CONFIG["max_cache_size_mb"] = max_cache_size_mb


def get_cache_config() -> Dict[str, Any]:
    """Get current cache configuration."""
    return dict(_config._CACHE_CONFIG)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    c = _config
    total_hits = c._CACHE_STATS["symbol_hits"] + c._CACHE_STATS["module_hits"]
    total_misses = c._CACHE_STATS["symbol_misses"] + c._CACHE_STATS["module_misses"]
    total_requests = total_hits + total_misses
    hit_rate = total_hits / total_requests if total_requests > 0 else 0.0

    return {
        **c._CACHE_STATS,
        "hit_rate": hit_rate,
        "total_requests": total_requests,
    }


def reset_cache_stats() -> None:
    """Reset cache statistics."""
    c = _config
    c._CACHE_STATS["symbol_hits"] = 0
    c._CACHE_STATS["symbol_misses"] = 0
    c._CACHE_STATS["module_hits"] = 0
    c._CACHE_STATS["module_misses"] = 0
    c._CACHE_STATS["last_build_time"] = 0.0
    c._CACHE_STATS["build_count"] = 0


def invalidate_package_cache(package_name: str) -> bool:
    """Invalidate cache for a specific package."""
    c = _config

    # Return False if package not tracked
    if package_name not in c._TRACKED_PACKAGES:
        return False

    del c._TRACKED_PACKAGES[package_name]

    # Remove symbols from cache
    to_remove = []
    for symbol, locations in list(c._SYMBOL_CACHE.items()):
        filtered = [loc for loc in locations if not loc[0].startswith(package_name)]
        if filtered:
            c._SYMBOL_CACHE[symbol] = filtered
        else:
            to_remove.append(symbol)

    for symbol in to_remove:
        c._SYMBOL_CACHE.pop(symbol, None)

    # Also check third-party cache
    to_remove = []
    for symbol, locations in list(c._THIRD_PARTY_SYMBOL_CACHE.items()):
        filtered = [loc for loc in locations if not loc[0].startswith(package_name)]
        if filtered:
            c._THIRD_PARTY_SYMBOL_CACHE[symbol] = filtered
        else:
            to_remove.append(symbol)

    for symbol in to_remove:
        c._THIRD_PARTY_SYMBOL_CACHE.pop(symbol, None)

    _save_tracked_packages()
    return True


def clear_symbol_cache() -> None:
    """Clear the symbol cache (memory only)."""
    c = _config
    c._SYMBOL_CACHE.clear()
    c._STDLIB_SYMBOL_CACHE.clear()
    c._THIRD_PARTY_SYMBOL_CACHE.clear()
    c._CONFIRMED_MAPPINGS.clear()

    # Modify the config module variables using setters
    c._set_symbol_index_built(False)
    c._set_stdlib_cache_built(False)
    c._set_third_party_cache_built(False)


def enable_cache_compression(enabled: bool = True) -> None:
    """Enable or disable cache compression."""
    _config._CACHE_CONFIG["enable_compression"] = enabled


__all__ = [
    # Cache configuration
    "set_cache_config",
    "get_cache_config",
    "get_cache_stats",
    "reset_cache_stats",
    "invalidate_package_cache",
    "clear_symbol_cache",
    "enable_cache_compression",
    # Cache directory
    "set_cache_dir",
    "get_cache_dir",
    "reset_cache_dir",
    # File cache
    "enable_file_cache",
    "disable_file_cache",
    "is_file_cache_enabled",
    "clear_file_cache",
    "get_file_cache_info",
    "force_save_cache",
    # Background and incremental
    "enable_background_build",
    "get_preheat_config",
    "enable_incremental_index",
    "get_incremental_config",
    # Version
    "get_package_version",
    "get_all_package_versions",
    "get_laziest_import_version",
    "get_cache_version",
]