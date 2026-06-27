from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .. import _config
from .._cache import (
    get_cache_config,
    set_cache_config,
)
from .._symbol import (
    get_module_skip_config,
    get_symbol_resolution_config,
    get_symbol_search_config,
    set_module_skip_config,
)

# ─── Dataclasses ──────────────────────────────────────────────


@dataclass
class AutoInstallConfig:
    enabled: bool = False
    interactive: bool = True
    allow_non_interactive: bool = False
    index: Optional[str] = None
    extra_args: list[str] = field(default_factory=list)
    prefer_uv: bool = False
    silent: bool = False


@dataclass
class RetryConfig:
    enabled: bool = False
    max_retries: int = 3
    retry_delay: float = 0.5
    modules: set[str] = field(default_factory=set)


@dataclass
class SymbolSearchConfig:
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
    auto_symbol: bool = True
    auto_threshold: float = 0.7
    conflict_threshold: float = 0.3
    symbol_misspelling: bool = True
    context_aware: bool = True
    warn_on_conflict: bool = True
    save_preferences: bool = True
    strict: bool = False


@dataclass
class CacheConfig:
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
    skip_test_modules: bool = True
    skip_internal_modules: bool = True
    skip_large_modules: bool = True
    large_module_threshold: int = 100
    skip_modules_file: Optional[str] = None


# ─── Helpers ─────────────────────────────────────────────────


def _apply_search_config(cfg: SymbolSearchConfig) -> None:
    _config._SYMBOL_SEARCH_CONFIG.update(asdict(cfg))


def _apply_resolution_config(cfg: SymbolResolutionConfig) -> None:
    _config._SYMBOL_RESOLUTION_CONFIG.update(asdict(cfg))


# ─── Module-level API functions ──────────────────────────────


def enable_debug_mode() -> None:
    _config._DEBUG_MODE = True


def disable_debug_mode() -> None:
    _config._DEBUG_MODE = False


def is_debug_mode() -> bool:
    return _config._DEBUG_MODE


def enable_auto_search() -> None:
    _config._AUTO_SEARCH_ENABLED = True


def disable_auto_search() -> None:
    _config._AUTO_SEARCH_ENABLED = False


def is_auto_search_enabled() -> bool:
    return _config._AUTO_SEARCH_ENABLED


def get_import_stats() -> dict[str, Any]:
    from .._config import _IMPORT_STATS

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
    from .._config import _IMPORT_STATS

    _IMPORT_STATS.total_imports = 0
    _IMPORT_STATS.total_time = 0.0
    _IMPORT_STATS.module_times.clear()
    _IMPORT_STATS.module_access_counts.clear()


# ─── ConfigNamespace ─────────────────────────────────────────


