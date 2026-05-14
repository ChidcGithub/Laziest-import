from typing import (
    Any, Dict, List, Optional, Set, Tuple, Callable, Union, Iterator
)
from dataclasses import dataclass, field, asdict
from pathlib import Path
import warnings
import logging

# ─── Direct submodule imports (no circular dependencies) ─────────────────────

from . import _config

from ._alias import (
    _ALIAS_MAP,
    _LAZY_MODULES,
    _build_known_modules_cache,
    register_alias,
    unregister_alias,
    reload_aliases,
    export_aliases,
    validate_aliases,
    _validate_alias,
    register_aliases,
)

from ._cache import (
    clear_symbol_cache,
    get_cache_stats,
    reset_cache_stats,
    set_cache_config,
    get_cache_config,
    clear_file_cache,
    get_file_cache_info,
    force_save_cache,
    enable_file_cache,
    disable_file_cache,
    is_file_cache_enabled,
    set_cache_dir,
    get_cache_dir,
    reset_cache_dir,
    enable_cache_compression,
    enable_background_build,
    get_preheat_config,
    enable_incremental_index,
    get_incremental_config,
    get_cache_version,
    _get_cache_dir,
    _get_cache_size,
    _cleanup_cache_if_needed,
    _check_cache_size_before_save,
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
    _calculate_file_sha,
    _get_caller_file_path,
    _get_cache_file_path,
    _load_file_cache,
    _save_file_cache,
    _init_file_cache,
    _start_background_preload,
    _record_module_load,
    _save_current_cache,
    _start_background_index_build,
    _is_background_index_building,
    _wait_for_background_index,
    FileCache,
    SymbolIndexCache,
)

from ._symbol import (
    search_symbol,
    rebuild_symbol_index,
    get_symbol_search_config,
    get_symbol_cache_info,
    set_symbol_preference,
    get_symbol_preference,
    clear_symbol_preference,
    list_symbol_conflicts,
    set_module_priority,
    get_module_priority,
    enable_symbol_search,
    disable_symbol_search,
    is_symbol_search_enabled,
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
    _is_stdlib_module,
    _scan_module_symbols,
    _build_symbol_index,
    _search_symbol_direct,
    _search_symbol_enhanced,
    _handle_symbol_not_found,
    _build_incremental_symbol_index,
    _remove_package_symbols,
    _search_symbol_enhanced,
)

from ._public_api import (
    list_loaded,
    list_available,
    get_module,
    clear_cache,
    reset_all as _reset_all,
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
    validate_aliases_importable,
)

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

from ._async_ops import import_async, import_multiple_async

from ._fuzzy import _search_module

from ._proxy import _get_lazy_module

from ._which import which, which_all, SymbolLocation

from ._rcconfig import (
    load_rc_config,
    get_rc_value,
    create_rc_file,
    get_rc_info,
    reload_rc_config,
    save_rc_config,
)


# ═══════════════════════════════════════════════════════════════
#  Helper: Update symbol search configuration
# ═══════════════════════════════════════════════════════════════

def _apply_search_config(cfg: "SymbolSearchConfig") -> None:
    _config._SYMBOL_SEARCH_CONFIG.update(asdict(cfg))


def _apply_resolution_config(cfg: "SymbolResolutionConfig") -> None:
    _config._SYMBOL_RESOLUTION_CONFIG.update(asdict(cfg))


# ═══════════════════════════════════════════════════════════════
#  Dataclasses
# ═══════════════════════════════════════════════════════════════

@dataclass
class AutoInstallConfig:
    """Auto-install configuration"""
    enabled: bool = False
    interactive: bool = True
    index: Optional[str] = None
    extra_args: List[str] = field(default_factory=list)
    prefer_uv: bool = False
    silent: bool = False


@dataclass
class RetryConfig:
    """Retry configuration"""
    enabled: bool = False
    max_retries: int = 3
    retry_delay: float = 0.5
    modules: Set[str] = field(default_factory=set)


@dataclass
class SymbolSearchConfig:
    """Symbol search configuration"""
    enabled: bool = True
    interactive: bool = True
    exact_params: bool = False
    max_results: int = 5
    search_depth: int = 1
    cache_enabled: bool = True
    skip_private: bool = True
    skip_stdlib: bool = False


@dataclass
class SymbolResolutionConfig:
    """Symbol resolution configuration"""
    auto_symbol: bool = True
    auto_threshold: float = 0.7
    conflict_threshold: float = 0.3
    symbol_misspelling: bool = True
    context_aware: bool = True
    warn_on_conflict: bool = True
    save_preferences: bool = True


@dataclass
class CacheConfig:
    """Cache configuration"""
    enabled: bool = True
    max_size_mb: int = 100
    cleanup_threshold: float = 0.8
    file_cache_enabled: bool = True
    symbol_index_enabled: bool = True
    persist_across_sessions: bool = True
    symbol_index_ttl: int = 86400
    stdlib_cache_ttl: int = 604800
    third_party_cache_ttl: int = 86400
    enable_compression: bool = False


@dataclass
class ModuleSkipConfig:
    """Module skip configuration"""
    skip_test_modules: bool = True
    skip_internal_modules: bool = True
    skip_large_modules: bool = True
    large_module_threshold: int = 100
    skip_modules_file: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
#  HookList
# ═══════════════════════════════════════════════════════════════

class HookList:
    """
    Subscribable hook list.

    Supports += and -= operators:
        lz.hooks.pre += my_hook
        lz.hooks.post -= my_hook
    """

    def __init__(self, hook_list: List[Callable]) -> None:
        self._hooks = hook_list

    def add(self, callback: Callable) -> None:
        """Register a hook"""
        if callback not in self._hooks:
            self._hooks.append(callback)

    def remove(self, callback: Callable) -> bool:
        """Remove a hook, returns whether successful"""
        try:
            self._hooks.remove(callback)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """Clear all hooks"""
        self._hooks.clear()

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        """Trigger all registered hooks (internal use)"""
        for hook in list(self._hooks):
            try:
                hook(*args, **kwargs)
            except Exception:
                pass

    def __iadd__(self, callback: Callable) -> "HookList":
        self.add(callback)
        return self

    def __isub__(self, callback: Callable) -> "HookList":
        self.remove(callback)
        return self

    def __len__(self) -> int:
        return len(self._hooks)

    def __iter__(self) -> Iterator[Callable]:
        return iter(self._hooks)

    def __repr__(self) -> str:
        return f"HookList(hooks={len(self._hooks)})"


# ═══════════════════════════════════════════════════════════════
#  ModuleNamespace
# ═══════════════════════════════════════════════════════════════

