"""
Cache system for laziest-import.

This subpackage provides:
- Cache directory management
- Symbol index persistence
- File cache system
- Background index building
- Incremental update detection
- Version query utilities
"""

# Import all from submodules
from ._dir import (
    set_cache_dir,
    get_cache_dir,
    reset_cache_dir,
    _get_cache_dir,
    _get_cache_size,
    _cleanup_cache_if_needed,
    _check_cache_size_before_save,
)

from ._symbol_index import (
    SymbolIndexCache,
    _get_symbol_index_path,
    _get_tracked_packages_path,
    _save_compressed_json,
    _load_compressed_json,
    _should_use_compression,
    _get_compressed_path,
    _save_symbol_index,
    _load_symbol_index,
    _save_tracked_packages,
    _load_tracked_packages,
    _get_package_version,
    _track_package,
    _check_package_changed,
)

from ._file_cache import (
    FileCache,
    _CACHE_LOCK,
    _CALLER_FILE_PATH,
    _CALLER_FILE_SHA,
    _CALLER_LOADED_MODULES,
    _calculate_file_sha,
    _get_caller_file_path,
    _get_cache_file_path,
    _load_file_cache,
    _save_file_cache,
    _init_file_cache,
    _start_background_preload,
    _record_module_load,
    _save_current_cache,
    enable_file_cache,
    disable_file_cache,
    is_file_cache_enabled,
    clear_file_cache,
    get_file_cache_info,
    force_save_cache,
)

from ._background import (
    _BACKGROUND_BUILD_LOCK,
    _start_background_index_build,
    _is_background_index_building,
    _wait_for_background_index,
    enable_background_build,
    get_preheat_config,
)

from ._incremental import (
    _get_installed_packages,
    _detect_changed_packages,
    _get_incremental_update_modules,
    enable_incremental_index,
    get_incremental_config,
)

from ._version import (
    get_package_version,
    get_all_package_versions,
    get_laziest_import_version,
    get_cache_version,
)

from ._api import (
    # Cache configuration
    set_cache_config,
    get_cache_config,
    get_cache_stats,
    reset_cache_stats,
    invalidate_package_cache,
    clear_symbol_cache,
    enable_cache_compression,
)


# Public API - what users typically import
__all__ = [
    # Data classes
    "SymbolIndexCache",
    "FileCache",
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
    # Internal symbols (for backward compatibility)
    "_CACHE_LOCK",
    "_CALLER_FILE_PATH",
    "_CALLER_FILE_SHA",
    "_CALLER_LOADED_MODULES",
    "_BACKGROUND_BUILD_LOCK",
    "_get_cache_dir",
    "_get_cache_size",
    "_cleanup_cache_if_needed",
    "_check_cache_size_before_save",
    "_get_symbol_index_path",
    "_get_tracked_packages_path",
    "_save_compressed_json",
    "_load_compressed_json",
    "_should_use_compression",
    "_get_compressed_path",
    "_save_symbol_index",
    "_load_symbol_index",
    "_save_tracked_packages",
    "_load_tracked_packages",
    "_get_package_version",
    "_track_package",
    "_check_package_changed",
    "_calculate_file_sha",
    "_get_caller_file_path",
    "_get_cache_file_path",
    "_load_file_cache",
    "_save_file_cache",
    "_init_file_cache",
    "_start_background_preload",
    "_record_module_load",
    "_save_current_cache",
    "_start_background_index_build",
    "_is_background_index_building",
    "_wait_for_background_index",
    "_get_installed_packages",
    "_detect_changed_packages",
    "_get_incremental_update_modules",
]