class ConfigNamespace:
    def __init__(self) -> None:
        self._auto_install_cache: Optional[AutoInstallConfig] = None
        self._retry_cache: Optional[RetryConfig] = None
        self._symbol_search_cache: Optional[SymbolSearchConfig] = None
        self._symbol_resolution_cache: Optional[SymbolResolutionConfig] = None
        self._cache_config_cache: Optional[CacheConfig] = None
        self._module_skip_cache: Optional[ModuleSkipConfig] = None

    def refresh(self) -> None:
        """Invalidate all cached dataclass instances.
        Next access will re-read from internal config dicts."""
        self._auto_install_cache = None
        self._retry_cache = None
        self._symbol_search_cache = None
        self._symbol_resolution_cache = None
        self._cache_config_cache = None
        self._module_skip_cache = None

    @property
    def debug(self) -> bool:
        return _config._DEBUG_MODE

    @debug.setter
    def debug(self, value: bool) -> None:
        _config._DEBUG_MODE = value

    @property
    def auto_search(self) -> bool:
        return _config._AUTO_SEARCH_ENABLED

    @auto_search.setter
    def auto_search(self, value: bool) -> None:
        _config._AUTO_SEARCH_ENABLED = value

    @property
    def auto_install(self) -> AutoInstallConfig:
        if self._auto_install_cache is None:
            c = _config._AUTO_INSTALL_CONFIG
            self._auto_install_cache = AutoInstallConfig(
                enabled=c["enabled"],
                interactive=c["interactive"],
                allow_non_interactive=c["allow_non_interactive"],
                index=c["index"],
                extra_args=list(c["extra_args"]),
                prefer_uv=c["prefer_uv"],
                silent=c["silent"],
            )
        return self._auto_install_cache

    @auto_install.setter
    def auto_install(self, cfg: AutoInstallConfig) -> None:
        _config._AUTO_INSTALL_CONFIG["enabled"] = cfg.enabled
        _config._AUTO_INSTALL_CONFIG["interactive"] = cfg.interactive
        _config._AUTO_INSTALL_CONFIG["allow_non_interactive"] = cfg.allow_non_interactive
        _config._AUTO_INSTALL_CONFIG["index"] = cfg.index
        _config._AUTO_INSTALL_CONFIG["extra_args"] = list(cfg.extra_args)
        _config._AUTO_INSTALL_CONFIG["prefer_uv"] = cfg.prefer_uv
        _config._AUTO_INSTALL_CONFIG["silent"] = cfg.silent
        self._auto_install_cache = cfg

    @property
    def auto_install_enabled(self) -> bool:
        return _config._AUTO_INSTALL_CONFIG["enabled"]

    @auto_install_enabled.setter
    def auto_install_enabled(self, value: bool) -> None:
        _config._AUTO_INSTALL_CONFIG["enabled"] = value
        if self._auto_install_cache is not None:
            self._auto_install_cache.enabled = value

    @property
    def retry(self) -> RetryConfig:
        if self._retry_cache is None:
            c = _config._RETRY_CONFIG
            self._retry_cache = RetryConfig(
                enabled=c["enabled"],
                max_retries=c["max_retries"],
                retry_delay=c["retry_delay"],
                modules=set(c["retry_modules"]),
            )
        return self._retry_cache

    @retry.setter
    def retry(self, cfg: RetryConfig) -> None:
        _config._RETRY_CONFIG["enabled"] = cfg.enabled
        _config._RETRY_CONFIG["max_retries"] = cfg.max_retries
        _config._RETRY_CONFIG["retry_delay"] = cfg.retry_delay
        _config._RETRY_CONFIG["retry_modules"] = set(cfg.modules)
        self._retry_cache = cfg

    @property
    def symbol_search(self) -> SymbolSearchConfig:
        if self._symbol_search_cache is None:
            self._symbol_search_cache = SymbolSearchConfig(**get_symbol_search_config())
        return self._symbol_search_cache

    @symbol_search.setter
    def symbol_search(self, cfg: SymbolSearchConfig) -> None:
        _apply_search_config(cfg)
        self._symbol_search_cache = cfg

    @property
    def symbol_resolution(self) -> SymbolResolutionConfig:
        if self._symbol_resolution_cache is None:
            self._symbol_resolution_cache = SymbolResolutionConfig(**get_symbol_resolution_config())
        return self._symbol_resolution_cache

    @symbol_resolution.setter
    def symbol_resolution(self, cfg: SymbolResolutionConfig) -> None:
        _apply_resolution_config(cfg)
        self._symbol_resolution_cache = cfg

    @property
    def cache(self) -> CacheConfig:
        if self._cache_config_cache is None:
            raw = get_cache_config()
            raw["max_size_mb"] = raw.pop("max_cache_size_mb", 100)
            self._cache_config_cache = CacheConfig(**raw)
        return self._cache_config_cache

    @cache.setter
    def cache(self, cfg: CacheConfig) -> None:
        set_cache_config(
            max_cache_size_mb=cfg.max_size_mb,
            symbol_index_ttl=cfg.symbol_index_ttl,
            stdlib_cache_ttl=cfg.stdlib_cache_ttl,
            third_party_cache_ttl=cfg.third_party_cache_ttl,
            enable_compression=cfg.enable_compression,
        )
        self._cache_config_cache = cfg

    @property
    def module_skip(self) -> ModuleSkipConfig:
        if self._module_skip_cache is None:
            self._module_skip_cache = ModuleSkipConfig(**get_module_skip_config())
        return self._module_skip_cache

    @module_skip.setter
    def module_skip(self, cfg: ModuleSkipConfig) -> None:
        set_module_skip_config(
            skip_test_modules=cfg.skip_test_modules,
            skip_internal_modules=cfg.skip_internal_modules,
            skip_large_modules=cfg.skip_large_modules,
            large_module_threshold=cfg.large_module_threshold,
        )
        self._module_skip_cache = cfg

    @property
    def import_stats(self) -> dict[str, Any]:
        return get_import_stats()

    def snapshot(self) -> dict[str, Any]:
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

    def restore(self, snapshot: dict[str, Any]) -> None:
        self.refresh()
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
        import json

        def _convert(obj):
            if isinstance(obj, set):
                return sorted(obj)
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_convert(i) for i in obj]
            return obj

        data = _convert(self.snapshot())
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        return json.dumps(data, indent=2)

    def temp_config(self, **kwargs: Any) -> "ConfigContext":
        return ConfigContext(self, kwargs)

    def __repr__(self) -> str:
        return f"<ConfigNamespace: debug={self.debug}, auto_search={self.auto_search}>"


class ConfigContext:
    def __init__(self, config_ns: ConfigNamespace, overrides: dict[str, Any]) -> None:
        self._config_ns = config_ns
        self._overrides = overrides
        self._snap: dict[str, Any] = {}

    def __enter__(self) -> "ConfigContext":
        self._snap = self._config_ns.snapshot()
        for key, value in self._overrides.items():
            if hasattr(self._config_ns, key) and not key.startswith("_"):
                setattr(self._config_ns, key, value)
        return self

    def __exit__(self, *args: Any) -> None:
        self._config_ns.restore(self._snap)
