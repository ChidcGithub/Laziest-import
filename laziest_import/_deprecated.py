"""
Backward-compatible wrapper for the old API.

All functions are deprecated and will emit a FutureWarning when called.
Please migrate to the new LazyImport API:

    from laziest_import import LazyImport
    lz = LazyImport()

    # Or use module-level convenience functions:
    from laziest_import import lz
    lz().module.numpy

Old API -> New API mapping:
    enable_debug_mode()          -> lz.config.debug = True
    search_symbol('DF')          -> lz.symbol.search('DF')
    which('sqrt')                -> lz.symbol.which('sqrt')
    get_cache_stats()            -> lz.cache.stats
    clear_symbol_cache()         -> lz.cache.symbols.clear()
    register_alias('np','numpy') -> lz.alias.register('np', 'numpy')
    add_pre_import_hook(fn)      -> lz.hooks.pre += fn
    ...
"""

import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from . import _config


def _warn(func_name: str, new_api: str) -> None:
    warnings.warn(
        f"{func_name}() is deprecated and will be removed in laziest-import 1.0.0. "
        f"Use {new_api} instead. "
        f"See https://github.com/ChidcGithub/Laziest-import for migration guide.",
        FutureWarning,
        stacklevel=3,
    )


def _get_lz() -> "LazyImport":
    from ._api import lz
    return lz


# ─── Module loading functions ──────────────────────────────

def list_loaded() -> List[str]:
    """Deprecated -> lz().module.list_loaded()"""
    _warn("list_loaded", "lz().module.list_loaded()")
    from ._public_api import list_loaded as _list_loaded
    return _list_loaded()


def list_available() -> List[str]:
    """Deprecated -> lz().module.list_available()"""
    _warn("list_available", "lz().module.list_available()")
    from ._public_api import list_available as _list_available
    return _list_available()


def get_module(alias: str) -> Optional[Any]:
    """Deprecated -> lz().module.get(alias) or lz().alias[alias]"""
    _warn("get_module", "lz().module.get(alias)")
    from ._public_api import get_module as _get_module
    return _get_module(alias)


def clear_cache() -> None:
    """Deprecated -> lz().cache.clear()"""
    _warn("clear_cache", "lz().cache.clear()")
    _get_lz().cache.clear()


def reset_all() -> None:
    """Deprecated -> lz().cache.clear() + lz().alias.reload() + lz().symbol.index.reset()"""
    _warn("reset_all", "lz().cache.clear() and other combined operations")
    from ._config import reset_all as _reset_all
    _reset_all()


def get_version(alias: str) -> Optional[str]:
    """Deprecated -> lz().version.of(alias)"""
    _warn("get_version", "lz().version.of(alias)")
    from ._public_api import get_version as _get_version
    return _get_version(alias)


def reload_module(alias: str) -> bool:
    """Deprecated -> lz().module.reload(alias)"""
    _warn("reload_module", "lz().module.reload(alias)")
    from ._public_api import reload_module as _reload_module
    return _reload_module(alias)


# ─── Search functions ──────────────────────────────────

def enable_auto_search() -> None:
    """Deprecated -> lz.config.auto_search = True or lz.config.auto_search = True"""
    _warn("enable_auto_search", "lz.config.auto_search = True")
    _get_lz().config.auto_search = True


def disable_auto_search() -> None:
    """Deprecated -> lz.config.auto_search = False"""
    _warn("disable_auto_search", "lz.config.auto_search = False")
    _get_lz().config.auto_search = False


def is_auto_search_enabled() -> bool:
    """Deprecated -> lz.config.auto_search"""
    _warn("is_auto_search_enabled", "lz.config.auto_search")
    return _config._AUTO_SEARCH_ENABLED


def search_module(name: str) -> Optional[str]:
    """Deprecated -> lz().symbol.search(name)"""
    _warn("search_module", "lz().symbol.search(name)")
    from ._public_api import search_module as _search_module
    return _search_module(name)


