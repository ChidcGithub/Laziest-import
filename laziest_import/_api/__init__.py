"""
Object-oriented API for laziest-import.

Usage:
    from laziest_import import LazyImport
    lz = LazyImport()
    arr = lz.module.numpy.array([1, 2, 3])
    lz.config.debug = True
"""

from typing import Any, Dict, List, Optional

from .. import _config as _config_module
from .._alias import _ALIAS_MAP
from .._proxy import _get_lazy_module
from .._fuzzy import _search_module
from .._symbol import _search_symbol_enhanced, _handle_symbol_not_found
from .._cache import get_package_version

# ─── Import namespace classes from sub-modules ───────────────

from ._module import (
    ModuleNamespace,
    list_loaded,
    list_available,
    get_module,
    reload_module,
)
from ._alias import AliasNamespace
from ._symbol import (
    SymbolNamespace,
    SymbolIndexNamespace,
    SymbolConfigNamespace,
)
from ._cache import (
    CacheNamespace,
    CacheSymbolsNamespace,
    CacheFilesNamespace,
    CacheStatsNamespace,
    CacheConfigNamespace,
    clear_cache,
)
from ._config import (
    ConfigNamespace,
    ConfigContext,
    AutoInstallConfig,
    RetryConfig,
    SymbolSearchConfig,
    SymbolResolutionConfig,
    CacheConfig,
    ModuleSkipConfig,
    enable_debug_mode,
    disable_debug_mode,
    is_debug_mode,
    enable_auto_search,
    disable_auto_search,
    is_auto_search_enabled,
    get_import_stats,
    reset_import_stats,
)
from ._hooks import HookList, HookNamespace
from ._analyze import AnalyzeNamespace, ProfileNamespace
from ._async import AsyncNamespace
from ._install import InstallNamespace, ExportNamespace
from ._background import BackgroundNamespace
from ._version import VersionNamespace, get_version
from ._rcconfig import RCConfigNamespace

# ─── Global config instance placeholder ──────────────────────

_global_config: Optional["ConfigNamespace"] = None


# ═══════════════════════════════════════════════════════════════
#  LazyImport (main class)
# ═══════════════════════════════════════════════════════════════

class LazyImport:
    """
    Unified object-oriented API entry point for laziest-import.

    All namespaces are accessed via properties:

        from laziest_import import LazyImport
        lz = LazyImport()

        lz.module.numpy
        lz.config.debug = True
        lz.symbol.search('DataFrame')
        lz.cache.symbols.clear()
        lz.hooks.pre += my_hook
    """

    def __init__(self) -> None:
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

    @property
    def module(self) -> ModuleNamespace:
        if self._module_ns is None:
            self._module_ns = ModuleNamespace()
        return self._module_ns

    @property
    def alias(self) -> AliasNamespace:
        if self._alias_ns is None:
            self._alias_ns = AliasNamespace()
        return self._alias_ns

    @property
    def symbol(self) -> SymbolNamespace:
        if self._symbol_ns is None:
            self._symbol_ns = SymbolNamespace()
        return self._symbol_ns

    @property
    def cache(self) -> CacheNamespace:
        if self._cache_ns is None:
            self._cache_ns = CacheNamespace()
        return self._cache_ns

    @property
    def config(self) -> ConfigNamespace:
        if self._config_ns is None:
            self._config_ns = ConfigNamespace()
        return self._config_ns

    @property
    def analyze(self) -> AnalyzeNamespace:
        if self._analyze_ns is None:
            self._analyze_ns = AnalyzeNamespace()
        return self._analyze_ns

    @property
    def profile(self) -> ProfileNamespace:
        if self._profile_ns is None:
            self._profile_ns = ProfileNamespace()
        return self._profile_ns

    @property
    def hooks(self) -> HookNamespace:
        if self._hooks_ns is None:
            self._hooks_ns = HookNamespace()
        return self._hooks_ns

    @property
    def async_(self) -> AsyncNamespace:
        if self._async_ns is None:
            self._async_ns = AsyncNamespace()
        return self._async_ns

    @property
    def install(self) -> InstallNamespace:
        if self._install_ns is None:
            self._install_ns = InstallNamespace()
        return self._install_ns

    @property
    def export(self) -> ExportNamespace:
        if self._export_ns is None:
            self._export_ns = ExportNamespace()
        return self._export_ns

    @property
    def background(self) -> BackgroundNamespace:
        if self._background_ns is None:
            self._background_ns = BackgroundNamespace()
        return self._background_ns

    @property
    def version(self) -> VersionNamespace:
        if self._version_ns is None:
            self._version_ns = VersionNamespace()
        return self._version_ns

    def version_of(self, package: str) -> Optional[str]:
        return get_package_version(package)

    @property
    def rc(self) -> RCConfigNamespace:
        if self._rc_ns is None:
            self._rc_ns = RCConfigNamespace()
        return self._rc_ns

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_") and name != "__version__":
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        if name in _ALIAS_MAP:
            return _get_lazy_module(name)._get_module()

        if _config_module._AUTO_SEARCH_ENABLED:
            found = _search_module(name)
            if found:
                _ALIAS_MAP[name] = found
                return _get_lazy_module(name)._get_module()

        if _config_module._SYMBOL_RESOLUTION_CONFIG["auto_symbol"]:
            match = _search_symbol_enhanced(name, auto=True)
            if match:
                from .._proxy._symbol import LazySymbol
                return LazySymbol(
                    symbol_name=match.symbol_name,
                    module_name=match.module_name,
                    symbol_type=match.symbol_type,
                )

            if _config_module._SYMBOL_SEARCH_CONFIG["enabled"]:
                found_module = _handle_symbol_not_found(name)
                if found_module:
                    return _get_lazy_module(name)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'. "
            f"Try lz.module.{name} or lz.symbol.search('{name}')"
        )

    def __dir__(self) -> List[str]:
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
        return _config_module.__version__

    def __repr__(self) -> str:
        return (
            f"<LazyImport: v{_config_module.__version__}, "
            f"{len(_list_loaded())} loaded, "
            f"{len(_ALIAS_MAP)} aliases>"
        )


# ═══════════════════════════════════════════════════════════════
#  Module-level singleton
# ═══════════════════════════════════════════════════════════════

lz = LazyImport()
_global_config = lz.config

# ─── Re-export all namespace classes ─────────────────────────

__all__ = [
    "LazyImport",
    "lz",
    "ModuleNamespace",
    "AliasNamespace",
    "SymbolNamespace",
    "SymbolIndexNamespace",
    "SymbolConfigNamespace",
    "CacheNamespace",
    "CacheSymbolsNamespace",
    "CacheFilesNamespace",
    "CacheStatsNamespace",
    "CacheConfigNamespace",
    "ConfigNamespace",
    "ConfigContext",
    "HookList",
    "HookNamespace",
    "AnalyzeNamespace",
    "ProfileNamespace",
    "AsyncNamespace",
    "InstallNamespace",
    "ExportNamespace",
    "BackgroundNamespace",
    "VersionNamespace",
    "RCConfigNamespace",
    "AutoInstallConfig",
    "RetryConfig",
    "SymbolSearchConfig",
    "SymbolResolutionConfig",
    "CacheConfig",
    "ModuleSkipConfig",
    # Module-level functions (for backward compat via _deprecated)
    "list_loaded",
    "list_available",
    "get_module",
    "clear_cache",
    "reload_module",
    "get_version",
    "enable_debug_mode",
    "disable_debug_mode",
    "is_debug_mode",
    "enable_auto_search",
    "disable_auto_search",
    "is_auto_search_enabled",
    "get_import_stats",
    "reset_import_stats",
]