class ModuleNamespace:
    """
    Module loading namespace.

    Usage:
        lz.module.numpy                    # Attribute-style (triggers lazy loading)
        lz.module.get('numpy')             # Method-style (returns None if not found)
        lz.module.load('numpy')            # Force load and return
        lz.module.reload('numpy')          # Reload
        lz.module.list_loaded()            # List loaded modules
        lz.module.list_available()         # List available modules
        lz.module.is_loaded('numpy')       # Check if loaded
    """

    def get(self, name: str) -> Optional[Any]:
        """Get a loaded module object, returns None if not found"""
        return get_module(name)

    def load(self, name: str) -> Any:
        """Load and return a module (force trigger lazy loading)"""
        lm = _get_lazy_module(name)
        return lm._get_module()

    def reload(self, name: str) -> bool:
        """Reload a loaded module"""
        return reload_module(name)

    def list_loaded(self) -> List[str]:
        """List loaded module aliases"""
        return list_loaded()

    def list_available(self) -> List[str]:
        """List all available module aliases"""
        return list_available()

    def is_loaded(self, name: str) -> bool:
        """Check if a module is loaded"""
        return name in list_loaded()

    # ---- Dict-style access ----

    def __getitem__(self, name: str) -> Any:
        mod = get_module(name)
        if mod is None:
            raise KeyError(
                f"Module '{name}' is not loaded. "
                f"Access it via lz.module.load('{name}') or lz.module['{name}'] = <module> first."
            )
        return mod

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return _get_lazy_module(name)._get_module()
        except Exception as e:
            raise AttributeError(
                f"Cannot load module '{name}': {e}"
            ) from e

    def __dir__(self) -> List[str]:
        return sorted(set(self.list_available()))

    def __repr__(self) -> str:
        loaded = self.list_loaded()
        return (
            f"<ModuleNamespace: "
            f"{len(loaded)}/{len(self.list_available())} loaded>"
        )


# ═══════════════════════════════════════════════════════════════
#  AliasNamespace
# ═══════════════════════════════════════════════════════════════

class AliasNamespace:
    """
    Alias management namespace, supports both dict-style and method-style APIs.

    Usage:
        lz.alias.register('np', 'numpy')          # Method-style
        lz.alias['my_np'] = 'numpy'                # Dict-style
        mod = lz.alias['np']                       # Get lazy proxy
        lz.alias.reload()                          # Reload from config
        lz.alias.export('/path/aliases.json')      # Export
    """

    # ---- Method-style API ----

    def register(self, alias: str, module_name: str) -> None:
        """Register a single alias"""
        register_alias(alias, module_name)

    def register_many(self, aliases: Dict[str, str]) -> List[str]:
        """Batch register aliases, returns list of successfully registered ones"""
        registered: List[str] = []
        for alias, mod in aliases.items():
            try:
                register_alias(alias, mod)
                registered.append(alias)
            except ValueError:
                pass
        return registered

    def unregister(self, alias: str) -> bool:
        """Unregister an alias, returns whether successful"""
        return unregister_alias(alias)

    def reload(self) -> None:
        """Reload all aliases from config file"""
        reload_aliases()

    def export(
        self,
        path: Optional[str] = None,
        include_categories: bool = True,
    ) -> str:
        """
        Export aliases to a JSON file or return as string.

        Args:
            path: Output file path, None to return as string only
            include_categories: Whether to include category info

        Returns:
            JSON string
        """
        return export_aliases(path, include_categories)

    def validate(
        self, aliases: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[str]]:
        """
        Validate alias validity.

        Args:
            aliases: Alias mapping to validate, None validates all current aliases

        Returns:
            Dict containing 'valid', 'invalid', 'warnings'
        """
        return validate_aliases(aliases)

    def import_file(self, path: str) -> int:
        """
        Import aliases from a JSON file.

        Args:
            path: JSON file path

        Returns:
            Number of aliases successfully imported
        """
        import json
        from pathlib import Path as _Path

        p = _Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Alias file not found: {path}")

        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        flattened: Dict[str, str] = {}
        for k, v in data.items():
            if isinstance(v, dict):
                flattened.update(v)
            elif isinstance(v, str):
                flattened[k] = v

        registered = self.register_many(flattened)
        return len(registered)

    def search(self, pattern: str) -> List[str]:
        """
        Search for aliases matching a specified pattern.

        Args:
            pattern: Search pattern (substring match)

        Returns:
            List of matching aliases
        """
        pattern_lower = pattern.lower()
        return [
            alias for alias in _ALIAS_MAP
            if pattern_lower in alias.lower()
        ]

    # ---- Dict-style API ----

    def __setitem__(self, alias: str, module_name: str) -> None:
        register_alias(alias, module_name)

    def __getitem__(self, alias: str) -> Any:
        if alias not in _ALIAS_MAP:
            raise KeyError(f"Alias '{alias}' not found. Register it first.")
        return _get_lazy_module(alias)

    def __delitem__(self, alias: str) -> None:
        if not self.unregister(alias):
            raise KeyError(f"Alias '{alias}' not found")

    def __contains__(self, alias: str) -> bool:
        return alias in _ALIAS_MAP

    def __len__(self) -> int:
        return len(_ALIAS_MAP)

    def __iter__(self) -> Iterator[str]:
        return iter(_ALIAS_MAP)

    def keys(self) -> List[str]:
        return list(_ALIAS_MAP.keys())

    def values(self) -> List[str]:
        return list(_ALIAS_MAP.values())

    def items(self) -> List[Tuple[str, str]]:
        return list(_ALIAS_MAP.items())

    def get(self, alias: str, default: Optional[str] = None) -> Optional[str]:
        return _ALIAS_MAP.get(alias, default)

    def __repr__(self) -> str:
        return f"<AliasNamespace: {len(self)} aliases>"


# ═══════════════════════════════════════════════════════════════
#  SymbolNamespace
# ═══════════════════════════════════════════════════════════════

class SymbolIndexNamespace:
    """Symbol index management sub-namespace"""

    def build(self, force: bool = False, max_modules: int = 100, timeout: float = 30.0) -> None:
        """
        Build/rebuild the symbol index.

        Args:
            force: Whether to force rebuild
            max_modules: Maximum number of modules to scan
            timeout: Timeout in seconds
        """
        _build_symbol_index(force=force, max_modules=max_modules, timeout=timeout)

    def rebuild(self) -> None:
        """Force rebuild the symbol index"""
        rebuild_symbol_index()

    def incremental(self) -> bool:
        """
        Perform incremental index build.

        Returns:
            Whether successful
        """
        return _build_incremental_symbol_index()

    def reset(self) -> None:
        """Reset symbol cache (does not clear index files)"""
        clear_symbol_cache()

    def clear(self) -> None:
        """Clear symbol cache (alias for reset)"""
        clear_symbol_cache()

    @property
    def built(self) -> bool:
        """Whether the index has been built"""
        return _config._SYMBOL_INDEX_BUILT

    @property
    def count(self) -> int:
        """Number of indexed symbols"""
        return len(_config._SYMBOL_CACHE)

    @property
    def is_built(self) -> bool:
        """Whether the index has been built (alias for built)"""
        return self.built

    def __repr__(self) -> str:
        return f"<SymbolIndex: built={self.built}, symbols={self.count}>"