def search_class(class_name: str) -> Optional[tuple]:
    """Deprecated -> lz().symbol.search(name, symbol_type='class')"""
    _warn("search_class", "lz().symbol.search(name, symbol_type='class')")
    from ._public_api import search_class as _search_class
    return _search_class(class_name)


# ─── Debug functions ──────────────────────────────────

def enable_debug_mode() -> None:
    """Deprecated -> lz.config.debug = True"""
    _warn("enable_debug_mode", "lz.config.debug = True")
    _get_lz().config.debug = True


def disable_debug_mode() -> None:
    """Deprecated -> lz.config.debug = False"""
    _warn("disable_debug_mode", "lz.config.debug = False")
    _get_lz().config.debug = False


def is_debug_mode() -> bool:
    """Deprecated -> lz.config.debug"""
    _warn("is_debug_mode", "lz.config.debug")
    return _config._DEBUG_MODE


# ─── Statistics functions ──────────────────────────────────

def get_import_stats() -> Dict[str, Any]:
    """Deprecated -> lz.config.import_stats"""
    _warn("get_import_stats", "lz.config.import_stats")
    from ._public_api import get_import_stats as _get_import_stats
    return _get_import_stats()


def reset_import_stats() -> None:
    """Deprecated -> (no direct equivalent, pending)"""
    _warn("reset_import_stats", "no direct equivalent in new API yet")
    from ._public_api import reset_import_stats as _reset_import_stats
    _reset_import_stats()


# ─── Symbol search functions ──────────────────────────────

def search_symbol(
    name: str,
    symbol_type: Optional[str] = None,
    signature: Optional[str] = None,
    max_results: Optional[int] = None,
) -> List[Any]:
    """Deprecated -> lz().symbol.search(name, symbol_type, signature, max_results)"""
    _warn("search_symbol", "lz().symbol.search()")
    from ._symbol import search_symbol as _search_symbol
    return _search_symbol(name, symbol_type, signature, max_results)


def enable_symbol_search(
    interactive: bool = True,
    exact_params: bool = False,
    max_results: int = 5,
    search_depth: int = 1,
    skip_stdlib: bool = False,
) -> None:
    """Deprecated -> lz().symbol.config.enable() or lz().symbol.config.interactive = ..."""
    _warn("enable_symbol_search", "lz().symbol.config")
    from ._symbol import enable_symbol_search as _enable
    _enable(interactive, exact_params, max_results, search_depth, skip_stdlib)


def disable_symbol_search() -> None:
    """Deprecated -> lz().symbol.config.enabled = False"""
    _warn("disable_symbol_search", "lz().symbol.config")
    from ._symbol import disable_symbol_search as _disable
    _disable()


def is_symbol_search_enabled() -> bool:
    """Deprecated -> lz().symbol.config.enabled"""
    _warn("is_symbol_search_enabled", "lz().symbol.config.enabled")
    from ._symbol import is_symbol_search_enabled as _is_enabled
    return _is_enabled()


def rebuild_symbol_index() -> None:
    """Deprecated -> lz().symbol.index.rebuild()"""
    _warn("rebuild_symbol_index", "lz().symbol.index.rebuild()")
    from ._symbol import rebuild_symbol_index as _rebuild
    _rebuild()


def get_symbol_search_config() -> Dict[str, Any]:
    """Deprecated -> lz().symbol.config.snapshot()"""
    _warn("get_symbol_search_config", "lz().symbol.config")
    from ._symbol import get_symbol_search_config as _get
    return _get()


def get_symbol_cache_info() -> Dict[str, Any]:
    """Deprecated -> lz().symbol.cache_info()"""
    _warn("get_symbol_cache_info", "lz().symbol.cache_info()")
    from ._symbol import get_symbol_cache_info as _get
    return _get()


def set_symbol_preference(symbol: str, module: str) -> None:
    """Deprecated -> lz().symbol.prefer(symbol, module)"""
    _warn("set_symbol_preference", "lz().symbol.prefer()")
    from ._symbol import set_symbol_preference as _set
    _set(symbol, module)


