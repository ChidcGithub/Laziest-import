"""
Symbol search system for laziest-import.

This package provides symbol search and resolution functionality.

Public API:
    - enable_symbol_search / disable_symbol_search
    - search_symbol
    - rebuild_symbol_index
    - set_symbol_preference / get_symbol_preference / clear_symbol_preference
    - And more...
"""

# Import from submodules
from ._scan import (
    _is_stdlib_module,
    _scan_module_symbols,
    _get_signature_hint,
)

from ._index import (
    _build_symbol_index,
    _SYMBOL_INDEX_LOCK,
)

from ._search import (
    search_symbol,
    _search_symbol_direct,
    _search_symbol_enhanced,
    _handle_symbol_not_found,
    _compare_signatures,
    _score_symbol_match,
    _warn_symbol_conflict,
    _interactive_confirm,
    _is_interactive_terminal,
)

from ._api import (
    # Symbol Search API
    enable_symbol_search,
    disable_symbol_search,
    is_symbol_search_enabled,
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
)

from ._incremental import (
    _build_incremental_symbol_index,
    _remove_package_symbols,
    build_symbol_index_incremental,
)

from ._shard import (
    search_with_sharding,
    enable_sharding,
    disable_sharding,
    get_sharding_config,
    clear_shard_cache,
    _SHARD_CONFIG,
    _get_shard_key,
    _load_shard,
    _save_shard,
)

# Import internal state variables from _config for backward compatibility
from .._config import (
    _SYMBOL_CACHE,
    _STDLIB_SYMBOL_CACHE,
    _THIRD_PARTY_SYMBOL_CACHE,
)


# Public exports
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
    # Internal exports (for backward compatibility)
    "_is_stdlib_module",
    "_scan_module_symbols",
    "_build_symbol_index",
    "_search_symbol_direct",
    "_search_symbol_enhanced",
    "_handle_symbol_not_found",
    "_build_incremental_symbol_index",
    "_remove_package_symbols",
    "_SYMBOL_CACHE",
    "_STDLIB_SYMBOL_CACHE",
    "_THIRD_PARTY_SYMBOL_CACHE",
]
