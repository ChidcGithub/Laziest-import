"""
Symbol search system for laziest-import.

This module re-exports all functionality from the _symbol package
for backward compatibility.
"""

# Re-export everything from the _symbol package
from ._symbol import (
    # Symbol Search API
    enable_symbol_search,
    disable_symbol_search,
    is_symbol_search_enabled,
    search_symbol,
    rebuild_symbol_index,
    get_symbol_search_config,
    get_symbol_cache_info,
    # Symbol Resolution API
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
    # Module Skip Configuration API
    get_module_skip_config,
    set_module_skip_config,
    # Incremental Build API
    build_symbol_index_incremental,
    # Sharding API
    search_with_sharding,
    enable_sharding,
    disable_sharding,
    get_sharding_config,
    clear_shard_cache,
    # Internal exports
    _is_stdlib_module,
    _scan_module_symbols,
    _build_symbol_index,
    _search_symbol_direct,
    _search_symbol_enhanced,
    _handle_symbol_not_found,
    _build_incremental_symbol_index,
    _remove_package_symbols,
    # Internal state (for backward compatibility)
    _SYMBOL_CACHE,
    _STDLIB_SYMBOL_CACHE,
    _THIRD_PARTY_SYMBOL_CACHE,
)


# Also export thread lock for backward compatibility
from ._symbol._index import _SYMBOL_INDEX_LOCK


__all__ = [
    # Symbol Search API
    "enable_symbol_search",
    "disable_symbol_search",
    "is_symbol_search_enabled",
    "search_symbol",
    "rebuild_symbol_index",
    "get_symbol_search_config",
    "get_symbol_cache_info",
    # Symbol Resolution API
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
    # Module Skip Configuration API
    "get_module_skip_config",
    "set_module_skip_config",
    # Incremental Build API
    "build_symbol_index_incremental",
    # Sharding API
    "search_with_sharding",
    "enable_sharding",
    "disable_sharding",
    "get_sharding_config",
    "clear_shard_cache",
    # Internal exports
    "_is_stdlib_module",
    "_scan_module_symbols",
    "_build_symbol_index",
    "_SYMBOL_INDEX_LOCK",
    "_search_symbol_direct",
    "_search_symbol_enhanced",
    "_handle_symbol_not_found",
    "_build_incremental_symbol_index",
    "_remove_package_symbols",
    "_SYMBOL_CACHE",
    "_STDLIB_SYMBOL_CACHE",
    "_THIRD_PARTY_SYMBOL_CACHE",
]