def get_symbol_preference(symbol: str) -> Optional[str]:
    """Deprecated -> lz().symbol.preference(symbol)"""
    _warn("get_symbol_preference", "lz().symbol.preference()")
    from ._symbol import get_symbol_preference as _get
    return _get(symbol)


def clear_symbol_preference(symbol: str) -> bool:
    """Deprecated -> lz().symbol.clear_preference(symbol)"""
    _warn("clear_symbol_preference", "lz().symbol.clear_preference()")
    from ._symbol import clear_symbol_preference as _clear
    return _clear(symbol)


def list_symbol_conflicts(symbol: str) -> List[Dict[str, Any]]:
    """Deprecated -> lz().symbol.conflicts(symbol)"""
    _warn("list_symbol_conflicts", "lz().symbol.conflicts()")
    from ._symbol import list_symbol_conflicts as _list
    return _list(symbol)


def set_module_priority(module: str, priority: int) -> None:
    """Deprecated -> lz().symbol.config.module_priority namespace method"""
    _warn("set_module_priority", "lz().symbol module config")
    from ._symbol import set_module_priority as _set
    _set(module, priority)


def get_module_priority(module: str) -> int:
    """Deprecated -> lz().symbol.config.module_priority"""
    _warn("get_module_priority", "lz().symbol module config")
    from ._symbol import get_module_priority as _get
    return _get(module)


def enable_auto_symbol_resolution(
    auto_threshold: float = 0.7,
    conflict_threshold: float = 0.3,
    warn_on_conflict: bool = True,
) -> None:
    """Deprecated -> lz().symbol.config.auto_resolution = True"""
    _warn("enable_auto_symbol_resolution", "lz().symbol.config.auto_resolution")
    from ._symbol import enable_auto_symbol_resolution as _enable
    _enable(auto_threshold, conflict_threshold, warn_on_conflict)


def disable_auto_symbol_resolution() -> None:
    """Deprecated -> lz().symbol.config.auto_resolution = False"""
    _warn("disable_auto_symbol_resolution", "lz().symbol.config.auto_resolution")
    from ._symbol import disable_auto_symbol_resolution as _disable
    _disable()


def get_symbol_resolution_config() -> Dict[str, Any]:
    """Deprecated -> lz().symbol.config"""
    _warn("get_symbol_resolution_config", "lz().symbol.config")
    from ._symbol import get_symbol_resolution_config as _get
    return _get()


def get_loaded_modules_context() -> Set[str]:
    """Deprecated -> lz().symbol namespace"""
    _warn("get_loaded_modules_context", "lz().symbol")
    from ._symbol import get_loaded_modules_context as _get
    return _get()


def get_module_skip_config() -> Dict[str, Any]:
    """Deprecated -> lz.config.module_skip"""
    _warn("get_module_skip_config", "lz.config.module_skip")
    from ._symbol import get_module_skip_config as _get
    return _get()


def set_module_skip_config(
    skip_test_modules: Optional[bool] = None,
    skip_internal_modules: Optional[bool] = None,
    skip_large_modules: Optional[bool] = None,
    large_module_threshold: Optional[int] = None,
) -> None:
    """Deprecated -> lz.config.module_skip"""
    _warn("set_module_skip_config", "lz.config.module_skip")
    from ._symbol import set_module_skip_config as _set
    _set(skip_test_modules, skip_internal_modules, skip_large_modules, large_module_threshold)


# ─── Symbol index functions ──────────────────────────────

def search_with_sharding(symbol_name: str, max_results: int = 5) -> List[Any]:
    """Deprecated -> lz().symbol.sharded()"""
    _warn("search_with_sharding", "lz().symbol.sharded()")
    from ._symbol import search_with_sharding as _search
    return _search(symbol_name, max_results)


def enable_sharding(enabled: bool = True) -> None:
    """Deprecated -> lz().symbol.config"""
    _warn("enable_sharding", "lz().symbol.config")
    from ._symbol import enable_sharding as _enable
    _enable(enabled)