class SymbolConfigNamespace:
    """
    Symbol search and resolution configuration sub-namespace.

    All modifications are synced in real-time to the underlying _config global state.
    """

    # ---- Toggles ----

    def enable(self) -> None:
        """Enable symbol search"""
        enable_symbol_search()

    def disable(self) -> None:
        """Disable symbol search"""
        disable_symbol_search()

    @property
    def enabled(self) -> bool:
        """Whether symbol search is enabled"""
        return is_symbol_search_enabled()

    # ---- Search parameters ----

    @property
    def interactive(self) -> bool:
        return get_symbol_search_config().get("interactive", True)

    @interactive.setter
    def interactive(self, value: bool) -> None:
        _config._SYMBOL_SEARCH_CONFIG["interactive"] = value

    @property
    def exact_params(self) -> bool:
        return get_symbol_search_config().get("exact_params", False)

    @exact_params.setter
    def exact_params(self, value: bool) -> None:
        _config._SYMBOL_SEARCH_CONFIG["exact_params"] = value

    @property
    def max_results(self) -> int:
        return get_symbol_search_config().get("max_results", 5)

    @max_results.setter
    def max_results(self, value: int) -> None:
        _config._SYMBOL_SEARCH_CONFIG["max_results"] = value

    @property
    def search_depth(self) -> int:
        return get_symbol_search_config().get("search_depth", 1)

    @search_depth.setter
    def search_depth(self, value: int) -> None:
        _config._SYMBOL_SEARCH_CONFIG["search_depth"] = value

    @property
    def skip_private(self) -> bool:
        return get_symbol_search_config().get("skip_private", True)

    @skip_private.setter
    def skip_private(self, value: bool) -> None:
        _config._SYMBOL_SEARCH_CONFIG["skip_private"] = value

    @property
    def skip_stdlib(self) -> bool:
        return get_symbol_search_config().get("skip_stdlib", False)

    @skip_stdlib.setter
    def skip_stdlib(self, value: bool) -> None:
        _config._SYMBOL_SEARCH_CONFIG["skip_stdlib"] = value

    @property
    def cache_enabled(self) -> bool:
        return get_symbol_search_config().get("cache_enabled", True)

    @cache_enabled.setter
    def cache_enabled(self, value: bool) -> None:
        _config._SYMBOL_SEARCH_CONFIG["cache_enabled"] = value

    # ---- Resolution parameters ----

    @property
    def auto_resolution(self) -> bool:
        return get_symbol_resolution_config().get("auto_symbol", True)

    @auto_resolution.setter
    def auto_resolution(self, value: bool) -> None:
        if value:
            enable_auto_symbol_resolution()
        else:
            disable_auto_symbol_resolution()

    @property
    def auto_threshold(self) -> float:
        return get_symbol_resolution_config().get("auto_threshold", 0.7)

    @auto_threshold.setter
    def auto_threshold(self, value: float) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["auto_threshold"] = value

    @property
    def conflict_threshold(self) -> float:
        return get_symbol_resolution_config().get("conflict_threshold", 0.3)

    @conflict_threshold.setter
    def conflict_threshold(self, value: float) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["conflict_threshold"] = value

    @property
    def misspelling(self) -> bool:
        return get_symbol_resolution_config().get("symbol_misspelling", True)

    @misspelling.setter
    def misspelling(self, value: bool) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["symbol_misspelling"] = value

    @property
    def context_aware(self) -> bool:
        return get_symbol_resolution_config().get("context_aware", True)

    @context_aware.setter
    def context_aware(self, value: bool) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["context_aware"] = value

    @property
    def warn_on_conflict(self) -> bool:
        return get_symbol_resolution_config().get("warn_on_conflict", True)

    @warn_on_conflict.setter
    def warn_on_conflict(self, value: bool) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["warn_on_conflict"] = value

    @property
    def save_preferences(self) -> bool:
        return get_symbol_resolution_config().get("save_preferences", True)

    @save_preferences.setter
    def save_preferences(self, value: bool) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["save_preferences"] = value

    # ---- Export / snapshot ----

    def snapshot(self) -> Dict[str, Any]:
        """Get a complete snapshot of search + resolution config"""
        return {
            "search": dict(get_symbol_search_config()),
            "resolution": dict(get_symbol_resolution_config()),
        }

    def export(self, path: Optional[str] = None) -> str:
        """Export config as JSON"""
        import json
        data = self.snapshot()
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        return json.dumps(data, indent=2)

    def __repr__(self) -> str:
        return (
            f"<SymbolConfig: enabled={self.enabled}, "
            f"auto_resolution={self.auto_resolution}>"
        )


