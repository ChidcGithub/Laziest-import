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
# Re-export _FILE_CACHE_ENABLED from config for backward compatibility
from .._config import _FILE_CACHE_ENABLED
from ._api import (
    clear_symbol_cache,
    enable_cache_compression,
    get_cache_config,
    get_cache_stats,
    invalidate_package_cache,
    reset_cache_stats,
    # Cache configuration
    set_cache_config,
)
from ._background import (
    _BACKGROUND_BUILD_LOCK,
    _is_background_index_building,
    _start_background_index_build,
    _wait_for_background_index,
    enable_background_build,
    get_preheat_config,
)
from ._dir import (
    _check_cache_size_before_save,
    _cleanup_cache_if_needed,
    _get_cache_dir,
    _get_cache_size,
    get_cache_dir,
    reset_cache_dir,
    set_cache_dir,
)
from ._file_cache import (
    _CACHE_LOCK,
    _CALLER_FILE_PATH,
    _CALLER_FILE_SHA,
    _CALLER_LOADED_MODULES,
    FileCache,
    _calculate_file_sha,
    _get_cache_file_path,
    _get_caller_file_path,
    _init_file_cache,
    _load_file_cache,
    _record_module_load,
    _save_current_cache,
    _save_file_cache,
    _start_background_preload,
    clear_file_cache,
    disable_file_cache,
    enable_file_cache,
    force_save_cache,
    get_file_cache_info,
    is_file_cache_enabled,
)
from ._incremental import (
    _detect_changed_packages,
    _get_incremental_update_modules,
    _get_installed_packages,
    enable_incremental_index,
    get_incremental_config,
)
from ._symbol_index import (
    SymbolIndexCache,
    _check_package_changed,
    _get_compressed_path,
    _get_package_version,
    _get_symbol_index_path,
    _get_tracked_packages_path,
    _load_compressed_json,
    _load_symbol_index,
    _load_tracked_packages,
    _save_compressed_json,
    _save_symbol_index,
    _save_tracked_packages,
    _should_use_compression,
    _track_package,
)
from ._version import (
    get_all_package_versions,
    get_cache_version,
    get_laziest_import_version,
    get_package_version,
)

# Public API - what users typically import
__all__ = [
    "_BACKGROUND_BUILD_LOCK",
    # Internal symbols (for backward compatibility)
    "_CACHE_LOCK",
    "_CALLER_FILE_PATH",
    "_CALLER_FILE_SHA",
    "_CALLER_LOADED_MODULES",
    "_FILE_CACHE_ENABLED",
    "FileCache",
    # Data classes
    "SymbolIndexCache",
    "_calculate_file_sha",
    "_check_cache_size_before_save",
    "_check_package_changed",
    "_cleanup_cache_if_needed",
    "_detect_changed_packages",
    "_get_cache_dir",
    "_get_cache_file_path",
    "_get_cache_size",
    "_get_caller_file_path",
    "_get_compressed_path",
    "_get_incremental_update_modules",
    "_get_installed_packages",
    "_get_package_version",
    "_get_symbol_index_path",
    "_get_tracked_packages_path",
    "_init_file_cache",
    "_is_background_index_building",
    "_load_compressed_json",
    "_load_file_cache",
    "_load_symbol_index",
    "_load_tracked_packages",
    "_record_module_load",
    "_save_compressed_json",
    "_save_current_cache",
    "_save_file_cache",
    "_save_symbol_index",
    "_save_tracked_packages",
    "_should_use_compression",
    "_start_background_index_build",
    "_start_background_preload",
    "_track_package",
    "_wait_for_background_index",
    "clear_file_cache",
    "clear_symbol_cache",
    "disable_file_cache",
    # Background and incremental
    "enable_background_build",
    "enable_cache_compression",
    # File cache
    "enable_file_cache",
    "enable_incremental_index",
    "force_save_cache",
    "get_all_package_versions",
    "get_cache_config",
    "get_cache_dir",
    "get_cache_stats",
    "get_cache_version",
    "get_file_cache_info",
    "get_incremental_config",
    "get_laziest_import_version",
    # Version
    "get_package_version",
    "get_preheat_config",
    "invalidate_package_cache",
    "is_file_cache_enabled",
    "reset_cache_dir",
    "reset_cache_stats",
    # Cache configuration
    "set_cache_config",
    # Cache directory
    "set_cache_dir",
]