def disable_sharding() -> None:
    """Deprecated -> lz().symbol.config"""
    _warn("disable_sharding", "lz().symbol.config")
    from ._symbol import disable_sharding as _disable
    _disable()


def get_sharding_config() -> Dict[str, Any]:
    """Deprecated -> lz().symbol.config"""
    _warn("get_sharding_config", "lz().symbol.config")
    from ._symbol import get_sharding_config as _get
    return _get()


def clear_shard_cache() -> None:
    """Deprecated -> lz().symbol.config"""
    _warn("clear_shard_cache", "lz().symbol.config")
    from ._symbol import clear_shard_cache as _clear
    _clear()


def build_symbol_index_incremental() -> bool:
    """Deprecated -> lz().symbol.index.incremental()"""
    _warn("build_symbol_index_incremental", "lz().symbol.index.incremental()")
    from ._symbol import build_symbol_index_incremental as _build
    return _build()


# ─── Cache config functions ──────────────────────────────

def set_cache_config(
    symbol_index_ttl: Optional[int] = None,
    stdlib_cache_ttl: Optional[int] = None,
    third_party_cache_ttl: Optional[int] = None,
    enable_compression: Optional[bool] = None,
    max_cache_size_mb: Optional[int] = None,
) -> None:
    """Deprecated -> lz().cache.config.max_size_mb = 200 etc."""
    _warn("set_cache_config", "lz().cache.config")
    from ._cache import set_cache_config as _set
    _set(symbol_index_ttl, stdlib_cache_ttl, third_party_cache_ttl, enable_compression, max_cache_size_mb)


def get_cache_config() -> Dict[str, Any]:
    """Deprecated -> lz().cache.config"""
    _warn("get_cache_config", "lz().cache.config")
    from ._cache import get_cache_config as _get
    return _get()


def get_cache_stats() -> Dict[str, Any]:
    """Deprecated -> lz().cache.stats"""
    _warn("get_cache_stats", "lz().cache.stats")
    from ._cache import get_cache_stats as _get
    return _get()


def reset_cache_stats() -> None:
    """Deprecated -> lz().cache.stats.reset()"""
    _warn("reset_cache_stats", "lz().cache.stats.reset()")
    from ._cache import reset_cache_stats as _reset
    _reset()


def invalidate_package_cache(package_name: str) -> bool:
    """Deprecated -> lz().cache namespace"""
    _warn("invalidate_package_cache", "lz().cache")
    from ._cache import invalidate_package_cache as _invalidate
    return _invalidate(package_name)


def clear_symbol_cache() -> None:
    """Deprecated -> lz().cache.symbols.clear()"""
    _warn("clear_symbol_cache", "lz().cache.symbols.clear()")
    from ._cache import clear_symbol_cache as _clear
    _clear()


def enable_cache_compression(enabled: bool = True) -> None:
    """Deprecated -> lz().cache.compression = True"""
    _warn("enable_cache_compression", "lz().cache.compression")
    from ._cache import enable_cache_compression as _enable
    _enable(enabled)


# ─── File cache functions ──────────────────────────────

def enable_file_cache() -> None:
    """Deprecated -> lz().cache.files.enabled = True"""
    _warn("enable_file_cache", "lz().cache.files.enabled")
    from ._cache import enable_file_cache as _enable
    _enable()


def disable_file_cache() -> None:
    """Deprecated -> lz().cache.files.enabled = False"""
    _warn("disable_file_cache", "lz().cache.files.enabled")
    from ._cache import disable_file_cache as _disable
    _disable()


def is_file_cache_enabled() -> bool:
    """Deprecated -> lz().cache.files.enabled"""
    _warn("is_file_cache_enabled", "lz().cache.files.enabled")
    from ._cache import is_file_cache_enabled as _is_enabled
    return _is_enabled()


def clear_file_cache(file_path: Optional[str] = None) -> int:
    """Deprecated -> lz().cache.files.clear(file_path)"""
    _warn("clear_file_cache", "lz().cache.files.clear()")
    from ._cache import clear_file_cache as _clear
    return _clear(file_path)