class SymbolNamespace:
    """
    Symbol search namespace.

    Usage:
        lz.symbol.search('DataFrame')          # Search symbols
        lz.symbol.which('sqrt')                # Find definition location
        lz.symbol.which_all('sqrt')            # Find all locations
        lz.symbol.prefer('DF', 'pandas')       # Set preference
        lz.symbol.preference('DF')             # Get preference
        lz.symbol.conflicts()                  # Get all conflicts
        lz.symbol.index.build()                # Build index
        lz.symbol.index.reset()                # Reset index
        lz.symbol.config.enabled = False       # Configure
        lz.symbol.config.sharding.enable()     # Sharded search
    """

    # ---- Search ----

    def search(
        self,
        name: str,
        symbol_type: Optional[str] = None,
        signature: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[Any]:
        """
        Search for symbols.

        Args:
            name: Symbol name (supports fuzzy matching)
            symbol_type: Type filter ('class', 'function', 'callable')
            signature: Signature filter
            max_results: Maximum number of results

        Returns:
            List[SearchResult]
        """
        return search_symbol(name, symbol_type, signature, max_results)

    def sharded(self, name: str, max_results: int = 5) -> List[Any]:
        """Search using sharded index (faster for large datasets)"""
        return search_with_sharding(name, max_results)

    # ---- Location lookup ----

    def which(
        self,
        name: str,
        module_hint: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Find where a symbol is defined (returns first match).

        Args:
            name: Symbol name (supports "module.symbol" format)
            module_hint: Optional module hint

        Returns:
            SymbolLocation or None
        """
        return which(name, module_hint)

    def which_all(self, name: str) -> List[Any]:
        """
        Find all locations where a symbol is defined.

        Args:
            name: Symbol name

        Returns:
            List[SymbolLocation]
        """
        return which_all(name)

    # ---- Preferences ----

    def prefer(self, symbol: str, module: str) -> None:
        """Set preferred module for a symbol"""
        set_symbol_preference(symbol, module)

    def preference(self, symbol: str) -> Optional[str]:
        """Get preferred module for a symbol"""
        return get_symbol_preference(symbol)

    def clear_preference(self, symbol: str) -> bool:
        """Clear symbol preference"""
        return clear_symbol_preference(symbol)

    # ---- Conflicts ----

    def conflicts(self, symbol: Optional[str] = None) -> Any:
        """
        Get symbol conflict information.

        Args:
            symbol: If provided, return conflicts for this symbol only; otherwise return all

        Returns:
            SymbolConflict (single symbol) or Dict[str, SymbolConflict] (all)
        """
        from .._analysis._conflict import find_symbol_conflicts
        all_conflicts = find_symbol_conflicts()
        if symbol:
            return all_conflicts.get(symbol)
        return all_conflicts

    def conflict_summary(self) -> Dict[str, Any]:
        """Get conflict summary statistics"""
        from .._analysis._conflict import get_conflicts_summary
        return get_conflicts_summary()

    def show_conflicts(self, symbol_filter: Optional[str] = None, max_results: int = 20) -> None:
        """Display formatted symbol conflicts"""
        from .._analysis._conflict import show_conflicts
        show_conflicts(symbol_filter, max_results)

    # ---- Configuration ----

    @property
    def config(self) -> SymbolConfigNamespace:
        """Search/resolution configuration"""
        return _SYMBOL_CONFIG_NS

    # ---- Index ----

    @property
    def index(self) -> SymbolIndexNamespace:
        """Index management"""
        return _SYMBOL_INDEX_NS

    # ---- Cache info ----

    def cache_info(self) -> Dict[str, Any]:
        """Get symbol cache information"""
        return get_symbol_cache_info()

    # ---- Internal methods (advanced users) ----

    def _search_direct(self, name: str, symbol_type=None, signature=None, max_results=None) -> List[Any]:
        """Direct search (no fuzzy matching)"""
        return _search_symbol_direct(name, symbol_type, signature, max_results)

    def _enhanced(self, name: str, auto: bool = True, symbol_type=None) -> Optional[Any]:
        """Enhanced search (with auto-resolution and spell correction)"""
        return _search_symbol_enhanced(name, auto, symbol_type)

    def __repr__(self) -> str:
        info = get_symbol_cache_info()
        return f"<SymbolNamespace: {info.get('symbol_count', 0)} symbols, built={info.get('built', False)}>"


# ═══════════════════════════════════════════════════════════════
#  CacheNamespaces
# ═══════════════════════════════════════════════════════════════

class CacheSymbolsNamespace:
    """Symbol cache sub-namespace"""

    def clear(self) -> None:
        """Clear all symbol cache (memory)"""
        clear_symbol_cache()

    def reset(self) -> None:
        """Reset and rebuild index"""
        clear_symbol_cache()
        rebuild_symbol_index()

    @property
    def count(self) -> int:
        return len(_config._SYMBOL_CACHE)

    @property
    def stdlib_count(self) -> int:
        return len(_config._STDLIB_SYMBOL_CACHE)

    @property
    def third_party_count(self) -> int:
        return len(_config._THIRD_PARTY_SYMBOL_CACHE)

    def __repr__(self) -> str:
        return (
            f"<SymbolCache: {self.count} total, "
            f"{self.stdlib_count} stdlib, "
            f"{self.third_party_count} third-party>"
        )


class CacheFilesNamespace:
    """File cache sub-namespace"""

    def clear(self, file_path: Optional[str] = None) -> int:
        """
        Clear file cache.

        Args:
            file_path: If provided, clear cache for this file only; otherwise clear all

        Returns:
            Number of deleted cache files
        """
        return clear_file_cache(file_path)

    def info(self) -> Dict[str, Any]:
        """Get file cache details"""
        return get_file_cache_info()

    def force_save(self) -> bool:
        """Force save current file cache"""
        return force_save_cache()

    @property
    def enabled(self) -> bool:
        return is_file_cache_enabled()

    @enabled.setter
    def enabled(self, value: bool) -> None:
        if value:
            enable_file_cache()
        else:
            disable_file_cache()

    def __repr__(self) -> str:
        info = get_file_cache_info()
        return f"<FileCache: enabled={info['enabled']}, files={info['loaded_modules_count']}>"


class CacheStatsNamespace:
    """
    Cache statistics namespace.

    Supports attribute-style access to statistics.
    Usage: lz.cache.stats.hit_rate, lz.cache.stats['symbol_hits'] etc.
    """

    def _get_stats(self) -> Dict[str, Any]:
        return get_cache_stats()

    @property
    def hit_rate(self) -> float:
        return self._get_stats().get("hit_rate", 0.0)

    @property
    def symbol_hits(self) -> int:
        return self._get_stats().get("symbol_hits", 0)

    @property
    def symbol_misses(self) -> int:
        return self._get_stats().get("symbol_misses", 0)

    @property
    def module_hits(self) -> int:
        return self._get_stats().get("module_hits", 0)

    @property
    def module_misses(self) -> int:
        return self._get_stats().get("module_misses", 0)

    @property
    def total_requests(self) -> int:
        return self._get_stats().get("total_requests", 0)

    @property
    def last_build_time(self) -> float:
        return self._get_stats().get("last_build_time", 0.0)

    @property
    def build_count(self) -> int:
        return self._get_stats().get("build_count", 0)

    def reset(self) -> None:
        """Reset all statistics to zero"""
        reset_cache_stats()

    def __getitem__(self, key: str) -> Any:
        stats = self._get_stats()
        if key not in stats:
            raise KeyError(key)
        return stats[key]

    def __getattr__(self, name: str) -> Any:
        stats = self._get_stats()
        if name in stats:
            return stats[name]
        raise AttributeError(f"CacheStats has no attribute '{name}'")

    def __contains__(self, key: str) -> bool:
        return key in self._get_stats()

    def keys(self) -> List[str]:
        return list(self._get_stats().keys())

    def items(self) -> List[Tuple[str, Any]]:
        return list(self._get_stats().items())

    def __repr__(self) -> str:
        s = self._get_stats()
        return f"<CacheStats: hits={s.get('total_requests', 0)}, rate={s.get('hit_rate', 0):.1%}>"


class CacheConfigNamespace:
    """Cache config sub-namespace"""

    def __getitem__(self, key: str) -> Any:
        cfg = get_cache_config()
        if key not in cfg:
            raise KeyError(key)
        return cfg[key]

    def __setitem__(self, key: str, value: Any) -> None:
        set_cache_config(**{key: value})

    @property
    def max_size_mb(self) -> int:
        return get_cache_config().get("max_cache_size_mb", 100)

    @max_size_mb.setter
    def max_size_mb(self, value: int) -> None:
        set_cache_config(max_cache_size_mb=value)

    @property
    def symbol_index_ttl(self) -> int:
        return get_cache_config().get("symbol_index_ttl", 86400)

    @symbol_index_ttl.setter
    def symbol_index_ttl(self, value: int) -> None:
        set_cache_config(symbol_index_ttl=value)

    @property
    def stdlib_cache_ttl(self) -> int:
        return get_cache_config().get("stdlib_cache_ttl", 604800)

    @stdlib_cache_ttl.setter
    def stdlib_cache_ttl(self, value: int) -> None:
        set_cache_config(stdlib_cache_ttl=value)

    @property
    def third_party_cache_ttl(self) -> int:
        return get_cache_config().get("third_party_cache_ttl", 86400)

    @third_party_cache_ttl.setter
    def third_party_cache_ttl(self, value: int) -> None:
        set_cache_config(third_party_cache_ttl=value)

    @property
    def symbol_index_enabled(self) -> bool:
        return get_cache_config().get("symbol_index_enabled", True)

    @symbol_index_enabled.setter
    def symbol_index_enabled(self, value: bool) -> None:
        set_cache_config(symbol_index_enabled=value)

    @property
    def compression(self) -> bool:
        return get_cache_config().get("enable_compression", False)

    @compression.setter
    def compression(self, value: bool) -> None:
        enable_cache_compression(value)

    def snapshot(self) -> Dict[str, Any]:
        """Get cache config snapshot"""
        return dict(get_cache_config())

    def export(self, path: Optional[str] = None) -> str:
        """Export as JSON"""
        import json
        data = dict(get_cache_config())
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        return json.dumps(data, indent=2)

    def __repr__(self) -> str:
        return f"<CacheConfig: max={self.max_size_mb}MB, compression={self.compression}>"


class CacheNamespace:
    """
    Cache management namespace.

    Usage:
        lz.cache.clear()                  # Clear all cache
        lz.cache.symbols.clear()          # Clear symbol cache only
        lz.cache.files.clear()            # Clear file cache only
        lz.cache.stats                    # Statistics (attribute access)
        lz.cache.stats.reset()            # Reset statistics
        lz.cache.dir                      # Cache directory
        lz.cache.dir = '/new/path'        # Set cache directory
        lz.cache.compression = True       # Enable compression
    """

    @property
    def symbols(self) -> CacheSymbolsNamespace:
        """Symbol cache management"""
        return _CACHE_SYMBOLS_NS

    @property
    def files(self) -> CacheFilesNamespace:
        """File cache management"""
        return _CACHE_FILES_NS

    @property
    def stats(self) -> CacheStatsNamespace:
        """Cache statistics"""
        return _CACHE_STATS_NS

    @property
    def config(self) -> CacheConfigNamespace:
        """Detailed cache configuration"""
        return _CACHE_CONFIG_NS

    # ---- Core operations ----

    def clear(self) -> None:
        """Clear all cache (module + symbol + file)"""
        clear_cache()

    # ---- Directory ----

    @property
    def dir(self) -> Path:
        """Cache directory path"""
        return get_cache_dir()

    @dir.setter
    def dir(self, value: Union[str, Path]) -> None:
        set_cache_dir(value)

    def reset_dir(self) -> None:
        """Reset to default cache directory"""
        reset_cache_dir()

    # ---- Compression ----

    @property
    def compression(self) -> bool:
        return get_cache_config().get("enable_compression", False)

    @compression.setter
    def compression(self, value: bool) -> None:
        enable_cache_compression(value)

    def __repr__(self) -> str:
        return f"<CacheNamespace: dir={self.dir}>"


# ═══════════════════════════════════════════════════════════════
#  ConfigNamespace
# ═══════════════════════════════════════════════════════════════

class ConfigNamespace:
    """
    Global configuration namespace.

    All modifications are synced in real-time to the underlying _config global state.

    Usage:
        lz.config.debug = True
        lz.config.auto_search = False
        lz.config.auto_install.enabled = True
        lz.config.cache.max_size_mb = 500
        lz.config.symbol_search.max_results = 10
    """

    # ---- Debug ----

    @property
    def debug(self) -> bool:
        return _config._DEBUG_MODE

    @debug.setter
    def debug(self, value: bool) -> None:
        _config._DEBUG_MODE = value

    # ---- Auto search ----

    @property
    def auto_search(self) -> bool:
        return _config._AUTO_SEARCH_ENABLED

    @auto_search.setter
    def auto_search(self, value: bool) -> None:
        _config._AUTO_SEARCH_ENABLED = value

    # ---- Auto install ----

    @property
    def auto_install(self) -> AutoInstallConfig:
        """Get auto-install configuration snapshot"""
        c = _config._AUTO_INSTALL_CONFIG
        return AutoInstallConfig(
            enabled=c["enabled"],
            interactive=c["interactive"],
            index=c["index"],
            extra_args=list(c["extra_args"]),
            prefer_uv=c["prefer_uv"],
            silent=c["silent"],
        )

    @auto_install.setter
    def auto_install(self, cfg: AutoInstallConfig) -> None:
        """Set auto-install configuration"""
        _config._AUTO_INSTALL_CONFIG["enabled"] = cfg.enabled
        _config._AUTO_INSTALL_CONFIG["interactive"] = cfg.interactive
        _config._AUTO_INSTALL_CONFIG["index"] = cfg.index
        _config._AUTO_INSTALL_CONFIG["extra_args"] = list(cfg.extra_args)
        _config._AUTO_INSTALL_CONFIG["prefer_uv"] = cfg.prefer_uv
        _config._AUTO_INSTALL_CONFIG["silent"] = cfg.silent

    @property
    def auto_install_enabled(self) -> bool:
        return _config._AUTO_INSTALL_CONFIG["enabled"]

    @auto_install_enabled.setter
    def auto_install_enabled(self, value: bool) -> None:
        _config._AUTO_INSTALL_CONFIG["enabled"] = value

    # ---- Retry ----

    @property
    def retry(self) -> RetryConfig:
        """Get retry configuration snapshot"""
        c = _config._RETRY_CONFIG
        return RetryConfig(
            enabled=c["enabled"],
            max_retries=c["max_retries"],
            retry_delay=c["retry_delay"],
            modules=set(c["retry_modules"]),
        )

    @retry.setter
    def retry(self, cfg: RetryConfig) -> None:
        _config._RETRY_CONFIG["enabled"] = cfg.enabled
        _config._RETRY_CONFIG["max_retries"] = cfg.max_retries
        _config._RETRY_CONFIG["retry_delay"] = cfg.retry_delay
        _config._RETRY_CONFIG["retry_modules"] = cfg.modules

    # ---- Symbol search configuration (shortcut access) ----

    @property
    def symbol_search(self) -> SymbolSearchConfig:
        return SymbolSearchConfig(**get_symbol_search_config())

    @symbol_search.setter
    def symbol_search(self, cfg: SymbolSearchConfig) -> None:
        _apply_search_config(cfg)

    @property
    def symbol_resolution(self) -> SymbolResolutionConfig:
        return SymbolResolutionConfig(**get_symbol_resolution_config())

    @symbol_resolution.setter
    def symbol_resolution(self, cfg: SymbolResolutionConfig) -> None:
        _apply_resolution_config(cfg)

    # ---- Cache configuration (shortcut access) ----

    @property
    def cache(self) -> CacheConfig:
        return CacheConfig(**get_cache_config())

    @cache.setter
    def cache(self, cfg: CacheConfig) -> None:
        set_cache_config(
            max_cache_size_mb=cfg.max_size_mb,
            symbol_index_ttl=cfg.symbol_index_ttl,
            stdlib_cache_ttl=cfg.stdlib_cache_ttl,
            third_party_cache_ttl=cfg.third_party_cache_ttl,
            enable_compression=cfg.enable_compression,
        )

    # ---- Module skip configuration ----

    @property
    def module_skip(self) -> ModuleSkipConfig:
        return ModuleSkipConfig(**get_module_skip_config())

    @module_skip.setter
    def module_skip(self, cfg: ModuleSkipConfig) -> None:
        set_module_skip_config(
            skip_test_modules=cfg.skip_test_modules,
            skip_internal_modules=cfg.skip_internal_modules,
            skip_large_modules=cfg.skip_large_modules,
            large_module_threshold=cfg.large_module_threshold,
        )

    # ---- Import statistics ----

    @property
    def import_stats(self) -> Dict[str, Any]:
        return get_import_stats()

    # ---- Export / snapshot ----

    def snapshot(self) -> Dict[str, Any]:
        """
        Create a complete snapshot of all current configurations.

        Returns:
            Dictionary containing all configurations
        """
        return {
            "debug": self.debug,
            "auto_search": self.auto_search,
            "auto_install": asdict(self.auto_install),
            "retry": asdict(self.retry),
            "symbol_search": asdict(self.symbol_search),
            "symbol_resolution": asdict(self.symbol_resolution),
            "cache": asdict(self.cache),
            "module_skip": asdict(self.module_skip),
        }

    def restore(self, snapshot: Dict[str, Any]) -> None:
        """
        Restore configuration from a snapshot.

        Args:
            snapshot: Snapshot dictionary created by snapshot()
        """
        if "debug" in snapshot:
            self.debug = snapshot["debug"]
        if "auto_search" in snapshot:
            self.auto_search = snapshot["auto_search"]
        if "auto_install" in snapshot:
            self.auto_install = AutoInstallConfig(**snapshot["auto_install"])
        if "retry" in snapshot:
            self.retry = RetryConfig(**snapshot["retry"])
        if "symbol_search" in snapshot:
            self.symbol_search = SymbolSearchConfig(**snapshot["symbol_search"])
        if "symbol_resolution" in snapshot:
            self.symbol_resolution = SymbolResolutionConfig(**snapshot["symbol_resolution"])
        if "cache" in snapshot:
            self.cache = CacheConfig(**snapshot["cache"])
        if "module_skip" in snapshot:
            self.module_skip = ModuleSkipConfig(**snapshot["module_skip"])

    def export(self, path: Optional[str] = None) -> str:
        """
        Export configuration as JSON.

        Args:
            path: Output file path, None to return as string only

        Returns:
            JSON string (if path is None)
        """
        import json
        data = self.snapshot()
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        return json.dumps(data, indent=2)

    # ---- Context manager ----

    def temp_config(self, **kwargs: Any) -> "ConfigContext":
        """
        Create a temporary configuration context that auto-restores on exit.

        Usage:
            with lz.config.temp_config(debug=True, auto_search=False):
                # debug=True, auto_search=False within this scope
            # Values restored after exit
        """
        return ConfigContext(kwargs)

    def __repr__(self) -> str:
        return f"<ConfigNamespace: debug={self.debug}, auto_search={self.auto_search}>"


class ConfigContext:
    """
    Temporary configuration context manager.

    Usage:
        with lz.config.temp_config(debug=True):
            pass  # Auto-restores after exit
    """

    def __init__(self, overrides: Dict[str, Any]) -> None:
        self._overrides = overrides
        self._snap: Dict[str, Any] = {}
        self._entered = False

    def __enter__(self) -> "ConfigContext":
        from .._api import _global_config
        self._snap = _global_config.snapshot()
        self._entered = True
        for key, value in self._overrides.items():
            if hasattr(_global_config, key):
                setattr(_global_config, key, value)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._entered:
            from .._api import _global_config
            _global_config.restore(self._snap)


# ═══════════════════════════════════════════════════════════════
#  AnalyzeNamespace
# ═══════════════════════════════════════════════════════════════

class AnalyzeNamespace:
    """
    Code analysis namespace.

    Usage:
        result = lz.analyze.file('script.py')
        result = lz.analyze.code('import numpy')
        results = lz.analyze.dir('/path/to/project')
        tree = lz.analyze.dep_tree('.')
    """

    def file(self, file_path: str) -> Any:
        """Analyze a Python file to predict required imports"""
        from .._analysis._preanalyze import DependencyPreAnalyzer
        analyzer = DependencyPreAnalyzer()
        return analyzer.analyze_file(file_path)

    def code(self, source: str, file_path: str = "<string>") -> Any:
        """Analyze source code to predict required imports"""
        from .._analysis._preanalyze import DependencyPreAnalyzer
        analyzer = DependencyPreAnalyzer()
        return analyzer.analyze_source(source, file_path)

    def dir(
        self,
        dir_path: str,
        recursive: bool = True,
        exclude: Optional[Set[str]] = None,
    ) -> List[Any]:
        """Analyze all Python files in a directory"""
        from .._analysis._preanalyze import DependencyPreAnalyzer
        analyzer = DependencyPreAnalyzer()
        return analyzer.analyze_directory(dir_path, recursive, exclude)

    def dep_tree(
        self,
        dir_path: str = ".",
        max_depth: int = 3,
        exclude: Optional[Set[str]] = None,
    ) -> Any:
        """Generate a dependency tree"""
        from .._analysis._dependency import dependency_tree
        return dependency_tree(dir_path, max_depth=max_depth, exclude=exclude)

    def __repr__(self) -> str:
        return "<AnalyzeNamespace>"


# ═══════════════════════════════════════════════════════════════
#  ProfileNamespace
# ═══════════════════════════════════════════════════════════════

class ProfileNamespace:
    """
    Profiling namespace.

    Usage:
        lz.profile.start()
        # ... do work ...
        lz.profile.stop()
        lz.profile.print_report()
    """

    def start(self) -> None:
        """Start profiling"""
        from .._analysis._profiler import start_profiling
        start_profiling()

    def stop(self) -> None:
        """Stop profiling"""
        from .._analysis._profiler import stop_profiling
        stop_profiling()

    def report(self, print_report: bool = False) -> Any:
        """
        Get profiling report.

        Args:
            print_report: If True, also print the report

        Returns:
            ProfileReport object
        """
        from .._analysis._profiler import get_profile_report, print_profile_report
        if print_report:
            print_profile_report()
        return get_profile_report()

    def print_report(self) -> None:
        """Print profiling report"""
        from .._analysis._profiler import print_profile_report
        print_profile_report()

    @property
    def is_active(self) -> bool:
        """Whether the profiler is currently running"""
        from .._analysis._profiler import _profiler
        return _profiler.is_active()

    def __repr__(self) -> str:
        return f"<ProfileNamespace: active={self.is_active}>"


# ═══════════════════════════════════════════════════════════════
#  AsyncNamespace
# ═══════════════════════════════════════════════════════════════

class AsyncNamespace:
    """
    Async operations namespace.

    Usage:
        mod = await lz.async.get('numpy')
        mods = await lz.async.fetch('numpy', 'pandas', 'torch')
    """

    async def get(self, alias: str) -> Any:
        """Asynchronously import a single module"""
        return await import_async(alias)

    async def fetch(self, *aliases: str) -> Dict[str, Any]:
        """Asynchronously import multiple modules in parallel"""
        return await import_multiple_async(list(aliases))

    def __repr__(self) -> str:
        return "<AsyncNamespace>"


# ═══════════════════════════════════════════════════════════════
#  InstallNamespace
# ═══════════════════════════════════════════════════════════════

class InstallNamespace:
    """
    Package installation namespace.

    Usage:
        lz.install.package('torch')
        lz.install.auto.enabled = True
        lz.install.rebuild_cache()
    """

    def package(
        self,
        package_name: str,
        index: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
        interactive: Optional[bool] = None,
    ) -> bool:
        """
        Install a package.

        Args:
            package_name: pip package name
            index: Optional PyPI mirror URL
            extra_args: Additional pip arguments
            interactive: Whether to confirm interactively, None means use config

        Returns:
            Whether installation succeeded
        """
        return install_package(
            package_name, index=index, extra_args=extra_args,
            interactive=interactive,
        )

    @property
    def auto(self) -> AutoInstallConfig:
        """Get current auto-install configuration"""
        return get_auto_install_config()

    @auto.setter
    def auto(self, cfg: AutoInstallConfig) -> None:
        """Set auto-install configuration"""
        _config._AUTO_INSTALL_CONFIG.update(asdict(cfg))

    def enable(
        self,
        interactive: bool = True,
        index: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
        prefer_uv: bool = False,
        silent: bool = False,
    ) -> None:
        """Enable auto-install"""
        enable_auto_install(interactive, index, extra_args, prefer_uv, silent)

    def disable(self) -> None:
        """Disable auto-install"""
        disable_auto_install()

    @property
    def enabled(self) -> bool:
        """Whether auto-install is enabled"""
        return is_auto_install_enabled()

    def rebuild_cache(self) -> None:
        """Rebuild module cache"""
        rebuild_module_cache()

    def __repr__(self) -> str:
        return f"<InstallNamespace: auto_enabled={is_auto_install_enabled()}>"


# ═══════════════════════════════════════════════════════════════
#  ExportNamespace
# ═══════════════════════════════════════════════════════════════

class ExportNamespace:
    """Export namespace"""

    def aliases(
        self,
        path: Optional[str] = None,
        include_categories: bool = True,
    ) -> str:
        """
        Export aliases.

        Args:
            path: Output file path, None to return as string only
            include_categories: Whether to include category info

        Returns:
            JSON string
        """
        return export_aliases(path, include_categories)

    def config(self, path: Optional[str] = None) -> str:
        """
        Export complete configuration (symbol search, resolution, cache, etc.).

        Args:
            path: Output file path, None to return as string only

        Returns:
            JSON string
        """
        return _global_config.export(path)

    def __repr__(self) -> str:
        return "<ExportNamespace>"


# ═══════════════════════════════════════════════════════════════
#  BackgroundNamespace
# ═══════════════════════════════════════════════════════════════

class BackgroundNamespace:
    """
    Background index building namespace.

    Usage:
        lz.background.start(callback=my_callback)
        lz.background.wait(timeout=60)
        lz.background.stop()
    """

    def start(
        self,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """
        Start background index building.

        Args:
            progress_callback: Progress callback, receives (status, progress)
            timeout: Timeout in seconds

        Returns:
            Whether successfully started (False if already built or building)
        """
        from .._lazy_index import start_background_index_build
        return start_background_index_build(progress_callback, timeout)

    def stop(self) -> None:
        """Stop background build (wait for current task to complete)"""
        from .._lazy_index import get_background_builder
        builder = get_background_builder()
        builder.stop()

    @property
    def is_building(self) -> bool:
        """Whether a build is currently in progress"""
        from .._lazy_index import is_index_building
        return is_index_building()

    def wait(self, timeout: float = 30.0) -> bool:
        """
        Wait for background build to complete.

        Args:
            timeout: Timeout in seconds

        Returns:
            Whether completed before timeout
        """
        from .._lazy_index import wait_for_index
        return wait_for_index(timeout)

    @property
    def timeout(self) -> float:
        """Get/set background build timeout"""
        from .._lazy_index import get_background_timeout
        return get_background_timeout()

    @timeout.setter
    def timeout(self, value: float) -> None:
        from .._lazy_index import set_background_timeout
        set_background_timeout(value)

    @property
    def preheat(self) -> Dict[str, Any]:
        """Preheat configuration"""
        return get_preheat_config()

    def enable(self, enabled: bool = True) -> None:
        """Enable/disable background building"""
        enable_background_build(enabled)

    def __repr__(self) -> str:
        return f"<BackgroundNamespace: building={self.is_building}>"


# ═══════════════════════════════════════════════════════════════
#  HookNamespace
# ═══════════════════════════════════════════════════════════════

class HookNamespace:
    """
    Hook management namespace.

    Usage:
        lz.hooks.pre += my_pre_hook     # Equivalent to add_pre_import_hook
        lz.hooks.post += my_post_hook   # Equivalent to add_post_import_hook
        lz.hooks.pre -= my_pre_hook     # Equivalent to remove_pre_import_hook
        lz.hooks.clear()                # Equivalent to clear_import_hooks
    """

    @property
    def pre(self) -> HookList:
        """Pre-import hooks (called before module import)"""
        return HookList(_config._PRE_IMPORT_HOOKS)

    @property
    def post(self) -> HookList:
        """Post-import hooks (called after module import)"""
        return HookList(_config._POST_IMPORT_HOOKS)

    def clear(self) -> None:
        """Clear all hooks"""
        _config._PRE_IMPORT_HOOKS.clear()
        _config._POST_IMPORT_HOOKS.clear()

    def __repr__(self) -> str:
        return (
            f"<HookNamespace: pre={len(_config._PRE_IMPORT_HOOKS)}, "
            f"post={len(_config._POST_IMPORT_HOOKS)}>"
        )


# ═══════════════════════════════════════════════════════════════
#  VersionNamespace
# ═══════════════════════════════════════════════════════════════

class VersionNamespace:
    """Version information namespace"""

    @property
    def current(self) -> str:
        """laziest-import version number"""
        return _config.__version__

    def of(self, package: str) -> Optional[str]:
        """Get the version of an installed package"""
        return get_package_version(package)

    def all_packages(self) -> Dict[str, str]:
        """Get versions of all installed packages"""
        return get_all_package_versions()

    def laziest_import(self) -> str:
        """Get laziest-import version (equivalent to current)"""
        return get_laziest_import_version()

    def cache(self) -> str:
        """Get cache version"""
        return get_cache_version()

    # Support str() conversion
    def __str__(self) -> str:
        return self.current

    def __repr__(self) -> str:
        return f"<VersionNamespace: v{self.current}>"


# ═══════════════════════════════════════════════════════════════
#  RCConfigNamespace
# ═══════════════════════════════════════════════════════════════

class RCConfigNamespace:
    """RC config file management namespace"""

    def load(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load RC configuration"""
        return load_rc_config(force_reload)

    def get(self, key: str, default: Any = None) -> Any:
        """Get an RC config value"""
        return get_rc_value(key, default)

    def create(self, path: Optional[str] = None, template: bool = True) -> Path:
        """Create an RC file"""
        return create_rc_file(path, template)

    def save(self, config: Dict[str, Any], path: Optional[str] = None) -> Path:
        """Save RC configuration"""
        return save_rc_config(config, path)

    def paths(self) -> List[str]:
        """List all RC file paths"""
        return [str(p) for p in _LAZIESTRC_PATHS]

    @property
    def paths_list(self) -> List[str]:
        """RC file path list"""
        return self.paths()

    def reload(self) -> Dict[str, Any]:
        """Force reload RC configuration"""
        return reload_rc_config()

    def info(self) -> Dict[str, Any]:
        """Get RC configuration info"""
        return get_rc_info()

    def __repr__(self) -> str:
        active = find_rc_file()
        return f"<RCConfigNamespace: active={active}>"


# ═══════════════════════════════════════════════════════════════
#  LazyImport (main class)
# ═══════════════════════════════════════════════════════════════

# Singleton reference, used internally by ConfigContext
_global_config: Optional["ConfigNamespace"] = None


class LazyImport:
    """
    Unified object-oriented API entry point for laziest-import.

    All namespaces are accessed via properties:

        from laziest_import import LazyImport
        lz = LazyImport()

        # Module loading
        np = lz.module.numpy
        pd = lz.module.get('pandas')

        # Configuration
        lz.config.debug = True
        lz.config.auto_install.enabled = True

        # Symbol search
        results = lz.symbol.search('DataFrame')
        loc = lz.symbol.which('sqrt')

        # Alias management (dict-style)
        lz.alias['my_np'] = 'numpy'
        mod = lz.alias['my_np']

        # Caching
        lz.cache.symbols.clear()
        lz.cache.files.clear()
        stats = lz.cache.stats

        # Hooks
        lz.hooks.pre += my_pre_hook
        lz.hooks.post += my_post_hook

        # Async
        mod = await lz.async.get('numpy')
        mods = await lz.async.fetch('numpy', 'pandas')

        # Analysis
        result = lz.analyze.file('script.py')
        result = lz.analyze.code('import numpy')

        # Profiling
        with lz.config.temp_config(debug=True):
            lz.profile.start()
            # ... do work ...
            lz.profile.stop()
            lz.profile.print_report()

        # Export
        lz.alias.export('/path/aliases.json')
        lz.config.export('/path/config.json')

        # RC config
        rc = lz.rc.load()
        lz.rc.create('/path/.laziestrc')

    Note:
        - Multiple LazyImport() instances can be created; they all share the same global state
        - Recommended to create a singleton: lz = LazyImport()
        - Or use module-level convenience functions: from laziest_import import lz
    """

    def __init__(self) -> None:
        """Create a LazyImport instance. All instances share the same _config global state."""
        # Lazy initialization of namespaces (avoid circular imports)
        self._module_ns: Optional[ModuleNamespace] = None
        self._alias_ns: Optional[AliasNamespace] = None
        self._symbol_ns: Optional[SymbolNamespace] = None
        self._cache_ns: Optional[CacheNamespace] = None
        self._config_ns: Optional[ConfigNamespace] = None
        self._analyze_ns: Optional[AnalyzeNamespace] = None
        self._profile_ns: Optional[ProfileNamespace] = None
        self._hooks_ns: Optional[HookNamespace] = None
        self._async_ns: Optional[AsyncNamespace] = None
        self._install_ns: Optional[InstallNamespace] = None
        self._export_ns: Optional[ExportNamespace] = None
        self._background_ns: Optional[BackgroundNamespace] = None
        self._version_ns: Optional[VersionNamespace] = None
        self._rc_ns: Optional[RCConfigNamespace] = None

    # ─── Module access ─────────────────────────────

    @property
    def module(self) -> ModuleNamespace:
        if self._module_ns is None:
            self._module_ns = ModuleNamespace()
        return self._module_ns

    # ─── Alias management ─────────────────────────────

    @property
    def alias(self) -> AliasNamespace:
        if self._alias_ns is None:
            self._alias_ns = AliasNamespace()
        return self._alias_ns

    # ─── Symbol search ─────────────────────────────

    @property
    def symbol(self) -> SymbolNamespace:
        if self._symbol_ns is None:
            self._symbol_ns = SymbolNamespace()
        return self._symbol_ns

    # ─── Cache management ─────────────────────────────

    @property
    def cache(self) -> CacheNamespace:
        if self._cache_ns is None:
            self._cache_ns = CacheNamespace()
        return self._cache_ns

    # ─── Global configuration ─────────────────────────────

    @property
    def config(self) -> ConfigNamespace:
        if self._config_ns is None:
            self._config_ns = ConfigNamespace()
        return self._config_ns

    # ─── Code analysis ─────────────────────────────

    @property
    def analyze(self) -> AnalyzeNamespace:
        if self._analyze_ns is None:
            self._analyze_ns = AnalyzeNamespace()
        return self._analyze_ns

    # ─── Profiling ─────────────────────────────

    @property
    def profile(self) -> ProfileNamespace:
        if self._profile_ns is None:
            self._profile_ns = ProfileNamespace()
        return self._profile_ns

    # ─── Hook system ─────────────────────────────

    @property
    def hooks(self) -> HookNamespace:
        if self._hooks_ns is None:
            self._hooks_ns = HookNamespace()
        return self._hooks_ns

    # ─── Async operations ─────────────────────────────

    @property
    def async_(self) -> AsyncNamespace:
        """Async operations (using async_ to avoid conflict with Python keyword async)"""
        if self._async_ns is None:
            self._async_ns = AsyncNamespace()
        return self._async_ns

    # ─── Package installation ─────────────────────────────

    @property
    def install(self) -> InstallNamespace:
        if self._install_ns is None:
            self._install_ns = InstallNamespace()
        return self._install_ns

    # ─── Export ─────────────────────────────

    @property
    def export(self) -> ExportNamespace:
        if self._export_ns is None:
            self._export_ns = ExportNamespace()
        return self._export_ns

    # ─── Background building ─────────────────────────────

    @property
    def background(self) -> BackgroundNamespace:
        if self._background_ns is None:
            self._background_ns = BackgroundNamespace()
        return self._background_ns

    # ─── Version info ─────────────────────────────

    @property
    def version(self) -> VersionNamespace:
        if self._version_ns is None:
            self._version_ns = VersionNamespace()
        return self._version_ns

    def version_of(self, package: str) -> Optional[str]:
        """Get the version of an installed package"""
        return get_package_version(package)

    # ─── RC config ─────────────────────────────

    @property
    def rc(self) -> RCConfigNamespace:
        if self._rc_ns is None:
            self._rc_ns = RCConfigNamespace()
        return self._rc_ns

    # ─── Module-level shortcut access ───────────────────────

    def __getattr__(self, name: str) -> Any:
        """
        Support lz.numpy, lz.pandas, etc. shortcuts.
        Equivalent to lz.module.numpy.
        """
        if name.startswith("_") and name != "__version__":
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # 1. Check alias map
        if name in _ALIAS_MAP:
            return _get_lazy_module(name)._get_module()

        # 2. Try auto search
        if _config._AUTO_SEARCH_ENABLED:
            found = _search_module(name)
            if found:
                _ALIAS_MAP[name] = found
                return _get_lazy_module(name)._get_module()

        # 3. Try symbol auto-resolution
        if _config._SYMBOL_RESOLUTION_CONFIG["auto_symbol"]:
            match = _search_symbol_enhanced(name, auto=True)
            if match:
                return LazySymbol(
                    symbol_name=match.symbol_name,
                    module_name=match.module_name,
                    symbol_type=match.symbol_type,
                )

            # Try interactive resolution
            if _config._SYMBOL_SEARCH_CONFIG["enabled"]:
                found_module = _handle_symbol_not_found(name)
                if found_module:
                    return _get_lazy_module(name)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'. "
            f"Try lz.module.{name} or lz.symbol.search('{name}')"
        )

    def __dir__(self) -> List[str]:
        """Support tab completion"""
        base = [
            "module", "alias", "symbol", "cache",
            "config", "analyze", "profile", "hooks",
            "async_", "install", "export", "background",
            "version", "rc",
        ]
        base.extend(_ALIAS_MAP.keys())
        return sorted(set(base))

    @property
    def __version__(self) -> str:
        return _config.__version__

    def __repr__(self) -> str:
        return (
            f"<LazyImport: v{_config.__version__}, "
            f"{len(list_loaded())} loaded, "
            f"{len(_ALIAS_MAP)} aliases>"
        )


# ═══════════════════════════════════════════════════════════════
#  Module-level singleton (for from laziest_import import lz)
# ═══════════════════════════════════════════════════════════════

#: Global LazyImport singleton instance
#: Usage: from laziest_import import lz; lz.module.numpy; lz.config.debug = True
lz = LazyImport()


# Needs to be imported after class definition (because LazySymbol references _search_symbol_enhanced)
from ._proxy._symbol import LazySymbol