def get_file_cache_info() -> Dict[str, Any]:
    """Deprecated -> lz().cache.files.info()"""
    _warn("get_file_cache_info", "lz().cache.files.info()")
    from ._cache import get_file_cache_info as _get
    return _get()


def force_save_cache() -> bool:
    """Deprecated -> lz().cache.files.force_save()"""
    _warn("force_save_cache", "lz().cache.files.force_save()")
    from ._cache import force_save_cache as _force
    return _force()


# ─── Background build functions ──────────────────────────────

def enable_background_build(enabled: bool = True) -> None:
    """Deprecated -> lz().background.enable(enabled)"""
    _warn("enable_background_build", "lz().background.enable()")
    from ._cache import enable_background_build as _enable
    _enable(enabled)


def get_preheat_config() -> dict:
    """Deprecated -> lz().background.preheat"""
    _warn("get_preheat_config", "lz().background.preheat")
    from ._cache import get_preheat_config as _get
    return _get()


def enable_incremental_index(enabled: bool = True) -> None:
    """Deprecated -> lz().background related"""
    _warn("enable_incremental_index", "lz().background related")
    from ._cache import enable_incremental_index as _enable
    _enable(enabled)


def get_incremental_config() -> Dict[str, Any]:
    """Deprecated -> lz().background related"""
    _warn("get_incremental_config", "lz().background related")
    from ._cache import get_incremental_config as _get
    return _get()


# ─── Version functions ──────────────────────────────────

def get_package_version(package_name: str) -> Optional[str]:
    """Deprecated -> lz().version.of(package_name)"""
    _warn("get_package_version", "lz().version.of()")
    from ._cache import get_package_version as _get
    return _get(package_name)


def get_all_package_versions() -> Dict[str, str]:
    """Deprecated -> lz().version.all_packages()"""
    _warn("get_all_package_versions", "lz().version.all_packages()")
    from ._cache import get_all_package_versions as _get
    return _get()


def get_laziest_import_version() -> str:
    """Deprecated -> lz().version.current"""
    _warn("get_laziest_import_version", "lz().version.current")
    from ._cache import get_laziest_import_version as _get
    return _get()


def get_cache_version() -> str:
    """Deprecated -> internal use"""
    _warn("get_cache_version", "lz().cache")
    from ._cache import get_cache_version as _get
    return _get()


# ─── Alias management functions ──────────────────────────────

def get_config_paths() -> List[str]:
    """Deprecated -> lz().alias related"""
    _warn("get_config_paths", "lz().alias")
    from ._alias import get_config_paths as _get
    return _get()


def get_config_dirs() -> List[str]:
    """Deprecated -> lz().alias related"""
    _warn("get_config_dirs", "lz().alias")
    from ._alias import get_config_dirs as _get
    return _get()


def reload_aliases() -> None:
    """Deprecated -> lz().alias.reload()"""
    _warn("reload_aliases", "lz().alias.reload()")
    from ._alias import reload_aliases as _reload
    _reload()


def export_aliases(path: Optional[str] = None, include_categories: bool = True) -> str:
    """Deprecated -> lz().alias.export(path, include_categories)"""
    _warn("export_aliases", "lz().alias.export()")
    from ._alias import export_aliases as _export
    return _export(path, include_categories)


def validate_aliases(aliases: Optional[Dict[str, str]] = None) -> Dict[str, List[str]]:
    """Deprecated -> lz().alias.validate(aliases)"""
    _warn("validate_aliases", "lz().alias.validate()")
    from ._alias import validate_aliases as _validate
    return _validate(aliases)


def register_alias(alias: str, module_name: str) -> None:
    """Deprecated -> lz().alias.register(alias, module_name)"""
    _warn("register_alias", "lz().alias.register()")
    from ._alias import register_alias as _register
    _register(alias, module_name)


def register_aliases(aliases: Dict[str, str]) -> List[str]:
    """Deprecated -> lz().alias.register_many(aliases)"""
    _warn("register_aliases", "lz().alias.register_many()")
    from ._alias import register_aliases as _register
    return _register(aliases)


def unregister_alias(alias: str) -> bool:
    """Deprecated -> lz().alias.unregister(alias) or del lz().alias[alias]"""
    _warn("unregister_alias", "lz().alias.unregister()")
    from ._alias import unregister_alias as _unregister
    return _unregister(alias)


# ─── Install functions ──────────────────────────────────

def install_package(
    package_name: str,
    index: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    interactive: Optional[bool] = None,
) -> bool:
    """Deprecated -> lz().install.package(package_name, ...)"""
    _warn("install_package", "lz().install.package()")
    from ._install import install_package as _install
    return _install(package_name, index, extra_args, interactive)


def enable_auto_install(
    interactive: bool = True,
    index: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    prefer_uv: bool = False,
    silent: bool = False,
) -> None:
    """Deprecated -> lz().install.enable(interactive=...)"""
    _warn("enable_auto_install", "lz().install.enable()")
    from ._install import enable_auto_install as _enable
    _enable(interactive, index, extra_args, prefer_uv, silent)


def disable_auto_install() -> None:
    """Deprecated -> lz().install.disable()"""
    _warn("disable_auto_install", "lz().install.disable()")
    from ._install import disable_auto_install as _disable
    _disable()


def is_auto_install_enabled() -> bool:
    """Deprecated -> lz().install.enabled"""
    _warn("is_auto_install_enabled", "lz().install.enabled")
    from ._install import is_auto_install_enabled as _is_enabled
    return _is_enabled()


def get_auto_install_config() -> Dict[str, Any]:
    """Deprecated -> lz().install.auto"""
    _warn("get_auto_install_config", "lz().install.auto")
    from ._install import get_auto_install_config as _get
    return _get()


def set_pip_index(url: Optional[str]) -> None:
    """Deprecated -> lz().install related config"""
    _warn("set_pip_index", "lz().install related config")
    from ._install import set_pip_index as _set
    _set(url)


def set_pip_extra_args(args: List[str]) -> None:
    """Deprecated -> lz().install related config"""
    _warn("set_pip_extra_args", "lz().install related config")
    from ._install import set_pip_extra_args as _set
    _set(args)


def rebuild_module_cache() -> None:
    """Deprecated -> lz().install.rebuild_cache()"""
    _warn("rebuild_module_cache", "lz().install.rebuild_cache()")
    from ._install import rebuild_module_cache as _rebuild
    _rebuild()


# ─── Async functions ──────────────────────────────────

async def import_async(alias: str) -> Any:
    """Deprecated -> await lz().async.get(alias)"""
    _warn("import_async", "await lz().async.get()")
    from ._async_ops import import_async as _import
    return await _import(alias)


async def import_multiple_async(aliases: List[str]) -> Dict[str, Any]:
    """Deprecated -> await lz().async.fetch(*aliases)"""
    _warn("import_multiple_async", "await lz().async.fetch()")
    from ._async_ops import import_multiple_async as _import
    return await _import(aliases)


def enable_retry(
    max_retries: int = 3, retry_delay: float = 0.5, modules: Optional[Set[str]] = None
) -> None:
    """Deprecated -> lz.config.retry.enabled = True"""
    _warn("enable_retry", "lz.config.retry")
    from ._async_ops import enable_retry as _enable
    _enable(max_retries, retry_delay, modules)


def disable_retry() -> None:
    """Deprecated -> lz.config.retry.enabled = False"""
    _warn("disable_retry", "lz.config.retry")
    from ._async_ops import disable_retry as _disable
    _disable()


def is_retry_enabled() -> bool:
    """Deprecated -> lz.config.retry.enabled"""
    _warn("is_retry_enabled", "lz.config.retry.enabled")
    from ._async_ops import is_retry_enabled as _is_enabled
    return _is_enabled()


# ─── Utility functions ──────────────────────────────────

def which(symbol_name: str, module_hint: Optional[str] = None) -> Optional[Any]:
    """Deprecated -> lz().symbol.which(symbol_name, module_hint)"""
    _warn("which", "lz().symbol.which()")
    from ._which import which as _which
    return _which(symbol_name, module_hint)


def which_all(symbol_name: str) -> List[Any]:
    """Deprecated -> lz().symbol.which_all(symbol_name)"""
    _warn("which_all", "lz().symbol.which_all()")
    from ._which import which_all as _which_all
    return _which_all(symbol_name)


def validate_aliases_importable(
    aliases: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Deprecated -> lz().alias.validate(aliases)"""
    _warn("validate_aliases_importable", "lz().alias.validate()")
    from ._public_api import validate_aliases_importable as _validate
    return _validate(aliases)


# ─── Analysis functions ──────────────────────────────────

def analyze_file(file_path: str) -> Any:
    """Deprecated -> lz().analyze.file(file_path)"""
    _warn("analyze_file", "lz().analyze.file()")
    from ._analysis import analyze_file as _analyze
    return _analyze(file_path)


def analyze_source(source: str, file_path: str = "<string>") -> Any:
    """Deprecated -> lz().analyze.code(source, file_path)"""
    _warn("analyze_source", "lz().analyze.code()")
    from ._analysis import analyze_source as _analyze
    return _analyze(source, file_path)


def analyze_directory(
    dir_path: str, recursive: bool = True, exclude: Optional[set] = None
) -> List[Any]:
    """Deprecated -> lz().analyze.dir(dir_path, recursive, exclude)"""
    _warn("analyze_directory", "lz().analyze.dir()")
    from ._analysis import analyze_directory as _analyze
    return _analyze(dir_path, recursive, exclude)


# ─── Profiling functions ──────────────────────────────

def start_profiling() -> None:
    """Deprecated -> lz().profile.start()"""
    _warn("start_profiling", "lz().profile.start()")
    from ._analysis import start_profiling as _start
    _start()


def stop_profiling() -> None:
    """Deprecated -> lz().profile.stop()"""
    _warn("stop_profiling", "lz().profile.stop()")
    from ._analysis import stop_profiling as _stop
    _stop()


def get_profile_report() -> Any:
    """Deprecated -> lz().profile.report()"""
    _warn("get_profile_report", "lz().profile.report()")
    from ._analysis import get_profile_report as _get
    return _get()


def print_profile_report() -> None:
    """Deprecated -> lz().profile.print_report()"""
    _warn("print_profile_report", "lz().profile.print_report()")
    from ._analysis import print_profile_report as _print
    _print()


# ─── Environment functions ──────────────────────────────────

def detect_environment() -> Any:
    """Deprecated -> lz().analyze related"""
    _warn("detect_environment", "lz().analyze related")
    from ._analysis import detect_environment as _detect
    return _detect()


def show_environment() -> None:
    """Deprecated -> lz().analyze related"""
    _warn("show_environment", "lz().analyze related")
    from ._analysis import show_environment as _show
    _show()


# ─── Preference functions ──────────────────────────────────

def save_preferences() -> bool:
    """Deprecated -> preference management"""
    _warn("save_preferences", "preference management API")
    from ._analysis._preferences import save_preferences as _save
    return _save()


def load_preferences() -> Dict[str, str]:
    """Deprecated -> preference management"""
    _warn("load_preferences", "preference management API")
    from ._analysis._preferences import load_preferences as _load
    return _load()


def apply_preferences() -> None:
    """Deprecated -> preference management"""
    _warn("apply_preferences", "preference management API")
    from ._analysis._preferences import apply_preferences as _apply
    _apply()


def clear_preferences() -> bool:
    """Deprecated -> preference management"""
    _warn("clear_preferences", "preference management API")
    from ._analysis._preferences import clear_preferences as _clear
    return _clear()


def get_preferences_path() -> Path:
    """Deprecated -> preference management"""
    _warn("get_preferences_path", "preference management API")
    from ._analysis._preferences import get_preferences_path as _get
    return _get()


# ─── Dependency tree functions ────────────────────────────────

def dependency_tree(dir_path: str = ".", max_depth: int = 3, exclude: Optional[set] = None) -> Any:
    """Deprecated -> lz().analyze.dep_tree()"""
    _warn("dependency_tree", "lz().analyze.dep_tree()")
    from ._analysis._dependency import dependency_tree as _tree
    return _tree(dir_path, max_depth, exclude)


def print_dependency_tree(dir_path: str = ".", max_depth: int = 3, exclude: Optional[set] = None) -> None:
    """Deprecated -> lz().analyze.dep_tree() + print"""
    _warn("print_dependency_tree", "lz().analyze.dep_tree()")
    from ._analysis._dependency import print_dependency_tree as _print
    _print(dir_path, max_depth, exclude)


# ─── Benchmark functions ──────────────────────────────

def benchmark(func, *args, **kwargs) -> Any:
    """Deprecated -> lz().profile related"""
    _warn("benchmark", "lz().profile related")
    from ._analysis._benchmark import benchmark as _benchmark
    return _benchmark(func, *args, **kwargs)


def benchmark_imports(aliases: List[str], iterations: int = 10) -> Any:
    """Deprecated -> lz().profile related"""
    _warn("benchmark_imports", "lz().profile related")
    from ._analysis._benchmark import benchmark_imports as _benchmark
    return _benchmark(aliases, iterations)


def print_benchmark_report(report: Any) -> None:
    """Deprecated -> lz().profile.print_report()"""
    _warn("print_benchmark_report", "lz().profile.print_report()")
    from ._analysis._benchmark import print_benchmark_report as _print
    _print(report)


# ─── Hook functions ──────────────────────────────────

def add_pre_import_hook(hook: Callable) -> None:
    """Deprecated -> lz().hooks.pre += hook"""
    _warn("add_pre_import_hook", "lz().hooks.pre += hook")
    _config._PRE_IMPORT_HOOKS.append(hook)


def add_post_import_hook(hook: Callable) -> None:
    """Deprecated -> lz().hooks.post += hook"""
    _warn("add_post_import_hook", "lz().hooks.post += hook")
    _config._POST_IMPORT_HOOKS.append(hook)


def remove_pre_import_hook(hook: Callable) -> bool:
    """Deprecated -> lz().hooks.pre -= hook"""
    _warn("remove_pre_import_hook", "lz().hooks.pre -= hook")
    try:
        _config._PRE_IMPORT_HOOKS.remove(hook)
        return True
    except ValueError:
        return False


def remove_post_import_hook(hook: Callable) -> bool:
    """Deprecated -> lz().hooks.post -= hook"""
    _warn("remove_post_import_hook", "lz().hooks.post -= hook")
    try:
        _config._POST_IMPORT_HOOKS.remove(hook)
        return True
    except ValueError:
        return False


def clear_import_hooks() -> None:
    """Deprecated -> lz().hooks.clear()"""
    _warn("clear_import_hooks", "lz().hooks.clear()")
    _config._PRE_IMPORT_HOOKS.clear()
    _config._POST_IMPORT_HOOKS.clear()


# ─── Help function ──────────────────────────────────

def help(topic: Optional[str] = None) -> str:
    """This function is not marked as deprecated because it is the interactive help entry point"""
    from ._help import help as _help
    return _help(topic)


# ─── Internal symbols (not recommended for external use) ────────────────────

def _infer_context() -> Set[str]:
    """Internal use, recommended to use lz().symbol related API"""
    _warn("_infer_context", "lz().symbol")
    from ._symbol import _infer_context as _ctx
    return _ctx()


def _handle_symbol_not_found(name: str) -> Optional[str]:
    """Internal use, recommended to use lz().symbol.which()"""
    _warn("_handle_symbol_not_found", "lz().symbol.which()")
    from ._symbol import _handle_symbol_not_found as _handle
    return _handle(name)